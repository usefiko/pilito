# راهنمای Debug - مشکل "بعضی وقت‌ها تکرار می‌شود"

## مشکل
گاهی اوقات پیام‌های Workflow هنوز تکراری می‌شوند.

## چرا "بعضی وقت‌ها"؟

این می‌تواند به دلایل زیر باشد:

### ۱. محتوای متفاوت
```python
# پیام اصلی
"سلام! به نیما گُلد خوش آمدید.\n"

# پیام webhook (Instagram \n را حذف می‌کند)
"سلام! به نیما گُلد خوش آمدید."

# ما strip() می‌کنیم پس این مشکل حل شده ✅
```

### ۲. کاراکترهای مخفی
```python
# پیام اصلی
"سلام!\u200cچطوری؟"  # Zero-width non-joiner

# پیام webhook  
"سلام!چطوری؟"  # بدون ZWNJ

# این یکسان نیست! ❌
```

### ۳. Time Window
```python
# اگر webhook بیشتر از ۶۰ ثانیه دیر برسد
# پیام از time window خارج می‌شود
recent_cutoff = timezone.now() - timedelta(seconds=60)
```

### ۴. Race Condition
```python
# اگر دو webhook همزمان برسند
# ممکن است هر دو query را همزمان اجرا کنند
# و هیچ کدام پیام دیگری را نبینند
```

## چک کردن دقیق

### مرحله ۱: فعال کردن DEBUG logs

در `settings.py` یا environment:
```python
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'message': {
            'handlers': ['console'],
            'level': 'DEBUG',  # ⬅️ این را DEBUG کنید
        },
        'workflow': {
            'handlers': ['console'],
            'level': 'DEBUG',  # ⬅️ این را DEBUG کنید
        },
    },
}
```

### مرحله ۲: اجرای اسکریپت چک

```bash
# روی سرور
cd /path/to/project
bash check_workflow_logs.sh > workflow_debug.txt

# یا
chmod +x check_workflow_logs.sh
./check_workflow_logs.sh
```

### مرحله ۳: چک کردن لاگ‌های DEBUG

با DEBUG فعال، باید این‌ها را ببینید:

```
🔍 Checking for duplicate owner messages...
   Checking 3 recent messages

   [1] Comparing with message msg_123:
       Type: marketing
       Created: 2025-11-07 10:00:05
       Content length: 125 -> normalized: 123
       First 80 chars: سلام! به...
       Match: False
       Metadata: {'sent_from_app': True, ...}

   [2] Comparing with message msg_456:
       Type: AI
       Created: 2025-11-07 10:00:03
       Content length: 100 -> normalized: 98
       First 80 chars: خواهش می‌کنم...
       Match: False
       Metadata: {'sent_from_app': True, ...}

   [3] Comparing with message msg_789:
       Type: support
       Created: 2025-11-07 10:00:01
       Content length: 50 -> normalized: 48
       First 80 chars: بله حتماً...
       Match: True
       Metadata: {'sent_from_app': True, ...}

   ✅ MATCH FOUND at index 3: message msg_789
```

### مرحله ۴: اگر Match نیافت (تکراری ایجاد شد)

اگر لاگ‌ها نشان می‌دهند که Match پیدا نشد، ببینید:

```
   [1] Comparing with message msg_WORKFLOW:
       Type: marketing
       Created: 2025-11-07 10:00:05
       Content length: 125 -> normalized: 123
       First 80 chars: سلام! خوش آمدید...
       Match: False           ⬅️ چرا False؟
       Metadata: {'sent_from_app': True}
```

**علت‌های احتمالی**:
1. محتوا دقیقاً یکسان نیست (کاراکتر مخفی، فاصله extra)
2. Time window گذشته (بیشتر از ۶۰ ثانیه)
3. Conversation متفاوت است

## دستورات Debug در Django Shell

```python
from message.models import Message, Conversation
from django.utils import timezone
from datetime import timedelta

# پیدا کردن تکراری‌های اخیر
recent = Message.objects.filter(
    created_at__gte=timezone.now() - timedelta(minutes=10)
).order_by('-created_at').values(
    'id', 'type', 'content', 'created_at', 'conversation_id', 'metadata'
)

for msg in recent:
    print(f"\nID: {msg['id']}")
    print(f"Type: {msg['type']}")
    print(f"Conversation: {msg['conversation_id']}")
    print(f"Content: {msg['content'][:80]}")
    print(f"Created: {msg['created_at']}")
    print(f"Metadata: {msg['metadata']}")

# پیدا کردن تکراری‌های دقیق
from django.db.models import Count

duplicates = Message.objects.filter(
    created_at__gte=timezone.now() - timedelta(minutes=10)
).values('conversation_id', 'content').annotate(
    count=Count('id')
).filter(count__gt=1).order_by('-count')

print(f"\n\nFound {duplicates.count()} duplicate sets:")
for dup in duplicates:
    print(f"\nConversation: {dup['conversation_id']}")
    print(f"Content: {dup['content'][:80]}...")
    print(f"Count: {dup['count']}")
    
    # نمایش همه
    msgs = Message.objects.filter(
        conversation_id=dup['conversation_id'],
        content=dup['content']
    ).order_by('-created_at').values('id', 'type', 'created_at', 'metadata')
    
    for m in msgs:
        print(f"  - {m['id']}: {m['type']}, {m['created_at']}, metadata={m['metadata']}")

# مقایسه دقیق محتوا
msg1_id = "MSG_1_ID"  # جایگزین کنید
msg2_id = "MSG_2_ID"  # جایگزین کنید

msg1 = Message.objects.get(id=msg1_id)
msg2 = Message.objects.get(id=msg2_id)

print(f"\nMessage 1:")
print(f"  Content: '{msg1.content}'")
print(f"  Length: {len(msg1.content)}")
print(f"  Normalized: '{msg1.content.strip()}'")
print(f"  Normalized length: {len(msg1.content.strip())}")
print(f"  Repr: {repr(msg1.content)}")

print(f"\nMessage 2:")
print(f"  Content: '{msg2.content}'")
print(f"  Length: {len(msg2.content)}")
print(f"  Normalized: '{msg2.content.strip()}'")
print(f"  Normalized length: {len(msg2.content.strip())}")
print(f"  Repr: {repr(msg2.content)}")

print(f"\nComparison:")
print(f"  Exact match: {msg1.content == msg2.content}")
print(f"  Normalized match: {msg1.content.strip() == msg2.content.strip()}")

# بررسی byte-by-byte
if msg1.content.strip() != msg2.content.strip():
    c1 = msg1.content.strip()
    c2 = msg2.content.strip()
    print(f"\n  Difference found:")
    for i, (ch1, ch2) in enumerate(zip(c1, c2)):
        if ch1 != ch2:
            print(f"    Position {i}: '{ch1}' (U+{ord(ch1):04X}) vs '{ch2}' (U+{ord(ch2):04X})")
```

## راه‌حل‌های پیشنهادی

### راه‌حل ۱: Normalization بیشتر

اگر مشکل کاراکترهای مخفی است:

```python
import unicodedata

def normalize_content(content):
    # حذف ZWNJ, ZWJ و کاراکترهای مخفی
    content = content.strip()
    # حذف کاراکترهای Unicode invisible
    content = ''.join(ch for ch in content if unicodedata.category(ch) != 'Cf')
    # فشرده کردن فاصله‌های متعدد
    import re
    content = re.sub(r'\s+', ' ', content)
    return content
```

### راه‌حل ۲: افزایش Time Window

اگر webhook دیر می‌رسد:

```python
recent_cutoff = timezone.now() - timedelta(seconds=120)  # از ۶۰ به ۱۲۰
```

### راه‌حل ۳: استفاده از Transaction Lock

اگر race condition است:

```python
from django.db import transaction

with transaction.atomic():
    # قفل کردن conversation
    conversation = Conversation.objects.select_for_update().get(id=conversation_id)
    # چک duplicate
    # ایجاد message
```

## اطلاعاتی که به من بفرستید

اگر هنوز مشکل دارید، لطفاً این‌ها را بفرستید:

1. **خروجی `check_workflow_logs.sh`**
2. **لاگ‌های DEBUG** (با DEBUG=True)
3. **خروجی دستورات Django shell بالا**
4. **ID دو پیام تکراری**
5. **زمان دقیق هر کدام**

با این اطلاعات می‌تونم دقیقاً ببینم چه اتفاقی افتاده! 🔍

