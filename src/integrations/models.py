from django.db import models
from django.conf import settings
from django.utils import timezone
import uuid


class IntegrationToken(models.Model):
    """
    API Tokens for external integrations (WooCommerce, Shopify, etc.)
    Each user can have multiple tokens (for different stores)
    """
    
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
    
    # Token (shown only once upon creation)
    token = models.CharField(max_length=128, unique=True, db_index=True)
    token_preview = models.CharField(
        max_length=20,
        help_text="Safe preview (e.g., wc_sk...abc123)"
    )
    
    integration_type = models.CharField(max_length=20, choices=INTEGRATION_TYPES)
    name = models.CharField(
        max_length=100,
        help_text="Friendly name for identification (e.g., 'Main Store')"
    )
    
    # Security & Tracking
    is_active = models.BooleanField(default=True)
    last_used_at = models.DateTimeField(null=True, blank=True)
    usage_count = models.IntegerField(default=0)
    
    # Optional: IP Whitelist for extra security
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
    """
    Log of all WooCommerce webhook events
    Used for idempotency and debugging
    """
    
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
        help_text="Unique event ID from WooCommerce (for idempotency)"
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
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        status = "✅" if self.processed_successfully else "❌"
        return f"{status} {self.event_type} - Product {self.woo_product_id}"

