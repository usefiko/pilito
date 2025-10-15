"""
Nightly Reconciliation Command
Catches missed signals, orphaned chunks, missing embeddings
Run: python manage.py reconcile_knowledge_base
Schedule: Celery Beat @ 3 AM daily
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from AI_model.models import TenantKnowledge
from web_knowledge.models import QAPair, Product, WebsitePage
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Nightly reconciliation: cleanup orphans, queue missing chunks'
    
    def handle(self, *args, **options):
        from AI_model.tasks import chunk_qapair_async, chunk_product_async, chunk_webpage_async
        
        self.stdout.write("\n" + "="*80)
        self.stdout.write("🌙 NIGHTLY KNOWLEDGE BASE RECONCILIATION")
        self.stdout.write("="*80 + "\n")
        
        results = {
            'orphaned_deleted': 0,
            'missing_chunks_queued': 0,
            'missing_embeddings_queued': 0
        }
        
        # 1. Find and delete orphaned FAQ chunks
        self.stdout.write("1️⃣ Cleaning orphaned FAQ chunks...")
        faq_chunk_ids = set(TenantKnowledge.objects.filter(
            chunk_type='faq', source_id__isnull=False
        ).values_list('source_id', flat=True))
        
        existing_qa_ids = set(QAPair.objects.values_list('id', flat=True))
        orphaned_faq_ids = faq_chunk_ids - existing_qa_ids
        
        if orphaned_faq_ids:
            deleted = TenantKnowledge.objects.filter(
                chunk_type='faq', source_id__in=orphaned_faq_ids
            ).delete()[0]
            results['orphaned_deleted'] += deleted
            self.stdout.write(f"   ✅ Deleted {deleted} orphaned FAQ chunks")
        
        # 2. Find missing FAQ chunks
        self.stdout.write("\n2️⃣ Queueing missing FAQ chunks...")
        chunked_qa_ids = set(TenantKnowledge.objects.filter(
            chunk_type='faq'
        ).values_list('source_id', flat=True))
        
        qapairs_without_chunks = QAPair.objects.filter(
            generation_status='completed'
        ).exclude(id__in=chunked_qa_ids)[:100]
        
        for qa in qapairs_without_chunks:
            chunk_qapair_async.apply_async(args=[str(qa.id)], countdown=10)
            results['missing_chunks_queued'] += 1
        
        if results['missing_chunks_queued'] > 0:
            self.stdout.write(f"   ✅ Queued {results['missing_chunks_queued']} missing FAQ chunks")
        
        # 3. Find and delete orphaned Product chunks
        self.stdout.write("\n3️⃣ Cleaning orphaned Product chunks...")
        product_chunk_ids = set(TenantKnowledge.objects.filter(
            chunk_type='product', source_id__isnull=False
        ).values_list('source_id', flat=True))
        
        existing_product_ids = set(Product.objects.values_list('id', flat=True))
        orphaned_product_ids = product_chunk_ids - existing_product_ids
        
        if orphaned_product_ids:
            deleted = TenantKnowledge.objects.filter(
                chunk_type='product', source_id__in=orphaned_product_ids
            ).delete()[0]
            results['orphaned_deleted'] += deleted
            self.stdout.write(f"   ✅ Deleted {deleted} orphaned Product chunks")
        
        # 4. Find missing Product chunks
        self.stdout.write("\n4️⃣ Queueing missing Product chunks...")
        chunked_product_ids = set(TenantKnowledge.objects.filter(
            chunk_type='product'
        ).values_list('source_id', flat=True))
        
        products_without_chunks = Product.objects.exclude(
            id__in=chunked_product_ids
        )[:100]
        
        count_before = results['missing_chunks_queued']
        for product in products_without_chunks:
            chunk_product_async.apply_async(args=[str(product.id)], countdown=10)
            results['missing_chunks_queued'] += 1
        
        if results['missing_chunks_queued'] > count_before:
            self.stdout.write(f"   ✅ Queued {results['missing_chunks_queued'] - count_before} missing Product chunks")
        
        # 5. Find chunks with missing embeddings
        self.stdout.write("\n5️⃣ Queueing chunks with missing embeddings...")
        missing_embeddings = TenantKnowledge.objects.filter(
            tldr_embedding__isnull=True
        )[:50]
        
        for chunk in missing_embeddings:
            if chunk.chunk_type == 'faq' and chunk.source_id:
                chunk_qapair_async.apply_async(args=[str(chunk.source_id)], countdown=10)
                results['missing_embeddings_queued'] += 1
            elif chunk.chunk_type == 'product' and chunk.source_id:
                chunk_product_async.apply_async(args=[str(chunk.source_id)], countdown=10)
                results['missing_embeddings_queued'] += 1
            elif chunk.chunk_type == 'website' and chunk.source_id:
                chunk_webpage_async.apply_async(args=[str(chunk.source_id)], countdown=10)
                results['missing_embeddings_queued'] += 1
        
        if results['missing_embeddings_queued'] > 0:
            self.stdout.write(f"   ✅ Queued {results['missing_embeddings_queued']} chunks for re-embedding")
        
        # Final summary
        self.stdout.write("\n" + "="*80)
        self.stdout.write("📊 RECONCILIATION COMPLETE:")
        self.stdout.write(f"   - Orphaned chunks deleted: {results['orphaned_deleted']}")
        self.stdout.write(f"   - Missing chunks queued: {results['missing_chunks_queued']}")
        self.stdout.write(f"   - Missing embeddings queued: {results['missing_embeddings_queued']}")
        self.stdout.write("="*80 + "\n")
