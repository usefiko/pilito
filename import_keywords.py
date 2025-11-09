#!/usr/bin/env python
"""
Import Intent Keywords to Database
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from AI_model.models import IntentKeyword
from django.core.cache import cache

# پاک کردن Keywords قبلی
deleted_count = IntentKeyword.objects.filter(user__isnull=True).delete()[0]
print(f'🗑️  Deleted {deleted_count} old global keywords')

# Keywords data
keywords_data = [
    # ==================== PRICING ====================
    # فارسی
    ('pricing', 'fa', 'قیمت', 1.5),
    ('pricing', 'fa', 'قیمتش', 1.5),
    ('pricing', 'fa', 'قیمتش چنده', 1.5),
    ('pricing', 'fa', 'چنده', 1.5),
    ('pricing', 'fa', 'چند', 1.5),
    ('pricing', 'fa', 'هزینه', 1.5),
    ('pricing', 'fa', 'تعرفه', 1.0),
    ('pricing', 'fa', 'پلن', 1.0),
    ('pricing', 'fa', 'پکیج', 1.0),
    ('pricing', 'fa', 'اشتراک', 1.0),
    ('pricing', 'fa', 'خرید', 1.0),
    ('pricing', 'fa', 'فروش', 1.0),
    ('pricing', 'fa', 'تومان', 1.5),
    ('pricing', 'fa', 'دلار', 1.0),
    ('pricing', 'fa', 'پرداخت', 1.0),
    ('pricing', 'fa', 'پول', 1.0),
    ('pricing', 'fa', 'ارزون', 1.0),
    ('pricing', 'fa', 'گرون', 1.0),
    ('pricing', 'fa', 'تخفیف', 1.0),
    ('pricing', 'fa', 'کد تخفیف', 1.0),
    ('pricing', 'fa', 'میخرم', 1.0),
    ('pricing', 'fa', 'میخوام بخرم', 1.0),
    # انگلیسی
    ('pricing', 'en', 'price', 1.5),
    ('pricing', 'en', 'cost', 1.5),
    ('pricing', 'en', 'pricing', 1.5),
    ('pricing', 'en', 'how much', 1.5),
    ('pricing', 'en', 'plan', 1.0),
    ('pricing', 'en', 'package', 1.0),
    ('pricing', 'en', 'subscription', 1.0),
    ('pricing', 'en', 'buy', 1.0),
    ('pricing', 'en', 'purchase', 1.0),
    ('pricing', 'en', 'payment', 1.0),
    ('pricing', 'en', 'dollar', 1.0),
    ('pricing', 'en', 'cheap', 1.0),
    ('pricing', 'en', 'expensive', 1.0),
    ('pricing', 'en', 'discount', 1.0),
    
    # ==================== PRODUCT ====================
    # فارسی
    ('product', 'fa', 'محصول', 1.5),
    ('product', 'fa', 'محصولات', 1.5),
    ('product', 'fa', 'محصولاتتون', 1.5),
    ('product', 'fa', 'سرویس', 1.0),
    ('product', 'fa', 'خدمات', 1.0),
    ('product', 'fa', 'ویژگی', 1.0),
    ('product', 'fa', 'امکانات', 1.0),
    ('product', 'fa', 'قابلیت', 1.0),
    ('product', 'fa', 'چیه', 1.5),
    ('product', 'fa', 'چیست', 1.0),
    ('product', 'fa', 'داری', 1.5),
    ('product', 'fa', 'دارید', 1.5),
    ('product', 'fa', 'دارین', 1.5),
    ('product', 'fa', 'داری؟', 1.5),
    ('product', 'fa', 'دارید؟', 1.5),
    ('product', 'fa', 'دارین؟', 1.5),
    ('product', 'fa', 'چی داری', 1.5),
    ('product', 'fa', 'چی دارید', 1.5),
    ('product', 'fa', 'چی دارین', 1.5),
    ('product', 'fa', 'موجود', 1.0),
    ('product', 'fa', 'موجوده', 1.0),
    ('product', 'fa', 'موجودی', 1.0),
    ('product', 'fa', 'رنگبندی', 1.0),
    ('product', 'fa', 'سایز', 1.0),
    ('product', 'fa', 'مدل', 1.0),
    ('product', 'fa', 'کالکشن', 1.0),
    ('product', 'fa', 'جنس', 1.0),
    ('product', 'fa', 'کیفیت', 1.0),
    ('product', 'fa', 'نمونه', 1.0),
    ('product', 'fa', 'مشخصات', 1.0),
    # انگلیسی
    ('product', 'en', 'product', 1.5),
    ('product', 'en', 'products', 1.5),
    ('product', 'en', 'service', 1.0),
    ('product', 'en', 'feature', 1.0),
    ('product', 'en', 'functionality', 1.0),
    ('product', 'en', 'capability', 1.0),
    ('product', 'en', 'what does', 1.0),
    ('product', 'en', 'what is', 1.0),
    ('product', 'en', 'do you have', 1.5),
    ('product', 'en', 'available', 1.0),
    ('product', 'en', 'in stock', 1.0),
    ('product', 'en', 'specifications', 1.0),
    
    # ==================== HOWTO ====================
    # فارسی
    ('howto', 'fa', 'چطور', 2.0),
    ('howto', 'fa', 'چطوری', 2.0),
    ('howto', 'fa', 'چگونه', 1.5),
    ('howto', 'fa', 'راهنما', 1.5),
    ('howto', 'fa', 'آموزش', 1.5),
    ('howto', 'fa', 'نحوه', 1.5),
    ('howto', 'fa', 'روش', 1.0),
    ('howto', 'fa', 'مراحل', 1.0),
    ('howto', 'fa', 'کمک', 1.5),
    ('howto', 'fa', 'میشه', 1.0),
    ('howto', 'fa', 'میتونم', 1.0),
    ('howto', 'fa', 'راه', 1.0),
    ('howto', 'fa', 'گام به گام', 1.0),
    ('howto', 'fa', 'توضیح بده', 1.0),
    ('howto', 'fa', 'توضیح', 1.0),
    ('howto', 'fa', 'یاد بده', 1.0),
    # انگلیسی
    ('howto', 'en', 'how', 2.0),
    ('howto', 'en', 'how to', 2.0),
    ('howto', 'en', 'guide', 1.5),
    ('howto', 'en', 'tutorial', 1.5),
    ('howto', 'en', 'steps', 1.0),
    ('howto', 'en', 'instruction', 1.0),
    ('howto', 'en', 'way to', 1.0),
    ('howto', 'en', 'how do i', 2.0),
    ('howto', 'en', 'help', 1.5),
    ('howto', 'en', 'can i', 1.0),
    
    # ==================== CONTACT ==================== ⭐ مهم‌ترین!
    # فارسی
    # آدرس
    ('contact', 'fa', 'آدرس', 2.0),
    ('contact', 'fa', 'ادرس', 2.0),  # املای غلط رایج
    ('contact', 'fa', 'آدرستون', 2.0),
    ('contact', 'fa', 'ادرستون', 2.0),  # املای غلط رایج
    ('contact', 'fa', 'آدرس شما', 2.0),
    ('contact', 'fa', 'ادرس شما', 2.0),  # املای غلط رایج
    ('contact', 'fa', 'کجایید', 2.0),
    ('contact', 'fa', 'کجاست', 2.0),
    ('contact', 'fa', 'کجا', 1.5),
    ('contact', 'fa', 'محل', 1.5),
    ('contact', 'fa', 'موقعیت', 1.0),
    ('contact', 'fa', 'لوکیشن', 1.0),
    # ارسال ⭐
    ('contact', 'fa', 'ارسال', 2.0),
    ('contact', 'fa', 'ارسال دارید', 2.0),
    ('contact', 'fa', 'ارسال دارین', 2.0),
    ('contact', 'fa', 'ارسالتون', 2.0),
    ('contact', 'fa', 'نحوه ارسال', 2.0),
    ('contact', 'fa', 'چطور ارسال', 2.0),
    ('contact', 'fa', 'پست', 1.5),
    ('contact', 'fa', 'پیک', 1.5),
    ('contact', 'fa', 'تحویل', 1.5),
    ('contact', 'fa', 'رایگان', 1.0),
    ('contact', 'fa', 'هزینه ارسال', 1.5),
    ('contact', 'fa', 'زمان ارسال', 1.5),
    ('contact', 'fa', 'چقدر طول میکشه', 1.0),
    ('contact', 'fa', 'کی میرسه', 1.5),
    # تماس
    ('contact', 'fa', 'تماس', 1.5),
    ('contact', 'fa', 'ارتباط', 1.5),
    ('contact', 'fa', 'پشتیبانی', 1.5),
    ('contact', 'fa', 'شماره', 1.5),
    ('contact', 'fa', 'تلفن', 1.5),
    ('contact', 'fa', 'موبایل', 1.0),
    ('contact', 'fa', 'ایمیل', 1.0),
    ('contact', 'fa', 'اینستاگرام', 1.0),
    ('contact', 'fa', 'تلگرام', 1.0),
    ('contact', 'fa', 'واتساپ', 1.0),
    ('contact', 'fa', 'ساعت کاری', 1.5),
    ('contact', 'fa', 'زمان کاری', 1.0),
    ('contact', 'fa', 'باز', 1.0),
    ('contact', 'fa', 'بسته', 1.0),
    # انگلیسی
    ('contact', 'en', 'contact', 2.0),
    ('contact', 'en', 'address', 2.0),
    ('contact', 'en', 'location', 2.0),
    ('contact', 'en', 'where', 2.0),
    ('contact', 'en', 'support', 1.5),
    ('contact', 'en', 'phone', 1.5),
    ('contact', 'en', 'email', 1.5),
    ('contact', 'en', 'reach', 1.0),
    ('contact', 'en', 'hours', 1.5),
    ('contact', 'en', 'call', 1.0),
    ('contact', 'en', 'shipping', 2.0),
    ('contact', 'en', 'delivery', 2.0),
    ('contact', 'en', 'ship', 1.5),
    
    # ==================== GENERAL ====================
    # فارسی
    ('general', 'fa', 'سلام', 0.5),
    ('general', 'fa', 'درود', 0.5),
    ('general', 'fa', 'ممنون', 0.5),
    ('general', 'fa', 'متشکرم', 0.5),
    ('general', 'fa', 'خوبی', 0.5),
    ('general', 'fa', 'چطوری', 0.5),
    # انگلیسی
    ('general', 'en', 'hello', 0.5),
    ('general', 'en', 'hi', 0.5),
    ('general', 'en', 'thanks', 0.5),
    ('general', 'en', 'thank you', 0.5),
]

# Create keywords
created = 0
for intent, lang, keyword, weight in keywords_data:
    try:
        IntentKeyword.objects.create(
            intent=intent,
            language=lang,
            keyword=keyword,
            weight=weight,
            user=None,
            is_active=True
        )
        created += 1
    except Exception as e:
        print(f'⚠️  Error creating {keyword}: {e}')

print(f'\n✅ Created {created} keywords successfully!')

# نمایش آمار
from collections import Counter
counter = Counter([kw[0] for kw in keywords_data])
print('\n📊 Keywords by Intent:')
for intent, count in counter.items():
    print(f'  - {intent}: {count}')

# پاک کردن cache
cache.delete_pattern('intent_keywords:*')
print('\n✅ Cache cleared!')

print('\n🎉 Import completed successfully!')

