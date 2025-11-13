"""
Signals for integrations app
Auto-chunk WordPress content to TenantKnowledge
"""
import logging
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver

logger = logging.getLogger(__name__)


@receiver(post_save, sender='integrations.WordPressContent')
def sync_wordpress_content_to_knowledge_base(sender, instance, created, **kwargs):
    """
    Auto-chunk WordPress content when created/updated
    + اضافه کردن به WebsitePage برای نمایش در dashboard
    """
    try:
        from AI_model.models import TenantKnowledge
        from AI_model.services.embedding_service import EmbeddingService
        from web_knowledge.models import WebsiteSource, WebsitePage
        import hashlib
        
        # Skip if not published
        if not instance.is_published:
            # Delete from knowledge base
            TenantKnowledge.objects.filter(
                user=instance.user,
                chunk_type='website',
                source_id=instance.id
            ).delete()
            # Delete from WebsitePage
            WebsitePage.objects.filter(
                source_type='wordpress',
                wordpress_post_id=instance.wp_post_id
            ).delete()
            logger.info(f"🗑️ Removed unpublished content from KB & Pages: {instance.title}")
            return
        
        # ✅ اضافه کردن به WebsitePage (برای نمایش در dashboard)
        # ابتدا WebsiteSource برای WordPress پیدا یا بساز
        wordpress_source, _ = WebsiteSource.objects.get_or_create(
            user=instance.user,
            url='https://wordpress-sync',
            defaults={
                'name': '📝 محتوای WordPress',
                'description': 'صفحات و نوشته‌های همگام‌سازی شده از WordPress',
                'max_pages': 10000,
                'crawl_depth': 1,
                'crawl_status': 'completed',
                'crawl_progress': 100.0  # WordPress content is always complete (no crawling needed)
            }
        )
        
        # Update crawl_progress if it was already created (in case it was 0)
        if wordpress_source.crawl_progress < 100.0:
            wordpress_source.crawl_progress = 100.0
            wordpress_source.save(update_fields=['crawl_progress'])
        
        # ایجاد یا به‌روزرسانی WebsitePage
        webpage, webpage_created = WebsitePage.objects.update_or_create(
            url=instance.permalink,
            defaults={
                'website': wordpress_source,
                'title': instance.title,
                'cleaned_content': instance.content,
                'raw_content': instance.content,  # برای WordPress همانه
                'word_count': len(instance.content.split()),
                'processing_status': 'completed',
                'processed_at': instance.last_synced_at,
                'source_type': 'wordpress',
                'wordpress_post_id': instance.wp_post_id,
                'meta_description': instance.excerpt[:160] if instance.excerpt else '',
            }
        )
        
        logger.info(f"✅ WordPress content {'added to' if webpage_created else 'updated in'} WebsitePage: {instance.title}")
        
        # Build full text for embedding
        full_text = f"# {instance.title}\n\n"
        
        if instance.excerpt:
            full_text += f"**خلاصه:** {instance.excerpt}\n\n"
        
        full_text += instance.content
        
        if instance.author:
            full_text += f"\n\nنویسنده: {instance.author}"
        
        if instance.categories:
            full_text += f"\n\nدسته‌بندی: {', '.join(instance.categories)}"
        
        if instance.tags:
            full_text += f"\n\nبرچسب‌ها: {', '.join(instance.tags)}"
        
        # Generate TL;DR
        tldr = instance.title
        if instance.excerpt:
            tldr += f" - {instance.excerpt[:150]}"
        elif len(instance.content) > 0:
            tldr += f" - {instance.content[:150]}..."
        
        # Generate embeddings
        embedding_service = EmbeddingService()
        tldr_embedding = embedding_service.get_embedding(tldr)
        full_embedding = embedding_service.get_embedding(full_text[:5000])  # Limit to 5000 chars
        
        if not tldr_embedding or not full_embedding:
            logger.warning(f"⚠️ Failed to generate embeddings for: {instance.title}")
            return
        
        # Create or update in TenantKnowledge
        chunk, chunk_created = TenantKnowledge.objects.update_or_create(
            user=instance.user,
            chunk_type='website',
            source_id=instance.id,
            defaults={
                'section_title': instance.title,
                'full_text': full_text[:10000],  # Limit
                'tldr': tldr[:500],
                'tldr_embedding': tldr_embedding,
                'full_embedding': full_embedding,
                'word_count': len(full_text.split()),
                'metadata': {
                    'content_type': instance.content_type,
                    'post_type': instance.post_type_slug,
                    'permalink': instance.permalink,
                    'categories': instance.categories,
                    'tags': instance.tags,
                    'author': instance.author,
                }
            }
        )
        
        action = "Added" if chunk_created else "Updated"
        logger.info(f"✅ {action} WordPress content in KB: {instance.title}")
        
    except Exception as e:
        logger.error(f"❌ Failed to sync WordPress content: {e}")


@receiver(pre_delete, sender='integrations.WordPressContent')
def cleanup_wordpress_content_chunks(sender, instance, **kwargs):
    """Delete chunks when WordPress content is deleted"""
    try:
        from AI_model.models import TenantKnowledge
        
        deleted = TenantKnowledge.objects.filter(
            user=instance.user,
            chunk_type='website',
            source_id=instance.id
        ).delete()
        
        if deleted[0] > 0:
            logger.info(f"🗑️ Deleted {deleted[0]} chunks for WordPress content: {instance.title}")
            
    except Exception as e:
        logger.error(f"❌ Failed to delete chunks: {e}")

