# 🔄 WooCommerce Sync - معماری کامل و راهنمای پیاده‌سازی

## 📋 فهرست مطالب
1. [نگاه کلی](#نگاه-کلی)
2. [معماری Backend (Django)](#معماری-backend)
3. [معماری Plugin (WordPress)](#معماری-plugin)
4. [جریان کامل (Flow)](#جریان-کامل)
5. [راهنمای پیاده‌سازی گام‌به‌گام](#راهنمای-پیاده‌سازی)
6. [تست و راه‌اندازی](#تست-و-راه‌اندازی)

---

## 🎯 نگاه کلی

### هدف
ایجاد سیستمی که محصولات WooCommerce را به‌صورت خودکار با پلتفرم فیکو سینک کند و در سیستم RAG (TenantKnowledge) قرار دهد.

### ویژگی‌های کلیدی
- ✅ سبک و بدون فشار بر WordPress
- ✅ پردازش Async در Django
- ✅ Smart Sync (تشخیص تغییرات محتوایی vs. قیمت)
- ✅ Idempotent (جلوگیری از duplicate)
- ✅ امنیت با Integration Token
- ✅ Auto-chunking و embedding
- ✅ Admin panel برای مدیریت

### تصمیمات معماری

| موضوع | تصمیم | دلیل |
|-------|-------|------|
| **App جدید؟** | بله - `integrations` | آینده‌نگری برای Shopify، Magento و... |
| **Event Deduplication** | هر دو (WordPress + Django) | WordPress: debounce سبک / Django: guarantee idempotency |
| **مدل Product جدید؟** | خیر - استفاده از `web_knowledge.Product` | مدل موجود کامل است، فقط فیلد `external_id` اضافه می‌شود |
| **Celery Queue** | `default` | اولویت معمولی، background task |
| **Variable Products** | فاز 2 | نسخه اولیه فقط Simple Products |

---

## 🏗️ معماری Backend

### 1. App Structure

```
src/integrations/
├── __init__.py
├── apps.py
├── admin.py
├── models.py
├── serializers.py
├── views.py
├── tasks.py
├── signals.py
├── permissions.py
├── urls.py
├── services/
│   ├── __init__.py
│   ├── token_generator.py
│   └── woocommerce_processor.py
└── migrations/
    └── 0001_initial.py
```

### 2. Models

#### 2.1 IntegrationToken
```python
class IntegrationToken(models.Model):
    """
    API Tokens برای integrations خارجی
    هر کاربر می‌تواند چند token داشته باشد (برای چند فروشگاه)
    """
    INTEGRATION_TYPES = [
        ('woocommerce', 'WooCommerce'),
        ('shopify', 'Shopify'),
        ('custom', 'Custom'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='integration_tokens')
    
    # Token (فقط یکبار نمایش داده می‌شود)
    token = models.CharField(max_length=128, unique=True, db_index=True)
    token_preview = models.CharField(max_length=20)  # wc_sk...abc123
    
    integration_type = models.CharField(max_length=20, choices=INTEGRATION_TYPES)
    name = models.CharField(max_length=100, help_text="نام دلخواه برای شناسایی (مثلاً: فروشگاه اصلی)")
    
    # Security & Tracking
    is_active = models.BooleanField(default=True)
    last_used_at = models.DateTimeField(null=True, blank=True)
    usage_count = models.IntegerField(default=0)
    
    # Optional: IP Whitelist
    allowed_ips = models.JSONField(default=list, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'integration_tokens'
        verbose_name = "🔑 Integration Token"
        verbose_name_plural = "🔑 Integration Tokens"
        indexes = [
            models.Index(fields=['user', 'integration_type', 'is_active']),
            models.Index(fields=['token']),
        ]
```

#### 2.2 WooCommerceEventLog
```python
class WooCommerceEventLog(models.Model):
    """
    لاگ تمام رویدادهای دریافتی از WooCommerce
    برای idempotency و debugging
    """
    EVENT_TYPES = [
        ('product.created', 'Product Created'),
        ('product.updated', 'Product Updated'),
        ('product.deleted', 'Product Deleted'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    
    # Event Info
    event_id = models.CharField(max_length=100, unique=True, db_index=True)
    event_type = models.CharField(max_length=30, choices=EVENT_TYPES)
    
    # References
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    token = models.ForeignKey(IntegrationToken, on_delete=models.SET_NULL, null=True)
    woo_product_id = models.IntegerField()
    
    # Data
    payload = models.JSONField()
    
    # Processing
    processed_successfully = models.BooleanField(default=True)
    error_message = models.TextField(blank=True, null=True)
    
    # Metadata
    source_ip = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=500, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    
    class Meta:
        db_table = 'woocommerce_event_log'
        verbose_name = "📝 WooCommerce Event Log"
        verbose_name_plural = "📝 WooCommerce Event Logs"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'event_type', 'created_at']),
            models.Index(fields=['event_id']),
        ]
```

#### 2.3 تغییرات در Product Model
```python
# در web_knowledge/models.py - فیلد جدید:

class Product(models.Model):
    # ... فیلدهای موجود
    
    # 🆕 فیلد جدید برای integration
    external_id = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        db_index=True,
        help_text="ID محصول از سیستم خارجی (مثلاً woo_414)"
    )
    external_source = models.CharField(
        max_length=20,
        blank=True,
        choices=[
            ('woocommerce', 'WooCommerce'),
            ('shopify', 'Shopify'),
            ('manual', 'Manual'),
        ],
        default='manual'
    )
    
    class Meta:
        # ... موارد موجود
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'external_id'],
                condition=models.Q(external_id__isnull=False),
                name='unique_external_product_per_user'
            )
        ]
```

### 3. API Endpoints

#### 3.1 Token Management (Admin Only)

```python
# GET /api/v1/integrations/tokens/
# لیست تمام tokenها (admin می‌تونه همه رو ببینه)
# Response:
{
    "count": 10,
    "results": [
        {
            "id": "uuid",
            "user": {"id": 1, "email": "user@example.com"},
            "name": "فروشگاه اصلی",
            "integration_type": "woocommerce",
            "token_preview": "wc_sk...abc123",
            "is_active": true,
            "last_used_at": "2025-11-10T10:00:00Z",
            "usage_count": 150,
            "created_at": "2025-11-01T10:00:00Z"
        }
    ]
}

# POST /api/v1/integrations/tokens/generate/
# ساخت token جدید (admin برای هر کاربری می‌تونه بسازه)
# Request:
{
    "user_id": 123,  # اختیاری - اگه نباشه برای خود admin می‌سازه
    "integration_type": "woocommerce",
    "name": "فروشگاه اصلی"
}
# Response:
{
    "id": "uuid",
    "token": "wc_sk_live_a1b2c3d4e5f6...",  # فقط یکبار نمایش داده می‌شود
    "token_preview": "wc_sk...abc123",
    "integration_type": "woocommerce",
    "name": "فروشگاه اصلی",
    "created_at": "2025-11-10T10:00:00Z",
    "message": "⚠️ این token فقط یکبار نمایش داده می‌شود. لطفاً آن را کپی کنید."
}

# DELETE /api/v1/integrations/tokens/{id}/
# حذف/غیرفعال‌سازی token
# Response: 204 No Content
```

#### 3.2 WooCommerce Webhook

```python
# POST /api/integrations/woocommerce/webhook/
# دریافت رویدادهای WooCommerce
# Headers:
Authorization: Bearer wc_sk_live_a1b2c3d4...
Content-Type: application/json

# Request Body:
{
    "event_id": "wc_2025_11_10_54321",
    "event_type": "product.updated",
    "product": {
        "id": 414,
        "sku": "PROD-001",
        "name": "کفش اسپرت مردانه",
        "short_description": "کفش اسپرت سبک و راحت",
        "description": "این کفش با زیره نرم...",
        "price": 850000,
        "regular_price": 950000,
        "sale_price": 850000,
        "currency": "IRT",
        "stock_quantity": 12,
        "stock_status": "instock",
        "categories": ["کفش", "مردانه"],
        "tags": ["ورزشی", "تابستانی"],
        "image": "https://...",
        "gallery": ["https://...", "https://..."],
        "permalink": "https://...",
        "type": "simple",
        "date_modified": "2025-11-10T09:30:00Z"
    }
}

# Response (202 Accepted - فوری برمی‌گرده):
{
    "status": "accepted",
    "message": "رویداد دریافت شد و در صف پردازش قرار گرفت",
    "event_id": "wc_2025_11_10_54321"
}

# یا در صورت duplicate (200 OK):
{
    "status": "skipped",
    "message": "این رویداد قبلاً پردازش شده است",
    "event_id": "wc_2025_11_10_54321"
}

# یا در صورت خطا (400/401/500):
{
    "error": "Invalid token",
    "detail": "..."
}
```

#### 3.3 Health Check

```python
# GET /api/integrations/woocommerce/health/
# تست اتصال از پلاگین WordPress
# Headers:
Authorization: Bearer wc_sk_live_a1b2c3d4...

# Response (200 OK):
{
    "status": "ok",
    "message": "اتصال برقرار است",
    "user": {
        "id": 123,
        "email": "user@example.com",
        "username": "myshop"
    },
    "integration_type": "woocommerce",
    "timestamp": "2025-11-10T10:00:00Z"
}
```

#### 3.4 Event Logs (Admin)

```python
# GET /api/v1/integrations/woocommerce/events/
# مشاهده لاگ‌های sync
# Query params: ?user_id=123&event_type=product.updated&limit=50

# Response:
{
    "count": 150,
    "results": [
        {
            "id": "uuid",
            "event_id": "wc_2025_11_10_54321",
            "event_type": "product.updated",
            "user": {"id": 123, "email": "..."},
            "woo_product_id": 414,
            "processed_successfully": true,
            "created_at": "2025-11-10T10:00:00Z"
        }
    ]
}
```

### 4. Celery Tasks

```python
# integrations/tasks.py

from celery import shared_task
import logging

logger = logging.getLogger(__name__)

@shared_task(bind=True, max_retries=3, default_retry_delay=30)
def process_woocommerce_product(self, payload: dict):
    """
    پردازش async محصولات WooCommerce
    
    Flow:
    1. Parse payload
    2. Calculate content hash
    3. Update or Create Product
    4. Signal خودکار chunk می‌کنه
    
    Queue: default
    Priority: معمولی
    """
    try:
        from integrations.services.woocommerce_processor import WooCommerceProcessor
        
        processor = WooCommerceProcessor()
        result = processor.process_event(payload)
        
        return result
        
    except Exception as e:
        logger.error(f"Failed to process WooCommerce product: {e}")
        # Retry با exponential backoff
        raise self.retry(exc=e)
```

### 5. Service Layer

```python
# integrations/services/woocommerce_processor.py

import hashlib
from typing import Dict, Any
from web_knowledge.models import Product
from integrations.models import WooCommerceEventLog

class WooCommerceProcessor:
    """پردازشگر رویدادهای WooCommerce"""
    
    def process_event(self, payload: Dict[str, Any]) -> Dict[str, str]:
        """
        پردازش یک رویداد WooCommerce
        
        Args:
            payload: JSON دریافتی از WordPress
            
        Returns:
            نتیجه پردازش
        """
        event_type = payload.get('event_type')
        
        if event_type in ['product.created', 'product.updated']:
            return self._handle_product_upsert(payload)
        elif event_type == 'product.deleted':
            return self._handle_product_delete(payload)
        else:
            raise ValueError(f"Unknown event type: {event_type}")
    
    def _handle_product_upsert(self, payload: Dict) -> Dict:
        """ایجاد یا آپدیت محصول"""
        product_data = payload['product']
        user = self._get_user_from_payload(payload)
        
        # محاسبه hash محتوایی
        content_hash = self._calculate_content_hash(product_data)
        
        external_id = f"woo_{product_data['id']}"
        
        # پیدا کردن محصول موجود
        existing_product = Product.objects.filter(
            user=user,
            external_id=external_id
        ).first()
        
        # بررسی نیاز به regenerate embedding
        needs_embedding = True
        if existing_product:
            old_hash = existing_product.metadata.get('content_hash', '')
            if old_hash == content_hash:
                needs_embedding = False
        
        # آماده‌سازی داده‌ها
        product_defaults = {
            'title': product_data['name'],
            'description': product_data.get('description', ''),
            'short_description': product_data.get('short_description', ''),
            'price': product_data.get('price'),
            'currency': product_data.get('currency', 'IRT'),
            'stock_quantity': product_data.get('stock_quantity'),
            'in_stock': product_data.get('stock_status') == 'instock',
            'link': product_data.get('permalink', ''),
            'external_source': 'woocommerce',
            'tags': product_data.get('tags', []),
            'category': ', '.join(product_data.get('categories', [])),
            'metadata': {
                'woo_product_id': product_data['id'],
                'sku': product_data.get('sku', ''),
                'content_hash': content_hash,
                'regular_price': product_data.get('regular_price'),
                'sale_price': product_data.get('sale_price'),
                'on_sale': product_data.get('on_sale', False),
                'images': {
                    'main': product_data.get('image'),
                    'gallery': product_data.get('gallery', [])
                },
                'needs_embedding': needs_embedding,
            }
        }
        
        # Create or Update
        product, created = Product.objects.update_or_create(
            user=user,
            external_id=external_id,
            defaults=product_defaults
        )
        
        # Signal خودکار chunk می‌کنه (web_knowledge/signals.py)
        
        action = "created" if created else "updated"
        logger.info(f"✅ Product {action}: {product.title} (ID: {product.id})")
        
        return {
            'status': 'success',
            'action': action,
            'product_id': str(product.id),
            'needs_embedding': needs_embedding
        }
    
    def _handle_product_delete(self, payload: Dict) -> Dict:
        """حذف محصول (soft delete)"""
        product_data = payload['product']
        user = self._get_user_from_payload(payload)
        
        external_id = f"woo_{product_data['id']}"
        
        # Soft delete
        deleted_count = Product.objects.filter(
            user=user,
            external_id=external_id
        ).update(is_active=False)
        
        # Signal خودکار چانک‌ها رو حذف می‌کنه
        
        return {
            'status': 'success',
            'action': 'deleted',
            'deleted_count': deleted_count
        }
    
    def _calculate_content_hash(self, product_data: Dict) -> str:
        """محاسبه hash فقط از فیلدهای محتوایی"""
        critical_fields = [
            product_data.get('name', ''),
            product_data.get('short_description', ''),
            product_data.get('description', ''),
            ','.join(product_data.get('categories', [])),
            ','.join(product_data.get('tags', [])),
        ]
        content = '|'.join(critical_fields)
        return hashlib.sha256(content.encode('utf-8')).hexdigest()
    
    def _get_user_from_payload(self, payload: Dict):
        """استخراج user از payload (از token)"""
        # این تابع توسط view فراخوانی می‌شود و user قبلاً validate شده
        pass
```

### 6. Token Generator Service

```python
# integrations/services/token_generator.py

import secrets
import string

class TokenGenerator:
    """ساخت tokenهای امن برای integrations"""
    
    @staticmethod
    def generate_woocommerce_token() -> str:
        """
        ساخت token به فرمت:
        wc_sk_live_{40 random chars}
        
        مثال: wc_sk_live_a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0
        """
        alphabet = string.ascii_lowercase + string.digits
        random_part = ''.join(secrets.choice(alphabet) for _ in range(40))
        return f"wc_sk_live_{random_part}"
    
    @staticmethod
    def get_token_preview(token: str) -> str:
        """
        ساخت preview امن از token
        wc_sk_live_a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0
        -> wc_sk...s9t0
        """
        if len(token) < 15:
            return token[:8] + '...'
        return token[:6] + '...' + token[-6:]
```

### 7. Authentication Backend

```python
# integrations/backends/integration_auth.py

from rest_framework import authentication
from rest_framework.exceptions import AuthenticationFailed
from integrations.models import IntegrationToken
from django.utils import timezone

class IntegrationTokenAuthentication(authentication.BaseAuthentication):
    """
    احراز هویت با Integration Token
    Header: Authorization: Bearer wc_sk_live_...
    """
    
    def authenticate(self, request):
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        
        if not auth_header.startswith('Bearer '):
            return None
        
        token_string = auth_header[7:]  # حذف 'Bearer '
        
        try:
            token = IntegrationToken.objects.select_related('user').get(
                token=token_string,
                is_active=True
            )
        except IntegrationToken.DoesNotExist:
            raise AuthenticationFailed('Invalid or inactive token')
        
        # چک کردن انقضا
        if token.expires_at and token.expires_at < timezone.now():
            raise AuthenticationFailed('Token has expired')
        
        # آپدیت آمار استفاده
        token.last_used_at = timezone.now()
        token.usage_count += 1
        token.save(update_fields=['last_used_at', 'usage_count'])
        
        return (token.user, token)
    
    def authenticate_header(self, request):
        return 'Bearer'
```

---

## 🔌 معماری Plugin

### 1. ساختار فایل‌ها

```
fiko-woocommerce-sync/
├── fiko-woocommerce-sync.php       (Main plugin file - 30 lines)
├── includes/
│   ├── class-fiko-api.php          (API communication - 120 lines)
│   ├── class-fiko-hooks.php        (WooCommerce hooks - 100 lines)
│   └── helpers.php                 (Utilities - 60 lines)
├── admin/
│   ├── class-admin-page.php        (Settings UI - 180 lines)
│   ├── views/
│   │   └── settings.php            (HTML template - 100 lines)
│   ├── css/
│   │   └── admin.css               (Minimal styles - 50 lines)
│   └── js/
│       └── admin.js                (Test connection - 80 lines)
├── assets/
│   └── icon.png
├── uninstall.php                   (Cleanup - 25 lines)
└── readme.txt                      (WordPress standard)

تعداد کل خطوط: ~745 lines
```

### 2. Main Plugin File

```php
<?php
/**
 * Plugin Name: Fiko WooCommerce Sync
 * Plugin URI: https://fiko.ai
 * Description: سینک خودکار محصولات WooCommerce با پلتفرم فیکو
 * Version: 1.0.0
 * Author: Fiko Team
 * Author URI: https://fiko.ai
 * Text Domain: fiko-woocommerce-sync
 * Requires at least: 5.8
 * Requires PHP: 7.4
 * WC requires at least: 5.0
 * WC tested up to: 8.5
 */

defined('ABSPATH') || exit;

// Version
define('FIKO_WC_SYNC_VERSION', '1.0.0');
define('FIKO_WC_SYNC_PLUGIN_DIR', plugin_dir_path(__FILE__));
define('FIKO_WC_SYNC_PLUGIN_URL', plugin_dir_url(__FILE__));

// چک کردن WooCommerce
function fiko_wc_check_woocommerce() {
    if (!class_exists('WooCommerce')) {
        add_action('admin_notices', function() {
            echo '<div class="error"><p>پلاگین Fiko WooCommerce Sync نیاز به WooCommerce دارد.</p></div>';
        });
        return false;
    }
    return true;
}

// Load plugin
if (fiko_wc_check_woocommerce()) {
    require_once FIKO_WC_SYNC_PLUGIN_DIR . 'includes/helpers.php';
    require_once FIKO_WC_SYNC_PLUGIN_DIR . 'includes/class-fiko-api.php';
    require_once FIKO_WC_SYNC_PLUGIN_DIR . 'includes/class-fiko-hooks.php';
    
    if (is_admin()) {
        require_once FIKO_WC_SYNC_PLUGIN_DIR . 'admin/class-admin-page.php';
    }
    
    // Initialize
    add_action('plugins_loaded', function() {
        Fiko_WC_Hooks::init();
        if (is_admin()) {
            Fiko_WC_Admin_Page::init();
        }
    });
}
```

### 3. API Class (سبک و ساده)

```php
<?php
// includes/class-fiko-api.php

class Fiko_WC_API {
    
    private static $api_url = 'https://api.fiko.ai/api/integrations/woocommerce';
    
    /**
     * ارسال داده محصول به فیکو
     */
    public static function sync_product($product_id) {
        $token = get_option('fiko_wc_api_token');
        
        if (empty($token)) {
            return new WP_Error('no_token', 'API Token تنظیم نشده است');
        }
        
        // Debounce check (سبک)
        $transient_key = 'fiko_sync_' . $product_id;
        if (get_transient($transient_key)) {
            return new WP_Error('debounced', 'درخواست قبلی هنوز در حال پردازش است');
        }
        set_transient($transient_key, true, 30); // 30 seconds
        
        // ساخت payload
        $product = wc_get_product($product_id);
        if (!$product) {
            return new WP_Error('invalid_product', 'محصول یافت نشد');
        }
        
        $payload = self::build_payload($product, 'product.updated');
        
        // ارسال
        $response = wp_remote_post(self::$api_url . '/webhook/', [
            'headers' => [
                'Content-Type' => 'application/json',
                'Authorization' => 'Bearer ' . $token,
            ],
            'body' => wp_json_encode($payload),
            'timeout' => 10,
            'blocking' => false, // Non-blocking! فوری برمی‌گرده
        ]);
        
        if (is_wp_error($response)) {
            self::log_error($product_id, $response->get_error_message());
            return $response;
        }
        
        self::log_success($product_id, 'synced');
        return true;
    }
    
    /**
     * حذف محصول
     */
    public static function delete_product($product_id) {
        $token = get_option('fiko_wc_api_token');
        if (empty($token)) return;
        
        $product = wc_get_product($product_id);
        $payload = self::build_payload($product, 'product.deleted');
        
        wp_remote_post(self::$api_url . '/webhook/', [
            'headers' => [
                'Content-Type' => 'application/json',
                'Authorization' => 'Bearer ' . $token,
            ],
            'body' => wp_json_encode($payload),
            'timeout' => 10,
            'blocking' => false,
        ]);
    }
    
    /**
     * تست اتصال
     */
    public static function test_connection($token) {
        $response = wp_remote_get(self::$api_url . '/health/', [
            'headers' => [
                'Authorization' => 'Bearer ' . $token,
            ],
            'timeout' => 10,
        ]);
        
        if (is_wp_error($response)) {
            return [
                'success' => false,
                'message' => $response->get_error_message()
            ];
        }
        
        $code = wp_remote_retrieve_response_code($response);
        $body = json_decode(wp_remote_retrieve_body($response), true);
        
        if ($code === 200) {
            return [
                'success' => true,
                'message' => 'اتصال برقرار است!',
                'data' => $body
            ];
        }
        
        return [
            'success' => false,
            'message' => $body['error'] ?? 'خطای ناشناخته'
        ];
    }
    
    /**
     * ساخت JSON payload
     */
    private static function build_payload($product, $event_type) {
        $event_id = 'wc_' . date('Y_m_d_His') . '_' . $product->get_id();
        
        return [
            'event_id' => $event_id,
            'event_type' => $event_type,
            'product' => [
                'id' => $product->get_id(),
                'sku' => $product->get_sku(),
                'name' => $product->get_name(),
                'short_description' => $product->get_short_description(),
                'description' => $product->get_description(),
                'price' => (float) $product->get_price(),
                'regular_price' => (float) $product->get_regular_price(),
                'sale_price' => $product->get_sale_price() ? (float) $product->get_sale_price() : null,
                'currency' => get_woocommerce_currency(),
                'stock_quantity' => $product->get_stock_quantity(),
                'stock_status' => $product->get_stock_status(),
                'categories' => self::get_product_categories($product),
                'tags' => self::get_product_tags($product),
                'image' => wp_get_attachment_url($product->get_image_id()),
                'gallery' => self::get_gallery_images($product),
                'permalink' => get_permalink($product->get_id()),
                'type' => $product->get_type(),
                'on_sale' => $product->is_on_sale(),
                'date_modified' => $product->get_date_modified()->date('c'),
            ]
        ];
    }
    
    private static function get_product_categories($product) {
        $terms = get_the_terms($product->get_id(), 'product_cat');
        if (!$terms || is_wp_error($terms)) return [];
        return array_map(function($term) { return $term->name; }, $terms);
    }
    
    private static function get_product_tags($product) {
        $terms = get_the_terms($product->get_id(), 'product_tag');
        if (!$terms || is_wp_error($terms)) return [];
        return array_map(function($term) { return $term->name; }, $terms);
    }
    
    private static function get_gallery_images($product) {
        $image_ids = $product->get_gallery_image_ids();
        $images = [];
        foreach ($image_ids as $image_id) {
            $url = wp_get_attachment_url($image_id);
            if ($url) $images[] = $url;
        }
        return $images;
    }
    
    private static function log_success($product_id, $action) {
        update_post_meta($product_id, '_fiko_last_sync', current_time('mysql'));
        update_post_meta($product_id, '_fiko_sync_status', 'success');
    }
    
    private static function log_error($product_id, $message) {
        update_post_meta($product_id, '_fiko_sync_error', $message);
        update_post_meta($product_id, '_fiko_sync_status', 'error');
    }
}
```

### 4. Hooks Class

```php
<?php
// includes/class-fiko-hooks.php

class Fiko_WC_Hooks {
    
    public static function init() {
        // فقط اگر token وجود داشته باشد
        if (!get_option('fiko_wc_api_token')) {
            return;
        }
        
        // Product created/updated
        add_action('woocommerce_update_product', [__CLASS__, 'on_product_saved'], 10, 1);
        add_action('woocommerce_new_product', [__CLASS__, 'on_product_saved'], 10, 1);
        
        // Product deleted
        add_action('before_delete_post', [__CLASS__, 'on_product_deleted'], 10, 1);
    }
    
    public static function on_product_saved($product_id) {
        // فقط برای product type
        if (get_post_type($product_id) !== 'product') {
            return;
        }
        
        // Skip auto-saves and revisions
        if (wp_is_post_autosave($product_id) || wp_is_post_revision($product_id)) {
            return;
        }
        
        // Sync async
        Fiko_WC_API::sync_product($product_id);
    }
    
    public static function on_product_deleted($post_id) {
        if (get_post_type($post_id) !== 'product') {
            return;
        }
        
        Fiko_WC_API::delete_product($post_id);
    }
}
```

### 5. Admin Settings Page

```php
<?php
// admin/class-admin-page.php

class Fiko_WC_Admin_Page {
    
    public static function init() {
        add_action('admin_menu', [__CLASS__, 'add_menu']);
        add_action('admin_init', [__CLASS__, 'register_settings']);
        add_action('admin_enqueue_scripts', [__CLASS__, 'enqueue_assets']);
        
        // AJAX handler
        add_action('wp_ajax_fiko_wc_test_connection', [__CLASS__, 'ajax_test_connection']);
    }
    
    public static function add_menu() {
        add_submenu_page(
            'woocommerce',
            'فیکو - سینک محصولات',
            'فیکو Sync',
            'manage_options',
            'fiko-wc-sync',
            [__CLASS__, 'render_page']
        );
    }
    
    public static function register_settings() {
        register_setting('fiko_wc_sync', 'fiko_wc_api_token');
        register_setting('fiko_wc_sync', 'fiko_wc_enable_logging');
    }
    
    public static function enqueue_assets($hook) {
        if ($hook !== 'woocommerce_page_fiko-wc-sync') {
            return;
        }
        
        wp_enqueue_style(
            'fiko-wc-admin',
            FIKO_WC_SYNC_PLUGIN_URL . 'admin/css/admin.css',
            [],
            FIKO_WC_SYNC_VERSION
        );
        
        wp_enqueue_script(
            'fiko-wc-admin',
            FIKO_WC_SYNC_PLUGIN_URL . 'admin/js/admin.js',
            ['jquery'],
            FIKO_WC_SYNC_VERSION,
            true
        );
        
        wp_localize_script('fiko-wc-admin', 'fikoWC', [
            'ajax_url' => admin_url('admin-ajax.php'),
            'nonce' => wp_create_nonce('fiko_wc_test'),
        ]);
    }
    
    public static function render_page() {
        include FIKO_WC_SYNC_PLUGIN_DIR . 'admin/views/settings.php';
    }
    
    public static function ajax_test_connection() {
        check_ajax_referer('fiko_wc_test', 'nonce');
        
        if (!current_user_can('manage_options')) {
            wp_send_json_error(['message' => 'عدم دسترسی']);
        }
        
        $token = sanitize_text_field($_POST['token'] ?? '');
        
        if (empty($token)) {
            wp_send_json_error(['message' => 'لطفاً token را وارد کنید']);
        }
        
        $result = Fiko_WC_API::test_connection($token);
        
        if ($result['success']) {
            wp_send_json_success($result);
        } else {
            wp_send_json_error($result);
        }
    }
}
```

### 6. Settings Template (HTML)

```php
<?php
// admin/views/settings.php
defined('ABSPATH') || exit;

$token = get_option('fiko_wc_api_token', '');
$enable_logging = get_option('fiko_wc_enable_logging', false);

if (isset($_POST['fiko_wc_save_settings']) && check_admin_referer('fiko_wc_settings')) {
    update_option('fiko_wc_api_token', sanitize_text_field($_POST['fiko_wc_api_token']));
    update_option('fiko_wc_enable_logging', isset($_POST['fiko_wc_enable_logging']));
    echo '<div class="notice notice-success"><p>تنظیمات ذخیره شد.</p></div>';
    $token = get_option('fiko_wc_api_token');
}
?>

<div class="wrap fiko-wc-settings">
    <h1>🔄 فیکو - سینک محصولات WooCommerce</h1>
    
    <div class="fiko-wc-card">
        <h2>📌 راهنمای نصب</h2>
        <ol>
            <li>به داشبورد فیکو بروید: <a href="https://app.fiko.ai" target="_blank">app.fiko.ai</a></li>
            <li>به بخش <strong>تنظیمات > ادغام‌ها > WooCommerce</strong> بروید</li>
            <li>روی دکمه <strong>"ایجاد Token"</strong> کلیک کنید</li>
            <li>Token را کپی کرده و در کادر زیر paste کنید</li>
            <li>روی دکمه <strong>"تست اتصال"</strong> کلیک کنید</li>
            <li>در صورت موفقیت، <strong>"ذخیره"</strong> را بزنید</li>
        </ol>
    </div>
    
    <form method="post" action="" class="fiko-wc-form">
        <?php wp_nonce_field('fiko_wc_settings'); ?>
        
        <table class="form-table">
            <tr>
                <th scope="row">
                    <label for="fiko_wc_api_token">🔑 API Token</label>
                </th>
                <td>
                    <input 
                        type="text" 
                        id="fiko_wc_api_token" 
                        name="fiko_wc_api_token" 
                        value="<?php echo esc_attr($token); ?>" 
                        class="regular-text"
                        placeholder="wc_sk_live_..."
                    >
                    <p class="description">
                        Token را از داشبورد فیکو دریافت کنید
                    </p>
                </td>
            </tr>
            
            <tr>
                <th scope="row">⚙️ تنظیمات</th>
                <td>
                    <label>
                        <input 
                            type="checkbox" 
                            name="fiko_wc_enable_logging" 
                            <?php checked($enable_logging); ?>
                        >
                        فعال‌سازی لاگ‌ها (برای debugging)
                    </label>
                </td>
            </tr>
        </table>
        
        <p class="submit">
            <button type="button" id="fiko-test-connection" class="button">
                🔍 تست اتصال
            </button>
            <button type="submit" name="fiko_wc_save_settings" class="button button-primary">
                💾 ذخیره تنظیمات
            </button>
        </p>
    </form>
    
    <div id="fiko-test-result" style="display:none;"></div>
    
    <?php if ($token): ?>
    <div class="fiko-wc-card">
        <h2>✅ وضعیت سینک</h2>
        <p>پلاگین فعال است و تغییرات محصولات به‌صورت خودکار به فیکو ارسال می‌شود.</p>
        
        <h3>رویدادهای سینک شده:</h3>
        <ul>
            <li>✅ ایجاد محصول جدید</li>
            <li>✅ ویرایش محصول</li>
            <li>✅ حذف محصول</li>
        </ul>
    </div>
    <?php endif; ?>
</div>
```

### 7. JavaScript (Test Connection)

```javascript
// admin/js/admin.js

jQuery(document).ready(function($) {
    $('#fiko-test-connection').on('click', function() {
        const button = $(this);
        const token = $('#fiko_wc_api_token').val();
        const resultDiv = $('#fiko-test-result');
        
        if (!token) {
            alert('لطفاً ابتدا API Token را وارد کنید');
            return;
        }
        
        button.prop('disabled', true).text('⏳ در حال تست...');
        resultDiv.hide();
        
        $.ajax({
            url: fikoWC.ajax_url,
            method: 'POST',
            data: {
                action: 'fiko_wc_test_connection',
                nonce: fikoWC.nonce,
                token: token
            },
            success: function(response) {
                if (response.success) {
                    resultDiv.html(
                        '<div class="notice notice-success">' +
                        '<p><strong>✅ ' + response.data.message + '</strong></p>' +
                        '<p>کاربر: ' + response.data.data.user.email + '</p>' +
                        '</div>'
                    ).show();
                } else {
                    resultDiv.html(
                        '<div class="notice notice-error">' +
                        '<p><strong>❌ خطا:</strong> ' + response.data.message + '</p>' +
                        '</div>'
                    ).show();
                }
            },
            error: function() {
                resultDiv.html(
                    '<div class="notice notice-error">' +
                    '<p>خطا در برقراری ارتباط</p>' +
                    '</div>'
                ).show();
            },
            complete: function() {
                button.prop('disabled', false).text('🔍 تست اتصال');
            }
        });
    });
});
```

---

## 🔄 جریان کامل (Flow)

### مثال: کاربر محصول جدید می‌سازد

```
1. کاربر در WooCommerce محصول "کفش اسپرت" را ایجاد می‌کند
   └─> WordPress: woocommerce_new_product hook

2. Plugin: Fiko_WC_Hooks::on_product_saved()
   ├─> Debounce check (transient) - OK
   ├─> Build JSON payload
   └─> wp_remote_post (non-blocking) به Django
       └─> 202 Accepted (فوری برمی‌گرده)

3. Django View: WooCommerceWebhookView
   ├─> Validate token ✓
   ├─> Check duplicate event_id
   │   └─> WooCommerceEventLog.objects.filter(event_id=...).exists()
   │       └─> False (جدید است)
   ├─> Create event log
   └─> Dispatch Celery task
       └─> process_woocommerce_product.apply_async()

4. Celery Worker (queue: default)
   ├─> WooCommerceProcessor.process_event()
   ├─> Calculate content_hash
   ├─> Product.objects.update_or_create()
   │   └─> external_id="woo_414"
   │       defaults={...}
   └─> ✅ محصول ایجاد شد

5. Django Signal (post_save) - خودکار!
   └─> sync_product_to_knowledge_base()
       ├─> Generate TL;DR
       ├─> Generate embeddings (OpenAI)
       └─> TenantKnowledge.objects.create()
           └─> ✅ چانک ایجاد شد

6. نتیجه نهایی:
   ✅ محصول در web_knowledge.Product
   ✅ چانک در TenantKnowledge با embedding
   ✅ آماده برای RAG و جستجو
```

### مثال: کاربر قیمت محصول را تغییر می‌دهد

```
1. قیمت از 950,000 به 850,000 تغییر می‌کند
   └─> woocommerce_update_product hook

2. Plugin → Django (مثل بالا)

3. Celery: WooCommerceProcessor
   ├─> محاسبه content_hash
   │   └─> Hash محتوا (name, description, categories, tags)
   ├─> مقایسه با hash قبلی
   │   └─> ⚠️ محتوا تغییر نکرده! (فقط قیمت)
   ├─> Product.objects.update_or_create()
   │   └─> فقط metadata آپدیت می‌شود
   │       metadata['price'] = 850000
   └─> ✅ بدون regenerate embedding

4. Signal:
   └─> چک می‌کنه محتوا تغییر کرده؟
       └─> خیر → فقط metadata آپدیت می‌شه
           └─> ✅ هزینه embedding ذخیره شد
```

---

## 📝 راهنمای پیاده‌سازی گام‌به‌گام

### فاز 1: Backend Django

#### گام 1: ایجاد App
```bash
cd src
python manage.py startapp integrations
```

#### گام 2: اضافه کردن به INSTALLED_APPS
```python
# core/settings/common.py
INSTALLED_APPS = [
    # ...
    'integrations',
]
```

#### گام 3: ایجاد Models
- `IntegrationToken`
- `WooCommerceEventLog`
- Migration برای اضافه کردن `external_id` به `Product`

#### گام 4: ایجاد Serializers
- `IntegrationTokenSerializer`
- `WooCommerceWebhookSerializer`
- `EventLogSerializer`

#### گام 5: ایجاد Views
- `IntegrationTokenViewSet` (Admin only)
- `WooCommerceWebhookView`
- `WooCommerceHealthCheckView`
- `EventLogViewSet` (Admin only)

#### گام 6: ایجاد Authentication Backend
- `IntegrationTokenAuthentication`

#### گام 7: ایجاد Services
- `TokenGenerator`
- `WooCommerceProcessor`

#### گام 8: ایجاد Celery Task
- `process_woocommerce_product`
- اضافه کردن به `celery.py` task routes

#### گام 9: Admin Panel
- `IntegrationTokenAdmin`
- `WooCommerceEventLogAdmin`

#### گام 10: URLs
```python
# integrations/urls.py
urlpatterns = [
    path('tokens/', IntegrationTokenViewSet.as_view(...)),
    path('woocommerce/webhook/', WooCommerceWebhookView.as_view()),
    path('woocommerce/health/', WooCommerceHealthCheckView.as_view()),
    path('woocommerce/events/', EventLogViewSet.as_view(...)),
]

# core/urls.py
urlpatterns += [
    path('api/integrations/', include('integrations.urls')),
]
```

### فاز 2: Plugin WordPress

#### گام 1: ساخت ساختار فولدر
```bash
mkdir -p fiko-woocommerce-sync/{includes,admin/{views,css,js},assets}
```

#### گام 2: فایل‌های اصلی
- `fiko-woocommerce-sync.php`
- `includes/class-fiko-api.php`
- `includes/class-fiko-hooks.php`
- `includes/helpers.php`

#### گام 3: Admin Panel
- `admin/class-admin-page.php`
- `admin/views/settings.php`
- `admin/css/admin.css`
- `admin/js/admin.js`

#### گام 4: Cleanup
- `uninstall.php`

#### گام 5: Documentation
- `readme.txt` (WordPress standard)

### فاز 3: تست

#### Backend Testing
```python
# tests/test_integration_token.py
def test_token_generation():
    token = TokenGenerator.generate_woocommerce_token()
    assert token.startswith('wc_sk_live_')
    assert len(token) == 51

def test_webhook_authentication():
    # ...

def test_duplicate_event():
    # ...

def test_content_hash_calculation():
    # ...
```

#### Plugin Testing
1. نصب پلاگین در WordPress
2. تست connection
3. ایجاد/ویرایش/حذف محصول
4. بررسی لاگ‌ها در Django admin

---

## 🧪 تست و راه‌اندازی

### Checklist نصب Backend

- [ ] Migration اجرا شده
- [ ] Admin user ساخته شده
- [ ] Token برای تست ایجاد شده
- [ ] Celery worker در حال اجرا
- [ ] Redis/RabbitMQ فعال
- [ ] Endpoint `/api/integrations/woocommerce/health/` پاسخ می‌دهد

### Checklist نصب Plugin

- [ ] WooCommerce نصب و فعال است
- [ ] پلاگین آپلود و فعال شده
- [ ] Token در تنظیمات وارد شده
- [ ] تست اتصال موفق
- [ ] محصول تستی ایجاد شده
- [ ] در Django admin لاگ ثبت شده
- [ ] در TenantKnowledge چانک ایجاد شده

### سناریوهای تست

#### تست 1: ایجاد محصول
```
1. در WooCommerce محصول جدید بساز
2. بررسی کن:
   - در WordPress: _fiko_sync_status = success
   - در Django: WooCommerceEventLog ثبت شده
   - در Django: Product ایجاد شده با external_id=woo_X
   - در Django: TenantKnowledge چانک دارد
```

#### تست 2: ویرایش قیمت
```
1. قیمت محصول را تغییر بده (بدون تغییر توضیحات)
2. بررسی کن:
   - Product.metadata['price'] آپدیت شده
   - TenantKnowledge embedding تغییر نکرده (Smart Sync)
```

#### تست 3: ویرایش توضیحات
```
1. توضیحات محصول را تغییر بده
2. بررسی کن:
   - Product.metadata['content_hash'] تغییر کرده
   - TenantKnowledge embedding جدید ساخته شده
```

#### تست 4: حذف محصول
```
1. محصول را حذف کن
2. بررسی کن:
   - Product.is_active = False (soft delete)
   - TenantKnowledge chunks حذف شده
```

#### تست 5: Duplicate Prevention
```
1. محصول را 2 بار پشت سر هم ذخیره کن
2. بررسی کن:
   - فقط 1 event log ثبت شده
   - یا اگر 2 تا ثبت شده، duplicate skip شده
```

---

## 📊 مانیتورینگ و آمار

### Metrics برای Monitoring

```python
# integrations/metrics.py (اختیاری)

from prometheus_client import Counter, Histogram

woocommerce_events_total = Counter(
    'woocommerce_events_total',
    'Total WooCommerce events received',
    ['event_type', 'status']
)

woocommerce_processing_duration = Histogram(
    'woocommerce_processing_duration_seconds',
    'Time spent processing WooCommerce events'
)
```

### لاگ‌های مفید

```python
# در هر مرحله:
logger.info(f"✅ WooCommerce product created: {product.title}")
logger.warning(f"⚠️ Duplicate event skipped: {event_id}")
logger.error(f"❌ Failed to process: {error}")
```

### Admin Dashboard

در Django admin می‌توانید:
- لیست tokenها را ببینید
- آمار استفاده هر token
- لاگ رویدادها (موفق/ناموفق)
- محصولات sync شده

---

## 🔒 امنیت

### Best Practices

1. **Token Security**
   - Token فقط یکبار نمایش داده می‌شود
   - در database به‌صورت plain ذخیره می‌شود (چون باید match کنیم)
   - اما در WordPress می‌توان encrypt کرد

2. **Rate Limiting**
   ```python
   # در view
   throttle_classes = [UserRateThrottle]
   throttle_scope = 'woocommerce_webhook'
   ```

3. **IP Whitelist** (اختیاری)
   ```python
   # در authentication
   if token.allowed_ips:
       client_ip = request.META.get('REMOTE_ADDR')
       if client_ip not in token.allowed_ips:
           raise PermissionDenied()
   ```

4. **HTTPS Only**
   - تمام ارتباطات حتماً از HTTPS
   - در WordPress: `FORCE_SSL_ADMIN = true`

---

## 🚀 بهینه‌سازی

### Performance Tips

1. **Non-blocking در WordPress**
   ```php
   'blocking' => false  // فوری برمی‌گرده
   ```

2. **Batch Processing** (فاز 2)
   - برای bulk import اولیه
   - Action Scheduler استفاده کنیم

3. **Caching**
   - Token lookup را cache کنیم (Redis)
   - Embedding cache (قبلاً هست)

4. **Database Indexes**
   - روی `external_id`, `event_id`, `token`

---

## 📝 یادداشت‌های مهم

### محدودیت‌های نسخه اولیه (v1.0)

- ❌ Variable Products (فاز 2)
- ❌ Bulk Sync اولیه (فاز 2)
- ❌ Sync دوطرفه (فاز 3)
- ❌ Conflict Resolution (فاز 3)
- ❌ Webhook Signature (فاز 2)

### نکات پیاده‌سازی

1. **از signal موجود استفاده کنیم**
   - `web_knowledge/signals.py` خودکار chunk می‌کنه
   - نیازی به کد اضافه نیست

2. **Smart Sync خیلی مهمه**
   - صرفه‌جویی در هزینه embedding
   - سرعت بیشتر

3. **Idempotency ضروریه**
   - WooCommerce ممکنه چند بار بفرسته
   - باید safe باشه

4. **Logging برای debugging**
   - همه چیز رو log کنیم (حداقل در dev)

---

## 📞 پشتیبانی و مستندات

### لینک‌های مفید

- [WooCommerce Hooks Reference](https://woocommerce.github.io/code-reference/hooks/hooks.html)
- [Django Celery](https://docs.celeryproject.org/)
- [pgvector](https://github.com/pgvector/pgvector)

### سوالات متداول

**Q: چرا embedding regenerate نمی‌شه وقتی قیمت تغییر می‌کنه؟**
A: برای صرفه‌جویی در هزینه. قیمت در metadata ذخیره می‌شه.

**Q: چند وقت طول می‌کشه تا محصول چانک بشه؟**
A: معمولاً 10-60 ثانیه (بسته به صف Celery)

**Q: آیا محصولات موجود رو هم sync می‌کنه؟**
A: نه، فعلاً فقط تغییرات جدید. برای bulk sync از endpoint جداگانه استفاده کنید (فاز 2)

---

## ✅ چک‌لیست پیاده‌سازی

### Backend
- [ ] Models ایجاد شده
- [ ] Migrations اجرا شده
- [ ] Serializers نوشته شده
- [ ] Views پیاده شده
- [ ] Authentication backend آماده
- [ ] Services ایجاد شده
- [ ] Celery task نوشته شده
- [ ] Admin panel تنظیم شده
- [ ] URLs اضافه شده
- [ ] Tests نوشته شده

### Plugin
- [ ] ساختار فایل‌ها آماده
- [ ] Main plugin file
- [ ] API class
- [ ] Hooks class
- [ ] Admin page
- [ ] Settings template
- [ ] JavaScript برای test
- [ ] CSS styling
- [ ] Uninstall script
- [ ] readme.txt

### Testing
- [ ] Unit tests نوشته شده
- [ ] Integration tests
- [ ] تست در محیط staging
- [ ] تست با محصولات واقعی
- [ ] تست performance
- [ ] تست security

---

**تاریخ ایجاد:** 2025-11-10  
**نسخه:** 1.0  
**نویسنده:** Fiko Backend Team

