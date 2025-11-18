# راه‌حل نهایی - جلوگیری از تکرار پیام‌های Workflow

## مشکل جدید
پیام‌های ارسالی از طریق **Workflow Nodes** هم تکراری می‌شدند! 

### چرا؟
Workflow ها هم مثل AI از `InstagramService` استفاده می‌کنند و پیام به Instagram می‌فرستند، اما:
- ✅ پیام در دیتابیس ذخیره می‌شد
- ✅ به Instagram ارسال می‌شد
- ❌ اما cache/metadata تنظیم نمی‌شد
- ❌ وقتی webhook برمی‌گشت، تکراری ایجاد می‌شد!

## راه‌حل

به **همه جاهایی** که workflow از InstagramService استفاده می‌کرد، همان منطق cache و metadata را اضافه کردیم.

### فایل‌های تغییر یافته

#### ۱. `workflow/services/workflow_execution_service.py`

در method `_execute_send_message`:
```python
elif source == 'instagram':
    svc = InstagramService.get_service_for_conversation(conversation)
    if svc:
        send_res = svc.send_message_to_customer(customer, message_content)
        
        # ✅ Mark message as sent to prevent webhook duplicate
        if send_res.get('success'):
            # Cache it
            message_hash = hashlib.md5(f"{conversation.id}:{message_content}".encode()).hexdigest()
            cache_key = f"instagram_sent_msg_{message_hash}"
            cache.set(cache_key, True, timeout=60)
            logger.info(f"📝 [Workflow] Cached sent message")
            
            # Update metadata
            if send_res.get('message_id') and message:
                message.metadata = message.metadata or {}
                message.metadata['external_message_id'] = str(send_res.get('message_id'))
                message.metadata['sent_from_app'] = True
                message.save(update_fields=['metadata'])
                logger.info(f"📝 [Workflow] Stored Instagram message_id in metadata")
```

#### ۲. `workflow/services/node_execution_service.py`

در **همه جاهای** استفاده از InstagramService (۳ مورد):
```python
elif getattr(customer, 'source', '') == 'instagram':
    svc = InstagramService.get_service_for_conversation(conversation)
    if svc:
        send_res = svc.send_message_to_customer(customer, msg.content)
        
        # ✅ Mark message as sent to prevent webhook duplicate
        if send_res.get('success'):
            message_hash = hashlib.md5(f"{conversation.id}:{msg.content}".encode()).hexdigest()
            cache_key = f"instagram_sent_msg_{message_hash}"
            cache.set(cache_key, True, timeout=60)
            logger.info(f"📝 [Node] Cached sent message")
            
            if send_res.get('message_id') and msg:
                msg.metadata = msg.metadata or {}
                msg.metadata['external_message_id'] = str(send_res.get('message_id'))
                msg.metadata['sent_from_app'] = True
                msg.save(update_fields=['metadata'])
                logger.info(f"📝 [Node] Stored Instagram message_id")
```

## چگونه کار می‌کند؟

### وقتی Workflow پیام می‌فرستد:
```
1. ✅ Message در دیتابیس ایجاد می‌شود (type='marketing' یا 'support')
2. ✅ پیام به Instagram ارسال می‌شود
3. ✅ message_hash محاسبه و در cache ذخیره می‌شود
4. ✅ metadata['sent_from_app'] = True تنظیم می‌شود
5. ✅ لاگ: "📝 [Workflow] Cached sent message"
```

### وقتی Instagram webhook برمی‌گردد:
```
1. 📥 Webhook دریافت می‌شود
2. 🔍 محتوا normalize می‌شود (.strip())
3. 🔍 پیام‌های اخیر چک می‌شوند
4. ⚠️ پیام Workflow پیدا می‌شود (محتوای normalized یکسان است)
5. ⚠️ لاگ: "DUPLICATE DETECTED - BLOCKING"
6. ✅ ایجاد تکراری جلوگیری می‌شود!
```

## تست کردن

### مرحله ۱: یک Workflow تنظیم کنید
- یک workflow بسازید که یک پیام به مشتری بفرستد
- Trigger کنید

### مرحله ۲: لاگ‌ها را ببینید
```bash
docker logs -f CONTAINER_ID | grep -E "(Workflow|Node|DUPLICATE)"
```

**باید ببینید**:
```
📝 [Workflow] Cached sent message to prevent webhook duplicate
📝 [Workflow] Stored Instagram message_id in metadata
...
🔍 Checking for duplicate owner messages...
⚠️⚠️⚠️ DUPLICATE DETECTED - BLOCKING ⚠️⚠️⚠️
   Existing message type: marketing
   >>> SKIPPING DUPLICATE CREATION <<<
```

### مرحله ۳: چک کردن دیتابیس
```python
from message.models import Message
from django.utils import timezone
from datetime import timedelta

# پیام‌های ۵ دقیقه اخیر
recent = Message.objects.filter(
    type='marketing',
    created_at__gte=timezone.now() - timedelta(minutes=5)
).values('id', 'content', 'metadata', 'created_at')

for msg in recent:
    print(msg)
    print(f"Has sent_from_app flag: {'sent_from_app' in (msg['metadata'] or {})}")
```

## خلاصه تغییرات

| جایی که تغییر کرد | چه تغییری | چرا؟ |
|------------------|-----------|------|
| `workflow_execution_service.py` | اضافه کردن cache + metadata بعد از ارسال Instagram | جلوگیری از duplicate در workflow |
| `node_execution_service.py` | اضافه کردن cache + metadata بعد از ارسال Instagram (۳ مورد) | جلوگیری از duplicate در node execution |
| همه موارد | لاگ `📝 [Workflow]` یا `📝 [Node]` | debug آسان |

## نتیجه

حالا **هیچ پیامی تکراری نخواهد شد**، چه:
- ✅ پیام AI
- ✅ پیام Support (دستی)
- ✅ پیام Marketing (Workflow)
- ✅ پیام از Node های Workflow

همه پیام‌ها cache و metadata دارند، و webhook duplicate ها را detect می‌کند! 🎉

---

## اگر هنوز مشکل داشتید

لاگ‌ها را برای من بفرستید:
```bash
docker logs CONTAINER | grep -E "(Workflow|Node|DUPLICATE|Cached)" | tail -50
```

و نتیجه این query را:
```python
Message.objects.filter(
    created_at__gte=timezone.now() - timedelta(minutes=5)
).values('id', 'type', 'content', 'metadata', 'created_at').order_by('-created_at')[:10]
```

