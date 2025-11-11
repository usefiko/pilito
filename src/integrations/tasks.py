from celery import shared_task
import logging
import time

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=30)
def process_woocommerce_product(self, payload: dict, user_id: int, event_log_id: str):
    """
    Process WooCommerce product async
    
    Args:
        payload: Webhook data
        user_id: User ID
        event_log_id: WooCommerceEventLog ID
        
    Queue: default
    Priority: معمولی (background processing)
    """
    from integrations.services import WooCommerceProcessor
    from integrations.models import WooCommerceEventLog
    from accounts.models import User
    
    start_time = time.time()
    
    try:
        # Get user
        user = User.objects.get(id=user_id)
        
        # Process event
        processor = WooCommerceProcessor(user=user)
        result = processor.process_event(payload)
        
        # Update event log
        processing_time = int((time.time() - start_time) * 1000)
        WooCommerceEventLog.objects.filter(id=event_log_id).update(
            processed_successfully=True,
            processing_time_ms=processing_time
        )
        
        logger.info(
            f"✅ WooCommerce product processed: {result} "
            f"(user: {user.email}, time: {processing_time}ms)"
        )
        
        return result
        
    except Exception as e:
        logger.error(f"❌ Failed to process WooCommerce product: {e}", exc_info=True)
        
        # Update event log with error
        WooCommerceEventLog.objects.filter(id=event_log_id).update(
            processed_successfully=False,
            error_message=str(e)
        )
        
        # Retry with exponential backoff
        retry_count = self.request.retries
        countdown = 2 ** retry_count * 30  # 30s, 60s, 120s
        
        logger.warning(f"⏰ Retrying task (attempt {retry_count + 1}/{self.max_retries})")
        
        raise self.retry(exc=e, countdown=countdown)


@shared_task(bind=True, max_retries=3, default_retry_delay=30)
def process_wordpress_content(self, payload: dict, user_id: int, event_log_id: str):
    """
    Process WordPress Pages/Posts async
    
    Args:
        payload: Webhook data
        user_id: User ID
        event_log_id: WordPressContentEventLog ID
        
    Queue: default
    """
    from integrations.services import WordPressContentProcessor
    from integrations.models import WordPressContentEventLog
    from accounts.models import User
    
    start_time = time.time()
    
    try:
        # Get user
        user = User.objects.get(id=user_id)
        
        # Process event
        processor = WordPressContentProcessor(user=user)
        result = processor.process_event(payload)
        
        # Update event log
        processing_time = int((time.time() - start_time) * 1000)
        WordPressContentEventLog.objects.filter(id=event_log_id).update(
            processed_successfully=True,
            processing_time_ms=processing_time
        )
        
        logger.info(
            f"✅ WordPress content processed: {result} "
            f"(user: {user.email}, time: {processing_time}ms)"
        )
        
        return result
        
    except Exception as e:
        logger.error(f"❌ Failed to process WordPress content: {e}", exc_info=True)
        
        # Update event log with error
        WordPressContentEventLog.objects.filter(id=event_log_id).update(
            processed_successfully=False,
            error_message=str(e)
        )
        
        # Retry with exponential backoff
        retry_count = self.request.retries
        countdown = 2 ** retry_count * 30
        
        logger.warning(f"⏰ Retrying task (attempt {retry_count + 1}/{self.max_retries})")
        
        raise self.retry(exc=e, countdown=countdown)

