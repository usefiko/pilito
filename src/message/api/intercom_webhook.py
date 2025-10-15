"""
Intercom Webhook Handler

Receives and processes webhook events from Intercom.
Handles conversation events, message events, and contact events.
"""

import hmac
import hashlib
import json
import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

logger = logging.getLogger(__name__)


@method_decorator(csrf_exempt, name='dispatch')
class IntercomWebhookView(APIView):
    """
    Handle incoming webhooks from Intercom.
    
    Verifies webhook signature and processes events.
    
    Webhook Events:
    - conversation.user.created: New conversation started by user
    - conversation.user.replied: User replied to conversation
    - conversation.admin.replied: Admin replied to conversation
    - conversation.admin.closed: Admin closed conversation
    - contact.created: New contact created
    - contact.updated: Contact was updated
    """
    
    permission_classes = []  # Public endpoint (verified via signature)
    authentication_classes = []
    
    def post(self, request):
        """
        Process incoming Intercom webhook.
        
        Request must include X-Hub-Signature header for verification.
        """
        try:
            # Get the signature from headers
            signature = request.META.get('HTTP_X_HUB_SIGNATURE')
            
            if not signature:
                logger.warning("⚠️ Webhook received without signature")
                return Response({
                    'error': 'Missing signature'
                }, status=status.HTTP_401_UNAUTHORIZED)
            
            # Verify webhook signature
            if not self.verify_signature(request.body, signature):
                logger.error("❌ Invalid webhook signature")
                return Response({
                    'error': 'Invalid signature'
                }, status=status.HTTP_401_UNAUTHORIZED)
            
            # Parse webhook data
            webhook_data = request.data
            
            # Get event type
            topic = webhook_data.get('topic')
            data = webhook_data.get('data', {})
            
            logger.info(f"📨 Received Intercom webhook: {topic}")
            
            # Route to appropriate handler
            if topic == 'conversation.user.created':
                return self.handle_conversation_created(data)
            
            elif topic == 'conversation.user.replied':
                return self.handle_user_replied(data)
            
            elif topic == 'conversation.admin.replied':
                return self.handle_admin_replied(data)
            
            elif topic == 'conversation.admin.closed':
                return self.handle_conversation_closed(data)
            
            elif topic == 'contact.created':
                return self.handle_contact_created(data)
            
            elif topic == 'contact.updated':
                return self.handle_contact_updated(data)
            
            # ============ Ticket Topics (Support Tickets) ============
            elif topic == 'ticket.admin.replied':
                return self.handle_ticket_admin_replied(data)
            
            elif topic == 'ticket.contact.replied':
                return self.handle_ticket_contact_replied(data)
            
            elif topic == 'ticket.state.updated':  # Note: dot not underscore!
                return self.handle_ticket_state_updated(data)
            
            elif topic == 'ticket.closed':
                return self.handle_ticket_closed(data)
            
            elif topic == 'ticket.created':
                return self.handle_ticket_created(data)
            
            elif topic == 'ticket.note.created':
                return self.handle_ticket_note_created(data)
            
            else:
                logger.info(f"ℹ️ Unhandled webhook topic: {topic}")
                return Response({'status': 'ignored'}, status=status.HTTP_200_OK)
                
        except json.JSONDecodeError:
            logger.error("❌ Invalid JSON in webhook payload")
            return Response({
                'error': 'Invalid JSON'
            }, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            logger.error(f"❌ Error processing webhook: {str(e)}")
            return Response({
                'error': 'Internal server error'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def verify_signature(self, payload: bytes, signature: str) -> bool:
        """
        Verify Intercom webhook signature.
        
        Intercom sends webhooks with X-Hub-Signature header containing SHA-1 HMAC.
        
        Args:
            payload: Raw request body
            signature: X-Hub-Signature header value (format: "sha1=...")
            
        Returns:
            True if signature is valid, False otherwise
        """
        # Skip verification در development اگر secret تنظیم نشده
        if not settings.INTERCOM_WEBHOOK_SECRET or settings.INTERCOM_WEBHOOK_SECRET == 'TEMP_SECRET_WILL_UPDATE_AFTER_SETUP':
            logger.warning("⚠️ INTERCOM_WEBHOOK_SECRET not configured, skipping verification (DEV MODE)")
            return True  # Allow for testing
        
        try:
            # Intercom uses SHA-1 HMAC (not SHA-256!)
            # Documentation: https://developers.intercom.com/docs/references/webhooks/
            expected_signature = hmac.new(
                settings.INTERCOM_WEBHOOK_SECRET.encode('utf-8'),
                payload,
                hashlib.sha1  # توجه: SHA-1 است نه SHA-256!
            ).hexdigest()
            
            # Remove "sha1=" prefix from signature if present
            if signature.startswith('sha1='):
                signature = signature[5:]
            
            # Compare signatures (constant-time comparison)
            is_valid = hmac.compare_digest(expected_signature, signature)
            
            if is_valid:
                logger.info("✅ Webhook signature verified successfully")
            else:
                logger.error(f"❌ Invalid webhook signature. Expected: {expected_signature[:10]}..., Got: {signature[:10]}...")
            
            return is_valid
            
        except Exception as e:
            logger.error(f"❌ Error verifying signature: {str(e)}")
            return False
    
    def handle_conversation_created(self, data: dict) -> Response:
        """
        Handle new conversation created by user.
        
        Args:
            data: Conversation data from webhook
            
        Returns:
            Response indicating success or failure
        """
        try:
            conversation_id = data.get('item', {}).get('id')
            user_data = data.get('item', {}).get('user', {})
            external_id = user_data.get('external_id')
            
            logger.info(f"💬 New conversation {conversation_id} created by user (external_id: {external_id})")
            
            # TODO: Implement conversation sync to Fiko database
            # This will be handled by ConversationSyncService
            
            return Response({'status': 'processed'}, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"❌ Error handling conversation created: {str(e)}")
            return Response({'status': 'error'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def handle_user_replied(self, data: dict) -> Response:
        """
        Handle user reply in conversation.
        
        Args:
            data: Conversation data from webhook
            
        Returns:
            Response indicating success or failure
        """
        try:
            conversation_id = data.get('item', {}).get('id')
            conversation_parts = data.get('item', {}).get('conversation_parts', {}).get('conversation_parts', [])
            
            if conversation_parts:
                latest_part = conversation_parts[-1]
                message_body = latest_part.get('body')
                
                logger.info(f"💬 User replied to conversation {conversation_id}")
                logger.debug(f"Message: {message_body[:100]}...")
                
                # TODO: Sync reply to Fiko database
                
            return Response({'status': 'processed'}, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"❌ Error handling user reply: {str(e)}")
            return Response({'status': 'error'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def handle_admin_replied(self, data: dict) -> Response:
        """
        Handle admin reply in conversation (old Conversations API).
        
        Note: This is for legacy Intercom Conversations, not Support Tickets.
        Support Tickets use handle_ticket_admin_replied() instead.
        
        Args:
            data: Conversation data from webhook
            
        Returns:
            Response indicating success or failure
        """
        try:
            conversation_id = data.get('item', {}).get('id')
            conversation_parts = data.get('item', {}).get('conversation_parts', {}).get('conversation_parts', [])
            
            if conversation_parts:
                latest_part = conversation_parts[-1]
                admin_name = latest_part.get('author', {}).get('name', 'Admin')
                message_body = latest_part.get('body')
                
                logger.info(f"👨‍💼 Admin {admin_name} replied to conversation {conversation_id}")
                logger.debug(f"Message: {message_body[:100] if message_body else 'N/A'}...")
                
                # Note: Conversation model doesn't have intercom_conversation_id field
                # This is for informational purposes only (displayed in chat widget)
                logger.info("ℹ️ Conversation admin reply logged (displayed in chat widget)")
                
            return Response({'status': 'processed'}, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"❌ Error handling admin reply: {str(e)}")
            return Response({'status': 'error'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def handle_conversation_closed(self, data: dict) -> Response:
        """
        Handle conversation closed by admin.
        
        Args:
            data: Conversation data from webhook
            
        Returns:
            Response indicating success or failure
        """
        try:
            conversation_id = data.get('item', {}).get('id')
            admin_data = data.get('item', {}).get('admin', {})
            admin_name = admin_data.get('name')
            
            logger.info(f"✅ Conversation {conversation_id} closed by {admin_name}")
            
            # TODO: Update conversation status in Fiko database
            
            return Response({'status': 'processed'}, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"❌ Error handling conversation closed: {str(e)}")
            return Response({'status': 'error'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def handle_contact_created(self, data: dict) -> Response:
        """
        Handle new contact created in Intercom.
        
        Args:
            data: Contact data from webhook
            
        Returns:
            Response indicating success or failure
        """
        try:
            contact_id = data.get('item', {}).get('id')
            email = data.get('item', {}).get('email')
            external_id = data.get('item', {}).get('external_id')
            
            logger.info(f"👤 New contact created: {email} (external_id: {external_id})")
            
            # Usually contacts are created from Fiko, so this is informational
            
            return Response({'status': 'processed'}, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"❌ Error handling contact created: {str(e)}")
            return Response({'status': 'error'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def handle_contact_updated(self, data: dict) -> Response:
        """
        Handle contact updated in Intercom.
        
        Args:
            data: Contact data from webhook
            
        Returns:
            Response indicating success or failure
        """
        try:
            contact_id = data.get('item', {}).get('id')
            email = data.get('item', {}).get('email')
            external_id = data.get('item', {}).get('external_id')
            
            logger.info(f"👤 Contact updated: {email} (external_id: {external_id})")
            
            # Can be used to sync updates back to Fiko if needed
            
            return Response({'status': 'processed'}, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"❌ Error handling contact updated: {str(e)}")
            return Response({'status': 'error'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    # ==================== TICKET HANDLERS ====================
    
    def handle_ticket_admin_replied(self, data: dict) -> Response:
        """
        Handle admin reply in Support Ticket.
        Syncs the admin's reply from Intercom to Fiko Support Ticket.
        
        Args:
            data: Ticket data from webhook
            
        Returns:
            Response indicating success or failure
        """
        try:
            from settings.models import SupportTicket, SupportMessage, SupportMessageAttachment
            from django.core.files.base import ContentFile
            import requests as req_lib
            
            # Webhook structure for ticket.admin.replied can be:
            # Option 1: { "type": "...", "item": { "ticket": {...}, "ticket_part": {...} } }
            # Option 2: { "type": "...", "ticket": {...}, "ticket_part": {...} }
            
            # Support both structures
            item = data.get('item', data)  # If no 'item', use data itself
            ticket_data = item.get('ticket', {})
            ticket_part = item.get('ticket_part', {})
            
            # Extract ticket ID (prefer ticket_id, fallback to id)
            intercom_ticket_id = str(ticket_data.get('id') or ticket_data.get('ticket_id'))
            
            if not ticket_part:
                logger.warning(f"⚠️ No ticket_part in admin reply for ticket {intercom_ticket_id}")
                return Response({'status': 'no_content'}, status=status.HTTP_200_OK)
            
            # Check part type
            part_type = ticket_part.get('part_type')
            author = ticket_part.get('author', {})
            body = ticket_part.get('body', '')
            attachments = ticket_part.get('attachments', [])
            
            # Skip if no body (e.g., pure state changes)
            if not body:
                logger.info(f"ℹ️ Skipping ticket part with no body (part_type: {part_type})")
                return Response({'status': 'no_content'}, status=status.HTTP_200_OK)
            
            # Only process replies from admins (not bots or system messages)
            author_type = author.get('type', '')
            if author_type not in ['admin', 'team']:
                logger.info(f"ℹ️ Skipping non-admin author type: {author_type}")
                return Response({'status': 'ignored'}, status=status.HTTP_200_OK)
            
            admin_name = author.get('name', 'Support Team')
            
            # Extract images from HTML body and add to attachments list
            import re
            from html import unescape
            
            # Find all <img> tags in body and extract URLs
            img_pattern = r'<img[^>]+src=["\']([^"\']+)["\'][^>]*>'
            img_urls = re.findall(img_pattern, body)
            
            # If images found in HTML, add them to attachments list
            if img_urls:
                logger.info(f"📸 Found {len(img_urls)} embedded image(s) in HTML body")
                for img_url in img_urls:
                    # Extract filename from URL (last part after /)
                    filename = img_url.split('/')[-1].split('?')[0]  # Remove query params
                    if not filename or filename == '':
                        filename = 'image.jpg'
                    
                    # Add to attachments list if not already there
                    if not any(att.get('url') == img_url for att in attachments):
                        attachments.append({
                            'url': img_url,
                            'name': filename,
                            'content_type': 'image/jpeg'  # Default to JPEG
                        })
                        logger.info(f"📎 Added embedded image as attachment: {filename}")
            
            # Clean HTML properly - preserve content, remove tags
            # Convert basic HTML line breaks and paragraphs
            body = (
                body.replace("<br>", "\n")
                    .replace("<br/>", "\n")
                    .replace("<br />", "\n")
                    .replace("</p>", "\n")
            )
            
            # Remove opening paragraph tags
            body = re.sub(r'<p[^>]*>', '', body)
            
            # Remove <img> tags (we already extracted them)
            body = re.sub(r'<img[^>]*>', '', body)
            
            # Remove <div> tags
            body = re.sub(r'<div[^>]*>', '', body)
            body = re.sub(r'</div>', '', body)
            
            # Decode HTML entities (e.g., &amp; → &)
            body = unescape(body)
            
            # Remove extra whitespace and non-printable chars
            body = re.sub(r'\s+\n', '\n', body).strip()
            
            # If body is empty after cleaning but we have attachments, use placeholder
            if not body and attachments:
                body = "[📎 Image attachment]"
            
            # Find Fiko ticket by intercom_ticket_id
            try:
                fiko_ticket = SupportTicket.objects.get(intercom_ticket_id=intercom_ticket_id)
            except SupportTicket.DoesNotExist:
                logger.error(f"❌ Fiko ticket not found for Intercom ticket {intercom_ticket_id}")
                return Response({'status': 'ticket_not_found'}, status=status.HTTP_404_NOT_FOUND)
            
            # Create support message in Fiko
            # Use update_fields to prevent triggering signals that would sync back to Intercom
            support_message = SupportMessage(
                ticket=fiko_ticket,
                content=body,
                sender=None,  # Admin message, not from a User
                is_from_support=True
            )
            # Set a flag to skip Intercom sync (checked in signal)
            support_message._skip_intercom_sync = True
            support_message.save()
            
            # Download and save attachments from Intercom (if any)
            if attachments:
                logger.info(f"📎 Downloading {len(attachments)} attachment(s) from Intercom...")
                for attachment_data in attachments:
                    try:
                        attachment_url = attachment_data.get('url')
                        attachment_name = attachment_data.get('name', 'attachment')
                        attachment_type = attachment_data.get('content_type', 'application/octet-stream')
                        
                        if not attachment_url:
                            logger.warning(f"⚠️ Attachment without URL: {attachment_data}")
                            continue
                        
                        # Download the file from Intercom
                        logger.info(f"⬇️ Downloading: {attachment_name} from {attachment_url}")
                        file_response = req_lib.get(attachment_url, timeout=30)
                        file_response.raise_for_status()
                        
                        # Create ContentFile from downloaded data
                        file_content = ContentFile(file_response.content, name=attachment_name)
                        
                        # Create attachment in Django
                        attachment_obj = SupportMessageAttachment.objects.create(
                            message=support_message,
                            file=file_content
                        )
                        
                        logger.info(f"✅ Saved attachment: {attachment_name} ({attachment_obj.file_size} bytes)")
                        
                    except Exception as e:
                        logger.error(f"❌ Failed to download attachment {attachment_name}: {str(e)}")
                        continue
            
            # Update ticket status if needed
            if fiko_ticket.status == 'open':
                fiko_ticket.status = 'support_response'
                fiko_ticket.save(update_fields=['status', 'updated_at'])
            
            logger.info(
                f"✅ Synced admin reply from Intercom ticket {intercom_ticket_id} "
                f"to Fiko ticket #{fiko_ticket.id} as message #{support_message.id}"
            )
            
            # TODO: Send WebSocket notification to frontend for real-time update
            
            return Response({
                'status': 'synced',
                'fiko_ticket_id': fiko_ticket.id,
                'message_id': support_message.id
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"❌ Error handling ticket admin reply: {str(e)}")
            return Response({'status': 'error'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def handle_ticket_contact_replied(self, data: dict) -> Response:
        """Handle customer reply in ticket (usually not needed as it originates from Fiko)"""
        logger.info("📝 Ticket contact replied (usually no action needed)")
        return Response({'status': 'acknowledged'}, status=status.HTTP_200_OK)
    
    def handle_ticket_state_updated(self, data: dict) -> Response:
        """
        Handle ticket state/status change.
        Syncs status from Intercom to Fiko.
        """
        try:
            from settings.models import SupportTicket
            
            ticket_data = data.get('item', {})
            intercom_ticket_id = ticket_data.get('id')
            ticket_state = ticket_data.get('ticket_state', {})
            new_state = ticket_state.get('category', '')
            
            logger.info(f"🔄 Ticket state updated: {intercom_ticket_id} → {new_state}")
            
            # Find Fiko ticket
            try:
                fiko_ticket = SupportTicket.objects.get(intercom_ticket_id=intercom_ticket_id)
            except SupportTicket.DoesNotExist:
                logger.error(f"❌ Fiko ticket not found for Intercom ticket {intercom_ticket_id}")
                return Response({'status': 'ticket_not_found'}, status=status.HTTP_404_NOT_FOUND)
            
            # Map Intercom state to Fiko status
            state_mapping = {
                'submitted': 'open',
                'in_progress': 'under_review',
                'waiting_on_customer': 'support_response',
                'resolved': 'closed',
            }
            
            fiko_status = state_mapping.get(new_state)
            
            if fiko_status and fiko_ticket.status != fiko_status:
                old_status = fiko_ticket.status
                fiko_ticket.status = fiko_status
                fiko_ticket.save(update_fields=['status', 'updated_at'])
                
                logger.info(
                    f"✅ Updated Fiko ticket #{fiko_ticket.id} status: {old_status} → {fiko_status}"
                )
            
            return Response({'status': 'synced'}, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"❌ Error handling ticket state update: {str(e)}")
            return Response({'status': 'error'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def handle_ticket_closed(self, data: dict) -> Response:
        """Handle ticket closed event"""
        try:
            from settings.models import SupportTicket
            
            ticket_data = data.get('item', {})
            intercom_ticket_id = ticket_data.get('id')
            
            logger.info(f"🔒 Ticket closed: {intercom_ticket_id}")
            
            try:
                fiko_ticket = SupportTicket.objects.get(intercom_ticket_id=intercom_ticket_id)
                
                if fiko_ticket.status != 'closed':
                    fiko_ticket.status = 'closed'
                    fiko_ticket.save(update_fields=['status', 'updated_at'])
                    logger.info(f"✅ Closed Fiko ticket #{fiko_ticket.id}")
                
            except SupportTicket.DoesNotExist:
                logger.error(f"❌ Fiko ticket not found for Intercom ticket {intercom_ticket_id}")
            
            return Response({'status': 'processed'}, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"❌ Error handling ticket closed: {str(e)}")
            return Response({'status': 'error'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def handle_ticket_created(self, data: dict) -> Response:
        """Handle ticket created (informational, tickets are created from Fiko)"""
        logger.info("🎫 Ticket created in Intercom (informational)")
        return Response({'status': 'acknowledged'}, status=status.HTTP_200_OK)
    
    def handle_ticket_note_created(self, data: dict) -> Response:
        """Handle internal note added to ticket"""
        logger.info("📝 Ticket note created (internal)")
        return Response({'status': 'acknowledged'}, status=status.HTTP_200_OK)

