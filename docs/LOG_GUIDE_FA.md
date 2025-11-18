# راهنمای لاگ‌ها - Debug پیام‌های تکراری

## لاگ‌های اضافه شده

### ۱. لاگ‌های ارسال پیام

#### AI Message (gemini_service.py)
```
✅ AI message created: msg_XXX
   Content: [first 50 chars]...
   Type: AI
   is_ai_response: True

✅ AI response sent to Instagram successfully
   Instagram message_id: 1234567890
   
📝 Cached sent message to prevent webhook duplicate
   Cache key: abc123def456...
   Cache timeout: 60 seconds
   
📝 Stored Instagram message_id in AI message metadata
   Updated metadata: {...}
```

#### Support Message (send_message.py)
```
📤 [Support] Sending Instagram message...
   Conversation: conv_123
   Customer: cust_456
   Content (first 80 chars): سلام...
   Content length: 123

✅ [Support] Instagram message sent successfully
   Instagram message_id: 1234567890
   
📝 [Support] Cached sent message to prevent webhook duplicate
   Cache key: abc123def456...
   Cache timeout: 60 seconds
```

#### Workflow Message (workflow_execution_service.py)
```
📤 [Workflow] Sending Instagram message...
   Conversation: conv_123
   Customer: cust_456
   Content (first 80 chars): پیام workflow...
   Content length: 123

✅ [Workflow] Instagram message sent successfully
   Instagram message_id: 1234567890
   
📝 [Workflow] Cached sent message to prevent webhook duplicate
   Cache key: abc123def456...
   Cache timeout: 60 seconds
   
📝 [Workflow] Stored Instagram message_id in metadata
   Message ID: msg_789
   External message_id: 1234567890
   Metadata: {'sent_from_app': True, ...}
```

#### Node Message (node_execution_service.py)
```
📤 [Node] Sending Instagram message...
   Conversation: conv_123
   Message ID: msg_789
   Content (first 80 chars): پیام node...
   Content length: 123

✅ [Node] Instagram message sent successfully
   Instagram message_id: 1234567890
   
📝 [Node] Cached sent message to prevent webhook duplicate
   Cache key: abc123def456...
   Cache timeout: 60 seconds
   
📝 [Node] Stored Instagram message_id in metadata
   Message ID: msg_789
   External message_id: 1234567890
   Metadata: {'sent_from_app': True, ...}
```

### ۲. لاگ‌های دریافت Webhook

#### وقتی webhook می‌رسد (insta.py)
```
📩 Instagram Webhook Data: {...}

Processing message from SENDER_ID to RECIPIENT_ID: محتوای پیام

📤 Detected OWNER message: Account owner SENDER_ID sent message to customer RECIPIENT_ID

🔍 Checking for duplicate owner messages...
   Content (first 80 chars): محتوای پیام...
   Content length: 123
   Conversation: conv_123
   Time cutoff: 2025-11-07 10:00:00
   
   Checking 3 recent messages
```

#### وقتی duplicate پیدا می‌شود ✅
```
⚠️⚠️⚠️ DUPLICATE DETECTED - BLOCKING WEBHOOK MESSAGE ⚠️⚠️⚠️
   Existing message ID: msg_XXX
   Existing message type: AI  (یا support یا marketing)
   Existing message is_ai: True
   Existing message created: 2025-11-07 10:00:05
   Time difference: 4.2 seconds
   Content match (normalized): YES
   >>> SKIPPING DUPLICATE CREATION FROM WEBHOOK <<<
```

#### وقتی duplicate نیست ✅
```
✅ No duplicate found - this is a NEW owner message from Instagram app

✅ Text message created: msg_NEW (type=support)
```

## چطور لاگ‌ها را ببینیم؟

### تمام لاگ‌ها
```bash
docker logs -f CONTAINER_ID
```

### فقط لاگ‌های مربوط به Instagram
```bash
docker logs -f CONTAINER_ID | grep -E "(Instagram|instagram)"
```

### فقط لاگ‌های ارسال
```bash
docker logs -f CONTAINER_ID | grep -E "(Sending Instagram|sent successfully)"
```

### فقط لاگ‌های duplicate
```bash
docker logs -f CONTAINER_ID | grep -E "(DUPLICATE|Checking for duplicate)"
```

### فقط لاگ‌های cache
```bash
docker logs -f CONTAINER_ID | grep -E "(Cached sent|Cache key)"
```

### فقط لاگ‌های AI
```bash
docker logs -f CONTAINER_ID | grep -E "(AI message|AI response)"
```

### فقط لاگ‌های Workflow
```bash
docker logs -f CONTAINER_ID | grep -E "(\[Workflow\]|\[Node\])"
```

### فقط لاگ‌های Support
```bash
docker logs -f CONTAINER_ID | grep "\[Support\]"
```

### ترکیبی - ببینید چه اتفاقی می‌افتد
```bash
docker logs -f CONTAINER_ID | grep -E "(📤|✅|⚠️|📝|🔍)"
```

## سناریوهای مختلف

### سناریو ۱: AI پیام می‌فرستد (بدون duplicate) ✅

**انتظار**:
```
1. ✅ AI message created: msg_123
2. ✅ AI response sent to Instagram
3. 📝 Cached sent message
4. 📝 Stored Instagram message_id
5. [بعد از 1-3 ثانیه]
6. 🔍 Checking for duplicate owner messages...
7. ⚠️⚠️⚠️ DUPLICATE DETECTED - BLOCKING ⚠️⚠️⚠️
8. >>> SKIPPING DUPLICATE CREATION <<<
```

### سناریو ۲: Support پیام می‌فرستد (بدون duplicate) ✅

**انتظار**:
```
1. 📤 [Support] Sending Instagram message...
2. ✅ [Support] Instagram message sent successfully
3. 📝 [Support] Cached sent message
4. [بعد از 1-3 ثانیه]
5. 🔍 Checking for duplicate owner messages...
6. ⚠️⚠️⚠️ DUPLICATE DETECTED - BLOCKING ⚠️⚠️⚠️
```

### سناریو ۳: Workflow پیام می‌فرستد (بدون duplicate) ✅

**انتظار**:
```
1. 📤 [Workflow] Sending Instagram message...
2. ✅ [Workflow] Instagram message sent successfully
3. 📝 [Workflow] Cached sent message
4. 📝 [Workflow] Stored Instagram message_id
5. [بعد از 1-3 ثانیه]
6. 🔍 Checking for duplicate owner messages...
7. ⚠️⚠️⚠️ DUPLICATE DETECTED - BLOCKING ⚠️⚠️⚠️
```

### سناریو ۴: از Instagram app مستقیم پیام می‌فرستید (ایجاد می‌شود) ✅

**انتظار**:
```
1. 🔍 Checking for duplicate owner messages...
2. Checking 0 recent messages  (یا پیامی پیدا نمی‌شود)
3. ✅ No duplicate found - this is a NEW owner message
4. ✅ Text message created: msg_NEW (type=support)
```

## اگر مشکل وجود دارد

### چک کردن cache
```python
from django.core.cache import cache
import hashlib

conversation_id = "YOUR_CONV_ID"
content = "YOUR_MESSAGE_CONTENT"

message_hash = hashlib.md5(f"{conversation_id}:{content}".encode()).hexdigest()
cache_key = f"instagram_sent_msg_{message_hash}"

print(f"Cache key: {cache_key}")
print(f"Cache value: {cache.get(cache_key)}")
```

### چک کردن metadata
```python
from message.models import Message

msg = Message.objects.get(id="YOUR_MSG_ID")
print(f"Type: {msg.type}")
print(f"is_ai_response: {msg.is_ai_response}")
print(f"Metadata: {msg.metadata}")
print(f"Has sent_from_app: {'sent_from_app' in (msg.metadata or {})}")
```

### چک کردن normalized content
```python
msg1 = Message.objects.get(id="MSG_1_ID")
msg2 = Message.objects.get(id="MSG_2_ID")

print(f"Content 1: '{msg1.content}'")
print(f"Content 2: '{msg2.content}'")
print(f"Normalized 1: '{msg1.content.strip()}'")
print(f"Normalized 2: '{msg2.content.strip()}'")
print(f"Are equal (normalized): {msg1.content.strip() == msg2.content.strip()}")
```

## نکات مهم

1. **لاگ‌ها به ترتیب زمانی هستند** - می‌توانید ببینید دقیقاً چه اتفاقی افتاده
2. **emoji ها کمک می‌کنند** - راحت‌تر می‌توانید مراحل مختلف را ببینید
3. **تگ‌های مختلف** - `[AI]`, `[Support]`, `[Workflow]`, `[Node]` کمک می‌کنند بفهمید کجا پیام ساخته شده
4. **Time difference** - وقتی duplicate پیدا می‌شود، می‌بینید چند ثانیه فاصله بوده

## کمک گرفتن

اگر هنوز مشکل دارید، لطفاً این‌ها را بفرستید:

1. **لاگ‌های کامل** از زمان ارسال تا دریافت webhook (حدود ۱۰ خط)
2. **ID پیام تکراری** (هر دو)
3. **نتیجه query های بالا**

من کمکتون می‌کنم! 💪

