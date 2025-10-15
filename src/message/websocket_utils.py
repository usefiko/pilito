import json
import logging
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.utils import timezone
from message.models import Conversation, Message
from message.serializers import WSMessageSerializer, WSConversationSerializer
from django.core.cache import cache

logger = logging.getLogger(__name__)


def notify_new_customer_message(message):
    """
    Notify user about new customer message via WebSocket
    This should only be called for incoming customer messages from external platforms (Telegram/Instagram)
    """
    try:
        # Dedupe: avoid double-broadcasting the same message
        try:
            dedupe_key = f"ws_sent_msg_{message.id}"
            if cache.get(dedupe_key):
                logger.debug(f"WS dedupe: message {message.id} already broadcast, skipping")
                return
            cache.set(dedupe_key, True, timeout=10)
        except Exception:
            pass
        channel_layer = get_channel_layer()
        conversation = message.conversation
        user_id = conversation.user.id
        
        # Serialize message
        message_data = WSMessageSerializer(message).data
        
        logger.info(f"Notifying new customer message: conversation {conversation.id}, user {user_id}")
        
        # Send to chat room if anyone is connected
        chat_group_name = f'chat_{conversation.id}'
        async_to_sync(channel_layer.group_send)(
            chat_group_name,
            {
                'type': 'chat_message',
                'message': message_data,
                'timestamp': timezone.now().isoformat()
            }
        )
        
        # Send to user's conversation list to update conversation summary
        user_group_name = f'user_{user_id}_conversations'
        async_to_sync(channel_layer.group_send)(
            user_group_name,
            {
                'type': 'new_customer_message',
                'conversation_id': conversation.id,
                'message': message_data,
                'timestamp': timezone.now().isoformat()
            }
        )
        
        logger.debug(f"Successfully notified new customer message for conversation {conversation.id}")
        
    except Exception as e:
        logger.error(f"Error notifying new customer message: {e}")


def notify_conversation_status_change(conversation):
    """
    Notify user about conversation status changes
    """
    try:
        channel_layer = get_channel_layer()
        user_id = conversation.user.id
        
        # Serialize conversation
        conversation_data = WSConversationSerializer(conversation).data
        
        logger.info(f"Notifying conversation status change: conversation {conversation.id}, user {user_id}, status {conversation.status}")
        
        # Send to user's conversation list
        user_group_name = f'user_{user_id}_conversations'
        async_to_sync(channel_layer.group_send)(
            user_group_name,
            {
                'type': 'conversation_updated',
                'conversation': conversation_data,
                'timestamp': timezone.now().isoformat()
            }
        )
        
        logger.debug(f"Successfully notified conversation status change for conversation {conversation.id}")
        
    except Exception as e:
        logger.error(f"Error notifying conversation status change: {e}")


def notify_conversation_deleted(conversation_id, user_id):
    """
    Notify user about conversation deletion via WebSocket
    """
    try:
        channel_layer = get_channel_layer()
        
        logger.info(f"Notifying conversation deletion: conversation {conversation_id}, user {user_id}")
        
        # Send to user's conversation list
        user_group_name = f'user_{user_id}_conversations'
        async_to_sync(channel_layer.group_send)(
            user_group_name,
            {
                'type': 'conversation_deleted',
                'conversation_id': conversation_id,
                'timestamp': timezone.now().isoformat()
            }
        )
        
        # Also notify the specific chat room if anyone is connected
        chat_group_name = f'chat_{conversation_id}'
        async_to_sync(channel_layer.group_send)(
            chat_group_name,
            {
                'type': 'conversation_deleted',
                'conversation_id': conversation_id,
                'timestamp': timezone.now().isoformat()
            }
        )
        
        logger.debug(f"Successfully notified conversation deletion for conversation {conversation_id}")
        
    except Exception as e:
        logger.error(f"Error notifying conversation deletion: {e}")


def notify_customer_updated(customer):
    """
    Notify users about customer updates via WebSocket
    """
    try:
        from message.serializers import CustomerSerializer
        channel_layer = get_channel_layer()
        
        # Get all users who have conversations with this customer
        user_ids = customer.conversations.values_list('user_id', flat=True).distinct()
        
        # Serialize customer data
        customer_data = CustomerSerializer(customer).data
        
        logger.info(f"Notifying customer update: customer {customer.id}, users {list(user_ids)}")
        
        for user_id in user_ids:
            # Send to user's customer list
            user_customers_group_name = f'user_{user_id}_customers'
            async_to_sync(channel_layer.group_send)(
                user_customers_group_name,
                {
                    'type': 'customer_updated',
                    'customer_id': customer.id,
                    'customer_data': customer_data,
                    'timestamp': timezone.now().isoformat()
                }
            )
            
            # Also send to conversation list since customer updates affect conversations
            user_conversations_group_name = f'user_{user_id}_conversations'
            async_to_sync(channel_layer.group_send)(
                user_conversations_group_name,
                {
                    'type': 'conversation_updated',
                    'customer_id': customer.id,
                    'customer_data': customer_data,
                    'timestamp': timezone.now().isoformat()
                }
            )
        
        logger.debug(f"Successfully notified customer update for customer {customer.id}")
        
    except Exception as e:
        logger.error(f"Error notifying customer update: {e}")


def notify_customer_deleted(customer_id, user_id):
    """
    Notify user about customer deletion via WebSocket
    """
    try:
        channel_layer = get_channel_layer()
        
        logger.info(f"Notifying customer deletion: customer {customer_id}, user {user_id}")
        
        # Send to user's customer list
        user_customers_group_name = f'user_{user_id}_customers'
        async_to_sync(channel_layer.group_send)(
            user_customers_group_name,
            {
                'type': 'customer_deleted',
                'customer_id': customer_id,
                'timestamp': timezone.now().isoformat()
            }
        )
        
        # Also send to conversation list since customer deletion affects conversations
        user_conversations_group_name = f'user_{user_id}_conversations'
        async_to_sync(channel_layer.group_send)(
            user_conversations_group_name,
            {
                'type': 'customer_deleted',
                'customer_id': customer_id,
                'timestamp': timezone.now().isoformat()
            }
        )
        
        logger.debug(f"Successfully notified customer deletion for customer {customer_id}")
        
    except Exception as e:
        logger.error(f"Error notifying customer deletion: {e}")


def broadcast_to_chat_room(conversation_id, message_type, data):
    """
    Broadcast a message to a specific chat room
    """
    try:
        channel_layer = get_channel_layer()
        chat_group_name = f'chat_{conversation_id}'
        
        logger.info(f"Broadcasting to chat room {chat_group_name}: {message_type}")
        
        async_to_sync(channel_layer.group_send)(
            chat_group_name,
            {
                'type': message_type,
                'timestamp': timezone.now().isoformat(),
                **data
            }
        )
        
        logger.debug(f"Successfully broadcasted {message_type} to chat room {conversation_id}")
        
    except Exception as e:
        logger.error(f"Error broadcasting to chat room {conversation_id}: {e}")


def get_online_users_in_conversation(conversation_id):
    """
    Get list of online users in a conversation (future implementation)
    This would require storing user presence information
    """
    # This is a placeholder for future presence tracking
    return []



def notify_message_read(conversation_id, user_id):
    """
    Notify that messages have been read
    """
    try:
        channel_layer = get_channel_layer()
        chat_group_name = f'chat_{conversation_id}'
        
        logger.debug(f"User {user_id} marked messages as read in conversation {conversation_id}")
        
        async_to_sync(channel_layer.group_send)(
            chat_group_name,
            {
                'type': 'messages_read',
                'user_id': user_id,
                'conversation_id': conversation_id,
                'timestamp': timezone.now().isoformat()
            }
        )
        
    except Exception as e:
        logger.error(f"Error notifying message read: {e}")


class WebSocketNotificationMixin:
    """
    Mixin to add WebSocket notification capabilities to models
    """
    
    def notify_websocket_update(self):
        """
        Override this method in models to define WebSocket notification behavior
        """
        pass

    def notify_websocket_creation(self):
        """
        Notify about model creation via WebSocket
        """
        if hasattr(self, 'conversation'):
            notify_conversation_status_change(self.conversation)

    def notify_websocket_deletion(self):
        """
        Notify about model deletion via WebSocket
        """
        if hasattr(self, 'conversation'):
            notify_conversation_status_change(self.conversation) 