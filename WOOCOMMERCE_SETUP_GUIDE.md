# 🚀 راهنمای نصب و راه‌اندازی WooCommerce Sync

این فایل شامل تمام مراحل نصب و راه‌اندازی سیستم WooCommerce Sync است.

---

## 📋 خلاصه اقدامات

✅ **Backend (Django):**
- App `integrations` ایجاد شد
- Models ساخته شد
- Views و Serializers آماده است
- Celery Task پیاده شد
- Admin Panel آماده است

✅ **Plugin (WordPress):**
- پلاگین کامل در `/fiko-woocommerce-sync/` آماده است
- آماده برای زیپ و آپلود در WordPress

✅ **Migration:**
- فیلدهای `external_id` و `external_source` به Product اضافه شدند

---

## 🔧 مرحله 1: راه‌اندازی Backend

### 1.1. اضافه کردن App به INSTALLED_APPS

```python
# src/core/settings/common.py

INSTALLED_APPS = [
    # ... existing apps
    'integrations',
]
```

### 1.2. اضافه کردن URLs

```python
# src/core/urls.py

urlpatterns = [
    # ... existing patterns
    path('api/integrations/', include('integrations.urls')),
]
```

### 1.3. اضافه کردن Celery Task Route

```python
# src/core/celery.py

app.conf.task_routes = {
    # ... existing routes
    
    # 🔄 WooCommerce Integration Tasks → Default Queue
    'integrations.tasks.process_woocommerce_product': {
        'queue': 'default',
        'routing_key': 'default.integration',
    },
}
```

### 1.4. اجرای Migration

```bash
cd /Users/omidataei/Documents/GitHub/pilito2/Untitled/src

# ایجاد migrations برای integrations app
python manage.py makemigrations integrations

# ایجاد migration برای Product (اگر قبلاً نساخته‌اید)
python manage.py makemigrations web_knowledge

# اجرای migrations
python manage.py migrate
```

### 1.5. ایجاد Superuser (اگر نداری)

```bash
python manage.py createsuperuser
```

### 1.6. راه‌اندازی Celery Worker

```bash
# در یک terminal جداگانه:
celery -A core worker -l info

# یا با docker:
docker compose exec celery celery -A core worker -l info
```

---

## 🔌 مرحله 2: راه‌اندازی WordPress Plugin

### 2.1. آماده‌سازی Plugin برای آپلود

```bash
cd /Users/omidataei/Documents/GitHub/pilito2/Untitled

# زیپ کردن پلاگین
zip -r fiko-woocommerce-sync.zip fiko-woocommerce-sync/ -x "*.DS_Store" "*__pycache__*" "*.pyc"
```

### 2.2. نصب Plugin در WordPress

1. به پنل WordPress بروید
2. Plugins > Add New > Upload Plugin
3. فایل `fiko-woocommerce-sync.zip` را آپلود کنید
4. روی "Install Now" کلیک کنید
5. پلاگین را فعال کنید (Activate)

---

## 🎯 مرحله 3: تنظیمات و اتصال

### 3.1. ایجاد Token در Django Admin

1. به Django Admin بروید: `https://api.fiko.ai/admin/`
2. به بخش **Integrations > Integration Tokens** بروید
3. روی **Add Integration Token** کلیک کنید
4. یا از API استفاده کنید:

```bash
# با curl (برای admin):
curl -X POST https://api.fiko.ai/api/v1/integrations/tokens/generate/ \
  -H "Authorization: Bearer YOUR_ADMIN_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "integration_type": "woocommerce",
    "name": "فروشگاه اصلی"
  }'
```

**⚠️ مهم:** Token فقط یکبار نمایش داده می‌شود، حتماً کپی کنید!

### 3.2. تنظیمات Plugin در WordPress

1. در WordPress به **WooCommerce > فیکو Sync** بروید
2. Token دریافتی را در کادر **API Token** paste کنید
3. روی **🔍 تست اتصال** کلیک کنید
4. اگر پیام ✅ دریافت کردید، روی **💾 ذخیره تنظیمات** کلیک کنید

---

## ✅ تست

### تست 1: ایجاد محصول جدید

1. در WordPress > Products > Add New
2. یک محصول تستی بسازید
3. Publish کنید
4. در Django Admin > WooCommerce Event Logs ببینید که رویداد ثبت شده

### تست 2: بررسی Chunk

1. در Django Admin > Tenant Knowledge (RAG) ببینید
2. باید یک chunk جدید با `chunk_type='product'` ایجاد شده باشد

### تست 3: API Frontend

```bash
# لیست محصولات WooCommerce
curl -X GET "https://api.fiko.ai/api/v1/web-knowledge/products/?external_source=woocommerce" \
  -H "Authorization: Bearer USER_JWT_TOKEN"
```

---

## 📊 مانیتورینگ

### Django Admin Panels

1. **Integration Tokens**: `/admin/integrations/integrationtoken/`
   - مشاهده و مدیریت tokenها
   - آمار استفاده

2. **WooCommerce Event Logs**: `/admin/integrations/woocommerceeventlog/`
   - لیست تمام رویدادها
   - فیلتر بر اساس موفق/ناموفق
   - مشاهده payload

3. **Products**: `/admin/web_knowledge/product/`
   - محصولات sync شده
   - فیلتر بر اساس `external_source=woocommerce`

### WordPress

1. **Products List**: ستون **🔄 Fiko** وضعیت sync را نشان می‌دهد:
   - ✅ = Synced successfully
   - ❌ = Error
   - — = Not synced yet

2. **Settings Page**: `WooCommerce > فیکو Sync`
   - آمار کلی
   - تست اتصال

---

## 🐛 عیب‌یابی

### مشکل: محصول sync نمی‌شود

**بررسی:**
1. Token درست وارد شده؟
2. Celery worker در حال اجرا است؟
3. لاگ‌های Celery را بررسی کنید
4. لاگ‌های WordPress (با فعال کردن logging در تنظیمات)

```bash
# لاگ Celery
docker compose logs celery -f

# لاگ WordPress
tail -f wp-content/debug.log
```

### مشکل: Token invalid

**راه‌حل:**
1. مطمئن شوید token به درستی کپی شده
2. بررسی کنید token منقضی نشده باشد
3. در Django Admin token را چک کنید که `is_active=True` باشد

### مشکل: Duplicate event

این طبیعی است! سیستم از `event_id` برای idempotency استفاده می‌کند.

---

## 🔄 Workflow کامل

```
1. کاربر در WooCommerce محصول می‌سازد
   ↓
2. Plugin: Hook woocommerce_new_product فعال می‌شود
   ↓
3. Plugin: بررسی debounce (30s)
   ↓
4. Plugin: ارسال POST به /api/integrations/woocommerce/webhook/
   ↓
5. Django: Validate token با IntegrationTokenAuthentication
   ↓
6. Django: ایجاد WooCommerceEventLog
   ↓
7. Django: Dispatch Celery task
   ↓
8. Celery: WooCommerceProcessor.process_event()
   ↓
9. Celery: Product.objects.update_or_create()
   ↓
10. Django Signal: sync_product_to_knowledge_base()
   ↓
11. Django: TenantKnowledge.objects.create() با embedding
   ↓
12. ✅ محصول آماده برای RAG و AI
```

---

## 📝 API Endpoints

### برای Plugin (WordPress)

```
POST   /api/integrations/woocommerce/webhook/   # دریافت events
GET    /api/integrations/woocommerce/health/    # تست اتصال
```

### برای Admin (Django)

```
GET    /api/v1/integrations/tokens/             # لیست tokenها
POST   /api/v1/integrations/tokens/generate/    # ساخت token
DELETE /api/v1/integrations/tokens/{id}/        # حذف token
GET    /api/v1/integrations/woocommerce/events/ # لیست event logs
```

### برای Frontend (محصولات)

```
GET    /api/v1/web-knowledge/products/                    # لیست همه محصولات
GET    /api/v1/web-knowledge/products/?external_source=woocommerce  # فقط WooCommerce
GET    /api/v1/web-knowledge/products/{id}/               # جزئیات محصول
```

---

## 🎨 استفاده در Frontend

### React Example

```jsx
import useSWR from 'swr'

function WooCommerceProducts() {
  const { data, error } = useSWR(
    '/api/v1/web-knowledge/products/?external_source=woocommerce',
    fetcher
  )
  
  if (error) return <div>خطا در بارگذاری</div>
  if (!data) return <div>در حال بارگذاری...</div>
  
  return (
    <div>
      {data.results.map(product => (
        <ProductCard key={product.id} product={product} />
      ))}
    </div>
  )
}
```

---

## 📚 فایل‌های مرجع

- **معماری کامل**: `docs/wordpress/WOOCOMMERCE_SYNC_ARCHITECTURE.md`
- **Quick Reference**: `docs/wordpress/WOOCOMMERCE_SYNC_QUICK_REFERENCE.md`
- **نمونه کدهای Backend**: `docs/wordpress/WOOCOMMERCE_SYNC_CODE_SAMPLES.md`
- **نمونه کدهای Plugin**: `docs/wordpress/WOOCOMMERCE_PLUGIN_CODE_SAMPLES.md`
- **API Frontend**: `docs/wordpress/WOOCOMMERCE_FRONTEND_API.md`

---

## ✨ ویژگی‌های پیاده شده

✅ سینک خودکار محصولات (Create, Update, Delete)  
✅ Smart Sync (تشخیص تغییرات محتوایی vs. قیمت)  
✅ Idempotency (جلوگیری از duplicate)  
✅ Debouncing (30 ثانیه)  
✅ Non-blocking requests (سبک برای WordPress)  
✅ Async processing (Celery)  
✅ Auto-chunking (Signal-based)  
✅ Embedding generation (OpenAI)  
✅ Admin panel کامل  
✅ Event logging  
✅ Error handling & retry  
✅ API برای frontend  
✅ فیلترها و جستجو  

---

## 🚧 فاز بعدی (آینده)

- [ ] Variable Products support
- [ ] Bulk sync اولیه
- [ ] Webhook signature verification
- [ ] Conflict resolution
- [ ] Rate limiting
- [ ] Metrics & monitoring

---

**نسخه:** 1.0.0  
**تاریخ:** 2025-11-10  
**وضعیت:** ✅ آماده تست

