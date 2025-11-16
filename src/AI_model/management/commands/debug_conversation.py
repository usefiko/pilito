"""
Management command برای دیباگ کانورسیشن خاص
Usage: python manage.py debug_conversation Tt7bxs
"""

from django.core.management.base import BaseCommand
from message.models import Conversation, Message
from accounts.models import User
from AI_model.models import TenantKnowledge
from settings.models import AIPrompts
from AI_model.services.query_router import QueryRouter
from AI_model.services.context_retriever import ContextRetriever
from AI_model.services.embedding_service import EmbeddingService
from AI_model.services.gemini_service import GeminiChatService


class Command(BaseCommand):
    help = 'Debug a specific conversation to see why AI responds incorrectly'

    def add_arguments(self, parser):
        parser.add_argument('conversation_id', type=str, help='Conversation ID to debug')

    def handle(self, *args, **options):
        conversation_id = options['conversation_id']
        
        self.stdout.write("="*80)
        self.stdout.write(self.style.SUCCESS(f"🔍 دیباگ کانورسیشن: {conversation_id}"))
        self.stdout.write("="*80)
        
        try:
            conversation = Conversation.objects.get(id=conversation_id)
            user = conversation.user
            
            self.stdout.write(f"\n👤 کاربر: {user.username} ({user.email})")
            self.stdout.write(f"📱 منبع: {conversation.source}")
            self.stdout.write(f"📊 وضعیت: {conversation.status}")
            
            # 1. بررسی Manual Chunks
            self.stdout.write(f"\n{'='*80}")
            self.stdout.write("1️⃣ بررسی Manual Chunks")
            self.stdout.write(f"{'='*80}")
            
            manual_chunks = TenantKnowledge.objects.filter(user=user, chunk_type='manual')
            chunk_count = manual_chunks.count()
            self.stdout.write(self.style.SUCCESS(f"✅ تعداد Manual Chunks: {chunk_count}"))
            
            if chunk_count > 0:
                self.stdout.write(f"\n📄 نمونه Chunks (اولین 5 تا):")
                for i, chunk in enumerate(manual_chunks[:5], 1):
                    self.stdout.write(f"\n  Chunk {i}:")
                    self.stdout.write(f"    ID: {chunk.id}")
                    self.stdout.write(f"    Title: {chunk.section_title[:60] if chunk.section_title else 'N/A'}...")
                    self.stdout.write(f"    Content (first 200 chars): {chunk.full_text[:200]}...")
                    self.stdout.write(f"    Word count: {chunk.word_count}")
            else:
                self.stdout.write(self.style.ERROR("❌ هیچ Manual Chunk پیدا نشد!"))
                self.stdout.write("   → باید manual prompt را chunk کنید")
            
            # 2. بررسی Manual Prompt
            self.stdout.write(f"\n{'='*80}")
            self.stdout.write("2️⃣ بررسی Manual Prompt")
            self.stdout.write(f"{'='*80}")
            
            try:
                prompts = AIPrompts.objects.get(user=user)
                if prompts.manual_prompt:
                    length = len(prompts.manual_prompt)
                    self.stdout.write(self.style.SUCCESS(f"✅ Manual Prompt موجود است ({length} کاراکتر)"))
                    
                    # چک کردن کلمات کلیدی
                    bio_keywords = ['بیو', 'بیوگرافی', 'مزون', 'ما', 'کی هستیم', 'چی کار', 'چه کسی', 'درباره']
                    found_keywords = [kw for kw in bio_keywords if kw in prompts.manual_prompt]
                    if found_keywords:
                        self.stdout.write(self.style.SUCCESS(f"✅ کلمات کلیدی بیوگرافی پیدا شد: {found_keywords}"))
                    else:
                        self.stdout.write(self.style.WARNING(f"⚠️ کلمات کلیدی بیوگرافی پیدا نشد!"))
                    
                    # نمایش بخشی از manual prompt
                    self.stdout.write(f"\n📄 Manual Prompt (اولین 500 کاراکتر):")
                    self.stdout.write(f"   {prompts.manual_prompt[:500]}...")
                else:
                    self.stdout.write(self.style.ERROR("❌ Manual Prompt خالی است!"))
            except AIPrompts.DoesNotExist:
                self.stdout.write(self.style.ERROR("❌ AIPrompts برای این کاربر وجود ندارد!"))
            
            # 3. بررسی آخرین پیام مشتری
            self.stdout.write(f"\n{'='*80}")
            self.stdout.write("3️⃣ بررسی آخرین پیام مشتری")
            self.stdout.write(f"{'='*80}")
            
            last_customer_msg = Message.objects.filter(
                conversation=conversation,
                type='customer'
            ).order_by('-created_at').first()
            
            if not last_customer_msg:
                self.stdout.write(self.style.ERROR("❌ هیچ پیام مشتری پیدا نشد!"))
                return
            
            query = last_customer_msg.content
            self.stdout.write(f"📝 سوال: '{query}'")
            self.stdout.write(f"⏰ زمان: {last_customer_msg.created_at}")
            
            # 4. تست Routing
            self.stdout.write(f"\n{'='*80}")
            self.stdout.write("4️⃣ تست Routing")
            self.stdout.write(f"{'='*80}")
            
            routing = QueryRouter.route_query(query, user=user)
            self.stdout.write(f"Intent: {routing['intent']}")
            self.stdout.write(f"Confidence: {routing['confidence']:.2f}")
            self.stdout.write(f"Primary Source: {routing['primary_source']}")
            self.stdout.write(f"Secondary Sources: {routing['secondary_sources']}")
            self.stdout.write(f"Keywords Matched: {routing.get('keywords_matched', [])}")
            
            # 5. تست Retrieval
            self.stdout.write(f"\n{'='*80}")
            self.stdout.write("5️⃣ تست Retrieval")
            self.stdout.write(f"{'='*80}")
            
            try:
                embedding_service = EmbeddingService()
                query_embedding = embedding_service.get_embedding(query, task_type="retrieval_query")
                
                if not query_embedding:
                    self.stdout.write(self.style.ERROR("❌ Query embedding failed!"))
                else:
                    self.stdout.write(self.style.SUCCESS("✅ Query embedding generated"))
                    
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
                    
                    self.stdout.write(f"\n📊 نتایج Retrieval:")
                    self.stdout.write(f"   Primary Context: {len(retrieval_result['primary_context'])} chunks")
                    self.stdout.write(f"   Secondary Context: {len(retrieval_result['secondary_context'])} chunks")
                    self.stdout.write(f"   Total Chunks: {retrieval_result['total_chunks']}")
                    self.stdout.write(f"   Sources Used: {retrieval_result['sources_used']}")
                    self.stdout.write(f"   Method: {retrieval_result['retrieval_method']}")
                    
                    # نمایش chunks
                    if retrieval_result['primary_context']:
                        self.stdout.write(f"\n📄 Primary Chunks:")
                        for i, chunk in enumerate(retrieval_result['primary_context'][:3], 1):
                            self.stdout.write(f"\n  Chunk {i}:")
                            self.stdout.write(f"    Title: {chunk.get('title', 'N/A')[:60]}...")
                            self.stdout.write(f"    Type: {chunk.get('type', 'N/A')}")
                            self.stdout.write(f"    Score: {chunk.get('score', 0):.3f}")
                            self.stdout.write(f"    Content (first 200 chars): {chunk.get('content', '')[:200]}...")
                    
                    if retrieval_result['secondary_context']:
                        self.stdout.write(f"\n📄 Secondary Chunks:")
                        for i, chunk in enumerate(retrieval_result['secondary_context'][:3], 1):
                            self.stdout.write(f"\n  Chunk {i}:")
                            self.stdout.write(f"    Title: {chunk.get('title', 'N/A')[:60]}...")
                            self.stdout.write(f"    Type: {chunk.get('type', 'N/A')}")
                            self.stdout.write(f"    Score: {chunk.get('score', 0):.3f}")
                            self.stdout.write(f"    Content (first 200 chars): {chunk.get('content', '')[:200]}...")
                    
                    if retrieval_result['total_chunks'] == 0:
                        self.stdout.write(self.style.ERROR("\n❌❌❌ مشکل اصلی: هیچ chunk پیدا نشد!"))
                        self.stdout.write("   → باید بررسی کنید چرا retrieval chunks را پیدا نمی‌کند")
                    else:
                        self.stdout.write(self.style.SUCCESS(f"\n✅ Chunks پیدا شدند ({retrieval_result['total_chunks']} chunk)"))
                        # چک کردن آیا manual chunks در نتایج هستند
                        manual_in_results = any(
                            chunk.get('type') == 'manual' 
                            for chunk in retrieval_result['primary_context'] + retrieval_result['secondary_context']
                        )
                        if manual_in_results:
                            self.stdout.write(self.style.SUCCESS("✅ Manual chunks در نتایج هستند!"))
                        else:
                            self.stdout.write(self.style.WARNING("⚠️ Manual chunks در نتایج نیستند!"))
                            
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"❌ Retrieval failed: {e}"))
                import traceback
                self.stdout.write(traceback.format_exc())
            
            # 6. تست ساخت Prompt
            self.stdout.write(f"\n{'='*80}")
            self.stdout.write("6️⃣ تست ساخت Prompt")
            self.stdout.write(f"{'='*80}")
            
            try:
                ai_service = GeminiChatService(user)
                prompt = ai_service._build_prompt(query, conversation)
                
                self.stdout.write(self.style.SUCCESS(f"✅ Prompt ساخته شد ({len(prompt)} کاراکتر)"))
                
                # چک کردن آیا manual chunks در prompt هستند
                manual_in_prompt = any(
                    keyword in prompt.lower() 
                    for keyword in ['manual', 'مزون', 'ما', 'بیو']
                )
                
                if manual_in_prompt:
                    self.stdout.write(self.style.SUCCESS("✅ Manual content در prompt پیدا شد!"))
                else:
                    self.stdout.write(self.style.ERROR("❌ Manual content در prompt پیدا نشد!"))
                
                # چک کردن Anti-Hallucination
                if "متأسفانه این اطلاعات الان در دسترس نیست" in prompt:
                    self.stdout.write(self.style.WARNING("⚠️ عبارت 'متأسفانه این اطلاعات...' در prompt هست"))
                else:
                    self.stdout.write(self.style.SUCCESS("✅ عبارت 'متأسفانه این اطلاعات...' در prompt نیست"))
                
                # نمایش بخشی از prompt
                self.stdout.write(f"\n📄 Prompt (اولین 1500 کاراکتر):")
                self.stdout.write(f"{prompt[:1500]}...")
                
                # نمایش بخش knowledge base
                if "KNOWLEDGE BASE" in prompt or "**" in prompt:
                    kb_start = prompt.find("KNOWLEDGE BASE") if "KNOWLEDGE BASE" in prompt else prompt.find("**")
                    if kb_start != -1:
                        kb_section = prompt[kb_start:kb_start+1000]
                        self.stdout.write(f"\n📚 بخش Knowledge Base در Prompt:")
                        self.stdout.write(f"{kb_section}...")
                
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"❌ Prompt building failed: {e}"))
                import traceback
                self.stdout.write(traceback.format_exc())
            
            # 7. بررسی آخرین پاسخ AI
            self.stdout.write(f"\n{'='*80}")
            self.stdout.write("7️⃣ بررسی آخرین پاسخ AI")
            self.stdout.write(f"{'='*80}")
            
            last_ai_msg = Message.objects.filter(
                conversation=conversation,
                type='AI'
            ).order_by('-created_at').first()
            
            if last_ai_msg:
                self.stdout.write(f"📝 پاسخ AI: '{last_ai_msg.content[:200]}...'")
                self.stdout.write(f"⏰ زمان: {last_ai_msg.created_at}")
                
                if "متأسفانه این اطلاعات" in last_ai_msg.content:
                    self.stdout.write(self.style.ERROR("❌ AI گفته 'متأسفانه این اطلاعات...'"))
                else:
                    self.stdout.write(self.style.SUCCESS("✅ AI پاسخ دیگری داده"))
            else:
                self.stdout.write(self.style.WARNING("⚠️ هیچ پاسخ AI پیدا نشد"))
            
            # خلاصه
            self.stdout.write(f"\n{'='*80}")
            self.stdout.write("📊 خلاصه نتایج:")
            self.stdout.write(f"{'='*80}")
            self.stdout.write(f"✅ Manual Chunks: {chunk_count}")
            self.stdout.write(f"✅ Routing: {routing['intent']} → {routing['primary_source']}")
            
            self.stdout.write(f"\n💡 پیشنهادات:")
            if chunk_count == 0:
                self.stdout.write(self.style.ERROR("   ❌ مشکل: Manual chunks وجود ندارند!"))
                self.stdout.write("   → باید manual prompt را chunk کنید")
            else:
                self.stdout.write(self.style.SUCCESS("   ✅ Manual chunks وجود دارند"))
                if retrieval_result and retrieval_result['total_chunks'] == 0:
                    self.stdout.write(self.style.ERROR("   ❌ مشکل: Retrieval chunks را پیدا نمی‌کند!"))
                    self.stdout.write("   → باید بررسی کنید چرا hybrid search کار نمی‌کند")
                elif retrieval_result:
                    manual_in_results = any(
                        chunk.get('type') == 'manual' 
                        for chunk in retrieval_result['primary_context'] + retrieval_result['secondary_context']
                    )
                    if not manual_in_results:
                        self.stdout.write(self.style.WARNING("   ⚠️ مشکل: Manual chunks در نتایج retrieval نیستند!"))
                        self.stdout.write("   → ممکن است similarity score پایین باشد")
        
        except Conversation.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"❌ کانورسیشن با ID '{conversation_id}' پیدا نشد!"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Error: {e}"))
            import traceback
            self.stdout.write(traceback.format_exc())

