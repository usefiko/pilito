import logging
import time
from celery import shared_task
from django.utils import timezone
from django.core.files.base import ContentFile
from datetime import timedelta
from settings.models import InstagramChannel
from typing import Dict, Any
import requests

logger = logging.getLogger(__name__)


# ============================================================================
# INTERCOM INTEGRATION TASKS
# ============================================================================

@shared_task(
    name='message.sync_conversation_to_intercom',
    bind=True,
    autoretry_for=(Exception,),
    retry_kwargs={'max_retries': 3, 'countdown': 60},
    retry_backoff=True
)
def sync_conversation_to_intercom_async(self, conversation_id: str):
    """
    Asynchronously sync a Fiko conversation to Intercom.
    
    Args:
        conversation_id: Fiko Conversation ID
        
    Returns:
        Dictionary with sync result
    """
    from message.models import Conversation
    from message.services.intercom_conversation_sync import IntercomConversationSyncService
    
    try:
        conversation = Conversation.objects.select_related('user', 'customer').get(id=conversation_id)
        
        logger.info(f"🔄 Starting Intercom sync for conversation {conversation_id}")
        
        # Get first message content for initial message
        first_message = conversation.messages.filter(type='customer').first()
        if not first_message:
            logger.warning(f"⚠️ No customer message found for conversation {conversation_id}")
            return {'success': False, 'error': 'No customer message found'}
        
        # Create conversation in Intercom
        result = IntercomConversationSyncService.create_conversation(
            user_id=conversation.user.id,
            message_text=first_message.content,
            subject=conversation.title
        )
        
        if result:
            # Save Intercom conversation ID
            conversation.intercom_conversation_id = result['id']
            conversation.save(update_fields=['intercom_conversation_id'])
            
            logger.info(
                f"✅ Successfully synced conversation {conversation_id} to Intercom. "
                f"Intercom ID: {result['id']}"
            )
            
            return {
                'success': True,
                'conversation_id': conversation_id,
                'intercom_id': result['id']
            }
        else:
            logger.error(f"❌ Failed to sync conversation {conversation_id} to Intercom")
            return {
                'success': False,
                'conversation_id': conversation_id,
                'error': 'Sync failed'
            }
            
    except Conversation.DoesNotExist:
        logger.error(f"❌ Conversation {conversation_id} not found")
        return {
            'success': False,
            'conversation_id': conversation_id,
            'error': 'Conversation not found'
        }
        
    except Exception as e:
        logger.error(f"❌ Error syncing conversation {conversation_id}: {str(e)}")
        raise


@shared_task(
    name='message.sync_message_to_intercom',
    bind=True,
    autoretry_for=(Exception,),
    retry_kwargs={'max_retries': 3, 'countdown': 60},
    retry_backoff=True
)
def sync_message_to_intercom_async(self, message_id: str):
    """
    Asynchronously sync a Fiko message to Intercom conversation.
    
    Args:
        message_id: Fiko Message ID
        
    Returns:
        Dictionary with sync result
    """
    from message.models import Message
    from message.services.intercom_conversation_sync import IntercomConversationSyncService
    
    try:
        message = Message.objects.select_related('conversation').get(id=message_id)
        
        logger.info(f"🔄 Starting Intercom sync for message {message_id}")
        
        # Get Intercom conversation ID
        intercom_conversation_id = message.conversation.intercom_conversation_id
        
        if not intercom_conversation_id:
            logger.warning(f"⚠️ Conversation {message.conversation.id} not synced to Intercom")
            return {
                'success': False,
                'error': 'Conversation not synced to Intercom'
            }
        
        # Add message to Intercom conversation
        result = IntercomConversationSyncService.add_message_to_conversation(
            conversation_id=intercom_conversation_id,
            message_text=message.content,
            message_type='comment'
        )
        
        if result:
            logger.info(f"✅ Successfully synced message {message_id} to Intercom")
            return {
                'success': True,
                'message_id': message_id
            }
        else:
            logger.error(f"❌ Failed to sync message {message_id} to Intercom")
            return {
                'success': False,
                'message_id': message_id,
                'error': 'Sync failed'
            }
            
    except Message.DoesNotExist:
        logger.error(f"❌ Message {message_id} not found")
        return {
            'success': False,
            'message_id': message_id,
            'error': 'Message not found'
        }
        
    except Exception as e:
        logger.error(f"❌ Error syncing message {message_id}: {str(e)}")
        raise


@shared_task(bind=True, retry_kwargs={'max_retries': 3, 'countdown': 60})
def auto_refresh_instagram_tokens(self, days_before_expiry=7):
    """
    Automatically refresh Instagram tokens that are close to expiration
    This task runs periodically to ensure tokens never expire
    """
    try:
        logger.info("🔄 Starting automatic Instagram token refresh")
        
        # Get all connected Instagram channels
        channels = InstagramChannel.objects.filter(is_connect=True)
        logger.info(f"🔍 Found {channels.count()} connected Instagram channels")

        if not channels:
            logger.info("⚠️ No connected Instagram channels found")
            return {"status": "success", "message": "No channels to refresh"}

        # Determine which tokens need refreshing
        channels_to_refresh = []
        now = timezone.now()
        threshold_date = now + timedelta(days=days_before_expiry)

        for channel in channels:
            should_refresh = False
            reason = ""

            if not channel.access_token:
                logger.warning(f"❌ {channel.username}: No access token")
                continue

            if hasattr(channel, 'token_expires_at') and channel.token_expires_at:
                if channel.token_expires_at <= threshold_date:
                    should_refresh = True
                    if channel.token_expires_at <= now:
                        # Token is already expired - urgent refresh needed
                        reason = f"⚠️ EXPIRED {abs((channel.token_expires_at - now).days)} days ago"
                        logger.warning(f"🚨 {channel.username}: Token EXPIRED on {channel.token_expires_at}")
                    else:
                        days_left = (channel.token_expires_at - now).days
                        hours_left = ((channel.token_expires_at - now).seconds // 3600)
                        reason = f"expires in {days_left} days, {hours_left} hours"
                else:
                    days_left = (channel.token_expires_at - now).days
                    logger.info(f"✅ {channel.username}: Token valid for {days_left} more days")
                    
                    # Additional safety check: if token expires within 2 days, also schedule for refresh
                    if days_left <= 2:
                        should_refresh = True
                        reason = f"⚠️ SAFETY CHECK: expires in {days_left} days (safety refresh)"
                        logger.warning(f"🛡️ {channel.username}: Safety refresh triggered - expires in {days_left} days")
            else:
                # No expiration data - check token validity and potentially refresh
                if _should_refresh_unknown_expiry_token(channel):
                    should_refresh = True
                    reason = "unknown expiry, token validation suggested refresh"
                else:
                    logger.info(f"✅ {channel.username}: Token appears valid (no expiry data)")

            if should_refresh:
                channels_to_refresh.append((channel, reason))
                logger.info(f"🔄 {channel.username}: Scheduled for refresh ({reason})")

        if not channels_to_refresh:
            logger.info("✅ All tokens are up to date!")
            return {"status": "success", "message": "All tokens are up to date"}

        # Perform actual refresh
        success_count = 0
        error_count = 0
        results = []

        for channel, reason in channels_to_refresh:
            logger.info(f"🔄 Refreshing: {channel.username} ({reason})")
            
            try:
                success = _refresh_channel_token(channel)
                if success:
                    success_count += 1
                    message = f"✅ Successfully refreshed token for {channel.username}"
                    logger.info(message)
                    results.append({"channel": channel.username, "status": "success", "reason": reason})
                else:
                    error_count += 1
                    message = f"❌ Failed to refresh token for {channel.username}"
                    logger.error(message)
                    
                    # Check if token is completely expired and can't be refreshed
                    if "expired" in reason.lower():
                        logger.critical(f"🚨 CRITICAL: {channel.username} token is expired and needs manual reconnection")
                        # Optionally disable the channel to prevent repeated errors
                        try:
                            channel.is_connect = False
                            channel.save()
                            logger.warning(f"⚠️ Disabled channel {channel.username} due to expired token")
                        except Exception as save_error:
                            logger.error(f"Failed to disable channel {channel.username}: {save_error}")
                    
                    results.append({"channel": channel.username, "status": "failed", "reason": reason, "needs_reconnection": "expired" in reason.lower()})
            except Exception as e:
                error_count += 1
                message = f"❌ Error refreshing {channel.username}: {str(e)}"
                logger.error(message)
                results.append({"channel": channel.username, "status": "error", "reason": str(e)})

        # Summary
        summary = {
            "status": "completed",
            "total_channels": len(channels_to_refresh),
            "successful": success_count,
            "failed": error_count,
            "results": results
        }
        
        logger.info(f"📊 Refresh Summary: {success_count} successful, {error_count} failed")
        
        if error_count > 0:
            logger.warning(f"⚠️ {error_count} tokens failed to refresh. Users may need to reconnect.")
        
        return summary

    except Exception as exc:
        logger.error(f"❌ Fatal error in auto_refresh_instagram_tokens: {exc}")
        # Retry the task
        raise self.retry(exc=exc)


@shared_task(bind=True, retry_kwargs={'max_retries': 2, 'countdown': 30})
def refresh_single_instagram_token(self, channel_id):
    """
    Refresh a specific Instagram channel token
    Used when a specific token fails during normal operations
    """
    try:
        logger.info(f"🔄 Refreshing token for channel ID: {channel_id}")
        
        channel = InstagramChannel.objects.get(id=channel_id, is_connect=True)
        
        if not channel.access_token:
            logger.error(f"❌ Channel {channel.username}: No access token")
            return {"status": "error", "message": "No access token"}
        
        success = _refresh_channel_token(channel)
        
        if success:
            logger.info(f"✅ Successfully refreshed token for {channel.username}")
            return {"status": "success", "channel": channel.username}
        else:
            logger.error(f"❌ Failed to refresh token for {channel.username}")
            return {"status": "failed", "channel": channel.username}
            
    except InstagramChannel.DoesNotExist:
        logger.error(f"❌ Channel with ID {channel_id} not found")
        return {"status": "error", "message": "Channel not found"}
    except Exception as exc:
        logger.error(f"❌ Error refreshing channel {channel_id}: {exc}")
        raise self.retry(exc=exc)


def _should_refresh_unknown_expiry_token(channel):
    """Check if a token with unknown expiry should be refreshed"""
    try:
        # Simple test - try to make an API call to see if token works
        url = f"https://graph.instagram.com/me"
        params = {
            'fields': 'id,username',
            'access_token': channel.access_token
        }
        
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            # Token works, but we might want to refresh it proactively
            # Check if channel was created/updated recently (might have short-lived token)
            if hasattr(channel, 'updated_at'):
                time_since_update = timezone.now() - channel.updated_at
                
                # If token was created/updated more than 30 days ago, refresh it
                if time_since_update.days > 30:
                    logger.warning(f"🔄 {channel.username}: Token is {time_since_update.days} days old, refreshing proactively")
                    return True
                if time_since_update.days < 1:  # Updated less than 24 hours ago
                    return True  # Might be a fresh short-lived token
            return False  # Token works and isn't fresh
        elif response.status_code == 400:
            error_data = response.json()
            error_code = error_data.get('error', {}).get('code')
            if error_code == 190:  # Token expired/invalid
                return True
        
        return False
        
    except Exception as e:
        logger.error(f"Error checking token validity for {channel.username}: {e}")
        return False


def _refresh_channel_token(channel):
    """Refresh token for a specific channel"""
    try:
        # Try Facebook Graph API first (for short-lived to long-lived conversion)
        new_token, expires_in = _exchange_for_long_lived_token(channel.access_token)
        
        if new_token:
            _update_channel_token(channel, new_token, expires_in)
            return True
        
        # If Facebook API failed, try Instagram API
        new_token, expires_in = _refresh_long_lived_instagram_token(channel.access_token)
        
        if new_token:
            _update_channel_token(channel, new_token, expires_in)
            return True
        
        return False
        
    except Exception as e:
        logger.error(f"Error refreshing token for {channel.username}: {e}")
        return False


def _exchange_for_long_lived_token(short_lived_token):
    """Exchange short-lived token for long-lived token using Instagram Graph API"""
    try:
        url = 'https://graph.instagram.com/access_token'
        params = {
            'grant_type': 'ig_exchange_token',
            'client_secret': '071f08aea723183951494234746982e4',
            'access_token': short_lived_token
        }
        
        response = requests.get(url, params=params, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            return data.get('access_token'), data.get('expires_in')
        else:
            return None, None
            
    except Exception:
        return None, None


def _refresh_long_lived_instagram_token(current_token):
    """Refresh Instagram long-lived token"""
    try:
        url = "https://graph.instagram.com/refresh_access_token"
        params = {
            'grant_type': 'ig_refresh_token',
            'access_token': current_token
        }
        
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            return data.get('access_token'), data.get('expires_in')
        else:
            return None, None
            
    except Exception:
        return None, None


def _update_channel_token(channel, new_token, expires_in):
    """Update channel with new token and expiry"""
    try:
        channel.access_token = new_token
        
        if expires_in:
            expiration_time = timezone.now() + timedelta(seconds=int(expires_in))
            channel.token_expires_at = expiration_time
            days = expires_in // (24 * 3600)
            hours = (expires_in % (24 * 3600)) // 3600
            logger.info(f"📅 {channel.username}: New token expires in {days} days, {hours} hours")
        
        channel.save()
        
    except Exception as e:
        logger.error(f"Error updating channel token: {e}")
        raise


# ============================================================================
# VOICE & MEDIA PROCESSING TASKS
# ============================================================================

@shared_task(bind=True, max_retries=3, default_retry_delay=10)
def process_telegram_voice(self, message_id: str, file_id: str, bot_token: str) -> Dict[str, Any]:
    """
    Process Telegram voice message (transcription)
    
    Args:
        message_id: Message ID to process
        file_id: Telegram file ID
        bot_token: Bot token for file download
    
    Returns:
        Dict with processing result
    """
    start_time = time.time()
    
    try:
        from message.models import Message
        from message.services.telegram_service import TelegramService
        from AI_model.services.media_processor import MediaProcessorService
        
        # Get message
        try:
            message = Message.objects.get(id=message_id)
        except Message.DoesNotExist:
            logger.error(f"❌ Message {message_id} not found")
            return {'success': False, 'error': 'Message not found'}
        
        # Update status
        message.processing_status = 'processing'
        message.save(update_fields=['processing_status'])
        
        logger.info(f"🔄 Processing Telegram voice: {message_id}")
        
        # Download file from Telegram
        telegram_service = TelegramService(bot_token)
        file_result = telegram_service.get_file_download_url(file_id)
        
        if not file_result.get('success'):
            raise Exception(f"Failed to get download URL: {file_result.get('error')}")
        
        download_url = file_result['download_url']
        response = requests.get(download_url, timeout=30)
        response.raise_for_status()
        
        # Save media file to S3
        filename = f"telegram_voice_{message_id}.ogg"
        message.media_file.save(filename, ContentFile(response.content), save=False)
        message.media_url = download_url  # Store for reference
        message.save(update_fields=['media_file', 'media_url'])
        
        # Process with AI - create temporary local file
        import tempfile
        import os
        
        # Get user from message conversation
        user = message.conversation.user if message.conversation else None
        processor = MediaProcessorService(user=user)
        
        if not processor.is_ready():
            raise Exception("MediaProcessorService not ready")
        
        # Save to temporary file for processing
        with tempfile.NamedTemporaryFile(suffix='.ogg', delete=False) as tmp_file:
            tmp_file.write(response.content)
            tmp_path = tmp_file.name
        
        try:
            result = processor.process_voice(tmp_path)
        finally:
            # Clean up temp file
            try:
                os.unlink(tmp_path)
            except:
                pass
        if result['success']:
            message.content = result['transcription']
            message.transcription = result['transcription']
        else:
            raise Exception(result['error'])
        
        # Update message as completed
        message.processing_status = 'completed'
        message.processed_at = timezone.now()
        message.processing_duration_ms = int((time.time() - start_time) * 1000)
        message.save()
        
        logger.info(f"✅ Telegram voice processed: {message_id} ({message.processing_duration_ms}ms)")
        logger.info(f"📝 Transcription: {message.content[:100]}...")
        
        # Notify WebSocket
        from message.websocket_utils import notify_new_customer_message
        notify_new_customer_message(message)
        
        # Trigger AI response now that content is ready
        from AI_model.tasks import process_ai_response_async
        from django.core.cache import cache
        
        # Set force flag to bypass guards
        cache.set(f"ai_force_{message_id}", True, timeout=30)
        
        logger.info(f"🤖 Triggering AI response for transcribed message {message_id}")
        process_ai_response_async.delay(message_id)
        
        return {
            'success': True,
            'message_id': message_id,
            'content': message.content[:100],
            'duration_ms': message.processing_duration_ms
        }
        
    except Exception as e:
        error_msg = str(e)
        logger.error(f"❌ Failed to process Telegram voice {message_id}: {error_msg}")
        
        # Update message as failed
        try:
            message = Message.objects.get(id=message_id)
            message.processing_status = 'failed'
            message.processing_error = error_msg
            message.content = f"[پردازش پیام صوتی ناموفق بود]"
            message.processing_duration_ms = int((time.time() - start_time) * 1000)
            message.save()
        except:
            pass
        
        # Retry if not last attempt
        if self.request.retries < self.max_retries:
            logger.info(f"🔄 Retrying voice processing (attempt {self.request.retries + 1}/{self.max_retries})")
            raise self.retry(exc=e)
        
        return {
            'success': False,
            'error': error_msg,
            'message_id': message_id
        }


@shared_task(bind=True, max_retries=3, default_retry_delay=10)
def process_telegram_image(self, message_id: str, file_id: str, bot_token: str, caption: str = None) -> Dict[str, Any]:
    """
    Process Telegram image message (analysis with AI)
    
    Args:
        message_id: Message ID to process
        file_id: Telegram file ID
        bot_token: Bot token for file download
        caption: Optional caption text with image
    
    Returns:
        Dict with processing result
    """
    start_time = time.time()
    
    try:
        from message.models import Message
        from message.services.telegram_service import TelegramService
        from AI_model.services.media_processor import MediaProcessorService
        
        # Get message
        try:
            message = Message.objects.get(id=message_id)
        except Message.DoesNotExist:
            logger.error(f"❌ Message {message_id} not found")
            return {'success': False, 'error': 'Message not found'}
        
        # Update status
        message.processing_status = 'processing'
        message.save(update_fields=['processing_status'])
        
        if caption:
            logger.info(f"🔄 Processing Telegram image with caption: {message_id}")
        else:
            logger.info(f"🔄 Processing Telegram image: {message_id}")
        
        # Download file from Telegram
        telegram_service = TelegramService(bot_token)
        file_result = telegram_service.get_file_download_url(file_id)
        
        if not file_result.get('success'):
            raise Exception(f"Failed to get download URL: {file_result.get('error')}")
        
        download_url = file_result['download_url']
        response = requests.get(download_url, timeout=30)
        response.raise_for_status()
        
        # Save media file to S3/storage
        filename = f"telegram_image_{message_id}.jpg"
        message.media_file.save(filename, ContentFile(response.content), save=False)
        message.media_url = download_url  # Store for reference
        message.save(update_fields=['media_file', 'media_url'])
        
        # Process with AI - create temporary local file
        import tempfile
        import os
        
        # Get user from message conversation
        user = message.conversation.user if message.conversation else None
        processor = MediaProcessorService(user=user)
        
        if not processor.is_ready():
            raise Exception("MediaProcessorService not ready")
        
        # Save to temporary file for processing
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp_file:
            tmp_file.write(response.content)
            tmp_path = tmp_file.name
        
        try:
            result = processor.process_image(tmp_path, analysis_type='comprehensive')
        finally:
            # Clean up temp file
            try:
                os.unlink(tmp_path)
            except:
                pass
                
        if result['success']:
            # Combine caption (if any) with image description
            if caption:
                message.content = f"{caption}\n\n[Image Analysis]: {result['description']}"
            else:
                message.content = result['description']
            message.transcription = result['description']
        else:
            raise Exception(result['error'])
        
        # Update message as completed
        message.processing_status = 'completed'
        message.processed_at = timezone.now()
        message.processing_duration_ms = int((time.time() - start_time) * 1000)
        message.save()
        
        logger.info(f"✅ Telegram image processed: {message_id} ({message.processing_duration_ms}ms)")
        logger.info(f"📝 Description: {message.content[:100]}...")
        
        # Notify WebSocket
        from message.websocket_utils import notify_new_customer_message
        notify_new_customer_message(message)
        
        # Trigger AI response now that content is ready
        from AI_model.tasks import process_ai_response_async
        from django.core.cache import cache
        
        # Set force flag to bypass guards
        cache.set(f"ai_force_{message_id}", True, timeout=30)
        
        logger.info(f"🤖 Triggering AI response for analyzed image {message_id}")
        process_ai_response_async.delay(message_id)
        
        return {
            'success': True,
            'message_id': message_id,
            'content': message.content[:100],
            'duration_ms': message.processing_duration_ms
        }
        
    except Exception as e:
        error_msg = str(e)
        logger.error(f"❌ Failed to process Telegram image {message_id}: {error_msg}")
        
        # Update message as failed
        try:
            message = Message.objects.get(id=message_id)
            message.processing_status = 'failed'
            message.processing_error = error_msg
            message.content = f"[پردازش تصویر ناموفق بود]"
            message.processing_duration_ms = int((time.time() - start_time) * 1000)
            message.save()
        except:
            pass
        
        # Retry if not last attempt
        if self.request.retries < self.max_retries:
            logger.info(f"🔄 Retrying image processing (attempt {self.request.retries + 1}/{self.max_retries})")
            raise self.retry(exc=e)
        
        return {
            'success': False,
            'error': error_msg,
            'message_id': message_id
        }
