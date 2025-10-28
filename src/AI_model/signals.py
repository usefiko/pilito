"""
Django signals for AI model integration
Handles automatic AI responses to customer messages
"""
import logging
from django.db.models.signals import post_save, post_delete, pre_delete
from django.dispatch import receiver
from django.utils import timezone

logger = logging.getLogger(__name__)


def connect_ai_signals():
    """
    Connect AI signals for automatic message processing
    """
    # Signal is connected via decorator - no manual connection needed
    logger.info("Connected AI model signals for automatic message processing")


@receiver(post_save, sender='message.Message')
def handle_new_customer_message(sender, instance, created, **kwargs):
    """
    Handle new customer messages and trigger AI response if needed
    
    This signal is triggered when a new Message is created.
    This is the SINGLE point of AI response triggering to prevent duplicates.
    """
    # Only process newly created customer messages
    if not created or instance.type != 'customer':
        logger.debug(f"Skipping message {instance.id} - not a new customer message")
        return
    
    # Don't process if already answered or is AI response
    if instance.is_answered or getattr(instance, 'is_ai_response', False):
        logger.debug(f"Skipping message {instance.id} - already answered or is AI response")
        return
    
    # Skip voice/image messages that are still processing
    # They will trigger AI after transcription/analysis completes
    if hasattr(instance, 'message_type') and instance.message_type in ['voice', 'image']:
        if hasattr(instance, 'processing_status') and instance.processing_status != 'completed':
            logger.info(f"Skipping message {instance.id} - {instance.message_type} message still processing (status: {instance.processing_status})")
            return
    
    # Check if conversation should be handled by AI
    if instance.conversation.status != 'active':
        logger.info(f"Skipping AI processing for conversation {instance.conversation.id} - status is '{instance.conversation.status}', not 'active'")
        return
    
    try:
        # Import here to avoid circular imports
        from AI_model.services.message_integration import MessageSystemIntegration
        from AI_model.tasks import process_ai_response_async
        from AI_model.models import AIGlobalConfig
        from workflow.services.trigger_service import TriggerService
        from workflow.models import TriggerEventLog
        
        # Check if global AI is enabled
        global_config = AIGlobalConfig.get_config()
        if not global_config.auto_response_enabled:
            logger.info(f"Global AI is disabled - skipping message {instance.id}")
            return
        
        # Check workflow AI control settings for this conversation
        from django.core.cache import cache
        conversation_id = str(instance.conversation.id)
        ai_control_key = f"ai_control_{conversation_id}"
        ai_control = cache.get(ai_control_key, {})
        
        # If AI is specifically disabled for this conversation, allow override when waiting has just ended
        if ai_control.get('ai_enabled') is False:
            try:
                waiting_ended_key = f"waiting_ended_{conversation_id}"
                if cache.get(waiting_ended_key):
                    # Auto-clear disable after waiting ended
                    cache.set(ai_control_key, {'ai_enabled': True}, timeout=86400)
                    logger.info(f"AI re-enabled for conversation {conversation_id} due to recent waiting end")
                else:
                    logger.info(f"AI disabled by workflow for conversation {conversation_id} - skipping message {instance.id}")
                    return
            except Exception:
                logger.info(f"AI disabled by workflow for conversation {conversation_id} - skipping message {instance.id}")
                return

        # Additional guard: if the latest workflow execution for this conversation is WAITING, skip AI
        # This avoids stale/old WAITING executions from blocking AI indefinitely.
        try:
            from workflow.models import WorkflowExecution
            latest_exec = WorkflowExecution.objects.filter(
                conversation=conversation_id
            ).order_by('-created_at').first()
            if latest_exec and latest_exec.status == 'WAITING' and (latest_exec.context_data or {}).get('waiting_node_id'):
                logger.info(f"AI skipped for message {instance.id} - latest execution for conversation {conversation_id} is WAITING")
                return
        except Exception as wait_err:
            logger.warning(f"Failed to check latest waiting state for conversation {conversation_id}: {wait_err}")
        
        # Small debounce to allow workflow gating to engage in racey environments
        try:
            import time
            time.sleep(2)
        except Exception:
            pass

        # Check if there are active workflows that might handle this message
        # If yes, don't trigger AI immediately - let workflow decide
        try:
            from workflow.models import Workflow
            business_owner_id = str(instance.conversation.user.id)
            if Workflow.objects.filter(created_by_id=business_owner_id, status='ACTIVE').exists():
                logger.info(f"Active workflows found for business owner {business_owner_id} - AI will be triggered by workflow if needed")
                return
        except Exception as wf_check_err:
            logger.debug(f"Could not check for active workflows: {wf_check_err}")
        
        # Additional check to prevent duplicate processing
        # Check if there's already a pending AI task for this message
        from django.core.cache import cache
        cache_key = f"ai_processing_{instance.id}"
        if cache.get(cache_key):
            logger.warning(f"AI processing already in progress for message {instance.id} - skipping duplicate")
            return
        
        # Mark as being processed (expires in 5 minutes)
        cache.set(cache_key, True, timeout=300)
        
        # Check if we should add a delay
        delay_seconds = global_config.response_delay_seconds
        
        # Process AI response asynchronously
        if delay_seconds > 0:
            # Schedule with delay
            process_ai_response_async.apply_async(
                args=[instance.id],
                countdown=delay_seconds
            )
            logger.info(f"✅ Scheduled AI response for message {instance.id} with {delay_seconds}s delay")
        else:
            # Process immediately
            process_ai_response_async.delay(instance.id)
            logger.info(f"✅ Triggered immediate AI response for message {instance.id}")
            
    except Exception as e:
        logger.error(f"Error in AI signal handler for message {instance.id}: {str(e)}")
        # Clear cache on error
        from django.core.cache import cache
        cache_key = f"ai_processing_{instance.id}"
        cache.delete(cache_key)


def handle_conversation_status_change(sender, instance, **kwargs):
    """
    Handle conversation status changes
    This can be used to trigger AI activation/deactivation
    """
    try:
        if hasattr(instance, 'status'):
            logger.info(f"Conversation {instance.id} status changed to '{instance.status}'")
            
            # If switching to AI mode, could trigger welcome message
            if instance.status == 'active':
                # Could add logic here to send AI welcome message
                pass
                
    except Exception as e:
        logger.error(f"Error handling conversation status change: {str(e)}")


def cleanup_old_usage_data():
    """
    Cleanup old AI usage tracking data (older than 1 year)
    Can be called periodically
    """
    try:
        from AI_model.models import AIUsageTracking
        from datetime import date, timedelta
        
        # Delete usage data older than 1 year
        cutoff_date = date.today() - timedelta(days=365)
        deleted_count = AIUsageTracking.objects.filter(date__lt=cutoff_date).delete()[0]
        
        if deleted_count > 0:
            logger.info(f"Cleaned up {deleted_count} old AI usage tracking records")
            
    except Exception as e:
        logger.error(f"Error cleaning up old usage data: {str(e)}")


def ensure_global_ai_config():
    """
    Ensure global AI configuration exists
    """
    try:
        from AI_model.models import AIGlobalConfig
        config = AIGlobalConfig.get_config()
        logger.info(f"Global AI config ensured: {config.model_name}")
    except Exception as e:
        logger.error(f"Error ensuring global AI config: {str(e)}")

# ============================================================
# AUTO-CHUNKING SIGNALS (Real-time Knowledge Updates)
# ============================================================

@receiver(post_save, sender='web_knowledge.QAPair')
def on_qapair_saved_for_chunking(sender, instance, created, **kwargs):
    """Auto-chunk QAPair when created/updated (if completed)"""
    if instance.generation_status != 'completed':
        return
    
    from AI_model.tasks import chunk_qapair_async
    chunk_qapair_async.apply_async(args=[str(instance.id)], countdown=5)
    logger.debug(f"Queued chunking for QAPair {instance.id}")


@receiver(pre_delete, sender='web_knowledge.QAPair')
def on_qapair_deleted_cleanup_chunks(sender, instance, **kwargs):
    """Delete chunks BEFORE QAPair is deleted (pre_delete ensures relationships still exist)"""
    try:
        from AI_model.models import TenantKnowledge
        
        # Use pre_delete so instance.page and instance.user are still accessible
        # Delete chunks synchronously (not async) to ensure they're deleted before QAPair
        deleted = TenantKnowledge.objects.filter(
            source_id=instance.id,
            chunk_type='faq'
        ).delete()
        
        if deleted[0] > 0:
            logger.info(f"✅ Deleted {deleted[0]} chunks for QAPair {instance.id}")
        else:
            logger.debug(f"No chunks to delete for QAPair {instance.id}")
            
    except Exception as e:
        logger.error(f"❌ Failed to delete chunks for QAPair {instance.id}: {e}")


@receiver(post_save, sender='web_knowledge.Product')
def on_product_saved_for_chunking(sender, instance, created, **kwargs):
    """Auto-chunk Product when created/updated"""
    from AI_model.tasks import chunk_product_async
    chunk_product_async.apply_async(args=[str(instance.id)], countdown=5)
    logger.debug(f"Queued chunking for Product {instance.id}")


@receiver(pre_delete, sender='web_knowledge.Product')
def on_product_deleted_cleanup_chunks(sender, instance, **kwargs):
    """Delete chunks BEFORE Product is deleted"""
    try:
        from AI_model.models import TenantKnowledge
        
        deleted = TenantKnowledge.objects.filter(
            source_id=instance.id,
            chunk_type='product'
        ).delete()
        
        if deleted[0] > 0:
            logger.info(f"✅ Deleted {deleted[0]} chunks for Product {instance.id}")
        else:
            logger.debug(f"No chunks to delete for Product {instance.id}")
            
    except Exception as e:
        logger.error(f"❌ Failed to delete chunks for Product {instance.id}: {e}")


@receiver(post_save, sender='web_knowledge.WebsitePage')
def on_webpage_saved_for_chunking(sender, instance, **kwargs):
    """
    Auto-chunk WebPage when processing completes
    Only queues chunking if page is completed AND not already chunked
    """
    if instance.processing_status != 'completed':
        return
    
    # Check if already chunked to avoid duplicate work (idempotent)
    from AI_model.models import TenantKnowledge
    already_chunked = TenantKnowledge.objects.filter(
        source_id=instance.id,
        chunk_type='website'
    ).exists()
    
    if already_chunked:
        logger.debug(f"WebPage {instance.id} already chunked, skipping")
        return
    
    from AI_model.tasks import chunk_webpage_async
    chunk_webpage_async.apply_async(args=[str(instance.id)], countdown=10)
    logger.debug(f"Queued chunking for WebPage {instance.id}")


@receiver(pre_delete, sender='web_knowledge.WebsitePage')
def on_webpage_deleted_cleanup_chunks(sender, instance, **kwargs):
    """Delete chunks BEFORE WebPage is deleted"""
    try:
        from AI_model.models import TenantKnowledge
        
        deleted = TenantKnowledge.objects.filter(
            source_id=instance.id,
            chunk_type='website'
        ).delete()
        
        if deleted[0] > 0:
            logger.info(f"✅ Deleted {deleted[0]} chunks for WebPage {instance.id}")
        else:
            logger.debug(f"No chunks to delete for WebPage {instance.id}")
            
    except Exception as e:
        logger.error(f"❌ Failed to delete chunks for WebPage {instance.id}: {e}")


@receiver(post_save, sender='settings.AIPrompts')
def on_aiprompts_saved_for_chunking(sender, instance, **kwargs):
    """Auto-chunk Manual Prompt when edited or delete chunks when cleared"""
    from AI_model.tasks import chunk_manual_prompt_async
    from AI_model.models import TenantKnowledge
    
    if instance.manual_prompt and instance.manual_prompt.strip():
        # Has content: chunk it (reduced debounce from 30s to 5s)
        chunk_manual_prompt_async.apply_async(args=[instance.user.id], countdown=5)
        logger.debug(f"Queued Manual Prompt chunking for user {instance.user.username}")
    else:
        # Empty: delete existing chunks
        deleted = TenantKnowledge.objects.filter(
            user=instance.user,
            chunk_type='manual'
        ).delete()
        if deleted[0] > 0:
            logger.info(f"✅ Deleted {deleted[0]} Manual Prompt chunks (prompt cleared)")
