#!/usr/bin/env python
"""
Test script to debug why address query is not found
"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.contrib.auth import get_user_model
from AI_model.models import TenantKnowledge
from AI_model.services.production_rag import ProductionRAG
from AI_model.services.hybrid_retriever import HybridRetriever
from AI_model.services.embedding_service import EmbeddingService
from AI_model.services.token_budget_controller import TokenBudgetController
from AI_model.services.persian_normalizer import get_normalizer

User = get_user_model()
user = User.objects.get(phone_number='+989158157440')

print('='*80)
print('🔍 تست کامل: چرا آدرس پیدا نمی‌شود؟')
print('='*80)

query = "ادرستون"
print(f'\n1️⃣ Query: "{query}"')

# Check if address exists in chunks
print(f'\n2️⃣ بررسی وجود آدرس در chunks:')
print('-'*80)

faq_chunks = TenantKnowledge.objects.filter(
    user=user,
    chunk_type='faq'
)

print(f'   تعداد FAQ chunks: {faq_chunks.count()}')

address_chunks = []
for chunk in faq_chunks:
    text = f"{chunk.section_title or ''} {chunk.full_text}"
    if 'مشهد' in text and 'فردوسی' in text:
        address_chunks.append(chunk)
        print(f'\n   ✅ Chunk با آدرس پیدا شد:')
        print(f'      ID: {chunk.id}')
        print(f'      Title: {chunk.section_title}')
        print(f'      Text preview: {chunk.full_text[:200]}...')
        print(f'      Has tldr_embedding: {chunk.tldr_embedding is not None and len(chunk.tldr_embedding) > 0}')
        print(f'      Has full_embedding: {chunk.full_embedding is not None and len(chunk.full_embedding) > 0}')

if not address_chunks:
    print('   ❌ هیچ chunkی با آدرس پیدا نشد!')
    print('   ⚠️ مشکل: آدرس در chunks موجود نیست!')
else:
    print(f'\n   ✅ {len(address_chunks)} chunk با آدرس پیدا شد')

# Test normalization
print(f'\n3️⃣ تست Normalization:')
print('-'*80)
normalizer = get_normalizer()
query_normalized = normalizer.normalize_for_search(query) if normalizer.is_persian(query) else query
print(f'   Query اصلی: "{query}"')
print(f'   Query normalized: "{query_normalized}"')

if address_chunks:
    chunk_text = f"{address_chunks[0].section_title or ''} {address_chunks[0].full_text}"
    chunk_normalized = normalizer.normalize_for_search(chunk_text) if normalizer.is_persian(chunk_text) else chunk_text
    print(f'\n   Chunk text normalized preview: {chunk_normalized[:200]}...')
    
    # Check if normalized query matches
    if query_normalized in chunk_normalized:
        print(f'   ✅ Normalized query در chunk پیدا شد!')
    else:
        print(f'   ❌ Normalized query در chunk پیدا نشد!')

# Test embedding generation
print(f'\n4️⃣ تست Embedding Generation:')
print('-'*80)
embedding_service = EmbeddingService()
query_embedding = embedding_service.get_embedding(query_normalized, task_type="retrieval_query")

if query_embedding:
    print(f'   ✅ Query embedding ساخته شد: {len(query_embedding)} dimensions')
else:
    print(f'   ❌ Query embedding ساخته نشد!')
    sys.exit(1)

# Test BM25 search
print(f'\n5️⃣ تست BM25 Search:')
print('-'*80)
try:
    bm25_results = HybridRetriever._bm25_search(query_normalized, user, 'faq', 20)
    print(f'   تعداد نتایج BM25: {len(bm25_results)}')
    
    if bm25_results:
        print(f'   Top 5 BM25 results:')
        for i, (chunk_id, score) in enumerate(bm25_results[:5], 1):
            chunk = TenantKnowledge.objects.get(id=chunk_id)
            has_address = 'مشهد' in chunk.full_text and 'فردوسی' in chunk.full_text
            print(f'      {i}. Chunk ID: {chunk_id}, Score: {score:.4f}, Has address: {"✅" if has_address else "❌"}')
    else:
        print('   ❌ هیچ نتیجه‌ای از BM25 پیدا نشد!')
except Exception as e:
    print(f'   ❌ BM25 search failed: {e}')
    import traceback
    traceback.print_exc()

# Test Vector search
print(f'\n6️⃣ تست Vector Search:')
print('-'*80)
try:
    vector_results = HybridRetriever._vector_search(query_embedding, user, 'faq', 20, language='fa')
    print(f'   تعداد نتایج Vector: {len(vector_results)}')
    
    if vector_results:
        print(f'   Top 5 Vector results:')
        for i, (chunk_id, similarity) in enumerate(vector_results[:5], 1):
            chunk = TenantKnowledge.objects.get(id=chunk_id)
            has_address = 'مشهد' in chunk.full_text and 'فردوسی' in chunk.full_text
            print(f'      {i}. Chunk ID: {chunk_id}, Similarity: {similarity:.4f}, Has address: {"✅" if has_address else "❌"}')
    else:
        print('   ❌ هیچ نتیجه‌ای از Vector پیدا نشد!')
        print('   ⚠️ ممکن است threshold خیلی بالا باشد (0.98 = similarity > 0.02)')
except Exception as e:
    print(f'   ❌ Vector search failed: {e}')
    import traceback
    traceback.print_exc()

# Test Hybrid search
print(f'\n7️⃣ تست Hybrid Search:')
print('-'*80)
try:
    hybrid_results = HybridRetriever.hybrid_search(
        query=query_normalized,
        user=user,
        chunk_type='faq',
        query_embedding=query_embedding,
        top_k=10
    )
    print(f'   تعداد نتایج Hybrid: {len(hybrid_results)}')
    
    if hybrid_results:
        print(f'   Top 5 Hybrid results:')
        for i, result in enumerate(hybrid_results[:5], 1):
            content = result.get('content', '')
            score = result.get('score', 0)
            has_address = 'مشهد' in content and 'فردوسی' in content
            print(f'      {i}. Score: {score:.4f}, Has address: {"✅" if has_address else "❌"}')
            print(f'         Preview: {content[:150]}...')
    else:
        print('   ❌ هیچ نتیجه‌ای از Hybrid پیدا نشد!')
except Exception as e:
    print(f'   ❌ Hybrid search failed: {e}')
    import traceback
    traceback.print_exc()

# Test ProductionRAG
print(f'\n8️⃣ تست ProductionRAG:')
print('-'*80)
try:
    rag_result = ProductionRAG.retrieve_context(
        query=query,
        user=user,
        primary_source='faq',
        secondary_sources=[],
        primary_budget=650,
        secondary_budget=0,
        routing_info=None
    )
    
    primary_chunks = rag_result.get('primary_context', [])
    print(f'   تعداد نتایج ProductionRAG: {len(primary_chunks)}')
    
    if primary_chunks:
        print(f'   Top 5 ProductionRAG results:')
        for i, chunk in enumerate(primary_chunks[:5], 1):
            content = chunk.get('content', '')
            has_address = 'مشهد' in content and 'فردوسی' in content
            print(f'      {i}. Has address: {"✅" if has_address else "❌"}')
            print(f'         Preview: {content[:150]}...')
            
            if has_address:
                print(f'         ✅✅✅ آدرس در نتایج ProductionRAG پیدا شد!')
    else:
        print('   ❌ هیچ نتیجه‌ای از ProductionRAG پیدا نشد!')
except Exception as e:
    print(f'   ❌ ProductionRAG failed: {e}')
    import traceback
    traceback.print_exc()

print(f'\n9️⃣ نتیجه نهایی:')
print('='*80)
print('✅ تست کامل شد!')
print('بررسی کنید که در کدام مرحله آدرس پیدا نشده است.')

