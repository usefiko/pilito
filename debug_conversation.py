#!/usr/bin/env python
"""
اسکریپت دیباگ برای بررسی کانورسیشن خاص
ID: Tt7bxs
"""

import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.development')
django.setup()

from message.models import Conversation, Message
from accounts.models import User
from AI_model.models import TenantKnowledge
from settings.models import AIPrompts
from AI_model.services.query_router import QueryRouter
from AI_model.services.context_retriever import ContextRetriever
from AI_model.services.embedding_service import EmbeddingService
from AI_model.services.gemini_service import GeminiChatService

def debug_conversation(conversation_id):
    """دیباگ یک کانورسیشن خاص"""
    print("="*80)
    print(f"🔍 دیباگ کانورسیشن: {conversation_id}")
    print("="*80)
    
    try:
        conversation = Conversation.objects.get(id=conversation_id)
        user = conversation.user
        
        print(f"\n👤 کاربر: {user.username} ({user.email})")
        print(f"📱 منبع: {conversation.source}")
        print(f"📊 وضعیت: {conversation.status}")
        
        # 1. بررسی Manual Chunks
        print(f"\n{'='*80}")
        print("1️⃣ بررسی Manual Chunks")
        print(f"{'='*80}")
        
        manual_chunks = TenantKnowledge.objects.filter(user=user, chunk_type='manual')
        chunk_count = manual_chunks.count()
        print(f"✅ تعداد Manual Chunks: {chunk_count}")
        
        if chunk_count > 0:
            print(f"\n📄 نمونه Chunks (اولین 5 تا):")
            for i, chunk in enumerate(manual_chunks[:5], 1):
                print(f"\n  Chunk {i}:")
                print(f"    ID: {chunk.id}")
                print(f"    Title: {chunk.section_title[:60] if chunk.section_title else 'N/A'}...")
                print(f"    Content (first 200 chars): {chunk.full_text[:200]}...")
                print(f"    Word count: {chunk.word_count}")
                print(f"    Created: {chunk.created_at}")
        else:
            print("❌ هیچ Manual Chunk پیدا نشد!")
            print("   → باید manual prompt را chunk کنید")
        
        # 2. بررسی Manual Prompt
        print(f"\n{'='*80}")
        print("2️⃣ بررسی Manual Prompt")
        print(f"{'='*80}")
        
        try:
            prompts = AIPrompts.objects.get(user=user)
            if prompts.manual_prompt:
                length = len(prompts.manual_prompt)
                print(f"✅ Manual Prompt موجود است ({length} کاراکتر)")
                
                # چک کردن کلمات کلیدی
                bio_keywords = ['بیو', 'بیوگرافی', 'مزون', 'ما', 'کی هستیم', 'چی کار', 'چه کسی', 'درباره']
                found_keywords = [kw for kw in bio_keywords if kw in prompts.manual_prompt]
                if found_keywords:
                    print(f"✅ کلمات کلیدی بیوگرافی پیدا شد: {found_keywords}")
                else:
                    print(f"⚠️ کلمات کلیدی بیوگرافی پیدا نشد!")
                
                # نمایش بخشی از manual prompt
                print(f"\n📄 Manual Prompt (اولین 500 کاراکتر):")
                print(f"   {prompts.manual_prompt[:500]}...")
            else:
                print("❌ Manual Prompt خالی است!")
        except AIPrompts.DoesNotExist:
            print("❌ AIPrompts برای این کاربر وجود ندارد!")
        
        # 3. بررسی آخرین پیام مشتری
        print(f"\n{'='*80}")
        print("3️⃣ بررسی آخرین پیام مشتری")
        print(f"{'='*80}")
        
        last_customer_msg = Message.objects.filter(
            conversation=conversation,
            type='customer'
        ).order_by('-created_at').first()
        
        if last_customer_msg:
            query = last_customer_msg.content
            print(f"📝 سوال: '{query}'")
            print(f"⏰ زمان: {last_customer_msg.created_at}")
            
            # 4. تست Routing
            print(f"\n{'='*80}")
            print("4️⃣ تست Routing")
            print(f"{'='*80}")
            
            routing = QueryRouter.route_query(query, user=user)
            print(f"Intent: {routing['intent']}")
            print(f"Confidence: {routing['confidence']:.2f}")
            print(f"Primary Source: {routing['primary_source']}")
            print(f"Secondary Sources: {routing['secondary_sources']}")
            print(f"Keywords Matched: {routing.get('keywords_matched', [])}")
            
            # 5. تست Retrieval
            print(f"\n{'='*80}")
            print("5️⃣ تست Retrieval")
            print(f"{'='*80}")
            
            try:
                embedding_service = EmbeddingService()
                query_embedding = embedding_service.get_embedding(query, task_type="retrieval_query")
                
                if not query_embedding:
                    print("❌ Query embedding failed!")
                else:
                    print("✅ Query embedding generated")
                    
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
                    
                    print(f"\n📊 نتایج Retrieval:")
                    print(f"   Primary Context: {len(retrieval_result['primary_context'])} chunks")
                    print(f"   Secondary Context: {len(retrieval_result['secondary_context'])} chunks")
                    print(f"   Total Chunks: {retrieval_result['total_chunks']}")
                    print(f"   Sources Used: {retrieval_result['sources_used']}")
                    print(f"   Method: {retrieval_result['retrieval_method']}")
                    
                    # نمایش chunks
                    if retrieval_result['primary_context']:
                        print(f"\n📄 Primary Chunks:")
                        for i, chunk in enumerate(retrieval_result['primary_context'][:3], 1):
                            print(f"\n  Chunk {i}:")
                            print(f"    Title: {chunk.get('title', 'N/A')[:60]}...")
                            print(f"    Type: {chunk.get('type', 'N/A')}")
                            print(f"    Score: {chunk.get('score', 0):.3f}")
                            print(f"    Content (first 200 chars): {chunk.get('content', '')[:200]}...")
                    
                    if retrieval_result['secondary_context']:
                        print(f"\n📄 Secondary Chunks:")
                        for i, chunk in enumerate(retrieval_result['secondary_context'][:3], 1):
                            print(f"\n  Chunk {i}:")
                            print(f"    Title: {chunk.get('title', 'N/A')[:60]}...")
                            print(f"    Type: {chunk.get('type', 'N/A')}")
                            print(f"    Score: {chunk.get('score', 0):.3f}")
                            print(f"    Content (first 200 chars): {chunk.get('content', '')[:200]}...")
                    
                    if retrieval_result['total_chunks'] == 0:
                        print("\n❌❌❌ مشکل اصلی: هیچ chunk پیدا نشد!")
                        print("   → باید بررسی کنید چرا retrieval chunks را پیدا نمی‌کند")
                    else:
                        print(f"\n✅ Chunks پیدا شدند ({retrieval_result['total_chunks']} chunk)")
                        # چک کردن آیا manual chunks در نتایج هستند
                        manual_in_results = any(
                            chunk.get('type') == 'manual' 
                            for chunk in retrieval_result['primary_context'] + retrieval_result['secondary_context']
                        )
                        if manual_in_results:
                            print("✅ Manual chunks در نتایج هستند!")
                        else:
                            print("⚠️ Manual chunks در نتایج نیستند!")
                            
            except Exception as e:
                print(f"❌ Retrieval failed: {e}")
                import traceback
                traceback.print_exc()
            
            # 6. تست ساخت Prompt
            print(f"\n{'='*80}")
            print("6️⃣ تست ساخت Prompt")
            print(f"{'='*80}")
            
            try:
                ai_service = GeminiChatService(user)
                prompt = ai_service._build_prompt(query, conversation)
                
                print(f"✅ Prompt ساخته شد ({len(prompt)} کاراکتر)")
                
                # چک کردن آیا manual chunks در prompt هستند
                manual_in_prompt = any(
                    keyword in prompt.lower() 
                    for keyword in ['manual', 'مزون', 'ما', 'بیو']
                )
                
                if manual_in_prompt:
                    print("✅ Manual content در prompt پیدا شد!")
                else:
                    print("❌ Manual content در prompt پیدا نشد!")
                
                # چک کردن Anti-Hallucination
                if "متأسفانه این اطلاعات الان در دسترس نیست" in prompt:
                    print("⚠️ عبارت 'متأسفانه این اطلاعات...' در prompt هست")
                else:
                    print("✅ عبارت 'متأسفانه این اطلاعات...' در prompt نیست")
                
                # نمایش بخشی از prompt
                print(f"\n📄 Prompt (اولین 1500 کاراکتر):")
                print(f"{prompt[:1500]}...")
                
                # نمایش بخش knowledge base
                if "KNOWLEDGE BASE" in prompt or "**" in prompt:
                    kb_start = prompt.find("KNOWLEDGE BASE") if "KNOWLEDGE BASE" in prompt else prompt.find("**")
                    if kb_start != -1:
                        kb_section = prompt[kb_start:kb_start+1000]
                        print(f"\n📚 بخش Knowledge Base در Prompt:")
                        print(f"{kb_section}...")
                
            except Exception as e:
                print(f"❌ Prompt building failed: {e}")
                import traceback
                traceback.print_exc()
        
        else:
            print("❌ هیچ پیام مشتری پیدا نشد!")
        
        # 7. بررسی آخرین پاسخ AI
        print(f"\n{'='*80}")
        print("7️⃣ بررسی آخرین پاسخ AI")
        print(f"{'='*80}")
        
        last_ai_msg = Message.objects.filter(
            conversation=conversation,
            type='AI'
        ).order_by('-created_at').first()
        
        if last_ai_msg:
            print(f"📝 پاسخ AI: '{last_ai_msg.content[:200]}...'")
            print(f"⏰ زمان: {last_ai_msg.created_at}")
            
            if "متأسفانه این اطلاعات" in last_ai_msg.content:
                print("❌ AI گفته 'متأسفانه این اطلاعات...'")
            else:
                print("✅ AI پاسخ دیگری داده")
        else:
            print("⚠️ هیچ پاسخ AI پیدا نشد")
        
        # خلاصه
        print(f"\n{'='*80}")
        print("📊 خلاصه نتایج:")
        print(f"{'='*80}")
        print(f"✅ Manual Chunks: {chunk_count}")
        if last_customer_msg:
            routing = QueryRouter.route_query(last_customer_msg.content, user=user)
            print(f"✅ Routing: {routing['intent']} → {routing['primary_source']}")
        
        print(f"\n💡 پیشنهادات:")
        if chunk_count == 0:
            print("   ❌ مشکل: Manual chunks وجود ندارند!")
            print("   → باید manual prompt را chunk کنید")
        else:
            print("   ✅ Manual chunks وجود دارند")
            # باید retrieval را چک کنیم
            if last_customer_msg:
                try:
                    embedding_service = EmbeddingService()
                    query_embedding = embedding_service.get_embedding(last_customer_msg.content, task_type="retrieval_query")
                    if query_embedding:
                        routing = QueryRouter.route_query(last_customer_msg.content, user=user)
                        retrieval_result = ContextRetriever.retrieve_context(
                            query=last_customer_msg.content,
                            user=user,
                            primary_source=routing['primary_source'],
                            secondary_sources=routing['secondary_sources'],
                            primary_budget=routing['token_budgets']['primary'],
                            secondary_budget=routing['token_budgets']['secondary'],
                            routing_info=routing
                        )
                        if retrieval_result['total_chunks'] == 0:
                            print("   ❌ مشکل: Retrieval chunks را پیدا نمی‌کند!")
                            print("   → باید بررسی کنید چرا hybrid search کار نمی‌کند")
                        else:
                            print(f"   ✅ Retrieval کار می‌کند ({retrieval_result['total_chunks']} chunks)")
                            manual_in_results = any(
                                chunk.get('type') == 'manual' 
                                for chunk in retrieval_result['primary_context'] + retrieval_result['secondary_context']
                            )
                            if not manual_in_results:
                                print("   ⚠️ مشکل: Manual chunks در نتایج retrieval نیستند!")
                                print("   → ممکن است similarity score پایین باشد")
                except:
                    pass
        
    except Conversation.DoesNotExist:
        print(f"❌ کانورسیشن با ID '{conversation_id}' پیدا نشد!")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    conversation_id = "Tt7bxs"
    debug_conversation(conversation_id)

