"""
Workflow Execution Service

Handles workflow execution, action processing, and context management.
"""

import json
import time
import logging
import requests
from typing import Dict, List, Any, Optional, Union
from datetime import datetime, timedelta

from django.utils import timezone
from django.db import transaction
from django.core.mail import send_mail
from django.conf import settings

from workflow.models import (
    Workflow,
    WorkflowExecution,
    WorkflowAction,
    WorkflowActionExecution,
    Action,
    ActionLog
)
from workflow.utils.condition_evaluator import (
    evaluate_conditions,
    substitute_template_placeholders
)
from workflow.settings_adapters import (
    get_model_class,
    get_field_name,
    get_sender_type_values,
    get_conversation_status_values,
    add_user_tag,
    remove_user_tag,
    INTEGRATION_SETTINGS
)

logger = logging.getLogger(__name__)


class WorkflowExecutionService:
    """
    Service for executing workflows and their actions
    """
    
    def __init__(self):
        self.sender_types = get_sender_type_values()
        self.conversation_statuses = get_conversation_status_values()
    
    def execute_workflow(self, workflow: Workflow, context: Dict[str, Any]) -> WorkflowExecution:
        """
        Execute a workflow with the given context.
        
        Args:
            workflow: Workflow instance to execute
            context: Execution context data
        
        Returns:
            WorkflowExecution instance
        """
        try:
            # Additional safety check: Verify workflow ownership if conversation context is available
            conversation_id = context.get('event', {}).get('conversation_id')
            if conversation_id and workflow.created_by:
                try:
                    from message.models import Conversation
                    conversation = Conversation.objects.select_related('user').get(id=conversation_id)
                    if conversation.user.id != workflow.created_by.id:
                        logger.error(f"🚫 Security violation: Workflow '{workflow.name}' (owner: {workflow.created_by.id}) "
                                   f"attempted execution on conversation owned by user {conversation.user.id}")
                        # Create a failed execution record for auditing
                        execution = WorkflowExecution.objects.create(
                            workflow=workflow,
                            status='FAILED',
                            user=context.get('event', {}).get('user_id'),
                            conversation=conversation_id,
                            trigger_data=context.get('event', {}),
                            context_data=context,
                            started_at=timezone.now(),
                            completed_at=timezone.now(),
                            error_message=f"Workflow ownership validation failed: workflow belongs to user {workflow.created_by.id}, conversation belongs to user {conversation.user.id}"
                        )
                        return execution
                except Exception as e:
                    logger.warning(f"Could not verify workflow ownership: {e}")
                    # Continue execution if we can't verify ownership (backward compatibility)
            
            # Check for existing WAITING execution of the same workflow to prevent duplicates
            if conversation_id:
                existing_waiting = WorkflowExecution.objects.filter(
                    workflow=workflow,
                    conversation=conversation_id,
                    status='WAITING'
                ).first()
                
                if existing_waiting:
                    logger.warning(f"⚠️ Workflow '{workflow.name}' already has a WAITING execution {existing_waiting.id} for conversation {conversation_id} - skipping duplicate execution")
                    return existing_waiting
            
            # Create workflow execution record
            execution = WorkflowExecution.objects.create(
                workflow=workflow,
                status='RUNNING',
                user=context.get('event', {}).get('user_id'),
                conversation=context.get('event', {}).get('conversation_id'),
                trigger_data=context.get('event', {}),
                context_data=context,
                started_at=timezone.now()
            )
            
            logger.info(f"Started workflow execution #{execution.id} for workflow '{workflow.name}'")
            
            # Check if this is a node-based workflow
            has_nodes = workflow.nodes.exists()
            
            if has_nodes:
                # Use node-based execution service
                logger.info(f"Executing node-based workflow {workflow.name}")
                try:
                    from workflow.services.node_execution_service import NodeBasedWorkflowExecutionService
                    node_service = NodeBasedWorkflowExecutionService()
                    
                    # Execute node workflow (respect start_node_id from context if provided)
                    start_node_id = context.get('start_node_id') if isinstance(context, dict) else None
                    node_execution = node_service.execute_node_workflow(workflow, context, start_node_id=start_node_id)
                    
                    # Update the original execution with node execution results
                    if node_execution:
                        execution.status = node_execution.status
                        execution.completed_at = node_execution.completed_at
                        execution.result_data = node_execution.result_data
                        execution.error_message = node_execution.error_message
                        execution.save()
                    
                    return execution
                    
                except ImportError:
                    logger.warning("Node execution service not available, falling back to action-based execution")
                except Exception as e:
                    logger.error(f"Error in node-based execution: {e}")
                    execution.status = 'FAILED'
                    execution.error_message = f"Node execution failed: {str(e)}"
                    execution.completed_at = timezone.now()
                    execution.save()
                    return execution
            
            try:
                # Get ordered workflow actions
                workflow_actions = WorkflowAction.objects.filter(
                    workflow=workflow
                ).select_related('action', 'condition').order_by('order')
                
                if not workflow_actions.exists():
                    execution.status = 'COMPLETED'
                    execution.completed_at = timezone.now()
                    execution.result_data = {'message': 'No actions to execute'}
                    execution.save()
                    return execution
                
                # Execute actions in order
                for workflow_action in workflow_actions:
                    try:
                        action_execution = self._execute_workflow_action(
                            execution, 
                            workflow_action, 
                            context
                        )
                        
                        # Stop execution if required action failed
                        if action_execution.status == 'FAILED' and workflow_action.is_required:
                            execution.status = 'FAILED'
                            execution.error_message = f"Required action failed: {workflow_action.action.name}"
                            execution.completed_at = timezone.now()
                            execution.save()
                            logger.error(f"Workflow execution #{execution.id} failed on required action")
                            return execution
                        
                        # Add action result to context if configured
                        if workflow_action.add_result_to_context and action_execution.result_data:
                            context_key = f"action_{workflow_action.action.action_type}_{workflow_action.order}"
                            context[context_key] = action_execution.result_data
                    
                    except Exception as e:
                        logger.error(f"Error executing action {workflow_action.action.name}: {e}")
                        if workflow_action.is_required:
                            execution.status = 'FAILED'
                            execution.error_message = str(e)
                            execution.completed_at = timezone.now()
                            execution.save()
                            return execution
                
                # Mark execution as completed
                execution.status = 'COMPLETED'
                execution.completed_at = timezone.now()
                execution.result_data = {'executed_actions': workflow_actions.count()}
                execution.save()
                
                logger.info(f"Completed workflow execution #{execution.id}")
                return execution
            
            except Exception as e:
                execution.status = 'FAILED'
                execution.error_message = str(e)
                execution.error_details = {'exception_type': type(e).__name__}
                execution.completed_at = timezone.now()
                execution.save()
                logger.error(f"Workflow execution #{execution.id} failed: {e}")
                raise
        
        except Exception as e:
            logger.error(f"Error creating workflow execution for {workflow.name}: {e}")
            raise
    
    def _execute_workflow_action(
        self, 
        execution: WorkflowExecution, 
        workflow_action: WorkflowAction, 
        context: Dict[str, Any]
    ) -> WorkflowActionExecution:
        """
        Execute a single workflow action.
        
        Args:
            execution: WorkflowExecution instance
            workflow_action: WorkflowAction instance
            context: Execution context
        
        Returns:
            WorkflowActionExecution instance
        """
        # Create action execution record
        action_execution = WorkflowActionExecution.objects.create(
            workflow_execution=execution,
            workflow_action=workflow_action,
            status='PENDING',
            input_data=context
        )
        
        try:
            # ✅ Pass workflow_action through context for actions that need access to .config
            # This avoids changing _execute_action signature and breaking existing code
            context_with_action = dict(context)
            context_with_action['_workflow_action'] = workflow_action
            
            # Check if action has a condition
            if workflow_action.condition:
                condition_config = {
                    'operator': workflow_action.condition.operator,
                    'conditions': workflow_action.condition.conditions,
                    'use_custom_code': workflow_action.condition.use_custom_code,
                    'custom_code': workflow_action.condition.custom_code
                }
                
                if not evaluate_conditions(condition_config, context_with_action):
                    action_execution.status = 'SKIPPED'
                    action_execution.completed_at = timezone.now()
                    action_execution.result_data = {'reason': 'Condition not met'}
                    action_execution.save()
                    logger.info(f"Skipped action {workflow_action.action.name} - condition not met")
                    return action_execution
            
            # Apply delay if configured
            if workflow_action.action.delay > 0:
                action_execution.status = 'WAITING'
                action_execution.save()
                # Schedule this action to execute after delay
                try:
                    from workflow.tasks import execute_workflow_action
                    execute_workflow_action.apply_async(args=[action_execution.id], countdown=workflow_action.action.delay)
                    logger.info(f"Scheduled action {workflow_action.action.name} after {workflow_action.action.delay} seconds (action_execution #{action_execution.id})")
                except Exception as se:
                    logger.error(f"Failed to schedule delayed action execution: {se}")
                # Return without running now
                return action_execution
            
            # Mark as running
            action_execution.status = 'RUNNING'
            action_execution.started_at = timezone.now()
            action_execution.save()
            
            # Execute the action
            start_time = time.time()
            result = self._execute_action(workflow_action.action, context_with_action)
            duration = time.time() - start_time
            
            # Update execution record
            action_execution.status = 'COMPLETED'
            action_execution.completed_at = timezone.now()
            action_execution.result_data = result
            action_execution.save()
            
            # Log action execution
            ActionLog.objects.create(
                action=workflow_action.action,
                duration=duration,
                context=context_with_action,
                result=result,
                success=True
            )
            
            logger.info(f"Completed action {workflow_action.action.name} in {duration:.2f}s")
            return action_execution
        
        except Exception as e:
            action_execution.status = 'FAILED'
            action_execution.error_message = str(e)
            action_execution.error_details = {'exception_type': type(e).__name__}
            action_execution.completed_at = timezone.now()
            action_execution.save()
            
            # Log action failure
            ActionLog.objects.create(
                action=workflow_action.action,
                duration=time.time() - start_time if 'start_time' in locals() else 0,
                context=context_with_action if 'context_with_action' in locals() else context,
                result={},
                success=False,
                error_message=str(e)
            )
            
            logger.error(f"Action {workflow_action.action.name} failed: {e}")
            raise
    
    def _execute_action(self, action: Action, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a specific action based on its type.
        
        Args:
            action: Action instance
            context: Execution context
        
        Returns:
            Action execution result
        """
        # Substitute placeholders in configuration
        config = substitute_template_placeholders(action.configuration, context)
        
        if action.action_type == 'send_message':
            return self._execute_send_message(config, context)
        elif action.action_type == 'update_user':
            return self._execute_update_user(config, context)
        elif action.action_type == 'add_tag':
            return self._execute_add_tag(config, context)
        elif action.action_type == 'remove_tag':
            return self._execute_remove_tag(config, context)
        elif action.action_type == 'send_email':
            return self._execute_send_email(config, context)
        elif action.action_type == 'add_note':
            return self._execute_add_note(config, context)
        elif action.action_type == 'webhook':
            return self._execute_webhook(config, context)
        elif action.action_type == 'wait':
            return self._execute_wait(config, context)
        elif action.action_type == 'redirect_conversation':
            return self._execute_redirect_conversation(config, context)
        elif action.action_type == 'set_conversation_status':
            return self._execute_set_conversation_status(config, context)
        elif action.action_type == 'custom_code':
            return self._execute_custom_code(config, context)
        elif action.action_type == 'control_ai_response':
            return self._execute_control_ai_response(config, context)
        elif action.action_type == 'update_ai_context':
            return self._execute_update_ai_context(config, context)
        elif action.action_type == 'instagram_comment_dm_reply':
            return self._execute_instagram_comment_action(config, context)
        else:
            raise ValueError(f"Unknown action type: {action.action_type}")
    
    def _execute_send_message(self, config: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute send_message action with enhanced chat integration"""
        message_content = config.get('message', '')
        if not message_content:
            raise ValueError("Message content is required")
        
        conversation_id = context.get('event', {}).get('conversation_id')
        user_id = context.get('event', {}).get('user_id')
        
        if not conversation_id or not user_id:
            raise ValueError("Conversation ID and User ID are required")
        
        try:
            # Import here to avoid circular imports
            from message.models import Message, Conversation, Customer
            from message.utils import send_message_notification
            from message.serializers import WSMessageSerializer
            
            # Get conversation and customer
            conversation = Conversation.objects.get(id=conversation_id)
            customer = Customer.objects.get(id=user_id)
            
            # Determine message type from config (default to marketing)
            message_type = config.get('message_type', 'marketing')
            if message_type not in ['marketing', 'support', 'AI']:
                message_type = 'marketing'
            
            # Create message in database with workflow metadata
            message = Message.objects.create(
                conversation=conversation,
                customer=customer,
                content=message_content,
                type=message_type,
                metadata={
                    'workflow_execution': True,
                    'action_type': 'send_message',
                    'workflow_id': context.get('workflow_id'),
                    'execution_id': context.get('execution_id'),
                    'sent_via_workflow': True
                }
            )
            
            # Prevent AI from responding to the previous customer message by marking it answered
            try:
                if message_type == 'marketing':
                    Message.objects.filter(
                        conversation_id=conversation_id,
                        type='customer',
                        is_answered=False
                    ).update(is_answered=True)
            except Exception as e:
                logger.warning(f"Failed to mark previous customer messages as answered: {e}")
            
            # Broadcast to WebSocket chat group so clients see the marketing message immediately
            try:
                from channels.layers import get_channel_layer
                from asgiref.sync import async_to_sync
                channel_layer = get_channel_layer()
                if channel_layer:
                    group_name = f"chat_{conversation_id}"
                    payload = {
                        'type': 'chat_message',
                        'message': WSMessageSerializer(message).data,
                        'external_send_result': {}
                    }
                    async_to_sync(channel_layer.group_send)(group_name, payload)
                    # Also notify conversation list to refresh
                    user_group = f"user_{conversation.user.id}_conversations"
                    async_to_sync(channel_layer.group_send)(user_group, {
                        'type': 'conversation_updated',
                        'conversation_id': str(conversation_id)
                    })
            except Exception as e:
                logger.warning(f"Failed to broadcast workflow message to WebSocket: {e}")
            
            # Send real-time notification via WebSocket
            try:
                # Import here to avoid circular imports
                from channels.layers import get_channel_layer
                from asgiref.sync import async_to_sync
                
                channel_layer = get_channel_layer()
                if channel_layer:
                    # Already sent formatted chat_message above; keep this as a light log
                    logger.info(f"Broadcasted workflow message {message.id} to chat group")
                else:
                    logger.warning("Channel layer not available for WebSocket notification")
            except Exception as e:
                logger.warning(f"Failed to send WebSocket notification: {e}")
            
            result = {
                'message_id': str(message.id),
                'content': message_content,
                'message_type': message_type,
                'sent_to_channel': False,
                'websocket_notification_sent': True
            }
            
            # Try to send to external channels
            try:
                source = getattr(customer, 'source', '')
                if source == 'telegram':
                    from message.services.telegram_service import TelegramService
                    svc = TelegramService.get_service_for_conversation(conversation)
                    if svc:
                        send_res = svc.send_message_to_customer(customer, message_content)
                        result['sent_to_channel'] = bool(send_res.get('success'))
                        result['channel'] = 'telegram'
                    else:
                        logger.warning("Telegram service not available for this conversation")
                elif source == 'instagram':
                    from message.services.instagram_service import InstagramService
                    svc = InstagramService.get_service_for_conversation(conversation)
                    if svc:
                        logger.info(f"📤 [Workflow] Sending Instagram message...")
                        logger.info(f"   Conversation: {conversation.id}")
                        logger.info(f"   Customer: {customer.id}")
                        logger.info(f"   Content (first 80 chars): {message_content[:80]}...")
                        logger.info(f"   Content length: {len(message_content)}")
                        
                        send_res = svc.send_message_to_customer(customer, message_content)
                        result['sent_to_channel'] = bool(send_res.get('success'))
                        result['channel'] = 'instagram'
                        
                        if send_res.get('success'):
                            logger.info(f"✅ [Workflow] Instagram message sent successfully")
                            logger.info(f"   Instagram message_id: {send_res.get('message_id')}")
                        else:
                            logger.warning(f"❌ [Workflow] Instagram message send failed: {send_res.get('error')}")
                        
                        # ✅ Mark message as sent to prevent webhook duplicate
                        if send_res.get('success'):
                            from django.core.cache import cache
                            import hashlib
                            
                            message_hash = hashlib.md5(
                                f"{conversation.id}:{message_content}".encode()
                            ).hexdigest()
                            cache_key = f"instagram_sent_msg_{message_hash}"
                            cache.set(cache_key, True, timeout=60)
                            logger.info(f"📝 [Workflow] Cached sent message to prevent webhook duplicate")
                            logger.info(f"   Cache key: {cache_key}")
                            logger.info(f"   Cache timeout: 60 seconds")
                            
                            # Also update message metadata if message_id is available
                            if send_res.get('message_id') and message:
                                message.metadata = message.metadata or {}
                                message.metadata['external_message_id'] = str(send_res.get('message_id'))
                                message.metadata['sent_from_app'] = True
                                message.save(update_fields=['metadata'])
                                logger.info(f"📝 [Workflow] Stored Instagram message_id in metadata")
                                logger.info(f"   Message ID: {message.id}")
                                logger.info(f"   External message_id: {send_res.get('message_id')}")
                                logger.info(f"   Metadata: {message.metadata}")
                    else:
                        logger.warning("Instagram service not available for this conversation")
            except Exception as e:
                logger.warning(f"Failed to send external channel message: {e}")
             
            return result
        
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            raise
    
    def _send_telegram_message(self, chat_id: str, message: str):
        """Send message via Telegram Bot API"""
        token = INTEGRATION_SETTINGS.get('TELEGRAM_BOT_TOKEN')
        if not token:
            raise ValueError("TELEGRAM_BOT_TOKEN not configured")
        
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        data = {
            'chat_id': chat_id,
            'text': message,
            'parse_mode': 'HTML'
        }
        
        response = requests.post(url, json=data, timeout=10)
        response.raise_for_status()
    
    def _send_instagram_message(self, user_id: str, message: str):
        """Send message via N8N webhook"""
        webhook_url = INTEGRATION_SETTINGS.get('N8N_WEBHOOK_URL')
        if not webhook_url:
            raise ValueError("N8N_WEBHOOK_URL not configured")
        
        data = {
            'userId': user_id,
            'message': message,
            'sender_type': 'MARKETING'
        }
        
        response = requests.post(webhook_url, json=data, timeout=10)
        response.raise_for_status()
    
    def _execute_update_user(self, config: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute update_user action"""
        user_id = context.get('event', {}).get('user_id')
        if not user_id:
            raise ValueError("User ID is required")
        
        try:
            UserModel = get_model_class('USER')
            user = UserModel.objects.get(id=user_id)
            
            updates = config.get('updates', {})
            updated_fields = []
            
            for field, value in updates.items():
                if hasattr(user, field):
                    setattr(user, field, value)
                    updated_fields.append(field)
            
            if updated_fields:
                user.save(update_fields=updated_fields)
            
            return {
                'user_id': user_id,
                'updated_fields': updated_fields,
                'updates_applied': len(updated_fields)
            }
        
        except Exception as e:
            logger.error(f"Error updating user {user_id}: {e}")
            raise
    
    def _execute_add_tag(self, config: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute add_tag action"""
        user_id = context.get('event', {}).get('user_id')
        tag_name = config.get('tag_name', '')
        
        if not user_id or not tag_name:
            raise ValueError("User ID and tag name are required")
        
        try:
            UserModel = get_model_class('USER')
            user = UserModel.objects.get(id=user_id)
            
            success = add_user_tag(user, tag_name)
            
            return {
                'user_id': user_id,
                'tag_name': tag_name,
                'success': success
            }
        
        except Exception as e:
            logger.error(f"Error adding tag {tag_name} to user {user_id}: {e}")
            raise
    
    def _execute_remove_tag(self, config: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute remove_tag action"""
        user_id = context.get('event', {}).get('user_id')
        tag_name = config.get('tag_name', '')
        
        if not user_id or not tag_name:
            raise ValueError("User ID and tag name are required")
        
        try:
            UserModel = get_model_class('USER')
            user = UserModel.objects.get(id=user_id)
            
            success = remove_user_tag(user, tag_name)
            
            return {
                'user_id': user_id,
                'tag_name': tag_name,
                'success': success
            }
        
        except Exception as e:
            logger.error(f"Error removing tag {tag_name} from user {user_id}: {e}")
            raise
    
    def _execute_send_email(self, config: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute send_email action"""
        subject = config.get('subject', '')
        body = config.get('body', '')
        recipient_email = config.get('recipient', context.get('user', {}).get('email', ''))
        
        if not recipient_email:
            raise ValueError("Recipient email is required")
        
        try:
            send_mail(
                subject=subject,
                message=body,
                from_email=INTEGRATION_SETTINGS.get('DEFAULT_FROM_EMAIL'),
                recipient_list=[recipient_email],
                fail_silently=False,
                html_message=body if config.get('is_html', False) else None
            )
            
            return {
                'recipient': recipient_email,
                'subject': subject,
                'sent': True
            }
        
        except Exception as e:
            logger.error(f"Error sending email to {recipient_email}: {e}")
            raise
    
    def _execute_add_note(self, config: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute add_note action"""
        note_content = config.get('note', '')
        if not note_content:
            raise ValueError("Note content is required")
        
        conversation_id = context.get('event', {}).get('conversation_id')
        user_id = context.get('event', {}).get('user_id')
        
        try:
            MessageModel = get_model_class('MESSAGE')
            ConversationModel = get_model_class('CONVERSATION')
            UserModel = get_model_class('USER')
            
            conversation = ConversationModel.objects.get(id=conversation_id)
            user = UserModel.objects.get(id=user_id)
            
            # Create internal note as message with metadata
            message_data = {
                get_field_name('MESSAGE', 'CONVERSATION_FIELD'): conversation,
                get_field_name('MESSAGE', 'CUSTOMER_FIELD'): user,
                get_field_name('MESSAGE', 'CONTENT_FIELD'): note_content,
                get_field_name('MESSAGE', 'SENDER_TYPE_FIELD'): self.sender_types['SUPPORT'],
            }
            
            # Add note metadata if field exists
            metadata_field = get_field_name('MESSAGE', 'METADATA_FIELD')
            if hasattr(MessageModel, metadata_field):
                message_data[metadata_field] = {
                    'note_type': 'workflow_note',
                    'internal': True
                }
            
            message = MessageModel.objects.create(**message_data)
            
            return {
                'note_id': str(message.id),
                'content': note_content
            }
        
        except Exception as e:
            logger.error(f"Error adding note: {e}")
            raise
    
    def _execute_webhook(self, config: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute webhook action"""
        url = config.get('url', '')
        method = config.get('method', 'POST').upper()
        headers = config.get('headers', {})
        payload = config.get('payload', {})
        
        if not url:
            raise ValueError("Webhook URL is required")
        
        try:
            # Redact sensitive headers for logging
            safe_headers = {k: '***' if 'auth' in k.lower() or 'token' in k.lower() else v 
                          for k, v in headers.items()}
            
            response = requests.request(
                method=method,
                url=url,
                headers=headers,
                json=payload,
                timeout=30
            )
            
            response.raise_for_status()
            
            return {
                'url': url,
                'method': method,
                'status_code': response.status_code,
                'headers': safe_headers,
                'success': True
            }
        
        except Exception as e:
            logger.error(f"Webhook request failed: {e}")
            raise
    
    def _execute_wait(self, config: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute wait action"""
        duration = config.get('duration', 0)
        unit = config.get('unit', 'seconds')
        
        # Convert to seconds
        if unit == 'minutes':
            duration *= 60
        elif unit == 'hours':
            duration *= 3600
        elif unit == 'days':
            duration *= 86400
        
        # In a real implementation, this would schedule the next action with Celery
        # For now, we just log the wait time
        logger.info(f"Wait action: {duration} seconds")
        
        return {
            'duration': duration,
            'unit': unit,
            'scheduled': True
        }
    
    def _execute_set_conversation_status(self, config: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute set_conversation_status action"""
        new_status = config.get('status', '')
        conversation_id = context.get('event', {}).get('conversation_id')
        
        if not conversation_id or not new_status:
            raise ValueError("Conversation ID and status are required")
        
        # Check if status exists in project
        if new_status not in self.conversation_statuses.values():
            logger.warning(f"Status '{new_status}' not available in project, skipping")
            return {
                'conversation_id': conversation_id,
                'requested_status': new_status,
                'changed': False,
                'reason': 'Status not available'
            }
        
        try:
            ConversationModel = get_model_class('CONVERSATION')
            conversation = ConversationModel.objects.get(id=conversation_id)
            
            old_status = getattr(conversation, get_field_name('CONVERSATION', 'STATUS_FIELD'))
            setattr(conversation, get_field_name('CONVERSATION', 'STATUS_FIELD'), new_status)
            conversation.save()
            
            return {
                'conversation_id': conversation_id,
                'old_status': old_status,
                'new_status': new_status,
                'changed': True
            }
        
        except Exception as e:
            logger.error(f"Error setting conversation status: {e}")
            raise

    def _execute_redirect_conversation(self, config: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute redirect_conversation action for classic workflows"""
        destination = config.get('redirect_destination') or config.get('destination')
        conversation_id = context.get('event', {}).get('conversation_id')
        if not conversation_id:
            raise ValueError("Conversation ID is required")
        try:
            from workflow.settings_adapters import (
                get_model_class,
                get_field_name,
                get_conversation_status_values,
            )
            ConversationModel = get_model_class('CONVERSATION')
            status_field = get_field_name('CONVERSATION', 'STATUS_FIELD')
            status_values = get_conversation_status_values()
            conversation = ConversationModel.objects.select_related('user').get(id=conversation_id)
            old_status = getattr(conversation, status_field)
            new_status = status_values.get('SUPPORT_ACTIVE', old_status)
            setattr(conversation, status_field, new_status)
            conversation.save()
            logger.info(f"Redirected conversation {conversation_id} to {destination}; status {old_status} -> {new_status}")
            # Broadcast update
            try:
                from channels.layers import get_channel_layer
                from asgiref.sync import async_to_sync
                channel_layer = get_channel_layer()
                if channel_layer:
                    user_group = f"user_{conversation.user.id}_conversations"
                    async_to_sync(channel_layer.group_send)(user_group, {
                        'type': 'conversation_updated',
                        'conversation_id': str(conversation_id)
                    })
            except Exception as be:
                logger.warning(f"Failed to broadcast conversation redirect: {be}")
            return {
                'conversation_id': conversation_id,
                'redirected_to': destination,
                'old_status': old_status,
                'new_status': new_status,
            }
        except Exception as e:
            logger.error(f"Error redirecting conversation: {e}")
            raise
    
    def _execute_custom_code(self, config: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute custom_code action"""
        code = config.get('code', '')
        if not code:
            raise ValueError("Custom code is required")
        
        try:
            # Create a restricted environment
            safe_globals = {
                '__builtins__': {
                    'len': len,
                    'str': str,
                    'int': int,
                    'float': float,
                    'bool': bool,
                    'list': list,
                    'dict': dict,
                    'tuple': tuple,
                    'set': set,
                    'abs': abs,
                    'min': min,
                    'max': max,
                    'sum': sum,
                    'round': round,
                    'isinstance': isinstance,
                    'type': type,
                    'hasattr': hasattr,
                    'getattr': getattr,
                },
                'context': context,
                'config': config,
            }
            
            # Create local namespace
            safe_locals = {'result': {}}
            
            # Execute the code
            exec(code, safe_globals, safe_locals)
            
            return safe_locals.get('result', {})
        
        except Exception as e:
            logger.error(f"Error executing custom code: {e}")
            raise
    
    def _execute_control_ai_response(self, config: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute control_ai_response action to control AI behavior in conversations"""
        conversation_id = context.get('event', {}).get('conversation_id')
        if not conversation_id:
            raise ValueError("Conversation ID is required")
        
        action_type = config.get('action', 'disable')  # disable, enable, custom_prompt, reset_context
        
        try:
            from message.models import Conversation
            from django.core.cache import cache
            
            conversation = Conversation.objects.get(id=conversation_id)
            
            # Create AI control cache key
            ai_control_key = f"ai_control_{conversation_id}"
            
            if action_type == 'disable':
                # Disable AI for this conversation
                cache.set(ai_control_key, {'ai_enabled': False}, timeout=86400)  # 24 hours
                result = {'ai_disabled': True, 'conversation_id': conversation_id}
                
            elif action_type == 'enable':
                # Enable AI for this conversation
                cache.set(ai_control_key, {'ai_enabled': True}, timeout=86400)
                result = {'ai_enabled': True, 'conversation_id': conversation_id}
                
            elif action_type == 'custom_prompt':
                # Set custom AI prompt for this conversation
                custom_prompt = config.get('custom_prompt', '')
                if custom_prompt:
                    cache.set(ai_control_key, {
                        'ai_enabled': True,
                        'custom_prompt': custom_prompt
                    }, timeout=86400)
                    result = {
                        'custom_prompt_set': True,
                        'conversation_id': conversation_id,
                        'prompt': custom_prompt
                    }
                else:
                    result = {'error': 'Custom prompt is required'}
                    
            elif action_type == 'reset_context':
                # Reset AI context for this conversation
                ai_context_key = f"ai_context_{conversation_id}"
                cache.delete(ai_context_key)
                result = {'context_reset': True, 'conversation_id': conversation_id}
                
            else:
                result = {'error': f'Unknown AI control action: {action_type}'}
            
            logger.info(f"AI control action '{action_type}' executed for conversation {conversation_id}")
            return result
            
        except Exception as e:
            logger.error(f"Error executing AI control action: {e}")
            raise
    
    def _execute_update_ai_context(self, config: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute update_ai_context action to add context information for AI"""
        conversation_id = context.get('event', {}).get('conversation_id')
        if not conversation_id:
            raise ValueError("Conversation ID is required")
        
        context_data = config.get('context_data', {})
        if not context_data:
            raise ValueError("Context data is required")
        
        try:
            from django.core.cache import cache
            
            # Get existing AI context
            ai_context_key = f"ai_context_{conversation_id}"
            existing_context = cache.get(ai_context_key, {})
            
            # Merge new context data
            existing_context.update(context_data)
            
            # Save updated context
            cache.set(ai_context_key, existing_context, timeout=86400)  # 24 hours
            
            result = {
                'context_updated': True,
                'conversation_id': conversation_id,
                'context_data': existing_context
            }
            
            logger.info(f"AI context updated for conversation {conversation_id}")
            return result
            
        except Exception as e:
            logger.error(f"Error updating AI context: {e}")
            raise
    
    def _execute_instagram_comment_action(self, config: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute instagram_comment_dm_reply action
        
        This action sends a DM and optionally replies to an Instagram comment
        
        Args:
            config: Not used (config comes from workflow_action.config, accessed via context)
            context: Execution context containing event data and workflow_action
            
        Returns:
            Action execution result
        """
        from workflow.services.instagram_comment_action import handle_instagram_comment_dm_reply
        
        event = context.get('event', {})
        event_data = event.get('data', {}) if isinstance(event, dict) else {}
        
        # ✅ Get user from context (set by TriggerService)
        user = None
        if 'workflow_owner_id' in context:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            try:
                user = User.objects.get(id=context['workflow_owner_id'])
            except User.DoesNotExist:
                raise ValueError(f"User {context['workflow_owner_id']} not found")
        else:
            raise ValueError("workflow_owner_id not found in context for instagram_comment action")
        
        # ✅ Get workflow_action from context (we need it for .config)
        # The workflow_action is passed through context in _execute_workflow_action
        workflow_action = context.get('_workflow_action')
        if not workflow_action:
            # Fallback: try to get from action_execution if available
            # This should not happen in normal flow, but safety check
            raise ValueError("workflow_action not found in context")
        
        # Call handler
        action_result = handle_instagram_comment_dm_reply(
            workflow_action=workflow_action,
            event_data=event_data,
            user=user
        )
        
        return action_result

