#!/usr/bin/env python
"""
Test script for RAG Status API
Tests the /api/v1/ai/rag/status/ endpoint
"""

import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework.authtoken.models import Token
from AI_model.models import TenantKnowledge, PGVECTOR_AVAILABLE, SessionMemory, IntentKeyword, IntentRouting

User = get_user_model()

def test_rag_status_api():
    """Test RAG status API endpoint"""
    
    print("=" * 60)
    print("Testing RAG Status API")
    print("=" * 60)
    
    # 1. Get or create test user
    print("\n1. Setting up test user...")
    user = User.objects.filter(is_active=True).first()
    if not user:
        print("❌ No active users found. Please create a user first.")
        return
    
    print(f"✅ Using user: {user.username}")
    
    # 2. Create or get auth token
    print("\n2. Getting auth token...")
    token, created = Token.objects.get_or_create(user=user)
    print(f"✅ Token: {token.key[:20]}...")
    
    # 3. Initialize API client
    print("\n3. Initializing API client...")
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {token.key}')
    print("✅ API client ready")
    
    # 4. Call RAG status API
    print("\n4. Calling RAG status API...")
    response = client.get('/api/v1/ai/rag/status/')
    
    print(f"   Status Code: {response.status_code}")
    
    if response.status_code == 200:
        print("✅ API call successful")
        
        data = response.json()
        
        # 5. Display results
        print("\n" + "=" * 60)
        print("RAG STATUS RESULTS")
        print("=" * 60)
        
        print(f"\n📊 System Status:")
        print(f"   RAG Enabled: {data['rag_enabled']}")
        print(f"   pgvector Available: {data['pgvector_available']}")
        print(f"   Embedding Service: {data['embedding_service_available']}")
        print(f"   Health Status: {data['health_status'].upper()}")
        
        print(f"\n📚 Knowledge Base:")
        kb = data['knowledge_base']
        print(f"   Total Chunks: {kb['total']}")
        print(f"   FAQ: {kb['faq']['count']}")
        print(f"   Manual: {kb['manual']['count']}")
        print(f"   Products: {kb['product']['count']}")
        print(f"   Website: {kb['website']['count']}")
        
        print(f"\n🔢 Embedding Statistics:")
        emb = data['embedding_stats']
        print(f"   Total Chunks: {emb['total_chunks']}")
        print(f"   With TL;DR Embeddings: {emb['chunks_with_tldr_embedding']}")
        print(f"   With Full Embeddings: {emb['chunks_with_full_embedding']}")
        print(f"   Without Embeddings: {emb['chunks_without_embedding']}")
        print(f"   Coverage: {emb['embedding_coverage']}%")
        
        print(f"\n🎯 Intent Routing:")
        intent = data['intent_routing']
        print(f"   Keywords Configured: {intent['keywords_configured']}")
        print(f"   Routing Rules: {intent['routing_rules_configured']}")
        print(f"   Has Custom Keywords: {intent['has_custom_keywords']}")
        
        print(f"\n🧠 Session Memory:")
        memory = data['session_memory']
        print(f"   Total Conversations: {memory['total_conversations']}")
        print(f"   With Memory: {memory['conversations_with_memory']}")
        print(f"   Coverage: {memory['memory_coverage']}%")
        
        print(f"\n📅 Last Updated:")
        print(f"   {data['last_updated'] or 'Never'}")
        
        if data['issues']:
            print(f"\n⚠️  Issues Detected ({len(data['issues'])}):")
            for i, issue in enumerate(data['issues'], 1):
                print(f"   {i}. {issue}")
        else:
            print(f"\n✅ No issues detected")
        
        # 6. Validation checks
        print("\n" + "=" * 60)
        print("VALIDATION CHECKS")
        print("=" * 60)
        
        checks = []
        
        # Check pgvector
        actual_pgvector = PGVECTOR_AVAILABLE
        if actual_pgvector == data['pgvector_available']:
            checks.append(("pgvector status", "✅ PASS"))
        else:
            checks.append(("pgvector status", f"❌ FAIL (actual: {actual_pgvector}, API: {data['pgvector_available']})"))
        
        # Check total chunks
        actual_chunks = TenantKnowledge.objects.filter(user=user).count()
        if actual_chunks == data['knowledge_base']['total']:
            checks.append(("total chunks count", "✅ PASS"))
        else:
            checks.append(("total chunks count", f"❌ FAIL (actual: {actual_chunks}, API: {data['knowledge_base']['total']})"))
        
        # Check chunk breakdown
        for chunk_type, display_name in TenantKnowledge.CHUNK_TYPE_CHOICES:
            actual_count = TenantKnowledge.objects.filter(user=user, chunk_type=chunk_type).count()
            api_count = data['knowledge_base'][chunk_type]['count']
            if actual_count == api_count:
                checks.append((f"{chunk_type} chunks", "✅ PASS"))
            else:
                checks.append((f"{chunk_type} chunks", f"❌ FAIL (actual: {actual_count}, API: {api_count})"))
        
        # Check embeddings
        actual_with_emb = TenantKnowledge.objects.filter(user=user, tldr_embedding__isnull=False).count()
        if actual_with_emb == data['embedding_stats']['chunks_with_tldr_embedding']:
            checks.append(("chunks with embeddings", "✅ PASS"))
        else:
            checks.append(("chunks with embeddings", f"❌ FAIL (actual: {actual_with_emb}, API: {data['embedding_stats']['chunks_with_tldr_embedding']})"))
        
        # Check session memory
        actual_memory = SessionMemory.objects.filter(user=user).count()
        if actual_memory == data['session_memory']['conversations_with_memory']:
            checks.append(("session memories", "✅ PASS"))
        else:
            checks.append(("session memories", f"❌ FAIL (actual: {actual_memory}, API: {data['session_memory']['conversations_with_memory']})"))
        
        # Check intent keywords
        actual_keywords = IntentKeyword.objects.filter(
            models.Q(user=user) | models.Q(user__isnull=True),
            is_active=True
        ).count()
        from django.db import models
        if actual_keywords == data['intent_routing']['keywords_configured']:
            checks.append(("intent keywords", "✅ PASS"))
        else:
            checks.append(("intent keywords", f"❌ FAIL (actual: {actual_keywords}, API: {data['intent_routing']['keywords_configured']})"))
        
        # Print validation results
        print()
        for check_name, result in checks:
            print(f"   {check_name:.<40} {result}")
        
        # Summary
        passed = sum(1 for _, r in checks if r.startswith("✅"))
        total = len(checks)
        print(f"\n   Summary: {passed}/{total} checks passed")
        
        if passed == total:
            print("\n🎉 All validation checks passed!")
        else:
            print(f"\n⚠️  {total - passed} validation check(s) failed")
        
    else:
        print(f"❌ API call failed with status {response.status_code}")
        print(f"   Response: {response.json()}")
    
    print("\n" + "=" * 60)
    print("Test Complete")
    print("=" * 60)

if __name__ == "__main__":
    try:
        test_rag_status_api()
    except Exception as e:
        print(f"\n❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

