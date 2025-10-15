# AI Platform Response Enhancement

## مسئله (Problem)

قبلاً سیستم AI پاسخ‌ها را تولید می‌کرد اما آن‌ها را به پلتفرم اصلی (تلگرام/اینستاگرام) ارسال نمی‌کرد. این یعنی:

- ✅ پیام مشتری دریافت می‌شد
- ✅ AI پاسخ تولید می‌کرد  
- ✅ پاسخ در دیتابیس ذخیره می‌شد
- ❌ **اما پاسخ به مشتری ارسال نمی‌شد!**

## راه‌حل (Solution)

### 1. شرط Status=Active ✅

کد قبلاً درست بود - فقط conversations با `status='active'` پردازش می‌شوند:

```python
# در message_integration.py
if conversation.status != 'active':
    logger.info(f"Skipping AI processing - status is '{conversation.status}', not 'active'")
    return False
```

### 2. ارسال خودکار به پلتفرم ✅ **جدید**

قابلیت جدید اضافه شد که بعد از ایجاد AI response، آن را به پلتفرم مناسب ارسال کند.

#### فایل‌های تغییر یافته:

**`src/AI_model/services/gemini_service.py`**

```python
def create_ai_message(self, conversation, ai_response: Dict[str, Any]):
    # ... ایجاد AI message
    
    # Send the AI response to the appropriate platform
    self._send_ai_response_to_platform(ai_message, conversation)
    
    return ai_message

def _send_ai_response_to_platform(self, ai_message, conversation):
    """ارسال پاسخ AI به پلتفرم مناسب (تلگرام/اینستاگرام)"""
    try:
        if conversation.source == 'telegram':
            self._send_telegram_response(ai_message, conversation)
        elif conversation.source == 'instagram':
            self._send_instagram_response(ai_message, conversation)
    except Exception as e:
        logger.error(f"Error sending AI response: {str(e)}")

def _send_telegram_response(self, ai_message, conversation):
    """ارسال پاسخ به تلگرام"""
    from message.services.telegram_service import TelegramService
    
    telegram_service = TelegramService.get_service_for_conversation(conversation)
    result = telegram_service.send_message_to_customer(
        conversation.customer, 
        ai_message.content
    )
    
    if result.get('success'):
        logger.info(f"✅ AI response sent to Telegram successfully")
    else:
        logger.error(f"❌ Failed to send AI response to Telegram")

def _send_instagram_response(self, ai_message, conversation):
    """ارسال پاسخ به اینستاگرام"""
    from message.services.instagram_service import InstagramService
    
    instagram_service = InstagramService.get_service_for_conversation(conversation)
    result = instagram_service.send_message_to_customer(
        conversation.customer, 
        ai_message.content
    )
```

## فلوی کامل (Complete Flow)

### قبل (Before):
```
1. مشتری پیام می‌فرستد (تلگرام/اینستاگرام)
2. Webhook دریافت می‌کند
3. Message و Conversation ایجاد می‌شود (status='active')
4. AI signal trigger می‌شود
5. AI پاسخ تولید می‌کند
6. پاسخ در دیتابیس ذخیره می‌شود
❌ 7. هیچ‌چیز به مشتری ارسال نمی‌شد!
```

### بعد (After):
```
1. مشتری پیام می‌فرستد (تلگرام/اینستاگرام)
2. Webhook دریافت می‌کند  
3. Message و Conversation ایجاد می‌شود (status='active')
4. AI signal trigger می‌شود
5. AI پاسخ تولید می‌کند
6. پاسخ در دیتابیس ذخیره می‌شود
✅ 7. پاسخ به همان پلتفرم ارسال می‌شود!
```

## سرویس‌های استفاده شده

### TelegramService
```python
# قابلیت‌های موجود:
- send_message(chat_id, text)
- send_message_to_customer(customer, text)  
- get_service_for_conversation(conversation)
```

### InstagramService  
```python
# قابلیت‌های موجود:
- send_message(recipient_id, text)
- send_message_to_customer(customer, text)
- get_service_for_conversation(conversation)
```

## تست

### دستور تست:
```bash
docker exec -it django_app python manage.py test_ai_platform_response
```

### تست دستی:
```bash
docker exec -it django_app python manage.py shell
```

```python
# تست با یک پیام واقعی
from message.models import Message
from AI_model.services.message_integration import MessageSystemIntegration

# پیدا کردن پیام اخیر
msg = Message.objects.filter(
    type='customer', 
    conversation__status='active'
).order_by('-created_at').first()

print(f"Testing message: {msg.content}")
print(f"Platform: {msg.conversation.source}")

# ریست کردن وضعیت
msg.is_answered = False
msg.save()

# تست AI processing
integration = MessageSystemIntegration(msg.conversation.user)
result = integration.process_new_customer_message(msg)

print(f"Result: {result}")
# باید نتیجه موفق باشد و پیام به پلتفرم ارسال شود
```

## مزایا

### 1. **پاسخگویی کامل خودکار**
- مشتری پیام می‌فرستد → فوراً پاسخ دریافت می‌کند
- نیازی به دخالت انسان نیست

### 2. **پشتیبانی از همه پلتفرم‌ها**
- ✅ تلگرام: پاسخ به همان چت ارسال می‌شود
- ✅ اینستاگرام: پاسخ به همان DM ارسال می‌شود

### 3. **مدیریت خطا**
- اگر ارسال ناموفق باشد، error log می‌شود
- AI response همچنان در دیتابیس ذخیره می‌ماند

### 4. **کنترل Status**
- فقط conversations با `status='active'` پردازش می‌شوند
- سایر وضعیت‌ها (`support_active`, `marketing_active`, `closed`) نادیده گرفته می‌شوند

## نکات مهم

### 1. **Celery Worker باید کار کند**
```bash
# چک کردن worker:
docker logs celery_worker --tail 20

# باید نشان دهد:
# Connected to redis://redis:6379/0
# celery@container ready.
```

### 2. **AI Prompts باید تنظیم شده باشند**
```python
# هر user باید AI prompts داشته باشد
from settings.models import AIPrompts
prompts = AIPrompts.objects.filter(user=user).first()
# باید manual_prompt و auto_prompt داشته باشد
```

### 3. **Channel Configuration**
- تلگرام: `TelegramChannel` با `bot_token` 
- اینستاگرام: `InstagramChannel` با `access_token`

## مثال Log های موفق

```
INFO AI response generated for user: سلام! چگونه می‌توانم کمکتان کنم؟
INFO AI message created: abc123 for conversation xyz789  
INFO ✅ AI response sent to Telegram successfully: message abc123
```

یا برای اینستاگرام:
```
INFO AI response generated for user: Hello! How can I help you?
INFO AI message created: def456 for conversation xyz789
INFO ✅ AI response sent to Instagram successfully: message def456  
```

## خلاصه

حالا سیستم **کاملاً خودکار** است:
- پیام دریافت → AI پردازش → پاسخ ارسال ✅
- تلگرام → تلگرام ✅  
- اینستاگرام → اینستاگرام ✅
- فقط `status='active'` ✅