"""
Node-Based Workflow Execution Service

Handles execution of workflows using the new node-based structure.
"""

import json
import time
import logging
from typing import Dict, List, Any, Optional, Union
from datetime import datetime, timedelta

from django.utils import timezone
from django.db import transaction
from django.core.mail import send_mail
from django.conf import settings

from workflow.models import (
    Workflow,
    WorkflowExecution,
    WorkflowNode,
    WhenNode,
    ConditionNode,
    ActionNode,
    WaitingNode,
    NodeConnection,
    UserResponse
)
from workflow.utils.condition_evaluator import (
    evaluate_conditions,
    evaluate_condition_group,
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


class NodeExecutionResult:
    """Result of node execution"""
    
    def __init__(self, success: bool = True, data: Dict = None, next_nodes: List = None, 
                 waiting_for_response: bool = False, error: str = None):
        self.success = success
        self.data = data or {}
        self.next_nodes = next_nodes or []
        self.waiting_for_response = waiting_for_response
        self.error = error


class NodeBasedWorkflowExecutionService:
    """
    Service for executing node-based workflows
    """
    
    def __init__(self):
        self.sender_types = get_sender_type_values()
        self.conversation_statuses = get_conversation_status_values()
    
    def _get_conversation_language(self, conversation_id: Optional[str]) -> str:
        """Best-effort fetch of conversation owner's language for localization."""
        try:
            if not conversation_id:
                return 'english'
            ConversationModel = get_model_class('CONVERSATION')
            conv = ConversationModel.objects.select_related('user').get(id=conversation_id)
            lang = getattr(conv.user, 'language', '') or ''
            return (lang or 'english').lower()
        except Exception:
            return 'english'
    
    def _translate_invalid_prompt(self, storage_type: str, language: str) -> str:
        """Localized invalid input prompt by storage_type and language."""
        lang = (language or 'english').lower()
        if 'fa' in lang or 'persian' in lang or 'farsi' in lang:
            if storage_type == 'email':
                return 'Invalid. Please enter a valid email. Please try again.'
            if storage_type == 'phone':
                return 'Invalid. Please enter a valid phone number. Please try again.'
            return 'Invalid. Please try again.'
        else:
            if storage_type == 'email':
                return 'Invalid input. Please provide a valid email address. Please try again.'
            if storage_type == 'phone':
                return 'Invalid input. Please provide a valid phone number. Please try again.'
            return 'Invalid input. Please try again.'
    
    def execute_node_workflow(self, workflow: Workflow, context: Dict[str, Any], 
                             start_node_id: str = None) -> WorkflowExecution:
        """
        Execute a workflow using node-based structure.
        
        Args:
            workflow: Workflow instance to execute
            context: Execution context data
            start_node_id: Optional specific node to start from
        
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
                        logger.error(f"🚫 Security violation: Node-based workflow '{workflow.name}' (owner: {workflow.created_by.id}) "
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
                            error_message=f"Node workflow ownership validation failed: workflow belongs to user {workflow.created_by.id}, conversation belongs to user {conversation.user.id}"
                        )
                        return execution
                except Exception as e:
                    logger.warning(f"Could not verify node workflow ownership: {e}")
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
            
            logger.info(f"Started node-based workflow execution #{execution.id} for workflow '{workflow.name}'")
            
            try:
                # Find starting nodes
                if start_node_id:
                    start_nodes = [WorkflowNode.objects.get(id=start_node_id, workflow=workflow)]
                else:
                    start_nodes = list(workflow.nodes.filter(node_type='when', is_active=True))
                
                if not start_nodes:
                    execution.status = 'COMPLETED'
                    execution.completed_at = timezone.now()
                    execution.result_data = {'message': 'No starting nodes found'}
                    execution.save()
                    return execution
                
                # Execute workflow starting from trigger nodes
                execution_context = context.copy()
                execution_context['execution_id'] = execution.id
                
                for start_node in start_nodes:
                    try:
                        # If explicit start node is provided, skip trigger check and start immediately
                        if start_node_id:
                            self._execute_node_chain(start_node, execution_context, execution)
                        else:
                            # Check if this when node should trigger
                            if self._should_when_node_trigger(start_node, context):
                                self._execute_node_chain(start_node, execution_context, execution)
                    except Exception as e:
                        logger.error(f"Error executing from start node {start_node.id}: {e}")
                        continue
                
                # Update execution status
                if execution.status == 'RUNNING':
                    execution.status = 'COMPLETED'
                    execution.completed_at = timezone.now()
                    execution.result_data = {'message': 'Workflow completed successfully'}
                    execution.save()
                    
                    # Re-enable AI now that workflow is truly completed
                    try:
                        from django.core.cache import cache
                        conversation_id = context.get('event', {}).get('conversation_id')
                        if conversation_id:
                            ai_control_key = f"ai_control_{conversation_id}"
                            cache.set(ai_control_key, {'ai_enabled': True}, timeout=86400)
                            logger.info(f"✅ Normal workflow completed for conversation {conversation_id}. Re-enabling AI.")
                    except Exception as e:
                        logger.warning(f"Could not re-enable AI after normal workflow completion: {e}")
                
                logger.info(f"Completed node-based workflow execution #{execution.id}")
                return execution
            
            except Exception as e:
                execution.status = 'FAILED'
                execution.error_message = str(e)
                execution.error_details = {'exception_type': type(e).__name__}
                execution.completed_at = timezone.now()
                execution.save()
                logger.error(f"Node-based workflow execution #{execution.id} failed: {e}")
                raise
        
        except Exception as e:
            logger.error(f"Error creating node-based workflow execution for {workflow.name}: {e}")
            raise
    
    def _should_when_node_trigger(self, when_node: WorkflowNode, context: Dict[str, Any]) -> bool:
        """
        Check if a when node should trigger based on the event context.
        """
        try:
            when_node_obj = WhenNode.objects.get(id=when_node.id)
            # Get event type from the context - can be in different places
            event_type = context.get('event', {}).get('type') or context.get('event', {}).get('event_type', '')
            if not event_type and 'event' in context:
                # If not found directly, infer from event data structure
                if 'data' in context['event'] and 'content' in context['event']['data']:
                    event_type = 'MESSAGE_RECEIVED'
            
            event_data = context.get('event', {}).get('data', {})
            
            # Map event types to when node types for matching
            event_to_when_mapping = {
                'MESSAGE_RECEIVED': 'receive_message',
                'USER_CREATED': 'new_customer',
                'TAG_ADDED': 'add_tag',
                'SCHEDULED': 'scheduled',
            }
            
            expected_when_type = event_to_when_mapping.get(event_type)
            
            # Special case: add_tag can also trigger on MESSAGE_RECEIVED if it has tags configured
            # This allows filtering users by tags when they send a message (frontend "by tag" feature)
            if event_type == 'MESSAGE_RECEIVED' and when_node_obj.when_type == 'add_tag' and when_node_obj.tags:
                logger.info(f"🏷️  add_tag when node will act as tag filter for MESSAGE_RECEIVED event")
                # Allow it to continue and check tags below
            elif expected_when_type != when_node_obj.when_type:
                logger.debug(f"Event type {event_type} (when: {expected_when_type}) doesn't match node when_type: {when_node_obj.when_type}")
                return False
            
            # Check when type specific conditions
            if when_node_obj.when_type == 'receive_message':
                # Check keywords
                if when_node_obj.keywords:
                    message_content = event_data.get('content', '').lower()
                    if not any(keyword.lower() in message_content for keyword in when_node_obj.keywords):
                        logger.debug(f"Message content '{message_content}' doesn't contain any keywords: {when_node_obj.keywords}")
                        return False
                
                # Check channels
                if when_node_obj.channels and 'all' not in when_node_obj.channels:
                    source = context.get('user', {}).get('source', '')
                    if source not in when_node_obj.channels:
                        logger.debug(f"User source '{source}' not in allowed channels: {when_node_obj.channels}")
                        return False
                
                # Check tags - filter by customer tags (user_id in context is customer_id)
                if when_node_obj.tags:
                    user_tags = context.get('user', {}).get('tags', [])
                    
                    # If tags not in context, try to fetch from database
                    if not user_tags and context.get('event', {}).get('user_id'):
                        try:
                            from workflow.settings_adapters import get_model_class
                            # Note: USER model is mapped to message.Customer in settings_adapters
                            UserModel = get_model_class('USER')
                            customer_id = context.get('event', {}).get('user_id')
                            customer = UserModel.objects.get(id=customer_id)
                            
                            # Try 'tag' first (as per FIELD_MAPPINGS), then 'tags' as fallback
                            try:
                                user_tags = list(customer.tag.values_list('name', flat=True))
                            except:
                                try:
                                    user_tags = list(customer.tags.values_list('name', flat=True))
                                except:
                                    user_tags = []
                            
                            logger.info(f"🏷️ Loaded customer tags for filtering: customer_id={customer_id}, tags={user_tags}")
                        except Exception as e:
                            logger.warning(f"Could not load customer tags for tag filtering: {e}")
                            user_tags = []
                    
                    # Check if customer has at least one of the required tags
                    has_required_tag = any(tag in user_tags for tag in when_node_obj.tags)
                    
                    if not has_required_tag:
                        logger.info(f"❌ Customer tags {user_tags} don't match required tags: {when_node_obj.tags}")
                        return False
                    else:
                        logger.info(f"✅ Customer has required tag from: {when_node_obj.tags}")
            
            elif when_node_obj.when_type == 'scheduled':
                # Validate schedule by workflow owner's timezone (or conversation owner's if available)
                try:
                    from django.conf import settings as dj_settings
                    from zoneinfo import ZoneInfo
                    user_timezone = None
                    # Prefer conversation owner if present in context
                    owner_tz = None
                    try:
                        # If conversation is present, try to get its owner user for tz
                        conversation_id = context.get('event', {}).get('conversation_id')
                        if conversation_id:
                            from message.models import Conversation as _Conv
                            conv = _Conv.objects.select_related('user').get(id=conversation_id)
                            owner_tz = getattr(conv.user, 'time_zone', None)
                            if not owner_tz:
                                # Fallback by country
                                owner_country = (getattr(conv.user, 'country', '') or '').lower()
                                if 'iran' in owner_country or owner_country in ['ir', 'irn']:
                                    owner_tz = 'Asia/Tehran'
                    except Exception:
                        owner_tz = None
                    if not owner_tz and getattr(when_node_obj.workflow, 'created_by', None):
                        owner = when_node_obj.workflow.created_by
                        owner_tz = getattr(owner, 'time_zone', None)
                        if not owner_tz:
                            owner_country = (getattr(owner, 'country', '') or '').lower()
                            if 'iran' in owner_country or owner_country in ['ir', 'irn']:
                                owner_tz = 'Asia/Tehran'
                    if owner_tz:
                        user_timezone = ZoneInfo(owner_tz)
                    else:
                        # Default to project timezone if user tz is not set
                        project_tz = getattr(dj_settings, 'TIME_ZONE', 'UTC')
                        try:
                            user_timezone = ZoneInfo(project_tz)
                        except Exception:
                            user_timezone = ZoneInfo('UTC')
                    # Compute localized now
                    localized_now = timezone.now().astimezone(user_timezone)
                    schedule_time = getattr(when_node_obj, 'schedule_time', None)
                    schedule_date = getattr(when_node_obj, 'schedule_start_date', None)
                    frequency = getattr(when_node_obj, 'schedule_frequency', None)
                    if not schedule_time or not frequency:
                        logger.debug("Scheduled when node missing schedule_time or frequency")
                        return False
                    # Helper: check time match within 60 seconds tolerance
                    def _time_matches(now_time, target_time):
                        try:
                            from datetime import datetime as _dt, date as _date
                            now_dt = _dt.combine(_date.today(), now_time)
                            tgt_dt = _dt.combine(_date.today(), target_time)
                            delta = abs((now_dt - tgt_dt).total_seconds())
                            return delta <= 60
                        except Exception:
                            return now_time.hour == target_time.hour and now_time.minute == target_time.minute
                    # Match based on frequency
                    if frequency == 'once':
                        if not schedule_date:
                            return False
                        if (localized_now.date() == schedule_date) and _time_matches(localized_now.time(), schedule_time):
                            return True
                        return False
                    elif frequency == 'daily':
                        return _time_matches(localized_now.time(), schedule_time)
                    elif frequency == 'weekly':
                        if not schedule_date:
                            return False
                        # Trigger on the weekday of schedule_start_date at the given time
                        if localized_now.weekday() != schedule_date.weekday():
                            return False
                        return _time_matches(localized_now.time(), schedule_time)
                    elif frequency == 'monthly':
                        if not schedule_date:
                            return False
                        if localized_now.day != schedule_date.day:
                            return False
                        return _time_matches(localized_now.time(), schedule_time)
                    elif frequency == 'yearly':
                        if not schedule_date:
                            return False
                        if (localized_now.month != schedule_date.month) or (localized_now.day != schedule_date.day):
                            return False
                        return _time_matches(localized_now.time(), schedule_time)
                    else:
                        logger.debug(f"Unknown schedule frequency: {frequency}")
                        return False
                except Exception as tz_err:
                    logger.error(f"Error evaluating scheduled when node timezone: {tz_err}")
                    return False
                
            elif when_node_obj.when_type == 'add_tag':
                # Two modes for add_tag:
                # 1. TAG_ADDED event: check if the added tag matches
                # 2. MESSAGE_RECEIVED event: filter by user tags (frontend "by tag" feature)
                
                if event_type == 'TAG_ADDED':
                    # Original behavior: trigger when a specific tag is added
                    if when_node_obj.tags:
                        added_tag = event_data.get('tag_name', '')
                        if added_tag not in when_node_obj.tags:
                            logger.debug(f"Added tag '{added_tag}' not in required tags: {when_node_obj.tags}")
                            return False
                
                elif event_type == 'MESSAGE_RECEIVED':
                    # New behavior: filter by user tags when message is received
                    if when_node_obj.tags:
                        user_tags = context.get('user', {}).get('tags', [])
                        
                        # If tags not in context, try to fetch from database
                        if not user_tags and context.get('event', {}).get('user_id'):
                            try:
                                from workflow.settings_adapters import get_model_class
                                UserModel = get_model_class('USER')
                                user_id = context.get('event', {}).get('user_id')
                                user = UserModel.objects.get(id=user_id)
                                
                                # Try different tag field names
                                try:
                                    user_tags = list(user.tag.values_list('name', flat=True))
                                except:
                                    try:
                                        user_tags = list(user.tags.values_list('name', flat=True))
                                    except:
                                        user_tags = []
                            except Exception as e:
                                logger.warning(f"Could not load user tags for add_tag filtering: {e}")
                                user_tags = []
                        
                        # Check if user has at least one of the required tags
                        has_required_tag = any(tag in user_tags for tag in when_node_obj.tags)
                        
                        if not has_required_tag:
                            logger.debug(f"🏷️  User tags {user_tags} don't match required tags: {when_node_obj.tags}")
                            return False
                        else:
                            logger.info(f"✅ 🏷️  User has required tag from: {when_node_obj.tags} (add_tag as filter)")
                    
                    # Also check keywords if configured (just like receive_message)
                    if when_node_obj.keywords:
                        message_content = event_data.get('content', '').lower()
                        if not any(keyword.lower() in message_content for keyword in when_node_obj.keywords):
                            logger.debug(f"🏷️  Message content '{message_content}' doesn't contain any keywords: {when_node_obj.keywords}")
                            return False
                    
                    # Also check channels if configured
                    if when_node_obj.channels and 'all' not in when_node_obj.channels:
                        source = context.get('user', {}).get('source', '')
                        if source not in when_node_obj.channels:
                            logger.debug(f"🏷️  User source '{source}' not in allowed channels: {when_node_obj.channels}")
                            return False
            
            # For new_customer, the event type check above is sufficient
            
            return True
        
        except Exception as e:
            logger.error(f"Error checking when node trigger: {e}")
            return False
    
    def _execute_node_chain(self, node: WorkflowNode, context: Dict[str, Any], 
                           execution: WorkflowExecution):
        """
        Execute a chain of connected nodes.
        """
        visited_nodes = set()
        nodes_to_process = [(node, context.copy())]
        
        while nodes_to_process:
            current_node, current_context = nodes_to_process.pop(0)
            
            # Avoid infinite loops
            if current_node.id in visited_nodes:
                continue
            visited_nodes.add(current_node.id)
            
            try:
                # Execute current node
                result = self._execute_single_node(current_node, current_context, execution)
                
                # If waiting for response, pause execution
                if result.waiting_for_response:
                    # Persist waiting state details into execution context
                    try:
                        execution.context_data = execution.context_data or {}
                        if result.data:
                            execution.context_data.update(result.data)
                        execution.save(update_fields=['context_data'])
                    except Exception as se:
                        logger.warning(f"Failed to persist waiting state: {se}")
                    execution.status = 'WAITING'
                    execution.save(update_fields=['status'])
                    return
                
                # If node failed and is required, stop execution
                if not result.success:
                    logger.error(f"Node {current_node.id} failed: {result.error}")
                    continue
                
                # Update context with node results
                if result.data:
                    current_context.update(result.data)
                
                # Find next nodes to execute
                next_nodes = self._get_next_nodes(current_node, result, current_context)
                
                # Add next nodes to processing queue
                for next_node in next_nodes:
                    nodes_to_process.append((next_node, current_context.copy()))
            except Exception as e:
                logger.error(f"Error executing node {current_node.id}: {e}")
                continue
        
        # Log chain completion but don't re-enable AI here (will be done when workflow truly completes)
        if not nodes_to_process:
            conversation_id = context.get('event', {}).get('conversation_id')
            logger.info(f"🔗 Node chain completed for execution #{execution.id}, conversation {conversation_id}, status: {execution.status}")
            logger.info(f"🔗 Waiting for full workflow completion before re-enabling AI")
    
    def _execute_single_node(self, node: WorkflowNode, context: Dict[str, Any], 
                            execution: WorkflowExecution) -> NodeExecutionResult:
        """
        Execute a single workflow node.
        """
        try:
            logger.info(f"Executing node {node.id} ({node.node_type}): {node.title}")
            
            if node.node_type == 'when':
                # When nodes just pass through - they've already been triggered
                return NodeExecutionResult(success=True)
            
            elif node.node_type == 'condition':
                return self._execute_condition_node(node, context)
            
            elif node.node_type == 'action':
                result = self._execute_action_node(node, context, execution)
                try:
                    # If this action sent a message, mirror the action-based broadcasting/answering
                    if result.success and 'message_sent' in (result.data or {}):
                        from message.models import Message, Conversation
                        from message.serializers import WSMessageSerializer
                        from channels.layers import get_channel_layer
                        from asgiref.sync import async_to_sync
                        from message.services.telegram_service import TelegramService
                        from message.services.instagram_service import InstagramService
                        conversation_id = context.get('event', {}).get('conversation_id')
                        if conversation_id:
                            # Mark previous customer messages answered to prevent AI
                            Message.objects.filter(
                                conversation_id=conversation_id,
                                type='customer',
                                is_answered=False
                            ).update(is_answered=True)
                            # Try to load last created marketing/support message for serialization
                            msg = Message.objects.filter(conversation_id=conversation_id).order_by('-created_at').first()
                            # Send to external channel if possible
                            try:
                                if msg:
                                    conversation = Conversation.objects.select_related('customer').get(id=conversation_id)
                                    customer = conversation.customer
                                    if getattr(customer, 'source', '') == 'telegram':
                                        svc = TelegramService.get_service_for_conversation(conversation)
                                        if svc:
                                            svc.send_message_to_customer(customer, msg.content)
                                    elif getattr(customer, 'source', '') == 'instagram':
                                        svc = InstagramService.get_service_for_conversation(conversation)
                                        if svc:
                                            svc.send_message_to_customer(customer, msg.content)
                            except Exception as se:
                                logger.warning(f"Failed to send external channel message (node-based): {se}")
                            channel_layer = get_channel_layer()
                            if channel_layer and msg:
                                async_to_sync(channel_layer.group_send)(
                                    f"chat_{conversation_id}",
                                    {
                                        'type': 'chat_message',
                                        'message': WSMessageSerializer(msg).data,
                                        'external_send_result': {}
                                    }
                                )
                except Exception as e:
                    logger.warning(f"Failed node-based broadcast: {e}")
                return result
            
            elif node.node_type == 'waiting':
                return self._execute_waiting_node(node, context, execution)
            
            else:
                return NodeExecutionResult(success=False, error=f"Unknown node type: {node.node_type}")
        
        except Exception as e:
            logger.error(f"Error executing node {node.id}: {e}")
            return NodeExecutionResult(success=False, error=str(e))
    
    def _execute_condition_node(self, node: WorkflowNode, context: Dict[str, Any]) -> NodeExecutionResult:
        """Execute a condition node."""
        try:
            condition_node = ConditionNode.objects.get(id=node.id)
            
            # Evaluate conditions
            operator = getattr(condition_node, 'combination_operator', 'and')
            result = evaluate_condition_group(
                condition_node.conditions,
                operator,
                context
            )
            
            return NodeExecutionResult(
                success=True,
                data={'condition_result': result, 'condition_met': result}
            )
        
        except Exception as e:
            logger.error(f"Error executing condition node {node.id}: {e}")
            return NodeExecutionResult(success=False, error=str(e))
    
    def _execute_action_node(self, node: WorkflowNode, context: Dict[str, Any], 
                            execution: WorkflowExecution) -> NodeExecutionResult:
        """Execute an action node."""
        try:
            action_node = ActionNode.objects.get(id=node.id)
            
            if action_node.action_type == 'send_message':
                # Mark previous customer messages as answered to prevent AI duplicate
                try:
                    from workflow.settings_adapters import get_model_class, get_field_name
                    MessageModel = get_model_class('MESSAGE')
                    conversation_id = context.get('event', {}).get('conversation_id')
                    if conversation_id:
                        sender_field = get_field_name('MESSAGE', 'SENDER_TYPE_FIELD')
                        sender_customer = self.sender_types.get('CUSTOMER', 'customer')
                        filter_kwargs = {
                            'conversation_id': conversation_id,
                            'is_answered': False,
                        }
                        # Add sender type filter if such field exists
                        try:
                            filter_kwargs[sender_field] = sender_customer
                        except Exception:
                            pass
                        MessageModel.objects.filter(**filter_kwargs).update(is_answered=True)
                except Exception as mark_err:
                    logger.warning(f"Failed to mark customer messages answered before workflow send: {mark_err}")
                return self._execute_send_message_action(action_node, context)
            
            elif action_node.action_type == 'delay':
                return self._execute_delay_action(action_node, context, execution)
            
            elif action_node.action_type == 'redirect_conversation':
                return self._execute_redirect_action(action_node, context)
            
            elif action_node.action_type == 'add_tag':
                return self._execute_add_tag_action(action_node, context)
            
            elif action_node.action_type == 'remove_tag':
                return self._execute_remove_tag_action(action_node, context)
            
            elif action_node.action_type == 'transfer_to_human':
                return self._execute_transfer_to_human_action(action_node, context)
            
            elif action_node.action_type == 'webhook':
                return self._execute_webhook_action(action_node, context)
            
            elif action_node.action_type == 'custom_code':
                return self._execute_custom_code_action(action_node, context)
            
            elif action_node.action_type == 'control_ai_response':
                return self._execute_control_ai_response_action(action_node, context)
            
            elif action_node.action_type == 'update_ai_context':
                return self._execute_update_ai_context_action(action_node, context)
            
            else:
                return NodeExecutionResult(success=False, error=f"Unknown action type: {action_node.action_type}")
        
        except Exception as e:
            logger.error(f"Error executing action node {node.id}: {e}")
            return NodeExecutionResult(success=False, error=str(e))
    
    def _execute_waiting_node(self, node: WorkflowNode, context: Dict[str, Any], 
                             execution: WorkflowExecution) -> NodeExecutionResult:
        """Execute a waiting node."""
        try:
            waiting_node = WaitingNode.objects.get(id=node.id)
            conversation_id = context.get('event', {}).get('conversation_id')
            
            logger.info(f"🕐 [WaitingNode {waiting_node.id}] ===============================")
            logger.info(f"🕐 [WaitingNode {waiting_node.id}] Starting execution: '{waiting_node.title}'")
            logger.info(f"🕐 [WaitingNode {waiting_node.id}] Configuration:")
            logger.info(f"🕐 [WaitingNode {waiting_node.id}]   - storage_type: '{waiting_node.storage_type}'")
            logger.info(f"🕐 [WaitingNode {waiting_node.id}]   - allowed_errors: {waiting_node.allowed_errors}")
            logger.info(f"🕐 [WaitingNode {waiting_node.id}]   - exit_keywords: {waiting_node.exit_keywords}")
            logger.info(f"🕐 [WaitingNode {waiting_node.id}]   - conversation_id: {conversation_id}")
            logger.info(f"🕐 [WaitingNode {waiting_node.id}]   - execution_id: {execution.id}")

            # Allow reuse of WaitingNode on subsequent runs; do not skip based on prior conversation completions
            
            # Send message to customer asking for response
            customer_message = substitute_template_placeholders(waiting_node.customer_message, context)
            logger.info(f"🕐 [WaitingNode {waiting_node.id}] Prepared customer message: '{customer_message}'")
            
            # Send the message
            logger.info(f"🕐 [WaitingNode {waiting_node.id}] Sending customer message...")
            send_result = self._send_customer_message(customer_message, context)
            logger.info(f"🕐 [WaitingNode {waiting_node.id}] Message sent result: {send_result}")

            # Broadcast to websocket and ensure external channels mirror (similar to action send)
            logger.info(f"🕐 [WaitingNode {waiting_node.id}] Broadcasting message via websocket and external channels...")
            try:
                from message.models import Message, Conversation
                from message.serializers import WSMessageSerializer
                from channels.layers import get_channel_layer
                from asgiref.sync import async_to_sync
                from message.services.telegram_service import TelegramService
                from message.services.instagram_service import InstagramService
                conversation_id = context.get('event', {}).get('conversation_id')
                if conversation_id:
                    # Mark previous customer messages answered to prevent AI auto-reply
                    marked_count = Message.objects.filter(
                        conversation_id=conversation_id,
                        type='customer',
                        is_answered=False
                    ).update(is_answered=True)
                    logger.info(f"🕐 [WaitingNode {waiting_node.id}] Marked {marked_count} previous customer messages as answered")

                    # Try to load the message we just created for broadcast
                    msg = None
                    try:
                        message_id = (send_result or {}).get('message_id')
                        logger.info(f"🕐 [WaitingNode {waiting_node.id}] Looking for message to broadcast, message_id: {message_id}")
                        if message_id:
                            msg = Message.objects.filter(id=message_id).first()
                        if not msg:
                            msg = Message.objects.filter(conversation_id=conversation_id).order_by('-created_at').first()
                        logger.info(f"🕐 [WaitingNode {waiting_node.id}] Found message for broadcast: {msg.id if msg else 'None'}")
                    except Exception as e:
                        logger.warning(f"🕐 [WaitingNode {waiting_node.id}] Error finding message for broadcast: {e}")
                        msg = Message.objects.filter(conversation_id=conversation_id).order_by('-created_at').first()

                    # Ensure external channel send as a fallback (usually already done in _send_customer_message)
                    try:
                        if msg:
                            conversation = Conversation.objects.select_related('customer').get(id=conversation_id)
                            customer = conversation.customer
                            customer_source = getattr(customer, 'source', '')
                            logger.info(f"🕐 [WaitingNode {waiting_node.id}] Sending to external channel: {customer_source}")
                            if customer_source == 'telegram':
                                svc = TelegramService.get_service_for_conversation(conversation)
                                if svc:
                                    svc.send_message_to_customer(customer, msg.content)
                                    logger.info(f"🕐 [WaitingNode {waiting_node.id}] ✅ Sent via Telegram")
                                else:
                                    logger.warning(f"🕐 [WaitingNode {waiting_node.id}] ❌ No Telegram service available")
                            elif customer_source == 'instagram':
                                svc = InstagramService.get_service_for_conversation(conversation)
                                if svc:
                                    svc.send_message_to_customer(customer, msg.content)
                                    logger.info(f"🕐 [WaitingNode {waiting_node.id}] ✅ Sent via Instagram")
                                else:
                                    logger.warning(f"🕐 [WaitingNode {waiting_node.id}] ❌ No Instagram service available")
                            else:
                                logger.info(f"🕐 [WaitingNode {waiting_node.id}] No external channel needed for source: {customer_source}")
                        else:
                            logger.warning(f"🕐 [WaitingNode {waiting_node.id}] No message found for external channel send")
                    except Exception as se:
                        logger.warning(f"🕐 [WaitingNode {waiting_node.id}] Failed to send external channel message: {se}")

                    # Broadcast via websockets
                    try:
                        channel_layer = get_channel_layer()
                        if channel_layer and msg:
                            logger.info(f"🕐 [WaitingNode {waiting_node.id}] Broadcasting via WebSocket to chat_{conversation_id}")
                            async_to_sync(channel_layer.group_send)(
                                f"chat_{conversation_id}",
                                {
                                    'type': 'chat_message',
                                    'message': WSMessageSerializer(msg).data,
                                    'external_send_result': send_result or {}
                                }
                            )
                            logger.info(f"🕐 [WaitingNode {waiting_node.id}] ✅ WebSocket broadcast completed")
                        else:
                            logger.warning(f"🕐 [WaitingNode {waiting_node.id}] ❌ No channel layer or message for WebSocket broadcast")
                    except Exception as wse:
                        logger.warning(f"🕐 [WaitingNode {waiting_node.id}] Failed WebSocket broadcast: {wse}")
            except Exception as e:
                logger.warning(f"🕐 [WaitingNode {waiting_node.id}] Failed waiting-node broadcast setup: {e}")

            # Disable AI auto-response while waiting on this conversation
            logger.info(f"🕐 [WaitingNode {waiting_node.id}] Disabling AI auto-response for conversation...")
            try:
                from django.core.cache import cache
                conversation_id = context.get('event', {}).get('conversation_id')
                if conversation_id:
                    ai_control_key = f"ai_control_{conversation_id}"
                    cache.set(ai_control_key, {'ai_enabled': False}, timeout=86400)
                    logger.info(f"🕐 [WaitingNode {waiting_node.id}] ✅ AI disabled for conversation {conversation_id}")
                else:
                    logger.warning(f"🕐 [WaitingNode {waiting_node.id}] ❌ No conversation_id to disable AI")
            except Exception as e:
                logger.warning(f"🕐 [WaitingNode {waiting_node.id}] Failed to disable AI during waiting: {e}")
            
            # Mark execution as waiting
            logger.info(f"🕐 [WaitingNode {waiting_node.id}] Marking execution as WAITING for user response...")
            result = NodeExecutionResult(
                success=True,
                waiting_for_response=True,
                data={
                    'waiting_node_id': str(waiting_node.id),
                    'message_sent': customer_message
                }
            )
            logger.info(f"🕐 [WaitingNode {waiting_node.id}] ✅ Execution marked as waiting")
            # Schedule timeout if enabled
            try:
                if getattr(waiting_node, 'response_time_limit_enabled', False):
                    amount = int(getattr(waiting_node, 'response_timeout_amount', 0) or 0)
                    unit = getattr(waiting_node, 'response_timeout_unit', 'minutes')
                    timeout_seconds = amount
                    if unit == 'minutes':
                        timeout_seconds *= 60
                    elif unit == 'hours':
                        timeout_seconds *= 3600
                    elif unit == 'days':
                        timeout_seconds *= 86400
                    if timeout_seconds > 0:
                        logger.info(f"🕐 [WaitingNode {waiting_node.id}] Scheduling timeout: {amount} {unit} ({timeout_seconds} seconds)")
                        from workflow.tasks import waiting_node_timeout
                        waiting_node_timeout.apply_async(
                            args=[execution.id, str(waiting_node.id)],
                            countdown=timeout_seconds
                        )
                        logger.info(f"🕐 [WaitingNode {waiting_node.id}] ✅ Timeout scheduled for execution #{execution.id}")
                    else:
                        logger.info(f"🕐 [WaitingNode {waiting_node.id}] Timeout enabled but amount is 0 - no timeout scheduled")
                else:
                    logger.info(f"🕐 [WaitingNode {waiting_node.id}] Timeout is disabled")
            except Exception as te:
                logger.error(f"🕐 [WaitingNode {waiting_node.id}] Error scheduling timeout: {te}")

            logger.info(f"🕐 [WaitingNode {waiting_node.id}] ✅ WaitingNode execution completed successfully")
            logger.info(f"🕐 [WaitingNode {waiting_node.id}] ===============================")
            return result
        
        except Exception as e:
            logger.error(f"🕐 [WaitingNode {node.id}] ❌ Error executing waiting node: {e}")
            logger.info(f"🕐 [WaitingNode {node.id}] ===============================")
            return NodeExecutionResult(success=False, error=str(e))
    
    def _execute_send_message_action(self, action_node: ActionNode, context: Dict[str, Any]) -> NodeExecutionResult:
        """Execute send message action."""
        try:
            message_content = substitute_template_placeholders(action_node.message_content, context)
            
            if not message_content:
                return NodeExecutionResult(success=False, error="Message content is required")
            
            # Send the message
            # Ensure conversation exists; if not, create one for the owner and customer
            if not context.get('event', {}).get('conversation_id'):
                try:
                    from workflow.settings_adapters import get_model_class, get_conversation_status_values
                    ConversationModel = get_model_class('CONVERSATION')
                    user_id = context.get('event', {}).get('user_id')
                    if not user_id:
                        return NodeExecutionResult(success=False, error="User ID is required to create conversation")
                    owner_user = getattr(action_node.workflow, 'created_by', None)
                    if not owner_user:
                        return NodeExecutionResult(success=False, error="Workflow owner not found for conversation creation")
                    source = context.get('event', {}).get('data', {}).get('source') or ''
                    status_values = get_conversation_status_values()
                    defaults = {
                        'source': source or 'unknown',
                        'status': status_values.get('ACTIVE', 'active')
                    }
                    conversation, _ = ConversationModel.objects.get_or_create(
                        user=owner_user,
                        customer_id=user_id,
                        defaults=defaults
                    )
                    # inject conversation_id back into context
                    context.setdefault('event', {})['conversation_id'] = str(conversation.id)
                    logger.info(f"[NodeWorkflow] Created conversation {conversation.id} for user {user_id} to send message action")
                except Exception as ce:
                    return NodeExecutionResult(success=False, error=f"Failed to ensure conversation: {ce}")
            
            result = self._send_customer_message(message_content, context)
            
            return NodeExecutionResult(
                success=True,
                data={
                    'message_sent': message_content,
                    'channel_result': result
                }
            )
        
        except Exception as e:
            return NodeExecutionResult(success=False, error=str(e))
    
    def _execute_delay_action(self, action_node: ActionNode, context: Dict[str, Any], execution: WorkflowExecution) -> NodeExecutionResult:
        """Execute delay action."""
        try:
            delay_amount = action_node.delay_amount
            delay_unit = action_node.delay_unit
            
            # Convert to seconds
            delay_seconds = delay_amount
            if delay_unit == 'minutes':
                delay_seconds *= 60
            elif delay_unit == 'hours':
                delay_seconds *= 3600
            elif delay_unit == 'days':
                delay_seconds *= 86400
            
            # Schedule resume of node-based workflow after delay
            try:
                from workflow.tasks import resume_node_workflow_after_delay
                resume_node_workflow_after_delay.apply_async(
                    args=[execution.id, str(action_node.id)],
                    countdown=delay_seconds
                )
                logger.info(f"Scheduled resume of node workflow execution #{execution.id} after {delay_seconds}s")
            except Exception as se:
                logger.error(f"Failed to schedule node workflow resume: {se}")
            
            # Return waiting result so execution pauses
            return NodeExecutionResult(success=True, waiting_for_response=True, data={'delay_applied': delay_seconds})
        
        except Exception as e:
            return NodeExecutionResult(success=False, error=str(e))
    
    def _execute_redirect_action(self, action_node: ActionNode, context: Dict[str, Any]) -> NodeExecutionResult:
        """
        Execute conversation redirect action.
        
        Redirects conversation to AI or Support based on destination:
        - 'ai': Sets status to 'active', enables AI
        - Other destinations: Sets status to 'support_active', disables AI
        """
        try:
            destination = action_node.redirect_destination
            conversation_id = context.get('event', {}).get('conversation_id')
            
            if not conversation_id:
                return NodeExecutionResult(success=False, error="No conversation ID found")
            
            # Import required modules
            from workflow.settings_adapters import (
                get_model_class,
                get_field_name,
                get_conversation_status_values,
            )
            
            # Get conversation and status configuration
            ConversationModel = get_model_class('CONVERSATION')
            status_field = get_field_name('CONVERSATION', 'STATUS_FIELD')
            status_values = get_conversation_status_values()
            conversation = ConversationModel.objects.select_related('user').get(id=conversation_id)
            old_status = getattr(conversation, status_field)
            
            # Determine new status and AI control based on destination
            if destination == 'ai':
                # Redirect to AI: set status to 'active', enable AI
                new_status = status_values.get('ACTIVE', 'active')
                ai_enabled = True
                logger.info(f"[Redirect to AI] Conversation {conversation_id}: will enable AI, set status to '{new_status}'")
            else:
                # Redirect to Support/Sales/etc: set status to 'support_active', disable AI
                new_status = status_values.get('SUPPORT_ACTIVE', 'support_active')
                ai_enabled = False
                logger.info(f"[Redirect to {destination}] Conversation {conversation_id}: will disable AI, set status to '{new_status}'")
            
            # Update conversation status
            setattr(conversation, status_field, new_status)
            try:
                conversation.save(update_fields=[status_field, get_field_name('CONVERSATION', 'UPDATED_AT_FIELD')])
            except Exception:
                conversation.save()
            
            logger.info(f"✓ Conversation {conversation_id} status updated: {old_status} -> {new_status}")
            
            # Update AI control in cache with error handling
            try:
                from django.core.cache import cache
                ai_control_key = f"ai_control_{conversation_id}"
                cache.set(ai_control_key, {'ai_enabled': ai_enabled}, timeout=86400)
                logger.info(f"✓ AI control cache set: conversation={conversation_id}, ai_enabled={ai_enabled}")
            except Exception as cache_err:
                logger.warning(f"⚠ Failed to set AI control cache for conversation {conversation_id}: {cache_err}")
                logger.warning(f"  Conversation status was still updated successfully. AI behavior may be inconsistent.")
                # Continue execution - status change is more important than cache
            
            # Broadcast conversation update to WebSocket clients
            try:
                from channels.layers import get_channel_layer
                from asgiref.sync import async_to_sync
                user_group = f"user_{conversation.user.id}_conversations"
                channel_layer = get_channel_layer()
                if channel_layer:
                    async_to_sync(channel_layer.group_send)(user_group, {
                        'type': 'conversation_updated',
                        'conversation_id': str(conversation_id)
                    })
                    logger.info(f"✓ Broadcast sent to user group: {user_group}")
            except Exception as broadcast_err:
                logger.warning(f"⚠ Failed to broadcast conversation redirect for {conversation_id}: {broadcast_err}")
                # Continue execution - broadcast failure is not critical
            
            # Final success log
            logger.info(
                f"✅ [Redirect Complete] Conversation {conversation_id} redirected to '{destination}': "
                f"status {old_status}->{new_status}, AI={'enabled' if ai_enabled else 'disabled'}"
            )
            
            return NodeExecutionResult(
                success=True,
                data={
                    'redirected_to': destination,
                    'old_status': old_status,
                    'new_status': new_status,
                    'ai_enabled': ai_enabled
                }
            )
        
        except Exception as e:
            logger.error(f"❌ Error executing redirect action for conversation {conversation_id}: {e}", exc_info=True)
            return NodeExecutionResult(success=False, error=str(e))


    def _execute_add_tag_action(self, action_node: ActionNode, context: Dict[str, Any]) -> NodeExecutionResult:
        """Execute add tag action."""
        try:
            tag_name = action_node.tag_name
            user_id = context.get('event', {}).get('user_id')
            
            if not user_id or not tag_name:
                return NodeExecutionResult(success=False, error="User ID and tag name are required")
            
            UserModel = get_model_class('USER')
            user = UserModel.objects.get(id=user_id)
            success = add_user_tag(user, tag_name)
            
            return NodeExecutionResult(
                success=True,
                data={'tag_added': tag_name, 'success': success}
            )
        
        except Exception as e:
            return NodeExecutionResult(success=False, error=str(e))
    
    def _execute_remove_tag_action(self, action_node: ActionNode, context: Dict[str, Any]) -> NodeExecutionResult:
        """Execute remove tag action."""
        try:
            tag_name = action_node.tag_name
            user_id = context.get('event', {}).get('user_id')
            
            if not user_id or not tag_name:
                return NodeExecutionResult(success=False, error="User ID and tag name are required")
            
            UserModel = get_model_class('USER')
            user = UserModel.objects.get(id=user_id)
            success = remove_user_tag(user, tag_name)
            
            return NodeExecutionResult(
                success=True,
                data={'tag_removed': tag_name, 'success': success}
            )
        
        except Exception as e:
            return NodeExecutionResult(success=False, error=str(e))
    
    def _execute_transfer_to_human_action(self, action_node: ActionNode, context: Dict[str, Any]) -> NodeExecutionResult:
        """Execute transfer to human action."""
        try:
            conversation_id = context.get('event', {}).get('conversation_id')
            
            if not conversation_id:
                return NodeExecutionResult(success=False, error="No conversation ID found")
            
            # Set conversation status to indicate human transfer needed
            # This would integrate with your conversation management system
            logger.info(f"Transferring conversation {conversation_id} to human operator")
            
            return NodeExecutionResult(
                success=True,
                data={'transferred_to_human': True}
            )
        
        except Exception as e:
            return NodeExecutionResult(success=False, error=str(e))
    
    def _execute_webhook_action(self, action_node: ActionNode, context: Dict[str, Any]) -> NodeExecutionResult:
        """Execute webhook action."""
        try:
            import requests
            
            url = substitute_template_placeholders(action_node.webhook_url, context)
            method = action_node.webhook_method
            headers = action_node.webhook_headers
            payload = substitute_template_placeholders(action_node.webhook_payload, context)
            
            if not url:
                return NodeExecutionResult(success=False, error="Webhook URL is required")
            
            response = requests.request(
                method=method,
                url=url,
                headers=headers,
                json=payload,
                timeout=30
            )
            
            response.raise_for_status()
            
            return NodeExecutionResult(
                success=True,
                data={
                    'webhook_response': response.status_code,
                    'webhook_url': url
                }
            )
        
        except Exception as e:
            return NodeExecutionResult(success=False, error=str(e))
    
    def _execute_custom_code_action(self, action_node: ActionNode, context: Dict[str, Any]) -> NodeExecutionResult:
        """Execute custom code action."""
        try:
            code = action_node.custom_code
            if not code:
                return NodeExecutionResult(success=False, error="Custom code is required")
            
            # Execute custom code in restricted environment
            safe_globals = {
                '__builtins__': {
                    'len': len, 'str': str, 'int': int, 'float': float, 'bool': bool,
                    'list': list, 'dict': dict, 'tuple': tuple, 'set': set,
                    'abs': abs, 'min': min, 'max': max, 'sum': sum, 'round': round,
                    'isinstance': isinstance, 'type': type, 'hasattr': hasattr, 'getattr': getattr,
                },
                'context': context,
            }
            
            safe_locals = {'result': {}}
            exec(code, safe_globals, safe_locals)
            
            return NodeExecutionResult(
                success=True,
                data=safe_locals.get('result', {})
            )
        
        except Exception as e:
            return NodeExecutionResult(success=False, error=str(e))
    
    def _send_customer_message(self, message_content: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Send message to customer via their preferred channel."""
        try:
            conversation_id = context.get('event', {}).get('conversation_id')
            user_id = context.get('event', {}).get('user_id')
            
            if not conversation_id or not user_id:
                raise ValueError("Conversation ID and User ID are required")
            
            # Get models
            MessageModel = get_model_class('MESSAGE')
            ConversationModel = get_model_class('CONVERSATION')
            UserModel = get_model_class('USER')
            
            # Get conversation and user
            conversation = ConversationModel.objects.get(id=conversation_id)
            user = UserModel.objects.get(id=user_id)
            
            # Create message in database
            content_field = get_field_name('MESSAGE', 'CONTENT_FIELD')
            sender_type_field = get_field_name('MESSAGE', 'SENDER_TYPE_FIELD')
            
            message_data = {
                get_field_name('MESSAGE', 'CONVERSATION_FIELD'): conversation,
                get_field_name('MESSAGE', 'CUSTOMER_FIELD'): user,
                content_field: message_content,
                sender_type_field: self.sender_types['MARKETING'],
            }
            
            message = MessageModel.objects.create(**message_data)
            
            result = {
                'message_id': str(message.id),
                'content': message_content,
                'sent_to_channel': False
            }
            
            # Try to send to external channels
            source = getattr(user, get_field_name('USER', 'SOURCE_FIELD'), '')
            source_id = getattr(user, get_field_name('USER', 'SOURCE_ID_FIELD'), '')
            
            if source == 'telegram' and source_id and INTEGRATION_SETTINGS.get('TELEGRAM_BOT_TOKEN'):
                try:
                    self._send_telegram_message(source_id, message_content)
                    result['sent_to_channel'] = True
                    result['channel'] = 'telegram'
                except Exception as e:
                    logger.warning(f"Failed to send Telegram message: {e}")
            
            elif source == 'instagram' and source_id and INTEGRATION_SETTINGS.get('N8N_WEBHOOK_URL'):
                try:
                    self._send_instagram_message(source_id, message_content)
                    result['sent_to_channel'] = True
                    result['channel'] = 'instagram'
                except Exception as e:
                    logger.warning(f"Failed to send Instagram message: {e}")
            
            return result
        
        except Exception as e:
            logger.error(f"Error sending customer message: {e}")
            raise
    
    def _send_telegram_message(self, chat_id: str, message: str):
        """Send message via Telegram Bot API"""
        import requests
        
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
        import requests
        
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
    
    def _get_next_nodes(self, current_node: WorkflowNode, result: NodeExecutionResult, 
                       context: Dict[str, Any]) -> List[WorkflowNode]:
        """
        Get the next nodes to execute based on current node result.
        """
        try:
            # Get outgoing connections from current node
            connections = current_node.outgoing_connections.all()
            next_nodes = []
            
            is_skipped = bool((result.data or {}).get('skipped'))
            for connection in connections:
                should_follow = False
                
                # Determine if this connection should be followed
                if connection.connection_type == 'success' and result.success:
                    should_follow = True
                elif connection.connection_type == 'failure' and not result.success:
                    should_follow = True
                elif connection.connection_type == 'timeout':
                    # Handle timeout conditions
                    should_follow = False  # Would be set by timeout handler
                elif connection.connection_type == 'skip':
                    # Follow skip connections only when node processing indicated skip
                    should_follow = bool((result.data or {}).get('skipped'))
                
                # If this was an explicit skip, do not follow generic failure branches
                if is_skipped and connection.connection_type == 'failure':
                    should_follow = False
                
                # For condition nodes, check the condition result
                if (current_node.node_type == 'condition' and 
                    connection.connection_type == 'success'):
                    condition_met = result.data.get('condition_met', False)
                    should_follow = condition_met
                elif (current_node.node_type == 'condition' and 
                      connection.connection_type == 'failure'):
                    condition_met = result.data.get('condition_met', False)
                    should_follow = not condition_met
                
                # Check any additional connection conditions
                if should_follow and connection.condition:
                    try:
                        should_follow = evaluate_conditions(connection.condition, context)
                    except Exception as e:
                        logger.error(f"Error evaluating connection condition: {e}")
                        should_follow = False
                
                if should_follow:
                    next_nodes.append(connection.target_node)
            
            return next_nodes
        
        except Exception as e:
            logger.error(f"Error getting next nodes: {e}")
            return []
    
    def process_user_response(self, waiting_node_id: str, user_response: str, 
                             context: Dict[str, Any], execution: WorkflowExecution):
        """
        Process user response to a waiting node and continue workflow execution.
        """
        try:
            waiting_node = WaitingNode.objects.get(id=waiting_node_id)
            
            logger.info(f"📥 [WaitingResponse {waiting_node_id}] ===============================")
            logger.info(f"📥 [WaitingResponse {waiting_node_id}] Processing user response: '{user_response}'")
            logger.info(f"📥 [WaitingResponse {waiting_node_id}] Node: '{waiting_node.title}' (storage_type: {waiting_node.storage_type})")
            logger.info(f"📥 [WaitingResponse {waiting_node_id}] Execution: {execution.id} (status: {execution.status})")
            
            # Allow reuse: do not ignore inputs based on prior conversation completions
            
            # Idempotency/locking to prevent double-processing in race conditions
            try:
                from django.core.cache import cache
                lock_key = f"waiting_lock_{execution.id}_{waiting_node_id}"
                done_key = f"waiting_done_{execution.id}_{waiting_node_id}"
                if cache.get(done_key):
                    logger.info(f"Waiting node {waiting_node_id} already completed for execution {execution.id}")
                    return
                # Acquire lock (cache.add returns True only if key did not exist)
                if not cache.add(lock_key, True, timeout=60):
                    logger.info(f"Waiting node {waiting_node_id} is being processed by another worker; skipping")
                    return
            except Exception:
                cache = None

            # Ignore if execution is not actually waiting
            if getattr(execution, 'status', '') != 'WAITING':
                logger.info(f"Execution {execution.id} is not WAITING; ignoring user response")
                return

            # Ignore if the waiting node in context does not match
            ctx_waiting_id = (execution.context_data or {}).get('waiting_node_id')
            if str(ctx_waiting_id) != str(waiting_node_id):
                logger.info(f"Mismatched waiting node (ctx={ctx_waiting_id}, got={waiting_node_id}); ignoring")
                return
            
            # Additional check: ensure this execution is still the active WAITING execution for this conversation
            # In case there are multiple executions, only process the most recent one
            try:
                conversation_id = context.get('event', {}).get('conversation_id')
                if conversation_id:
                    most_recent_waiting = WorkflowExecution.objects.filter(
                        conversation=conversation_id,
                        status='WAITING'
                    ).order_by('-created_at').first()
                    
                    if most_recent_waiting and most_recent_waiting.id != execution.id:
                        logger.warning(f"Execution {execution.id} is not the most recent WAITING execution (most recent: {most_recent_waiting.id}); ignoring")
                        return
            except Exception as e:
                logger.warning(f"Failed to check most recent waiting execution: {e}")

            # Guard against double-processing: if a valid processed response already exists
            try:
                already_processed = UserResponse.objects.filter(
                    waiting_node=waiting_node,
                    workflow_execution=execution,
                    is_valid=True,
                    processed_at__isnull=False
                ).exists()
                if already_processed:
                    logger.info(f"Waiting node {waiting_node_id} already processed for execution {execution.id}; ignoring extra input")
                    return
            except Exception:
                pass

            # Additional check: if conversation is marked as waiting ended recently
            try:
                from django.core.cache import cache as _cache
                conv_id = context.get('event', {}).get('conversation_id')
                if conv_id and _cache.get(f"waiting_ended_{conv_id}"):
                    logger.info(f"Conversation {conv_id} waiting recently ended; ignoring delayed message processing")
                    return
            except Exception:
                pass

            # Normalize response
            response_text = (user_response or '').strip()

            # Check for exit keywords (case-insensitive exact match)
            try:
                exit_list = [str(k).strip().lower() for k in (waiting_node.exit_keywords or [])]
            except Exception:
                exit_list = []

            if response_text.lower() in exit_list:
                logger.info(f"[WaitingNode {waiting_node_id}] Exit keyword detected; closing node as unsuccessful and resuming AI")
                # Record response as processed (skipped)
                user_response_obj = UserResponse.objects.create(
                    waiting_node=waiting_node,
                    workflow_execution=execution,
                    user_id=context.get('event', {}).get('user_id'),
                    conversation_id=context.get('event', {}).get('conversation_id'),
                    response_value=response_text,
                    is_valid=True
                )
                user_response_obj.processed_at = timezone.now()
                user_response_obj.save(update_fields=['processed_at'])

                # Re-enable AI if it was disabled during waiting (exit keywords always re-enable AI)
                try:
                    from django.core.cache import cache
                    conversation_id = context.get('event', {}).get('conversation_id')
                    if conversation_id:
                        ai_control_key = f"ai_control_{conversation_id}"
                        cache.set(ai_control_key, {'ai_enabled': True}, timeout=86400)
                        logger.info(f"[WaitingNode {waiting_node_id}] AI re-enabled for conversation {conversation_id} after exit keyword")
                except Exception:
                    pass

                # Resume execution following skip connections
                execution.status = 'RUNNING'
                # Clear waiting node marker so AI can resume and guards pass
                try:
                    execution.context_data = execution.context_data or {}
                    if 'waiting_node_id' in execution.context_data:
                        del execution.context_data['waiting_node_id']
                except Exception:
                    pass
                execution.save(update_fields=['status', 'context_data'])
                # Mark completion (idempotency flags)
                try:
                    if cache is not None:
                        cache.set(f"waiting_done_{execution.id}_{waiting_node_id}", True, timeout=3600)
                        cache.delete(f"waiting_lock_{execution.id}_{waiting_node_id}")
                    conv_id = context.get('event', {}).get('conversation_id')
                except Exception:
                    pass

                # Don't set waiting_ended flag to prevent AI auto-reactivation
                logger.info(f"[WaitingNode {waiting_node_id}] Exit keyword processed - workflow will continue to next nodes")

                # After exit keyword, proceed to next nodes without AI processing
                logger.info(f"[WaitingNode {waiting_node_id}] Exit keyword detected - proceeding to next workflow nodes without AI processing")

                next_nodes = self._get_next_nodes(
                    waiting_node,
                    # Treat exit as unsuccessful
                    NodeExecutionResult(success=False, error="Exit keyword used"),
                    context
                )
                
                # Check if any of the next nodes are waiting nodes
                if next_nodes:
                    has_waiting_nodes = any(node.node_type == 'waiting' for node in next_nodes)
                    if has_waiting_nodes:
                        logger.info(f"[WaitingNode {waiting_node_id}] Next nodes include waiting nodes - AI will be disabled again by those nodes")
                    else:
                        logger.info(f"[WaitingNode {waiting_node_id}] No waiting nodes in exit chain - AI remains enabled")
                
                for next_node in next_nodes:
                    self._execute_node_chain(next_node, context, execution)
                return

            # Mark triggering customer message as answered to prevent AI from replying to it
            try:
                MessageModel = get_model_class('MESSAGE')
                msg_id = (
                    context.get('event', {}).get('data', {}).get('message_id')
                    or context.get('event', {}).get('message_id')
                )
                if msg_id:
                    MessageModel.objects.filter(id=msg_id).update(is_answered=True)
            except Exception as mark_msg_err:
                logger.warning(f"Failed to mark triggering message answered: {mark_msg_err}")
            
            # Validate user response
            logger.info(f"📥 [WaitingResponse {waiting_node_id}] Starting validation...")
            logger.info(f"📥 [WaitingResponse {waiting_node_id}] About to call _validate_user_response with response: '{response_text}'")
            is_valid, error_message = self._validate_user_response(waiting_node, response_text)
            logger.info(f"📥 [WaitingResponse {waiting_node_id}] Validation result: {'✅ VALID' if is_valid else '❌ INVALID'}")
            if error_message:
                logger.info(f"📥 [WaitingResponse {waiting_node_id}] Validation error message: '{error_message}'")
            
            # Store user response
            logger.info(f"📥 [WaitingResponse {waiting_node_id}] Storing user response in database...")
            user_response_obj = UserResponse.objects.create(
                waiting_node=waiting_node,
                workflow_execution=execution,
                user_id=context.get('event', {}).get('user_id'),
                conversation_id=context.get('event', {}).get('conversation_id'),
                response_value=response_text,
                is_valid=is_valid
            )
            logger.info(f"📥 [WaitingResponse {waiting_node_id}] ✅ UserResponse {user_response_obj.id} created")
            
            if not is_valid:
                logger.info(f"📥 [WaitingResponse {waiting_node_id}] ❌ Response is invalid - handling error case")
                logger.info(f"📥 [WaitingResponse {waiting_node_id}] Error message: '{error_message}'")
                logger.info(f"📥 [WaitingResponse {waiting_node_id}] ENTERING invalid response handling block")
                
                # Handle invalid response - DO NOT UPDATE FIELD
                # Count total invalid attempts for this waiting node within this execution
                try:
                    total_invalid = UserResponse.objects.filter(
                        waiting_node=waiting_node,
                        workflow_execution=execution,
                        is_valid=False
                    ).count()
                    logger.info(f"📥 [WaitingResponse {waiting_node_id}] Total invalid attempts: {total_invalid}")
                except Exception:
                    total_invalid = 1  # Fallback
                    logger.warning(f"📥 [WaitingResponse {waiting_node_id}] Could not count invalid attempts, using fallback: {total_invalid}")
                
                # Persist per-record counter (informational only)
                try:
                    user_response_obj.error_count = total_invalid
                    user_response_obj.save(update_fields=['error_count'])
                except Exception:
                    pass
                
                # Allow exactly 'allowed_errors' wrong attempts; on the next invalid, exit waiting
                allowed = int(getattr(waiting_node, 'allowed_errors', 1) or 1)
                logger.info(f"📥 [WaitingResponse {waiting_node_id}] Invalid attempt #{total_invalid} of {allowed} allowed")
                
                if total_invalid >= allowed:
                    # Exceeded max errors: end node with failure - NO FIELD UPDATE
                    logger.warning(f"📥 [WaitingResponse {waiting_node_id}] ❌ Exceeded max errors ({total_invalid}/{allowed}) - exiting unsuccessfully without field update")
                    # Re-enable AI and clear waiting marker
                    try:
                        from django.core.cache import cache
                        conversation_id = context.get('event', {}).get('conversation_id')
                        if conversation_id:
                            ai_control_key = f"ai_control_{conversation_id}"
                            cache.set(ai_control_key, {'ai_enabled': True}, timeout=86400)
                            logger.info(f"[WaitingNode {waiting_node_id}] AI re-enabled for conversation {conversation_id} (max errors exceeded)")
                    except Exception:
                        pass
                    execution.status = 'RUNNING'
                    try:
                        execution.context_data = execution.context_data or {}
                        if 'waiting_node_id' in execution.context_data:
                            del execution.context_data['waiting_node_id']
                    except Exception:
                        pass
                    execution.save(update_fields=['status', 'context_data'])
                    # Mark completion (idempotency flags) - execution level only
                    try:
                        if cache is not None:
                            cache.set(f"waiting_done_{execution.id}_{waiting_node_id}", True, timeout=3600)
                            cache.delete(f"waiting_lock_{execution.id}_{waiting_node_id}")
                    except Exception:
                        pass
                    # Mark recent waiting end
                    # Don't set waiting_ended flag to prevent AI auto-reactivation
                    logger.info(f"[WaitingNode {waiting_node_id}] Max errors exceeded - workflow will continue to next nodes")
                    # After max errors exceeded, proceed to next nodes without AI processing
                    logger.info(f"[WaitingNode {waiting_node_id}] Max errors exceeded - proceeding to next workflow nodes without AI processing")
                    # Execute next nodes after max errors - continue workflow with failure path
                    logger.info(f"📥 [WaitingResponse {waiting_node_id}] Max errors exceeded - continuing to next nodes with failure result")
                    
                    # Get next nodes to continue workflow after failure
                    failure_result = NodeExecutionResult(
                        success=False,
                        data={'failure_reason': 'max_errors_exceeded', 'error_count': total_invalid}
                    )
                    next_nodes = self._get_next_nodes(waiting_node, failure_result, context)
                    
                    if next_nodes:
                        logger.info(f"📥 [WaitingResponse {waiting_node_id}] Found {len(next_nodes)} next nodes after failure - continuing workflow")
                        
                        # Check if any of the next nodes are waiting nodes
                        has_waiting_nodes = any(node.node_type == 'waiting' for node in next_nodes)
                        if has_waiting_nodes:
                            logger.info(f"📥 [WaitingResponse {waiting_node_id}] Next nodes include waiting nodes - keeping AI disabled for now")
                        else:
                            # Only re-enable AI if there are no more waiting nodes to execute
                            try:
                                from django.core.cache import cache
                                conversation_id = context.get('event', {}).get('conversation_id')
                                if conversation_id:
                                    ai_control_key = f"ai_control_{conversation_id}"
                                    cache.set(ai_control_key, {'ai_enabled': True}, timeout=86400)
                                    logger.info(f"[WaitingNode {waiting_node_id}] AI re-enabled for conversation {conversation_id} - no more waiting nodes in failure chain")
                            except Exception:
                                pass
                        
                        try:
                            for next_node in next_nodes:
                                self._execute_node_chain(next_node, context, execution)
                            logger.info(f"📥 [WaitingResponse {waiting_node_id}] ✅ Continued workflow execution after max errors")
                        except Exception as e:
                            logger.error(f"📥 [WaitingResponse {waiting_node_id}] ❌ Error continuing workflow after max errors: {e}")
                    else:
                        logger.info(f"📥 [WaitingResponse {waiting_node_id}] No next nodes found after failure - marking workflow as completed")
                        # Mark execution as completed only if no next nodes to execute
                        if execution.status == 'RUNNING':
                            execution.status = 'COMPLETED'
                            execution.completed_at = timezone.now()
                            execution.result_data = {'message': 'Workflow completed after waiting node failure'}
                            execution.save()
                            logger.info(f"✅ Marked execution #{execution.id} as COMPLETED after waiting node failure")
                            
                            # Re-enable AI now that workflow is truly completed
                            try:
                                from django.core.cache import cache
                                conversation_id = context.get('event', {}).get('conversation_id')
                                if conversation_id:
                                    ai_control_key = f"ai_control_{conversation_id}"
                                    cache.set(ai_control_key, {'ai_enabled': True}, timeout=86400)
                                    logger.info(f"✅ Workflow truly completed (failure path) for conversation {conversation_id}. Re-enabling AI.")
                            except Exception as e:
                                logger.warning(f"Could not re-enable AI after workflow completion: {e}")
                    
                    return
                
                # Handle retry case (when not exceeding max errors)
                logger.info(f"📥 [WaitingResponse {waiting_node_id}] Checking retry logic: total_invalid={total_invalid}, allowed={allowed}")
                if total_invalid < allowed:
                    logger.info(f"📥 [WaitingResponse {waiting_node_id}] Invalid attempt #{total_invalid} of {allowed} allowed - sending retry message")
                
                    # Send specific error message based on validation failure
                    if error_message:
                        # Use the specific error message from validation
                        retry_msg = error_message
                    else:
                        # Fallback to localized generic message
                        conv_lang = self._get_conversation_language(context.get('event', {}).get('conversation_id'))
                        retry_msg = self._translate_invalid_prompt(getattr(waiting_node, 'storage_type', 'text'), conv_lang)
                    
                    # Ensure AI remains disabled while still waiting
                    conversation_id = context.get('event', {}).get('conversation_id')
                    logger.info(f"📥 [WaitingResponse {waiting_node_id}] AI already disabled for conversation {conversation_id}; sending error message: '{retry_msg}'")
                    send_result = self._send_customer_message(retry_msg, context)
                    logger.info(f"📥 [WaitingResponse {waiting_node_id}] Sent error message due to invalid input")
                    # Broadcast and external mirror for retry prompt
                    try:
                        from message.models import Message, Conversation
                        from message.serializers import WSMessageSerializer
                        from channels.layers import get_channel_layer
                        from asgiref.sync import async_to_sync
                        from message.services.telegram_service import TelegramService
                        from message.services.instagram_service import InstagramService
                        conversation_id = context.get('event', {}).get('conversation_id')
                        if conversation_id:
                            # Mark previous unanswered customer messages answered
                            Message.objects.filter(
                                conversation_id=conversation_id,
                                type='customer',
                                is_answered=False
                            ).update(is_answered=True)

                            # Load sent message for websocket broadcast
                            msg = None
                            try:
                                message_id = (send_result or {}).get('message_id')
                                if message_id:
                                    msg = Message.objects.filter(id=message_id).first()
                                if not msg:
                                    msg = Message.objects.filter(conversation_id=conversation_id).order_by('-created_at').first()
                            except Exception:
                                msg = Message.objects.filter(conversation_id=conversation_id).order_by('-created_at').first()

                            # External channel fallback (if service available)
                            try:
                                if msg:
                                    conversation = Conversation.objects.select_related('customer').get(id=conversation_id)
                                    customer = conversation.customer
                                    if getattr(customer, 'source', '') == 'telegram':
                                        svc = TelegramService.get_service_for_conversation(conversation)
                                        if svc:
                                            svc.send_message_to_customer(customer, msg.content)
                                    elif getattr(customer, 'source', '') == 'instagram':
                                        svc = InstagramService.get_service_for_conversation(conversation)
                                        if svc:
                                            svc.send_message_to_customer(customer, msg.content)
                            except Exception as se:
                                logger.warning(f"Failed to send external channel retry message (waiting-node): {se}")

                            # Websocket broadcast
                            channel_layer = get_channel_layer()
                            if channel_layer and msg:
                                async_to_sync(channel_layer.group_send)(
                                    f"chat_{conversation_id}",
                                    {
                                        'type': 'chat_message',
                                        'message': WSMessageSerializer(msg).data,
                                        'external_send_result': send_result or {}
                                    }
                                )
                    except Exception as be:
                        logger.warning(f"Failed to broadcast retry prompt: {be}")
                    
                    logger.info(f"📥 [WaitingResponse {waiting_node_id}] ❌ Invalid response handled - waiting for retry (no field update)")
                    logger.info(f"📥 [WaitingResponse {waiting_node_id}] RETURNING from invalid response handling")
                    return
                else:
                    logger.info(f"📥 [WaitingResponse {waiting_node_id}] Max errors reached - this should have been handled above")
            
            # VALID RESPONSE PATH: Only reached if response is valid
            logger.info(f"📥 [WaitingResponse {waiting_node_id}] REACHED VALID RESPONSE PATH - this should only happen for valid responses!")
            logger.info(f"📥 [WaitingResponse {waiting_node_id}] Validation result was: is_valid={is_valid}")
            logger.info(f"📥 [WaitingResponse {waiting_node_id}] ✅ Response is valid - proceeding with field update and storage")
            try:
                user_response_obj.processed_at = timezone.now()
                user_response_obj.save(update_fields=['processed_at'])
                logger.info(f"📥 [WaitingResponse {waiting_node_id}] ✅ Response marked as processed")
            except Exception as processing_error:
                logger.warning(f"📥 [WaitingResponse {waiting_node_id}] Failed to mark response as processed: {processing_error}")

            # Check if field has already been updated for this waiting node in this conversation
            # THIS ONLY HAPPENS FOR VALID RESPONSES
            logger.info(f"📥 [WaitingResponse {waiting_node_id}] ✅ Starting field update process for VALID response...")
            field_updated_successfully = False
            updated_field_name = ""
            
            # Check if this waiting node already updated a field for this conversation
            conversation_id = context.get('event', {}).get('conversation_id')
            field_already_updated = False
            
            try:
                # Check if any previous valid response (excluding current one) for this waiting node and conversation exists
                previous_valid_response = UserResponse.objects.filter(
                    waiting_node=waiting_node,
                    conversation_id=conversation_id,
                    is_valid=True,
                    processed_at__isnull=False
                ).exclude(id=user_response_obj.id).exists()
                
                if previous_valid_response:
                    field_already_updated = True
                    logger.info(f"📥 [WaitingResponse {waiting_node_id}] ⏭️ Field already updated for this waiting node in conversation {conversation_id} - skipping field update")
            except Exception as check_error:
                logger.warning(f"Failed to check previous valid responses: {check_error}")
            
            # Only update field if it hasn't been updated before for this waiting node
            if not field_already_updated:
                try:
                    storage_type = getattr(waiting_node, 'storage_type', 'text')
                    logger.info(f"💾 [Storage] Node {waiting_node.id}: storage_type='{storage_type}', response='{response_text}'")
                    
                    UserModel = get_model_class('USER')
                    user = UserModel.objects.get(id=context.get('event', {}).get('user_id'))
                    logger.info(f"💾 [Storage] User {user.id}: checking fields...")
                    
                    if storage_type == 'text' and hasattr(user, 'description'):
                        old_desc = getattr(user, 'description', '')
                        setattr(user, 'description', response_text)
                        user.save(update_fields=['description'])
                        logger.info(f"💾 [Storage] ✅ Saved to description: '{old_desc}' → '{response_text}'")
                        field_updated_successfully = True
                        updated_field_name = "Description"
                    elif storage_type == 'email' and hasattr(user, 'email'):
                        old_email = getattr(user, 'email', '')
                        setattr(user, 'email', response_text)
                        user.save(update_fields=['email'])
                        logger.info(f"💾 [Storage] ✅ Saved to email: '{old_email}' → '{response_text}'")
                        field_updated_successfully = True
                        updated_field_name = "Email"
                    elif storage_type == 'phone' and hasattr(user, 'phone_number'):
                        old_phone = getattr(user, 'phone_number', '')
                        setattr(user, 'phone_number', response_text)
                        user.save(update_fields=['phone_number'])
                        logger.info(f"💾 [Storage] ✅ Saved to phone_number: '{old_phone}' → '{response_text}'")
                        field_updated_successfully = True
                        updated_field_name = "Phone Number"
                    else:
                        logger.warning(f"💾 [Storage] ❌ No matching storage - type='{storage_type}', has_desc={hasattr(user, 'description')}, has_email={hasattr(user, 'email')}, has_phone={hasattr(user, 'phone_number')}")
                except Exception as pe:
                    logger.warning(f"Failed to persist user response to profile: {pe}")
                    
                # Log field update success but don't send message to user
                if field_updated_successfully:
                    logger.info(f"[WaitingNode {waiting_node_id}] Field '{updated_field_name}' updated successfully with value: '{response_text}'")
            else:
                logger.info(f"[WaitingNode {waiting_node_id}] Skipping field update - already updated for this conversation")
            
            # Add response to context
            context[f'user_response_{waiting_node_id}'] = response_text
            
            # Mark completion (idempotency flag) - execution level only
            try:
                if cache is not None:
                    cache.set(f"waiting_done_{execution.id}_{waiting_node_id}", True, timeout=3600)
                    cache.delete(f"waiting_lock_{execution.id}_{waiting_node_id}")
            except Exception:
                pass
            
            # Continue workflow execution from this node
            execution.status = 'RUNNING'
            # Clear waiting node marker to avoid re-processing
            try:
                execution.context_data = execution.context_data or {}
                if 'waiting_node_id' in execution.context_data:
                    del execution.context_data['waiting_node_id']
            except Exception:
                pass
            execution.save(update_fields=['status', 'context_data'])
            
            # Get next nodes and continue execution
            logger.info(f"📥 [WaitingResponse {waiting_node_id}] Getting next nodes after successful response...")
            next_nodes = self._get_next_nodes(
                waiting_node, 
                NodeExecutionResult(success=True, data={'user_response': response_text}),
                context
            )
            logger.info(f"📥 [WaitingResponse {waiting_node_id}] Found {len(next_nodes)} next nodes: {[n.title for n in next_nodes]}")
            
            # Check if any of the next nodes are waiting nodes
            has_waiting_nodes = any(node.node_type == 'waiting' for node in next_nodes)
            if has_waiting_nodes:
                logger.info(f"📥 [WaitingResponse {waiting_node_id}] Next nodes include waiting nodes - keeping AI disabled for now")
            else:
                # Only re-enable AI if there are no more waiting nodes to execute
                try:
                    from django.core.cache import cache
                    conversation_id = context.get('event', {}).get('conversation_id')
                    if conversation_id:
                        ai_control_key = f"ai_control_{conversation_id}"
                        cache.set(ai_control_key, {'ai_enabled': True}, timeout=86400)
                        logger.info(f"[WaitingNode {waiting_node_id}] AI re-enabled for conversation {conversation_id} - no more waiting nodes in chain")
                except Exception:
                    pass
            
            for next_node in next_nodes:
                logger.info(f"📥 [WaitingResponse {waiting_node_id}] Executing next node: {next_node.title}")
                self._execute_node_chain(next_node, context, execution)

            # Mark execution as completed if all nodes finished
            if execution.status == 'RUNNING':
                execution.status = 'COMPLETED'
                execution.completed_at = timezone.now()
                execution.result_data = {'message': 'Workflow completed after waiting node'}
                execution.save()
                logger.info(f"✅ Marked execution #{execution.id} as COMPLETED after waiting node completion")
                
                # Re-enable AI now that workflow is truly completed
                try:
                    from django.core.cache import cache
                    conversation_id = context.get('event', {}).get('conversation_id')
                    if conversation_id:
                        ai_control_key = f"ai_control_{conversation_id}"
                        cache.set(ai_control_key, {'ai_enabled': True}, timeout=86400)
                        logger.info(f"✅ Workflow truly completed for conversation {conversation_id}. Re-enabling AI.")
                except Exception as e:
                    logger.warning(f"Could not re-enable AI after workflow completion: {e}")
            elif execution.status == 'WAITING':
                # If execution is waiting again (due to another waiting node), keep AI disabled
                logger.info(f"📥 [WaitingResponse {waiting_node_id}] Execution is now WAITING on another node - AI remains disabled")

            # After successful waiting node completion, proceed to next nodes without AI processing
            logger.info(f"[WaitingNode {waiting_node_id}] Waiting node completed successfully - proceeding to next workflow nodes without AI processing")
        
            logger.info(f"📥 [WaitingResponse {waiting_node_id}] ✅ User response processing completed successfully")
            logger.info(f"📥 [WaitingResponse {waiting_node_id}] ===============================")
                
        except Exception as e:
            logger.error(f"📥 [WaitingResponse {waiting_node_id}] ❌ Error processing user response: {e}")
            logger.info(f"📥 [WaitingResponse {waiting_node_id}] ===============================")
            execution.status = 'FAILED'
            execution.error_message = str(e)
            execution.save()
        finally:
            # Release lock in any case if taken
            try:
                from django.core.cache import cache as _cache
                _cache.delete(f"waiting_lock_{execution.id}_{waiting_node_id}")
                logger.info(f"📥 [WaitingResponse {waiting_node_id}] Released processing lock")
            except Exception:
                pass
    
    def _validate_user_response(self, waiting_node: WaitingNode, response: str) -> tuple:
        """
        Validate user response based on waiting node requirements.
        
        Returns:
            (is_valid, error_message)
        """
        try:
            # Use storage_type to infer expected validation (text/email/phone)
            answer_type = getattr(waiting_node, 'storage_type', 'text')
            custom_error = getattr(waiting_node, 'error_message', '').strip()
            logger.info(f"🔍 [Validation] Node {waiting_node.id}: response='{response}', storage_type='{answer_type}', custom_error='{custom_error}'")
            
            # Additional check: if the node's title or message suggests email/phone but storage_type is text,
            # try to infer the expected validation from context
            node_title = getattr(waiting_node, 'title', '').lower()
            customer_message = getattr(waiting_node, 'customer_message', '').lower()
            
            # Auto-detect if this should be email validation
            if answer_type == 'text' and ('email' in node_title or 
                                         'email' in customer_message):
                logger.warning(f"🔍 [Validation] Node appears to be collecting email but storage_type is 'text' - enforcing email validation")
                answer_type = 'email'
            
            # Auto-detect if this should be phone validation  
            elif answer_type == 'text' and ('phone' in node_title or 
                                           'phone' in customer_message):
                logger.warning(f"🔍 [Validation] Node appears to be collecting phone but storage_type is 'text' - enforcing phone validation")
                answer_type = 'phone'
            
            if answer_type == 'text':
                logger.info(f"✅ [Validation] Text type - accepting without validation")
                return True, ""
            
            elif answer_type == 'email':
                import re
                email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
                if re.match(email_pattern, response.strip()):
                    logger.info(f"✅ [Validation] Email pattern matched")
                    return True, ""
                else:
                    logger.info(f"❌ [Validation] Email pattern failed")
                    # Use custom error message if provided, otherwise use default
                    if custom_error:
                        return False, custom_error
                    else:
                        return False, f"❌ Email '{response}' is invalid. Please enter a valid email (example: user@example.com)"
            
            elif answer_type == 'phone':
                # Enhanced phone validation
                import re
                # Remove all non-digit characters except + for international prefix
                clean_response = re.sub(r'[^\d+]', '', response)
                logger.info(f"🔍 [Validation] Phone check: original='{response}', clean='{clean_response}'")
                
                # Check for valid phone patterns
                if len(clean_response) < 10:
                    if custom_error:
                        return False, custom_error
                    return False, f"❌ Phone number '{response}' is too short. Please enter the complete number"
                elif len(clean_response) > 15:
                    if custom_error:
                        return False, custom_error
                    return False, f"❌ Phone number '{response}' is too long. Please enter the correct number"
                elif not clean_response.replace('+', '').isdigit():
                    if custom_error:
                        return False, custom_error
                    return False, f"❌ Phone number '{response}' should only contain numbers"
                else:
                    logger.info(f"✅ [Validation] Phone pattern matched")
                    return True, ""
            
            # Default: accept as text
            logger.info(f"✅ [Validation] Default - accepting as text")
            return True, ""
        
        except Exception as e:
            logger.error(f"Error validating user response: {e}")
            # Use custom error message if available, otherwise use default
            custom_error = getattr(waiting_node, 'error_message', '').strip()
            if custom_error:
                return False, custom_error
            return False, "خطا در اعتبارسنجی پاسخ"
    
    def _execute_control_ai_response_action(self, action_node: ActionNode, context: Dict[str, Any]) -> NodeExecutionResult:
        """Execute AI control action node."""
        try:
            conversation_id = context.get('event', {}).get('conversation_id')
            if not conversation_id:
                return NodeExecutionResult(success=False, error="Conversation ID is required")
            
            action_type = action_node.ai_control_action
            
            from message.models import Conversation
            from django.core.cache import cache
            
            conversation = Conversation.objects.get(id=conversation_id)
            ai_control_key = f"ai_control_{conversation_id}"
            
            if action_type == 'disable':
                cache.set(ai_control_key, {'ai_enabled': False}, timeout=86400)
                result_data = {'ai_disabled': True}
                
            elif action_type == 'enable':
                cache.set(ai_control_key, {'ai_enabled': True}, timeout=86400)
                result_data = {'ai_enabled': True}
                
            elif action_type == 'custom_prompt':
                custom_prompt = substitute_template_placeholders(action_node.ai_custom_prompt, context)
                if custom_prompt:
                    cache.set(ai_control_key, {
                        'ai_enabled': True,
                        'custom_prompt': custom_prompt
                    }, timeout=86400)
                    result_data = {'custom_prompt_set': True, 'prompt': custom_prompt}
                else:
                    return NodeExecutionResult(success=False, error="Custom prompt is required")
                    
            elif action_type == 'reset_context':
                ai_context_key = f"ai_context_{conversation_id}"
                cache.delete(ai_context_key)
                result_data = {'context_reset': True}
                
            else:
                return NodeExecutionResult(success=False, error=f"Unknown AI control action: {action_type}")
            
            logger.info(f"AI control action '{action_type}' executed for conversation {conversation_id}")
            return NodeExecutionResult(success=True, data=result_data)
            
        except Exception as e:
            return NodeExecutionResult(success=False, error=str(e))
    
    def _execute_update_ai_context_action(self, action_node: ActionNode, context: Dict[str, Any]) -> NodeExecutionResult:
        """Execute AI context update action node."""
        try:
            conversation_id = context.get('event', {}).get('conversation_id')
            if not conversation_id:
                return NodeExecutionResult(success=False, error="Conversation ID is required")
            
            # Process context data with template substitution
            context_data = substitute_template_placeholders(action_node.ai_context_data, context)
            if not context_data:
                return NodeExecutionResult(success=False, error="Context data is required")
            
            from django.core.cache import cache
            
            # Get existing AI context
            ai_context_key = f"ai_context_{conversation_id}"
            existing_context = cache.get(ai_context_key, {})
            
            # Merge new context data
            existing_context.update(context_data)
            
            # Save updated context
            cache.set(ai_context_key, existing_context, timeout=86400)
            
            result_data = {
                'context_updated': True,
                'context_data': existing_context
            }
            
            logger.info(f"AI context updated for conversation {conversation_id}")
            return NodeExecutionResult(success=True, data=result_data)
            
        except Exception as e:
            return NodeExecutionResult(success=False, error=str(e))
