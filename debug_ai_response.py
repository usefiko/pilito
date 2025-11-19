#!/usr/bin/env python
"""
اسکریپت دیباگ برای بررسی مشکل پاسخ AI
بررسی می‌کند:
1. آیا manual chunks وجود دارند؟
2. آیا routing درست کار می‌کند؟
3. آیا retrieval chunks را پیدا می‌کند؟
4. آیا Anti-Hallucination rules خیلی سخت‌گیرانه هستند؟
"""

import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.development')
django.setup()

from accounts.models import User
from AI_model.models import TenantKnowledge
from settings.models import AIPrompts, GeneralSettings
from AI_model.services.query_router import QueryRouter
from AI_model.services.context_retriever import ContextRetriever
from AI_model.services.embedding_service import EmbeddingService
from AI_model.services.token_budget_controller import TokenBudgetController

def check_manual_chunks(user):
    """بررسی manual chunks"""
    print(f"\n{'='*80}")
    print(f"📚 بررسی Manual Chunks برای {user.username}")
    print(f"{'='*80}")
    
    chunks = TenantKnowledge.objects.filter(user=user, chunk_type='manual')
    count = chunks.count()
    print(f"✅ تعداد Manual Chunks: {count}")
    
    if count > 0:
        print(f"\n📄 نمونه Chunks (اولین 3 تا):")
        for i, chunk in enumerate(chunks[:3], 1):
            print(f"\n  Chunk {i}:")
            print(f"    Title: {chunk.section_title[:50] if chunk.section_title else 'N/A'}...")
            print(f"    Content (first 100 chars): {chunk.full_text[:100]}...")
            print(f"    Word count: {chunk.word_count}")
    else:
        print("❌ هیچ Manual Chunk پیدا نشد!")
        print("   → باید manual prompt را chunk کنید")
    
    return count

def check_manual_prompt(user):
    """بررسی manual prompt"""
    print(f"\n{'='*80}")
    print(f"📝 بررسی Manual Prompt برای {user.username}")
    print(f"{'='*80}")
    
    try:
        prompts = AIPrompts.objects.get(user=user)
        if prompts.manual_prompt:
            length = len(prompts.manual_prompt)
            print(f"✅ Manual Prompt موجود است ({length} کاراکتر)")
            print(f"\n📄 محتوای اول (200 کاراکتر اول):")
            print(f"   {prompts.manual_prompt[:200]}...")
            
            # چک کردن آیا بیوگرافی در manual prompt هست
            bio_keywords = ['بیو', 'بیوگرافی', 'مزون', 'ما', 'کی هستیم', 'چی کار', 'چه کسی']
            found_keywords = [kw for kw in bio_keywords if kw in prompts.manual_prompt]
            if found_keywords:
                print(f"\n✅ کلمات کلیدی بیوگرافی پیدا شد: {found_keywords}")
            else:
                print(f"\n⚠️ کلمات کلیدی بیوگرافی پیدا نشد!")
        else:
            print("❌ Manual Prompt خالی است!")
    except AIPrompts.DoesNotExist:
        print("❌ AIPrompts برای این کاربر وجود ندارد!")

def test_routing(query, user):
    """تست routing"""
    print(f"\n{'='*80}")
    print(f"🎯 تست Routing برای سوال: '{query}'")
    print(f"{'='*80}")
    
    routing = QueryRouter.route_query(query, user=user)
    print(f"Intent: {routing['intent']}")
    print(f"Confidence: {routing['confidence']:.2f}")
    print(f"Primary Source: {routing['primary_source']}")
    print(f"Secondary Sources: {routing['secondary_sources']}")
    print(f"Keywords Matched: {routing.get('keywords_matched', [])}")
    
    return routing

def test_retrieval(query, user, routing):
    """تست retrieval"""
    print(f"\n{'='*80}")
    print(f"🔍 تست Retrieval برای سوال: '{query}'")
    print(f"{'='*80}")
    
    try:
        # Generate embedding
        embedding_service = EmbeddingService()
        query_embedding = embedding_service.get_embedding(query, task_type="retrieval_query")
        
        if not query_embedding:
            print("❌ Query embedding failed!")
            return []
        
        # Retrieve context
        retrieval_result = ContextRetriever.retrieve_context(
            query=query,
            user=user,
            primary_source=routing['primary_source'],
            secondary_sources=routing['secondary_sources'],
            primary_budget=routing['token_budgets']['primary'],
            secondary_budget=routing['token_budgets']['secondary'],
            routing_info=routing
        )
        
        print(f"✅ Primary Context: {len(retrieval_result['primary_context'])} chunks")
        print(f"✅ Secondary Context: {len(retrieval_result['secondary_context'])} chunks")
        print(f"✅ Total Chunks: {retrieval_result['total_chunks']}")
        
        # Show chunks
        if retrieval_result['primary_context']:
            print(f"\n📄 Primary Chunks:")
            for i, chunk in enumerate(retrieval_result['primary_context'][:3], 1):
                print(f"\n  Chunk {i}:")
                print(f"    Title: {chunk.get('title', 'N/A')[:50]}...")
                print(f"    Content (first 150 chars): {chunk.get('content', '')[:150]}...")
                print(f"    Score: {chunk.get('score', 0):.3f}")
                print(f"    Type: {chunk.get('type', 'N/A')}")
        
        if retrieval_result['secondary_context']:
            print(f"\n📄 Secondary Chunks:")
            for i, chunk in enumerate(retrieval_result['secondary_context'][:2], 1):
                print(f"\n  Chunk {i}:")
                print(f"    Title: {chunk.get('title', 'N/A')[:50]}...")
                print(f"    Content (first 150 chars): {chunk.get('content', '')[:150]}...")
                print(f"    Score: {chunk.get('score', 0):.3f}")
                print(f"    Type: {chunk.get('type', 'N/A')}")
        
        if retrieval_result['total_chunks'] == 0:
            print("\n❌ هیچ chunk پیدا نشد! این مشکل اصلی است!")
        
        return retrieval_result
        
    except Exception as e:
        print(f"❌ Retrieval failed: {e}")
        import traceback
        traceback.print_exc()
        return None

def check_anti_hallucination_rules():
    """بررسی Anti-Hallucination rules"""
    print(f"\n{'='*80}")
    print(f"🚨 بررسی Anti-Hallucination Rules")
    print(f"{'='*80}")
    
    settings = GeneralSettings.get_settings()
    rules = settings.anti_hallucination_rules
    
    print(f"📄 قوانین ({len(rules)} کاراکتر):")
    print(f"\n{rules[:500]}...")
    
    # چک کردن آیا خیلی سخت‌گیرانه است
    strict_phrases = [
        "NEVER",
        "متأسفانه این اطلاعات الان در دسترس نیست",
        "MUST SAY",
        "ALWAYS say"
    ]
    
    found_strict = [phrase for phrase in strict_phrases if phrase in rules]
    print(f"\n⚠️ عبارات سخت‌گیرانه پیدا شده: {found_strict}")
    
    # چک کردن knowledge_limitation_response
    limitation_response = settings.knowledge_limitation_response
    print(f"\n📢 Knowledge Limitation Response:")
    print(f"   {limitation_response}")

def test_full_prompt_building(query, user):
    """تست ساخت کامل prompt"""
    print(f"\n{'='*80}")
    print(f"🔨 تست ساخت Prompt برای سوال: '{query}'")
    print(f"{'='*80}")
    
    try:
        from AI_model.services.gemini_service import GeminiChatService
        from message.models import Conversation
        
        # Get or create a test conversation
        conversation = Conversation.objects.filter(user=user, is_active=True).first()
        if not conversation:
            print("⚠️ هیچ conversation فعالی پیدا نشد - از None استفاده می‌کنیم")
            conversation = None
        
        # Initialize AI service
        ai_service = GeminiChatService(user)
        
        # Build prompt
        prompt = ai_service._build_prompt(query, conversation)
        
        print(f"✅ Prompt ساخته شد ({len(prompt)} کاراکتر)")
        print(f"\n📄 Prompt (اولین 1000 کاراکتر):")
        print(f"{prompt[:1000]}...")
        
        # Check if manual chunks are in prompt
        if "manual" in prompt.lower() or "مزون" in prompt or "ما" in prompt:
            print("\n✅ Manual content در prompt پیدا شد!")
        else:
            print("\n❌ Manual content در prompt پیدا نشد!")
        
        # Check Anti-Hallucination rules
        if "متأسفانه این اطلاعات الان در دسترس نیست" in prompt:
            print("\n⚠️ عبارت 'متأسفانه این اطلاعات...' در prompt هست")
        else:
            print("\n✅ عبارت 'متأسفانه این اطلاعات...' در prompt نیست")
        
        return prompt
        
    except Exception as e:
        print(f"❌ Prompt building failed: {e}")
        import traceback
        traceback.print_exc()
        return None

def main():
    """تابع اصلی"""
    print("="*80)
    print("🔍 دیباگ پاسخ AI - بررسی مشکل 'متأسفانه این اطلاعات...'")
    print("="*80)
    
    # Get first active user
    try:
        user = User.objects.filter(is_active=True).first()
        if not user:
            print("❌ هیچ کاربر فعالی پیدا نشد!")
            return
        
        print(f"\n👤 کاربر انتخاب شده: {user.username} ({user.email})")
        
        # 1. Check manual chunks
        chunk_count = check_manual_chunks(user)
        
        # 2. Check manual prompt
        check_manual_prompt(user)
        
        # 3. Check Anti-Hallucination rules
        check_anti_hallucination_rules()
        
        # 4. Test with a real query
        test_query = "یک بیوگرافی از مزونتون میدی بهم کامل"
        print(f"\n{'='*80}")
        print(f"🧪 تست با سوال واقعی: '{test_query}'")
        print(f"{'='*80}")
        
        # Test routing
        routing = test_routing(test_query, user)
        
        # Test retrieval
        retrieval_result = test_retrieval(test_query, user, routing)
        
        # Test full prompt building
        prompt = test_full_prompt_building(test_query, user)
        
        # Summary
        print(f"\n{'='*80}")
        print("📊 خلاصه نتایج:")
        print(f"{'='*80}")
        print(f"✅ Manual Chunks: {chunk_count}")
        print(f"✅ Routing Intent: {routing['intent']} → {routing['primary_source']}")
        if retrieval_result:
            print(f"✅ Retrieved Chunks: {retrieval_result['total_chunks']}")
            if retrieval_result['total_chunks'] == 0:
                print("❌ مشکل: هیچ chunk پیدا نشد - این دلیل اصلی است!")
            else:
                print("✅ Chunks پیدا شدند - مشکل در Anti-Hallucination rules است")
        else:
            print("❌ Retrieval failed!")
        
        print(f"\n💡 پیشنهادات:")
        if chunk_count == 0:
            print("   1. Manual prompt را chunk کنید: python manage.py chunk_manual_prompt")
        if retrieval_result and retrieval_result['total_chunks'] == 0:
            print("   2. بررسی کنید چرا retrieval chunks را پیدا نمی‌کند")
            print("   3. ممکن است query embedding مشکل داشته باشد")
        if retrieval_result and retrieval_result['total_chunks'] > 0:
            print("   1. Chunks پیدا شدند - مشکل در Anti-Hallucination rules است")
            print("   2. قوانین را نرم‌تر کنید یا شرط 'اگر chunk داریم' اضافه کنید")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
