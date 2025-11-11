from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from django.contrib import messages
from django.http import HttpResponse
from integrations.models import (
    IntegrationToken, WooCommerceEventLog,
    WordPressContent, WordPressContentEventLog
)
from integrations.services import TokenGenerator
import json


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
        'id', 'token_display', 'token_preview', 'usage_count', 'last_used_at', 'created_at'
    ]
    actions = ['generate_new_token_action']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'user', 'name', 'integration_type')
        }),
        ('Token', {
            'fields': ('token_display', 'token_preview'),
            'description': '⚠️ Token کامل فقط در لحظه ساخت نمایش داده می‌شود. برای ساخت token جدید از دکمه "Generate New Token" استفاده کنید.'
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
    
    def token_display(self, obj):
        """Show token with copy button"""
        if obj and obj.token:
            return format_html(
                '<div style="background: #f0f0f0; padding: 10px; border-radius: 4px;">'
                '<code style="font-size: 12px; user-select: all;">{}</code><br>'
                '<small style="color: #666;">⚠️ این token امنیتی است. با احتیاط استفاده کنید.</small>'
                '</div>',
                obj.token
            )
        return '-'
    token_display.short_description = 'Full Token'
    
    def generate_new_token_action(self, request, queryset):
        """Generate new token for selected users"""
        if queryset.count() != 1:
            self.message_user(request, 'لطفاً فقط یک کاربر را انتخاب کنید', messages.ERROR)
            return
        
        token_obj = queryset.first()
        
        # Generate new token
        if token_obj.integration_type == 'woocommerce':
            new_token_string = TokenGenerator.generate_woocommerce_token()
        else:
            new_token_string = TokenGenerator.generate_shopify_token()
        
        token_preview = TokenGenerator.get_token_preview(new_token_string)
        
        # Update token
        token_obj.token = new_token_string
        token_obj.token_preview = token_preview
        token_obj.save()
        
        self.message_user(
            request,
            format_html(
                '✅ Token جدید ساخته شد!<br><br>'
                '<strong>Token:</strong> <code style="background: #f0f0f0; padding: 5px;">{}</code><br><br>'
                '⚠️ این token فقط اینجا نمایش داده می‌شود. لطفاً کپی کنید!',
                new_token_string
            ),
            messages.SUCCESS
        )
    generate_new_token_action.short_description = '🔑 ساخت Token جدید برای انتخاب شده'


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


@admin.register(WordPressContent)
class WordPressContentAdmin(admin.ModelAdmin):
    """Admin for WordPress Pages/Posts"""
    
    list_display = [
        'title', 'user_email', 'content_type', 'is_published',
        'word_count_display', 'last_synced_display'
    ]
    list_filter = ['content_type', 'is_published', 'created_at']
    search_fields = ['title', 'user__email', 'permalink']
    readonly_fields = ['id', 'content_hash', 'last_synced_at', 'created_at']
    
    fieldsets = (
        ('Basic Info', {
            'fields': ('id', 'user', 'title', 'content_type', 'post_type_slug')
        }),
        ('Content', {
            'fields': ('content', 'excerpt', 'permalink')
        }),
        ('Metadata', {
            'fields': ('author', 'categories', 'tags', 'featured_image', 'metadata')
        }),
        ('Status', {
            'fields': ('is_published', 'modified_date')
        }),
        ('Tracking', {
            'fields': ('content_hash', 'last_synced_at', 'created_at')
        }),
    )
    
    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'User'
    
    def word_count_display(self, obj):
        word_count = len(obj.content.split())
        if word_count > 1000:
            return format_html('<span style="color: orange;">{} کلمه</span>', word_count)
        return f"{word_count} کلمه"
    word_count_display.short_description = 'Word Count'
    
    def last_synced_display(self, obj):
        if obj.last_synced_at:
            return obj.last_synced_at.strftime('%Y-%m-%d %H:%M')
        return '-'
    last_synced_display.short_description = 'Last Synced'


@admin.register(WordPressContentEventLog)
class WordPressContentEventLogAdmin(admin.ModelAdmin):
    """Admin for WordPress Content Events"""
    
    list_display = [
        'event_type_display', 'wp_post_id', 'user_email',
        'status_display', 'created_at_display'
    ]
    list_filter = ['event_type', 'processed_successfully', 'created_at']
    search_fields = ['event_id', 'wp_post_id', 'user__email']
    readonly_fields = ['id', 'event_id', 'event_type', 'user', 'token', 'wp_post_id', 'payload', 'created_at']
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'User'
    
    def event_type_display(self, obj):
        icons = {
            'page.created': '📄➕',
            'page.updated': '📄✏️',
            'page.deleted': '📄🗑️',
            'post.created': '📝➕',
            'post.updated': '📝✏️',
            'post.deleted': '📝🗑️',
        }
        icon = icons.get(obj.event_type, '❓')
        return format_html('{} {}', icon, obj.get_event_type_display())
    event_type_display.short_description = 'Event'
    
    def status_display(self, obj):
        if obj.processed_successfully:
            return format_html('<span style="color: green;">✅</span>')
        return format_html('<span style="color: red;" title="{}">❌</span>', obj.error_message or '')
    status_display.short_description = 'Status'
    
    def created_at_display(self, obj):
        return obj.created_at.strftime('%Y-%m-%d %H:%M')
    created_at_display.short_description = 'Created'

