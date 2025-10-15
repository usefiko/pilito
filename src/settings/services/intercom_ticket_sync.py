"""
Intercom Ticket Sync Service (Tickets API v2.0)
Syncs Support Tickets to Intercom using the official Tickets API
"""

import logging
import requests
from django.conf import settings
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class IntercomTicketSyncService:
    """
    Service to sync Support Tickets to Intercom using Tickets API.
    
    Migration from Conversations API to Tickets API for:
    - Direct ticket creation in Intercom Tickets tab
    - Full custom attributes support
    - Two-way sync with webhooks
    - SLA tracking and reporting
    """
    
    API_VERSION = "2.10"  # Intercom API version
    
    @staticmethod
    def get_headers() -> Dict[str, str]:
        """Get Intercom API headers"""
        return {
            'Authorization': f'Bearer {settings.INTERCOM_ACCESS_TOKEN}',
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'Intercom-Version': getattr(settings, 'INTERCOM_API_VERSION', IntercomTicketSyncService.API_VERSION)
        }
    
    @classmethod
    def get_or_create_intercom_user(cls, user) -> Optional[str]:
        """
        Get or create Intercom user and return their Intercom Contact ID.
        
        Args:
            user: Django User instance
            
        Returns:
            str: Intercom contact ID (e.g., "68eba19cefa741d392e455bf") if successful, None otherwise
        """
        try:
            # Import here to avoid circular imports
            from accounts.services.intercom_contact_sync import IntercomContactSyncService
            
            # Sync user to Intercom and get contact data
            intercom_contact = IntercomContactSyncService.create_or_update_contact(user)
            
            if intercom_contact and 'id' in intercom_contact:
                contact_id = intercom_contact['id']
                logger.info(f"✅ Got Intercom contact ID {contact_id} for user {user.id}")
                return contact_id
            else:
                logger.error(f"❌ Failed to get Intercom contact ID for user {user.id}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Error getting Intercom contact ID for user {user.id}: {str(e)}")
            return None
    
    @classmethod
    def get_attachment_public_url(cls, attachment_obj) -> Optional[str]:
        """
        Get public URL for attachment file.
        
        NOTE: Intercom doesn't have a file upload API for attachments.
        We need to provide a publicly accessible URL instead.
        
        Args:
            attachment_obj: SupportMessageAttachment instance
            
        Returns:
            str: Public URL for the file, or None if not accessible
        """
        try:
            from django.conf import settings as django_settings
            
            # Get file URL
            file_url = attachment_obj.file.url
            
            # If it's a relative URL, make it absolute
            if file_url.startswith('/'):
                # Use MEDIA_URL from settings or construct it
                base_url = getattr(django_settings, 'BASE_URL', 'https://api.fiko.net')
                file_url = f"{base_url}{file_url}"
            
            logger.info(f"📎 Generated public URL for {attachment_obj.original_filename}: {file_url}")
            return file_url
            
        except Exception as e:
            logger.error(f"❌ Error getting public URL for attachment: {str(e)}")
            return None
    
    @classmethod
    def create_ticket(cls, ticket) -> Optional[Dict[str, Any]]:
        """
        Create a ticket in Intercom using the official Tickets API.
        
        This replaces the old create_ticket_conversation() method.
        
        API Endpoint: POST /tickets
        Docs: https://developers.intercom.com/docs/references/rest-api/api.intercom.io/tickets/createticket
        
        Args:
            ticket: SupportTicket instance
            
        Returns:
            dict: Intercom ticket data if successful, None otherwise
        """
        if not settings.INTERCOM_ACCESS_TOKEN:
            logger.warning("⚠️ Intercom access token not configured")
            return None
        
        try:
            # 1. Get Intercom Contact ID
            intercom_contact_id = cls.get_or_create_intercom_user(ticket.user)
            if not intercom_contact_id:
                logger.error(f"❌ Cannot create ticket {ticket.id} - failed to get Intercom contact ID")
                return None
            
            # 2. Get Ticket Type ID from database
            from settings.models import IntercomTicketType
            
            ticket_type_config = IntercomTicketType.objects.filter(
                department=ticket.department,
                is_active=True
            ).first()
            
            if not ticket_type_config:
                logger.error(
                    f"❌ No active IntercomTicketType found for department '{ticket.department}'. "
                    f"Please configure in Admin Panel: System Settings → Intercom Ticket Types"
                )
                return None
            
            # 3. Get ticket description (first message or title)
            first_message = ticket.messages.order_by('created_at').first()
            description = first_message.content if first_message else ticket.title
            
            # 4. Get attachment URLs (if any)
            attachment_urls = []
            if first_message and first_message.attachments.exists():
                logger.info(f"📎 Adding {first_message.attachments.count()} attachment URL(s) to ticket...")
                for attachment in first_message.attachments.all():
                    try:
                        public_url = cls.get_attachment_public_url(attachment)
                        if public_url:
                            attachment_urls.append({
                                'url': public_url,
                                'name': attachment.original_filename
                            })
                    except Exception as e:
                        logger.error(f"❌ Failed to get URL for attachment {attachment.id}: {str(e)}")
                        continue
            
            # 5. Build description with attachments
            if attachment_urls:
                description += "\n\n📎 Attachments:\n"
                for att in attachment_urls:
                    description += f"- {att['name']}: {att['url']}\n"
            
            # 6. Build ticket payload
            # ⚠️ CRITICAL: Must use "_default_title_" and "_default_description_"
            payload = {
                "ticket_type_id": ticket_type_config.intercom_ticket_type_id,
                "contacts": [
                    {"id": intercom_contact_id}
                ],
                "ticket_attributes": {
                    # Required default fields (Intercom API requirement)
                    "_default_title_": ticket.title,
                    "_default_description_": description,
                    
                    # Custom attributes (only ones defined in Intercom)
                    "department": ticket.get_department_display(),
                    "status": ticket.get_status_display(),
                    
                    # TODO: Add these to Intercom first, then uncomment:
                    # "fiko_ticket_id": str(ticket.id),
                    # "created_by": ticket.user.get_full_name() or ticket.user.username,
                    # "user_email": ticket.user.email,
                }
            }
            
            logger.info(
                f"📤 Creating Intercom Ticket for Fiko ticket #{ticket.id} "
                f"| Type: {ticket_type_config.name} (ID: {ticket_type_config.intercom_ticket_type_id})"
            )
            logger.debug(f"Payload: {payload}")
            
            # 7. Call Intercom Tickets API
            url = f"{settings.INTERCOM_API_BASE_URL}/tickets"
            response = requests.post(
                url,
                headers=cls.get_headers(),
                json=payload,
                timeout=15
            )
            
            # 8. Handle response
            if response.status_code in (200, 201):
                data = response.json()
                intercom_ticket_id = data.get("id")
                
                # Save Intercom Ticket ID back to Fiko
                ticket.intercom_ticket_id = intercom_ticket_id
                ticket.save(update_fields=["intercom_ticket_id"])
                
                logger.info(
                    f"✅ Created Intercom Ticket {intercom_ticket_id} for Fiko ticket #{ticket.id}"
                )
                
                return data
            
            elif response.status_code == 422:
                logger.error(
                    f"❌ Intercom API validation error for ticket {ticket.id}: "
                    f"{response.text}\n"
                    f"Possible causes:\n"
                    f"1. Invalid ticket_type_id: {ticket_type_config.intercom_ticket_type_id}\n"
                    f"2. Custom attributes not defined in Intercom\n"
                    f"3. Contact ID not found in Intercom"
                )
                return None
            
            else:
                logger.error(
                    f"❌ Intercom API error creating ticket {ticket.id}: "
                    f"{response.status_code} - {response.text}"
                )
                return None
                
        except requests.exceptions.HTTPError as e:
            logger.error(
                f"❌ HTTP error creating Intercom ticket for {ticket.id}: {str(e)}"
            )
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Network error creating Intercom ticket for {ticket.id}: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"❌ Unexpected error creating Intercom ticket for {ticket.id}: {str(e)}")
            return None
    
    @classmethod
    def add_message_to_ticket(cls, message, ticket_id: str) -> Optional[Dict[str, Any]]:
        """
        Add a reply/note to an existing Intercom ticket.
        
        Note: The exact endpoint for adding messages to tickets may vary by API version.
        This is a placeholder - check Intercom docs for your API version.
        
        Args:
            message: SupportMessage instance
            ticket_id: Intercom ticket ID
            
        Returns:
            dict: Response data if successful, None otherwise
        """
        # TODO: Implement based on Intercom API version
        # Possible endpoints:
        # - POST /tickets/{id}/reply
        # - POST /tickets/{id}/notes
        
        logger.warning(
            f"⚠️ add_message_to_ticket not yet implemented for Tickets API. "
            f"Message {message.id} for ticket {ticket_id} was not synced."
        )
        return None
    
    @classmethod
    def update_ticket_status(cls, ticket) -> Optional[Dict[str, Any]]:
        """
        Update ticket status/state in Intercom when status changes in Fiko.
        
        Args:
            ticket: SupportTicket instance with intercom_ticket_id
            
        Returns:
            dict: Response data if successful, None otherwise
        """
        if not ticket.intercom_ticket_id:
            logger.warning(
                f"⚠️ Ticket {ticket.id} has no intercom_ticket_id, cannot update status in Intercom"
            )
            return None
        
        if not settings.INTERCOM_ACCESS_TOKEN:
            logger.warning("⚠️ Intercom access token not configured")
            return None
        
        try:
            # Map Fiko status to Intercom ticket state
            status_mapping = {
                'open': 'submitted',
                'under_review': 'in_progress',
                'support_response': 'in_progress',
                'customer_reply': 'waiting_on_customer',
                'closed': 'resolved',
            }
            
            intercom_state = status_mapping.get(ticket.status, 'submitted')
            
            # TODO: Implement ticket state update endpoint
            # Endpoint might be: PATCH /tickets/{id} or PUT /tickets/{id}
            # Body: {"state": "resolved", "ticket_attributes": {...}}
            
            logger.warning(
                f"⚠️ update_ticket_status not yet fully implemented for Tickets API. "
                f"Ticket {ticket.id} status '{ticket.status}' → '{intercom_state}' was not synced."
            )
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Error updating ticket status for {ticket.id}: {str(e)}")
            return None
    
    # ============================================================================
    # Legacy methods (kept for backward compatibility with old conversation-based tickets)
    # ============================================================================
    
    @classmethod
    def create_ticket_conversation(cls, ticket) -> Optional[Dict[str, Any]]:
        """
        [DEPRECATED] Old method using Conversations API.
        
        This is kept for backward compatibility but should not be used for new tickets.
        Use create_ticket() instead.
        """
        logger.warning(
            f"⚠️ create_ticket_conversation() is deprecated. "
            f"Use create_ticket() for Tickets API instead."
        )
        # Redirect to new method
        return cls.create_ticket(ticket)
    
    @classmethod
    def add_message_to_ticket(cls, message, ticket_id: str) -> bool:
        """
        Add a message/comment to an existing Intercom Ticket (Tickets API).
        
        Args:
            message: SupportMessage instance
            ticket_id: Intercom ticket ID
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # 1. Get attachment URLs (if any)
            attachment_urls = []
            if message.attachments.exists():
                logger.info(f"📎 Adding {message.attachments.count()} attachment URL(s) to message...")
                for attachment in message.attachments.all():
                    try:
                        public_url = cls.get_attachment_public_url(attachment)
                        if public_url:
                            attachment_urls.append({
                                'url': public_url,
                                'name': attachment.original_filename
                            })
                    except Exception as e:
                        logger.error(f"❌ Failed to get URL for attachment {attachment.id}: {str(e)}")
                        continue
            
            # 2. Build message body with attachments
            message_body = message.content
            if attachment_urls:
                message_body += "\n\n📎 Attachments:\n"
                for att in attachment_urls:
                    message_body += f"- {att['name']}: {att['url']}\n"
            
            # 3. Check if message is from user or support
            if message.sender:
                # User message - get their Intercom contact ID
                intercom_contact_id = cls.get_or_create_intercom_user(message.sender)
                
                if not intercom_contact_id:
                    logger.error(f"❌ Could not get Intercom contact for user {message.sender.id}")
                    return False
                
                message_type = "comment"
                author = {
                    "type": "contact",
                    "id": intercom_contact_id
                }
            else:
                # Support message (admin reply)
                message_type = "note"  # Internal note or admin message
                author = {
                    "type": "admin",
                    "id": str(getattr(settings, 'INTERCOM_ADMIN_ID', '0'))
                }
            
            # 4. Prepare API request
            url = f"https://api.intercom.io/tickets/{ticket_id}/reply"
            
            # Get admin_id (required by Intercom API for all replies)
            admin_id = str(getattr(settings, 'INTERCOM_ADMIN_ID', None))
            if not admin_id or admin_id == '0' or admin_id == 'None':
                logger.error("❌ INTERCOM_ADMIN_ID not configured in settings")
                return False
            
            if message.sender:
                # User message - send as contact reply
                payload = {
                    "message_type": "comment",
                    "type": "user",
                    "body": message_body,
                    "intercom_user_id": intercom_contact_id,  # Intercom requires this format
                    "admin_id": int(admin_id)  # Required by Intercom API
                }
            else:
                # Admin message (support)
                payload = {
                    "message_type": "comment",
                    "type": "admin",
                    "admin_id": int(admin_id),
                    "body": message_body
                }
            
            logger.info(f"💬 Adding message to Intercom ticket {ticket_id}")
            
            response = requests.post(
                url,
                headers=cls.get_headers(),
                json=payload,
                timeout=10
            )
            
            if response.status_code in [200, 201]:
                logger.info(f"✅ Added message {message.id} to Intercom ticket {ticket_id}")
                return True
            else:
                logger.error(
                    f"❌ Intercom API error adding message to ticket {ticket_id}: "
                    f"{response.status_code} - {response.text}"
                )
                return False
                
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Request error adding message to Intercom ticket {ticket_id}: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"❌ Unexpected error adding message to ticket {ticket_id}: {str(e)}")
            return False
    
    @classmethod
    def add_message_to_conversation(cls, message, conversation_id: str) -> Optional[Dict[str, Any]]:
        """
        [DEPRECATED] Old method for adding messages to conversations.
        
        Kept for backward compatibility with old conversation-based tickets.
        """
        if not settings.INTERCOM_ACCESS_TOKEN:
            logger.warning("⚠️ Intercom access token not configured")
            return None
        
        try:
            # This still works for old conversation-based tickets
            if message.is_from_support:
                message_data = {
                    "message_type": "comment",
                    "type": "admin",
                    "admin_id": str(settings.INTERCOM_APP_ID),
                    "body": message.content
                }
            else:
                user = message.sender if message.sender else message.ticket.user
                intercom_user_id = cls.get_or_create_intercom_user(user)
                
                if not intercom_user_id:
                    logger.error(f"❌ Cannot add message {message.id} - failed to get Intercom user ID")
                    return None
                
                message_data = {
                    "message_type": "comment",
                    "type": "user",
                    "id": intercom_user_id,
                    "body": message.content
                }
            
            url = f"{settings.INTERCOM_API_BASE_URL}/conversations/{conversation_id}/reply"
            response = requests.post(
                url,
                headers=cls.get_headers(),
                json=message_data,
                timeout=10
            )
            
            if response.status_code == 200:
                logger.info(f"✅ Added message {message.id} to conversation {conversation_id}")
                return response.json()
            else:
                logger.error(
                    f"❌ Failed to add message {message.id}: {response.status_code} - {response.text}"
                )
                return None
                
        except Exception as e:
            logger.error(f"❌ Error adding message {message.id} to conversation: {str(e)}")
            return None
