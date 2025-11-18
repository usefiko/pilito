"""
Celery tasks for AI model operations
"""
import logging
from typing import Dict, Any, List, Optional
from celery import shared_task
from django.utils import timezone
from datetime import date, timedelta

logger = logging.getLogger(__name__)

@shared_task(bind=True, max_retries=3, queue='high_priority')
def process_ai_response_async(self, message_id):
    """
    Process AI response for a customer message asynchronously
    
    Args:
        message_id: ID of the Message instance to process
    """
    try:
        from message.models import Message
        from AI_model.services.message_integration import MessageSystemIntegration
        from django.core.cache import cache
        
        # Get the message
        try:
            message = Message.objects.get(id=message_id)
        except Message.DoesNotExist:
            logger.error(f"Message {message_id} not found")
            return {'success': False, 'error': 'Message not found'}
        
        # Double-check to prevent duplicate processing
        if message.is_answered:
            logger.warning(f"Message {message_id} already answered - skipping duplicate AI processing")
            # Clear cache since processing is complete
            cache_key = f"ai_processing_{message_id}"
            cache.delete(cache_key)
            return {'success': False, 'error': 'Message already answered'}
        
        # Check if this is already an AI response
        if getattr(message, 'is_ai_response', False):
            logger.warning(f"Message {message_id} is an AI response - skipping")
            cache_key = f"ai_processing_{message_id}"
            cache.delete(cache_key)
            return {'success': False, 'error': 'Cannot process AI response message'}

        # Force-allow AI if explicitly requested (e.g., after WaitingNode exit/timeout/success)
        forced_ai = False
        try:
            ai_force_key = f"ai_force_{message_id}"
            if cache.get(ai_force_key):
                forced_ai = True
                logger.info(f"AI processing FORCED for message {message_id} due to WaitingNode end/exit")
                # Consume the flag so it doesn't affect future messages
                cache.delete(ai_force_key)
        except Exception:
            forced_ai = False

        # Additional guard: if a system reply already exists right after this message, skip (unless forced)
        try:
            from workflow.settings_adapters import get_model_class, get_field_name, get_sender_type_values
            MessageModel = get_model_class('MESSAGE')
            sender_field = get_field_name('MESSAGE', 'SENDER_TYPE_FIELD')
            sender_types = get_sender_type_values()
            from datetime import timedelta
            conversation_fk = get_field_name('MESSAGE', 'CONVERSATION_FIELD') + '_id'
            convo_id = getattr(message, get_field_name('MESSAGE', 'CONVERSATION_FIELD')).id
            # Only consider replies within a short window and by system senders
            system_senders = [
                sender_types.get('MARKETING', 'marketing'),
                sender_types.get('SUPPORT', 'support'),
                sender_types.get('AI', 'AI')
            ]
            window_end = message.created_at + timedelta(seconds=20)
            reply_qs = MessageModel.objects.filter(
                **{conversation_fk: convo_id}
            ).filter(
                created_at__gt=message.created_at,
                created_at__lte=window_end
            )
            # Restrict to known system senders OR metadata auto_generated
            try:
                reply_qs = reply_qs.filter(**{f"{sender_field}__in": system_senders}) | reply_qs.filter(metadata__auto_generated=True)
            except Exception:
                reply_qs = reply_qs.filter(**{f"{sender_field}__in": system_senders})
            reply_exists = reply_qs.exists()
            if reply_exists and not forced_ai:
                logger.info(f"Detected existing reply after message {message_id}; skipping AI to avoid duplicate")
                cache_key = f"ai_processing_{message_id}"
                cache.delete(cache_key)
                return {'success': False, 'error': 'Reply already exists; AI skipped'}
        except Exception as guard_err:
            logger.warning(f"Post-reply duplicate guard failed for message {message_id}: {guard_err}")
        
        # Hard guard against active WaitingNode: consider only the latest execution for the conversation
        # This prevents stale WAITING executions from blocking AI after user exits/skips.
        try:
            from workflow.models import WorkflowExecution
            conversation_id = str(message.conversation.id)
            latest_exec = WorkflowExecution.objects.filter(
                conversation=conversation_id
            ).order_by('-created_at').first()
            is_waiting = latest_exec and latest_exec.status == 'WAITING' and (latest_exec.context_data or {}).get('waiting_node_id')
            # Allow override when we explicitly forced AI (e.g., after WaitingNode skip)
            if is_waiting and not forced_ai:
                logger.info(f"AI task skipped for message {message_id} - latest execution for conversation {conversation_id} is WAITING")
                cache_key = f"ai_processing_{message_id}"
                cache.delete(cache_key)
                return {'success': False, 'error': 'WaitingNode active; AI skipped'}
        except Exception as waiting_err:
            logger.warning(f"Failed WaitingNode guard in AI task for message {message_id}: {waiting_err}")

        # Respect explicit AI control cache flag if present (unless forced)
        try:
            ai_control_key = f"ai_control_{str(message.conversation.id)}"
            ai_control = cache.get(ai_control_key, {})
            if ai_control.get('ai_enabled') is False and not forced_ai:
                logger.info(f"AI task skipped for message {message_id} - ai_control disabled for conversation {message.conversation.id}")
                cache_key = f"ai_processing_{message_id}"
                cache.delete(cache_key)
                return {'success': False, 'error': 'AI disabled by workflow'}
        except Exception as cache_err:
            logger.debug(f"AI control cache check failed for message {message_id}: {cache_err}")

        # Send typing indicator for Instagram before processing
        if message.conversation.source == 'instagram':
            try:
                import time
                from message.services.instagram_service import InstagramService
                
                instagram_service = InstagramService.get_service_for_conversation(message.conversation)
                if instagram_service:
                    typing_result = instagram_service.send_typing_indicator_to_customer(
                        message.conversation.customer,
                        'typing_on'
                    )
                    if typing_result.get('success'):
                        # Store the typing start time in cache for dynamic timing
                        typing_start_key = f"typing_start_{message.conversation.id}"
                        cache.set(typing_start_key, time.time(), timeout=60)
                        logger.info(f"✍️ Typing indicator ON for Instagram conversation {message.conversation.id}")
                    else:
                        logger.debug(f"Could not send typing_on: {typing_result.get('error')}")
            except Exception as typing_err:
                logger.debug(f"Error sending typing_on indicator: {typing_err}")

        # Initialize integration service
        integration = MessageSystemIntegration(message.conversation.user)
        
        # Process the message
        result = integration.process_new_customer_message(message)
        
        if result['processed']:
            logger.info(f"Successfully processed message {message_id} with AI response")
            # Clear cache since processing is complete
            cache_key = f"ai_processing_{message_id}"
            cache.delete(cache_key)
            return {
                'success': True,
                'message_id': message_id,
                'ai_message_id': result.get('ai_message_id'),
                'response_time_ms': result.get('response_time_ms', 0)
            }
        else:
            reason = result.get('reason', 'Unknown error')
            error_type = result.get('error_type', 'general_error')
            
            if error_type == 'configuration_error':
                logger.error(f"❌ Configuration error for message {message_id}: {reason}")
                logger.error(f"👤 User action required: {result.get('user_action_required', 'Check AI configuration')}")
            else:
                logger.warning(f"Message {message_id} not processed: {reason}")
            
            # Clear cache since processing failed
            cache_key = f"ai_processing_{message_id}"
            cache.delete(cache_key)
            return {
                'success': False,
                'message_id': message_id,
                'reason': reason,
                'error_type': error_type,
                'user_action_required': result.get('user_action_required')
            }
            
    except Exception as e:
        logger.error(f"Error processing AI response for message {message_id}: {str(e)}")
        
        # Retry with exponential backoff
        if self.request.retries < self.max_retries:
            # Wait 2^retry_count seconds before retrying
            countdown = 2 ** self.request.retries
            logger.info(f"Retrying AI response processing for message {message_id} in {countdown} seconds")
            raise self.retry(countdown=countdown, exc=e)
        
        # Clear cache since all retries exhausted
        from django.core.cache import cache
        cache_key = f"ai_processing_{message_id}"
        cache.delete(cache_key)
        return {
            'success': False,
            'message_id': message_id,
            'error': str(e),
            'retries_exhausted': True
        }


@shared_task
def cleanup_old_usage_data():
    """
    Cleanup old AI usage tracking data
    Runs periodically to keep database size manageable
    """
    try:
        from AI_model.models import AIUsageTracking
        
        # Delete usage data older than 1 year
        cutoff_date = date.today() - timedelta(days=365)
        deleted_count, deleted_details = AIUsageTracking.objects.filter(date__lt=cutoff_date).delete()
        
        logger.info(f"Cleaned up {deleted_count} old AI usage tracking records older than {cutoff_date}")
        
        return {
            'success': True,
            'deleted_count': deleted_count,
            'cutoff_date': cutoff_date.isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error cleaning up old usage data: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }


@shared_task
def generate_usage_analytics():
    """
    Generate and cache usage analytics
    Can be run periodically to pre-calculate stats
    """
    try:
        from AI_model.models import AIUsageTracking
        from django.db.models import Sum, Avg, Count
        from accounts.models import User
        
        # Calculate analytics for yesterday
        yesterday = date.today() - timedelta(days=1)
        
        # Global stats
        global_stats = AIUsageTracking.objects.filter(date=yesterday).aggregate(
            total_users=Count('user', distinct=True),
            total_requests=Sum('total_requests'),
            total_tokens=Sum('total_tokens'),
            avg_response_time=Avg('average_response_time_ms'),
            total_successful=Sum('successful_requests'),
            total_failed=Sum('failed_requests')
        )
        
        # Top users by requests
        top_users = AIUsageTracking.objects.filter(date=yesterday).exclude(
            total_requests=0
        ).order_by('-total_requests')[:10]
        
        analytics_data = {
            'date': yesterday.isoformat(),
            'global_stats': global_stats,
            'top_users': [
                {
                    'user_id': usage.user.id,
                    'username': usage.user.username,
                    'total_requests': usage.total_requests,
                    'total_tokens': usage.total_tokens,
                    'success_rate': (usage.successful_requests / usage.total_requests * 100) if usage.total_requests > 0 else 0
                }
                for usage in top_users
            ]
        }
        
        logger.info(f"Generated analytics for {yesterday}: {global_stats['total_users']} users, {global_stats['total_requests']} requests")
        
        return {
            'success': True,
            'date': yesterday.isoformat(),
            'analytics': analytics_data
        }
        
    except Exception as e:
        logger.error(f"Error generating usage analytics: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }


@shared_task
def test_ai_configuration():
    """
    Test AI configuration for all users
    Useful for monitoring and debugging
    """
    try:
        from accounts.models import User
        from AI_model.utils import validate_ai_configuration
        
        results = []
        
        # Test for each user
        users = User.objects.filter(is_active=True)
        
        for user in users:
            try:
                validation = validate_ai_configuration(user)
                results.append({
                    'user_id': user.id,
                    'username': user.username,
                    'is_valid': validation['is_valid'],
                    'issues': validation['issues']
                })
            except Exception as e:
                results.append({
                    'user_id': user.id,
                    'username': user.username,
                    'is_valid': False,
                    'error': str(e)
                })
        
        # Summary
        valid_count = len([r for r in results if r['is_valid']])
        total_count = len(results)
        
        logger.info(f"AI configuration test completed: {valid_count}/{total_count} users have valid configuration")
        
        return {
            'success': True,
            'total_users': total_count,
            'valid_users': valid_count,
            'results': results
        }
        
    except Exception as e:
        logger.error(f"Error testing AI configuration: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }


@shared_task
def ensure_global_config():
    """
    Ensure global AI configuration exists
    """
    try:
        from AI_model.models import AIGlobalConfig
        
        config = AIGlobalConfig.get_config()
        
        return {
            'success': True,
            'config_id': config.id,
            'model_name': config.model_name,
            'auto_response_enabled': config.auto_response_enabled
        }
        
    except Exception as e:
        logger.error(f"Error ensuring global AI config: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }


@shared_task(name='AI_model.tasks.test_ai_integration')
def test_ai_integration():
    """
    Deprecated task to catch old scheduled jobs.
    """
    logger.warning("Deprecated task 'test_ai_integration' was called. Please remove it from your periodic task schedule.")
    return {'success': True, 'status': 'deprecated'}

# ============================================================
# AUTO-CHUNKING TASKS (Real-time Knowledge Updates)
# ============================================================

@shared_task(
    bind=True,
    max_retries=3,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=600,
    retry_jitter=True,
    name='ai_model.chunk_qapair'
)
def chunk_qapair_async(self, qapair_id: str) -> Dict[str, Any]:
    """
    Chunk a single QAPair asynchronously
    Triggered by post_save signal on QAPair model
    Idempotent: Safe to retry
    
    Args:
        qapair_id: UUID of QAPair to chunk
        
    Returns:
        dict: Result status
    """
    from web_knowledge.models import QAPair
    from AI_model.services.incremental_chunker import IncrementalChunker
    
    try:
        # Select related to avoid N+1 queries, but handle null relationships
        qa = QAPair.objects.select_related('page', 'page__website', 'page__website__user', 'user').get(id=qapair_id)
        
        # 🔒 FIX: Handle cases where page or website might be None
        # Priority: page.website.user > qa.user > skip
        user = None
        
        if qa.page and qa.page.website and qa.page.website.user:
            # Case 1: QAPair has page -> website -> user
        user = qa.page.website.user
        elif qa.user:
            # Case 2: QAPair has direct user reference
            user = qa.user
        else:
            # Case 3: No user found - cannot chunk
            logger.warning(
                f"⚠️ QAPair {qapair_id} has no associated user "
                f"(page={qa.page_id}, user={qa.user_id}) - skipping chunking"
            )
            return {
                'success': False,
                'qapair_id': str(qapair_id),
                'message': 'QAPair has no associated user - cannot chunk'
            }
        
        chunker = IncrementalChunker(user)
        success = chunker.chunk_qapair(qa)
        
        return {
            'success': success,
            'qapair_id': str(qapair_id),
            'user': user.username,
            'message': f'Chunked QAPair {qapair_id}'
        }
        
    except QAPair.DoesNotExist:
        logger.warning(f"QAPair {qapair_id} not found - may have been deleted")
        return {
            'success': True,  # Not an error - already deleted
            'qapair_id': str(qapair_id),
            'message': 'QAPair not found (already deleted)'
        }
    except Exception as e:
        logger.error(f"Failed to chunk QAPair {qapair_id}: {e}")
        raise  # Retry via Celery


@shared_task(
    bind=True,
    max_retries=3,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=600,
    retry_jitter=True,
    name='ai_model.chunk_product'
)
def chunk_product_async(self, product_id: str) -> Dict[str, Any]:
    """
    Chunk a single Product asynchronously
    Triggered by post_save signal on Product model
    Idempotent: Safe to retry
    
    Args:
        product_id: UUID of Product to chunk
        
    Returns:
        dict: Result status
    """
    from web_knowledge.models import Product
    from AI_model.services.incremental_chunker import IncrementalChunker
    
    try:
        product = Product.objects.select_related('user').get(id=product_id)
        
        # 🔒 FIX: Handle case where user might be None
        if not product.user:
            logger.warning(
                f"⚠️ Product {product_id} has no associated user - skipping chunking"
            )
            return {
                'success': False,
                'product_id': str(product_id),
                'message': 'Product has no associated user - cannot chunk'
            }
        
        user = product.user
        
        chunker = IncrementalChunker(user)
        success = chunker.chunk_product(product)
        
        return {
            'success': success,
            'product_id': str(product_id),
            'user': user.username,
            'message': f'Chunked Product {product_id}'
        }
        
    except Product.DoesNotExist:
        logger.warning(f"Product {product_id} not found - may have been deleted")
        return {
            'success': True,
            'product_id': str(product_id),
            'message': 'Product not found (already deleted)'
        }
    except Exception as e:
        logger.error(f"Failed to chunk Product {product_id}: {e}")
        raise


@shared_task(
    bind=True,
    max_retries=3,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=600,
    retry_jitter=True,
    name='ai_model.chunk_webpage'
)
def chunk_webpage_async(self, page_id: str) -> Dict[str, Any]:
    """
    Chunk a single WebPage asynchronously
    Triggered by post_save signal on WebsitePage model
    May create multiple chunks if content is large
    Idempotent: Safe to retry
    
    Args:
        page_id: UUID of WebsitePage to chunk
        
    Returns:
        dict: Result status
    """
    from web_knowledge.models import WebsitePage
    from AI_model.services.incremental_chunker import IncrementalChunker
    
    try:
        page = WebsitePage.objects.select_related('website', 'website__user').get(id=page_id)
        
        # 🔒 FIX: Handle cases where website or user might be None
        if not page.website:
            logger.warning(
                f"⚠️ WebPage {page_id} has no associated website - skipping chunking"
            )
            return {
                'success': False,
                'page_id': str(page_id),
                'message': 'WebPage has no associated website - cannot chunk'
            }
        
        if not page.website.user:
            logger.warning(
                f"⚠️ WebPage {page_id} has no associated user (website: {page.website.id}) - skipping chunking"
            )
            return {
                'success': False,
                'page_id': str(page_id),
                'message': 'WebPage has no associated user - cannot chunk'
            }
        
        user = page.website.user
        
        chunker = IncrementalChunker(user)
        success = chunker.chunk_webpage(page)
        
        return {
            'success': success,
            'page_id': str(page_id),
            'user': user.username,
            'message': f'Chunked WebPage {page_id}'
        }
        
    except WebsitePage.DoesNotExist:
        logger.warning(f"WebPage {page_id} not found - may have been deleted")
        return {
            'success': True,
            'page_id': str(page_id),
            'message': 'WebPage not found (already deleted)'
        }
    except Exception as e:
        logger.error(f"Failed to chunk WebPage {page_id}: {e}")
        raise


@shared_task(
    bind=True,
    max_retries=3,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=600,
    retry_jitter=True,
    name='ai_model.chunk_manual_prompt'
)
def chunk_manual_prompt_async(self, user_id: int) -> Dict[str, Any]:
    """
    Chunk user's manual prompt asynchronously
    Triggered by post_save signal on AIPrompts model
    Expensive operation (large text)
    Idempotent: Safe to retry
    
    Args:
        user_id: ID of user whose manual prompt to chunk
        
    Returns:
        dict: Result status
    """
    from django.contrib.auth import get_user_model
    from AI_model.services.incremental_chunker import IncrementalChunker
    
    User = get_user_model()
    
    try:
        user = User.objects.get(id=user_id)
        
        chunker = IncrementalChunker(user)
        success = chunker.chunk_manual_prompt()
        
        return {
            'success': success,
            'user_id': user_id,
            'user': user.username,
            'message': f'Chunked Manual Prompt for user {user.username}'
        }
        
    except User.DoesNotExist:
        logger.error(f"User {user_id} not found")
        return {
            'success': False,
            'user_id': user_id,
            'message': 'User not found'
        }
    except Exception as e:
        logger.error(f"Failed to chunk Manual Prompt for user {user_id}: {e}")
        raise


@shared_task(
    bind=True,
    max_retries=3,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=600,
    retry_jitter=True,
    name='ai_model.delete_chunks_for_source'
)
def delete_chunks_for_source_async(self, user_id: int, source_id: str, chunk_type: str) -> Dict[str, Any]:
    """
    Delete chunks when source is deleted
    Triggered by post_delete signals
    
    Args:
        user_id: ID of user
        source_id: UUID of deleted source
        chunk_type: Type of chunk (faq, product, website)
        
    Returns:
        dict: Result status
    """
    from django.contrib.auth import get_user_model
    from AI_model.services.incremental_chunker import IncrementalChunker
    
    User = get_user_model()
    
    try:
        user = User.objects.get(id=user_id)
        
        chunker = IncrementalChunker(user)
        deleted_count = chunker.delete_chunks_for_source(source_id, chunk_type)
        
        return {
            'success': True,
            'user': user.username,
            'source_id': source_id,
            'chunk_type': chunk_type,
            'deleted_count': deleted_count,
            'message': f'Deleted {deleted_count} chunks for {chunk_type} {source_id}'
        }
        
    except User.DoesNotExist:
        logger.error(f"User {user_id} not found")
        return {
            'success': False,
            'user_id': user_id,
            'message': 'User not found'
        }
    except Exception as e:
        logger.error(f"Failed to delete chunks for {chunk_type} {source_id}: {e}")
        raise


@shared_task(name='ai_model.reconcile_knowledge')
def reconcile_knowledge_task() -> Dict[str, Any]:
    """
    Nightly reconciliation task
    Catches missed signals, orphaned chunks, missing embeddings
    Scheduled via Celery Beat at 3 AM daily
    
    Returns:
        dict: Reconciliation results
    """
    from django.contrib.auth import get_user_model
    from AI_model.models import TenantKnowledge
    from web_knowledge.models import QAPair, Product, WebsitePage
    
    User = get_user_model()
    
    results = {
        'orphaned_deleted': 0,
        'missing_chunks_queued': 0,
        'missing_embeddings_queued': 0,
        'users_processed': 0
    }
    
    try:
        # 1. Find and delete orphaned chunks (source deleted but chunk exists)
        
        # FAQ orphans
        faq_chunk_ids = set(TenantKnowledge.objects.filter(
            chunk_type='faq',
            source_id__isnull=False
        ).values_list('source_id', flat=True))
        
        existing_qa_ids = set(QAPair.objects.values_list('id', flat=True))
        orphaned_faq_ids = faq_chunk_ids - existing_qa_ids
        
        if orphaned_faq_ids:
            deleted = TenantKnowledge.objects.filter(
                chunk_type='faq',
                source_id__in=orphaned_faq_ids
            ).delete()[0]
            results['orphaned_deleted'] += deleted
            logger.info(f"Deleted {deleted} orphaned FAQ chunks")
        
        # Product orphans
        product_chunk_ids = set(TenantKnowledge.objects.filter(
            chunk_type='product',
            source_id__isnull=False
        ).values_list('source_id', flat=True))
        
        existing_product_ids = set(Product.objects.values_list('id', flat=True))
        orphaned_product_ids = product_chunk_ids - existing_product_ids
        
        if orphaned_product_ids:
            deleted = TenantKnowledge.objects.filter(
                chunk_type='product',
                source_id__in=orphaned_product_ids
            ).delete()[0]
            results['orphaned_deleted'] += deleted
            logger.info(f"Deleted {deleted} orphaned Product chunks")
        
        # Website orphans
        website_chunk_ids = set(TenantKnowledge.objects.filter(
            chunk_type='website',
            source_id__isnull=False
        ).values_list('source_id', flat=True))
        
        existing_page_ids = set(WebsitePage.objects.values_list('id', flat=True))
        orphaned_page_ids = website_chunk_ids - existing_page_ids
        
        if orphaned_page_ids:
            deleted = TenantKnowledge.objects.filter(
                chunk_type='website',
                source_id__in=orphaned_page_ids
            ).delete()[0]
            results['orphaned_deleted'] += deleted
            logger.info(f"Deleted {deleted} orphaned Website chunks")
        
        # 2. Find missing chunks (source exists but no chunk)
        
        # Missing FAQ chunks
        chunked_qa_ids = set(TenantKnowledge.objects.filter(
            chunk_type='faq'
        ).values_list('source_id', flat=True))
        
        qapairs_without_chunks = QAPair.objects.filter(
            generation_status='completed'
        ).exclude(
            id__in=chunked_qa_ids
        )
        
        for qa in qapairs_without_chunks[:100]:  # Limit to 100 per run
            chunk_qapair_async.apply_async(args=[str(qa.id)], countdown=10)
            results['missing_chunks_queued'] += 1
        
        # Missing Product chunks
        chunked_product_ids = set(TenantKnowledge.objects.filter(
            chunk_type='product'
        ).values_list('source_id', flat=True))
        
        products_without_chunks = Product.objects.exclude(
            id__in=chunked_product_ids
        )
        
        for product in products_without_chunks[:100]:
            chunk_product_async.apply_async(args=[str(product.id)], countdown=10)
            results['missing_chunks_queued'] += 1
        
        # 3. Find chunks with missing embeddings
        missing_embeddings = TenantKnowledge.objects.filter(
            tldr_embedding__isnull=True
        )[:50]  # Limit to 50 per run
        
        for chunk in missing_embeddings:
            # Re-chunk the source to regenerate embedding
            if chunk.chunk_type == 'faq' and chunk.source_id:
                chunk_qapair_async.apply_async(args=[str(chunk.source_id)], countdown=10)
                results['missing_embeddings_queued'] += 1
            elif chunk.chunk_type == 'product' and chunk.source_id:
                chunk_product_async.apply_async(args=[str(chunk.source_id)], countdown=10)
                results['missing_embeddings_queued'] += 1
            elif chunk.chunk_type == 'website' and chunk.source_id:
                chunk_webpage_async.apply_async(args=[str(chunk.source_id)], countdown=10)
                results['missing_embeddings_queued'] += 1
        
        # 4. Count users processed
        results['users_processed'] = User.objects.count()
        
        logger.info(f"✅ Nightly reconciliation complete: {results}")
        
        return results
        
    except Exception as e:
        logger.error(f"❌ Reconciliation failed: {e}")
        raise
