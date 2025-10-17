# ☁️ راهنمای تنظیم Arvan Cloud Object Storage

## 📋 مقدمه

این پروژه از **Arvan Cloud Object Storage** (سازگار با S3) برای ذخیره فایل‌های استاتیک و مدیا استفاده می‌کند.

---

## 🎯 مزایای Arvan Cloud

✅ **سرعت بالا:** سرورهای داخل ایران → سرعت دانلود/آپلود بسیار بیشتر  
✅ **قیمت مناسب:** ارزان‌تر از AWS S3  
✅ **سازگار با S3:** هیچ تغییری در کد لازم نیست  
✅ **بدون فیلترینگ:** دسترسی مستقیم بدون نیاز به VPN  
✅ **پشتیبانی فارسی:** تیم پشتیبانی ایرانی

---

## 🔑 دریافت Credentials

### قدم 1: ثبت‌نام در Arvan Cloud

1. برو به: https://panel.arvancloud.ir
2. ثبت‌نام کن یا وارد شو
3. از منوی سمت چپ، **Object Storage** رو انتخاب کن

### قدم 2: ساخت Bucket

1. روی **Create Bucket** کلیک کن
2. یک نام منحصر به فرد انتخاب کن (مثلاً: `pilito-media`)
3. منطقه رو انتخاب کن:
   - **تهران (Tehran):** `ir-thr-at1`
   - **تبریز (Tabriz):** `ir-tbz-sh1`
4. **Access Level:** Public (برای فایل‌های عمومی)

### قدم 3: دریافت Access Keys

1. برو به **Access Management**
2. روی **Create Access Key** کلیک کن
3. دو کلید دریافت می‌کنی:
   - **Access Key:** مانند `3311a374-fb35-4d06-8f90-0f67eb6520c8`
   - **Secret Key:** مانند `***********************************`

⚠️ **مهم:** Secret Key فقط یکبار نمایش داده می‌شه، حتماً کپی کن!

---

## ⚙️ تنظیمات Environment Variables

در فایل `.env` در VPS خود این متغیرها رو اضافه کن:

```bash
# Arvan Cloud Object Storage Configuration
AWS_ACCESS_KEY_ID=3311a374-fb35-4d06-8f90-0f67eb6520c8
AWS_SECRET_ACCESS_KEY=your-secret-key-here
AWS_STORAGE_BUCKET_NAME=pilito-media
AWS_S3_REGION_NAME=ir-thr-at1

# Arvan Cloud Endpoint (Tehran)
AWS_S3_ENDPOINT_URL=https://s3.ir-thr-at1.arvanstorage.ir
AWS_S3_CUSTOM_DOMAIN=pilito-media.s3.ir-thr-at1.arvanstorage.ir

# اگر از منطقه تبریز استفاده می‌کنی:
# AWS_S3_ENDPOINT_URL=https://s3.ir-tbz-sh1.arvanstorage.ir
# AWS_S3_CUSTOM_DOMAIN=pilito-media.s3.ir-tbz-sh1.arvanstorage.ir
```

---

## 📝 تنظیمات کد (انجام شده ✅)

تنظیمات زیر در `src/core/settings/common.py` به روز شده:

```python
# ✅ Arvan Cloud Configuration
AWS_S3_ENDPOINT_URL = environ.get("AWS_S3_ENDPOINT_URL", "https://s3.ir-thr-at1.arvanstorage.ir")
AWS_S3_CUSTOM_DOMAIN = environ.get("AWS_S3_CUSTOM_DOMAIN", f'{AWS_STORAGE_BUCKET_NAME}.s3.ir-thr-at1.arvanstorage.ir')
```

**هیچ تغییر دیگری لازم نیست!** 🎉

---

## 🧪 تست Configuration

### در محیط توسعه (Local):

```bash
# فایل .env رو ویرایش کن
nano .env

# اضافه کن:
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
AWS_STORAGE_BUCKET_NAME=pilito-media
AWS_S3_ENDPOINT_URL=https://s3.ir-thr-at1.arvanstorage.ir
AWS_S3_CUSTOM_DOMAIN=pilito-media.s3.ir-thr-at1.arvanstorage.ir

# اجرای Django
python manage.py collectstatic --noinput
python manage.py runserver
```

### در Production (VPS):

```bash
# SSH به VPS
ssh root@185.164.72.165

# ویرایش .env
cd /root/pilito
nano .env

# اضافه کردن متغیرهای بالا

# Restart containers
docker-compose down
docker-compose up -d

# بررسی لاگ‌ها
docker logs django_app -f
```

---

## 🔍 بررسی موفقیت‌آمیز بودن

### تست 1: Collectstatic

```bash
docker exec django_app python manage.py collectstatic --noinput

# انتظار:
# ✅ Post-processed 'xxx' files
# ✅ Copying '...' to Arvan Cloud Storage
```

### تست 2: آپلود فایل

```python
# در Django shell
docker exec -it django_app python manage.py shell

from django.core.files.storage import default_storage
from django.core.files.base import ContentFile

# تست آپلود
path = default_storage.save('test.txt', ContentFile(b'Hello Arvan Cloud!'))
print(f"File uploaded to: {path}")
print(f"URL: {default_storage.url(path)}")

# تست دانلود
content = default_storage.open('test.txt').read()
print(f"Content: {content}")

# حذف فایل تست
default_storage.delete('test.txt')
```

### تست 3: دسترسی مستقیم

```bash
# بررسی URL های فایل‌های استاتیک
curl -I https://pilito-media.s3.ir-thr-at1.arvanstorage.ir/static/admin/css/base.css

# انتظار:
# HTTP/2 200 OK
```

---

## 📊 مقایسه Endpoints

| منطقه | Endpoint | بهترین برای |
|-------|----------|-------------|
| **تهران** | `s3.ir-thr-at1.arvanstorage.ir` | کاربران تهران و شمال |
| **تبریز** | `s3.ir-tbz-sh1.arvanstorage.ir` | کاربران تبریز و شمال‌غربی |

💡 **توصیه:** از منطقه نزدیک‌تر به سرور VPS خود استفاده کنید.

---

## 🛠️ عیب‌یابی

### مشکل 1: خطای 403 Forbidden

```bash
# بررسی Bucket Policy در پنل ArvanCloud
# مطمئن شو که Bucket روی Public تنظیم شده
```

### مشکل 2: فایل‌ها آپلود نمی‌شن

```bash
# بررسی credentials
docker exec django_app env | grep AWS

# بررسی اتصال به Arvan Cloud
docker exec django_app curl -I https://s3.ir-thr-at1.arvanstorage.ir

# بررسی لاگ‌ها
docker logs django_app --tail 100
```

### مشکل 3: Static files لود نمی‌شن

```bash
# Collectstatic مجدد
docker exec django_app python manage.py collectstatic --noinput --clear

# بررسی CORS در پنل ArvanCloud
# Settings → CORS → Add Rule:
# - Origin: *
# - Methods: GET, HEAD
```

---

## 💰 هزینه‌ها (تقریبی)

| آیتم | قیمت (تومان/ماه) |
|------|------------------|
| Storage 10GB | ~50,000 |
| Traffic 100GB | ~100,000 |
| Requests (100K) | ~30,000 |

💡 **نکته:** قیمت‌ها ممکنه تغییر کنه، حتماً از پنل ArvanCloud چک کن.

---

## 📚 مستندات

- **Arvan Cloud Docs:** https://www.arvancloud.ir/docs/object-storage
- **S3 API Compatibility:** https://docs.aws.amazon.com/AmazonS3/latest/API/
- **Django Storages:** https://django-storages.readthedocs.io/

---

## ✅ چک‌لیست نهایی

- [ ] ثبت‌نام در Arvan Cloud انجام شده
- [ ] Bucket ساخته شده (Public Access)
- [ ] Access Keys دریافت شده
- [ ] متغیرهای محیطی در `.env` تنظیم شده
- [ ] Docker containers restart شده
- [ ] Collectstatic موفقیت‌آمیز اجرا شده
- [ ] فایل‌های استاتیک قابل دسترسی هستند
- [ ] آپلود/دانلود مدیا تست شده

---

## 🎉 تبریک!

حالا پروژه شما از **Arvan Cloud Object Storage** استفاده می‌کنه! 🚀

**مزایا:**
- ⚡ سرعت بیشتر
- 💰 هزینه کمتر
- 🇮🇷 سرور داخل ایران
- 🔒 امنیت بالا

**سوال یا مشکل داری؟** به پشتیبانی ArvanCloud مراجعه کن یا به مستندات نگاه کن.

