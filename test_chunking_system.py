#!/usr/bin/env python
"""
🔍 تست کامل سیستم Chunking
بررسی می‌کنه که:
1. Signals درست register شدن
2. Chunking برای Manual Prompt, Website, Product, QAPair درست کار می‌کنه
3. داده‌ها در TenantKnowledge ذخیره می‌شن
"""

import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.db.models.signals import post_save
from django.contrib.auth import get_user_model
from web_knowledge.models import QAPair, Product, WebsitePage, WebsiteSource
from settings.models import AIPrompts
from AI_model.models import TenantKnowledge
from AI_model.tasks import (
    chunk_qapair_async,
    chunk_product_async,
    chunk_webpage_async,
    chunk_manual_prompt_async
)
import uuid
from datetime import datetime

User = get_user_model()

def print_section(title):
    print("\n" + "="*80)
    print(f"  {title}")
    print("="*80)

def check_signals():
    """چک می‌کنه که signals درست register شدن"""
    print_section("📡 بررسی Signal Registration")
    
    # Import signals to ensure they're registered
    import AI_model.signals
    
    # Check QAPair signals
    from web_knowledge.models import QAPair
    receivers = post_save._live_receivers(QAPair)
    qapair_signals = [r for r in receivers if 'chunking' in str(r).lower() or 'qapair' in str(r).lower()]
    
    print(f"✅ QAPair post_save signals: {len(qapair_signals)}")
    for sig in qapair_signals:
        print(f"   - {sig}")
    
    # Check Product signals
    from web_knowledge.models import Product
    receivers = post_save._live_receivers(Product)
    product_signals = [r for r in receivers if 'chunking' in str(r).lower() or 'product' in str(r).lower()]
    
    print(f"✅ Product post_save signals: {len(product_signals)}")
    for sig in product_signals:
        print(f"   - {sig}")
    
    # Check WebsitePage signals
    from web_knowledge.models import WebsitePage
    receivers = post_save._live_receivers(WebsitePage)
    webpage_signals = [r for r in receivers if 'chunking' in str(r).lower() or 'webpage' in str(r).lower()]
    
    print(f"✅ WebsitePage post_save signals: {len(webpage_signals)}")
    for sig in webpage_signals:
        print(f"   - {sig}")
    
    # Check AIPrompts signals
    from settings.models import AIPrompts
    receivers = post_save._live_receivers(AIPrompts)
    aiprompts_signals = [r for r in receivers if 'chunking' in str(r).lower() or 'manual' in str(r).lower()]
    
    print(f"✅ AIPrompts post_save signals: {len(aiprompts_signals)}")
    for sig in aiprompts_signals:
        print(f"   - {sig}")
    
    return len(qapair_signals) > 0 and len(product_signals) > 0 and len(webpage_signals) > 0 and len(aiprompts_signals) > 0

def test_manual_prompt_chunking():
    """تست chunking برای Manual Prompt"""
    print_section("📝 تست Manual Prompt Chunking")
    
    # Get first user
    user = User.objects.first()
    if not user:
        print("❌ هیچ کاربری پیدا نشد!")
        return False
    
    print(f"✅ کاربر پیدا شد: {user.username} (ID: {user.id})")
    
    # Get or create AIPrompts
    ai_prompts, created = AIPrompts.objects.get_or_create(user=user)
    
    # Set test manual prompt
    test_prompt = f"""
    این یک تست Manual Prompt است که در تاریخ {datetime.now()} ایجاد شده.
    
    اطلاعات شرکت:
    - نام: شرکت تست
    - آدرس: تهران، خیابان تست
    - تلفن: 021-12345678
    - ایمیل: test@example.com
    
    خدمات ما:
    1. طراحی وب سایت
    2. توسعه اپلیکیشن موبایل
    3. مشاوره فنی
    
    ساعات کاری: شنبه تا پنجشنبه، 9 صبح تا 6 عصر
    """
    
    # Delete existing chunks first
    TenantKnowledge.objects.filter(user=user, chunk_type='manual').delete()
    print(f"🗑️  Chunks قبلی حذف شدند")
    
    # Update manual prompt (this should trigger signal)
    ai_prompts.manual_prompt = test_prompt
    ai_prompts.save()
    print(f"✅ Manual Prompt ذخیره شد (Signal باید trigger بشه)")
    
    # Wait a bit for async task
    import time
    print("⏳ منتظر اجرای async task...")
    time.sleep(10)
    
    # Check if chunks were created
    chunks = TenantKnowledge.objects.filter(user=user, chunk_type='manual')
    chunk_count = chunks.count()
    
    print(f"📊 تعداد Chunks ایجاد شده: {chunk_count}")
    
    if chunk_count > 0:
        print("✅ Manual Prompt chunking موفق بود!")
        for chunk in chunks[:3]:  # Show first 3
            print(f"   - Chunk ID: {chunk.id}, Title: {chunk.section_title[:50]}...")
        return True
    else:
        print("❌ هیچ Chunk ایجاد نشد!")
        print("   ممکنه signal trigger نشده باشه یا task fail کرده باشه")
        return False

def test_qapair_chunking():
    """تست chunking برای QAPair"""
    print_section("❓ تست QAPair Chunking")
    
    # Get first user
    user = User.objects.first()
    if not user:
        print("❌ هیچ کاربری پیدا نشد!")
        return False
    
    print(f"✅ کاربر پیدا شد: {user.username}")
    
    # Get or create a website
    website, _ = WebsiteSource.objects.get_or_create(
        user=user,
        defaults={'url': 'https://test.example.com', 'name': 'Test Website'}
    )
    
    # Get or create a page
    page, _ = WebsitePage.objects.get_or_create(
        website=website,
        url='https://test.example.com/test',
        defaults={
            'title': 'Test Page',
            'processing_status': 'completed',
            'cleaned_content': 'This is test content for chunking'
        }
    )
    
    # Create test QAPair
    qa = QAPair.objects.create(
        page=page,
        user=user,
        question="سوال تست چیست؟",
        answer="این یک پاسخ تست است برای بررسی سیستم chunking.",
        generation_status='completed',
        created_by_ai=False
    )
    
    print(f"✅ QAPair ایجاد شد: {qa.id}")
    
    # Delete existing chunks
    TenantKnowledge.objects.filter(source_id=qa.id, chunk_type='faq').delete()
    print(f"🗑️  Chunks قبلی حذف شدند")
    
    # Trigger chunking manually (simulate signal)
    from AI_model.tasks import chunk_qapair_async
    result = chunk_qapair_async(str(qa.id))
    print(f"✅ Task اجرا شد: {result}")
    
    # Check if chunks were created
    chunks = TenantKnowledge.objects.filter(source_id=qa.id, chunk_type='faq')
    chunk_count = chunks.count()
    
    print(f"📊 تعداد Chunks ایجاد شده: {chunk_count}")
    
    if chunk_count > 0:
        print("✅ QAPair chunking موفق بود!")
        chunk = chunks.first()
        print(f"   - Chunk ID: {chunk.id}")
        print(f"   - Section Title: {chunk.section_title[:50]}...")
        print(f"   - Has Embedding: {chunk.tldr_embedding is not None}")
        return True
    else:
        print("❌ هیچ Chunk ایجاد نشد!")
        return False

def test_product_chunking():
    """تست chunking برای Product"""
    print_section("🛍️  تست Product Chunking")
    
    # Get first user
    user = User.objects.first()
    if not user:
        print("❌ هیچ کاربری پیدا نشد!")
        return False
    
    print(f"✅ کاربر پیدا شد: {user.username}")
    
    # Create test product
    product = Product.objects.create(
        user=user,
        title="محصول تست",
        description="این یک محصول تست است برای بررسی سیستم chunking. این محصول دارای ویژگی‌های مختلفی است.",
        price="100000",
        link="https://test.example.com/product/test"
    )
    
    print(f"✅ Product ایجاد شد: {product.id}")
    
    # Delete existing chunks
    TenantKnowledge.objects.filter(source_id=product.id, chunk_type='product').delete()
    print(f"🗑️  Chunks قبلی حذف شدند")
    
    # Trigger chunking manually
    result = chunk_product_async(str(product.id))
    print(f"✅ Task اجرا شد: {result}")
    
    # Check if chunks were created
    chunks = TenantKnowledge.objects.filter(source_id=product.id, chunk_type='product')
    chunk_count = chunks.count()
    
    print(f"📊 تعداد Chunks ایجاد شده: {chunk_count}")
    
    if chunk_count > 0:
        print("✅ Product chunking موفق بود!")
        chunk = chunks.first()
        print(f"   - Chunk ID: {chunk.id}")
        print(f"   - Section Title: {chunk.section_title[:50]}...")
        print(f"   - Has Embedding: {chunk.tldr_embedding is not None}")
        return True
    else:
        print("❌ هیچ Chunk ایجاد نشد!")
        return False

def test_webpage_chunking():
    """تست chunking برای WebsitePage"""
    print_section("🌐 تست WebsitePage Chunking")
    
    # Get first user
    user = User.objects.first()
    if not user:
        print("❌ هیچ کاربری پیدا نشد!")
        return False
    
    print(f"✅ کاربر پیدا شد: {user.username}")
    
    # Get or create website
    website, _ = WebsiteSource.objects.get_or_create(
        user=user,
        defaults={'url': 'https://test.example.com', 'name': 'Test Website'}
    )
    
    # Create test page with content
    test_content = """
    این یک صفحه تست است برای بررسی سیستم chunking.
    
    بخش اول:
    این بخش شامل اطلاعات اولیه در مورد شرکت است. ما یک شرکت فناوری هستیم که در زمینه توسعه نرم‌افزار فعالیت می‌کنیم.
    
    بخش دوم:
    خدمات ما شامل طراحی وب سایت، توسعه اپلیکیشن موبایل و مشاوره فنی است. ما با تیمی متخصص آماده خدمت‌رسانی به شما هستیم.
    
    بخش سوم:
    برای تماس با ما می‌توانید از طریق ایمیل یا تلفن با ما در ارتباط باشید. ساعات کاری ما شنبه تا پنجشنبه از 9 صبح تا 6 عصر است.
    """
    
    page = WebsitePage.objects.create(
        website=website,
        url='https://test.example.com/test-page',
        title='صفحه تست Chunking',
        cleaned_content=test_content,
        processing_status='completed'
    )
    
    print(f"✅ WebsitePage ایجاد شد: {page.id}")
    
    # Delete existing chunks
    TenantKnowledge.objects.filter(source_id=page.id, chunk_type='website').delete()
    print(f"🗑️  Chunks قبلی حذف شدند")
    
    # Trigger chunking manually
    result = chunk_webpage_async(str(page.id))
    print(f"✅ Task اجرا شد: {result}")
    
    # Check if chunks were created
    chunks = TenantKnowledge.objects.filter(source_id=page.id, chunk_type='website')
    chunk_count = chunks.count()
    
    print(f"📊 تعداد Chunks ایجاد شده: {chunk_count}")
    
    if chunk_count > 0:
        print("✅ WebsitePage chunking موفق بود!")
        for i, chunk in enumerate(chunks[:3], 1):
            print(f"   {i}. Chunk ID: {chunk.id}, Title: {chunk.section_title[:50]}...")
        return True
    else:
        print("❌ هیچ Chunk ایجاد نشد!")
        return False

def check_existing_chunks():
    """بررسی Chunks موجود در سیستم"""
    print_section("📊 بررسی Chunks موجود")
    
    total_chunks = TenantKnowledge.objects.count()
    print(f"📊 کل Chunks در سیستم: {total_chunks}")
    
    # By type
    chunk_types = TenantKnowledge.objects.values('chunk_type').annotate(
        count=models.Count('id')
    ).order_by('-count')
    
    print("\n📈 Chunks بر اساس نوع:")
    for ct in chunk_types:
        chunk_type = ct['chunk_type']
        count = ct['count']
        print(f"   - {chunk_type}: {count}")
        
        # Check embeddings
        with_embedding = TenantKnowledge.objects.filter(
            chunk_type=chunk_type,
            tldr_embedding__isnull=False
        ).count()
        print(f"     (با embedding: {with_embedding})")
    
    # By user
    print("\n👥 Chunks بر اساس کاربر (Top 5):")
    user_chunks = TenantKnowledge.objects.values('user__username').annotate(
        count=models.Count('id')
    ).order_by('-count')[:5]
    
    for uc in user_chunks:
        print(f"   - {uc['user__username']}: {uc['count']} chunks")
    
    return total_chunks > 0

def main():
    """اجرای تمام تست‌ها"""
    print("\n" + "🔍"*40)
    print("  تست کامل سیستم Chunking")
    print("🔍"*40)
    
    results = {}
    
    # 1. Check signals
    results['signals'] = check_signals()
    
    # 2. Check existing chunks
    results['existing_chunks'] = check_existing_chunks()
    
    # 3. Test manual prompt
    try:
        results['manual_prompt'] = test_manual_prompt_chunking()
    except Exception as e:
        print(f"❌ خطا در تست Manual Prompt: {e}")
        import traceback
        traceback.print_exc()
        results['manual_prompt'] = False
    
    # 4. Test QAPair
    try:
        results['qapair'] = test_qapair_chunking()
    except Exception as e:
        print(f"❌ خطا در تست QAPair: {e}")
        import traceback
        traceback.print_exc()
        results['qapair'] = False
    
    # 5. Test Product
    try:
        results['product'] = test_product_chunking()
    except Exception as e:
        print(f"❌ خطا در تست Product: {e}")
        import traceback
        traceback.print_exc()
        results['product'] = False
    
    # 6. Test WebsitePage
    try:
        results['webpage'] = test_webpage_chunking()
    except Exception as e:
        print(f"❌ خطا در تست WebsitePage: {e}")
        import traceback
        traceback.print_exc()
        results['webpage'] = False
    
    # Summary
    print_section("📋 خلاصه نتایج")
    
    for test_name, result in results.items():
        status = "✅" if result else "❌"
        print(f"{status} {test_name}: {'موفق' if result else 'ناموفق'}")
    
    success_count = sum(1 for r in results.values() if r)
    total_count = len(results)
    
    print(f"\n📊 نتیجه کلی: {success_count}/{total_count} تست موفق")
    
    if success_count == total_count:
        print("🎉 همه تست‌ها موفق بودند!")
    else:
        print("⚠️  برخی تست‌ها ناموفق بودند. لطفاً لاگ‌ها رو بررسی کنید.")

if __name__ == '__main__':
    from django.db import models
    main()

