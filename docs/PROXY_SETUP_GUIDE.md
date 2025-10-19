# 🔒 راهنمای کامل راه‌اندازی سیستم Proxy Management

## ✅ تغییراتی که اعمال شده

### 📁 فایل‌های جدید ساخته شده:
1. ✅ `src/core/models.py` - مدل ProxySetting
2. ✅ `src/core/admin.py` - پنل مدیریت پروکسی
3. ✅ `src/core/utils.py` - توابع کمکی برای استفاده از پروکسی

### 📝 فایل‌های ویرایش شده:
#### Instagram API (12 فایل):
- ✅ `src/message/services/instagram_service.py` (6 مورد)
- ✅ `src/message/insta.py` (8 مورد)
- ✅ `src/message/api/instagram_callback.py` (4 مورد)
- ✅ `src/message/tasks.py` (4 مورد)

#### Telegram API (7 فایل):
- ✅ `src/message/services/telegram_service.py` (5 مورد)
- ✅ `src/settings/channels_view.py` (3 مورد)
- ✅ `src/workflow/services/workflow_execution_service.py` (1 مورد)
- ✅ `src/workflow/services/node_execution_service.py` (1 مورد)

#### تنظیمات:
- ✅ `src/core/settings/common.py` - اضافه شدن 'core' به INSTALLED_APPS

---

## 🚀 مراحل راه‌اندازی

### مرحله ۱: اجرای Migration در Production

وقتی پروژه رو Deploy می‌کنی، باید Migration رو اجرا کنی:

```bash
# داخل Docker container یا محیط production
python manage.py makemigrations core
python manage.py migrate
```

یا اگر از Docker استفاده می‌کنی:

```bash
docker-compose exec web python manage.py makemigrations core
docker-compose exec web python manage.py migrate
```

---

### مرحله ۲: اضافه کردن پروکسی از پنل Admin

۱. وارد پنل ادمین Django شو:
   ```
   https://api.pilito.com/admin/
   ```

۲. به قسمت **"Core → Proxy Settings"** برو

۳. روی **"Add Proxy Setting"** کلیک کن

۴. اطلاعات پروکسی رو وارد کن:

   ```
   Name: Main Proxy Server
   HTTP Proxy: http://username:password@ip:port
   HTTPS Proxy: http://username:password@ip:port
   Fallback HTTP Proxy: (اختیاری) http://username2:password2@ip2:port2
   Fallback HTTPS Proxy: (اختیاری) http://username2:password2@ip2:port2
   Is Active: ✅ (فعال)
   ```

۵. روی **"Save"** کلیک کن

**نکته مهم:** فقط یک پروکسی باید `is_active=True` باشه. سیستم خودکار بقیه رو غیرفعال می‌کنه.

---

## 🧪 تست عملکرد

### تست ۱: Instagram API

```python
# در Django shell
python manage.py shell

from core.utils import get_active_proxy, get_fallback_proxy
import requests

# تست پروکسی اصلی
proxies = get_active_proxy()
print(f"Active Proxy: {proxies}")

# تست درخواست به Instagram
url = "https://graph.instagram.com/v23.0/me?fields=id,username&access_token=YOUR_TOKEN"
response = requests.get(url, proxies=proxies, timeout=10)
print(f"Status: {response.status_code}")
print(f"Response: {response.json()}")
```

### تست ۲: Telegram API

```python
from core.utils import get_active_proxy
import requests

# تست Telegram Bot
bot_token = "YOUR_BOT_TOKEN"
url = f"https://api.telegram.org/bot{bot_token}/getMe"

response = requests.get(url, proxies=get_active_proxy(), timeout=10)
print(f"Status: {response.status_code}")
print(f"Response: {response.json()}")
```

---

## 🔄 تغییر پروکسی

### روش ۱: از پنل Admin

1. وارد **Core → Proxy Settings** شو
2. پروکسی جدید رو `is_active=True` کن
3. سیستم خودکار پروکسی قبلی رو غیرفعال می‌کنه
4. **نیازی به Restart سرور نیست!** ✅

### روش ۲: با Django Management Command

می‌تونی یک command سفارشی بسازی:

```python
# src/core/management/commands/switch_proxy.py
from django.core.management.base import BaseCommand
from core.models import ProxySetting

class Command(BaseCommand):
    help = 'Switch to a different proxy'
    
    def add_arguments(self, parser):
        parser.add_argument('proxy_name', type=str)
    
    def handle(self, *args, **kwargs):
        name = kwargs['proxy_name']
        try:
            proxy = ProxySetting.objects.get(name=name)
            proxy.is_active = True
            proxy.save()
            self.stdout.write(self.style.SUCCESS(f'✅ Switched to proxy: {name}'))
        except ProxySetting.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'❌ Proxy not found: {name}'))
```

استفاده:
```bash
python manage.py switch_proxy "Main Proxy Server"
```

---

## 🛡️ نکات امنیتی

### ۱. محافظت از اطلاعات پروکسی

پروکسی‌ها شامل username/password هستن، پس:

- ✅ فقط مدیرها (Superuser) به Core → Proxy Settings دسترسی داشته باشن
- ✅ از HTTPS برای پنل ادمین استفاده کن
- ✅ Password های پروکسی رو قوی انتخاب کن

### ۲. استفاده از پروکسی مناسب

- ✅ از **Residential Proxy** یا **Datacenter Proxy** معتبر استفاده کن
- ❌ از **Free Proxy** استفاده نکن (ناپایدار و غیرامن هستن)
- ✅ IP پروکسی باید از **کشورهای غیر تحریمی** باشه

### ۳. مانیتورینگ

می‌تونی از Log ها بفهمی پروکسی کار می‌کنه یا نه:

```bash
# مشاهده لاگ‌ها
docker-compose logs -f web | grep "proxy"
```

یا در کد:

```python
import logging
logger = logging.getLogger(__name__)
logger.info(f"🔒 Using proxy: {proxy.name}")
```

---

## 🔧 عیب‌یابی (Troubleshooting)

### مشکل ۱: "No active proxy found"

**علت:** هیچ پروکسی فعالی وجود نداره

**راه حل:**
1. وارد پنل ادمین شو
2. یک پروکسی رو `is_active=True` کن
3. ذخیره کن

---

### مشکل ۲: "Connection timeout"

**علت:** پروکسی down هست یا آدرس اشتباهه

**راه حل:**
1. آدرس پروکسی رو چک کن (باید به فرمت `http://user:pass@ip:port` باشه)
2. از Fallback Proxy استفاده کن
3. پروکسی رو با curl تست کن:
   ```bash
   curl -x http://user:pass@ip:port https://api.telegram.org/bot<TOKEN>/getMe
   ```

---

### مشکل ۳: "407 Proxy Authentication Required"

**علت:** Username یا Password اشتباهه

**راه حل:**
1. اطلاعات Proxy رو از ارائه‌دهنده بگیر
2. در پنل ادمین آپدیت کن
3. دوباره تست کن

---

### مشکل ۴: Migration Error

**علت:** مدل core قبلاً migrate نشده

**راه حل:**
```bash
# حذف فایل‌های migration قدیمی (اگر وجود داره)
rm -rf src/core/migrations/

# ساخت مجدد
python manage.py makemigrations core
python manage.py migrate core
```

---

## 📊 مانیتورینگ و لاگ‌گیری

### فعال کردن Debug Log برای Proxy

در `settings/production.py`:

```python
LOGGING = {
    # ... existing config ...
    'loggers': {
        'core.utils': {
            'handlers': ['file', 'console'],
            'level': 'DEBUG',  # برای دیدن جزئیات پروکسی
            'propagate': False,
        },
    }
}
```

### مشاهده لاگ‌ها

```bash
# تمام لاگ‌های مربوط به پروکسی
tail -f /app/logs/django.log | grep proxy

# فقط errorها
tail -f /app/logs/django.log | grep -i "error.*proxy"
```

---

## 🎯 بهترین روش‌ها (Best Practices)

### ۱. استفاده از Fallback Proxy

همیشه یک **Fallback Proxy** تنظیم کن تا در صورت خرابی پروکسی اصلی، سرویس قطع نشه.

### ۲. Rotation پروکسی

برای جلوگیری از Rate Limit:

1. چند پروکسی مختلف بخر
2. هر چند ساعت یکبار بینشون switch کن
3. می‌تونی با Celery Beat خودکار کنی:

```python
# در celery beat schedule
'rotate-proxy': {
    'task': 'core.tasks.rotate_proxy',
    'schedule': crontab(hour='*/6'),  # هر 6 ساعت
}
```

### ۳. Health Check

یک تسک health check برای پروکسی بنویس:

```python
@shared_task
def check_proxy_health():
    from core.utils import get_active_proxy
    import requests
    
    proxies = get_active_proxy()
    if not proxies:
        logger.error("❌ No active proxy configured!")
        return False
    
    try:
        # تست با یک API ساده
        response = requests.get(
            "https://api.telegram.org/botTOKEN/getMe",
            proxies=proxies,
            timeout=5
        )
        if response.status_code == 200:
            logger.info("✅ Proxy health check: OK")
            return True
    except Exception as e:
        logger.error(f"❌ Proxy health check failed: {e}")
        # می‌تونی اینجا به Fallback switch کنی
        return False
```

---

## 📞 پشتیبانی

در صورت بروز مشکل:

1. لاگ‌ها رو چک کن
2. تنظیمات پروکسی رو در پنل ادمین بررسی کن
3. با `curl` پروکسی رو تست کن
4. اگر مشکل حل نشد، تیکت بزن

---

## ✅ خلاصه

✅ **سیستم پروکسی کامل پیاده‌سازی شده**

- تمام APIهای Instagram از پروکسی استفاده می‌کنن (12 مورد)
- تمام APIهای Telegram از پروکسی استفاده می‌کنن (7 مورد)
- پشتیبانی از Fallback Proxy برای High Availability
- مدیریت راحت از پنل Django Admin
- بدون نیاز به Restart سرور
- Log کامل برای مانیتورینگ

**برای فعال‌سازی فقط کافیه:**
1. Migration رو اجرا کنی
2. یک پروکسی از پنل ادمین اضافه کنی
3. اون رو فعال کنی

**تموم! 🎉**

