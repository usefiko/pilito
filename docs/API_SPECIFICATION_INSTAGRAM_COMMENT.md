# 🔌 API Specification - Instagram Comment Workflow

## Base URL
```
Production: https://your-domain.com/api
Development: http://localhost:8000/api
```

---

## 📋 Table of Contents
1. [Authentication](#authentication)
2. [Products API](#products-api)
3. [Workflow API](#workflow-api)
4. [Instagram Channels API](#instagram-channels-api)
5. [Error Codes](#error-codes)

---

## 🔐 Authentication

همه endpoint‌ها نیاز به authentication دارند:

```http
Authorization: Bearer <access_token>
```

یا استفاده از session authentication (اگر از همان دامنه درخواست می‌دهید).

---

## 📦 Products API

### 1. لیست محصولات

```http
GET /api/knowledge/products/
```

#### Query Parameters:
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| search | string | No | جستجو در عنوان و توضیحات |
| is_active | boolean | No | فقط محصولات فعال (default: all) |
| page | integer | No | شماره صفحه (default: 1) |
| page_size | integer | No | تعداد در هر صفحه (default: 20) |

#### Response 200 OK:
```json
{
  "count": 25,
  "next": "https://.../api/knowledge/products/?page=2",
  "previous": null,
  "results": [
    {
      "id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
      "title": "محصول نمونه",
      "description": "توضیحات کامل محصول",
      "price": 1500000,
      "currency": "IRT",
      "price_display": "1,500,000 تومان",
      "billing_period": "one_time",
      "product_url": "https://example.com/product",
      "buy_url": "https://example.com/buy",
      "image_url": "https://example.com/media/products/image.jpg",
      "is_active": true,
      "created_at": "2025-11-17T10:30:00Z",
      "updated_at": "2025-11-17T10:30:00Z"
    }
  ]
}
```

#### Response Fields:
| Field | Type | Description |
|-------|------|-------------|
| id | uuid | شناسه یکتا محصول |
| title | string | عنوان محصول (max: 200 chars) |
| description | string/null | توضیحات محصول |
| price | decimal/null | قیمت (عدد) |
| currency | string | واحد پولی: "IRT", "USD", "EUR" |
| price_display | string | قیمت فرمت شده برای نمایش |
| billing_period | string | "one_time", "monthly", "yearly", "custom" |
| product_url | string/null | لینک صفحه محصول |
| buy_url | string/null | لینک خرید مستقیم |
| image_url | string/null | URL تصویر محصول |
| is_active | boolean | وضعیت فعال/غیرفعال |
| created_at | datetime | تاریخ ساخت |
| updated_at | datetime | تاریخ آخرین ویرایش |

#### مثال با جستجو:
```http
GET /api/knowledge/products/?search=کفش&is_active=true
```

---

### 2. جزئیات یک محصول

```http
GET /api/knowledge/products/{id}/
```

#### Response 200 OK:
همان ساختار object بالا

#### Response 404 Not Found:
```json
{
  "detail": "Not found."
}
```

---

### 3. ساخت محصول جدید

```http
POST /api/knowledge/products/
Content-Type: application/json
```

#### Request Body:
```json
{
  "title": "محصول جدید",
  "description": "توضیحات",
  "price": 2500000,
  "currency": "IRT",
  "billing_period": "one_time",
  "product_url": "https://example.com/new-product",
  "buy_url": "https://example.com/buy/123",
  "image_url": "https://example.com/images/new.jpg",
  "is_active": true
}
```

#### Validation Rules:
- `title`: اجباری، حداکثر 200 کاراکتر
- `price`: اختیاری، باید عدد مثبت باشد
- `currency`: default = "IRT"
- `billing_period`: default = "one_time"
- `product_url`, `buy_url`: باید URL معتبر باشند (اگر مقدار دارند)

#### Response 201 Created:
Object محصول ساخته شده

#### Response 400 Bad Request:
```json
{
  "title": ["This field is required."],
  "price": ["Ensure this value is greater than or equal to 0."]
}
```

---

## 🔄 Workflow API

### 1. دریافت انواع Trigger

```http
GET /api/workflow/event-types/
```

#### Response 200 OK:
```json
{
  "results": [
    {
      "id": "uuid",
      "name": "MESSAGE_RECEIVED",
      "display_name": "Receive Message",
      "category": "message",
      "description": "Triggered when customer sends a message",
      "available_fields": ["message_text", "customer_id", ...]
    },
    {
      "id": "uuid",
      "name": "INSTAGRAM_COMMENT",
      "display_name": "Instagram Comment",
      "category": "instagram",
      "description": "Triggered when someone comments on Instagram post",
      "available_fields": ["comment_text", "username", "post_url", ...]
    }
  ]
}
```

---

### 2. دریافت انواع Action

```http
GET /api/workflow/actions/types/
```

#### Response 200 OK:
```json
{
  "action_types": [
    {
      "value": "send_message",
      "label": "Send Message",
      "description": "Send a message to customer",
      "config_schema": {...}
    },
    {
      "value": "instagram_comment_dm_reply",
      "label": "Instagram Comment → DM + Reply",
      "description": "Send DM and optional public reply to Instagram comment",
      "config_schema": {
        "dm_mode": {
          "type": "choice",
          "choices": ["STATIC", "PRODUCT"],
          "required": true
        },
        "dm_text_template": {
          "type": "text",
          "required_if": {"dm_mode": "STATIC"},
          "max_length": 1000
        },
        "product_id": {
          "type": "uuid",
          "required_if": {"dm_mode": "PRODUCT"}
        },
        "public_reply_enabled": {
          "type": "boolean",
          "default": false
        },
        "public_reply_template": {
          "type": "text",
          "required_if": {"public_reply_enabled": true},
          "max_length": 300
        }
      }
    }
  ]
}
```

---

### 3. ساخت Workflow جدید

```http
POST /api/workflow/workflows/
Content-Type: application/json
```

#### Request Body - مثال 1 (STATIC Mode):
```json
{
  "name": "پاسخ به کامنت‌های قیمت",
  "description": "ارسال خودکار دایرکت برای سوالات قیمت",
  "status": "ACTIVE",
  "triggers": [
    {
      "trigger_type": "INSTAGRAM_COMMENT",
      "is_active": true,
      "filters": {
        "operator": "OR",
        "conditions": [
          {
            "field": "comment_text",
            "operator": "contains",
            "value": "قیمت"
          },
          {
            "field": "comment_text",
            "operator": "contains",
            "value": "چنده"
          }
        ]
      }
    }
  ],
  "actions": [
    {
      "action_type": "instagram_comment_dm_reply",
      "order": 1,
      "is_required": true,
      "config": {
        "dm_mode": "STATIC",
        "dm_text_template": "سلام {{username}}! 👋\n\nممنون از کامنتت.\n\nبرای دیدن قیمت‌ها:\n[[CTA:مشاهده محصولات|https://example.com/products]]\n\nسوال دیگه‌ای داری؟ اینجا بپرس 👇",
        "public_reply_enabled": true,
        "public_reply_template": "{{username}} عزیز، پیام دادیم! لطفاً دایرکت چک کنید 💌"
      }
    }
  ]
}
```

#### Request Body - مثال 2 (PRODUCT Mode):
```json
{
  "name": "معرفی محصول خاص",
  "description": "پاسخ خودکار با AI برای محصول مشخص",
  "status": "ACTIVE",
  "triggers": [
    {
      "trigger_type": "INSTAGRAM_COMMENT",
      "is_active": true
    }
  ],
  "actions": [
    {
      "action_type": "instagram_comment_dm_reply",
      "order": 1,
      "config": {
        "dm_mode": "PRODUCT",
        "product_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
        "public_reply_enabled": true,
        "public_reply_template": "ممنون {{username}}! پیام دادیم 🎁"
      }
    }
  ]
}
```

#### Response 201 Created:
```json
{
  "id": "uuid",
  "name": "پاسخ به کامنت‌های قیمت",
  "description": "...",
  "status": "ACTIVE",
  "created_at": "2025-11-17T12:00:00Z",
  "triggers": [...],
  "actions": [...]
}
```

#### Response 400 Bad Request:
```json
{
  "actions": [
    {
      "config": {
        "dm_text_template": ["This field is required when dm_mode is STATIC"],
        "product_id": ["Product not found"]
      }
    }
  ]
}
```

---

### 4. دریافت لیست Workflows

```http
GET /api/workflow/workflows/
```

#### Query Parameters:
| Parameter | Type | Description |
|-----------|------|-------------|
| status | string | ACTIVE, DRAFT, PAUSED |
| trigger_type | string | فیلتر بر اساس نوع trigger |
| search | string | جستجو در نام و توضیحات |

#### Response 200 OK:
```json
{
  "count": 5,
  "results": [
    {
      "id": "uuid",
      "name": "Workflow Name",
      "status": "ACTIVE",
      "trigger_count": 1,
      "action_count": 2,
      "created_at": "2025-11-17T10:00:00Z",
      "last_executed": "2025-11-17T11:30:00Z"
    }
  ]
}
```

---

### 5. آپدیت Workflow

```http
PUT /api/workflow/workflows/{id}/
PATCH /api/workflow/workflows/{id}/
```

همان ساختار POST (برای PUT همه فیلدها، برای PATCH فقط تغییرات)

---

### 6. حذف Workflow

```http
DELETE /api/workflow/workflows/{id}/
```

#### Response 204 No Content

---

## 📱 Instagram Channels API

### 1. لیست کانال‌های اینستاگرام

```http
GET /api/settings/instagram-channels/
```

#### Response 200 OK:
```json
{
  "results": [
    {
      "id": "uuid",
      "username": "my_business_page",
      "instagram_user_id": "17841400123456",
      "account_type": "business",
      "is_connect": true,
      "access_token_valid": true,
      "webhook_configured": true,
      "permissions": [
        "instagram_basic",
        "instagram_manage_messages",
        "instagram_manage_comments"
      ],
      "created_at": "2025-11-01T10:00:00Z"
    }
  ]
}
```

#### Account Types:
- `"business"` - Business Account (✅ می‌تواند از comment workflow استفاده کند)
- `"creator"` - Creator Account (✅ می‌تواند از comment workflow استفاده کند)
- `"personal"` - Personal Account (❌ نمی‌تواند از comment workflow استفاده کند)

---

### 2. تست Webhook

```http
POST /api/settings/instagram-channels/{id}/test-webhook/
```

#### Response 200 OK:
```json
{
  "success": true,
  "message": "Webhook is properly configured",
  "subscriptions": [
    "messages",
    "messaging_postbacks",
    "comments"
  ],
  "webhook_url": "https://your-domain.com/api/instagram-webhook/"
}
```

#### Response 400 Bad Request:
```json
{
  "success": false,
  "error": "Comments webhook not subscribed",
  "message": "Please subscribe to 'comments' webhook event in Meta App Dashboard",
  "help_url": "https://developers.facebook.com/docs/instagram-api/guides/webhooks"
}
```

---

### 3. تست ارسال پیام

```http
POST /api/settings/instagram-channels/{id}/test-message/
Content-Type: application/json
```

#### Request Body:
```json
{
  "recipient_id": "instagram_user_id",
  "text": "Test message",
  "buttons": [
    {
      "type": "web_url",
      "title": "Visit Website",
      "url": "https://example.com"
    }
  ]
}
```

#### Response 200 OK:
```json
{
  "success": true,
  "message_id": "mid.xyz123",
  "recipient_id": "123456"
}
```

---

## ❌ Error Codes

### HTTP Status Codes:

| Code | Meaning | Description |
|------|---------|-------------|
| 200 | OK | درخواست موفق |
| 201 | Created | Resource جدید ساخته شد |
| 204 | No Content | حذف موفق |
| 400 | Bad Request | خطای validation |
| 401 | Unauthorized | نیاز به authentication |
| 403 | Forbidden | عدم دسترسی |
| 404 | Not Found | Resource یافت نشد |
| 500 | Internal Server Error | خطای سرور |

### Error Response Format:
```json
{
  "detail": "Error message",
  "code": "ERROR_CODE",
  "field_errors": {
    "field_name": ["Error message 1", "Error message 2"]
  }
}
```

### Custom Error Codes:

| Code | Description |
|------|-------------|
| INVALID_ACCOUNT_TYPE | حساب Personal نمی‌تواند از comment workflow استفاده کند |
| WEBHOOK_NOT_CONFIGURED | Webhook تنظیم نشده |
| PRODUCT_NOT_FOUND | محصول یافت نشد یا غیرفعال است |
| INVALID_CTA_FORMAT | فرمت دکمه CTA اشتباه است |
| TOO_MANY_CTA_BUTTONS | بیش از 3 دکمه CTA |
| MISSING_PERMISSION | Permission لازم وجود ندارد |

---

## 📝 نکات مهم برای Developer

### 1. Rate Limiting:
- هر user حداکثر 100 request در دقیقه
- Header‌های rate limit:
  ```
  X-RateLimit-Limit: 100
  X-RateLimit-Remaining: 95
  X-RateLimit-Reset: 1700220000
  ```

### 2. Pagination:
همه endpoint‌های لیست از pagination پشتیبانی می‌کنند:
```json
{
  "count": 100,
  "next": "https://.../api/resource/?page=2",
  "previous": null,
  "results": [...]
}
```

### 3. Filtering & Search:
- `?search=query` - جستجو در فیلدهای متنی
- `?field=value` - فیلتر دقیق
- `?field__contains=value` - فیلتر شامل
- `?ordering=-created_at` - مرتب‌سازی (- برای نزولی)

### 4. Datetime Format:
همه تاریخ‌ها به فرمت ISO 8601:
```
2025-11-17T10:30:00Z
```

### 5. UUID Format:
همه IDها به فرمت UUID v4:
```
f47ac10b-58cc-4372-a567-0e02b2c3d479
```

---

## 🧪 نمونه‌های cURL برای تست

### تست لیست محصولات:
```bash
curl -X GET \
  'https://your-domain.com/api/knowledge/products/?is_active=true' \
  -H 'Authorization: Bearer YOUR_TOKEN'
```

### تست ساخت Workflow:
```bash
curl -X POST \
  'https://your-domain.com/api/workflow/workflows/' \
  -H 'Authorization: Bearer YOUR_TOKEN' \
  -H 'Content-Type: application/json' \
  -d '{
    "name": "Test Workflow",
    "status": "ACTIVE",
    "triggers": [{
      "trigger_type": "INSTAGRAM_COMMENT"
    }],
    "actions": [{
      "action_type": "instagram_comment_dm_reply",
      "config": {
        "dm_mode": "STATIC",
        "dm_text_template": "Test message",
        "public_reply_enabled": false
      }
    }]
  }'
```

### تست Webhook:
```bash
curl -X POST \
  'https://your-domain.com/api/settings/instagram-channels/CHANNEL_ID/test-webhook/' \
  -H 'Authorization: Bearer YOUR_TOKEN'
```

---

## 📚 منابع مفید

- [Instagram Graph API - Comments](https://developers.facebook.com/docs/instagram-api/reference/ig-media/comments)
- [Instagram Messaging API - Button Template](https://developers.facebook.com/docs/messenger-platform/instagram/features/generic-template)
- [Webhook Setup Guide](https://developers.facebook.com/docs/instagram-api/guides/webhooks)

---

**Version**: 1.0  
**Last Updated**: 2025-11-17  
**API Base URL**: `https://your-domain.com/api`

