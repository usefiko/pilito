"""
Django signals for marketing workflow integration

Handles automatic workflow triggering from message events.
"""

import logging
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

from workflow.services.trigger_service import TriggerService
from workflow.tasks import process_event

logger = logging.getLogger(__name__)


@receiver(post_save, sender='message.Message')
def handle_message_created(sender, instance, created, **kwargs):
    """
    Handle new message creation and potentially trigger workflows.
    
    This signal is triggered when a new Message is created.
    Only processes customer messages that are new.
    """
    # Only process newly created customer messages
    if not created or instance.type != 'customer':
        return
    
    # Don't process if already answered
    if getattr(instance, 'is_answered', False):
        return
    
    try:
        # Only disable AI if there are active workflows for MESSAGE_RECEIVED
        try:
            from workflow.models import Workflow
            from django.core.cache import cache
            
            conversation_id = str(instance.conversation.id)
            user_id = str(instance.customer.id)
            
            # Check if user has any active workflows for MESSAGE_RECEIVED
            active_workflows = Workflow.objects.filter(
                created_by_id=user_id,
                status='ACTIVE'
            ).exists()
            
            if active_workflows:
                ai_control_key = f"ai_control_{conversation_id}"
                # Short TTL safeguard (10 seconds instead of 300)
                cache.set(ai_control_key, {'ai_enabled': False}, timeout=10)
                logger.info(f"Temporarily disabled AI for conversation {conversation_id} (has active workflows)")
            else:
                logger.debug(f"No active workflows for user {user_id}, AI remains enabled")
                
        except Exception as ae:
            logger.debug(f"Could not check workflows or set AI disable: {ae}")

        # Create trigger event log
        event_log = TriggerService.create_event_log(
            event_type='MESSAGE_RECEIVED',
            event_data={
                'message_id': str(instance.id),
                'conversation_id': str(instance.conversation.id),
                'user_id': str(instance.customer.id),
                'content': instance.content,
                'source': getattr(instance.customer, 'source', 'unknown'),
                'timestamp': instance.created_at.isoformat()
            },
            user_id=str(instance.customer.id),
            conversation_id=str(instance.conversation.id)
        )
        
        # Queue event processing
        logger.info(f"🚀 [SIGNAL] About to queue process_event task for event_log_id: {event_log.id}")
        logger.info(f"🚀 [SIGNAL] Event data: {event_log.event_data}")
        logger.info(f"🚀 [SIGNAL] User ID: {event_log.user_id}, Conversation: {event_log.conversation_id}")
        
        # Check if we have any WAITING executions
        from workflow.models import WorkflowExecution
        waiting_executions = WorkflowExecution.objects.filter(
            conversation=event_log.conversation_id,
            status='WAITING'
        )
        logger.info(f"🚀 [SIGNAL] Found {waiting_executions.count()} WAITING executions for conversation {event_log.conversation_id}")
        for exec in waiting_executions:
            waiting_node_id = exec.context_data.get('waiting_node_id') if exec.context_data else None
            logger.info(f"🚀 [SIGNAL]   - Execution {exec.id}: waiting_node_id={waiting_node_id}")
        
        # Process waiting executions through Celery task (removed duplicate direct processing to prevent double messages)
        
        process_event.delay(str(event_log.id))
        logger.info(f"✅ [SIGNAL] Queued workflow processing for message {instance.id} with event_log {event_log.id}")
    
    except Exception as e:
        logger.error(f"Error handling message creation signal for message {instance.id}: {e}")


@receiver(post_save, sender='message.Customer')
def handle_customer_created(sender, instance, created, **kwargs):
    """
    Handle new customer creation and trigger user registration workflows.
    """
    if not created:
        return
    
    try:
        # Create trigger event log for user registration
        event_log = TriggerService.create_event_log(
            event_type='USER_CREATED',
            event_data={
                'user_id': str(instance.id),
                'email': getattr(instance, 'email', ''),
                'first_name': getattr(instance, 'first_name', ''),
                'last_name': getattr(instance, 'last_name', ''),
                'username': getattr(instance, 'username', ''),
                'source': getattr(instance, 'source', 'unknown'),
                'timestamp': instance.created_at.isoformat()
            },
            user_id=str(instance.id)
        )
        
        # Queue event processing
        process_event.delay(str(event_log.id))
        
        logger.info(f"Queued workflow processing for new customer {instance.id}")
    
    except Exception as e:
        logger.error(f"Error handling customer creation signal for customer {instance.id}: {e}")


@receiver(post_save, sender='message.Conversation')
def handle_conversation_created(sender, instance, created, **kwargs):
    """
    Handle new conversation creation and trigger conversation workflows.
    """
    if not created:
        return
    
    try:
        # Create trigger event log for conversation creation
        event_log = TriggerService.create_event_log(
            event_type='CONVERSATION_CREATED',
            event_data={
                'conversation_id': str(instance.id),
                'user_id': str(instance.customer.id),
                'source': getattr(instance, 'source', 'unknown'),
                'timestamp': instance.created_at.isoformat()
            },
            user_id=str(instance.customer.id),
            conversation_id=str(instance.id)
        )
        
        # Queue event processing
        process_event.delay(str(event_log.id))
        
        logger.info(f"Queued workflow processing for new conversation {instance.id}")
    
    except Exception as e:
        logger.error(f"Error handling conversation creation signal for conversation {instance.id}: {e}")


def trigger_tag_added_event(user_id: str, tag_name: str, added_by: str = 'system'):
    """
    Manually trigger tag added event.
    
    Args:
        user_id: ID of the user/customer
        tag_name: Name of the tag that was added
        added_by: Who added the tag
    """
    try:
        event_log = TriggerService.create_event_log(
            event_type='TAG_ADDED',
            event_data={
                'user_id': user_id,
                'tag_name': tag_name,
                'added_by': added_by,
                'timestamp': timezone.now().isoformat()
            },
            user_id=user_id
        )
        
        # Queue event processing
        process_event.delay(str(event_log.id))
        
        logger.info(f"Triggered TAG_ADDED event for user {user_id}, tag {tag_name}")
    
    except Exception as e:
        logger.error(f"Error triggering tag added event: {e}")


def trigger_tag_removed_event(user_id: str, tag_name: str, removed_by: str = 'system'):
    """
    Manually trigger tag removed event.
    
    Args:
        user_id: ID of the user/customer
        tag_name: Name of the tag that was removed
        removed_by: Who removed the tag
    """
    try:
        event_log = TriggerService.create_event_log(
            event_type='TAG_REMOVED',
            event_data={
                'user_id': user_id,
                'tag_name': tag_name,
                'removed_by': removed_by,
                'timestamp': timezone.now().isoformat()
            },
            user_id=user_id
        )
        
        # Queue event processing
        process_event.delay(str(event_log.id))
        
        logger.info(f"Triggered TAG_REMOVED event for user {user_id}, tag {tag_name}")
    
    except Exception as e:
        logger.error(f"Error triggering tag removed event: {e}")


def trigger_conversation_closed_event(conversation_id: str, user_id: str, closed_by: str = 'system'):
    """
    Manually trigger conversation closed event.
    
    Args:
        conversation_id: ID of the conversation
        user_id: ID of the user/customer
        closed_by: Who closed the conversation
    """
    try:
        event_log = TriggerService.create_event_log(
            event_type='CONVERSATION_CLOSED',
            event_data={
                'conversation_id': conversation_id,
                'user_id': user_id,
                'closed_by': closed_by,
                'timestamp': timezone.now().isoformat()
            },
            user_id=user_id,
            conversation_id=conversation_id
        )
        
        # Queue event processing
        process_event.delay(str(event_log.id))
        
        logger.info(f"Triggered CONVERSATION_CLOSED event for conversation {conversation_id}")
    
    except Exception as e:
        logger.error(f"Error triggering conversation closed event: {e}")


def connect_workflow_signals():
    """
    Connect workflow signals for automatic event processing.
    
    This function is called from apps.py to ensure signals are connected.
    """
    # Import signal handlers to ensure they are registered
    from . import signals  # This ensures all @receiver decorators are processed
    logger.info("Connected marketing workflow signals for automatic event processing")
