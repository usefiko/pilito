from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Sum, Count, Q
from import_export import resources
from import_export.admin import ExportMixin
from .models import (
    AIGlobalConfig, AIUsageTracking, AIUsageLog, TenantKnowledge,
    SessionMemory, IntentKeyword, IntentRouting
)

@admin.register(AIGlobalConfig)
class AIGlobalConfigAdmin(admin.ModelAdmin):
    list_display = ('model_name', 'auto_response_enabled', 'temperature', 'max_tokens', 'created_at')
    list_filter = ('auto_response_enabled', 'business_hours_only')
    readonly_fields = ('created_at', 'updated_at')
    
    def has_add_permission(self, request):
        # Only allow one global config
        return not AIGlobalConfig.objects.exists()
    
    def has_delete_permission(self, request, obj=None):
        # Don't allow deletion of global config
        return False

# Resource for exporting AI Usage Logs
class AIUsageLogResource(resources.ModelResource):
    """Resource class for exporting AI Usage Log data"""
    class Meta:
        model = AIUsageLog
        fields = (
            'id', 'user__username', 'user__email', 'section', 
            'prompt_tokens', 'completion_tokens', 'total_tokens',
            'response_time_ms', 'success', 'model_name', 
            'error_message', 'created_at'
        )
        export_order = (
            'created_at', 'user__username', 'user__email', 'section',
            'total_tokens', 'prompt_tokens', 'completion_tokens',
            'response_time_ms', 'success', 'model_name', 'error_message', 'id'
        )


@admin.register(AIUsageLog)
class AIUsageLogAdmin(ExportMixin, admin.ModelAdmin):
    """
    Admin interface for AI Usage Logs with comprehensive filtering,
    search, and export capabilities
    """
    resource_class = AIUsageLogResource
    
    list_display = (
        'created_at_display', 'user_display', 'section_display', 
        'tokens_display', 'response_time_display', 'success_badge',
        'model_name'
    )
    
    list_filter = (
        'success',
        'section',
        'model_name',
        ('created_at', admin.DateFieldListFilter),
        'user',
    )
    
    search_fields = (
        'user__username',
        'user__email',
        'section',
        'model_name',
        'error_message',
        'id'
    )
    
    readonly_fields = (
        'id', 'user', 'section', 'prompt_tokens', 'completion_tokens',
        'total_tokens', 'response_time_ms', 'success', 'model_name',
        'error_message', 'metadata', 'created_at'
    )
    
    date_hierarchy = 'created_at'
    
    ordering = ('-created_at',)
    
    list_per_page = 50
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'user', 'section', 'model_name', 'created_at')
        }),
        ('Token Usage', {
            'fields': ('prompt_tokens', 'completion_tokens', 'total_tokens')
        }),
        ('Performance', {
            'fields': ('response_time_ms', 'success', 'error_message')
        }),
        ('Additional Context', {
            'fields': ('metadata',),
            'classes': ('collapse',)
        }),
    )
    
    # Custom display methods
    def created_at_display(self, obj):
        """Display created_at in a readable format"""
        return obj.created_at.strftime('%Y-%m-%d %H:%M:%S')
    created_at_display.short_description = 'Timestamp'
    created_at_display.admin_order_field = 'created_at'
    
    def user_display(self, obj):
        """Display user with link"""
        return format_html(
            '<a href="/admin/accounts/user/{}/change/">{}</a>',
            obj.user.id,
            obj.user.username
        )
    user_display.short_description = 'User'
    user_display.admin_order_field = 'user'
    
    def section_display(self, obj):
        """Display section with color coding"""
        colors = {
            'chat': '#4CAF50',
            'prompt_generation': '#2196F3',
            'marketing_workflow': '#FF9800',
            'knowledge_qa': '#9C27B0',
            'product_recommendation': '#00BCD4',
            'rag_pipeline': '#3F51B5',
            'web_knowledge': '#8BC34A',
            'session_memory': '#FFC107',
            'intent_detection': '#E91E63',
            'embedding_generation': '#607D8B',
            'other': '#9E9E9E'
        }
        color = colors.get(obj.section, '#000000')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 3px; font-weight: bold;">{}</span>',
            color,
            obj.get_section_display()
        )
    section_display.short_description = 'Section/Feature'
    section_display.admin_order_field = 'section'
    
    def tokens_display(self, obj):
        """Display token usage"""
        return format_html(
            '<strong>{}</strong><br/>'
            '<small style="color: #666;">↑{} / ↓{}</small>',
            obj.total_tokens,
            obj.prompt_tokens,
            obj.completion_tokens
        )
    tokens_display.short_description = 'Tokens (Total/In/Out)'
    tokens_display.admin_order_field = 'total_tokens'
    
    def response_time_display(self, obj):
        """Display response time with color coding"""
        if obj.response_time_ms < 1000:
            color = '#4CAF50'  # Green
        elif obj.response_time_ms < 3000:
            color = '#FF9800'  # Orange
        else:
            color = '#F44336'  # Red
        
        return format_html(
            '<span style="color: {}; font-weight: bold;">{} ms</span>',
            color,
            obj.response_time_ms
        )
    response_time_display.short_description = 'Response Time'
    response_time_display.admin_order_field = 'response_time_ms'
    
    def success_badge(self, obj):
        """Display success status with badge"""
        if obj.success:
            return format_html(
                '<span style="background-color: #4CAF50; color: white; padding: 3px 8px; '
                'border-radius: 3px; font-weight: bold;">✓ Success</span>'
            )
        else:
            return format_html(
                '<span style="background-color: #F44336; color: white; padding: 3px 8px; '
                'border-radius: 3px; font-weight: bold;">✗ Failed</span>'
            )
    success_badge.short_description = 'Status'
    success_badge.admin_order_field = 'success'
    
    def has_add_permission(self, request):
        """Disable manual adding (logs should be created via API)"""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """Allow deletion only for superusers"""
        return request.user.is_superuser
    
    def changelist_view(self, request, extra_context=None):
        """Add summary statistics to the changelist view"""
        extra_context = extra_context or {}
        
        # Get queryset with current filters
        ChangeList = self.get_changelist(request)
        
        # Django 5.1+ requires additional parameters
        cl = ChangeList(
            request, 
            self.model, 
            self.list_display,
            self.list_display_links, 
            self.list_filter, 
            self.date_hierarchy,
            self.search_fields, 
            self.list_select_related, 
            self.list_per_page,
            self.list_max_show_all, 
            self.list_editable, 
            self,
            self.sortable_by if hasattr(self, 'sortable_by') else None,  # Django 5.1+
            self.search_help_text if hasattr(self, 'search_help_text') else None  # Django 5.1+
        )
        
        # Calculate statistics
        queryset = cl.get_queryset(request)
        stats = queryset.aggregate(
            total_requests=Count('id'),
            total_tokens=Sum('total_tokens'),
            successful_requests=Count('id', filter=Q(success=True)),
            failed_requests=Count('id', filter=Q(success=False))
        )
        
        extra_context['usage_stats'] = stats
        
        return super().changelist_view(request, extra_context=extra_context)


@admin.register(AIUsageTracking)
class AIUsageTrackingAdmin(admin.ModelAdmin):
    """Daily aggregated AI usage statistics"""
    list_display = ('user', 'date', 'total_requests', 'total_tokens', 'successful_requests', 'failed_requests', 'average_response_time_ms')
    list_filter = ('date', 'user')
    search_fields = ('user__username', 'user__email')
    readonly_fields = ('created_at', 'updated_at')
    date_hierarchy = 'date'
    
    def get_readonly_fields(self, request, obj=None):
        # Make most fields readonly as they're automatically calculated
        if obj:  # editing an existing object
            return self.readonly_fields + ('user', 'date', 'total_requests', 'total_prompt_tokens', 
                                        'total_completion_tokens', 'total_tokens', 'total_response_time_ms',
                                        'average_response_time_ms', 'successful_requests', 'failed_requests')
        return self.readonly_fields


@admin.register(TenantKnowledge)
class TenantKnowledgeAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'chunk_type', 'section_title', 'language', 'word_count', 'created_at')
    list_filter = ('chunk_type', 'language', 'user', 'created_at')
    search_fields = ('section_title', 'full_text', 'tldr', 'user__username')
    readonly_fields = ('id', 'created_at', 'updated_at')
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Basic Info', {
            'fields': ('id', 'user', 'chunk_type', 'source_id')
        }),
        ('Content', {
            'fields': ('section_title', 'full_text', 'tldr', 'language', 'word_count')
        }),
        ('Hierarchical Structure', {
            'fields': ('document_id',),
            'classes': ('collapse',)
        }),
        ('Embeddings', {
            'fields': ('tldr_embedding', 'full_embedding'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('metadata', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(SessionMemory)
class SessionMemoryAdmin(admin.ModelAdmin):
    list_display = ('conversation', 'user', 'message_count', 'last_updated')
    list_filter = ('user', 'last_updated')
    search_fields = ('conversation__id', 'user__username', 'cumulative_summary')
    readonly_fields = ('conversation', 'created_at', 'last_updated')
    date_hierarchy = 'last_updated'
    
    fieldsets = (
        ('Conversation', {
            'fields': ('conversation', 'user')
        }),
        ('Summary', {
            'fields': ('cumulative_summary', 'message_count')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'last_updated'),
            'classes': ('collapse',)
        }),
    )


@admin.register(IntentKeyword)
class IntentKeywordAdmin(admin.ModelAdmin):
    list_display = ('keyword', 'intent', 'language', 'weight', 'user', 'is_active')
    list_filter = ('intent', 'language', 'is_active', 'user')
    search_fields = ('keyword', 'user__username')
    list_editable = ('weight', 'is_active')
    
    fieldsets = (
        ('Keyword Info', {
            'fields': ('intent', 'language', 'keyword', 'weight')
        }),
        ('Scope', {
            'fields': ('user', 'is_active')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ('created_at', 'updated_at')
    
    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        # Invalidate cache when keyword changes
        try:
            from django.core.cache import cache
            cache_key = f"intent_keywords:{obj.user.id if obj.user else 'global'}"
            cache.delete(cache_key)
        except:
            pass


@admin.register(IntentRouting)
class IntentRoutingAdmin(admin.ModelAdmin):
    list_display = ('intent', 'primary_source', 'primary_token_budget', 'secondary_token_budget', 'is_active')
    list_filter = ('primary_source', 'is_active')
    list_editable = ('is_active',)
    
    fieldsets = (
        ('Intent', {
            'fields': ('intent',)
        }),
        ('Routing', {
            'fields': ('primary_source', 'secondary_sources')
        }),
        ('Token Budgets', {
            'fields': ('primary_token_budget', 'secondary_token_budget')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ('created_at', 'updated_at')
    
    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        # Invalidate cache when routing changes
        try:
            from django.core.cache import cache
            cache.delete('intent_routing_config')
        except:
            pass