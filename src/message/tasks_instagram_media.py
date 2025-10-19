"""
Instagram Media Processing Tasks (Image & Voice)
"""
import time
import logging
import requests
from typing import Dict, Any
from celery import shared_task
from django.utils import timezone
from django.core.files.base import ContentFile

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=10)
def process_instagram_image(self, message_id: str, media_url: str, access_token: str) -> Dict[str, Any]:
    """
    Process Instagram image message (analysis with AI)
    
    Args:
        message_id: Message ID to process
        media_url: Instagram media URL
        access_token: Instagram access token (if needed for private media)
    
    Returns:
        Dict with processing result
    """
    start_time = time.time()
    
    try:
        from message.models import Message
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
        
        logger.info(f"🔄 Processing Instagram image: {message_id}")
        
        # Download image from Instagram URL
        response = requests.get(media_url, timeout=30)
        response.raise_for_status()
        
        # Save media file
        filename = f"instagram_image_{message_id}.jpg"
        message.media_file.save(filename, ContentFile(response.content), save=True)
        
        # Process with AI
        import tempfile
        import os
        
        processor = MediaProcessorService()
        
        if not processor.is_ready():
            raise Exception("MediaProcessorService not ready")
        
        # Save to temporary file for processing
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp_file:
            tmp_file.write(response.content)
            tmp_path = tmp_file.name
        
        try:
            result = processor.process_image(tmp_path, analysis_type='comprehensive')
        finally:
            try:
                os.unlink(tmp_path)
            except:
                pass
                
        if result['success']:
            message.content = result['description']
            message.transcription = result['description']
        else:
            raise Exception(result['error'])
        
        # Update message as completed
        message.processing_status = 'completed'
        message.processed_at = timezone.now()
        message.processing_duration_ms = int((time.time() - start_time) * 1000)
        message.save()
        
        logger.info(f"✅ Instagram image processed: {message_id} ({message.processing_duration_ms}ms)")
        logger.info(f"📝 Description: {message.content[:100]}...")
        
        # Notify WebSocket
        from message.websocket_utils import notify_new_customer_message
        notify_new_customer_message(message)
        
        # Trigger AI response
        from AI_model.tasks import process_ai_response_async
        from django.core.cache import cache
        
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
        logger.error(f"❌ Failed to process Instagram image {message_id}: {error_msg}")
        
        try:
            message = Message.objects.get(id=message_id)
            message.processing_status = 'failed'
            message.processing_error = error_msg
            message.content = f"[پردازش تصویر ناموفق بود]"
            message.processing_duration_ms = int((time.time() - start_time) * 1000)
            message.save()
        except:
            pass
        
        if self.request.retries < self.max_retries:
            logger.info(f"🔄 Retrying Instagram image (attempt {self.request.retries + 1}/{self.max_retries})")
            raise self.retry(exc=e)
        
        return {
            'success': False,
            'error': error_msg,
            'message_id': message_id
        }


@shared_task(bind=True, max_retries=3, default_retry_delay=10)
def process_instagram_voice(self, message_id: str, media_url: str, access_token: str) -> Dict[str, Any]:
    """
    Process Instagram voice message (transcription)
    
    Args:
        message_id: Message ID to process
        media_url: Instagram media URL
        access_token: Instagram access token
    
    Returns:
        Dict with processing result
    """
    start_time = time.time()
    
    try:
        from message.models import Message
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
        
        logger.info(f"🔄 Processing Instagram voice: {message_id}")
        
        # Download voice from Instagram URL
        response = requests.get(media_url, timeout=30)
        response.raise_for_status()
        
        # Save media file
        filename = f"instagram_voice_{message_id}.m4a"
        message.media_file.save(filename, ContentFile(response.content), save=True)
        
        # Process with AI
        import tempfile
        import os
        
        processor = MediaProcessorService()
        
        if not processor.is_ready():
            raise Exception("MediaProcessorService not ready")
        
        # Save to temporary file
        with tempfile.NamedTemporaryFile(suffix='.m4a', delete=False) as tmp_file:
            tmp_file.write(response.content)
            tmp_path = tmp_file.name
        
        try:
            result = processor.process_voice(tmp_path)
        finally:
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
        
        logger.info(f"✅ Instagram voice processed: {message_id} ({message.processing_duration_ms}ms)")
        logger.info(f"📝 Transcription: {message.content[:100]}...")
        
        # Notify WebSocket
        from message.websocket_utils import notify_new_customer_message
        notify_new_customer_message(message)
        
        # Trigger AI response
        from AI_model.tasks import process_ai_response_async
        from django.core.cache import cache
        
        cache.set(f"ai_force_{message_id}", True, timeout=30)
        logger.info(f"🤖 Triggering AI response for transcribed voice {message_id}")
        process_ai_response_async.delay(message_id)
        
        return {
            'success': True,
            'message_id': message_id,
            'content': message.content[:100],
            'duration_ms': message.processing_duration_ms
        }
        
    except Exception as e:
        error_msg = str(e)
        logger.error(f"❌ Failed to process Instagram voice {message_id}: {error_msg}")
        
        try:
            message = Message.objects.get(id=message_id)
            message.processing_status = 'failed'
            message.processing_error = error_msg
            message.content = f"[پردازش پیام صوتی ناموفق بود]"
            message.processing_duration_ms = int((time.time() - start_time) * 1000)
            message.save()
        except:
            pass
        
        if self.request.retries < self.max_retries:
            logger.info(f"🔄 Retrying Instagram voice (attempt {self.request.retries + 1}/{self.max_retries})")
            raise self.retry(exc=e)
        
        return {
            'success': False,
            'error': error_msg,
            'message_id': message_id
        }

