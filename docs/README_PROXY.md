# 🌐 Proxy Management System for Django (Instagram & Telegram Support)

## 🎯 هدف
اضافه کردن امکان مدیریت و تغییر Proxy (برای Instagram و Telegram API) از طریق پنل Django Admin بدون نیاز به تغییر `.env` یا ری‌استارت سرور.

---

## 🧱 مرحله ۱: ایجاد مدل ProxySetting

📍 مسیر: `core/models.py`

```python
from django.db import models

class ProxySetting(models.Model):
    name = models.CharField(max_length=50, unique=True)
    http_proxy = models.CharField(max_length=255)
    https_proxy = models.CharField(max_length=255)
    fallback_http_proxy = models.CharField(max_length=255, blank=True, null=True)
    fallback_https_proxy = models.CharField(max_length=255, blank=True, null=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} ({'Active' if self.is_active else 'Inactive'})"
```

---

## 🧰 مرحله ۲: اضافه کردن مدل به Admin Panel

📍 مسیر: `core/admin.py`

```python
from django.contrib import admin
from .models import ProxySetting

@admin.register(ProxySetting)
class ProxySettingAdmin(admin.ModelAdmin):
    list_display = ('name', 'http_proxy', 'https_proxy', 'fallback_http_proxy', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name', 'http_proxy', 'https_proxy')
```

✅ حالا می‌تونی از طریق پنل ادمین Proxy اضافه / ویرایش / فعال و غیرفعال کنی.

---

## 🧠 مرحله ۳: ساخت Utility برای گرفتن Proxy فعال

📍 مسیر: `core/utils.py`

```python
from .models import ProxySetting

def get_active_proxy():
    proxy = ProxySetting.objects.filter(is_active=True).first()
    if proxy:
        return {
            "http": proxy.http_proxy,
            "https": proxy.https_proxy
        }
    return {}

def get_fallback_proxy():
    proxy = ProxySetting.objects.filter(is_active=True).first()
    if proxy and proxy.fallback_http_proxy:
        return {
            "http": proxy.fallback_http_proxy,
            "https": proxy.fallback_https_proxy
        }
    return {}
```

---

## 🌐 مرحله ۴: استفاده در API Callها (Instagram و Telegram)

📍 مثال: Instagram API

```python
import requests
from core.utils import get_active_proxy, get_fallback_proxy

def fetch_instagram_me(token: str):
    url = f"https://graph.instagram.com/me?access_token={token}"
    try:
        response = requests.get(url, proxies=get_active_proxy(), timeout=15)
        response.raise_for_status()
    except Exception:
        response = requests.get(url, proxies=get_fallback_proxy(), timeout=15)
    return response.json()
```

📍 مثال: Telegram API

```python
import requests
from core.utils import get_active_proxy, get_fallback_proxy

def send_telegram_message(bot_token: str, chat_id: str, text: str):
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {"chat_id": chat_id, "text": text}
    try:
        response = requests.post(url, json=payload, proxies=get_active_proxy(), timeout=15)
        response.raise_for_status()
    except Exception:
        response = requests.post(url, json=payload, proxies=get_fallback_proxy(), timeout=15)
    return response.json()
```

---

## 🧭 مرحله ۵: انجام Migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

---

## 🔐 مرحله ۶: ورود به Django Admin و اضافه کردن Proxy

۱. وارد `/admin` شو  
۲. ProxySetting رو باز کن  
۳. اطلاعات Proxy رو وارد کن:

```
http_proxy = http://USER:PASS@IP:PORT
https_proxy = http://USER:PASS@IP:PORT
fallback_http_proxy = (اختیاری)
fallback_https_proxy = (اختیاری)
is_active = ✅
```

۴. ذخیره کن ✅

---

## 🧪 مرحله ۷: تست نهایی

```python
from core.utils import get_active_proxy
import requests

url = "https://graph.instagram.com/me?access_token=YOUR_TOKEN"
res = requests.get(url, proxies=get_active_proxy(), timeout=15)
print(res.status_code, res.json())

# یا برای Telegram:
bot_token = "YOUR_BOT_TOKEN"
chat_id = "YOUR_CHAT_ID"
res = requests.post(
    f"https://api.telegram.org/bot{bot_token}/sendMessage",
    json={"chat_id": chat_id, "text": "Proxy test ✅"},
    proxies=get_active_proxy(),
    timeout=15
)
print(res.status_code, res.json())
```

✅ اگر 200 برگشت یعنی پروکسی درست ست شده.

---

## 🛡 نکات امنیتی
- فقط مدیرها به بخش ProxySetting دسترسی داشته باشن.
- ترجیحاً از IP اختصاصی (Residential) استفاده کن تا بلاک نشی.
- فقط یک Proxy باید `is_active=True` باشه.

---

## 🧭 Optional — قابلیت Switch سریع
بعداً می‌تونی با ساختن Action در Admin، بین Proxyها با یک کلیک سوییچ انجام بدی.

---

✅ با این ساختار، می‌تونی هر لحظه Proxy رو از طریق Admin تغییر بدی، بدون نیاز به SSH یا تغییر `.env` 🚀
