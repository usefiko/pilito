# 🤖 سیستم خودکار مدیریت توکن‌های اینستاگرام

## خلاصه

این سیستم به طور **کاملاً خودکار** توکن‌های اینستاگرام را مدیریت می‌کند و هیچ دخالت دستی نیاز ندارد.

### 🎯 ویژگی‌های کلیدی:

- ✅ **راه‌اندازی یک‌بار**: فقط یک بار اجرا کنید، بقیه خودکار
- ✅ **رفرش خودکار**: هر روز ساعت 3 صبح
- ✅ **رفرش اضطراری**: هر 6 ساعت برای توکن‌های نزدیک انقضا  
- ✅ **بازیابی هوشمند**: در زمان ارسال پیام، خطاها خودکار برطرف می‌شوند
- ✅ **مانیتورینگ کامل**: لاگ‌های جامع و قابل رؤیت

---

## 🚀 راه‌اندازی سریع

### گام 1: نصب و راه‌اندازی
```bash
# اجرای اسکریپت خودکار (فقط یک بار)
./run_token_refresh_system.sh
```

**همین!** 🎉 سیستم حالا کاملاً خودکار کار می‌کند.

### گام 2: بررسی وضعیت (اختیاری)
```bash
# بررسی وضعیت توکن‌ها
python src/manage.py convert_instagram_tokens --check-only
```

---

## 📅 زمان‌بندی خودکار

سیستم بر اساس این برنامه کار می‌کند:

### 🕒 روزانه ساعت 3:00 صبح
- بررسی تمام توکن‌ها
- رفرش توکن‌هایی که ظرف 7 روز منقضی می‌شوند
- گزارش نتایج در لاگ

### ⚡ هر 6 ساعت (اضطراری)
- بررسی فوری توکن‌ها
- رفرش توکن‌هایی که ظرف 1 روز منقضی می‌شوند
- مناسب برای شرایط اضطراری

### 🔄 در زمان ارسال پیام
- اگر توکن منقضی شده، خودکار رفرش می‌شود
- پیام مجدداً ارسال می‌شود
- کاربر متوجه مشکل نمی‌شود

---

## 📊 نظارت و مانیتورینگ

### لاگ‌های سیستم:
```bash
# لاگ Worker (عملیات رفرش)
tail -f logs/celery_worker.log

# لاگ Beat (زمان‌بندی)
tail -f logs/celery_beat.log

# لاگ Redis
tail -f logs/redis.log
```

### Django Admin Panel:
```
http://localhost:8000/admin/django_celery_beat/
```
- مشاهده وضعیت Periodic Tasks
- فعال/غیرفعال کردن زمان‌بندی‌ها
- تاریخچه اجراها

### نظارت Realtime:
```bash
# مانیتور Celery (نصب Flower لازم)
pip install flower
celery -A core flower

# دسترسی: http://localhost:5555
```

---

## 🛠️ مدیریت سیستم

### شروع سیستم:
```bash
./run_token_refresh_system.sh
```

### توقف سیستم:
```bash
./stop_token_system.sh
```

### ری‌استارت:
```bash
./stop_token_system.sh
./run_token_refresh_system.sh
```

### تست دستی:
```bash
# تست فوری (بدون انتظار برای زمان‌بندی)
cd src
python manage.py shell -c "
from message.tasks import auto_refresh_instagram_tokens
result = auto_refresh_instagram_tokens.delay()
print(f'Task ID: {result.id}')
"
```

---

## 🔧 تنظیمات پیشرفته

### تغییر زمان‌بندی:

فایل: `src/core/settings/common.py`

```python
CELERY_BEAT_SCHEDULE = {
    'auto-refresh-instagram-tokens': {
        'task': 'message.tasks.auto_refresh_instagram_tokens',
        'schedule': crontab(hour=3, minute=0),  # تغییر ساعت
        'kwargs': {'days_before_expiry': 7},    # تغییر آستانه روز
    },
}
```

### تغییر آستانه رفرش:

```python
# رفرش توکن‌هایی که ظرف 10 روز منقضی می‌شوند
{'days_before_expiry': 10}
```

### تنظیم لاگ‌ها:

فایل: `src/core/settings/common.py`

```python
LOGGING = {
    'version': 1,
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': 'logs/instagram_tokens.log',
        },
    },
    'loggers': {
        'message.tasks': {
            'handlers': ['file'],
            'level': 'INFO',
        },
    },
}
```

---

## 🚨 عیب‌یابی

### مشکلات رایج:

#### 1. سیستم اجرا نمی‌شود
```bash
# بررسی Redis
redis-cli ping
# باید پاسخ "PONG" برگرداند

# بررسی virtualenv
which python
# باید path صحیح نشان دهد
```

#### 2. توکن‌ها رفرش نمی‌شوند
```bash
# بررسی لاگ‌ها
tail -n 50 logs/celery_worker.log

# تست دستی task
cd src
python manage.py shell -c "
from message.tasks import auto_refresh_instagram_tokens
print(auto_refresh_instagram_tokens.delay().get())
"
```

#### 3. Periodic Tasks اجرا نمی‌شوند
```bash
# بررسی Beat
tail -n 20 logs/celery_beat.log

# بررسی Django Admin
# http://localhost:8000/admin/django_celery_beat/periodictask/
```

#### 4. Redis مشکل دارد
```bash
# راه‌اندازی مجدد Redis
redis-cli shutdown
redis-server --daemonize yes
```

### لاگ‌های مهم:

**موفقیت رفرش:**
```
✅ Successfully refreshed token for channel username
📅 username: New token expires in 60 days, 0 hours
```

**خطای رفرش:**
```
❌ Failed to refresh token for channel username
   All token refresh methods failed
```

**شروع task:**
```
🔄 Starting automatic Instagram token refresh
🔍 Found X connected Instagram channels
```

---

## 💻 Production Deployment

### Systemd Service (Linux):

ایجاد فایل `/etc/systemd/system/celery.service`:

```ini
[Unit]
Description=Celery Service
After=network.target

[Service]
Type=forking
User=your-app-user
Group=your-app-group
EnvironmentFile=/path/to/your/.env
WorkingDirectory=/path/to/your/project/src
ExecStart=/path/to/your/venv/bin/celery multi start worker1 -A core -Q instagram_tokens --pidfile=/var/run/celery/%n.pid --logfile=/var/log/celery/%n%I.log --loglevel=INFO
ExecStop=/path/to/your/venv/bin/celery multi stopwait worker1 --pidfile=/var/run/celery/%n.pid
ExecReload=/path/to/your/venv/bin/celery multi restart worker1 -A core -Q instagram_tokens --pidfile=/var/run/celery/%n.pid --logfile=/var/log/celery/%n%I.log --loglevel=INFO

[Install]
WantedBy=multi-user.target
```

ایجاد فایل `/etc/systemd/system/celerybeat.service`:

```ini
[Unit]
Description=Celery Beat Service
After=network.target

[Service]
Type=simple
User=your-app-user
Group=your-app-group
EnvironmentFile=/path/to/your/.env
WorkingDirectory=/path/to/your/project/src
ExecStart=/path/to/your/venv/bin/celery -A core beat --loglevel=INFO
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

فعال‌سازی:
```bash
sudo systemctl enable celery celerybeat
sudo systemctl start celery celerybeat
```

### Docker Compose:

```yaml
version: '3'
services:
  redis:
    image: redis:alpine
    
  celery_worker:
    build: .
    command: celery -A core worker -Q instagram_tokens --loglevel=info
    depends_on:
      - redis
    environment:
      - REDIS_URL=redis://redis:6379/0
      
  celery_beat:
    build: .
    command: celery -A core beat --loglevel=info
    depends_on:
      - redis
    environment:
      - REDIS_URL=redis://redis:6379/0
```

---

## 📈 آمار و گزارش‌گیری

### دستورات گزارش‌گیری:

```bash
# تعداد توکن‌های فعال
python src/manage.py shell -c "
from settings.models import InstagramChannel
print(f'Active channels: {InstagramChannel.objects.filter(is_connect=True).count()}')
"

# آخرین رفرش‌ها
python src/manage.py shell -c "
from django_celery_beat.models import PeriodicTask
from datetime import datetime
tasks = PeriodicTask.objects.filter(enabled=True)
for task in tasks:
    print(f'{task.name}: Last run = {task.last_run_at}')
"

# وضعیت انقضا توکن‌ها
python src/manage.py convert_instagram_tokens --check-only
```

### Monitoring Tools:

1. **Flower** (Web UI برای Celery)
2. **Prometheus + Grafana** (Metrics)
3. **Sentry** (Error tracking)
4. **Django Admin** (Task management)

---

## ✅ خلاصه

پس از اجرای `./run_token_refresh_system.sh` یک بار:

✅ **توکن‌ها خودکار رفرش می‌شوند**  
✅ **هیچ دخالت دستی لازم نیست**  
✅ **خطاها خودکار برطرف می‌شوند**  
✅ **سیستم 24/7 کار می‌کند**  

### 🎯 نتیجه:
**کاربران دیگر نیازی به reconnect ندارند و سیستم بدون وقفه کار می‌کند! 🚀**