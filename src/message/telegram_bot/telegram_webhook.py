from django.http import JsonResponse
import json
import logging
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from message.models import Customer,Conversation,Message
from settings.models import TelegramChannel
from message.websocket_utils import notify_new_customer_message
from message.services.telegram_service import TelegramService
from message.tasks import process_telegram_voice

logger = logging.getLogger(__name__)


class TelegramWebhook(APIView):
    permission_classes = [AllowAny]
    def post(self, *args, **kwargs):
        try:
            data = json.loads(self.request.body.decode("utf-8"))
            user_info = data['message']['from']
            chat_id = data['message']['chat']['id']
            telegram_id = user_info['id']
            first_name = user_info.get('first_name', '')
            last_name = user_info.get('last_name', '')
            username = user_info.get('username', '')
            bot_name = self.kwargs["bot_name"]
            
            # ============== Detect message type ==============
            message_text = data['message'].get('text')
            caption = data['message'].get('caption')  # Caption for photos/videos
            voice = data['message'].get('voice')
            photo = data['message'].get('photo')  # Array of PhotoSize objects
            
            message_type = 'text'
            file_id = None
            placeholder_text = None
            
            if voice:
                message_type = 'voice'
                file_id = voice.get('file_id')
                duration = voice.get('duration', 0)
                placeholder_text = "[Voice Message]"  # Simple placeholder, no notification to user
                logger.info(f"🎤 Voice message received from {telegram_id} (@{username}), duration: {duration}s")
                
            elif photo:
                message_type = 'image'
                # Get largest photo (last in array)
                largest_photo = photo[-1]
                file_id = largest_photo.get('file_id')
                # Use caption if available, otherwise generic placeholder
                if caption:
                    placeholder_text = f"[Image: {caption}]"
                    logger.info(f"📸 Image with caption received from {telegram_id} (@{username}): {caption}")
                else:
                    placeholder_text = "[Image]"
                    logger.info(f"📸 Image message received from {telegram_id} (@{username})")
                
            elif not message_text:
                # Unsupported message type (video, sticker, etc.)
                logger.info(f"⚠️ Unsupported message type from {telegram_id}, ignoring")
                return JsonResponse({
                    'status': 'ignored',
                    'reason': 'Unsupported message type'
                }, status=200)
            
            # Log text messages
            if message_type == 'text':
                logger.info(f"📨 Telegram text message from {telegram_id} (@{username}) to bot {bot_name}: {message_text}")

            channel = TelegramChannel.objects.get(bot_username=bot_name)
            bot_user = channel.user

            # Create Telegram service instance for profile picture fetching
            telegram_service = TelegramService(channel.bot_token)

            # Prepare potential profile image
            customer_profile_image = None

            # Try to fetch and save profile picture
            logger.info(f"🔍 Attempting to fetch profile picture for Telegram user {telegram_id}")
            try:
                profile_image = telegram_service.download_profile_picture(str(telegram_id))
                if profile_image:
                    customer_profile_image = profile_image
                    logger.info(f"✅ Profile picture downloaded for user {telegram_id}")
                else:
                    logger.info(f"📷 No profile picture available for user {telegram_id}")
            except Exception as e:
                logger.error(f"❌ Error downloading Telegram profile picture for {telegram_id}: {e}")

            # Create or update Customer but PRESERVE manual edits
            customer, created = Customer.objects.get_or_create(
                source='telegram',
                source_id=str(telegram_id),
            )

            # On create, set fetched fields
            if created:
                customer.first_name = first_name
                customer.last_name = last_name
                customer.username = username
                if customer_profile_image:
                    customer.profile_picture = customer_profile_image
                customer.save()
                action = "created"
            else:
                # Only fill empty fields; do not overwrite non-empty (manual) values
                updated = False
                if not customer.first_name and first_name:
                    customer.first_name = first_name
                    updated = True
                if not customer.last_name and last_name:
                    customer.last_name = last_name
                    updated = True
                if not customer.username and username:
                    customer.username = username
                    updated = True
                # Update profile picture only if missing or default placeholder
                try:
                    has_default_avatar = not customer.profile_picture or str(customer.profile_picture) == "customer_img/default.png"
                except Exception:
                    has_default_avatar = True
                if customer_profile_image and has_default_avatar:
                    customer.profile_picture = customer_profile_image
                    updated = True
                if updated:
                    customer.save()
                action = "updated"

            logger.info(f"Customer {action}: {customer} (manual edits preserved)")

            # Assign Telegram tag when customer is created
            if created:
                from message.models import Tag
                telegram_tag, tag_created = Tag.objects.get_or_create(name="Telegram")
                customer.tag.add(telegram_tag)
                tag_action = "created" if tag_created else "found"
                logger.info(f"Telegram tag {tag_action} and assigned to customer {customer.id}")

            # Get or create Conversation - only set status on creation
            try:
                # Try to get existing conversation first
                conversation = Conversation.objects.get(
                    user=bot_user,
                    source='telegram', 
                    customer=customer
                )
                conv_created = False
                logger.info(f"Found existing conversation: {conversation} with status: {conversation.status}")
                
            except Conversation.DoesNotExist:
                # Create new conversation with initial status
                from AI_model.utils import get_initial_conversation_status
                
                # Determine initial status based on user's default_reply_handler (only for new conversations)
                initial_status = get_initial_conversation_status(bot_user)
                
                conversation = Conversation.objects.create(
                    user=bot_user,
                    source='telegram', 
                    customer=customer,
                    status=initial_status
                )
                conv_created = True
                
                # Log the initial status for new conversation
                from AI_model.utils import log_conversation_status_change
                log_conversation_status_change(conversation, 'new', initial_status, f"Initial status based on user's default_reply_handler: {bot_user.default_reply_handler}")
                logger.info(f"Created new conversation: {conversation} with initial status: {initial_status}")
            
            # Always update conversation's updated_at field
            conversation.save(update_fields=['updated_at'])

            # ============== Create Message based on type ==============
            if message_type == 'text':
                # Original behavior - unchanged
                message = Message.objects.create(
                    content=message_text,
                    conversation=conversation,
                    customer=customer,
                    type='customer',
                    message_type='text',
                    processing_status='completed'
                )
                logger.info(f"✅ Text message created: {message.id}")
                
            else:
                # Voice or Image message
                message = Message.objects.create(
                    content=placeholder_text,
                    conversation=conversation,
                    customer=customer,
                    type='customer',
                    message_type=message_type,
                    metadata={
                        'telegram_file_id': file_id,
                        'bot_token_hint': bot_name  # Don't store token in DB
                    },
                    processing_status='pending'
                )
                logger.info(f"✅ {message_type.capitalize()} message created (pending): {message.id}")
                
                # Queue async processing based on type
                if message_type == 'voice':
                    logger.info(f"📤 Queueing voice processing task for message {message.id}")
                    process_telegram_voice.delay(
                        str(message.id),
                        file_id,
                        channel.bot_token
                    )
                elif message_type == 'image':
                    from message.tasks import process_telegram_image
                    logger.info(f"📤 Queueing image processing task for message {message.id}")
                    process_telegram_image.delay(
                        str(message.id),
                        file_id,
                        channel.bot_token,
                        caption  # Pass caption if available
                    )

            # Notify WebSocket only for text messages (voice/image will notify after processing)
            if message_type == 'text':
                notify_new_customer_message(message)

            # You can now process or store this message, or send it over WebSocket
            # Optional: respond back
            # send_telegram_message(chat_id, "Received your message!")

            # Return detailed response with all relevant information
            response_data = {
                "status": "success",
                "message": "Message received and processed successfully",
                "data": {
                    "bot": {
                        "username": bot_name,
                        "owner": {
                            "id": bot_user.id,
                            "username": getattr(bot_user, 'username', None),
                            "email": getattr(bot_user, 'email', None)
                        }
                    },
                    "customer": {
                        "id": customer.id,
                        "telegram_id": telegram_id,
                        "first_name": customer.first_name,
                        "last_name": customer.last_name,
                        "username": customer.username,
                        "full_name": f"{customer.first_name or ''} {customer.last_name or ''}".strip(),
                        "source": "telegram",
                        "has_profile_picture": bool(customer.profile_picture and customer.profile_picture != "customer_img/default.png"),
                        "profile_picture_url": customer.profile_picture.url if customer.profile_picture else None,
                        "was_created": created
                    },
                    "conversation": {
                        "id": conversation.id,
                        "source": "telegram",
                        "was_created": conv_created
                    },
                    "message": {
                        "id": message.id,
                        "content": message.content,
                        "message_type": message_type,
                        "processing_status": message.processing_status,
                        "chat_id": chat_id,
                        "timestamp": message.created_at.isoformat() if hasattr(message, 'created_at') else None
                    }
                }
            }
            
            return JsonResponse(response_data)

        except TelegramChannel.DoesNotExist:
            logger.error(f"❌ Telegram channel not found for bot: {bot_name}")
            return JsonResponse({
                "status": "error",
                "message": f"Bot channel '{bot_name}' not found",
                "error_code": "CHANNEL_NOT_FOUND"
            }, status=404)
        except KeyError as e:
            logger.error(f"❌ Missing required field in Telegram data: {str(e)}")
            return JsonResponse({
                "status": "error",
                "message": f"Missing required field: {str(e)}",
                "error_code": "INVALID_TELEGRAM_DATA"
            }, status=400)
        except Exception as e:
            logger.error(f"❌ Error processing Telegram webhook: {e}", exc_info=True)
            return JsonResponse({
                "status": "error",
                "message": f"An unexpected error occurred: {str(e)}",
                "error_code": "INTERNAL_ERROR"
            }, status=500)
