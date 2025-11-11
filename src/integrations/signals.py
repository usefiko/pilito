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
    Similar to Product sync but for Pages/Posts
    """
    try:
        from AI_model.models import TenantKnowledge
        from AI_model.services.embedding_service import EmbeddingService
        import hashlib
        
        # Skip if not published
        if not instance.is_published:
            # Delete from knowledge base
            TenantKnowledge.objects.filter(
                user=instance.user,
                chunk_type='website',
                source_id=instance.id
            ).delete()
            logger.info(f"🗑️ Removed unpublished content from KB: {instance.title}")
            return
        
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

