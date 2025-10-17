# 🔧 راهنمای حل مشکل Static Files با Arvan Cloud

## ❌ مشکل فعلی

صفحه Django Admin بدون CSS لود میشه و این خطاها رو میده:
```
- Refused to execute inline script (CSP violation)
- Uncaught SyntaxError: Invalid or unexpected token
- Static files نمیان
```

---

## 🎯 علت مشکل

1. **Static files به Arvan Cloud upload نشدن** ❌
2. **STATICFILES_STORAGE اشتباه تنظیم شده** ❌
3. **CORS در Arvan Cloud تنظیم نشده** ❌
4. **CSP headers مشکل دارن** ❌

---

## ✅ راه‌حل (قدم به قدم)

### قدم 1: SSH به VPS

```bash
ssh root@185.164.72.165
cd /root/pilito
```

### قدم 2: بررسی Environment Variables

```bash
# چک کن که این متغیرها درست تنظیم شدن:
cat .env | grep AWS

# باید این خروجی رو ببینی:
# AWS_ACCESS_KEY_ID=3311a374-fb35-4d06-8f90-0f67eb6520c8
# AWS_SECRET_ACCESS_KEY=your-secret-key
# AWS_STORAGE_BUCKET_NAME=pilito
# AWS_S3_ENDPOINT_URL=https://s3.ir-thr-at1.arvanstorage.ir
# AWS_S3_CUSTOM_DOMAIN=pilito.s3.ir-thr-at1.arvanstorage.ir
```

اگر **نیستن**، اضافه کن:
```bash
nano .env
```

اضافه کن:
```env
AWS_ACCESS_KEY_ID=3311a374-fb35-4d06-8f90-0f67eb6520c8
AWS_SECRET_ACCESS_KEY=<secret-key-از-پنل-arvan>
AWS_STORAGE_BUCKET_NAME=pilito
AWS_S3_REGION_NAME=ir-thr-at1
AWS_S3_ENDPOINT_URL=https://s3.ir-thr-at1.arvanstorage.ir
AWS_S3_CUSTOM_DOMAIN=pilito.s3.ir-thr-at1.arvanstorage.ir
```

### قدم 3: بررسی Bucket در Arvan Cloud

1. برو به: https://panel.arvancloud.ir
2. Object Storage → Buckets
3. Bucket `pilito` رو باز کن
4. چک کن:
   - ✅ **Access Level:** باید **Public** باشه
   - ✅ **CORS:** باید تنظیم شده باشه

#### تنظیم CORS در Arvan:

در پنل ArvanCloud → Bucket Settings → CORS:

```json
[
  {
    "AllowedOrigins": ["*"],
    "AllowedMethods": ["GET", "HEAD"],
    "AllowedHeaders": ["*"],
    "ExposeHeaders": [],
    "MaxAgeSeconds": 3600
  }
]
```

### قدم 4: Restart Docker Containers

```bash
cd /root/pilito
docker-compose down
docker-compose up -d
```

### قدم 5: اجرای Collectstatic

```bash
# اجرای collectstatic برای آپلود فایل‌های استاتیک به Arvan
docker exec django_app python manage.py collectstatic --noinput --clear

# انتظار:
# ✅ Copying 'admin/css/base.css'
# ✅ Post-processed 'xxx' files
```

اگر **خطا داد**:
```bash
# لاگ‌ها رو ببین
docker logs django_app --tail 50

# خطاهای رایج:
# - NoCredentialsError → .env درست نیست
# - AccessDenied → Secret Key اشتباهه
# - ConnectionError → Endpoint URL اشتباهه
```

### قدم 6: تست دسترسی به Static Files

```bash
# تست مستقیم URL
curl -I https://pilito.s3.ir-thr-at1.arvanstorage.ir/static/admin/css/base.css

# انتظار:
# HTTP/2 200 OK

# اگر 403 یا 404 داد → collectstatic اجرا نشده یا Bucket Public نیست
```

### قدم 7: بررسی Django Admin

1. برو به: http://185.164.72.165:8000/admin/
2. باید CSS ها لود شن و صفحه درست نمایش داده شه

---

## 🐛 عیب‌یابی مشکلات رایج

### مشکل 1: خطای NoCredentialsError

```bash
# چک کن .env درست load شده:
docker exec django_app env | grep AWS

# اگر خالی بود:
docker-compose down
docker-compose up -d
```

### مشکل 2: خطای AccessDenied (403)

```bash
# مطمئن شو Bucket روی Public هست
# مطمئن شو Secret Key درست وارد شده

# تست credentials با AWS CLI:
docker exec django_app pip install awscli
docker exec django_app aws s3 ls s3://pilito --endpoint-url=https://s3.ir-thr-at1.arvanstorage.ir
```

### مشکل 3: خطای ConnectionError

```bash
# چک کن Endpoint URL درسته:
echo $AWS_S3_ENDPOINT_URL

# باید: https://s3.ir-thr-at1.arvanstorage.ir

# تست اتصال:
curl -I https://s3.ir-thr-at1.arvanstorage.ir
```

### مشکل 4: CSP Violation

در `src/core/settings/production.py` اضافه کن:

```python
# اجازه بده static files از Arvan لود شن
CSP_DEFAULT_SRC = ("'self'", "https://pilito.s3.ir-thr-at1.arvanstorage.ir")
CSP_SCRIPT_SRC = ("'self'", "'unsafe-inline'", "https://pilito.s3.ir-thr-at1.arvanstorage.ir")
CSP_STYLE_SRC = ("'self'", "'unsafe-inline'", "https://pilito.s3.ir-thr-at1.arvanstorage.ir")
CSP_IMG_SRC = ("'self'", "data:", "https://pilito.s3.ir-thr-at1.arvanstorage.ir")
CSP_FONT_SRC = ("'self'", "data:", "https://pilito.s3.ir-thr-at1.arvanstorage.ir")
```

---

## 🔄 راه‌حل سریع (اگر همه چی fail شد)

### گزینه A: استفاده موقت از Local Static Files

```bash
# در VPS
cd /root/pilito
nano docker-compose.yml
```

اضافه کن volume برای static:
```yaml
services:
  web:
    volumes:
      - ./staticfiles:/app/staticfiles
```

در `src/core/settings/production.py`:
```python
# موقتی: استفاده از local static files
STATIC_URL = '/static/'
STATIC_ROOT = '/app/staticfiles'
STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'
```

```bash
docker-compose down
docker-compose up -d
docker exec django_app python manage.py collectstatic --noinput
```

### گزینه B: استفاده از WhiteNoise (توصیه نمیشه برای production)

```bash
docker exec django_app pip install whitenoise
```

در `src/core/settings/production.py`:
```python
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # اضافه کن
    # ...
]

STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
```

---

## ✅ چک‌لیست نهایی

- [ ] Environment variables در .env تنظیم شدن
- [ ] Bucket در Arvan Cloud روی Public هست
- [ ] CORS در Arvan Cloud تنظیم شده
- [ ] Docker containers restart شدن
- [ ] Collectstatic موفقیت‌آمیز اجرا شد
- [ ] تست curl موفقیت‌آمیز بود (200 OK)
- [ ] Django Admin با CSS درست لود میشه

---

## 📞 نیاز به کمک بیشتر؟

اگر هنوز کار نکرد، این اطلاعات رو بفرست:

```bash
# 1. لاگ Django
docker logs django_app --tail 100 > django.log

# 2. Environment variables
docker exec django_app env | grep AWS > env.log

# 3. تست curl
curl -I https://pilito.s3.ir-thr-at1.arvanstorage.ir/static/admin/css/base.css > curl.log

# 4. Docker compose config
cat docker-compose.yml > docker.log

# فایل‌های log رو بفرست
```

---

## 💡 توصیه نهایی

بهترین راه‌حل:
1. ✅ مطمئن شو Arvan Cloud credentials درست هستن
2. ✅ Bucket رو Public کن
3. ✅ CORS رو تنظیم کن
4. ✅ Collectstatic رو اجرا کن
5. ✅ تست کن با curl

**زمان تقریبی:** 5-10 دقیقه 🚀

