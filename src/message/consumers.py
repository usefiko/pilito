import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from accounts.functions.jwt import validate_token, claim_token
from message.models import Conversation, Message, Customer
from message.serializers import WSConversationSerializer, WSMessageSerializer, CustomerSerializer
from accounts.models import User
from rest_framework.renderers import JSONRenderer
from django.core.cache import cache
from django.utils import timezone
import shortuuid
from django.conf import settings
from django.db import models
from message.services.telegram_service import TelegramService
from message.services.instagram_service import InstagramService
from message.websocket_pagination import WebSocketPagination

logger = logging.getLogger(__name__)


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # Get conversation ID from URL route
        self.conversation_id = self.scope['url_route']['kwargs']['conversation_id']
        self.conversation_group_name = f'chat_{self.conversation_id}'
        
        # Check if user is already authenticated by middleware
        user = self.scope.get('user')
        if user and not user.is_anonymous:
            self.user = user
            logger.debug(f"User {self.user.id} connecting to conversation {self.conversation_id}")
        else:
            # Try to get user from token if middleware didn't authenticate
            user, error_message = await self.get_user_from_token()
            if user:
                self.user = user
                logger.debug(f"User {self.user.id} authenticated via token for conversation {self.conversation_id}")
            else:
                # For development: use first available user
                if getattr(settings, 'DEBUG', False):
                    user = await self.get_default_user()
                    if user:
                        self.user = user
                        logger.debug(f"Development mode: Using default user {self.user.id} for conversation {self.conversation_id}")
                    else:
                        logger.warning("WebSocket connection rejected: No user available")
                        await self.send(text_data=json.dumps({
                            'type': 'authentication_error',
                            'message': 'Authentication required',
                            'error_code': 'NO_USER_AVAILABLE',
                            'timestamp': timezone.now().isoformat()
                        }))
                        await self.close(code=4001)  # Custom close code for auth error
                        return
                else:
                    logger.warning(f"WebSocket connection rejected: {error_message}")
                    await self.send(text_data=json.dumps({
                        'type': 'authentication_error',
                        'message': error_message or 'Authentication required',
                        'error_code': 'AUTH_REQUIRED',
                        'timestamp': timezone.now().isoformat()
                    }))
                    await self.close(code=4001)  # Custom close code for auth error
                    return
        
        # Check conversation access
        has_access = await self.check_conversation_access()
        if not has_access:
            logger.warning(f"User {self.user.id} denied access to conversation {self.conversation_id}")
            await self.close(code=1008)
            return
        
        # 🔒 Check if user already has an active connection to this conversation
        # If yes, close old connections to prevent duplicate messages
        user_connection_key = f"ws_chat_{self.user.id}_{self.conversation_id}"
        old_channel = cache.get(user_connection_key)
        
        if old_channel and old_channel != self.channel_name:
            logger.info(f"User {self.user.id} reconnecting to conversation {self.conversation_id}, closing old connection")
            try:
                await self.channel_layer.send(
                    old_channel,
                    {
                        'type': 'close_connection',
                        'reason': 'duplicate_connection'
                    }
                )
            except Exception as e:
                logger.warning(f"Could not close old connection: {e}")
        
        # Store this channel as the active one (expires after 1 hour)
        cache.set(user_connection_key, self.channel_name, timeout=3600)
        
        # Join conversation group with timeout
        try:
            import asyncio
            await asyncio.wait_for(
                self.channel_layer.group_add(
                    self.conversation_group_name,
                    self.channel_name
                ),
                timeout=5.0
            )
        except asyncio.TimeoutError:
            logger.error(f"Timeout joining conversation group {self.conversation_group_name}")
            await self.close(code=1008)
            return
        
        # Set user as online for this conversation
        await self.set_user_online()
        
        await self.accept()
        logger.debug(f"User {self.user.id} connected to conversation {self.conversation_id}")
        
        # ✅ Send connection established confirmation
        await self.send(text_data=json.dumps({
            'type': 'connection_established',
            'message': '✅ Chat WebSocket connected successfully',
            'conversation_id': self.conversation_id,
            'timestamp': timezone.now().isoformat()
        }))
        
        # Send recent messages when user connects with timeout
        try:
            import asyncio
            await asyncio.wait_for(self.send_recent_messages(), timeout=10.0)
            await asyncio.wait_for(self.notify_user_presence(True), timeout=5.0)
        except asyncio.TimeoutError:
            logger.error(f"Timeout during chat connection setup for user {self.user.id}")
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Connection timeout - please refresh',
                'timestamp': timezone.now().isoformat()
            }))

    async def disconnect(self, close_code):
        logger.debug(f"User {getattr(self, 'user', 'Unknown').id if hasattr(self, 'user') else 'Unknown'} disconnecting from conversation {getattr(self, 'conversation_id', 'Unknown')}")
        
        try:
            # Clear user connection cache if this is the active connection
            if hasattr(self, 'user') and hasattr(self, 'conversation_id'):
                user_connection_key = f"ws_chat_{self.user.id}_{self.conversation_id}"
                cached_channel = cache.get(user_connection_key)
                if cached_channel == self.channel_name:
                    cache.delete(user_connection_key)
                    logger.debug(f"Cleared connection cache for user {self.user.id}, conversation {self.conversation_id}")
        except Exception as e:
            logger.warning(f"Error clearing connection cache: {e}")
        
        try:
            # Set user as offline with timeout
            if hasattr(self, 'user') and hasattr(self, 'conversation_id'):
                import asyncio
                await asyncio.wait_for(self.set_user_offline(), timeout=2.0)
                await asyncio.wait_for(self.notify_user_presence(False), timeout=2.0)
        except (asyncio.TimeoutError, Exception) as e:
            logger.warning(f"Error during user offline cleanup: {e}")
        
        try:
            # Leave conversation group with timeout
            if hasattr(self, 'conversation_group_name'):
                import asyncio
                await asyncio.wait_for(
                    self.channel_layer.group_discard(
                        self.conversation_group_name,
                        self.channel_name
                    ),
                    timeout=2.0
                )
        except (asyncio.TimeoutError, Exception) as e:
            logger.warning(f"Error during group cleanup: {e}")

    async def receive(self, text_data):
        try:
            text_data_json = json.loads(text_data)
            message_type = text_data_json.get('type', 'chat_message')
            
            if message_type == 'chat_message':
                await self.handle_chat_message(text_data_json)
            elif message_type == 'mark_read':
                await self.handle_mark_read(text_data_json)
            elif message_type == 'get_messages':
                # Handle request for paginated messages
                filters = text_data_json.get('filters', {})
                await self.send_recent_messages(filters)
            elif message_type == 'load_more_messages':
                # Handle request for more messages (pagination)
                filters = text_data_json.get('filters', {})
                await self.send_recent_messages(filters)
            elif message_type == 'submit_feedback':
                # Handle message feedback submission
                await self.handle_submit_feedback(text_data_json)
                
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'error': 'Invalid JSON format'
            }))

    async def handle_chat_message(self, data):
        content = data.get('content', '').strip()
        message_type = data.get('message_type', 'support')  # Default to support, but allow customer messages
        
        if not content:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'error': 'Message content cannot be empty'
            }))
            return
            
        # Validate message type
        if message_type not in ['support', 'customer']:
            message_type = 'support'  # Default fallback
            
        # Save message to database
        message = await self.save_message(content, message_type)
        if not message:
            await self.send(text_data=json.dumps({
                'type': 'error', 
                'error': 'Failed to save message'
            }))
            return
        
        # Handle different message types
        external_send_result = None  # Initialize to avoid undefined variable error
        
        if message_type == 'customer':
            # For customer messages, AI response will be handled by Django signals automatically
            # No need to trigger here to avoid duplicate processing
            logger.info(f"Customer message {message.id} saved - AI processing will be handled by signals")
        else:
            # For support messages, send to external platform (Telegram/Instagram)
            external_send_result = await self.send_to_external_platform(message)
        
        # Send message to conversation group
        try:
            import asyncio
            await asyncio.wait_for(
                self.channel_layer.group_send(
                    self.conversation_group_name,
                    {
                        'type': 'chat_message',
                        'message': await self.serialize_message(message),
                        'external_send_result': external_send_result
                    }
                ),
                timeout=5.0
            )
        except asyncio.TimeoutError:
            logger.error(f"Timeout sending message to conversation group {self.conversation_group_name}")
        
        # Notify conversation list updates (update conversation timestamp/summary)
        try:
            import asyncio
            await asyncio.wait_for(self.notify_conversation_update(), timeout=3.0)
        except asyncio.TimeoutError:
            logger.error(f"Timeout notifying conversation update for {self.conversation_id}")

    async def send_to_external_platform(self, message):
        """Send support message to external platform (Telegram/Instagram)"""
        try:
            conversation = await self.get_conversation()
            if not conversation:
                return {'success': False, 'error': 'Conversation not found'}
            
            customer = conversation.customer
            source = conversation.source
            
            if source == 'telegram':
                return await self.send_telegram_message(conversation, customer, message.content)
            elif source == 'instagram':
                return await self.send_instagram_message(conversation, customer, message.content)
            else:
                return {'success': False, 'error': 'Unknown conversation source'}
                
        except Exception as e:
            logger.error(f"Error sending to external platform: {e}")
            return {'success': False, 'error': str(e)}

    @database_sync_to_async
    def send_telegram_message(self, conversation, customer, message_text):
        """Send message via Telegram API"""
        try:
            telegram_service = TelegramService.get_service_for_conversation(conversation)
            if not telegram_service:
                return {'success': False, 'error': 'Telegram service not available'}
            
            result = telegram_service.send_message_to_customer(customer, message_text)
            logger.info(f"Telegram send result: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Error sending Telegram message: {e}")
            return {'success': False, 'error': str(e)}

    @database_sync_to_async 
    def send_instagram_message(self, conversation, customer, message_text):
        """Send message via Instagram API"""
        try:
            instagram_service = InstagramService.get_service_for_conversation(conversation)
            if not instagram_service:
                return {'success': False, 'error': 'Instagram service not available'}
            
            result = instagram_service.send_message_to_customer(customer, message_text)
            logger.info(f"Instagram send result: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Error sending Instagram message: {e}")
            return {'success': False, 'error': str(e)}

    # REMOVED: handle_customer_message_ai_trigger method
    # AI response processing is now handled exclusively by Django signals to prevent duplicate responses

    # REMOVED: check_ai_should_handle method
    # This logic is now handled in Django signals

    async def handle_mark_read(self, data):
        # Mark messages as read
        await self.mark_messages_read()
        
        # Notify about read status
        await self.channel_layer.group_send(
            self.conversation_group_name,
            {
                'type': 'messages_read',
                'user_id': self.user.id
            }
        )

    async def handle_submit_feedback(self, data):
        """Handle feedback submission for AI messages via WebSocket"""
        message_id = data.get('message_id')
        feedback_type = data.get('feedback', '').lower()
        comment = data.get('comment', '').strip()[:500]  # Max 500 chars
        
        # Validate required fields
        if not message_id:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'error': 'message_id is required'
            }))
            return
        
        # Validate feedback type
        if feedback_type not in ['positive', 'negative', 'none']:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'error': 'Invalid feedback type. Must be "positive", "negative", or "none"'
            }))
            return
        
        # Update message feedback
        result = await self.update_message_feedback(message_id, feedback_type, comment)
        
        if result['success']:
            # Send success response to the sender
            await self.send(text_data=json.dumps({
                'type': 'feedback_submitted',
                'success': True,
                'data': result['data']
            }))
            
            # Notify all users in the conversation about the feedback update
            await self.channel_layer.group_send(
                self.conversation_group_name,
                {
                    'type': 'feedback_updated',
                    'message_id': message_id,
                    'feedback': result['data']['feedback'],
                    'comment': result['data']['comment'],
                    'feedback_at': result['data']['feedback_at']
                }
            )
        else:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'error': result['error']
            }))

    # WebSocket message handlers
    async def chat_message(self, event):
        message = event['message']
        external_send_result = event.get('external_send_result', {})
        
        # Use DRF's JSONRenderer to properly handle datetime serialization
        response_data = {
            'type': 'chat_message',
            'message': message,
            'external_send_result': external_send_result
        }
        json_data = JSONRenderer().render(response_data).decode('utf-8')
        
        await self.send(text_data=json_data)



    async def messages_read(self, event):
        await self.send(text_data=json.dumps({
            'type': 'messages_read',
            'user_id': event['user_id']
        }))

    async def close_connection(self, event):
        """Handle duplicate connection - close this old connection silently"""
        reason = event.get('reason', 'unknown')
        logger.info(f"Silently closing old connection {self.channel_name} due to: {reason}")
        
        # 🔇 Don't send message to frontend - close silently to prevent refresh loop
        # Frontend should not auto-reconnect when server closes duplicate connections
        await self.close(code=1000)  # Normal closure

    async def ai_message(self, event):
        """Handle AI message broadcasts to chat room"""
        message = event['message']
        
        # Use DRF's JSONRenderer to properly handle datetime serialization
        response_data = {
            'type': 'ai_message',
            'message': message,
            'conversation_id': event.get('conversation_id'),
            'is_ai_response': event.get('is_ai_response', True)
        }
        json_data = JSONRenderer().render(response_data).decode('utf-8')
        
        await self.send(text_data=json_data)
        logger.debug(f"Sent AI message to chat room for conversation {event.get('conversation_id')}")

    async def conversation_deleted(self, event):
        """Handle conversation deletion broadcasts"""
        await self.send(text_data=json.dumps({
            'type': 'conversation_deleted',
            'conversation_id': event['conversation_id'],
            'timestamp': event['timestamp'],
            'message': 'This conversation has been deleted'
        }))
        logger.debug(f"Notified conversation deletion: {event['conversation_id']}")

    async def feedback_updated(self, event):
        """Handle feedback update broadcasts"""
        await self.send(text_data=json.dumps({
            'type': 'feedback_updated',
            'message_id': event['message_id'],
            'feedback': event['feedback'],
            'comment': event['comment'],
            'feedback_at': event['feedback_at']
        }))
        logger.debug(f"Notified feedback update for message {event['message_id']}")

    # Database operations
    @database_sync_to_async
    def update_message_feedback(self, message_id, feedback_type, comment=''):
        """Update feedback for a message"""
        try:
            # Get message and verify ownership
            message = Message.objects.select_related('conversation', 'conversation__user').get(
                id=message_id,
                conversation__user=self.user,
                conversation_id=self.conversation_id
            )
            
            # Verify it's an AI message
            if message.type != 'AI':
                return {
                    'success': False,
                    'error': 'Feedback can only be submitted for AI responses'
                }
            
            # Update message feedback
            message.feedback = feedback_type
            message.feedback_comment = comment
            message.feedback_at = timezone.now()
            message.save(update_fields=['feedback', 'feedback_comment', 'feedback_at'])
            
            return {
                'success': True,
                'data': {
                    'message_id': message.id,
                    'feedback': message.feedback,
                    'comment': message.feedback_comment,
                    'feedback_at': message.feedback_at.isoformat() if message.feedback_at else None
                }
            }
            
        except Message.DoesNotExist:
            return {
                'success': False,
                'error': 'Message not found or you do not have permission to access it'
            }
        except Exception as e:
            logger.error(f"Error updating message feedback: {e}")
            return {
                'success': False,
                'error': f'Failed to update feedback: {str(e)}'
            }

    @database_sync_to_async
    def get_user_from_token(self):
        """
        Get user from JWT token with proper error handling
        Returns: (user, error_message) tuple
        """
        try:
            # Get token from query string
            query_string = self.scope.get('query_string', b'').decode()
            token = None
            
            for param in query_string.split('&'):
                if param.startswith('token='):
                    token = param.split('=')[1]
                    break
            
            if not token:
                logger.debug("No token provided in query string")
                return None, "No authentication token provided"
                
            # Validate JWT token
            if not validate_token(token):
                logger.warning("Invalid or expired JWT token")
                return None, "Invalid or expired authentication token"
                
            payload = claim_token(token)
            user_id = payload.get('user_id')
            if not user_id:
                logger.warning("JWT token missing user_id")
                return None, "Invalid token payload"
                
            user = User.objects.get(id=user_id)
            return user, None
            
        except User.DoesNotExist:
            logger.warning(f"User not found for id: {user_id}")
            return None, "User not found"
        except Exception as e:
            logger.error(f"Error validating token: {e}")
            return None, "Authentication error"

    @database_sync_to_async
    def get_default_user(self):
        """
        Get a default user for development/testing when no token is provided
        """
        try:
            # Try to get the first available user
            user = User.objects.first()
            if user:
                logger.debug(f"Using default user: {user.email} (ID: {user.id})")
                return user
            return None
        except Exception:
            return None

    @database_sync_to_async
    def check_conversation_access(self):
        try:
            from django.db import connection
            # Add timeout for database query
            with connection.cursor() as cursor:
                conversation = Conversation.objects.select_related('user').get(
                    id=self.conversation_id,
                    user=self.user
                )
                return True
        except Conversation.DoesNotExist:
            logger.info(f"Conversation {self.conversation_id} not found for user {self.user.id}")
            return False
        except Exception as e:
            logger.error(f"Error checking conversation access: {e}")
            return False

    @database_sync_to_async
    def get_conversation(self):
        try:
            return Conversation.objects.select_related('customer').get(
                id=self.conversation_id,
                user=self.user
            )
        except Conversation.DoesNotExist:
            return None

    @database_sync_to_async
    def save_message(self, content, message_type='support'):
        try:
            conversation = Conversation.objects.get(
                id=self.conversation_id,
                user=self.user
            )
            
            message = Message.objects.create(
                conversation=conversation,
                customer=conversation.customer,
                content=content,
                type=message_type  # Use provided message type
            )
            
            # Update conversation timestamp
            conversation.save()
            
            return message
        except Exception as e:
            logger.error(f"Error saving message: {e}")
            return None

    @database_sync_to_async
    def serialize_message(self, message):
        serializer = WSMessageSerializer(message)
        return serializer.data

    @database_sync_to_async
    def get_recent_messages(self, filters=None):
        try:
            if filters is None:
                # Default pagination for recent messages (larger page size for chat history)
                filters = {'page_size': 50, 'page': 1}
            
            # Initialize pagination
            paginator = WebSocketPagination(filters)
            
            # Get messages for this conversation, ordered by creation time (newest first)
            messages_query = Message.objects.filter(
                conversation_id=self.conversation_id
            ).order_by('-created_at')
            
            # Use WebSocket pagination
            paginated_data = paginator.paginate_data(
                messages_query,
                WSMessageSerializer
            )
            
            # Reverse the data to get chronological order (oldest first) for chat display
            paginated_data['data'] = list(reversed(paginated_data['data']))
            
            return paginated_data
        except Exception as e:
            logger.error(f"Error getting recent messages: {e}")
            return {
                'data': [],
                'pagination': {
                    'count': 0,
                    'page_count': 0,
                    'page_size': 50,
                    'page': 1,
                    'total_pages': 1,
                    'has_next': False,
                    'has_previous': False,
                    'offset': 0,
                    'limit': 50,
                }
            }

    async def send_recent_messages(self, filters=None):
        try:
            message_data = await self.get_recent_messages(filters)
            
            # Use DRF's JSONRenderer to properly handle datetime serialization
            response_data = {
                'type': 'recent_messages',
                'messages': message_data['data'],
                'pagination': message_data['pagination'],
                'count': message_data['pagination']['count'],
                'page_count': message_data['pagination']['page_count'],
                'timestamp': timezone.now().isoformat()
            }
            json_data = JSONRenderer().render(response_data).decode('utf-8')
            
            await self.send(text_data=json_data)
            logger.debug(f"Sent {message_data['pagination']['page_count']}/{message_data['pagination']['count']} recent messages to user {self.user.id} (page {message_data['pagination']['page']})")
        except Exception as e:
            logger.error(f"Error sending recent messages to user {self.user.id}: {e}")
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Failed to load recent messages',
                'timestamp': timezone.now().isoformat()
            }))

    @database_sync_to_async
    def mark_messages_read(self):
        """
        Mark messages as read - but don't interfere with AI processing
        
        Only mark as answered if there's already an AI or support response,
        or if AI is not handling this conversation
        """
        try:
            from AI_model.utils import should_ai_handle_conversation
            from message.models import Conversation
            
            conversation = Conversation.objects.get(id=self.conversation_id)
            ai_handling = should_ai_handle_conversation(conversation)
            
            if not ai_handling:
                # If AI is not handling, safe to mark all as answered
                Message.objects.filter(
                    conversation_id=self.conversation_id,
                    type='customer'
                ).update(is_answered=True)
            else:
                # If AI is handling, only mark messages that have responses
                # Don't mark recent unanswered messages that AI should process
                
                # Mark messages that have AI responses after them
                from django.db import models
                
                # Get messages that have AI responses
                messages_with_responses = Message.objects.filter(
                    conversation_id=self.conversation_id,
                    type='customer',
                    is_answered=False
                ).annotate(
                    has_ai_response=models.Exists(
                        Message.objects.filter(
                            conversation_id=models.OuterRef('conversation_id'),
                            type='AI',
                            created_at__gt=models.OuterRef('created_at')
                        )
                    )
                ).filter(has_ai_response=True)
                
                messages_with_responses.update(is_answered=True)
                
        except Exception as e:
            logger.error(f"Error in mark_messages_read: {str(e)}")
            pass

    async def notify_conversation_update(self):
        # Notify user's conversation list about update
        try:
            user_group_name = f'user_{self.user.id}_conversations'
            import asyncio
            await asyncio.wait_for(
                self.channel_layer.group_send(
                    user_group_name,
                    {
                        'type': 'conversation_updated',
                        'conversation_id': self.conversation_id
                    }
                ),
                timeout=3.0
            )
        except asyncio.TimeoutError:
            logger.error(f"Timeout notifying conversation update for user {self.user.id}")
        except Exception as e:
            logger.error(f"Error notifying conversation update: {e}")

    # User Presence Management
    async def set_user_online(self):
        """Mark user as online for this conversation"""
        try:
            cache_key = f'user_online_{self.user.id}_{self.conversation_id}'
            cache.set(cache_key, True, timeout=300)  # 5 minutes timeout
            logger.debug(f"User {self.user.id} marked as online for conversation {self.conversation_id}")
        except Exception as e:
            logger.error(f"Error setting user online: {e}")

    async def set_user_offline(self):
        """Mark user as offline for this conversation"""
        try:
            cache_key = f'user_online_{self.user.id}_{self.conversation_id}'
            cache.delete(cache_key)
            logger.debug(f"User {self.user.id} marked as offline for conversation {self.conversation_id}")
        except Exception as e:
            logger.error(f"Error setting user offline: {e}")

    async def notify_user_presence(self, is_online):
        """Notify other users about presence change"""
        try:
            if hasattr(self, 'conversation_group_name') and hasattr(self, 'user'):
                import asyncio
                await asyncio.wait_for(
                    self.channel_layer.group_send(
                        self.conversation_group_name,
                        {
                            'type': 'user_presence',
                            'user_id': self.user.id,
                            'username': f"{self.user.first_name} {self.user.last_name}".strip() or self.user.email,
                            'is_online': is_online,
                            'timestamp': timezone.now().isoformat()
                        }
                    ),
                    timeout=3.0
                )
        except asyncio.TimeoutError:
            logger.error(f"Timeout notifying user presence for {self.user.id}")
        except Exception as e:
            logger.error(f"Error notifying user presence: {e}")

    async def user_presence(self, event):
        """Handle user presence updates"""
        # Don't send presence updates to the user themselves
        if event['user_id'] != self.user.id:
            try:
                await self.send(text_data=json.dumps({
                    'type': 'user_presence',
                    'user_id': event['user_id'],
                    'username': event['username'],
                    'is_online': event['is_online'],
                    'timestamp': event['timestamp']
                }))
            except Exception as e:
                logger.error(f"Error sending user presence: {e}")

    @database_sync_to_async
    def get_online_users_in_conversation(self):
        """Get list of online users in this conversation"""
        try:
            # This is a placeholder - you can expand this based on your needs
            cache_pattern = f'user_online_*_{self.conversation_id}'
            # Note: Redis cache doesn't support pattern matching directly in Django
            # For production, you might want to use a different approach
            return []
        except Exception as e:
            logger.error(f"Error getting online users: {e}")
            return []


class ConversationListConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # Check if user is already authenticated by middleware
        user = self.scope.get('user')
        if user and not user.is_anonymous:
            self.user = user
            logger.debug(f"User {self.user.id} connecting to conversation list")
        else:
            # Try to get user from token if middleware didn't authenticate
            user, error_message = await self.get_user_from_token()
            if user:
                self.user = user
                logger.debug(f"User {self.user.id} authenticated via token for conversation list")
            else:
                # For development: use first available user
                if getattr(settings, 'DEBUG', False):
                    user = await self.get_default_user()
                    if user:
                        self.user = user
                        logger.debug(f"Development mode: Using default user {self.user.id} for conversation list")
                    else:
                        logger.warning("ConversationList WebSocket connection rejected: No user available")
                        await self.send(text_data=json.dumps({
                            'type': 'authentication_error',
                            'message': 'Authentication required',
                            'error_code': 'NO_USER_AVAILABLE',
                            'timestamp': timezone.now().isoformat()
                        }))
                        await self.close(code=4001)
                        return
                else:
                    logger.warning(f"ConversationList WebSocket connection rejected: {error_message}")
                    await self.send(text_data=json.dumps({
                        'type': 'authentication_error',
                        'message': error_message or 'Authentication required',
                        'error_code': 'AUTH_REQUIRED',
                        'timestamp': timezone.now().isoformat()
                    }))
                    await self.close(code=4001)
                    return
        
        self.user_group_name = f'user_{self.user.id}_conversations'
        logger.debug(f"User {self.user.id} connecting to conversation list")
        
        # 🔒 Check if user already has an active connection to conversation list
        # If yes, close old connections to prevent duplicate refresh loops
        from django.core.cache import cache
        user_connection_key = f"ws_conversations_{self.user.id}"
        old_channel = cache.get(user_connection_key)
        
        if old_channel and old_channel != self.channel_name:
            logger.info(f"User {self.user.id} reconnecting to conversation list, closing old connection")
            try:
                await self.channel_layer.send(
                    old_channel,
                    {
                        'type': 'close_connection',
                        'reason': 'duplicate_connection'
                    }
                )
            except Exception as e:
                logger.warning(f"Could not close old conversation list connection: {e}")
        
        # Store this channel as the active one (expires after 1 hour)
        cache.set(user_connection_key, self.channel_name, timeout=3600)
        
        # Join user's conversation list group with timeout
        try:
            import asyncio
            await asyncio.wait_for(
                self.channel_layer.group_add(
                    self.user_group_name,
                    self.channel_name
                ),
                timeout=5.0
            )
        except asyncio.TimeoutError:
            logger.error(f"Timeout joining conversation list group for user {self.user.id}")
            await self.close(code=1008)
            return
        
        # Set user as online globally
        await self.set_global_user_online()
        
        await self.accept()
        logger.debug(f"User {self.user.id} connected to conversation list")
        
        # ✅ Send connection established confirmation
        await self.send(text_data=json.dumps({
            'type': 'connection_established',
            'message': '✅ Conversation List WebSocket connected successfully',
            'timestamp': timezone.now().isoformat()
        }))
        
        # Send current conversations with timeout
        try:
            import asyncio
            await asyncio.wait_for(self.send_conversations(), timeout=15.0)
        except asyncio.TimeoutError:
            logger.error(f"Timeout sending initial conversations to user {self.user.id}")
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Connection timeout - please refresh',
                'timestamp': timezone.now().isoformat()
            }))

    async def disconnect(self, close_code):
        logger.debug(f"User {getattr(self, 'user', 'Unknown').id if hasattr(self, 'user') else 'Unknown'} disconnecting from conversation list")
        
        try:
            # Set user as offline globally with timeout
            if hasattr(self, 'user'):
                import asyncio
                await asyncio.wait_for(self.set_global_user_offline(), timeout=2.0)
        except (asyncio.TimeoutError, Exception) as e:
            logger.warning(f"Error during conversation list user offline cleanup: {e}")
        
        try:
            # Leave user's conversation list group with timeout
            if hasattr(self, 'user_group_name'):
                import asyncio
                await asyncio.wait_for(
                    self.channel_layer.group_discard(
                        self.user_group_name,
                        self.channel_name
                    ),
                    timeout=2.0
                )
        except (asyncio.TimeoutError, Exception) as e:
            logger.warning(f"Error during conversation list group cleanup: {e}")

    async def receive(self, text_data):
        try:
            text_data_json = json.loads(text_data)
            message_type = text_data_json.get('type', 'get_conversations')
            
            if message_type == 'get_conversations':
                filters = text_data_json.get('filters', {})
                # Also extract pagination parameters from query string if not in filters
                filters = self._merge_query_params_with_filters(filters)
                await self.send_conversations(filters)
            elif message_type == 'refresh_conversations':
                filters = text_data_json.get('filters', {})
                filters = self._merge_query_params_with_filters(filters)
                await self.send_conversations(filters)
            elif message_type == 'search_conversations':
                # Support backward compatibility
                search_term = text_data_json.get('search_term', '')
                filters = {'search': search_term}
                filters = self._merge_query_params_with_filters(filters)
                await self.send_conversations(filters)
            elif message_type == 'filter_conversations':
                filters = text_data_json.get('filters', {})
                filters = self._merge_query_params_with_filters(filters)
                await self.send_conversations(filters)
            elif message_type == 'get_conversation_filter_options':
                await self.send_conversation_filter_options()
                
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'error': 'Invalid JSON format'
            }))

    async def close_connection(self, event):
        """Handle duplicate connection - close this old connection silently"""
        reason = event.get('reason', 'unknown')
        logger.info(f"Silently closing old conversation list connection {self.channel_name} due to: {reason}")
        
        # 🔇 Don't send message to frontend - close silently to prevent refresh loop
        await self.close(code=1000)  # Normal closure

    # WebSocket message handlers
    async def conversation_updated(self, event):
        # When a conversation is updated, send fresh conversation list
        logger.debug(f"Conversation updated for user {self.user.id}")
        try:
            await self.send_conversations()
        except Exception as e:
            logger.error(f"Error sending conversation update: {e}")

    async def new_customer_message(self, event):
        # When a new customer message arrives, refresh conversations
        logger.debug(f"New customer message for user {self.user.id}")
        try:
            await self.send_conversations()
            
            # Remove the redundant message forwarding to chat room
            # The message has already been sent to chat room by notify_new_customer_message()
            # Only refresh the conversation list here
            
        except Exception as e:
            logger.error(f"Error handling new customer message: {e}")

    async def ai_response(self, event):
        # When a new AI response arrives, refresh conversations
        logger.debug(f"AI response for user {self.user.id}")
        try:
            await self.send_conversations()
        except Exception as e:
            logger.error(f"Error handling AI response: {e}")

    async def conversation_deleted(self, event):
        # When a conversation is deleted, refresh conversations
        logger.debug(f"Conversation deleted for user {self.user.id}")
        try:
            await self.send_conversations()
        except Exception as e:
            logger.error(f"Error handling conversation deletion: {e}")

    async def customer_deleted(self, event):
        # When a customer is deleted, refresh conversations since it affects related conversations
        logger.debug(f"Customer deleted for user {self.user.id}")
        try:
            await self.send_conversations()
        except Exception as e:
            logger.error(f"Error handling customer deletion: {e}")

    def _merge_query_params_with_filters(self, filters):
        """
        Merge query string parameters with message filters.
        Priority: message filters > query string parameters
        """
        try:
            # Get query string from WebSocket connection
            query_string = self.scope.get('query_string', b'').decode()
            if not query_string:
                return filters
            
            # Parse query parameters
            query_params = {}
            for param in query_string.split('&'):
                if '=' in param:
                    key, value = param.split('=', 1)
                    # Only extract pagination-related parameters
                    if key in ['page_size', 'page', 'limit', 'offset']:
                        # Don't override if already in filters
                        if key not in filters:
                            try:
                                query_params[key] = int(value)
                            except ValueError:
                                logger.warning(f"Invalid query parameter {key}={value}")
            
            # Merge query params into filters (filters take priority)
            merged_filters = {**query_params, **filters}
            logger.debug(f"Merged filters: query_params={query_params}, filters={filters}, result={merged_filters}")
            return merged_filters
            
        except Exception as e:
            logger.error(f"Error merging query params with filters: {e}")
            return filters

    # Database operations
    @database_sync_to_async
    def get_user_from_token(self):
        """
        Get user from JWT token with proper error handling
        Returns: (user, error_message) tuple
        """
        try:
            # Get token from query string
            query_string = self.scope.get('query_string', b'').decode()
            token = None
            
            for param in query_string.split('&'):
                if param.startswith('token='):
                    token = param.split('=')[1]
                    break
            
            if not token:
                logger.debug("No token provided in query string")
                return None, "No authentication token provided"
                
            # Validate JWT token
            if not validate_token(token):
                logger.warning("Invalid or expired JWT token")
                return None, "Invalid or expired authentication token"
                
            payload = claim_token(token)
            user_id = payload.get('user_id')
            if not user_id:
                logger.warning("JWT token missing user_id")
                return None, "Invalid token payload"
                
            user = User.objects.get(id=user_id)
            return user, None
            
        except User.DoesNotExist:
            logger.warning(f"User not found for id: {user_id}")
            return None, "User not found"
        except Exception as e:
            logger.error(f"Error validating token: {e}")
            return None, "Authentication error"

    @database_sync_to_async
    def get_default_user(self):
        """
        Get a default user for development/testing when no token is provided
        """
        try:
            # Try to get the first available user
            user = User.objects.first()
            if user:
                logger.debug(f"Using default user for conversations: {user.email} (ID: {user.id})")
                return user
            return None
        except Exception:
            return None

    @database_sync_to_async
    def get_conversations(self, filters=None):
        try:
            if filters is None:
                filters = {}
            
            # Initialize pagination
            paginator = WebSocketPagination(filters)
            
            # Optimize query with proper select_related and prefetch_related
            conversations_query = Conversation.objects.filter(
                user=self.user
            ).select_related('customer').prefetch_related(
                'customer__tag', 'messages'
            )
            
            # Apply search filter
            search_term = filters.get('search', '')
            if search_term:
                conversations_query = conversations_query.filter(
                    models.Q(title__icontains=search_term) |
                    models.Q(customer__first_name__icontains=search_term) |
                    models.Q(customer__last_name__icontains=search_term) |
                    models.Q(customer__username__icontains=search_term) |
                    models.Q(customer__email__icontains=search_term) |
                    models.Q(messages__content__icontains=search_term)
                ).distinct()
            
            # Apply status filter
            status = filters.get('status')
            if status and status != 'all':
                conversations_query = conversations_query.filter(status=status)
            
            # Apply source filter
            source = filters.get('source')
            if source and source != 'all':
                conversations_query = conversations_query.filter(source=source)
            
            # Apply priority filter
            priority = filters.get('priority')
            if priority and priority != 'all':
                conversations_query = conversations_query.filter(priority=priority)
            
            # Apply customer tag filter
            tag_names = filters.get('tags', [])
            if tag_names:
                conversations_query = conversations_query.filter(customer__tag__name__in=tag_names)
            
            # Apply date range filter
            date_from = filters.get('date_from')
            date_to = filters.get('date_to')
            if date_from:
                conversations_query = conversations_query.filter(created_at__gte=date_from)
            if date_to:
                conversations_query = conversations_query.filter(created_at__lte=date_to)
            
            # Apply unread filter
            unread_only = filters.get('unread_only', False)
            if unread_only:
                conversations_query = conversations_query.filter(
                    messages__type='customer',
                    messages__is_answered=False
                ).distinct()
            
            # Apply ordering
            order_by = filters.get('order_by', '-updated_at')
            valid_orders = [
                'created_at', '-created_at', 'updated_at', '-updated_at', 
                'title', '-title', 'status', '-status', 'priority', '-priority'
            ]
            if order_by in valid_orders:
                conversations_query = conversations_query.order_by(order_by)
            else:
                conversations_query = conversations_query.order_by('-updated_at')
            
            # Use WebSocket pagination
            paginated_data = paginator.paginate_data(
                conversations_query,
                WSConversationSerializer
            )
            
            return paginated_data
        except Exception as e:
            logger.error(f"Error getting conversations: {e}")
            return {
                'data': [],
                'pagination': {
                    'count': 0,
                    'page_count': 0,
                    'page_size': 10,
                    'page': 1,
                    'total_pages': 1,
                    'has_next': False,
                    'has_previous': False,
                    'offset': 0,
                    'limit': 10,
                }
            }

    async def send_conversations(self, filters=None):
        try:
            if filters is None:
                filters = {}
            
            # Add timeout for database operations
            import asyncio
            conversation_data = await asyncio.wait_for(
                self.get_conversations(filters), 
                timeout=10.0  # 10 second timeout
            )
            
            # Use DRF's JSONRenderer to properly handle datetime serialization
            response_data = {
                'type': 'conversations_list',
                'conversations': conversation_data['data'],
                'pagination': conversation_data['pagination'],
                'filters': filters,
                'count': conversation_data['pagination']['count'],  # Total count
                'page_count': conversation_data['pagination']['page_count'],  # Current page count
                'timestamp': timezone.now().isoformat()
            }
            json_data = JSONRenderer().render(response_data).decode('utf-8')
            
            await self.send(text_data=json_data)
            logger.debug(f"Sent {conversation_data['pagination']['page_count']}/{conversation_data['pagination']['count']} conversations to user {self.user.id} (page {conversation_data['pagination']['page']}) with filters: {filters}")
        except asyncio.TimeoutError:
            logger.error(f"Timeout getting conversations for user {self.user.id}")
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Request timeout - please try again',
                'timestamp': timezone.now().isoformat()
            }))
        except Exception as e:
            logger.error(f"Error sending conversations to user {self.user.id}: {e}")
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Failed to load conversations',
                'timestamp': timezone.now().isoformat()
            }))

    @database_sync_to_async
    def get_conversation_filter_options(self):
        """Get available filter options for the current user's conversations"""
        try:
            from message.models import Tag
            
            # Get available statuses for this user's conversations
            available_statuses = Conversation.objects.filter(
                user=self.user
            ).values_list('status', flat=True).distinct()
            
            # Get available sources for this user's conversations
            available_sources = Conversation.objects.filter(
                user=self.user
            ).values_list('source', flat=True).distinct()
            
            # Get available priorities for this user's conversations
            available_priorities = Conversation.objects.filter(
                user=self.user
            ).values_list('priority', flat=True).distinct()
            
            # Get available tags for customers in this user's conversations
            available_tags = Tag.objects.filter(
                customers__conversations__user=self.user
            ).values_list('name', flat=True).distinct()
            
            return {
                'statuses': list(available_statuses),
                'sources': list(available_sources),
                'priorities': list(available_priorities),
                'tags': list(available_tags),
                'order_options': [
                    {'value': '-updated_at', 'label': 'Recently Updated'},
                    {'value': '-created_at', 'label': 'Recently Created'}, 
                    {'value': 'created_at', 'label': 'Oldest First'},
                    {'value': 'title', 'label': 'Title A-Z'},
                    {'value': '-title', 'label': 'Title Z-A'},
                    {'value': 'status', 'label': 'Status A-Z'},
                    {'value': 'priority', 'label': 'Priority A-Z'}
                ]
            }
        except Exception as e:
            logger.error(f"Error getting conversation filter options: {e}")
            return {
                'statuses': [],
                'sources': [],
                'priorities': [],
                'tags': [],
                'order_options': []
            }

    async def send_conversation_filter_options(self):
        """Send available conversation filter options to the client"""
        try:
            import asyncio
            options = await asyncio.wait_for(
                self.get_conversation_filter_options(), 
                timeout=5.0  # 5 second timeout
            )
            
            response_data = {
                'type': 'conversation_filter_options',
                'options': options,
                'timestamp': timezone.now().isoformat()
            }
            json_data = JSONRenderer().render(response_data).decode('utf-8')
            
            await self.send(text_data=json_data)
            logger.debug(f"Sent conversation filter options to user {self.user.id}")
        except asyncio.TimeoutError:
            logger.error(f"Timeout getting conversation filter options for user {self.user.id}")
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Request timeout - please try again',
                'timestamp': timezone.now().isoformat()
            }))
        except Exception as e:
            logger.error(f"Error sending conversation filter options to user {self.user.id}: {e}")
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Failed to load conversation filter options',
                'timestamp': timezone.now().isoformat()
            }))

    # Global User Presence Management
    async def set_global_user_online(self):
        """Mark user as online globally"""
        try:
            cache_key = f'user_global_online_{self.user.id}'
            cache.set(cache_key, {
                'timestamp': timezone.now().isoformat(),
                'status': 'online'
            }, timeout=300)  # 5 minutes timeout
            logger.debug(f"User {self.user.id} marked as globally online")
        except Exception as e:
            logger.error(f"Error setting user globally online: {e}")

    async def set_global_user_offline(self):
        """Mark user as offline globally"""
        try:
            cache_key = f'user_global_online_{self.user.id}'
            cache.delete(cache_key)
            logger.debug(f"User {self.user.id} marked as globally offline")
        except Exception as e:
            logger.error(f"Error setting user globally offline: {e}")

    @database_sync_to_async
    def is_user_online(self, user_id):
        """Check if a user is online globally"""
        try:
            cache_key = f'user_global_online_{user_id}'
            return cache.get(cache_key) is not None
        except Exception as e:
            logger.error(f"Error checking if user {user_id} is online: {e}")
            return False 


class CustomerListConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for managing customer lists with enhanced conversation data.
    
    This consumer sends customer data along with their associated conversations,
    including last messages, unread counts, and conversation status for each customer.
    
    Supported WebSocket Messages:
    - get_customers: Get customers with optional filters
    - refresh_customers: Refresh customer list
    - search_customers: Search customers (legacy support)
    - filter_customers: Filter customers with advanced filters
    - get_filter_options: Get available filter options
    
    Available Filters:
    - search: Text search in name, username, email, phone
    - source: Filter by customer source (telegram, instagram, unknown)
    - tags: Filter by tag names (array)
    - tag_ids: Filter by tag IDs (array)
    - has_email: Filter by email presence (true/false)
    - has_phone: Filter by phone number presence (true/false)
    - conversation_status: Filter by conversation status
    - has_unread: Filter by unread messages presence (true/false)
    - date_from/date_to: Filter by creation date range
    - last_activity_from/last_activity_to: Filter by last activity date range
    - order_by: Sort order (-created_at, -updated_at, first_name, etc.)
    
    Data Structure Sent:
    {
        "type": "customers_list",
        "customers": [
            {
                "id": "customer_id",
                "first_name": "John",
                "last_name": "Doe",
                "username": "johndoe",
                "email": "john@example.com",
                "phone_number": "+1234567890",
                "source": "telegram",
                "tags": [{"id": 1, "name": "VIP"}],
                "conversations": [
                    {
                        "id": "conversation_id",
                        "title": "Conversation Title",
                        "status": "active",
                        "last_message": {
                            "id": "message_id",
                            "content": "Hello!",
                            "type": "customer",
                            "is_ai_response": false,
                            "created_at": "2023-01-01T00:00:00Z"
                        },
                        "unread_count": 2
                    }
                ]
            }
        ],
        "pagination": {...},
        "filters": {...},
        "count": 10,
        "timestamp": "2023-01-01T00:00:00Z"
    }
    """
    async def connect(self):
        # Check if user is already authenticated by middleware
        user = self.scope.get('user')
        if user and not user.is_anonymous:
            self.user = user
            logger.debug(f"User {self.user.id} connecting to customer list")
        else:
            # Try to get user from token if middleware didn't authenticate
            user, error_message = await self.get_user_from_token()
            if user:
                self.user = user
                logger.debug(f"User {self.user.id} authenticated via token for customer list")
            else:
                # For development: use first available user
                if getattr(settings, 'DEBUG', False):
                    user = await self.get_default_user()
                    if user:
                        self.user = user
                        logger.debug(f"Development mode: Using default user {self.user.id} for customer list")
                    else:
                        logger.warning("CustomerList WebSocket connection rejected: No user available")
                        await self.send(text_data=json.dumps({
                            'type': 'authentication_error',
                            'message': 'Authentication required',
                            'error_code': 'NO_USER_AVAILABLE',
                            'timestamp': timezone.now().isoformat()
                        }))
                        await self.close(code=4001)
                        return
                else:
                    logger.warning(f"CustomerList WebSocket connection rejected: {error_message}")
                    await self.send(text_data=json.dumps({
                        'type': 'authentication_error',
                        'message': error_message or 'Authentication required',
                        'error_code': 'AUTH_REQUIRED',
                        'timestamp': timezone.now().isoformat()
                    }))
                    await self.close(code=4001)
                    return
        
        self.user_group_name = f'user_{self.user.id}_customers'
        logger.debug(f"User {self.user.id} connecting to customer list")
        
        # 🔒 Check if user already has an active connection to customer list
        # If yes, close old connections to prevent duplicate refresh loops
        from django.core.cache import cache
        user_connection_key = f"ws_customers_{self.user.id}"
        old_channel = cache.get(user_connection_key)
        
        if old_channel and old_channel != self.channel_name:
            logger.info(f"User {self.user.id} reconnecting to customer list, closing old connection")
            try:
                await self.channel_layer.send(
                    old_channel,
                    {
                        'type': 'close_connection',
                        'reason': 'duplicate_connection'
                    }
                )
            except Exception as e:
                logger.warning(f"Could not close old customer list connection: {e}")
        
        # Store this channel as the active one (expires after 1 hour)
        cache.set(user_connection_key, self.channel_name, timeout=3600)
        
        # Join user's customer list group with timeout
        try:
            import asyncio
            await asyncio.wait_for(
                self.channel_layer.group_add(
                    self.user_group_name,
                    self.channel_name
                ),
                timeout=5.0
            )
        except asyncio.TimeoutError:
            logger.error(f"Timeout joining customer list group for user {self.user.id}")
            await self.close(code=1008)
            return
        
        # Set user as online globally
        await self.set_global_user_online()
        
        await self.accept()
        logger.debug(f"User {self.user.id} connected to customer list")
        
        # ✅ Send connection established confirmation
        await self.send(text_data=json.dumps({
            'type': 'connection_established',
            'message': '✅ Customer List WebSocket connected successfully',
            'timestamp': timezone.now().isoformat()
        }))
        
        # Send current customers with timeout
        try:
            import asyncio
            await asyncio.wait_for(self.send_customers(), timeout=15.0)
        except asyncio.TimeoutError:
            logger.error(f"Timeout sending initial customers to user {self.user.id}")
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Connection timeout - please refresh',
                'timestamp': timezone.now().isoformat()
            }))

    async def disconnect(self, close_code):
        logger.debug(f"User {getattr(self, 'user', 'Unknown').id if hasattr(self, 'user') else 'Unknown'} disconnecting from customer list")
        
        try:
            # Set user as offline globally with timeout
            if hasattr(self, 'user'):
                import asyncio
                await asyncio.wait_for(self.set_global_user_offline(), timeout=2.0)
        except (asyncio.TimeoutError, Exception) as e:
            logger.warning(f"Error during customer list user offline cleanup: {e}")
        
        try:
            # Leave user's customer list group with timeout
            if hasattr(self, 'user_group_name'):
                import asyncio
                await asyncio.wait_for(
                    self.channel_layer.group_discard(
                        self.user_group_name,
                        self.channel_name
                    ),
                    timeout=2.0
                )
        except (asyncio.TimeoutError, Exception) as e:
            logger.warning(f"Error during customer list group cleanup: {e}")

    async def receive(self, text_data):
        try:
            text_data_json = json.loads(text_data)
            message_type = text_data_json.get('type', 'get_customers')
            
            if message_type == 'get_customers':
                filters = text_data_json.get('filters', {})
                # Also extract pagination parameters from query string if not in filters
                filters = self._merge_query_params_with_filters(filters)
                await self.send_customers(filters)
            elif message_type == 'refresh_customers':
                filters = text_data_json.get('filters', {})
                filters = self._merge_query_params_with_filters(filters)
                await self.send_customers(filters)
            elif message_type == 'search_customers':
                # Support backward compatibility
                search_term = text_data_json.get('search_term', '')
                filters = {'search': search_term}
                filters = self._merge_query_params_with_filters(filters)
                await self.send_customers(filters)
            elif message_type == 'filter_customers':
                filters = text_data_json.get('filters', {})
                filters = self._merge_query_params_with_filters(filters)
                await self.send_customers(filters)
            elif message_type == 'get_filter_options':
                await self.send_filter_options()
                
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'error': 'Invalid JSON format'
            }))

    # WebSocket message handlers
    async def close_connection(self, event):
        """Handle duplicate connection - close this old connection silently"""
        reason = event.get('reason', 'unknown')
        logger.info(f"Silently closing old customer list connection {self.channel_name} due to: {reason}")
        
        # 🔇 Don't send message to frontend - close silently to prevent refresh loop
        await self.close(code=1000)  # Normal closure

    async def customer_updated(self, event):
        # When a customer is updated, send fresh customer list
        logger.debug(f"Customer updated for user {self.user.id}")
        try:
            await self.send_customers()
        except Exception as e:
            logger.error(f"Error sending customer update: {e}")

    async def new_customer(self, event):
        # When a new customer is added, refresh customers
        logger.debug(f"New customer for user {self.user.id}")
        try:
            await self.send_customers()
        except Exception as e:
            logger.error(f"Error handling new customer: {e}")

    async def customer_deleted(self, event):
        # When a customer is deleted, refresh customers
        logger.debug(f"Customer deleted for user {self.user.id}")
        try:
            await self.send_customers()
        except Exception as e:
            logger.error(f"Error handling customer deletion: {e}")

    def _merge_query_params_with_filters(self, filters):
        """
        Merge query string parameters with message filters.
        Priority: message filters > query string parameters
        """
        try:
            # Get query string from WebSocket connection
            query_string = self.scope.get('query_string', b'').decode()
            if not query_string:
                return filters
            
            # Parse query parameters
            query_params = {}
            for param in query_string.split('&'):
                if '=' in param:
                    key, value = param.split('=', 1)
                    # Only extract pagination-related parameters
                    if key in ['page_size', 'page', 'limit', 'offset']:
                        # Don't override if already in filters
                        if key not in filters:
                            try:
                                query_params[key] = int(value)
                            except ValueError:
                                logger.warning(f"Invalid query parameter {key}={value}")
            
            # Merge query params into filters (filters take priority)
            merged_filters = {**query_params, **filters}
            logger.debug(f"Merged filters: query_params={query_params}, filters={filters}, result={merged_filters}")
            return merged_filters
            
        except Exception as e:
            logger.error(f"Error merging query params with filters: {e}")
            return filters

    # Database operations
    @database_sync_to_async
    def get_user_from_token(self):
        """
        Get user from JWT token with proper error handling
        Returns: (user, error_message) tuple
        """
        try:
            # Get token from query string
            query_string = self.scope.get('query_string', b'').decode()
            token = None
            
            for param in query_string.split('&'):
                if param.startswith('token='):
                    token = param.split('=')[1]
                    break
            
            if not token:
                logger.debug("No token provided in query string")
                return None, "No authentication token provided"
                
            # Validate JWT token
            if not validate_token(token):
                logger.warning("Invalid or expired JWT token")
                return None, "Invalid or expired authentication token"
                
            payload = claim_token(token)
            user_id = payload.get('user_id')
            if not user_id:
                logger.warning("JWT token missing user_id")
                return None, "Invalid token payload"
                
            user = User.objects.get(id=user_id)
            return user, None
            
        except User.DoesNotExist:
            logger.warning(f"User not found for id: {user_id}")
            return None, "User not found"
        except Exception as e:
            logger.error(f"Error validating token: {e}")
            return None, "Authentication error"

    @database_sync_to_async
    def get_default_user(self):
        """
        Get a default user for development/testing when no token is provided
        """
        try:
            # Try to get the first available user
            user = User.objects.first()
            if user:
                logger.debug(f"Using default user for customers: {user.email} (ID: {user.id})")
                return user
            return None
        except Exception:
            return None

    @database_sync_to_async
    def get_customers(self, filters=None):
        try:
            if filters is None:
                filters = {}
            
            # Initialize pagination
            paginator = WebSocketPagination(filters)
            
            # Base query for customers with this user's conversations
            base_query = Customer.objects.filter(
                conversations__user=self.user
            ).distinct()
            
            # Apply filters to base query
            filtered_query = base_query
            
            # Apply search filter
            search_term = filters.get('search', '')
            if search_term:
                filtered_query = filtered_query.filter(
                    models.Q(first_name__icontains=search_term) |
                    models.Q(last_name__icontains=search_term) |
                    models.Q(username__icontains=search_term) |
                    models.Q(email__icontains=search_term) |
                    models.Q(phone_number__icontains=search_term)
                )
            
            # Apply source filter
            source = filters.get('source')
            if source and source != 'all':
                filtered_query = filtered_query.filter(source=source)
            
            # Apply tag filter (support both tag names and IDs)
            tag_names = filters.get('tags', [])
            tag_ids = filters.get('tag_ids', [])
            if tag_names:
                filtered_query = filtered_query.filter(tag__name__in=tag_names)
            if tag_ids:
                filtered_query = filtered_query.filter(tag__id__in=tag_ids)
            
            # Apply has email filter
            has_email = filters.get('has_email')
            if has_email is not None:
                if has_email in ['true', True, 1, '1']:
                    # Filter customers with email
                    filtered_query = filtered_query.filter(email__isnull=False).exclude(email='')
                elif has_email in ['false', False, 0, '0']:
                    # Filter customers without email
                    filtered_query = filtered_query.filter(
                        models.Q(email__isnull=True) | models.Q(email='')
                    )
            
            # Apply has phone number filter
            has_phone = filters.get('has_phone')
            if has_phone is not None:
                if has_phone in ['true', True, 1, '1']:
                    # Filter customers with phone number
                    filtered_query = filtered_query.filter(phone_number__isnull=False).exclude(phone_number='')
                elif has_phone in ['false', False, 0, '0']:
                    # Filter customers without phone number
                    filtered_query = filtered_query.filter(
                        models.Q(phone_number__isnull=True) | models.Q(phone_number='')
                    )
            
            # Apply conversation status filter
            conversation_status = filters.get('conversation_status')
            if conversation_status and conversation_status != 'all':
                filtered_query = filtered_query.filter(conversations__status=conversation_status)
            
            # Apply unread messages filter
            has_unread = filters.get('has_unread')
            if has_unread is not None:
                if has_unread in ['true', True, 1, '1']:
                    # Filter customers with unread messages
                    filtered_query = filtered_query.filter(
                        conversations__messages__type='customer',
                        conversations__messages__is_answered=False
                    )
                elif has_unread in ['false', False, 0, '0']:
                    # Filter customers without unread messages
                    filtered_query = filtered_query.exclude(
                        conversations__messages__type='customer',
                        conversations__messages__is_answered=False
                    )
            
            # Apply date range filter
            date_from = filters.get('date_from')
            date_to = filters.get('date_to')
            if date_from:
                filtered_query = filtered_query.filter(created_at__gte=date_from)
            if date_to:
                filtered_query = filtered_query.filter(created_at__lte=date_to)
            
            # Apply last activity filter
            last_activity_from = filters.get('last_activity_from')
            last_activity_to = filters.get('last_activity_to')
            if last_activity_from:
                filtered_query = filtered_query.filter(updated_at__gte=last_activity_from)
            if last_activity_to:
                filtered_query = filtered_query.filter(updated_at__lte=last_activity_to)
            
            # Apply ordering
            order_by = filters.get('order_by', '-created_at')
            valid_orders = ['created_at', '-created_at', 'updated_at', '-updated_at', 'first_name', '-first_name']
            if order_by in valid_orders:
                customers_query = filtered_query.order_by(order_by)
            else:
                customers_query = filtered_query.order_by('-created_at')
            
            # Optimize query with select_related and prefetch_related for conversations and messages
            customers_query = customers_query.select_related().prefetch_related(
                'tag',  # Include tags for each customer
                'conversations__messages',
                'conversations'
            )
            
            # Use enhanced serializer that includes conversation data and WebSocket pagination
            from message.serializers import CustomerWithConversationSerializer
            paginated_data = paginator.paginate_data(
                customers_query,
                CustomerWithConversationSerializer,
                context={'user': self.user}
            )
            
            return paginated_data
        except Exception as e:
            logger.error(f"Error getting customers: {e}")
            return {
                'data': [],
                'pagination': {
                    'count': 0,
                    'page_count': 0,
                    'page_size': 10,
                    'page': 1,
                    'total_pages': 1,
                    'has_next': False,
                    'has_previous': False,
                    'offset': 0,
                    'limit': 10,
                }
            }

    async def send_customers(self, filters=None):
        try:
            if filters is None:
                filters = {}
            
            # Add timeout for database operations
            import asyncio
            customer_data = await asyncio.wait_for(
                self.get_customers(filters), 
                timeout=10.0  # 10 second timeout
            )
            
            # Use DRF's JSONRenderer to properly handle datetime serialization
            response_data = {
                'type': 'customers_list',
                'customers': customer_data['data'],  # Now includes conversation data and tags for each customer
                'pagination': customer_data['pagination'],
                'filters': filters,
                'count': customer_data['pagination']['count'],  # Total count regardless of pagination
                'page_count': customer_data['pagination']['page_count'],  # Count in current page
                'timestamp': timezone.now().isoformat()
            }
            json_data = JSONRenderer().render(response_data).decode('utf-8')
            
            await self.send(text_data=json_data)
            logger.debug(f"Sent {customer_data['pagination']['page_count']}/{customer_data['pagination']['count']} customers with conversation data and tags to user {self.user.id} (page {customer_data['pagination']['page']}) with filters: {filters}")
        except asyncio.TimeoutError:
            logger.error(f"Timeout getting customers for user {self.user.id}")
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Request timeout - please try again',
                'timestamp': timezone.now().isoformat()
            }))
        except Exception as e:
            logger.error(f"Error sending customers to user {self.user.id}: {e}")
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Failed to load customers',
                'timestamp': timezone.now().isoformat()
            }))

    @database_sync_to_async
    def get_filter_options(self):
        """Get available filter options for the current user's customers"""
        try:
            from message.models import Tag
            from django.db import connection
            
            # Set a query timeout to prevent hanging
            with connection.cursor() as cursor:
                # Optimize with a single query using annotations
                available_sources = list(Customer.objects.filter(
                    conversations__user=self.user
                ).values_list('source', flat=True).distinct()[:10])  # Limit results
                
                # Get available tags with limit
                available_tags = list(Tag.objects.filter(
                    customers__conversations__user=self.user
                ).values_list('name', flat=True).distinct()[:20])  # Limit results
            
            # Get conversation statuses
            available_statuses = list(Customer.objects.filter(
                conversations__user=self.user
            ).values_list('conversations__status', flat=True).distinct()[:10])
            
            return {
                'sources': available_sources,
                'tags': available_tags,
                'conversation_statuses': available_statuses,
                'has_email_options': [
                    {'value': 'true', 'label': 'Has Email'},
                    {'value': 'false', 'label': 'No Email'},
                    {'value': 'all', 'label': 'All'}
                ],
                'has_phone_options': [
                    {'value': 'true', 'label': 'Has Phone'},
                    {'value': 'false', 'label': 'No Phone'},
                    {'value': 'all', 'label': 'All'}
                ],
                'has_unread_options': [
                    {'value': 'true', 'label': 'Has Unread Messages'},
                    {'value': 'false', 'label': 'No Unread Messages'},
                    {'value': 'all', 'label': 'All'}
                ],
                'order_options': [
                    {'value': '-updated_at', 'label': 'Recently Updated'},
                    {'value': '-created_at', 'label': 'Recently Created'}, 
                    {'value': 'created_at', 'label': 'Oldest First'},
                    {'value': 'first_name', 'label': 'Name A-Z'},
                    {'value': '-first_name', 'label': 'Name Z-A'}
                ]
            }
        except Exception as e:
            logger.error(f"Error getting filter options: {e}")
            return {
                'sources': [],
                'tags': [],
                'conversation_statuses': [],
                'has_email_options': [
                    {'value': 'true', 'label': 'Has Email'},
                    {'value': 'false', 'label': 'No Email'},
                    {'value': 'all', 'label': 'All'}
                ],
                'has_phone_options': [
                    {'value': 'true', 'label': 'Has Phone'},
                    {'value': 'false', 'label': 'No Phone'},
                    {'value': 'all', 'label': 'All'}
                ],
                'has_unread_options': [
                    {'value': 'true', 'label': 'Has Unread Messages'},
                    {'value': 'false', 'label': 'No Unread Messages'},
                    {'value': 'all', 'label': 'All'}
                ],
                'order_options': [
                    {'value': '-updated_at', 'label': 'Recently Updated'},
                    {'value': '-created_at', 'label': 'Recently Created'}, 
                    {'value': 'created_at', 'label': 'Oldest First'},
                    {'value': 'first_name', 'label': 'Name A-Z'},
                    {'value': '-first_name', 'label': 'Name Z-A'}
                ]
            }

    async def send_filter_options(self):
        """Send available filter options to the client"""
        try:
            import asyncio
            options = await asyncio.wait_for(
                self.get_filter_options(), 
                timeout=5.0  # 5 second timeout for filter options
            )
            
            response_data = {
                'type': 'filter_options',
                'options': options,
                'timestamp': timezone.now().isoformat()
            }
            json_data = JSONRenderer().render(response_data).decode('utf-8')
            
            await self.send(text_data=json_data)
            logger.debug(f"Sent filter options to user {self.user.id}")
        except asyncio.TimeoutError:
            logger.error(f"Timeout getting filter options for user {self.user.id}")
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Request timeout - please try again',
                'timestamp': timezone.now().isoformat()
            }))
        except Exception as e:
            logger.error(f"Error sending filter options to user {self.user.id}: {e}")
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Failed to load filter options',
                'timestamp': timezone.now().isoformat()
            }))

    # Global User Presence Management
    async def set_global_user_online(self):
        """Mark user as online globally"""
        try:
            cache_key = f'user_global_online_{self.user.id}'
            cache.set(cache_key, {
                'timestamp': timezone.now().isoformat(),
                'status': 'online'
            }, timeout=300)  # 5 minutes timeout
            logger.debug(f"User {self.user.id} marked as globally online")
        except Exception as e:
            logger.error(f"Error setting user globally online: {e}")

    async def set_global_user_offline(self):
        """Mark user as offline globally"""
        try:
            cache_key = f'user_global_online_{self.user.id}'
            cache.delete(cache_key)
            logger.debug(f"User {self.user.id} marked as globally offline")
        except Exception as e:
            logger.error(f"Error setting user globally offline: {e}")

    @database_sync_to_async
    def is_user_online(self, user_id):
        """Check if a user is online globally"""
        try:
            cache_key = f'user_global_online_{user_id}'
            return cache.get(cache_key) is not None
        except Exception as e:
            logger.error(f"Error checking if user {user_id} is online: {e}")
            return False 