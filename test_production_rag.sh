#!/bin/bash
# Test script for Production RAG system

set -e

echo "======================================"
echo "🧪 Testing Production RAG System"
echo "======================================"
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test 1: Check dependencies
echo "📦 Test 1: Checking dependencies..."
docker-compose exec -T web python -c "
import sys
try:
    from sentence_transformers import CrossEncoder
    print('✅ sentence-transformers installed')
    sys.exit(0)
except ImportError:
    print('❌ sentence-transformers NOT installed')
    sys.exit(1)
" && echo -e "${GREEN}✅ Dependencies OK${NC}" || echo -e "${RED}❌ Dependencies missing${NC}"

echo ""

# Test 2: Load cross-encoder model
echo "🤖 Test 2: Loading cross-encoder model..."
docker-compose exec -T web python manage.py shell <<EOF
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.production')
django.setup()

try:
    from AI_model.services.cross_encoder_reranker import CrossEncoderReranker
    
    print("🔄 Initializing reranker...")
    reranker = CrossEncoderReranker(model_name='base', device='cpu')
    
    if reranker.model:
        print("✅ Cross-encoder loaded successfully")
        
        # Test reranking
        test_chunks = [
            {'content': 'ما بورسیه تحصیلی برای دانشجویان ارائه می‌دهیم'},
            {'content': 'قیمت محصولات ما بسیار مناسب است'},
            {'content': 'بورسیه ما شامل هزینه شهریه و اسکان می‌شود'}
        ]
        
        results = reranker.rerank(
            query='بورسیه دارین؟',
            chunks=test_chunks,
            top_k=2
        )
        
        print(f"✅ Reranked {len(results)} chunks")
        for i, r in enumerate(results):
            print(f"  {i+1}. Score: {r['score']:.3f}")
    else:
        print("❌ Model not loaded")
        
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

EOF

echo ""

# Test 3: Test ProductionRAG
echo "🎯 Test 3: Testing ProductionRAG..."
docker-compose exec -T web python manage.py shell <<EOF
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.production')
django.setup()

from accounts.models import User
from AI_model.services.production_rag import ProductionRAG

try:
    # Get test user
    user = User.objects.filter(phone_number='09123456789').first()
    if not user:
        user = User.objects.first()
    
    if not user:
        print("❌ No user found for testing")
    else:
        print(f"👤 Testing with user: {user.full_name or user.phone_number}")
        
        # Test retrieval
        result = ProductionRAG.retrieve_context(
            query='بورسیه دارین؟',
            user=user,
            primary_source='manual',
            secondary_sources=['faq', 'products'],
            primary_budget=800,
            secondary_budget=600
        )
        
        print(f"✅ Retrieval complete!")
        print(f"   Method: {result.get('retrieval_method')}")
        print(f"   Primary chunks: {len(result.get('primary_context', []))}")
        print(f"   Secondary chunks: {len(result.get('secondary_context', []))}")
        print(f"   Total chunks: {result.get('total_chunks', 0)}")
        
        if result.get('performance'):
            perf = result['performance']
            print(f"   Latency: {perf.get('latency_ms', 0):.0f}ms")
            print(f"   Reranking: {perf.get('reranking_used', False)}")
            print(f"   Complexity: {perf.get('query_complexity', 0):.2f}")

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

EOF

echo ""

# Test 4: Check feature flags
echo "🚩 Test 4: Checking feature flags..."
docker-compose exec -T web python manage.py shell <<EOF
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.production')
django.setup()

from AI_model.services.feature_flags import FeatureFlags

try:
    flags = FeatureFlags.get_all_flags()
    
    print("📋 Feature Flags:")
    for name, data in flags.items():
        status = "🟢 ON" if data['enabled'] else "🔴 OFF"
        print(f"   {name}: {status} (default: {data['default']})")
    
    print("")
    print("💡 To enable ProductionRAG:")
    print("   FeatureFlags.set_flag('production_rag', True)")

except Exception as e:
    print(f"❌ Error: {e}")

EOF

echo ""

# Test 5: Compare old vs new
echo "⚖️  Test 5: Comparing ContextRetriever vs ProductionRAG..."
docker-compose exec -T web python manage.py shell <<EOF
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.production')
django.setup()

import time
from accounts.models import User
from AI_model.services.context_retriever import ContextRetriever
from AI_model.services.production_rag import ProductionRAG

try:
    user = User.objects.first()
    if not user:
        print("❌ No user found")
    else:
        query = 'بورسیه دارین؟'
        
        # Test ContextRetriever
        print("🔵 Testing ContextRetriever...")
        start = time.time()
        result_old = ContextRetriever.retrieve_context(
            query=query,
            user=user,
            primary_source='manual',
            secondary_sources=['faq'],
            primary_budget=800,
            secondary_budget=300
        )
        time_old = (time.time() - start) * 1000
        
        # Test ProductionRAG
        print("🟢 Testing ProductionRAG...")
        start = time.time()
        result_new = ProductionRAG.retrieve_context(
            query=query,
            user=user,
            primary_source='manual',
            secondary_sources=['faq'],
            primary_budget=800,
            secondary_budget=600
        )
        time_new = (time.time() - start) * 1000
        
        # Compare
        print("")
        print("📊 Comparison:")
        print(f"   ContextRetriever:")
        print(f"      Chunks: {result_old.get('total_chunks', 0)}")
        print(f"      Latency: {time_old:.0f}ms")
        print("")
        print(f"   ProductionRAG:")
        print(f"      Chunks: {result_new.get('total_chunks', 0)}")
        print(f"      Latency: {time_new:.0f}ms")
        print("")
        
        improvement = result_new.get('total_chunks', 0) - result_old.get('total_chunks', 0)
        if improvement > 0:
            print(f"   ✅ ProductionRAG retrieved {improvement} more chunks")
        elif improvement < 0:
            print(f"   ⚠️  ProductionRAG retrieved {abs(improvement)} fewer chunks")
        else:
            print(f"   ➡️  Same number of chunks")

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

EOF

echo ""
echo "======================================"
echo "✅ Testing Complete!"
echo "======================================"
echo ""
echo "📝 Next steps:"
echo "   1. Review test results above"
echo "   2. Enable feature flag if tests pass:"
echo "      docker-compose exec web python manage.py shell"
echo "      >>> from AI_model.services.feature_flags import FeatureFlags"
echo "      >>> FeatureFlags.set_flag('production_rag', True)"
echo "   3. Monitor logs for RAG performance"
echo "   4. Gradually roll out to users"
echo ""

