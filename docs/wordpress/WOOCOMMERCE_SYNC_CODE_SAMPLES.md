# 💻 WooCommerce Sync - نمونه کدهای کامل

این فایل حاوی کدهای آماده برای شروع سریع پیاده‌سازی است.

---

## 📦 Backend: Models

### integrations/models.py

```python
from django.db import models
from django.conf import settings
from django.utils import timezone
import uuid


class IntegrationToken(models.Model):
    """API Tokens for external integrations (WooCommerce, Shopify, ...)"""
    
    INTEGRATION_TYPES = [
        ('woocommerce', 'WooCommerce'),
        ('shopify', 'Shopify'),
        ('custom', 'Custom Integration'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='integration_tokens'
    )
    
    # Token (shown only once)
    token = models.CharField(max_length=128, unique=True, db_index=True)
    token_preview = models.CharField(max_length=20, help_text="wc_sk...abc123")
    
    integration_type = models.CharField(max_length=20, choices=INTEGRATION_TYPES)
    name = models.CharField(
        max_length=100,
        help_text="Friendly name (e.g., 'Main Store')"
    )
    
    # Security & Tracking
    is_active = models.BooleanField(default=True)
    last_used_at = models.DateTimeField(null=True, blank=True)
    usage_count = models.IntegerField(default=0)
    
    # Optional: IP Whitelist
    allowed_ips = models.JSONField(
        default=list,
        blank=True,
        help_text="List of allowed IPs (empty = all allowed)"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Token expiration (null = never expires)"
    )
    
    class Meta:
        db_table = 'integration_tokens'
        verbose_name = "🔑 Integration Token"
        verbose_name_plural = "🔑 Integration Tokens"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'integration_type', 'is_active']),
            models.Index(fields=['token']),
            models.Index(fields=['is_active']),
        ]
    
    def __str__(self):
        return f"{self.user.email} - {self.name} ({self.integration_type})"
    
    def is_valid(self):
        """Check if token is active and not expired"""
        if not self.is_active:
            return False
        if self.expires_at and self.expires_at < timezone.now():
            return False
        return True


class WooCommerceEventLog(models.Model):
    """Log of all WooCommerce webhook events"""
    
    EVENT_TYPES = [
        ('product.created', 'Product Created'),
        ('product.updated', 'Product Updated'),
        ('product.deleted', 'Product Deleted'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Event Info
    event_id = models.CharField(
        max_length=100,
        unique=True,
        db_index=True,
        help_text="Unique event ID from WooCommerce"
    )
    event_type = models.CharField(max_length=30, choices=EVENT_TYPES)
    
    # References
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='woocommerce_events'
    )
    token = models.ForeignKey(
        IntegrationToken,
        on_delete=models.SET_NULL,
        null=True,
        related_name='events'
    )
    woo_product_id = models.IntegerField(help_text="Product ID in WooCommerce")
    
    # Data
    payload = models.JSONField(help_text="Full webhook payload")
    
    # Processing
    processed_successfully = models.BooleanField(default=True)
    error_message = models.TextField(blank=True, null=True)
    processing_time_ms = models.IntegerField(
        null=True,
        blank=True,
        help_text="Processing time in milliseconds"
    )
    
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
            models.Index(fields=['woo_product_id']),
            models.Index(fields=['processed_successfully']),
        ]
    
    def __str__(self):
        status = "✅" if self.processed_successfully else "❌"
        return f"{status} {self.event_type} - Product {self.woo_product_id}"
```

---

## 🔐 Backend: Authentication

### integrations/backends/integration_auth.py

```python
from rest_framework import authentication
from rest_framework.exceptions import AuthenticationFailed
from integrations.models import IntegrationToken
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)


class IntegrationTokenAuthentication(authentication.BaseAuthentication):
    """
    Custom authentication for Integration Tokens
    
    Header: Authorization: Bearer wc_sk_live_...
    """
    
    keyword = 'Bearer'
    
    def authenticate(self, request):
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        
        if not auth_header:
            return None
        
        if not auth_header.startswith(self.keyword + ' '):
            return None
        
        token_string = auth_header[len(self.keyword) + 1:]
        
        if not token_string:
            raise AuthenticationFailed('No token provided')
        
        return self.authenticate_credentials(token_string, request)
    
    def authenticate_credentials(self, token_string, request):
        try:
            token = IntegrationToken.objects.select_related('user').get(
                token=token_string
            )
        except IntegrationToken.DoesNotExist:
            logger.warning(f"Invalid token attempt: {token_string[:20]}...")
            raise AuthenticationFailed('Invalid token')
        
        if not token.is_active:
            logger.warning(f"Inactive token used: {token.id}")
            raise AuthenticationFailed('Token is inactive')
        
        if token.expires_at and token.expires_at < timezone.now():
            logger.warning(f"Expired token used: {token.id}")
            raise AuthenticationFailed('Token has expired')
        
        # Optional: Check IP whitelist
        if token.allowed_ips:
            client_ip = self.get_client_ip(request)
            if client_ip not in token.allowed_ips:
                logger.warning(f"IP not whitelisted: {client_ip} for token {token.id}")
                raise AuthenticationFailed('IP address not allowed')
        
        # Update usage stats
        token.last_used_at = timezone.now()
        token.usage_count += 1
        token.save(update_fields=['last_used_at', 'usage_count'])
        
        logger.info(f"Token authenticated: {token.id} (user: {token.user.email})")
        
        return (token.user, token)
    
    def authenticate_header(self, request):
        return self.keyword
    
    @staticmethod
    def get_client_ip(request):
        """Get client IP from request"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
```

---

## 🛠️ Backend: Services

### integrations/services/token_generator.py

```python
import secrets
import string


class TokenGenerator:
    """Generate secure tokens for integrations"""
    
    @staticmethod
    def generate_woocommerce_token() -> str:
        """
        Generate WooCommerce-style token
        
        Format: wc_sk_live_{40 random chars}
        Example: wc_sk_live_a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0
        """
        alphabet = string.ascii_lowercase + string.digits
        random_part = ''.join(secrets.choice(alphabet) for _ in range(40))
        return f"wc_sk_live_{random_part}"
    
    @staticmethod
    def generate_shopify_token() -> str:
        """Generate Shopify-style token"""
        alphabet = string.ascii_lowercase + string.digits
        random_part = ''.join(secrets.choice(alphabet) for _ in range(32))
        return f"shpat_{random_part}"
    
    @staticmethod
    def get_token_preview(token: str, show_first: int = 6, show_last: int = 6) -> str:
        """
        Create safe preview of token
        
        Example:
            wc_sk_live_a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0
            -> wc_sk...s9t0
        """
        if len(token) < show_first + show_last + 3:
            return token[:show_first] + '...'
        return token[:show_first] + '...' + token[-show_last:]


class WooCommerceProcessor:
    """Process WooCommerce webhook events"""
    
    def __init__(self, user=None, token=None):
        self.user = user
        self.token = token
    
    def process_event(self, payload: dict) -> dict:
        """
        Process a WooCommerce event
        
        Args:
            payload: Webhook payload from WordPress
            
        Returns:
            Processing result
        """
        import hashlib
        from web_knowledge.models import Product
        
        event_type = payload.get('event_type')
        
        if event_type in ['product.created', 'product.updated']:
            return self._handle_product_upsert(payload)
        elif event_type == 'product.deleted':
            return self._handle_product_delete(payload)
        else:
            raise ValueError(f"Unknown event type: {event_type}")
    
    def _handle_product_upsert(self, payload: dict) -> dict:
        """Create or update product"""
        from web_knowledge.models import Product
        from decimal import Decimal
        import logging
        
        logger = logging.getLogger(__name__)
        product_data = payload['product']
        
        # Calculate content hash
        content_hash = self._calculate_content_hash(product_data)
        
        external_id = f"woo_{product_data['id']}"
        
        # Find existing product
        existing_product = Product.objects.filter(
            user=self.user,
            external_id=external_id
        ).first()
        
        # Check if embedding regeneration needed
        needs_embedding = True
        if existing_product:
            old_hash = existing_product.metadata.get('content_hash', '')
            if old_hash == content_hash:
                needs_embedding = False
                logger.info(f"📝 Content unchanged, updating metadata only")
        
        # Prepare product data
        product_defaults = {
            'title': product_data['name'],
            'description': product_data.get('description', ''),
            'short_description': product_data.get('short_description', ''),
            'price': Decimal(str(product_data.get('price', 0))) if product_data.get('price') else None,
            'currency': product_data.get('currency', 'IRT'),
            'stock_quantity': product_data.get('stock_quantity'),
            'in_stock': product_data.get('stock_status') == 'instock',
            'link': product_data.get('permalink', ''),
            'external_source': 'woocommerce',
            'is_active': True,
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
                'last_sync_at': str(timezone.now()),
            }
        }
        
        # Create or Update
        product, created = Product.objects.update_or_create(
            user=self.user,
            external_id=external_id,
            defaults=product_defaults
        )
        
        # Signal will auto-chunk (web_knowledge/signals.py)
        
        action = "created" if created else "updated"
        logger.info(f"✅ Product {action}: {product.title} (ID: {product.id})")
        
        return {
            'status': 'success',
            'action': action,
            'product_id': str(product.id),
            'needs_embedding': needs_embedding
        }
    
    def _handle_product_delete(self, payload: dict) -> dict:
        """Soft delete product"""
        from web_knowledge.models import Product
        import logging
        
        logger = logging.getLogger(__name__)
        product_data = payload['product']
        
        external_id = f"woo_{product_data['id']}"
        
        # Soft delete
        deleted_count = Product.objects.filter(
            user=self.user,
            external_id=external_id
        ).update(is_active=False)
        
        # Signal will auto-cleanup chunks
        
        logger.info(f"🗑️ Product soft-deleted: {external_id}")
        
        return {
            'status': 'success',
            'action': 'deleted',
            'deleted_count': deleted_count
        }
    
    def _calculate_content_hash(self, product_data: dict) -> str:
        """Calculate hash from content fields only"""
        import hashlib
        
        critical_fields = [
            product_data.get('name', ''),
            product_data.get('short_description', ''),
            product_data.get('description', ''),
            ','.join(product_data.get('categories', [])),
            ','.join(product_data.get('tags', [])),
        ]
        content = '|'.join(critical_fields)
        return hashlib.sha256(content.encode('utf-8')).hexdigest()
```

---

## 📡 Backend: Views

### integrations/views.py

```python
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from integrations.models import IntegrationToken, WooCommerceEventLog
from integrations.backends.integration_auth import IntegrationTokenAuthentication
from integrations.services.token_generator import TokenGenerator, WooCommerceProcessor
from integrations.tasks import process_woocommerce_product
from django.utils import timezone
import logging
import time

logger = logging.getLogger(__name__)


class GenerateTokenView(APIView):
    """
    Generate new integration token (Admin only)
    
    POST /api/v1/integrations/tokens/generate/
    """
    permission_classes = [IsAuthenticated, IsAdminUser]
    
    def post(self, request):
        user_id = request.data.get('user_id')
        integration_type = request.data.get('integration_type', 'woocommerce')
        name = request.data.get('name', 'Integration Token')
        
        # Determine user (admin can create for others)
        if user_id and request.user.is_staff:
            from accounts.models import User
            try:
                user = User.objects.get(id=user_id)
            except User.DoesNotExist:
                return Response(
                    {'error': 'User not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
        else:
            user = request.user
        
        # Generate token
        if integration_type == 'woocommerce':
            token_string = TokenGenerator.generate_woocommerce_token()
        elif integration_type == 'shopify':
            token_string = TokenGenerator.generate_shopify_token()
        else:
            return Response(
                {'error': 'Invalid integration type'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        token_preview = TokenGenerator.get_token_preview(token_string)
        
        # Create token
        token = IntegrationToken.objects.create(
            user=user,
            token=token_string,
            token_preview=token_preview,
            integration_type=integration_type,
            name=name
        )
        
        logger.info(f"✅ Token created: {token.id} for user {user.email}")
        
        return Response({
            'id': str(token.id),
            'token': token_string,  # ⚠️ Shown only once!
            'token_preview': token_preview,
            'integration_type': integration_type,
            'name': name,
            'user': {
                'id': user.id,
                'email': user.email
            },
            'created_at': token.created_at,
            'message': '⚠️ این token فقط یکبار نمایش داده می‌شود. لطفاً آن را کپی کنید.'
        }, status=status.HTTP_201_CREATED)


class WooCommerceWebhookView(APIView):
    """
    Receive WooCommerce webhook events
    
    POST /api/integrations/woocommerce/webhook/
    """
    authentication_classes = [IntegrationTokenAuthentication]
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        start_time = time.time()
        
        payload = request.data
        event_id = payload.get('event_id')
        event_type = payload.get('event_type')
        product_data = payload.get('product', {})
        
        if not event_id or not event_type:
            return Response(
                {'error': 'Missing event_id or event_type'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check for duplicate (idempotency)
        if WooCommerceEventLog.objects.filter(event_id=event_id).exists():
            logger.info(f"⏭️ Duplicate event skipped: {event_id}")
            return Response({
                'status': 'skipped',
                'message': 'این رویداد قبلاً پردازش شده است',
                'event_id': event_id
            }, status=status.HTTP_200_OK)
        
        # Get token from auth
        token = request.auth  # IntegrationToken instance
        
        # Create event log
        event_log = WooCommerceEventLog.objects.create(
            event_id=event_id,
            event_type=event_type,
            user=request.user,
            token=token,
            woo_product_id=product_data.get('id', 0),
            payload=payload,
            source_ip=self._get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')[:500]
        )
        
        # Dispatch async task
        process_woocommerce_product.apply_async(
            args=[payload, request.user.id, str(event_log.id)],
            countdown=2  # Small delay to batch rapid changes
        )
        
        processing_time = int((time.time() - start_time) * 1000)
        
        logger.info(
            f"✅ Event accepted: {event_type} for product {product_data.get('id')} "
            f"(user: {request.user.email}, time: {processing_time}ms)"
        )
        
        return Response({
            'status': 'accepted',
            'message': 'رویداد دریافت شد و در صف پردازش قرار گرفت',
            'event_id': event_id,
            'processing_time_ms': processing_time
        }, status=status.HTTP_202_ACCEPTED)
    
    def _get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class WooCommerceHealthCheckView(APIView):
    """
    Test connection from WordPress plugin
    
    GET /api/integrations/woocommerce/health/
    """
    authentication_classes = [IntegrationTokenAuthentication]
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        token = request.auth
        
        return Response({
            'status': 'ok',
            'message': 'اتصال برقرار است',
            'user': {
                'id': request.user.id,
                'email': request.user.email,
                'username': request.user.username
            },
            'token': {
                'id': str(token.id),
                'integration_type': token.integration_type,
                'name': token.name,
                'last_used_at': token.last_used_at,
                'usage_count': token.usage_count
            },
            'timestamp': timezone.now()
        }, status=status.HTTP_200_OK)
```

---

## ⚙️ Backend: Celery Task

### integrations/tasks.py (یا AI_model/tasks.py)

```python
from celery import shared_task
import logging
import time

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=30)
def process_woocommerce_product(self, payload: dict, user_id: int, event_log_id: str):
    """
    Process WooCommerce product async
    
    Args:
        payload: Webhook data
        user_id: User ID
        event_log_id: WooCommerceEventLog ID
        
    Queue: default
    """
    from integrations.services.token_generator import WooCommerceProcessor
    from integrations.models import WooCommerceEventLog
    from accounts.models import User
    
    start_time = time.time()
    
    try:
        # Get user
        user = User.objects.get(id=user_id)
        
        # Process
        processor = WooCommerceProcessor(user=user)
        result = processor.process_event(payload)
        
        # Update event log
        processing_time = int((time.time() - start_time) * 1000)
        WooCommerceEventLog.objects.filter(id=event_log_id).update(
            processed_successfully=True,
            processing_time_ms=processing_time
        )
        
        logger.info(f"✅ WooCommerce product processed: {result}")
        
        return result
        
    except Exception as e:
        logger.error(f"❌ Failed to process WooCommerce product: {e}")
        
        # Update event log with error
        WooCommerceEventLog.objects.filter(id=event_log_id).update(
            processed_successfully=False,
            error_message=str(e)
        )
        
        # Retry with exponential backoff
        raise self.retry(exc=e, countdown=2 ** self.request.retries * 30)
```

---

## 🔧 Backend: URLs

### integrations/urls.py

```python
from django.urls import path
from integrations import views

urlpatterns = [
    # Token management (admin only)
    path('tokens/generate/', views.GenerateTokenView.as_view(), name='generate-token'),
    
    # WooCommerce webhook
    path('woocommerce/webhook/', views.WooCommerceWebhookView.as_view(), name='woocommerce-webhook'),
    path('woocommerce/health/', views.WooCommerceHealthCheckView.as_view(), name='woocommerce-health'),
]
```

### core/urls.py (اضافه کردن)

```python
urlpatterns = [
    # ... existing patterns
    path('api/integrations/', include('integrations.urls')),
]
```

---

## 🗄️ Backend: Migration

### Add external_id to Product

```bash
python manage.py makemigrations web_knowledge --name add_external_id_to_product
```

```python
# Generated migration file

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('web_knowledge', '0XXX_previous_migration'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='external_id',
            field=models.CharField(
                max_length=100,
                blank=True,
                null=True,
                db_index=True,
                help_text='External product ID (e.g., woo_414)'
            ),
        ),
        migrations.AddField(
            model_name='product',
            name='external_source',
            field=models.CharField(
                max_length=20,
                blank=True,
                choices=[
                    ('woocommerce', 'WooCommerce'),
                    ('shopify', 'Shopify'),
                    ('manual', 'Manual'),
                ],
                default='manual'
            ),
        ),
        migrations.AddConstraint(
            model_name='product',
            constraint=models.UniqueConstraint(
                fields=['user', 'external_id'],
                condition=models.Q(external_id__isnull=False),
                name='unique_external_product_per_user'
            ),
        ),
    ]
```

---

این نمونه کدها آماده استفاده هستند. برای جزئیات بیشتر به `WOOCOMMERCE_SYNC_ARCHITECTURE.md` مراجعه کنید.

