#!/bin/bash
# Test Query Answering with RAG

echo "🤖 Testing Query Answering (RAG)"
echo "================================"
echo ""

# Test query
QUERY="بورسیه دارین؟"

echo "📝 Test Query: '$QUERY'"
echo ""
echo "🔍 Testing RAG retrieval..."
echo ""

docker-compose exec -T web python manage.py shell <<PYTHON
from AI_model.services.query_router import QueryRouter
from AI_model.services.hybrid_retriever import HybridRetriever
from AI_model.services.embedding_service import EmbeddingService
from AI_model.models import TenantKnowledge
from django.contrib.auth import get_user_model

User = get_user_model()
user = User.objects.get(username='Faracoach')

query = "$QUERY"

print("=" * 60)
print("🎯 STEP 1: Intent Classification")
print("=" * 60)

# Route query
routing = QueryRouter.route_query(query, user=user)

print(f"Query: {query}")
print(f"Intent: {routing['intent']}")
print(f"Confidence: {routing['confidence']:.2%}")
print(f"Primary source: {routing['primary_source']}")
print(f"Secondary sources: {routing['secondary_sources']}")
print(f"Keywords matched: {routing.get('keywords_matched', [])}")

print("\n" + "=" * 60)
print("🔍 STEP 2: Embedding Generation")
print("=" * 60)

# Generate embedding
embedding_service = EmbeddingService()
query_embedding = embedding_service.get_embedding(query)

if query_embedding:
    print(f"✅ Query embedding generated: {len(query_embedding)} dimensions")
else:
    print(f"❌ Failed to generate embedding")

print("\n" + "=" * 60)
print("📚 STEP 3: Hybrid Search (BM25 + Vector)")
print("=" * 60)

# Check available chunks
total_chunks = TenantKnowledge.objects.filter(user=user).count()
manual_chunks = TenantKnowledge.objects.filter(user=user, chunk_type='manual').count()

print(f"Available chunks: {total_chunks} (manual: {manual_chunks})")

if total_chunks == 0:
    print("\n⚠️  No chunks found! You need to:")
    print("   1. Save manual prompt in Django Admin")
    print("   2. Wait for chunking to complete")
    print("   3. Run this test again")
else:
    # Perform hybrid search
    chunks = HybridRetriever.hybrid_search(
        query=query,
        user=user,
        chunk_type='manual',
        query_embedding=query_embedding,
        top_k=5,
        token_budget=800
    )
    
    print(f"\nRetrieved chunks: {len(chunks)}")
    
    if chunks:
        print("\n🎯 Top 3 Results:")
        for i, chunk_data in enumerate(chunks[:3], 1):
            chunk = chunk_data['chunk']
            score = chunk_data.get('score', 0)
            
            print(f"\n{i}. Score: {score:.3f}")
            print(f"   Title: {chunk.section_title}")
            print(f"   Words: {chunk.word_count}")
            print(f"   TL;DR: {chunk.tldr[:100]}...")
            print(f"   Preview: {chunk.full_text[:150]}...")
    else:
        print("\n⚠️  No relevant chunks found!")
        print("   This might mean:")
        print("   1. Manual prompt doesn't contain relevant content")
        print("   2. Embeddings not properly generated")
        print("   3. Search threshold too strict")

print("\n" + "=" * 60)
print("💡 STEP 4: Answer Generation")
print("=" * 60)

if total_chunks > 0 and chunks:
    print("\n✅ RAG is working! You can now test in the UI:")
    print(f"   1. Go to chat interface")
    print(f"   2. Ask: '{query}'")
    print(f"   3. AI should use the retrieved chunks to answer")
    print(f"\n   Expected: AI should mention 'بورسیه' details from manual prompt")
else:
    print("\n⚠️  Cannot test answer generation - no chunks retrieved")

print("\n" + "=" * 60)
print("📊 Summary")
print("=" * 60)
print(f"✓ Intent classification: {'✅' if routing['intent'] else '❌'}")
print(f"✓ Embedding generation: {'✅' if query_embedding else '❌'}")
print(f"✓ Chunks available: {'✅' if total_chunks > 0 else '❌'} ({total_chunks})")
print(f"✓ Chunks retrieved: {'✅' if chunks else '❌'} ({len(chunks) if chunks else 0})")
print("\n")

PYTHON

echo "================================"
echo "✅ Test complete!"
echo ""

