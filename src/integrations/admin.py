from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from integrations.models import IntegrationToken, WooCommerceEventLog


@admin.register(IntegrationToken)
class IntegrationTokenAdmin(admin.ModelAdmin):
    """Admin interface for Integration Tokens"""
    
    list_display = [
        'name', 'user_email', 'integration_type', 'token_preview_display',
        'is_active_display', 'usage_count', 'last_used_display', 'created_at'
    ]
    list_filter = ['integration_type', 'is_active', 'created_at']
    search_fields = ['name', 'user__email', 'user__username', 'token_preview']
    readonly_fields = [
        'id', 'token', 'token_preview', 'usage_count', 'last_used_at', 'created_at'
    ]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'user', 'name', 'integration_type')
        }),
        ('Token', {
            'fields': ('token', 'token_preview'),
            'description': '⚠️ Token فقط در اینجا نمایش داده می‌شود. هرگز آن را در جای دیگری ذخیره نکنید.'
        }),
        ('Security', {
            'fields': ('is_active', 'allowed_ips', 'expires_at')
        }),
        ('Usage Statistics', {
            'fields': ('usage_count', 'last_used_at')
        }),
        ('Timestamps', {
            'fields': ('created_at',)
        }),
    )
    
    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'User'
    user_email.admin_order_field = 'user__email'
    
    def token_preview_display(self, obj):
        return obj.token_preview
    token_preview_display.short_description = 'Token Preview'
    
    def is_active_display(self, obj):
        if obj.is_active:
            if obj.expires_at and obj.expires_at < timezone.now():
                return format_html('<span style="color: orange;">⏰ Expired</span>')
            return format_html('<span style="color: green;">✅ Active</span>')
        return format_html('<span style="color: red;">❌ Inactive</span>')
    is_active_display.short_description = 'Status'
    
    def last_used_display(self, obj):
        if obj.last_used_at:
            delta = timezone.now() - obj.last_used_at
            if delta.days > 30:
                return format_html('<span style="color: orange;">{}</span>', obj.last_used_at.strftime('%Y-%m-%d'))
            return obj.last_used_at.strftime('%Y-%m-%d %H:%M')
        return format_html('<span style="color: gray;">Never</span>')
    last_used_display.short_description = 'Last Used'


@admin.register(WooCommerceEventLog)
class WooCommerceEventLogAdmin(admin.ModelAdmin):
    """Admin interface for WooCommerce Event Logs"""
    
    list_display = [
        'event_type_display', 'woo_product_id', 'user_email',
        'status_display', 'processing_time_display', 'created_at_display'
    ]
    list_filter = ['event_type', 'processed_successfully', 'created_at']
    search_fields = [
        'event_id', 'woo_product_id', 'user__email', 'user__username'
    ]
    readonly_fields = [
        'id', 'event_id', 'event_type', 'user', 'token',
        'woo_product_id', 'payload', 'processed_successfully',
        'error_message', 'processing_time_ms', 'source_ip',
        'user_agent', 'created_at'
    ]
    
    fieldsets = (
        ('Event Information', {
            'fields': ('id', 'event_id', 'event_type', 'woo_product_id')
        }),
        ('References', {
            'fields': ('user', 'token')
        }),
        ('Processing', {
            'fields': ('processed_successfully', 'error_message', 'processing_time_ms')
        }),
        ('Payload', {
            'fields': ('payload',),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('source_ip', 'user_agent'),
            'classes': ('collapse',)
        }),
        ('Timestamp', {
            'fields': ('created_at',)
        }),
    )
    
    def has_add_permission(self, request):
        """Event logs cannot be created manually"""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Event logs cannot be modified"""
        return False
    
    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'User'
    user_email.admin_order_field = 'user__email'
    
    def event_type_display(self, obj):
        icons = {
            'product.created': '➕',
            'product.updated': '✏️',
            'product.deleted': '🗑️',
        }
        icon = icons.get(obj.event_type, '❓')
        return format_html('{} {}', icon, obj.get_event_type_display())
    event_type_display.short_description = 'Event Type'
    event_type_display.admin_order_field = 'event_type'
    
    def status_display(self, obj):
        if obj.processed_successfully:
            return format_html('<span style="color: green;">✅ Success</span>')
        return format_html(
            '<span style="color: red;" title="{}">❌ Failed</span>',
            obj.error_message or 'Unknown error'
        )
    status_display.short_description = 'Status'
    status_display.admin_order_field = 'processed_successfully'
    
    def processing_time_display(self, obj):
        if obj.processing_time_ms:
            if obj.processing_time_ms < 1000:
                return format_html('<span style="color: green;">{} ms</span>', obj.processing_time_ms)
            elif obj.processing_time_ms < 5000:
                return format_html('<span style="color: orange;">{} ms</span>', obj.processing_time_ms)
            else:
                return format_html('<span style="color: red;">{} ms</span>', obj.processing_time_ms)
        return format_html('<span style="color: gray;">-</span>')
    processing_time_display.short_description = 'Processing Time'
    processing_time_display.admin_order_field = 'processing_time_ms'
    
    def created_at_display(self, obj):
        return obj.created_at.strftime('%Y-%m-%d %H:%M:%S')
    created_at_display.short_description = 'Created At'
    created_at_display.admin_order_field = 'created_at'

