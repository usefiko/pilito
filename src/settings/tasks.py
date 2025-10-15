"""
Celery tasks for Settings app (Support Tickets)
"""

import logging
from celery import shared_task
from django.apps import apps

logger = logging.getLogger(__name__)


@shared_task(
    name='settings.sync_ticket_to_intercom',
    bind=True,
    max_retries=3,
    default_retry_delay=60
)
def sync_ticket_to_intercom_async(self, ticket_id: int):
    """
    Async task to sync a support ticket to Intercom using Tickets API.
    
    This is the NEW implementation using Intercom Tickets API instead of Conversations.
    
    Args:
        ticket_id: SupportTicket ID
        
    Returns:
        dict: Task result with success status and ticket ID
    """
    try:
        SupportTicket = apps.get_model('settings', 'SupportTicket')
        ticket = SupportTicket.objects.get(id=ticket_id)
        
        # Skip if already synced (check new field first, then old for backward compat)
        if ticket.intercom_ticket_id:
            logger.info(f"ℹ️ Ticket {ticket_id} already synced to Intercom ticket {ticket.intercom_ticket_id}")
            return {
                'success': True,
                'ticket_id': ticket_id,
                'intercom_ticket_id': ticket.intercom_ticket_id,
                'message': 'Already synced'
            }
        
        # Also check old field for backward compatibility
        if ticket.intercom_conversation_id:
            logger.info(f"ℹ️ Ticket {ticket_id} already synced to Intercom conversation {ticket.intercom_conversation_id} (legacy)")
            return {
                'success': True,
                'ticket_id': ticket_id,
                'intercom_conversation_id': ticket.intercom_conversation_id,
                'message': 'Already synced (legacy)'
            }
        
        # Import here to avoid circular imports
        from settings.services import IntercomTicketSyncService
        
        # Create Intercom ticket using NEW Tickets API
        intercom_ticket = IntercomTicketSyncService.create_ticket(ticket)
        
        if intercom_ticket and 'id' in intercom_ticket:
            # Ticket ID is already saved in the service method, just confirm
            logger.info(f"✅ Synced ticket {ticket_id} to Intercom ticket {intercom_ticket['id']}")
            
            return {
                'success': True,
                'ticket_id': ticket_id,
                'intercom_ticket_id': intercom_ticket['id']
            }
        else:
            logger.error(f"❌ Failed to sync ticket {ticket_id} to Intercom")
            # Retry with exponential backoff
            raise self.retry(exc=Exception("Intercom ticket creation failed"))
            
    except SupportTicket.DoesNotExist:
        logger.error(f"❌ Ticket {ticket_id} not found")
        return {
            'success': False,
            'ticket_id': ticket_id,
            'error': 'Ticket not found'
        }
    except Exception as e:
        logger.error(f"❌ Error syncing ticket {ticket_id} to Intercom: {str(e)}")
        # Retry up to 3 times
        try:
            raise self.retry(exc=e)
        except self.MaxRetriesExceededError:
            return {
                'success': False,
                'ticket_id': ticket_id,
                'error': str(e)
            }


@shared_task(name='settings.sync_ticket_message_to_intercom')
def sync_ticket_message_to_intercom_async(message_id: int):
    """
    Async task to sync a support ticket message to Intercom.
    
    Note: For Tickets API, message syncing is not yet fully implemented.
    This currently falls back to Conversations API for backward compatibility.
    
    Args:
        message_id: SupportMessage ID
        
    Returns:
        dict: Task result with success status
    """
    try:
        SupportMessage = apps.get_model('settings', 'SupportMessage')
        # IMPORTANT: prefetch attachments to ensure they're loaded for sync
        message = SupportMessage.objects.select_related('ticket').prefetch_related('attachments').get(id=message_id)
        
        # Check if ticket is synced to Intercom (either new or old way)
        intercom_id = message.ticket.intercom_ticket_id or message.ticket.intercom_conversation_id
        
        if not intercom_id:
            logger.info(f"ℹ️ Ticket {message.ticket.id} not synced to Intercom, skipping message {message_id}")
            return {
                'success': False,
                'message_id': message_id,
                'error': 'Ticket not synced to Intercom'
            }
        
        # Log attachment count for debugging
        attachment_count = message.attachments.count()
        logger.info(f"📊 Message {message_id} has {attachment_count} attachment(s)")
        
        # Import here to avoid circular imports
        from settings.services import IntercomTicketSyncService
        
        # Determine which method to use based on sync type
        if message.ticket.intercom_ticket_id:
            # NEW: Tickets API
            result = IntercomTicketSyncService.add_message_to_ticket(
                message,
                message.ticket.intercom_ticket_id
            )
            
            if result:
                logger.info(f"✅ Synced message {message_id} to Intercom ticket {message.ticket.intercom_ticket_id}")
                return {
                    'success': True,
                    'message_id': message_id,
                    'ticket_id': message.ticket.intercom_ticket_id
                }
            else:
                logger.error(f"❌ Failed to sync message {message_id} to Intercom ticket")
                return {
                    'success': False,
                    'message_id': message_id,
                    'error': 'Failed to add message to ticket'
                }
        else:
            # OLD: Conversations API (for backward compatibility)
            result = IntercomTicketSyncService.add_message_to_conversation(
                message,
                message.ticket.intercom_conversation_id
            )
            
            if result:
                logger.info(f"✅ Synced message {message_id} to Intercom conversation {message.ticket.intercom_conversation_id}")
                return {
                    'success': True,
                    'message_id': message_id,
                    'conversation_id': message.ticket.intercom_conversation_id
                }
            else:
                logger.error(f"❌ Failed to sync message {message_id} to Intercom")
                return {
                    'success': False,
                    'message_id': message_id,
                    'error': 'Failed to add message'
                }
            
    except SupportMessage.DoesNotExist:
        logger.error(f"❌ Message {message_id} not found")
        return {
            'success': False,
            'message_id': message_id,
            'error': 'Message not found'
        }
    except Exception as e:
        logger.error(f"❌ Error syncing message {message_id} to Intercom: {str(e)}")
        return {
            'success': False,
            'message_id': message_id,
            'error': str(e)
        }


@shared_task(name='settings.update_ticket_status_in_intercom')
def update_ticket_status_in_intercom_async(ticket_id: int):
    """
    Async task to update ticket status in Intercom.
    
    Note: Status update for Tickets API not yet fully implemented.
    
    Args:
        ticket_id: SupportTicket ID
        
    Returns:
        dict: Task result with success status
    """
    try:
        SupportTicket = apps.get_model('settings', 'SupportTicket')
        ticket = SupportTicket.objects.get(id=ticket_id)
        
        # Check if ticket is synced to Intercom (either new or old way)
        intercom_id = ticket.intercom_ticket_id or ticket.intercom_conversation_id
        
        if not intercom_id:
            logger.info(f"ℹ️ Ticket {ticket_id} not synced to Intercom, skipping status update")
            return {
                'success': False,
                'ticket_id': ticket_id,
                'error': 'Ticket not synced to Intercom'
            }
        
        # Import here to avoid circular imports
        from settings.services import IntercomTicketSyncService
        
        # Determine which method to use based on sync type
        if ticket.intercom_ticket_id:
            # NEW: Tickets API
            result = IntercomTicketSyncService.update_ticket_status(ticket)
            
            if result:
                logger.info(f"✅ Updated ticket {ticket_id} status in Intercom")
                return {
                    'success': True,
                    'ticket_id': ticket_id,
                    'intercom_ticket_id': ticket.intercom_ticket_id
                }
            else:
                logger.warning(f"⚠️ Status update not yet implemented for Tickets API")
                return {
                    'success': False,
                    'ticket_id': ticket_id,
                    'error': 'Tickets API status update not yet implemented'
                }
        else:
            # OLD: Conversations API (for backward compatibility)
            success = IntercomTicketSyncService.update_ticket_status(
                ticket,
                ticket.intercom_conversation_id
            )
            
            if success:
                logger.info(f"✅ Updated ticket {ticket_id} status in Intercom conversation")
                return {
                    'success': True,
                    'ticket_id': ticket_id,
                    'conversation_id': ticket.intercom_conversation_id
                }
            else:
                logger.error(f"❌ Failed to update ticket {ticket_id} status in Intercom")
                return {
                    'success': False,
                    'ticket_id': ticket_id,
                    'error': 'Failed to update status'
                }
            
    except SupportTicket.DoesNotExist:
        logger.error(f"❌ Ticket {ticket_id} not found")
        return {
            'success': False,
            'ticket_id': ticket_id,
            'error': 'Ticket not found'
        }
    except Exception as e:
        logger.error(f"❌ Error updating ticket {ticket_id} status in Intercom: {str(e)}")
        return {
            'success': False,
            'ticket_id': ticket_id,
            'error': str(e)
        }

