# 🚀 WooCommerce Sync - Quick Reference

## 📋 خلاصه تصمیمات معماری

| موضوع | تصمیم |
|-------|-------|
| **App جدید** | ✅ بله - `integrations` |
| **Event Deduplication** | ✅ هر دو (WordPress debounce + Django idempotency) |
| **مدل Product** | ✅ استفاده از `web_knowledge.Product` + فیلد `external_id` |
| **Celery Queue** | ✅ `default` (اولویت معمولی) |
| **Variable Products** | ❌ فاز 2 (فعلاً فقط Simple) |
| **Plugin Size** | ✅ ~745 lines (بسیار سبک) |

---

## 🏗️ Models (Backend)

### 1. IntegrationToken
```python
- token: wc_sk_live_{40chars}
- user: ForeignKey(User)
- integration_type: woocommerce, shopify, ...
- is_active, last_used_at, usage_count
```

### 2. WooCommerceEventLog
```python
- event_id: unique (برای idempotency)
- event_type: product.created/updated/deleted
- user, woo_product_id, payload
- processed_successfully
```

### 3. Product (تغییرات)
```python
+ external_id: woo_{id}
+ external_source: woocommerce, shopify, manual
```

---

## 🔌 API Endpoints

### Admin Endpoints
```
GET    /api/v1/integrations/tokens/
POST   /api/v1/integrations/tokens/generate/
DELETE /api/v1/integrations/tokens/{id}/
GET    /api/v1/integrations/woocommerce/events/
```

### Webhook Endpoints (برای Plugin)
```
POST   /api/integrations/woocommerce/webhook/
GET    /api/integrations/woocommerce/health/
```

---

## 📦 Plugin Structure

```
fiko-woocommerce-sync/
├── fiko-woocommerce-sync.php    (30 lines)
├── includes/
│   ├── class-fiko-api.php       (120 lines) - ارتباط با Django
│   ├── class-fiko-hooks.php     (100 lines) - WooCommerce hooks
│   └── helpers.php              (60 lines)
├── admin/
│   ├── class-admin-page.php     (180 lines)
│   └── views/settings.php       (100 lines)
└── uninstall.php                (25 lines)

✅ Total: ~745 lines (خیلی سبک!)
```

---

## 🔄 Flow (خلاصه)

```
WordPress محصول Save
    ↓
Debounce Check (transient 30s)
    ↓
wp_remote_post (non-blocking) ← فوری برمی‌گرده!
    ↓
Django: Validate Token
    ↓
Celery Task (async)
    ↓
Product.objects.update_or_create()
    ↓
Signal (خودکار!) → TenantKnowledge
    ↓
✅ Chunk + Embedding
```

---

## 🧠 Smart Sync Logic

### فیلدهای محتوایی (نیاز به embedding):
- name
- short_description
- description
- categories
- tags

**→ تغییر = regenerate embedding**

### فیلدهای metadata (بدون embedding):
- price
- stock_quantity
- images
- sale_price

**→ تغییر = فقط update metadata**

### محاسبه Hash:
```python
content_hash = sha256(
    name + short_description + description + 
    categories + tags
)
```

---

## 🔐 Authentication

### Token Format:
```
wc_sk_live_a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0
│   │   │    └─────────────── 40 random chars
│   │   └──────────────────── Environment (live/test)
│   └──────────────────────── Secret Key
└──────────────────────────── WooCommerce
```

### Request Header:
```
Authorization: Bearer wc_sk_live_...
```

---

## ⚡ Celery Task

```python
@shared_task(bind=True, max_retries=3, default_retry_delay=30)
def process_woocommerce_product(self, payload):
    processor = WooCommerceProcessor()
    return processor.process_event(payload)
```

**Queue:** `default`  
**Retry:** 3 بار با delay 30s

---

## 📝 JSON Payload Example

```json
{
  "event_id": "wc_2025_11_10_54321",
  "event_type": "product.updated",
  "product": {
    "id": 414,
    "sku": "PROD-001",
    "name": "کفش اسپرت مردانه",
    "short_description": "کفش سبک و راحت",
    "description": "این کفش با زیره نرم...",
    "price": 850000,
    "currency": "IRT",
    "stock_quantity": 12,
    "categories": ["کفش", "مردانه"],
    "tags": ["ورزشی"],
    "image": "https://...",
    "permalink": "https://..."
  }
}
```

---

## 🧪 تست سریع

### 1. Backend
```bash
# Generate token
POST /api/v1/integrations/tokens/generate/
{
    "integration_type": "woocommerce",
    "name": "تست فروشگاه"
}

# Test health
GET /api/integrations/woocommerce/health/
Authorization: Bearer {token}
```

### 2. Plugin
```
1. نصب پلاگین
2. وارد کردن token
3. کلیک "تست اتصال"
4. ایجاد محصول تستی
5. بررسی لاگ در Django admin
```

---

## ✅ Checklist پیاده‌سازی

### Backend (Django)
- [ ] App `integrations` ایجاد
- [ ] Models: IntegrationToken, WooCommerceEventLog
- [ ] Migration: اضافه کردن `external_id` به Product
- [ ] Views: Token management + Webhook
- [ ] Authentication: IntegrationTokenAuthentication
- [ ] Services: TokenGenerator, WooCommerceProcessor
- [ ] Celery: process_woocommerce_product task
- [ ] Admin: IntegrationTokenAdmin, EventLogAdmin
- [ ] URLs: /api/integrations/...

### Plugin (WordPress)
- [ ] Main file: fiko-woocommerce-sync.php
- [ ] API: class-fiko-api.php
- [ ] Hooks: class-fiko-hooks.php
- [ ] Admin: settings page + test connection
- [ ] Styles: admin.css
- [ ] Scripts: admin.js
- [ ] Cleanup: uninstall.php

### Testing
- [ ] Token generation کار می‌کنه
- [ ] Health check OK
- [ ] محصول جدید → sync می‌شه
- [ ] ویرایش قیمت → metadata only
- [ ] ویرایش توضیحات → new embedding
- [ ] حذف محصول → soft delete
- [ ] Duplicate event → skip می‌شه

---

## 🐛 Common Issues

### مشکل: Plugin هیچ کاری نمی‌کنه
- ✅ بررسی کن WooCommerce نصب باشه
- ✅ بررسی کن token درست وارد شده
- ✅ تست connection انجام بده

### مشکل: محصول sync نمی‌شه
- ✅ بررسی کن Celery worker اجرا باشه
- ✅ لاگ Django رو چک کن
- ✅ لاگ WordPress debug.log

### مشکل: Embedding regenerate نمی‌شه
- ✅ بررسی کن محتوا واقعاً تغییر کرده
- ✅ content_hash رو چک کن
- ✅ OpenAI API key موجود باشه

---

## 📞 بعد از پیاده‌سازی

### Documentation برای کاربران
```
1. راهنمای نصب پلاگین
2. نحوه دریافت token از داشبورد
3. troubleshooting رایج
4. ویدیو آموزشی (اختیاری)
```

### Monitoring
```python
# Metrics to track:
- تعداد events دریافتی
- تعداد محصولات sync شده
- میانگین زمان پردازش
- خطاها و retry ها
```

---

**نسخه:** 1.0  
**آخرین بروزرسانی:** 2025-11-10

برای جزئیات کامل به `WOOCOMMERCE_SYNC_ARCHITECTURE.md` مراجعه کنید.

