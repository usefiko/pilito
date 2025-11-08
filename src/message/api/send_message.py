from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db import transaction
from message.models import Conversation, Message
from message.serializers import MessageSerializer, WSMessageSerializer
from message.services.telegram_service import TelegramService
from message.services.instagram_service import InstagramService
from message.websocket_utils import notify_new_customer_message, broadcast_to_chat_room
import logging

logger = logging.getLogger(__name__)


class SendMessageAPIView(APIView):
    """
    API endpoint for sending messages from support to customers
    Supports both WebSocket real-time delivery and external platform delivery
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request, conversation_id):
        """
        Send a message to a specific conversation
        
        Body parameters:
        - content: Message content (required)
        - type: Message type (default: 'support')
        """
        try:
            content = request.data.get('content', '').strip()
            message_type = request.data.get('type', 'support')
            
            # Validation
            if not content:
                return Response({
                    'error': 'Message content is required',
                    'error_code': 'EMPTY_CONTENT'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            if len(content) > 1000:
                return Response({
                    'error': 'Message content too long (max 1000 characters)',
                    'error_code': 'CONTENT_TOO_LONG'
                }, status=status.HTTP_400_BAD_REQUEST)
                
            if message_type not in ['support', 'marketing']:
                return Response({
                    'error': 'Invalid message type. Must be "support" or "marketing"',
                    'error_code': 'INVALID_TYPE'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Get conversation and verify access
            try:
                conversation = Conversation.objects.select_related('customer', 'user').get(
                    id=conversation_id,
                    user=request.user
                )
            except Conversation.DoesNotExist:
                return Response({
                    'error': 'Conversation not found or access denied',
                    'error_code': 'CONVERSATION_NOT_FOUND'
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Create and save message in database
            with transaction.atomic():
                message = Message.objects.create(
                    conversation=conversation,
                    customer=conversation.customer,
                    content=content,
                    type=message_type,
                    metadata={}  # Initialize metadata
                )
                
                # Update conversation timestamp
                conversation.save()
            
            # Send to external platform (Telegram/Instagram)
            external_result = self._send_to_external_platform(conversation, content)
            
            # Store external message ID in metadata to prevent webhook duplicates
            if external_result.get('success') and external_result.get('message_id'):
                message.metadata = message.metadata or {}
                message.metadata['external_message_id'] = str(external_result.get('message_id'))
                message.metadata['sent_from_app'] = True
                message.save(update_fields=['metadata'])
                logger.info(f"Stored external message_id in metadata: {external_result.get('message_id')}")
            
            # Notify via WebSocket
            self._notify_websocket(message, external_result)
            
            # Serialize response
            serializer = WSMessageSerializer(message)
            
            return Response({
                'status': 'success',
                'message': 'Message sent successfully',
                'data': {
                    'message': serializer.data,
                    'external_send_result': external_result,
                    'conversation_id': conversation_id
                }
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            logger.error(f"Error sending message to conversation {conversation_id}: {e}")
            return Response({
                'error': 'An unexpected error occurred while sending message',
                'error_code': 'INTERNAL_ERROR',
                'details': str(e) if request.user.is_superuser else None
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def _send_to_external_platform(self, conversation, content):
        """Send message to external platform (Telegram/Instagram)"""
        try:
            customer = conversation.customer
            source = conversation.source
            
            if source == 'telegram':
                return self._send_telegram_message(conversation, customer, content)
            elif source == 'instagram':
                return self._send_instagram_message(conversation, customer, content)
            else:
                logger.warning(f"Unknown conversation source: {source}")
                return {'success': False, 'error': 'Unknown conversation source'}
                
        except Exception as e:
            logger.error(f"Error sending to external platform: {e}")
            return {'success': False, 'error': str(e)}
    
    def _send_telegram_message(self, conversation, customer, content):
        """Send message via Telegram API"""
        try:
            telegram_service = TelegramService.get_service_for_conversation(conversation)
            if not telegram_service:
                return {'success': False, 'error': 'Telegram service not available'}
            
            result = telegram_service.send_message_to_customer(customer, content)
            logger.info(f"Telegram send result for conversation {conversation.id}: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Error sending Telegram message: {e}")
            return {'success': False, 'error': str(e)}
    
    def _send_instagram_message(self, conversation, customer, content):
        """Send message via Instagram API"""
        try:
            logger.info(f"📤 [Support] Sending Instagram message...")
            logger.info(f"   Conversation: {conversation.id}")
            logger.info(f"   Customer: {customer.id}")
            logger.info(f"   Content (first 80 chars): {content[:80]}...")
            logger.info(f"   Content length: {len(content)}")
            
            instagram_service = InstagramService.get_service_for_conversation(conversation)
            if not instagram_service:
                logger.warning(f"❌ [Support] Instagram service not available")
                return {'success': False, 'error': 'Instagram service not available'}
            
            result = instagram_service.send_message_to_customer(customer, content)
            logger.info(f"Instagram send result for conversation {conversation.id}: {result}")
            
            if result.get('success'):
                logger.info(f"✅ [Support] Instagram message sent successfully")
                logger.info(f"   Instagram message_id: {result.get('message_id')}")
            else:
                logger.warning(f"❌ [Support] Instagram message send failed: {result.get('error')}")
            
            # ✅ Mark message as sent in cache to prevent duplicate from webhook
            if result.get('success'):
                from django.core.cache import cache
                import hashlib
                
                message_hash = hashlib.md5(
                    f"{conversation.id}:{content}".encode()
                ).hexdigest()
                cache_key = f"instagram_sent_msg_{message_hash}"
                cache.set(cache_key, True, timeout=60)
                logger.info(f"📝 [Support] Cached sent message to prevent webhook duplicate")
                logger.info(f"   Cache key: {cache_key}")
                logger.info(f"   Cache timeout: 60 seconds")
            
            return result
            
        except Exception as e:
            logger.error(f"Error sending Instagram message: {e}")
            return {'success': False, 'error': str(e)}
    
    def _notify_websocket(self, message, external_result):
        """Notify WebSocket clients about new message"""
        try:
            # Notify the specific chat room
            broadcast_to_chat_room(
                message.conversation.id,
                'chat_message',
                {
                    'message': WSMessageSerializer(message).data,
                    'external_send_result': external_result
                }
            )
            
            # Update conversation list for user (without sending the message again)
            from message.websocket_utils import notify_conversation_status_change
            notify_conversation_status_change(message.conversation)
            
            logger.debug(f"WebSocket notification sent for message {message.id}")
            
        except Exception as e:
            logger.error(f"Error sending WebSocket notification: {e}")


class ConversationStatusAPIView(APIView):
    """
    API endpoint for updating conversation status
    """
    permission_classes = [IsAuthenticated]
    
    def patch(self, request, conversation_id):
        """
        Update conversation status
        
        Body parameters:
        - status: New status ('active', 'support_active', 'marketing_active', 'closed')
        """
        try:
            new_status = request.data.get('status')
            
            if not new_status:
                return Response({
                    'error': 'Status is required',
                    'error_code': 'MISSING_STATUS'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            valid_statuses = ['active', 'support_active', 'marketing_active', 'closed']
            if new_status not in valid_statuses:
                return Response({
                    'error': f'Invalid status. Must be one of: {", ".join(valid_statuses)}',
                    'error_code': 'INVALID_STATUS'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Get conversation and verify access
            try:
                conversation = Conversation.objects.get(
                    id=conversation_id,
                    user=request.user
                )
            except Conversation.DoesNotExist:
                return Response({
                    'error': 'Conversation not found or access denied',
                    'error_code': 'CONVERSATION_NOT_FOUND'
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Update status
            old_status = conversation.status
            conversation.status = new_status
            conversation.save()
            
            # Notify via WebSocket about status change
            from message.websocket_utils import notify_conversation_status_change
            notify_conversation_status_change(conversation)
            
            logger.info(f"Conversation {conversation_id} status changed from {old_status} to {new_status}")
            
            return Response({
                'status': 'success',
                'message': 'Conversation status updated successfully',
                'data': {
                    'conversation_id': conversation_id,
                    'old_status': old_status,
                    'new_status': new_status
                }
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error updating conversation status {conversation_id}: {e}")
            return Response({
                'error': 'An unexpected error occurred while updating status',
                'error_code': 'INTERNAL_ERROR'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR) 