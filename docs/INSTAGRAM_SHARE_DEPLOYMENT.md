# Instagram Share Feature - Deployment Guide

## ✅ تغییرات اعمال شده

### 1️⃣ Models (`src/message/models.py`)
- ✅ اضافه شد: `('share', 'Post/Reel Share')` به `MESSAGE_TYPE_CHOICES`

### 2️⃣ Instagram Webhook (`src/message/insta.py`)
- ✅ تشخیص `attach_type == 'share'`
- ✅ استخراج caption/title/subtitle/url از payload
- ✅ ساخت Message با `message_type='share'` و `processing_status='completed'`
- ✅ فقط WebSocket notify (بدون AI trigger)

### 3️⃣ AI Signals (`src/AI_model/signals.py`)
- ✅ برای share: cache set + timeout schedule + return (no AI)
- ✅ برای text بعد از share: combine content + AI trigger
- ✅ منطق فقط برای Instagram + share

### 4️⃣ Timeout Task (`src/message/tasks.py`)
- ✅ `process_pending_share_timeout`: clear cache بدون AI trigger
- ✅ جواب نده روی share تنها

### 5️⃣ Anti-Hallucination Rules (`src/settings/models.py`)
- ✅ اضافه شد: راهنمای Instagram share
- ✅ هشدار: فقط caption را می‌بینی، نه تصویر/ویدیو

### 6️⃣ Tests (`src/message/tests/test_instagram_share.py`)
- ✅ 5 تست برای سناریوهای مختلف

---

## 🚀 مراحل Deploy

### مرحله 1: Migrations (روی سرور)

```bash
# SSH به سرور
ssh root@185.164.72.165

# ورود به دایرکتوری پروژه
cd /root/pilito

# Pull تغییرات
git pull origin main

# Activate virtual environment (اگر دارید)
source venv/bin/activate  # یا هر venv دیگری

# ساخت migrations
cd src
python manage.py makemigrations message

# اعمال migrations
python manage.py migrate

# بررسی migration
python manage.py showmigrations message
```

### مرحله 2: Restart Services

```bash
# Restart Docker services (اگر از Docker استفاده می‌کنید)
docker stack deploy -c docker-compose.swarm.yml pilito

# یا restart Gunicorn/Celery به صورت دستی:
systemctl restart gunicorn
systemctl restart celery-worker
systemctl restart celery-beat
```

### مرحله 3: بررسی لاگ‌ها

```bash
# Celery worker logs
docker service logs pilito_celery_worker --tail 50 --follow

# Web logs
docker service logs pilito_web --tail 50 --follow

# یا:
tail -f /path/to/logs/celery.log
tail -f /path/to/logs/django.log
```

---

## 🧪 تست دستی

### سناریو 1: Share → Text (اصلی)

1. **در Instagram**: به عنوان کاربر یک پست/ریلز share کنید به پیج
2. **انتظار**: پیام در پنل ذخیره می‌شود، AI جواب نمی‌دهد
3. **در Instagram**: سوال بپرسید: "این لباس چقدره؟"
4. **انتظار**: 
   - Content باید ترکیب share + سوال باشد
   - AI باید جواب contextual بدهد

**لاگ‌های مورد انتظار:**
```
⏳ Instagram share detected - waiting for follow-up question
   Message ID: xxx
   Caption preview: ...
   Timeout: 120s

✅ Combined share + question for AI processing
   Share ID: xxx
   Question ID: yyy
   Combined content length: 250 chars
```

### سناریو 2: Share تنها

1. **در Instagram**: فقط یک پست share کنید
2. **صبر کنید**: 2 دقیقه
3. **انتظار**: هیچ پیام AI جدید ساخته نشود

**لاگ مورد انتظار:**
```
⏰ Timeout for share xxx - no question received, cleared cache (no AI response)
```

### سناریو 3: Text عادی

1. **در Instagram**: یک پیام text بفرستید: "سلام"
2. **انتظار**: رفتار عادی، AI مثل قبل جواب بدهد

---

## 🔍 نکات مهم

### 1. Cache Configuration
مطمئن شوید Redis/Cache به درستی کار می‌کند:

```bash
# تست cache
python manage.py shell
>>> from django.core.cache import cache
>>> cache.set('test', 'value', timeout=10)
>>> cache.get('test')
'value'
```

### 2. Celery Broker
مطمئن شوید Celery به درستی با broker ارتباط دارد:

```bash
# بررسی Celery worker
celery -A core inspect active

# بررسی scheduled tasks
celery -A core inspect scheduled
```

### 3. Message Type Validation
اگر validation error گرفتید، مطمئن شوید migration اجرا شده:

```bash
python manage.py migrate message --fake-initial  # فقط در صورت نیاز
```

---

## 🐛 Troubleshooting

### مشکل: Migration error
```bash
# پاک کردن migrations cache
python manage.py migrate --fake message zero
python manage.py migrate message
```

### مشکل: Celery task اجرا نمی‌شود
```bash
# بررسی Celery logs
docker service logs pilito_celery_worker --tail 100

# چک کردن routing
python manage.py shell
>>> from message.tasks import process_pending_share_timeout
>>> process_pending_share_timeout.delay('test_conv_id')
```

### مشکل: Share تشخیص داده نمی‌شود
- بررسی کنید webhook از Instagram به درستی payload می‌فرستد
- لاگ insta.py را چک کنید: "📱 Instagram share received"

### مشکل: Content combine نمی‌شود
- بررسی cache: `cache.get('pending_share_xxx')`
- لاگ signals.py را چک کنید: "✅ Combined share + question"

---

## 📊 Monitoring

### Metrics to Watch

1. **Share Messages Created**: تعداد پیام‌های share ساخته شده
2. **Timeout Tasks Executed**: تعداد timeout task اجرا شده
3. **Combined Messages**: تعداد پیام‌های ترکیب شده
4. **Cache Hit Rate**: درصد پیدا شدن pending share در cache

### Query Examples

```python
# تعداد share messages
from message.models import Message
Message.objects.filter(message_type='share').count()

# تعداد combined messages (شامل CONTEXT)
Message.objects.filter(
    message_type='text',
    content__contains='[CONTEXT: پست/ریلز'
).count()
```

---

## ✅ Checklist نهایی

- [ ] Git pull شده
- [ ] Migrations ساخته و اجرا شده
- [ ] Services restart شده
- [ ] لاگ‌ها بررسی شده (no errors)
- [ ] تست سناریو 1 انجام شده
- [ ] تست سناریو 2 انجام شده
- [ ] تست سناریو 3 انجام شده
- [ ] Cache کار می‌کند
- [ ] Celery tasks schedule می‌شوند

---

## 📝 Notes

- این feature فقط برای Instagram است
- Image/Voice رفتار قبلی را دارند
- Telegram/Website تحت تأثیر نیستند
- Share تنها جواب نمی‌گیرد (طراحی)
- فقط آخرین share با text combine می‌شود

