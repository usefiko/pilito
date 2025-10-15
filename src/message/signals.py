"""
Django signals for message app
Handles automatic WebSocket notifications for model updates
"""
import logging
from django.db.models.signals import post_save
from django.dispatch import receiver

logger = logging.getLogger(__name__)


@receiver(post_save, sender='message.Customer', dispatch_uid='customer_websocket_notification_v2')
def handle_customer_updated(sender, instance, created, **kwargs):
    """
    Handle customer updates and send WebSocket notifications
    
    This signal is triggered when a Customer is saved (created or updated).
    For updates, it sends real-time notifications to connected users.
    """
    # Only send notifications for updates, not creation
    if created:
        logger.debug(f"Customer {instance.id} created - no WebSocket notification needed")
        return
    
    try:
        from message.websocket_utils import notify_customer_updated
        
        # Send WebSocket notification for the updated customer
        notify_customer_updated(instance)
        
        logger.info(f"Sent WebSocket notification for customer {instance.id} update")
        
    except Exception as e:
        logger.error(f"Error handling customer update signal for customer {instance.id}: {e}")


# ============================================================================
# INTERCOM INTEGRATION SIGNALS
# ============================================================================

@receiver(post_save, sender='message.Conversation')
def sync_conversation_to_intercom_on_create(sender, instance, created, **kwargs):
    """
    Automatically sync new conversations to Intercom when created.
    
    Only syncs if sync_to_intercom flag is True.
    """
    from django.conf import settings
    
    # Only sync if Intercom is configured and flag is set
    if not settings.INTERCOM_ACCESS_TOKEN:
        return
    
    if not created:
        return  # Only sync on creation
    
    if not getattr(instance, 'sync_to_intercom', False):
        return  # Only sync if explicitly enabled
    
    try:
        from message.tasks import sync_conversation_to_intercom_async
        
        # Trigger async sync
        sync_conversation_to_intercom_async.delay(instance.id)
        
        logger.info(f"🔄 Triggered Intercom sync for conversation {instance.id}")
        
    except Exception as e:
        logger.error(f"❌ Failed to trigger Intercom sync for conversation {instance.id}: {str(e)}")


@receiver(post_save, sender='message.Message')
def sync_message_to_intercom_on_create(sender, instance, created, **kwargs):
    """
    Automatically sync new messages to Intercom conversation.
    
    Only syncs customer messages and if conversation is synced to Intercom.
    """
    from django.conf import settings
    
    # Only sync if Intercom is configured
    if not settings.INTERCOM_ACCESS_TOKEN:
        return
    
    if not created:
        return  # Only sync on creation
    
    # Only sync customer messages (not AI/support responses)
    if instance.type != 'customer':
        return
    
    # Check if conversation has sync_to_intercom flag (if attribute exists)
    if not hasattr(instance.conversation, 'sync_to_intercom') or not instance.conversation.sync_to_intercom:
        return
    
    # Only sync if conversation has Intercom ID (if attribute exists)
    if not hasattr(instance.conversation, 'intercom_conversation_id') or not instance.conversation.intercom_conversation_id:
        return
    
    try:
        from message.tasks import sync_message_to_intercom_async
        
        # Trigger async sync
        sync_message_to_intercom_async.delay(instance.id)
        
        logger.info(f"🔄 Triggered Intercom sync for message {instance.id}")
        
    except Exception as e:
        logger.error(f"❌ Failed to trigger Intercom sync for message {instance.id}: {str(e)}")


def connect_message_signals():
    """
    Connect message app signals
    This function should be called in apps.py ready() method
    """
    logger.info("Connected message app signals for WebSocket notifications and Intercom sync")
