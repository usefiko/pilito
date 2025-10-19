# 🔧 راهنمای سرو Static Files از VPS (محلی)

## مشکل قبلی ❌
- تمام فایل‌ها (Static + Media) روی Arvan Cloud بودند
- Django Admin CSS/JS به درستی لود نمی‌شدند
- مشکلات CORS و CSP وجود داشت

## راه‌حل جدید ✅

### استراتژی:
1. **Static Files** (CSS, JS, Admin assets) → **VPS محلی** (سریع‌تر و بدون مشکل)
2. **Media Files** (عکس‌های آپلود شده کاربران) → **Arvan Cloud** (فضای نامحدود)

---

## تغییرات انجام شده

### 1. تنظیمات Django (`common.py`)
```python
# ✅ STATIC → VPS محلی
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# ✅ MEDIA → Arvan Cloud
MEDIA_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/media/'

STORAGES = {
    "default": {
        "BACKEND": "core.settings.storage_backends.MediaStorage",  # Arvan
    },
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",  # Local
    },
}
```

### 2. Nginx Configuration
```nginx
# ✅ Static files از VPS
location /static/ {
    alias /root/pilito/staticfiles/;
    expires 30d;
    add_header Cache-Control "public, immutable";
}

# ✅ Media files → مستقیم از Arvan (در Django تنظیم شده)
```

---

## نحوه اعمال تغییرات

### روش 1: استفاده از اسکریپت خودکار (توصیه می‌شود)

```bash
# 1. Pull جدیدترین تغییرات
cd /root/pilito
git pull origin main

# 2. اجرای اسکریپت
chmod +x fix_static_to_local.sh
./fix_static_to_local.sh
```

این اسکریپت:
- ✅ Nginx را تنظیم می‌کند
- ✅ `collectstatic` را اجرا می‌کند
- ✅ مجوزها را تنظیم می‌کند
- ✅ Django را restart می‌کند

---

### روش 2: دستی

#### مرحله 1: تنظیم Nginx
```bash
# ویرایش فایل Nginx
nano /etc/nginx/sites-available/api.pilito.com

# اضافه کردن بخش static:
location /static/ {
    alias /root/pilito/staticfiles/;
    expires 30d;
    add_header Cache-Control "public, immutable";
}

# Test و Reload
nginx -t
systemctl reload nginx
```

#### مرحله 2: جمع‌آوری Static Files
```bash
cd /root/pilito
docker-compose exec django_app python manage.py collectstatic --noinput --clear
```

#### مرحله 3: تنظیم مجوزها
```bash
chmod -R 755 /root/pilito/staticfiles/
chown -R root:root /root/pilito/staticfiles/
```

#### مرحله 4: Restart Django
```bash
docker-compose restart django_app
```

---

## تست و بررسی

### 1. بررسی Static Files
```bash
# بررسی فایل CSS ادمین
curl -I https://api.pilito.com/static/admin/css/base.css

# خروجی باید 200 OK باشه:
# HTTP/2 200
# content-type: text/css
```

### 2. بررسی Django Admin
1. برو به: `https://api.pilito.com/admin/`
2. باید CSS ها به درستی لود بشن
3. در Developer Tools → Network:
   - Static files: `https://api.pilito.com/static/...` ✅
   - Media files: `https://pilito.s3.ir-thr-at1.arvanstorage.ir/media/...` ✅

### 3. بررسی مسیرهای فایل‌ها
```bash
# بررسی تعداد فایل‌های static
ls -la /root/pilito/staticfiles/ | wc -l

# باید حدود 200+ فایل باشه
```

---

## مزایای این روش ✅

1. **سرعت بیشتر**: Static files از VPS محلی سرو میشن (کمتر از 10ms)
2. **بدون مشکل CORS/CSP**: همه چیز از یک domain سرو میشه
3. **هزینه کمتر**: فقط Media files روی Arvan (که حجم بیشتری دارن)
4. **Admin سریع‌تر**: CSS/JS ادمین فوری لود میشه
5. **مدیریت آسان‌تر**: Static files در دسترس مستقیم روی سرور

---

## عیب‌یابی

### مشکل 1: Static files لود نمیشن (404)
```bash
# بررسی وجود فایل‌ها
ls /root/pilito/staticfiles/admin/css/

# اگر خالی بود:
docker-compose exec django_app python manage.py collectstatic --noinput
```

### مشکل 2: Permission Denied
```bash
# تنظیم مجددی مجوزها
chmod -R 755 /root/pilito/staticfiles/
chown -R root:root /root/pilito/staticfiles/
```

### مشکل 3: Nginx 403 Forbidden
```bash
# بررسی مسیر در Nginx
nano /etc/nginx/sites-available/api.pilito.com

# مطمئن شو مسیر درسته:
# alias /root/pilito/staticfiles/;  ← باید با / تموم بشه
```

### مشکل 4: Cache قدیمی
```bash
# Cache مرورگر رو پاک کن یا:
curl -I https://api.pilito.com/static/admin/css/base.css?v=$(date +%s)
```

---

## نکات مهم ⚠️

1. **بعد از هر deploy:**
   ```bash
   docker-compose exec django_app python manage.py collectstatic --noinput
   ```

2. **Media files همچنان روی Arvan هستن** و تغییری نکردن

3. **Backup:**
   - اسکریپت خودکار از Nginx backup می‌گیره
   - در صورت مشکل: `/etc/nginx/sites-available/api.pilito.com.backup.*`

4. **Frontend:**
   - اگر Frontend هم Static files داره، اونها رو باید جداگانه مدیریت کنی

---

## سوالات متداول

### Q: آیا فایل‌های قدیمی Arvan پاک بشن?
**A:** خیر، فایل‌های Arvan همچنان موجودن. اگر میخوای پاکشون کنی:
```bash
# توصیه نمی‌شه - بذار برای backup باشن
```

### Q: Media files چطور؟
**A:** Media files همچنان روی Arvan هستن و تغییری نکردن. فقط Static files محلی شدن.

### Q: اگر بخوام دوباره Static رو روی Arvan بزارم؟
**A:** کافیه در `common.py`:
```python
STORAGES = {
    "staticfiles": {
        "BACKEND": "core.settings.storage_backends.StaticStorage",
    },
}
STATIC_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/static/'
```

---

## خلاصه
- ✅ Static files → VPS محلی (سریع و بدون مشکل)
- ✅ Media files → Arvan Cloud (فضای ذخیره‌سازی)
- ✅ Django Admin → سریع و درست کار می‌کنه
- ✅ هیچ مشکل CORS/CSP وجود نداره

---

**تاریخ آخرین بروزرسانی:** $(date)  
**نسخه:** 1.0

