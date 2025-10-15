"""
Debug Knowledge Retrieval - Check if RAG system is working
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from AI_model.models import TenantKnowledge
from AI_model.services.context_retriever import ContextRetriever
from AI_model.services.query_router import QueryRouter
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Debug knowledge retrieval system for a user'

    def add_arguments(self, parser):
        parser.add_argument('--username', type=str, required=True, help='Username to debug')
        parser.add_argument('--query', type=str, default='تیم فیکو کیا هستن؟', help='Test query')

    def handle(self, *args, **options):
        User = get_user_model()
        username = options['username']
        test_query = options['query']
        
        self.stdout.write("\n" + "="*80)
        self.stdout.write(f"🔍 DEBUGGING KNOWLEDGE RETRIEVAL FOR: {username}")
        self.stdout.write("="*80 + "\n")
        
        # 1. Find user
        try:
            user = User.objects.get(username=username)
            self.stdout.write(self.style.SUCCESS(f"✅ User found: {user.username} (ID: {user.id})"))
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"❌ User '{username}' not found!"))
            return
        
        # 2. Check TenantKnowledge
        self.stdout.write("\n" + "-"*80)
        self.stdout.write("📊 KNOWLEDGE BASE STATUS:")
        self.stdout.write("-"*80)
        
        total = TenantKnowledge.objects.filter(user=user).count()
        self.stdout.write(f"Total Chunks: {total}")
        
        if total == 0:
            self.stdout.write(self.style.ERROR("❌ PROBLEM: Knowledge base is EMPTY!"))
            self.stdout.write("\nSOLUTION: Run this command first:")
            self.stdout.write(f"  python manage.py populate_knowledge_base --user {username}")
            return
        
        # Breakdown by source
        for chunk_type in ['faq', 'manual', 'product', 'website']:
            count = TenantKnowledge.objects.filter(user=user, chunk_type=chunk_type).count()
            status = "✅" if count > 0 else "❌"
            self.stdout.write(f"  {status} {chunk_type.upper()}: {count} chunks")
        
        # 3. Check embeddings
        self.stdout.write("\n" + "-"*80)
        self.stdout.write("🧬 EMBEDDING STATUS:")
        self.stdout.write("-"*80)
        
        chunks_with_embedding = TenantKnowledge.objects.filter(
            user=user,
            tldr_embedding__isnull=False
        ).count()
        
        self.stdout.write(f"Chunks with embeddings: {chunks_with_embedding}/{total}")
        
        if chunks_with_embedding == 0:
            self.stdout.write(self.style.ERROR("❌ PROBLEM: No embeddings found!"))
            self.stdout.write("\nSOLUTION: Re-populate with embeddings:")
            self.stdout.write(f"  python manage.py populate_knowledge_base --user {username} --force")
            return
        elif chunks_with_embedding < total:
            self.stdout.write(self.style.WARNING(f"⚠️ WARNING: {total - chunks_with_embedding} chunks missing embeddings!"))
        else:
            self.stdout.write(self.style.SUCCESS("✅ All chunks have embeddings"))
        
        # 4. Test Query Router
        self.stdout.write("\n" + "-"*80)
        self.stdout.write(f"🎯 QUERY ROUTING TEST: '{test_query}'")
        self.stdout.write("-"*80)
        
        try:
            routing = QueryRouter.route_query(test_query, user=user)
            self.stdout.write(f"Intent: {routing['intent']}")
            self.stdout.write(f"Confidence: {routing['confidence']:.2f}")
            self.stdout.write(f"Primary Source: {routing['primary_source']}")
            self.stdout.write(f"Secondary Sources: {routing['secondary_sources']}")
            self.stdout.write(f"Token Budgets: Primary={routing['token_budgets']['primary']}, Secondary={routing['token_budgets']['secondary']}")
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Query routing failed: {e}"))
            return
        
        # 5. Test Context Retrieval
        self.stdout.write("\n" + "-"*80)
        self.stdout.write("📚 CONTEXT RETRIEVAL TEST:")
        self.stdout.write("-"*80)
        
        try:
            result = ContextRetriever.retrieve_context(
                query=test_query,
                user=user,
                primary_source=routing['primary_source'],
                secondary_sources=routing['secondary_sources'],
                primary_budget=routing['token_budgets']['primary'],
                secondary_budget=routing['token_budgets']['secondary'],
                routing_info=routing
            )
            
            self.stdout.write(f"Retrieval Method: {result['retrieval_method']}")
            self.stdout.write(f"Total Chunks Retrieved: {result['total_chunks']}")
            self.stdout.write(f"Primary Chunks: {len(result['primary_context'])}")
            self.stdout.write(f"Secondary Chunks: {len(result['secondary_context'])}")
            
            if result['total_chunks'] == 0:
                self.stdout.write(self.style.ERROR("\n❌ PROBLEM: No context retrieved!"))
                self.stdout.write("\nPOSSIBLE CAUSES:")
                self.stdout.write("  1. Similarity threshold too high (MIN_SIMILARITY_SCORE)")
                self.stdout.write("  2. Query embedding mismatch")
                self.stdout.write("  3. Wrong chunk_type filter")
                
                # Show sample chunks for debugging
                self.stdout.write("\n📝 SAMPLE CHUNKS IN DATABASE:")
                for chunk in TenantKnowledge.objects.filter(user=user)[:5]:
                    self.stdout.write(f"  [{chunk.chunk_type}] {chunk.section_title or 'No title'}")
                    self.stdout.write(f"    Content preview: {chunk.full_text[:100]}...")
                    self.stdout.write(f"    Has embedding: {'Yes' if chunk.tldr_embedding else 'No'}\n")
            else:
                self.stdout.write(self.style.SUCCESS(f"\n✅ Retrieved {result['total_chunks']} relevant chunks!"))
                
                # Show retrieved chunks
                self.stdout.write("\n📄 RETRIEVED CHUNKS:")
                for i, chunk in enumerate(result['primary_context'][:3], 1):
                    self.stdout.write(f"\n  {i}. [{chunk['type']}] {chunk['title']}")
                    self.stdout.write(f"     Score: {chunk['score']}")
                    self.stdout.write(f"     Content: {chunk['content'][:150]}...")
        
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Context retrieval failed: {e}"))
            import traceback
            self.stdout.write(traceback.format_exc())
            return
        
        # 6. Final Summary
        self.stdout.write("\n" + "="*80)
        self.stdout.write("📋 SUMMARY:")
        self.stdout.write("="*80)
        
        if result['total_chunks'] > 0:
            self.stdout.write(self.style.SUCCESS("✅ RAG system is WORKING!"))
            self.stdout.write(f"✅ Knowledge base has {total} chunks")
            self.stdout.write(f"✅ Embeddings are present ({chunks_with_embedding}/{total})")
            self.stdout.write(f"✅ Retrieved {result['total_chunks']} relevant chunks")
        else:
            self.stdout.write(self.style.ERROR("❌ RAG system has ISSUES!"))
            self.stdout.write("\nRECOMMENDED FIXES:")
            self.stdout.write("  1. Check embedding generation")
            self.stdout.write("  2. Lower MIN_SIMILARITY_SCORE in context_retriever.py")
            self.stdout.write("  3. Verify chunk_type values match query routing")
        
        self.stdout.write("\n" + "="*80 + "\n")

