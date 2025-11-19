"""
Celery tasks for marketing workflow processing
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

from celery import shared_task
from django.utils import timezone
from django.db import transaction

from workflow.models import (
    TriggerEventLog,
    WorkflowExecution,
    WorkflowActionExecution,
    Workflow
)
from workflow.services.trigger_service import TriggerService
from workflow.services.workflow_execution_service import WorkflowExecutionService
from workflow.settings_adapters import (
    get_model_class,
    get_field_name,
    get_conversation_status_values,
    check_marketing_active_status_available,
    call_ai_fallback_task,
    get_sender_type_values
)

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def process_event(self, event_log_id: str):
    """
    Process a trigger event and execute matching workflows.
    
    Args:
        event_log_id: ID of the TriggerEventLog to process
    
    Returns:
        Dict with processing results
    """
    logger.info(f"🚀🚀🚀 [ProcessEvent] TASK STARTED: process_event called with event_log_id: {event_log_id}")
    logger.info(f"🚀 [ProcessEvent] ENTRY: Starting process_event for event_log_id: {event_log_id}")
    logger.info(f"⚡ [ProcessEvent] Celery worker is processing this task NOW! Queue: workflow_tasks")
    
    try:
        # Get the event log
        try:
            event_log = TriggerEventLog.objects.get(id=event_log_id)
            logger.info(f"🚀 [ProcessEvent] Found event_log: {event_log.event_type}")
        except TriggerEventLog.DoesNotExist:
            logger.error(f"🚀 [ProcessEvent] Event log {event_log_id} not found")
            return {'success': False, 'error': 'Event log not found'}
        
        logger.info(f"🚀 [ProcessEvent] PROCESSING event {event_log.event_type} from log {event_log_id}")
        logger.info(f"📋 Event data: {event_log.event_data}")
        logger.info(f"👤 User ID: {event_log.user_id}, 💬 Conversation ID: {event_log.conversation_id}")
        
        # Resume node-based workflows waiting for a user response
        if event_log.event_type == 'MESSAGE_RECEIVED' and event_log.conversation_id and event_log.user_id:
            try:
                from workflow.utils.condition_evaluator import build_context_from_event_log
                from workflow.services.node_execution_service import NodeBasedWorkflowExecutionService
                from django.core.cache import cache
                
                logger.info(f"🔍 [WaitingResume] Checking for WAITING executions in conversation {event_log.conversation_id}")
                
                # Debug: Find all executions for this conversation
                all_executions = WorkflowExecution.objects.filter(
                    conversation=event_log.conversation_id
                ).order_by('-created_at')[:3]
                
                logger.info(f"🔍 [WaitingResume] Found {all_executions.count()} total executions for conversation:")
                for i, exec in enumerate(all_executions):
                    logger.info(f"  {i+1}. Execution {exec.id}: status={exec.status}, context={exec.context_data}")
                
                # Clean up duplicate WAITING executions for the same conversation and workflow
                waiting_executions = WorkflowExecution.objects.filter(
                    conversation=event_log.conversation_id,
                    status='WAITING'
                ).order_by('-created_at')
                
                if waiting_executions.count() > 1:
                    logger.warning(f"🔍 [WaitingResume] Found {waiting_executions.count()} duplicate WAITING executions for conversation {event_log.conversation_id}")
                    
                    # Group by workflow to find duplicates
                    workflow_groups = {}
                    for exec in waiting_executions:
                        workflow_id = exec.workflow.id
                        if workflow_id not in workflow_groups:
                            workflow_groups[workflow_id] = []
                        workflow_groups[workflow_id].append(exec)
                    
                    # Clean up duplicates - keep only the most recent execution per workflow
                    for workflow_id, executions in workflow_groups.items():
                        if len(executions) > 1:
                            # Keep the most recent, mark others as cancelled
                            executions.sort(key=lambda x: x.created_at, reverse=True)
                            most_recent = executions[0]
                            duplicates = executions[1:]
                            
                            logger.warning(f"🔍 [WaitingResume] Cleaning up {len(duplicates)} duplicate executions for workflow {workflow_id}, keeping execution {most_recent.id}")
                            
                            for duplicate in duplicates:
                                duplicate.status = 'CANCELLED'
                                duplicate.error_message = 'Cancelled due to duplicate execution cleanup'
                                duplicate.completed_at = timezone.now()
                                # Clear waiting_node_id to prevent this execution from responding to messages
                                if duplicate.context_data and 'waiting_node_id' in duplicate.context_data:
                                    del duplicate.context_data['waiting_node_id']
                                duplicate.save(update_fields=['status', 'error_message', 'completed_at', 'context_data'])
                                logger.info(f"🔍 [WaitingResume] Cancelled duplicate execution {duplicate.id}")
                
                execution = WorkflowExecution.objects.filter(
                    conversation=event_log.conversation_id,
                    status='WAITING'
                ).order_by('-created_at').first()
                
                if execution:
                    logger.info(f"🔍 [WaitingResume] Found WAITING execution: {execution.id}")
                    waiting_node_id = (execution.context_data or {}).get('waiting_node_id')
                    if waiting_node_id:
                        logger.info(f"🔍 [WaitingResume] Found waiting_node_id: {waiting_node_id}")
                        # Process user response directly - waiting nodes are now reusable per conversation
                        logger.info(f"🔍 [WaitingResume] Processing user response: '{event_log.event_data.get('content', '') if isinstance(event_log.event_data, dict) else ''}'")
                        context = build_context_from_event_log(event_log)
                        user_response = event_log.event_data.get('content', '') if isinstance(event_log.event_data, dict) else ''
                        logger.info(f"🔍 [WaitingResume] About to call node_service.process_user_response for waiting_node_id: {waiting_node_id}")
                        node_service = NodeBasedWorkflowExecutionService()
                        node_service.process_user_response(waiting_node_id, user_response, context, execution)
                        logger.info(f"🔍 [WaitingResume] Completed node_service.process_user_response call")
                    else:
                        logger.warning(f"🔍 [WaitingResume] WAITING execution {execution.id} has no waiting_node_id in context")
                        logger.warning(f"🔍 [WaitingResume] Execution context_data: {execution.context_data}")
                else:
                    logger.info(f"🔍 [WaitingResume] No WAITING execution found for conversation {event_log.conversation_id}")
                    # Debug: show all executions for this conversation
                    all_executions = WorkflowExecution.objects.filter(conversation=event_log.conversation_id).order_by('-created_at')
                    logger.info(f"🔍 [WaitingResume] All executions for conversation {event_log.conversation_id}:")
                    for exec in all_executions[:3]:
                        logger.info(f"🔍 [WaitingResume]   - Execution {exec.id}: status={exec.status}, workflow={exec.workflow.name}")
                        if exec.context_data:
                            waiting_node_id = exec.context_data.get('waiting_node_id')
                            logger.info(f"🔍 [WaitingResume]     context waiting_node_id: {waiting_node_id}")
            except Exception as e:
                logger.error(f"Failed to resume waiting node workflow: {e}")
        
        # Get workflows that should be triggered
        trigger_service = TriggerService()
        workflows = trigger_service.process_event_get_workflows(event_log)
        
        logger.info(f"🔍 Found {len(workflows)} workflows to potentially execute:")
        for i, workflow in enumerate(workflows):
            logger.info(f"  {i+1}. Workflow: '{workflow['workflow_name']}' (ID: {workflow['workflow_id']})")
            logger.info(f"     Priority: {workflow['priority']}, Node-based: {workflow.get('is_node_based', False)}")
            if workflow.get('is_node_based', False):
                logger.info(f"     When Node ID: {workflow.get('when_node_id', 'N/A')}")
        
        result = {
            'success': True,
            'event_log_id': event_log_id,
            'event_type': event_log.event_type,
            'workflows_triggered': len(workflows),
            'workflow_executions': []
        }
        
        if workflows:
            logger.info(f"Found {len(workflows)} workflows to execute for event {event_log.event_type}")
            
            # Set conversation to marketing_active if status exists and conversation is involved
            conversation_id = event_log.conversation_id
            original_status = None
            conversation_updated = False
            # Gating: if this event is a customer message, temporarily disable AI auto-replies
            # while workflows (including node-based) execute to prevent simultaneous AI answers
            ai_temporarily_disabled = False
            trigger_message_id = None
            trigger_message_created_at = None
            any_node_waiting = False
            
            if conversation_id and check_marketing_active_status_available():
                try:
                    ConversationModel = get_model_class('CONVERSATION')
                    conversation = ConversationModel.objects.get(id=conversation_id)
                    status_field = get_field_name('CONVERSATION', 'STATUS_FIELD')
                    original_status = getattr(conversation, status_field)
                    
                    status_values = get_conversation_status_values()
                    if original_status == status_values['ACTIVE']:
                        setattr(conversation, status_field, status_values['MARKETING_ACTIVE'])
                        conversation.save()
                        conversation_updated = True
                        logger.info(f"Set conversation {conversation_id} to marketing_active")
                
                except Exception as e:
                    logger.warning(f"Could not update conversation status: {e}")
            
            # Disable AI while executing workflows triggered by MESSAGE_RECEIVED
            if event_log.event_type == 'MESSAGE_RECEIVED' and conversation_id:
                try:
                    from django.core.cache import cache
                    ai_control_key = f"ai_control_{conversation_id}"
                    cache.set(ai_control_key, {'ai_enabled': False}, timeout=86400)
                    ai_temporarily_disabled = True
                    # Capture trigger message details for post-execution AI decision
                    trigger_message_id = event_log.event_data.get('message_id') if isinstance(event_log.event_data, dict) else None
                    if trigger_message_id:
                        try:
                            MessageModel = get_model_class('MESSAGE')
                            trigger_msg = MessageModel.objects.get(id=trigger_message_id)
                            trigger_message_created_at = getattr(trigger_msg, 'created_at', None)
                        except Exception as _me:
                            logger.debug(f"Unable to load trigger message {trigger_message_id}: {_me}")
                except Exception as _ae:
                    logger.warning(f"Failed to set AI control disable for conversation {conversation_id}: {_ae}")
            
            # Execute workflows
            execution_service = WorkflowExecutionService()
            
            for workflow_info in workflows:
                try:
                    workflow = Workflow.objects.get(id=workflow_info['workflow_id'])
                    
                    # Create workflow execution
                    execution = execution_service.execute_workflow(workflow, workflow_info['context'])
                    
                    result['workflow_executions'].append({
                        'workflow_id': workflow_info['workflow_id'],
                        'workflow_name': workflow_info['workflow_name'],
                        'execution_id': execution.id,
                        'status': execution.status,
                        'is_node_based': workflow_info.get('is_node_based', False)
                    })
                    # Track if any node-based execution ended in WAITING to keep AI disabled
                    try:
                        if execution.status == 'WAITING':
                            any_node_waiting = True
                    except Exception:
                        pass
                    
                    # For old-style workflows, schedule individual action executions
                    if not workflow_info.get('is_node_based', False):
                        for action_execution in execution.action_executions.filter(status='PENDING'):
                            execute_workflow_action.delay(action_execution.id)
                    # Node-based workflows are executed synchronously by the execution service
                
                except Exception as e:
                    logger.error(f"Error executing workflow {workflow_info['workflow_id']}: {e}")
                    result['workflow_executions'].append({
                        'workflow_id': workflow_info['workflow_id'],
                        'workflow_name': workflow_info['workflow_name'],
                        'error': str(e)
                    })
            
            # Re-enable AI and optionally force AI reply if no workflow sent a reply and no active workflows
            if event_log.event_type == 'MESSAGE_RECEIVED' and conversation_id:
                try:
                    from django.core.cache import cache
                    
                    # Check if any workflow is still actively running (WAITING, RUNNING, or PENDING)
                    any_workflow_active = False
                    try:
                        active_executions = WorkflowExecution.objects.filter(
                            conversation=conversation_id,
                            status__in=['WAITING', 'RUNNING', 'PENDING']
                        )
                        any_workflow_active = active_executions.exists()
                    except Exception:
                        any_workflow_active = any_node_waiting  # fallback to old logic
                    
                    if any_workflow_active:
                        logger.info(f"Keeping AI disabled for conversation {conversation_id} due to active workflow state")
                    else:
                        # Determine if any non-customer message was sent after the trigger message
                        workflow_replied = False
                        try:
                            if trigger_message_created_at is not None:
                                MessageModel = get_model_class('MESSAGE')
                                sender_field = get_field_name('MESSAGE', 'SENDER_TYPE_FIELD')
                                sender_types = {}
                                try:
                                    sender_types = get_sender_type_values()
                                except Exception:
                                    sender_types = {}
                                conversation_fk = get_field_name('MESSAGE', 'CONVERSATION_FIELD') + '_id'
                                qs = MessageModel.objects.filter(**{conversation_fk: conversation_id}).filter(created_at__gt=trigger_message_created_at)
                                try:
                                    customer_val = sender_types.get('CUSTOMER', 'customer')
                                    qs = qs.exclude(**{sender_field: customer_val})
                                except Exception:
                                    # Fallback: attempt to use 'type' field directly if available
                                    try:
                                        qs = qs.exclude(type='customer')
                                    except Exception:
                                        pass
                                workflow_replied = qs.exists()
                        except Exception as _qe:
                            logger.debug(f"Workflow reply detection failed: {_qe}")

                        # Re-enable AI now that workflows have completed (no waiting)
                        ai_control_key = f"ai_control_{conversation_id}"
                        cache.set(ai_control_key, {'ai_enabled': True}, timeout=86400)
                        logger.info(f"✅ Re-enabled AI for conversation {conversation_id} after workflow processing")

                        # If workflows did not send a reply, trigger AI now for the original message
                        if not workflow_replied and trigger_message_id:
                            try:
                                # ✅ Check if message is Instagram share (skip forced AI)
                                is_instagram_share = False
                                try:
                                    MessageModel = get_model_class('MESSAGE')
                                    msg = MessageModel.objects.get(id=trigger_message_id)
                                    is_instagram_share = (
                                        hasattr(msg, 'message_type') and
                                        hasattr(msg.conversation, 'source') and
                                        msg.conversation.source == 'instagram' and
                                        msg.message_type == 'share'
                                    )
                                except Exception as _me:
                                    logger.debug(f"Unable to load trigger message {trigger_message_id} for forced AI decision: {_me}")
                                
                                if is_instagram_share:
                                    logger.info(f"🎯 Skipping forced AI for Instagram share message {trigger_message_id} (waiting for follow-up question)")
                                else:
                                cache.set(f"ai_force_{trigger_message_id}", True, timeout=30)
                                from AI_model.tasks import process_ai_response_async
                                process_ai_response_async.delay(trigger_message_id)
                                logger.info(f"🎯 Forced AI processing for message {trigger_message_id} after workflows completed")
                            except Exception as _fe:
                                logger.warning(f"Failed to force AI processing post-workflow: {_fe}")
                except Exception as _re:
                    logger.warning(f"AI re-enable sequence failed: {_re}")
            
            # Revert conversation status after all workflows are queued
            # Only revert if it is still in marketing_active (i.e., not changed by actions to another state like support_active)
            if conversation_updated and original_status:
                try:
                    conversation = ConversationModel.objects.get(id=conversation_id)
                    current_status = getattr(conversation, status_field)
                    status_values = get_conversation_status_values()
                    if current_status == status_values['MARKETING_ACTIVE']:
                        setattr(conversation, status_field, original_status)
                        conversation.save()
                        logger.info(f"Reverted conversation {conversation_id} status to {original_status}")
                    else:
                        logger.info(f"Skipping revert for conversation {conversation_id}; status changed to {current_status}")
                except Exception as e:
                    logger.warning(f"Could not revert conversation status: {e}")
        
        else:
            logger.info(f"No workflows triggered for event {event_log.event_type}")
            
            # If this was a customer message and no workflow handled it, re-enable AI and force AI reply
            if (
                event_log.event_type == 'MESSAGE_RECEIVED' and 
                event_log.conversation_id and 
                event_log.user_id
            ):
                try:
                    ConversationModel = get_model_class('CONVERSATION')
                    conversation = ConversationModel.objects.get(id=event_log.conversation_id)
                    status_field = get_field_name('CONVERSATION', 'STATUS_FIELD')
                    current_status = getattr(conversation, status_field)
                    status_values = get_conversation_status_values()
                    if current_status == status_values['ACTIVE']:
                        message_id = event_log.event_data.get('message_id')
                        if message_id:
                            # Check if message is voice/image and still processing
                            skip_ai_fallback = False
                            try:
                                MessageModel = get_model_class('MESSAGE')
                                message = MessageModel.objects.get(id=message_id)
                                if hasattr(message, 'message_type') and message.message_type in ['voice', 'image']:
                                    if hasattr(message, 'processing_status') and message.processing_status != 'completed':
                                        skip_ai_fallback = True
                                        logger.info(f"AI fallback skipped for message {message_id}: {message.message_type} still processing (status: {message.processing_status})")
                            except Exception as msg_check_err:
                                logger.debug(f"Could not check message type/status: {msg_check_err}")
                            
                            if not skip_ai_fallback:
                                try:
                                    from django.core.cache import cache
                                    # Re-enable AI explicitly (we may have disabled it on message create)
                                    ai_control_key = f"ai_control_{event_log.conversation_id}"
                                    cache.set(ai_control_key, {'ai_enabled': True}, timeout=86400)
                                    # Force AI to bypass any residual guards for this message
                                    cache.set(f"ai_force_{message_id}", True, timeout=30)
                                except Exception as re_err:
                                    logger.warning(f"Failed to re-enable/force AI in no-workflow branch: {re_err}")

                                # Guard with cache key used by AI signal to prevent duplicate enqueue
                                try:
                                    from django.core.cache import cache
                                    from message.models import Message
                                    
                                    cache_key = f"ai_processing_{message_id}"
                                    if cache.get(cache_key):
                                        logger.info(f"AI fallback skipped for message {message_id}: already scheduled/processing")
                                    else:
                                        # ✅ Check if message is a share (waiting for follow-up)
                                        try:
                                            msg = Message.objects.get(id=message_id)
                                            if (hasattr(msg, 'message_type') and 
                                                hasattr(msg.conversation, 'source') and
                                                msg.conversation.source == 'instagram' and 
                                                msg.message_type == 'share'):
                                                logger.info(f"AI fallback skipped for message {message_id}: Instagram share (waiting for follow-up question)")
                                                # Skip AI fallback for share - handled by signals.py delay logic
                                                pass
                                    else:
                                        # Set a short-lived lock to avoid race, then enqueue via adapter
                                        cache.set(cache_key, True, timeout=300)
                                        success = call_ai_fallback_task(message_id, event_log.conversation_id)
                                        if success:
                                            result['ai_fallback_called'] = True
                                            logger.info(f"Called AI fallback for message {message_id}")
                                        else:
                                            result['ai_fallback_failed'] = True
                                            logger.warning(f"Failed to call AI fallback for message {message_id}")
                                        except Message.DoesNotExist:
                                            logger.warning(f"Message {message_id} not found, skipping AI fallback")
                                except Exception as cache_err:
                                    logger.warning(f"AI fallback cache guard failed: {cache_err}")
                except Exception as e:
                    logger.warning(f"Error checking for AI fallback: {e}")
        
        return result
    
    except Exception as e:
        logger.error(f"Error processing event {event_log_id}: {e}")
        
        # Retry with exponential backoff
        if self.request.retries < self.max_retries:
            countdown = 2 ** self.request.retries
            logger.info(f"Retrying event processing in {countdown} seconds")
            raise self.retry(countdown=countdown, exc=e)
        
        return {
            'success': False,
            'error': str(e),
            'retries_exhausted': True
        }


@shared_task(bind=True, max_retries=0)
def waiting_node_timeout(self, execution_id: int, waiting_node_id: str):
    """
    Handle response timeout for a WaitingNode by following its timeout connections
    if the execution is still WAITING on that node.
    """
    try:
        execution = WorkflowExecution.objects.get(id=execution_id)
        if execution.status != 'WAITING':
            return {'success': True, 'skipped': 'not waiting'}
        current_waiting = (execution.context_data or {}).get('waiting_node_id')
        if str(current_waiting) != str(waiting_node_id):
            return {'success': True, 'skipped': 'different waiting node'}

        from workflow.models import WaitingNode
        from workflow.services.node_execution_service import NodeBasedWorkflowExecutionService, NodeExecutionResult
        try:
            waiting_node = WaitingNode.objects.get(id=waiting_node_id)
        except WaitingNode.DoesNotExist:
            return {'success': False, 'error': 'waiting node not found'}

        # On timeout: clear waiting marker and re-enable AI, then resume via timeout branches
        try:
            from django.core.cache import cache
            conv_id = (execution.context_data or {}).get('event', {}).get('conversation_id') or execution.conversation
            if conv_id:
                cache.set(f"ai_control_{conv_id}", {'ai_enabled': True}, timeout=86400)
                cache.set(f"waiting_ended_{conv_id}", True, timeout=30)
                logger.info(f"[WaitingNode {waiting_node_id}] Timeout reached; AI re-enabled and waiting ended flagged for conversation {conv_id}")
        except Exception:
            pass
        try:
            execution.context_data = execution.context_data or {}
            if 'waiting_node_id' in execution.context_data:
                del execution.context_data['waiting_node_id']
        except Exception:
            pass
        execution.status = 'RUNNING'
        execution.save(update_fields=['status', 'context_data'])

        node_service = NodeBasedWorkflowExecutionService()
        context = execution.context_data or {}
        next_nodes = node_service._get_next_nodes(waiting_node, NodeExecutionResult(success=False, data={'timed_out': True}), context)
        # After timeout, proceed to next nodes without AI processing
        logger.info(f"[WaitingNode {waiting_node_id}] Waiting node timed out - proceeding to next workflow nodes without AI processing")
        for next_node in next_nodes:
            node_service._execute_node_chain(next_node, context, execution)
        return {'success': True, 'timed_out': True}
    except Exception as e:
        logger.error(f"waiting_node_timeout failed for execution {execution_id}: {e}")
        return {'success': False, 'error': str(e)}


@shared_task(bind=True, max_retries=3)
def execute_workflow_action(self, action_execution_id: int):
    """
    Execute a single workflow action.
    
    Args:
        action_execution_id: ID of the WorkflowActionExecution to execute
    
    Returns:
        Dict with execution results
    """
    try:
        # Get the action execution
        try:
            action_execution = WorkflowActionExecution.objects.select_related(
                'workflow_execution',
                'workflow_action__action',
                'workflow_action__workflow'
            ).get(id=action_execution_id)
        except WorkflowActionExecution.DoesNotExist:
            logger.error(f"Action execution {action_execution_id} not found")
            return {'success': False, 'error': 'Action execution not found'}
        
        # Check if execution is still valid
        if action_execution.status not in ['PENDING', 'WAITING']:
            logger.warning(f"Action execution {action_execution_id} is not in executable state: {action_execution.status}")
            return {'success': False, 'error': f'Invalid status: {action_execution.status}'}
        
        logger.info(f"Executing action {action_execution.workflow_action.action.name}")
        
        # Execute the action using the service
        execution_service = WorkflowExecutionService()
        context = action_execution.workflow_execution.context_data
        
        with transaction.atomic():
            # Execute the action
            result = execution_service._execute_workflow_action(
                action_execution.workflow_execution,
                action_execution.workflow_action,
                context
            )
            
            # Check if this was the last action in the workflow
            workflow_execution = action_execution.workflow_execution
            remaining_actions = workflow_execution.action_executions.filter(
                status__in=['PENDING', 'WAITING', 'RUNNING']
            ).exclude(id=action_execution_id)
            
            if not remaining_actions.exists():
                # Mark workflow as completed
                workflow_execution.status = 'COMPLETED'
                workflow_execution.completed_at = timezone.now()
                workflow_execution.save()
                
                # Revert conversation status if it was set to marketing_active
                conversation_id = workflow_execution.conversation
                if conversation_id and check_marketing_active_status_available():
                    try:
                        ConversationModel = get_model_class('CONVERSATION')
                        conversation = ConversationModel.objects.get(id=conversation_id)
                        status_field = get_field_name('CONVERSATION', 'STATUS_FIELD')
                        current_status = getattr(conversation, status_field)
                        
                        status_values = get_conversation_status_values()
                        if current_status == status_values['MARKETING_ACTIVE']:
                            setattr(conversation, status_field, status_values['ACTIVE'])
                            conversation.save()
                            logger.info(f"Reverted conversation {conversation_id} from marketing_active to active")
                    
                    except Exception as e:
                        logger.warning(f"Could not revert conversation status: {e}")
                
                logger.info(f"Completed workflow execution #{workflow_execution.id}")
        
        return {
            'success': True,
            'action_execution_id': action_execution_id,
            'action_name': action_execution.workflow_action.action.name,
            'status': action_execution.status,
            'workflow_completed': workflow_execution.status == 'COMPLETED'
        }
    
    except Exception as e:
        logger.error(f"Error executing action {action_execution_id}: {e}")
        
        # Update action execution status
        try:
            action_execution = WorkflowActionExecution.objects.get(id=action_execution_id)
            action_execution.status = 'FAILED'
            action_execution.error_message = str(e)
            action_execution.completed_at = timezone.now()
            action_execution.save()
        except:
            pass
        
        # Retry with exponential backoff
        if self.request.retries < self.max_retries:
            countdown = 2 ** self.request.retries
            logger.info(f"Retrying action execution in {countdown} seconds")
            raise self.retry(countdown=countdown, exc=e)
        
        return {
            'success': False,
            'error': str(e),
            'retries_exhausted': True
        }


@shared_task
def execute_scheduled_workflow(workflow_id: str, context_data: Optional[Dict[str, Any]] = None, trigger_id: Optional[str] = None):
    """
    Execute a workflow on a schedule.
    
    Args:
        workflow_id: ID of the workflow to execute
        context_data: Optional context data for execution
        trigger_id: Optional trigger ID that initiated this execution
    
    Returns:
        Dict with execution results
    """
    try:
        workflow = Workflow.objects.get(id=workflow_id)
        
        if not workflow.is_active():
            logger.warning(f"Scheduled workflow {workflow_id} is not active, skipping")
            return {'success': False, 'error': 'Workflow not active'}
        
        # Build context for scheduled execution
        context = context_data or {}
        if 'event' not in context:
            context['event'] = {
                'type': 'SCHEDULED',
                'data': {
                    'workflow_id': workflow_id,
                    'trigger_id': trigger_id,
                    'scheduled_at': timezone.now().isoformat()
                },
                'timestamp': timezone.now().isoformat()
            }
        
        # Execute workflow
        execution_service = WorkflowExecutionService()
        execution = execution_service.execute_workflow(workflow, context)
        
        logger.info(f"Executed scheduled workflow {workflow.name} (execution #{execution.id})")
        
        return {
            'success': True,
            'workflow_id': workflow_id,
            'execution_id': execution.id,
            'status': execution.status
        }
    
    except Workflow.DoesNotExist:
        logger.error(f"Scheduled workflow {workflow_id} not found")
        return {'success': False, 'error': 'Workflow not found'}
    
    except Exception as e:
        logger.error(f"Error executing scheduled workflow {workflow_id}: {e}")
        return {'success': False, 'error': str(e)}


@shared_task
def cleanup_old_executions(days: int = 30):
    """
    Cleanup old workflow executions and logs.
    
    Args:
        days: Number of days to keep (older records will be deleted)
    
    Returns:
        Dict with cleanup results
    """
    try:
        cutoff_date = timezone.now() - timedelta(days=days)
        
        # Cleanup old executions
        old_executions = WorkflowExecution.objects.filter(
            created_at__lt=cutoff_date,
            status__in=['COMPLETED', 'FAILED', 'TIMED_OUT']
        )
        
        execution_count = old_executions.count()
        old_executions.delete()
        
        # Cleanup old event logs
        old_event_logs = TriggerEventLog.objects.filter(created_at__lt=cutoff_date)
        event_log_count = old_event_logs.count()
        old_event_logs.delete()
        
        logger.info(f"Cleaned up {execution_count} old executions and {event_log_count} old event logs")
        
        return {
            'success': True,
            'cutoff_date': cutoff_date.isoformat(),
            'executions_deleted': execution_count,
            'event_logs_deleted': event_log_count
        }
    
    except Exception as e:
        logger.error(f"Error during cleanup: {e}")
        return {'success': False, 'error': str(e)}


@shared_task
def retry_failed_actions():
    """
    Retry failed workflow actions that are eligible for retry.
    
    Returns:
        Dict with retry results
    """
    try:
        # Find failed actions that can be retried
        from django.db import models
        
        failed_actions = WorkflowActionExecution.objects.filter(
            status='FAILED',
            retry_count__lt=models.F('max_retries'),
            next_retry_at__lte=timezone.now()
        ).select_related('workflow_action__action')
        
        retry_count = 0
        for action_execution in failed_actions:
            try:
                # Increment retry count
                action_execution.retry_count += 1
                action_execution.status = 'PENDING'
                action_execution.error_message = ''
                action_execution.save()
                
                # Schedule retry
                execute_workflow_action.delay(action_execution.id)
                retry_count += 1
                
                logger.info(f"Scheduled retry for action execution {action_execution.id}")
            
            except Exception as e:
                logger.error(f"Error scheduling retry for action {action_execution.id}: {e}")
        
        return {
            'success': True,
            'actions_retried': retry_count
        }
    
    except Exception as e:
        logger.error(f"Error during retry process: {e}")
        return {'success': False, 'error': str(e)}


@shared_task(bind=True, max_retries=0)
def resume_node_workflow_after_delay(self, execution_id: int, resume_from_node_id: str):
    """
    Resume a node-based workflow execution after a delay from the next node(s)
    following the given action node.
    """
    try:
        execution = WorkflowExecution.objects.select_related('workflow').get(id=execution_id)
        workflow = execution.workflow
        from workflow.services.node_execution_service import NodeBasedWorkflowExecutionService, NodeExecutionResult
        from workflow.models import WorkflowNode

        node_service = NodeBasedWorkflowExecutionService()
        # Rebuild minimal context from stored execution context
        context = execution.context_data or {}

        # Continue after the specified action node (do not re-execute it)
        try:
            action_node = WorkflowNode.objects.get(id=resume_from_node_id, workflow=workflow)
        except WorkflowNode.DoesNotExist:
            return {'success': False, 'error': 'action node not found'}

        execution.status = 'RUNNING'
        execution.save(update_fields=['status'])

        next_nodes = node_service._get_next_nodes(action_node, NodeExecutionResult(success=True, data={'delay_completed': True}), context)
        for next_node in next_nodes:
            node_service._execute_node_chain(next_node, context, execution)

        return {'success': True, 'resumed_execution_id': execution_id, 'continued_from_node': resume_from_node_id}
    except Exception as e:
        logger.error(f"Failed to resume node workflow execution #{execution_id}: {e}")
        return {'success': False, 'error': str(e)}


@shared_task
def process_scheduled_triggers():
    """
    Process scheduled triggers that are due for execution.
    
    Returns:
        Dict with processing results
    """
    try:
        from workflow.models import Trigger
        
        # Find scheduled triggers that are due
        due_triggers = Trigger.objects.filter(
            trigger_type='SCHEDULED',
            is_active=True,
            next_execution__lte=timezone.now()
        )
        
        processed_count = 0
        for trigger in due_triggers:
            try:
                # Create event log for scheduled trigger
                event_log = TriggerEventLog.objects.create(
                    event_type='SCHEDULED',
                    event_data={
                        'trigger_id': str(trigger.id),
                        'trigger_name': trigger.name,
                        'schedule_type': trigger.schedule_type
                    }
                )
                
                # Process the event
                process_event.delay(str(event_log.id))
                
                # Update next execution time
                if trigger.schedule_type == 'DAILY':
                    trigger.next_execution = timezone.now() + timedelta(days=1)
                elif trigger.schedule_type == 'WEEKLY':
                    trigger.next_execution = timezone.now() + timedelta(weeks=1)
                elif trigger.schedule_type == 'MONTHLY':
                    trigger.next_execution = timezone.now() + timedelta(days=30)
                
                trigger.save()
                processed_count += 1
                
                logger.info(f"Processed scheduled trigger {trigger.name}")
            
            except Exception as e:
                logger.error(f"Error processing scheduled trigger {trigger.id}: {e}")
        
        return {
            'success': True,
            'triggers_processed': processed_count
        }
    
    except Exception as e:
        logger.error(f"Error processing scheduled triggers: {e}")
        return {'success': False, 'error': str(e)}


@shared_task
def process_scheduled_when_nodes():
    """
    Scan node-based scheduled When nodes and trigger workflows at the correct
    local time based on the owner's timezone / country.
    This should run every minute via Celery beat.
    """
    try:
        from workflow.models import WhenNode, WorkflowNode
        from workflow.services.node_execution_service import NodeBasedWorkflowExecutionService
        from django.utils import timezone as dj_tz
        from datetime import timedelta

        now_utc = dj_tz.now()
        node_service = NodeBasedWorkflowExecutionService()

        # Active scheduled when nodes
        when_nodes = WhenNode.objects.filter(
            when_type='scheduled',
            is_active=True,
            workflow__status='ACTIVE'
        ).select_related('workflow')

        triggered_count = 0

        for wn in when_nodes:
            try:
                # Build minimal SCHEDULED event context
                context = {
                    'event': {
                        'type': 'SCHEDULED',
                        'data': {
                            'workflow_id': str(wn.workflow.id),
                            'when_node_id': str(wn.id),
                            'scheduled_scan_at': now_utc.isoformat()
                        },
                        'timestamp': now_utc.isoformat()
                    }
                }

                # Use the service's own evaluator (timezone-aware logic already added)
                should_fire = node_service._should_when_node_trigger(wn.workflownode_ptr, context)
                if not should_fire:
                    continue

                # Determine audience: all active conversations of the workflow owner,
                # optionally filtered by channels and customer tags
                owner = getattr(wn.workflow, 'created_by', None)
                if not owner:
                    continue

                ConversationModel = get_model_class('CONVERSATION')
                try:
                    conversations = ConversationModel.objects.filter(user=owner, is_active=True)
                except Exception:
                    conversations = ConversationModel.objects.filter(user=owner)

                for conv in conversations:
                    try:
                        # Channel filter
                        if wn.channels and 'all' not in wn.channels:
                            source_val = getattr(conv, 'source', '')
                            if source_val not in wn.channels:
                                continue

                        # Customer tag filter using multiple possible relations
                        if wn.tags:
                            customer = getattr(conv, 'customer', None) or getattr(conv, 'user', None)
                            if customer is None:
                                continue
                            tag_names = []
                            try:
                                tag_names = list(getattr(customer, 'tag').values_list('name', flat=True))
                            except Exception:
                                try:
                                    tag_names = list(getattr(customer, 'tags').values_list('name', flat=True))
                                except Exception:
                                    if isinstance(getattr(customer, 'tags', []), list):
                                        tag_names = getattr(customer, 'tags', [])
                            # Check if customer has ALL of the required tags
                            if not all(t in tag_names for t in wn.tags):
                                continue

                        # Per-conversation de-dup (last minute)
                        recent = WorkflowExecution.objects.filter(
                            workflow=wn.workflow,
                            conversation=str(getattr(conv, 'id')),
                            created_at__gte=now_utc - timedelta(minutes=1),
                            trigger_data__when_node_id=str(wn.id)
                        ).exists()
                        if recent:
                            continue

                        # Build context with conversation and customer identifiers
                        customer = getattr(conv, 'customer', None) or getattr(conv, 'user', None)
                        user_id = str(getattr(customer, 'id')) if customer else None
                        conv_id = str(getattr(conv, 'id'))
                        per_ctx = {
                            'event': {
                                'type': 'SCHEDULED',
                                'data': {
                                    'workflow_id': str(wn.workflow.id),
                                    'when_node_id': str(wn.id),
                                    'scheduled_scan_at': now_utc.isoformat()
                                },
                                'conversation_id': conv_id,
                                'user_id': user_id,
                                'timestamp': now_utc.isoformat()
                            }
                        }

                        execution = node_service.execute_node_workflow(
                            wn.workflow,
                            per_ctx,
                            start_node_id=str(wn.workflownode_ptr.id)
                        )

                        # Update execution trigger_data for deduplication trace
                        try:
                            execution.trigger_data = {
                                **(execution.trigger_data or {}),
                                'event_type': 'SCHEDULED',
                                'when_node_id': str(wn.id)
                            }
                            execution.save(update_fields=['trigger_data'])
                        except Exception:
                            pass

                        triggered_count += 1
                    except Exception as ce:
                        logger.error(f"Error scheduling per conversation for When node {wn.id}: {ce}")
            except Exception as ne:
                logger.error(f"Error processing scheduled When node {wn.id}: {ne}")

        return {
            'success': True,
            'scheduled_when_nodes_checked': when_nodes.count(),
            'workflows_triggered': triggered_count
        }
    except Exception as e:
        logger.error(f"Error in process_scheduled_when_nodes: {e}")
        return {'success': False, 'error': str(e)}
