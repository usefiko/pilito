# راهنمای Debug - چک کردن پیام‌های تکراری

## مرحله ۱: روی سرور لاگین کنید
```bash
ssh root@185.164.72.165
```

## مرحله ۲: پیدا کردن فایل لاگ Django
```bash
# معمولاً لاگ‌ها اینجا هستند:
ls -la /var/log/django*.log
# یا
ls -la /home/*/logs/
# یا
find / -name "django.log" 2>/dev/null
```

## مرحله ۳: چک کردن لاگ‌های اخیر
```bash
# لاگ‌های ۱۰۰ خط آخر
tail -100 /path/to/django.log

# یا لاگ‌های زنده
tail -f /path/to/django.log
```

## مرحله ۴: فیلتر کردن لاگ‌ها برای پیام‌های AI
```bash
# لاگ‌های ایجاد AI message
tail -200 /path/to/django.log | grep "AI message created"

# لاگ‌های ارسال به Instagram
tail -200 /path/to/django.log | grep "sent to Instagram"

# لاگ‌های دریافت webhook
tail -200 /path/to/django.log | grep "Instagram Webhook"

# لاگ‌های چک duplicate
tail -200 /path/to/django.log | grep "Checking for duplicate"

# لاگ‌های DUPLICATE DETECTED
tail -200 /path/to/django.log | grep "DUPLICATE DETECTED"
```

## مرحله ۵: چک کردن دیتابیس
```bash
# وارد Django shell شوید
cd /path/to/project
python manage.py shell
```

سپس در Python shell:
```python
from message.models import Message, Conversation
from django.utils import timezone
from datetime import timedelta

# پیام‌های ۵ دقیقه اخیر
recent = Message.objects.filter(
    created_at__gte=timezone.now() - timedelta(minutes=5)
).order_by('-created_at')

print(f"Total messages in last 5 minutes: {recent.count()}")

# نمایش جزئیات
for msg in recent[:20]:
    print(f"\n---")
    print(f"ID: {msg.id}")
    print(f"Type: {msg.type}")
    print(f"Content: {msg.content[:50]}...")
    print(f"is_ai_response: {msg.is_ai_response}")
    print(f"Created: {msg.created_at}")
    print(f"Conversation: {msg.conversation_id}")
    print(f"Metadata: {msg.metadata}")

# پیدا کردن duplicates
from django.db.models import Count
duplicates = Message.objects.values(
    'conversation', 'content'
).annotate(
    count=Count('id'),
    ids=Count('id')
).filter(count__gt=1)

print(f"\n\nDuplicate messages found: {duplicates.count()}")
for dup in duplicates[:5]:
    print(f"\n---")
    print(f"Conversation: {dup['conversation']}")
    print(f"Content: {dup['content'][:50]}...")
    print(f"Count: {dup['count']}")
    
    # نمایش همه پیام‌های تکراری
    msgs = Message.objects.filter(
        conversation_id=dup['conversation'],
        content=dup['content']
    ).order_by('-created_at')
    
    for m in msgs:
        print(f"  - ID: {m.id}, Type: {m.type}, Created: {m.created_at}")
```

## مرحله ۶: تست زنده
۱. یک پیام به AI بفرستید
۲. بلافاصله لاگ‌ها را ببینید:
```bash
tail -f /path/to/django.log | grep -E "(AI message|Instagram|duplicate|DUPLICATE)"
```

۳. منتظر بمانید تا webhook برسد (معمولاً ۱-۳ ثانیه)
۴. ببینید آیا پیام "DUPLICATE DETECTED" ظاهر می‌شود یا نه

## چیزی که باید ببینید:

### اگر کار می‌کند (بدون duplicate):
```
✅ AI message created: msg_123
   Content: سلام! چطور می‌تونم کمکتون کنم؟
   Type: AI

✅ AI response sent to Instagram successfully
   Instagram message_id: 1234567890

🔍 Checking for duplicate owner messages...
   Found 1 matching messages

⚠️⚠️⚠️ DUPLICATE DETECTED - BLOCKING ⚠️⚠️⚠️
   >>> SKIPPING DUPLICATE CREATION <<<
```

### اگر کار نمی‌کند (با duplicate):
```
✅ AI message created: msg_123
✅ AI response sent to Instagram

🔍 Checking for duplicate owner messages...
   Found 0 matching messages    ← این مشکل است!

✅ Text message created: msg_456 (type=support)    ← duplicate ایجاد شد!
```

## اگر هنوز duplicate ایجاد می‌شود:

این به معنی این است که query در دیتابیس پیام AI را پیدا نمی‌کند.
دلایل احتمالی:

1. **محتوای پیام دقیقاً یکسان نیست** (فاصله، enter، کاراکتر اضافی)
2. **زمان webhook خیلی دیر می‌رسد** (بیش از ۶۰ ثانیه)
3. **conversation_id متفاوت است**

لطفاً این اطلاعات را برام بفرستید:
- لاگ‌های مرحله ۴
- خروجی Django shell از مرحله ۵
- یک نمونه از پیام تکراری (ID هر دو پیام)

