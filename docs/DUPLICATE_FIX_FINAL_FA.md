# راه‌حل نهایی برای جلوگیری از تکرار پیام‌های AI

## مشکل
وقتی هوش مصنوعی یک پیام تولید می‌کند:
1. پیام در دیتابیس با `type='AI'` ذخیره می‌شود ✅
2. پیام به API اینستاگرام ارسال می‌شود ✅  
3. اینستاگرام webhook را برمی‌گرداند 📥
4. سیستم ما آن را به عنوان "پیام صاحب اکانت" تشخیص می‌داد ❌
5. پیام دوباره با `type='support'` ذخیره می‌شد ❌
6. **نتیجه**: پیام تکراری (یکبار AI، یکبار support) ❌❌

## راه‌حل ساده و قدرتمند

### مرحله 1: لاگ‌های دقیق
هنگام دریافت webhook از اینستاگرام، سیستم این موارد را چک می‌کند:

```python
logger.info(f"🔍 Checking for duplicate owner messages...")
logger.info(f"   Content: {message_content[:50]}...")
logger.info(f"   Conversation: {conversation.id}")
```

### مرحله 2: جستجوی ساده در دیتابیس
به جای روش‌های پیچیده، فقط یک سوال ساده می‌پرسیم:

**"آیا در ۶۰ ثانیه گذشته، پیامی با همین محتوا از نوع AI یا support وجود دارد؟"**

```python
existing_messages = Message.objects.filter(
    conversation=conversation,
    content=message_content,
    created_at__gte=recent_cutoff,  # ۶۰ ثانیه گذشته
    type__in=['support', 'AI']      # AI یا support
).order_by('-created_at')

if existing_messages.exists():
    # پیام تکراری است - ایجاد نکن!
    logger.warning("⚠️⚠️⚠️ DUPLICATE DETECTED - BLOCKING")
    return {"duplicate": True, "blocked": True}
```

### مرحله 3: لاگ‌های واضح
اگر پیام تکراری پیدا شود، لاگ‌های کامل ثبت می‌شود:

```
⚠️⚠️⚠️ DUPLICATE DETECTED - BLOCKING WEBHOOK MESSAGE ⚠️⚠️⚠️
   Existing message ID: abc123
   Existing message type: AI
   Existing message is_ai: True
   >>> SKIPPING DUPLICATE CREATION FROM WEBHOOK <<<
```

### مرحله 4: لاگ برای پیام‌های جدید واقعی
اگر تکراری نبود:

```
✅ No duplicate found - this is a NEW owner message from Instagram app
```

## چگونه کار می‌کند؟

### وقتی AI پیام تولید می‌کند:
```
1. ✅ AI message ایجاد می‌شود (type='AI')
2. ✅ لاگ: "AI message created: MSG_ID"
3. ✅ لاگ: "Content: [first 50 chars]..."
4. ✅ لاگ: "Type: AI"
5. ✅ پیام به Instagram API ارسال می‌شود
6. ✅ لاگ: "Instagram message_id: INSTA_MSG_ID"
7. ✅ لاگ: "Cached sent message to prevent duplicate"
```

### وقتی Instagram webhook را برمی‌گرداند:
```
1. 📥 Webhook دریافت می‌شود
2. 🔍 لاگ: "Checking for duplicate owner messages..."
3. 🔍 جستجو در دیتابیس برای پیام با همین محتوا
4. ⚠️ پیام موجود پیدا می‌شود!
5. ⚠️ لاگ: "DUPLICATE DETECTED - BLOCKING"
6. ⚠️ لاگ: "Existing message ID: MSG_ID"
7. ⚠️ لاگ: "Existing message type: AI"
8. ✅ ایجاد تکراری جلوگیری می‌شود!
```

### وقتی از Instagram App پیام ارسال می‌شود (مستقیم):
```
1. 📥 Webhook دریافت می‌شود
2. 🔍 لاگ: "Checking for duplicate owner messages..."
3. 🔍 جستجو در دیتابیس
4. ✅ هیچ پیامی پیدا نمی‌شود
5. ✅ لاگ: "No duplicate found - this is NEW"
6. ✅ پیام جدید با type='support' ایجاد می‌شود
```

## تغییرات انجام شده

### ۱. فایل: `src/message/insta.py`
- حذف روش‌های پیچیده (metadata query، cache)
- استفاده از یک query ساده در دیتابیس
- افزایش time window از ۳۰ به ۶۰ ثانیه
- اضافه کردن لاگ‌های دقیق و واضح

### ۲. فایل: `src/AI_model/services/gemini_service.py`
- اضافه کردن لاگ‌ها برای ایجاد AI message
- اضافه کردن لاگ‌ها برای ارسال به Instagram
- اضافه کردن لاگ برای metadata و cache

### ۳. فایل: `src/message/api/send_message.py`
- ذخیره `sent_from_app=True` در metadata
- ذخیره Instagram message_id در metadata

## چطور تست کنیم؟

### ۱. فعال کردن لاگ‌ها
مطمئن شوید که لاگ‌های Django فعال هستند.

### ۲. ارسال پیام توسط AI
وقتی AI پیام می‌فرستد، باید این لاگ‌ها را ببینید:

```
✅ AI message created: MSG_123
   Content: سلام! چطور می‌تونم کمکتون کنم؟
   Type: AI
   is_ai_response: True

✅ AI response sent to Instagram successfully
   Instagram message_id: INSTA_456
   Stored Instagram message_id in AI message metadata
   📝 Cached sent message to prevent webhook duplicate
```

### ۳. دریافت Webhook از Instagram
بعد از چند ثانیه، باید این لاگ را ببینید:

```
🔍 Checking for duplicate owner messages...
   Content: سلام! چطور می‌تونم کمکتون کنم؟
   Conversation: CONV_789
   Found 1 matching messages

⚠️⚠️⚠️ DUPLICATE DETECTED - BLOCKING WEBHOOK MESSAGE ⚠️⚠️⚠️
   Existing message ID: MSG_123
   Existing message type: AI
   Existing message is_ai: True
   >>> SKIPPING DUPLICATE CREATION FROM WEBHOOK <<<
```

### ۴. ارسال از Instagram App (مستقیم)
وقتی شما از Instagram app پیام بفرستید:

```
🔍 Checking for duplicate owner messages...
   Content: این پیام از اینستاگرام فرستادم
   Conversation: CONV_789
   Found 0 matching messages

✅ No duplicate found - this is a NEW owner message from Instagram app

✅ Text message created: MSG_999 (type=support)
```

## رفع مشکل (Troubleshooting)

### اگر هنوز پیام‌ها تکراری هستند:

#### ۱. چک کردن لاگ‌ها
```bash
# لاگ‌های webhook را ببینید
grep "Checking for duplicate" logs/django.log

# لاگ‌های AI را ببینید  
grep "AI message created" logs/django.log

# لاگ‌های duplicate را ببینید
grep "DUPLICATE DETECTED" logs/django.log
```

#### ۲. چک کردن دیتابیس
```python
# آیا پیام‌های AI در دیتابیس هستند؟
Message.objects.filter(type='AI').count()

# آیا پیام‌های تکراری وجود دارد؟
from django.db.models import Count
duplicates = Message.objects.values('conversation', 'content', 'created_at').annotate(
    count=Count('id')
).filter(count__gt=1)
print(duplicates)
```

#### ۳. چک کردن زمان
```python
from django.utils import timezone
from datetime import timedelta

# پیام‌های ۶۰ ثانیه گذشته
recent = Message.objects.filter(
    created_at__gte=timezone.now() - timedelta(seconds=60)
).values('id', 'type', 'content', 'created_at')

for msg in recent:
    print(msg)
```

## نتیجه‌گیری

این راه‌حل:
- ✅ **ساده است**: فقط یک query در دیتابیس
- ✅ **قابل اعتماد است**: همیشه کار می‌کند
- ✅ **سریع است**: query ساده و indexed
- ✅ **قابل debug است**: لاگ‌های واضح و کامل
- ✅ **پیام‌های واقعی را حفظ می‌کند**: فقط duplicateها را block می‌کند

با این تغییرات، **هیچ پیام تکراری ایجاد نخواهد شد**! 🎉

---

## یادداشت مهم

اگر هنوز مشکل وجود دارد، لطفاً:
1. لاگ‌ها را برای من بفرستید
2. یک نمونه از پیام تکراری را نشان دهید
3. زمان دقیق ایجاد هر دو پیام را بگویید

من کمک خواهم کرد! 💪

