"""
Django signals for Settings app
Handles automatic creation of AIPrompts and Intercom syncing for Support Tickets
"""

import logging
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings

logger = logging.getLogger(__name__)


# ============================================================================
# USER SIGNALS - AIPrompts Auto-Creation
# ============================================================================

@receiver(post_save, sender='accounts.User')
def create_ai_prompts_for_user(sender, instance, created, **kwargs):
    """
    Automatically create AIPrompts when a new User is created
    
    Args:
        sender: User model
        instance: User instance
        created: Boolean indicating if this is a new user
    """
    if created:
        try:
            from .models import AIPrompts
            prompts, prompts_created = AIPrompts.get_or_create_for_user(instance)
            if prompts_created:
                logger.info(f"✅ Auto-created AIPrompts for new user: {instance.username} ({instance.email})")
            else:
                logger.info(f"ℹ️ AIPrompts already existed for user: {instance.username}")
                
        except Exception as e:
            logger.error(f"❌ Error creating AIPrompts for user {instance.username}: {str(e)}")


# ============================================================================
# INTERCOM INTEGRATION SIGNALS - Support Tickets
# ============================================================================


@receiver(post_save, sender='settings.SupportTicket')
def sync_ticket_to_intercom_on_create(sender, instance, created, **kwargs):
    """
    Automatically sync new support tickets to Intercom.
    
    Creates a new Intercom conversation when a support ticket is created.
    """
    # Only sync if Intercom is configured
    if not settings.INTERCOM_ACCESS_TOKEN:
        return
    
    if not created:
        # If ticket is updated (not created), check if status changed to closed
        intercom_id = instance.intercom_ticket_id or instance.intercom_conversation_id
        if instance.status == 'closed' and intercom_id:
            try:
                from settings.tasks import update_ticket_status_in_intercom_async
                update_ticket_status_in_intercom_async.delay(instance.id)
                logger.info(f"🔄 Triggered Intercom status update for ticket {instance.id}")
            except Exception as e:
                logger.error(f"❌ Failed to trigger Intercom status update for ticket {instance.id}: {str(e)}")
        return
    
    try:
        from settings.tasks import sync_ticket_to_intercom_async
        
        # Trigger async sync
        sync_ticket_to_intercom_async.delay(instance.id)
        
        logger.info(f"🔄 Triggered Intercom sync for ticket {instance.id}")
        
    except Exception as e:
        logger.error(f"❌ Failed to trigger Intercom sync for ticket {instance.id}: {str(e)}")


@receiver(post_save, sender='settings.SupportMessage')
def sync_message_to_intercom_on_create(sender, instance, created, **kwargs):
    """
    Automatically sync new support messages to Intercom.
    
    Adds the message to the existing Intercom conversation or ticket.
    
    IMPORTANT: Uses 3-second countdown to allow time for attachments to be saved.
    Django serializers save related objects AFTER the main object is created,
    so we need this delay to ensure attachments exist before sync.
    """
    # Only sync if Intercom is configured
    if not settings.INTERCOM_ACCESS_TOKEN:
        return
    
    if not created:
        return  # Only sync on creation
    
    # CRITICAL: Skip if message came from Intercom webhook (prevent infinite loop)
    if getattr(instance, '_skip_intercom_sync', False):
        logger.debug(f"⏭️ Skipping Intercom sync for message {instance.id} (came from Intercom webhook)")
        return
    
    # Only sync if ticket has Intercom ID (ticket or conversation)
    intercom_id = instance.ticket.intercom_ticket_id or instance.ticket.intercom_conversation_id
    
    if not intercom_id:
        logger.debug(f"ℹ️ Ticket {instance.ticket.id} not synced to Intercom, skipping message {instance.id}")
        return
    
    # Use transaction.on_commit with countdown to allow attachments to be saved
    def trigger_sync():
        try:
            from settings.tasks import sync_ticket_message_to_intercom_async
            
            # Trigger async sync with 3 second countdown
            # This gives serializer time to save attachments after message creation
            sync_ticket_message_to_intercom_async.apply_async(
                args=[instance.id],
                countdown=3  # Wait 3 seconds for attachments to be saved
            )
            
            logger.info(f"🔄 Scheduled Intercom sync for message {instance.id} (countdown: 3s)")
            
        except Exception as e:
            logger.error(f"❌ Failed to schedule Intercom sync for message {instance.id}: {str(e)}")
    
    from django.db import transaction
    transaction.on_commit(trigger_sync)

