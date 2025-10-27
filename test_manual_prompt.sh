#!/bin/bash
# Test Manual Prompt Chunking for Faracoach

echo "📝 Testing Manual Prompt Chunking"
echo "=================================="
echo ""
echo "⏳ Waiting for chunking to complete (after you save manual prompt)..."
echo ""
echo "Run this script AFTER you've saved the manual prompt in Django Admin"
echo ""

# Wait for user
read -p "Press ENTER when you've saved the manual prompt in Django Admin..."

echo ""
echo "🔍 Checking chunks..."

docker-compose exec -T web python manage.py shell <<'PYTHON'
from AI_model.models import TenantKnowledge
from django.contrib.auth import get_user_model
import time

User = get_user_model()
user = User.objects.get(username='Faracoach')

print("\n⏳ Waiting for chunking to complete (max 60 seconds)...")
print("   Checking every 5 seconds...\n")

for i in range(12):  # 12 × 5 = 60 seconds
    manual_chunks = TenantKnowledge.objects.filter(user=user, chunk_type='manual')
    count = manual_chunks.count()
    
    if count > 0:
        print(f"\n✅ Found {count} manual chunks!")
        
        # Show details
        first_chunk = manual_chunks.first()
        last_chunk = manual_chunks.last()
        
        print(f"\n📊 Chunk Statistics:")
        print(f"   Total chunks: {count}")
        print(f"   Total words: {sum(c.word_count for c in manual_chunks)}")
        print(f"   Avg words per chunk: {sum(c.word_count for c in manual_chunks) // count}")
        
        print(f"\n📝 First Chunk:")
        print(f"   Title: {first_chunk.section_title}")
        print(f"   Words: {first_chunk.word_count}")
        print(f"   TL;DR: {first_chunk.tldr[:100]}...")
        print(f"   Full text preview: {first_chunk.full_text[:150]}...")
        
        # Check embeddings
        has_tldr_emb = first_chunk.tldr_embedding is not None
        has_full_emb = first_chunk.full_embedding is not None
        
        print(f"\n🔢 Embeddings:")
        print(f"   TL;DR embedding: {'✅ Yes' if has_tldr_emb else '❌ No'}")
        print(f"   Full embedding: {'✅ Yes' if has_full_emb else '❌ No'}")
        
        if has_full_emb:
            # Check dimensions
            import numpy as np
            emb_array = np.array(first_chunk.full_embedding)
            print(f"   Dimensions: {len(emb_array)} (should be 1536 for OpenAI)")
        
        print(f"\n🎉 Manual prompt chunking successful!")
        break
    
    if i < 11:
        print(f"   Attempt {i+1}/12: No chunks yet, waiting 5 seconds...")
        time.sleep(5)
    else:
        print(f"\n⚠️  No manual chunks found after 60 seconds!")
        print(f"   Possible issues:")
        print(f"   1. Manual prompt not saved yet")
        print(f"   2. Celery worker not running")
        print(f"   3. Signal not triggered")
        print(f"\n   Check celery logs: docker logs celery_worker --tail 100")

PYTHON

echo ""
echo "=================================="
echo "✅ Test complete!"
echo ""

