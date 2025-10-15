from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
import json

from workflow.models import (
    EventType,
    Trigger,
    Condition,
    Action,
    ActionTemplate,
    Workflow,
    TriggerWorkflowAssociation,
    WorkflowAction,
    WorkflowExecution,
    WorkflowActionExecution,
    TriggerEventLog,
    ActionLog,
    # New node-based models
    WorkflowNode,
    WhenNode,
    ConditionNode,
    ActionNode,
    WaitingNode,
    NodeConnection,
    UserResponse
)


@admin.register(EventType)
class EventTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'category', 'is_active', 'created_at')
    list_filter = ('category', 'is_active', 'created_at')
    search_fields = ('name', 'code', 'description')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        (None, {
            'fields': ('name', 'code', 'category', 'description', 'is_active')
        }),
        ('Schema', {
            'fields': ('available_fields',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )


@admin.register(Trigger)
class TriggerAdmin(admin.ModelAdmin):
    list_display = ('name', 'trigger_type', 'is_active', 'workflow_count', 'created_at')
    list_filter = ('trigger_type', 'is_active', 'schedule_type', 'created_at')
    search_fields = ('name', 'description')
    readonly_fields = ('created_at', 'updated_at', 'workflow_count')
    
    fieldsets = (
        (None, {
            'fields': ('name', 'description', 'trigger_type', 'is_active')
        }),
        ('Configuration', {
            'fields': ('configuration', 'filters'),
            'classes': ('collapse',)
        }),
        ('Scheduling', {
            'fields': ('schedule_type', 'next_execution'),
            'classes': ('collapse',)
        }),
        ('Info', {
            'fields': ('workflow_count', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def workflow_count(self, obj):
        return obj.workflow_associations.count()
    workflow_count.short_description = 'Associated Workflows'


@admin.register(Condition)
class ConditionAdmin(admin.ModelAdmin):
    list_display = ('name', 'operator', 'use_custom_code', 'created_at')
    list_filter = ('operator', 'use_custom_code', 'created_at')
    search_fields = ('name', 'description')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        (None, {
            'fields': ('name', 'description', 'operator')
        }),
        ('Conditions', {
            'fields': ('conditions',),
        }),
        ('Custom Code', {
            'fields': ('use_custom_code', 'custom_code'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )


@admin.register(Action)
class ActionAdmin(admin.ModelAdmin):
    list_display = ('name', 'action_type', 'is_active', 'order', 'delay', 'workflow_count')
    list_filter = ('action_type', 'is_active', 'created_at')
    search_fields = ('name', 'description')
    readonly_fields = ('created_at', 'updated_at', 'workflow_count')
    ordering = ('order', 'name')
    
    fieldsets = (
        (None, {
            'fields': ('name', 'description', 'action_type', 'is_active')
        }),
        ('Execution', {
            'fields': ('order', 'delay'),
        }),
        ('Configuration', {
            'fields': ('configuration',),
        }),
        ('Info', {
            'fields': ('workflow_count', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def workflow_count(self, obj):
        return obj.workflow_associations.count()
    workflow_count.short_description = 'Used in Workflows'


@admin.register(ActionTemplate)
class ActionTemplateAdmin(admin.ModelAdmin):
    list_display = ('name', 'action_type', 'category', 'is_featured', 'use_custom_code')
    list_filter = ('action_type', 'category', 'is_featured', 'use_custom_code')
    search_fields = ('name', 'description')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        (None, {
            'fields': ('name', 'description', 'action_type', 'category', 'is_featured')
        }),
        ('Configuration', {
            'fields': ('configuration',),
        }),
        ('Custom Code', {
            'fields': ('use_custom_code', 'custom_code'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )


class WorkflowActionInline(admin.TabularInline):
    model = WorkflowAction
    extra = 0
    fields = ('action', 'order', 'is_required', 'add_result_to_context', 'condition')
    ordering = ('order',)


class TriggerWorkflowAssociationInline(admin.TabularInline):
    model = TriggerWorkflowAssociation
    extra = 0
    fields = ('trigger', 'priority', 'is_active')
    ordering = ('priority',)


@admin.register(Workflow)
class WorkflowAdmin(admin.ModelAdmin):
    list_display = ('name', 'status', 'created_by', 'actions_count', 'triggers_count', 'executions_count', 'updated_at')
    list_filter = ('status', 'created_by', 'created_at')
    search_fields = ('name', 'description')
    readonly_fields = ('created_at', 'updated_at', 'actions_count', 'triggers_count', 'executions_count')
    inlines = [TriggerWorkflowAssociationInline, WorkflowActionInline]
    
    fieldsets = (
        (None, {
            'fields': ('name', 'description', 'status', 'created_by')
        }),
        ('Execution Settings', {
            'fields': ('max_executions', 'delay_between_executions'),
        }),
        ('Date Range', {
            'fields': ('start_date', 'end_date'),
            'classes': ('collapse',)
        }),
        ('UI Settings', {
            'fields': ('ui_settings', 'edges'),
            'classes': ('collapse',)
        }),
        ('Statistics', {
            'fields': ('actions_count', 'triggers_count', 'executions_count', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def actions_count(self, obj):
        return obj.workflow_actions.count()
    actions_count.short_description = 'Actions'
    
    def triggers_count(self, obj):
        return obj.trigger_associations.count()
    triggers_count.short_description = 'Triggers'
    
    def executions_count(self, obj):
        count = obj.executions.count()
        if count > 0:
            url = reverse('admin:workflow_workflowexecution_changelist')
            return format_html('<a href="{}?workflow__id__exact={}">{}</a>', url, obj.id, count)
        return count
    executions_count.short_description = 'Executions'


class WorkflowActionExecutionInline(admin.TabularInline):
    model = WorkflowActionExecution
    extra = 0
    readonly_fields = ('workflow_action', 'status', 'queued_at', 'started_at', 'completed_at', 'retry_count')
    fields = ('workflow_action', 'status', 'queued_at', 'started_at', 'completed_at', 'retry_count')
    ordering = ('workflow_action__order',)


@admin.register(WorkflowExecution)
class WorkflowExecutionAdmin(admin.ModelAdmin):
    list_display = ('id', 'workflow_link', 'status', 'user', 'conversation', 'duration_display', 'created_at')
    list_filter = ('status', 'workflow', 'created_at')
    search_fields = ('workflow__name', 'user', 'conversation')
    readonly_fields = ('created_at', 'duration_display', 'action_count')
    inlines = [WorkflowActionExecutionInline]
    
    fieldsets = (
        (None, {
            'fields': ('workflow', 'status', 'user', 'conversation')
        }),
        ('Timing', {
            'fields': ('started_at', 'completed_at', 'duration_display', 'created_at'),
        }),
        ('Data', {
            'fields': ('trigger_data', 'context_data', 'result_data'),
            'classes': ('collapse',)
        }),
        ('Errors', {
            'fields': ('error_message', 'error_details'),
            'classes': ('collapse',)
        }),
        ('Statistics', {
            'fields': ('action_count',),
            'classes': ('collapse',)
        })
    )
    
    def workflow_link(self, obj):
        url = reverse('admin:workflow_workflow_change', args=[obj.workflow.id])
        return format_html('<a href="{}">{}</a>', url, obj.workflow.name)
    workflow_link.short_description = 'Workflow'
    
    def duration_display(self, obj):
        if obj.duration:
            return f"{obj.duration.total_seconds():.2f} seconds"
        return "-"
    duration_display.short_description = 'Duration'
    
    def action_count(self, obj):
        return obj.action_executions.count()
    action_count.short_description = 'Action Executions'


@admin.register(WorkflowActionExecution)
class WorkflowActionExecutionAdmin(admin.ModelAdmin):
    list_display = ('id', 'workflow_execution_link', 'action_name', 'status', 'duration_display', 'queued_at')
    list_filter = ('status', 'workflow_action__action__action_type', 'queued_at')
    search_fields = ('workflow_action__action__name', 'workflow_execution__workflow__name')
    readonly_fields = ('queued_at', 'duration_display')
    
    fieldsets = (
        (None, {
            'fields': ('workflow_execution', 'workflow_action', 'status')
        }),
        ('Timing', {
            'fields': ('queued_at', 'started_at', 'completed_at', 'duration_display'),
        }),
        ('Data', {
            'fields': ('input_data', 'result_data'),
            'classes': ('collapse',)
        }),
        ('Errors & Retries', {
            'fields': ('error_message', 'error_details', 'retry_count', 'max_retries', 'next_retry_at'),
            'classes': ('collapse',)
        })
    )
    
    def workflow_execution_link(self, obj):
        url = reverse('admin:workflow_workflowexecution_change', args=[obj.workflow_execution.id])
        return format_html('<a href="{}">Execution #{}</a>', url, obj.workflow_execution.id)
    workflow_execution_link.short_description = 'Workflow Execution'
    
    def action_name(self, obj):
        return obj.workflow_action.action.name
    action_name.short_description = 'Action'
    
    def duration_display(self, obj):
        if obj.duration:
            return f"{obj.duration.total_seconds():.2f} seconds"
        return "-"
    duration_display.short_description = 'Duration'


@admin.register(TriggerEventLog)
class TriggerEventLogAdmin(admin.ModelAdmin):
    list_display = ('event_type', 'user_id', 'conversation_id', 'created_at')
    list_filter = ('event_type', 'created_at')
    search_fields = ('event_type', 'user_id', 'conversation_id')
    readonly_fields = ('created_at',)
    date_hierarchy = 'created_at'
    
    fieldsets = (
        (None, {
            'fields': ('event_type', 'user_id', 'conversation_id', 'created_at')
        }),
        ('Event Data', {
            'fields': ('event_data',),
        })
    )


@admin.register(ActionLog)
class ActionLogAdmin(admin.ModelAdmin):
    list_display = ('action_link', 'success', 'duration', 'executed_at')
    list_filter = ('success', 'action__action_type', 'executed_at')
    search_fields = ('action__name',)
    readonly_fields = ('executed_at',)
    date_hierarchy = 'executed_at'
    
    fieldsets = (
        (None, {
            'fields': ('action', 'success', 'duration', 'executed_at')
        }),
        ('Data', {
            'fields': ('context', 'result'),
            'classes': ('collapse',)
        }),
        ('Error', {
            'fields': ('error_message',),
            'classes': ('collapse',)
        })
    )
    
    def action_link(self, obj):
        url = reverse('admin:workflow_action_change', args=[obj.action.id])
        return format_html('<a href="{}">{}</a>', url, obj.action.name)
    action_link.short_description = 'Action'


# New Node-Based Workflow Admin Classes

@admin.register(WorkflowNode)
class WorkflowNodeAdmin(admin.ModelAdmin):
    list_display = ('title', 'workflow', 'node_type', 'is_active', 'created_at')
    list_filter = ('node_type', 'is_active', 'workflow')
    search_fields = ('title', 'workflow__name')
    readonly_fields = ('id', 'created_at', 'updated_at')
    ordering = ['workflow', 'node_type', 'created_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('workflow', 'node_type', 'title', 'is_active')
        }),
        ('Position', {
            'fields': ('position_x', 'position_y'),
            'classes': ('collapse',)
        }),
        ('Configuration', {
            'fields': ('configuration',),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(WhenNode)
class WhenNodeAdmin(admin.ModelAdmin):
    list_display = ('title', 'workflow', 'when_type', 'is_active', 'created_at')
    list_filter = ('when_type', 'is_active', 'workflow')
    search_fields = ('title', 'workflow__name')
    readonly_fields = ('id', 'node_type', 'created_at', 'updated_at')
    ordering = ['workflow', 'created_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('workflow', 'title', 'when_type', 'is_active')
        }),
        ('Trigger Settings', {
            'fields': ('keywords', 'tags', 'channels'),
        }),
        ('Scheduling (for Scheduled triggers)', {
            'fields': ('schedule_frequency', 'schedule_start_date', 'schedule_time'),
            'classes': ('collapse',)
        }),
        ('Position', {
            'fields': ('position_x', 'position_y'),
            'classes': ('collapse',)
        }),
        ('Configuration', {
            'fields': ('configuration',),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('id', 'node_type', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(ConditionNode)
class ConditionNodeAdmin(admin.ModelAdmin):
    list_display = ('title', 'workflow', 'combination_operator', 'is_active', 'created_at')
    list_filter = ('combination_operator', 'is_active', 'workflow')
    search_fields = ('title', 'workflow__name')
    readonly_fields = ('id', 'node_type', 'created_at', 'updated_at')
    ordering = ['workflow', 'created_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('workflow', 'title', 'combination_operator', 'is_active')
        }),
        ('Conditions', {
            'fields': ('conditions',),
            'description': 'لیست شرط‌ها - هر شرط باید شامل type و فیلدهای مربوطه باشد'
        }),
        ('Position', {
            'fields': ('position_x', 'position_y'),
            'classes': ('collapse',)
        }),
        ('Configuration', {
            'fields': ('configuration',),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('id', 'node_type', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(ActionNode)
class ActionNodeAdmin(admin.ModelAdmin):
    list_display = ('title', 'workflow', 'action_type', 'is_active', 'created_at')
    list_filter = ('action_type', 'is_active', 'workflow')
    search_fields = ('title', 'workflow__name', 'message_content')
    readonly_fields = ('id', 'node_type', 'created_at', 'updated_at')
    ordering = ['workflow', 'created_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('workflow', 'title', 'action_type', 'is_active')
        }),
        ('Message Action', {
            'fields': ('message_content',),
            'classes': ('collapse',)
        }),
        ('Delay Action', {
            'fields': ('delay_amount', 'delay_unit'),
            'classes': ('collapse',)
        }),
        ('Redirect Action', {
            'fields': ('redirect_destination',),
            'classes': ('collapse',)
        }),
        ('Tag Actions', {
            'fields': ('tag_name',),
            'classes': ('collapse',)
        }),
        ('Webhook Action', {
            'fields': ('webhook_url', 'webhook_method', 'webhook_headers', 'webhook_payload'),
            'classes': ('collapse',)
        }),
        ('Custom Code', {
            'fields': ('custom_code',),
            'classes': ('collapse',)
        }),
        ('Position', {
            'fields': ('position_x', 'position_y'),
            'classes': ('collapse',)
        }),
        ('Configuration', {
            'fields': ('configuration',),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('id', 'node_type', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(WaitingNode)
class WaitingNodeAdmin(admin.ModelAdmin):
    list_display = ('title', 'workflow', 'storage_type', 'response_time_limit_enabled', 'is_active', 'created_at')
    list_filter = ('storage_type', 'response_time_limit_enabled', 'is_active', 'workflow')
    search_fields = ('title', 'workflow__name', 'customer_message')
    readonly_fields = ('id', 'node_type', 'created_at', 'updated_at')
    ordering = ['workflow', 'created_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('workflow', 'title', 'is_active')
        }),
        ('Customer Interaction', {
            'fields': ('customer_message', 'error_message', 'choice_options'),
        }),
        ('Response Storage', {
            'fields': ('storage_type',),
            'description': 'نوع پاسخ مورد انتظار: Text, Email, Phone.'
        }),
        ('Response Time Limit', {
            'fields': ('response_time_limit_enabled', 'response_timeout_amount', 'response_timeout_unit'),
            'description': 'تنظیمات محدودیت زمانی پاسخ کاربر'
        }),
        ('Validation Settings', {
            'fields': ('allowed_errors', 'exit_keywords'),
            'classes': ('collapse',),
            'description': 'تنظیمات validation و skip keywords (exit_keywords)'
        }),
        ('Legacy Settings', {
            'fields': ('response_timeout',),
            'classes': ('collapse',),
            'description': 'فیلد قدیمی برای سازگاری با نسخه‌های قبل'
        }),
        ('Position', {
            'fields': ('position_x', 'position_y'),
            'classes': ('collapse',)
        }),
        ('Configuration', {
            'fields': ('configuration',),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('id', 'node_type', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(NodeConnection)
class NodeConnectionAdmin(admin.ModelAdmin):
    list_display = ('source_node_title', 'target_node_title', 'connection_type', 'workflow', 'created_at')
    list_filter = ('connection_type', 'workflow')
    search_fields = ('source_node__title', 'target_node__title', 'workflow__name')
    readonly_fields = ('id', 'created_at')
    ordering = ['workflow', 'created_at']
    
    def source_node_title(self, obj):
        return obj.source_node.title
    source_node_title.short_description = 'Source Node'
    
    def target_node_title(self, obj):
        return obj.target_node.title
    target_node_title.short_description = 'Target Node'
    
    fieldsets = (
        ('Connection', {
            'fields': ('workflow', 'source_node', 'target_node', 'connection_type')
        }),
        ('Condition', {
            'fields': ('condition',),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('id', 'created_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(UserResponse)
class UserResponseAdmin(admin.ModelAdmin):
    list_display = ('waiting_node_title', 'user_id', 'response_value', 'is_valid', 'error_count', 'created_at')
    list_filter = ('is_valid', 'waiting_node__workflow', 'created_at')
    search_fields = ('user_id', 'conversation_id', 'response_value', 'waiting_node__title')
    readonly_fields = ('id', 'created_at', 'processed_at')
    ordering = ['-created_at']
    
    def waiting_node_title(self, obj):
        return obj.waiting_node.title
    waiting_node_title.short_description = 'Waiting Node'
    
    fieldsets = (
        ('Response', {
            'fields': ('waiting_node', 'workflow_execution', 'user_id', 'conversation_id')
        }),
        ('Content', {
            'fields': ('response_value', 'is_valid', 'error_count'),
        }),
        ('Metadata', {
            'fields': ('id', 'created_at', 'processed_at'),
            'classes': ('collapse',)
        }),
    )


# Customize admin site
admin.site.site_header = "Fiko Marketing Workflow Administration"
admin.site.site_title = "Marketing Workflow Admin"
admin.site.index_title = "Welcome to Marketing Workflow Administration"