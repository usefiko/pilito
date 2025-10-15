"""
Signals for web_knowledge app
Automatically sync products to TenantKnowledge for AI search
"""
import logging
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.db import transaction

logger = logging.getLogger(__name__)


@receiver(post_save, sender='web_knowledge.Product')
def sync_product_to_knowledge_base(sender, instance, created, **kwargs):
    """
    When a Product is created or updated, automatically add/update it in TenantKnowledge
    This ensures products are searchable by the AI
    """
    try:
        from AI_model.models import TenantKnowledge
        from AI_model.services.embedding_service import EmbeddingService
        
        # Skip if product is not active
        if not instance.is_active:
            # If product was deactivated, delete from knowledge base
            TenantKnowledge.objects.filter(
                user=instance.user,
                chunk_type='product',
                source_id=instance.id
            ).delete()
            logger.info(f"🗑️ Removed inactive product from knowledge base: {instance.title}")
            return
        
        # Build full text for embedding
        full_text = f"Product: {instance.title}\n"
        full_text += f"Type: {instance.get_product_type_display()}\n"
        
        if instance.description:
            full_text += f"Description: {instance.description}\n"
        
        if instance.short_description:
            full_text += f"Short: {instance.short_description}\n"
        
        if instance.price:
            price_info = f"Price: {instance.price} {instance.currency}"
            if instance.original_price and instance.original_price > instance.price:
                price_info += f" (was {instance.original_price})"
            if instance.discount_percentage:
                price_info += f" - {instance.discount_percentage}% OFF"
            full_text += price_info + "\n"
        
        if instance.billing_period and instance.billing_period != 'one_time':
            full_text += f"Billing: {instance.get_billing_period_display()}\n"
        
        if instance.features:
            full_text += f"Features: {', '.join(instance.features[:5])}\n"  # First 5 features
        
        if instance.brand:
            full_text += f"Brand: {instance.brand}\n"
        
        if instance.category:
            full_text += f"Category: {instance.category}\n"
        
        if instance.in_stock is not None:
            full_text += f"In Stock: {'Yes' if instance.in_stock else 'No'}\n"
        
        if instance.link:
            full_text += f"Link: {instance.link}\n"
        
        if instance.tags:
            full_text += f"Tags: {', '.join(instance.tags[:5])}\n"  # First 5 tags
        
        # Generate TL;DR (summary)
        tldr_parts = [instance.title]
        if instance.short_description:
            tldr_parts.append(instance.short_description[:100])
        elif instance.description:
            tldr_parts.append(instance.description[:100])
        if instance.price:
            tldr_parts.append(f"{instance.price} {instance.currency}")
        
        tldr = " - ".join(tldr_parts)
        
        # Generate embeddings
        embedding_service = EmbeddingService()
        tldr_embedding = embedding_service.get_embedding(tldr)
        full_embedding = embedding_service.get_embedding(full_text)
        
        if not tldr_embedding or not full_embedding:
            logger.warning(f"⚠️ Failed to generate embeddings for product: {instance.title}")
            return
        
        # Detect language (simple: check if there are Persian/Arabic characters)
        def detect_language(text):
            if any('\u0600' <= c <= '\u06FF' or '\u0750' <= c <= '\u077F' for c in text):
                return 'fa'  # Persian
            return 'en'  # Default to English
        
        # Create or update in TenantKnowledge
        chunk, chunk_created = TenantKnowledge.objects.update_or_create(
            user=instance.user,
            chunk_type='product',
            source_id=instance.id,
            defaults={
                'section_title': instance.title,
                'full_text': full_text,
                'tldr': tldr,
                'tldr_embedding': tldr_embedding,
                'full_embedding': full_embedding,
                'language': detect_language(instance.title + ' ' + (instance.description or '')),
                'word_count': len(full_text.split()),
                'metadata': {
                    'product_type': instance.product_type,
                    'price': float(instance.price) if instance.price else None,
                    'currency': instance.currency,
                    'link': instance.link or '',
                    'brand': instance.brand or '',
                    'category': instance.category or '',
                    'tags': instance.tags or [],
                    'in_stock': instance.in_stock,
                    'has_discount': instance.has_discount,
                    'extraction_method': instance.extraction_method,
                }
            }
        )
        
        action = "Added" if chunk_created else "Updated"
        logger.info(f"✅ {action} product in knowledge base: {instance.title} (ID: {instance.id})")
        
    except Exception as e:
        logger.error(f"❌ Failed to sync product to knowledge base: {e}")
        import traceback
        logger.debug(traceback.format_exc())


@receiver(post_delete, sender='web_knowledge.Product')
def remove_product_from_knowledge_base(sender, instance, **kwargs):
    """
    When a Product is deleted, remove it from TenantKnowledge
    """
    try:
        from AI_model.models import TenantKnowledge
        
        deleted_count = TenantKnowledge.objects.filter(
            user=instance.user,
            chunk_type='product',
            source_id=instance.id
        ).delete()[0]
        
        if deleted_count > 0:
            logger.info(f"🗑️ Removed product from knowledge base: {instance.title}")
        
    except Exception as e:
        logger.error(f"❌ Failed to remove product from knowledge base: {e}")


logger.info("✅ Product sync signals registered")

