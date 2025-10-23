#!/usr/bin/env python
"""
Test script to debug link placeholder issue
Run directly on server: python test_link_debug.py
"""
import os
import sys
import django

# Setup Django
sys.path.insert(0, '/root/pilito/src')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.production')
django.setup()

from accounts.models.user import User
from web_knowledge.models import Product
from AI_model.models import TenantKnowledge
from settings.models import GeneralSettings, AIPrompts
from AI_model.services.gemini_service import GeminiChatService

print("=" * 80)
print("🔍 LINK DEBUG TEST")
print("=" * 80)

# Get user
try:
    user = User.objects.get(username='pilito')
    print(f"✅ User: {user.username}")
except:
    print("❌ User 'pilito' not found")
    sys.exit(1)

# 1. Check Products
print("\n" + "=" * 80)
print("📦 1. PRODUCTS - Check if links exist:")
print("=" * 80)
products = Product.objects.filter(user=user, is_active=True)[:3]
for p in products:
    print(f"\n- {p.title}")
    print(f"  Link: {p.link if p.link else '❌ NO LINK'}")
    print(f"  Price: {p.price} {p.currency}")

# 2. Check Knowledge Base
print("\n" + "=" * 80)
print("📚 2. KNOWLEDGE BASE - Check if links are stored:")
print("=" * 80)
kb_products = TenantKnowledge.objects.filter(
    user=user,
    chunk_type='product'
)[:3]
for kb in kb_products:
    print(f"\n- {kb.section_title}")
    has_link = 'Link:' in kb.full_text or 'link' in kb.metadata
    print(f"  Has 'Link:' in full_text: {'✅ YES' if 'Link:' in kb.full_text else '❌ NO'}")
    if 'Link:' in kb.full_text:
        # Extract the line with Link:
        for line in kb.full_text.split('\n'):
            if 'Link:' in line:
                print(f"  → {line.strip()}")
                break
    if 'link' in kb.metadata:
        print(f"  Metadata link: {kb.metadata.get('link', 'N/A')}")

# 3. Check Prompts
print("\n" + "=" * 80)
print("📝 3. PROMPTS - Check current settings:")
print("=" * 80)
general = GeneralSettings.get_settings()
prompts = AIPrompts.objects.filter(user=user).first()

print(f"\n🔹 Auto Prompt (first 300 chars):")
print(general.auto_prompt[:300] if general.auto_prompt else "❌ Empty")
print(f"\n  Has link instruction: {'✅ YES' if '🔗 CRITICAL' in general.auto_prompt else '❌ NO'}")

print(f"\n🔹 Manual Prompt (first 300 chars):")
if prompts and prompts.manual_prompt:
    print(prompts.manual_prompt[:300])
    # Check if manual prompt has [link] placeholder instruction
    if '[link]' in prompts.manual_prompt.lower():
        print("  ⚠️ WARNING: Manual prompt contains '[link]' - this might cause issues!")
else:
    print("❌ Empty")

# 4. Test AI Response
print("\n" + "=" * 80)
print("🤖 4. AI RESPONSE TEST:")
print("=" * 80)
print("\nGenerating AI response for: 'قیمت چنده؟'\n")

try:
    service = GeminiChatService(user=user)
    response = service.generate_response("قیمت چنده؟", conversation=None)
    
    if response.get('success'):
        ai_text = response.get('response', '')
        print(f"✅ AI Response ({len(ai_text)} chars):")
        print(f"\n{ai_text}\n")
        
        # Check for issues
        if '[link]' in ai_text.lower():
            print("❌ PROBLEM: Response contains '[link]' placeholder!")
        elif 'http' in ai_text.lower():
            print("✅ GOOD: Response contains actual URL!")
            # Extract URLs
            import re
            urls = re.findall(r'https?://[^\s]+', ai_text)
            if urls:
                print(f"   URLs found: {urls}")
        else:
            print("⚠️ WARNING: No URL found in response")
    else:
        print(f"❌ AI generation failed: {response.get('error', 'Unknown error')}")
        
except Exception as e:
    print(f"❌ Error testing AI: {e}")
    import traceback
    traceback.print_exc()

# 5. Test Context Retrieval
print("\n" + "=" * 80)
print("🔍 5. CONTEXT RETRIEVAL TEST:")
print("=" * 80)

try:
    from AI_model.services.context_retriever import ContextRetriever
    from AI_model.services.embedding_service import EmbeddingService
    
    # Get embedding for query
    emb_service = EmbeddingService()
    query_emb = emb_service.get_embedding("قیمت چنده؟")
    
    if query_emb:
        # Retrieve context
        result = ContextRetriever.retrieve_context(
            query="قیمت چنده؟",
            user=user,
            primary_source='products',
            secondary_sources=[],
            primary_budget=800,
            secondary_budget=0
        )
        
        print(f"\nRetrieved {len(result['primary_context'])} chunks from products:")
        
        for i, chunk in enumerate(result['primary_context'][:2], 1):
            print(f"\n--- Chunk {i}: {chunk.get('title', 'N/A')} ---")
            content = chunk.get('content', '')
            # Show first 200 chars
            print(content[:200])
            if 'Link:' in content:
                print("\n✅ Contains 'Link:' field")
                # Extract the link line
                for line in content.split('\n'):
                    if 'Link:' in line:
                        print(f"   {line.strip()}")
                        break
            else:
                print("\n❌ No 'Link:' field found")
    else:
        print("❌ Failed to generate embedding")
        
except Exception as e:
    print(f"❌ Error testing context retrieval: {e}")

print("\n" + "=" * 80)
print("✅ TEST COMPLETE")
print("=" * 80)

