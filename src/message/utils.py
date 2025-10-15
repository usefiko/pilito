"""
Utility functions for message app
"""
import logging
from .websocket_utils import notify_new_customer_message, broadcast_to_chat_room
from .serializers import WSMessageSerializer

logger = logging.getLogger(__name__)


def send_message_notification(message):
    """
    Send WebSocket notification for any message (customer or AI)
    
    This function determines the appropriate notification type based on message type
    and sends real-time updates via WebSocket
    """
    try:
        if message.type == 'customer':
            # For customer messages, use existing function
            notify_new_customer_message(message)
            logger.info(f"Sent customer message notification for message {message.id}")
            
        elif message.type == 'AI':
            # For AI messages, send AI response notification
            send_ai_message_notification(message)
            logger.info(f"Sent AI message notification for message {message.id}")
            
        else:
            # For other message types (support, marketing), send generic notification
            send_generic_message_notification(message)
            logger.info(f"Sent generic message notification for message {message.id}")
            
    except Exception as e:
        logger.error(f"Error sending message notification for message {message.id}: {str(e)}")


def send_ai_message_notification(ai_message):
    """
    Send WebSocket notification specifically for AI messages
    """
    try:
        conversation = ai_message.conversation
        
        # Serialize AI message
        message_data = WSMessageSerializer(ai_message).data
        
        logger.info(f"Sending AI message notification: conversation {conversation.id}")
        
        # Send to chat room if anyone is connected
        broadcast_to_chat_room(
            conversation_id=conversation.id,
            message_type='ai_message',
            data={
                'message': message_data,
                'conversation_id': conversation.id,
                'is_ai_response': True
            }
        )
        
        # Also send to user's conversation list to update conversation summary
        from channels.layers import get_channel_layer
        from asgiref.sync import async_to_sync
        from django.utils import timezone
        
        channel_layer = get_channel_layer()
        user_group_name = f'user_{conversation.user.id}_conversations'
        async_to_sync(channel_layer.group_send)(
            user_group_name,
            {
                'type': 'ai_response',
                'conversation_id': conversation.id,
                'message': message_data,
                'timestamp': timezone.now().isoformat()
            }
        )
        
        logger.debug(f"Successfully sent AI message notification for conversation {conversation.id}")
        
    except Exception as e:
        logger.error(f"Error sending AI message notification: {str(e)}")


def send_generic_message_notification(message):
    """
    Send WebSocket notification for generic messages (support, marketing, etc.)
    """
    try:
        conversation = message.conversation
        
        # Serialize message
        message_data = WSMessageSerializer(message).data
        
        logger.info(f"Sending generic message notification: conversation {conversation.id}, type {message.type}")
        
        # Send to chat room
        broadcast_to_chat_room(
            conversation_id=conversation.id,
            message_type='chat_message',
            data={
                'message': message_data,
                'conversation_id': conversation.id,
                'message_type': message.type
            }
        )
        
        logger.debug(f"Successfully sent generic message notification for conversation {conversation.id}")
        
    except Exception as e:
        logger.error(f"Error sending generic message notification: {str(e)}")


def mark_conversation_messages_as_read(conversation_id, user_id):
    """
    Mark messages in a conversation as read - but don't interfere with AI processing
    """
    try:
        from .models import Message, Conversation
        from .websocket_utils import notify_message_read
        from AI_model.utils import should_ai_handle_conversation
        from django.db import models
        
        conversation = Conversation.objects.get(id=conversation_id)
        ai_handling = should_ai_handle_conversation(conversation)
        
        if not ai_handling:
            # If AI is not handling, safe to mark all as answered
            updated_count = Message.objects.filter(
                conversation_id=conversation_id,
                is_answered=False
            ).update(is_answered=True)
        else:
            # If AI is handling, only mark messages that have responses
            # Don't mark recent unanswered messages that AI should process
            
            # Mark messages that have AI or support responses after them
            messages_with_responses = Message.objects.filter(
                conversation_id=conversation_id,
                type='customer',
                is_answered=False
            ).annotate(
                has_response=models.Exists(
                    Message.objects.filter(
                        conversation_id=models.OuterRef('conversation_id'),
                        type__in=['AI', 'support'],
                        created_at__gt=models.OuterRef('created_at')
                    )
                )
            ).filter(has_response=True)
            
            updated_count = messages_with_responses.update(is_answered=True)
        
        # Send WebSocket notification
        notify_message_read(conversation_id, user_id)
        
        logger.info(f"Marked {updated_count} messages as read in conversation {conversation_id} (AI handling: {ai_handling})")
        
        return updated_count
        
    except Exception as e:
        logger.error(f"Error marking messages as read: {str(e)}")
        return 0


def get_conversation_summary(conversation):
    """
    Get a summary of conversation for WebSocket notifications
    """
    try:
        from .models import Message
        
        # Get latest message
        latest_message = Message.objects.filter(
            conversation=conversation
        ).order_by('-created_at').first()
        
        # Count unread messages
        unread_count = Message.objects.filter(
            conversation=conversation,
            type='customer',
            is_answered=False
        ).count()
        
        summary = {
            'conversation_id': conversation.id,
            'customer_name': str(conversation.customer),
            'latest_message': latest_message.content if latest_message else '',
            'latest_message_time': latest_message.created_at if latest_message else None,
            'unread_count': unread_count,
            'status': conversation.status,
            'source': conversation.source
        }
        
        return summary
        
    except Exception as e:
        logger.error(f"Error getting conversation summary: {str(e)}")
        return {
            'conversation_id': conversation.id,
            'error': str(e)
        }