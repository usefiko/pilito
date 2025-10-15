from django.contrib import admin
from settings.models import Settings, GeneralSettings, TelegramChannel, InstagramChannel, AIPrompts, IntercomTicketType, SupportTicket, SupportMessage, SupportMessageAttachment, BusinessPrompt, UpToPro

# =============================================
# SYSTEM CONFIGURATION
# =============================================

@admin.register(GeneralSettings)
class GeneralSettingsAdmin(admin.ModelAdmin):
    list_display = ("__str__", "gemini_api_key_status", "openai_api_key_status", "has_auto_prompt", "updated_at")
    readonly_fields = ("created_at", "updated_at")
    
    fieldsets = (
        ('AI Configuration', {
            'fields': ('gemini_api_key', 'openai_api_key', 'auto_prompt'),
            'description': 'Configure API keys and global prompts for AI services'
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def gemini_api_key_status(self, obj):
        if obj.gemini_api_key and len(obj.gemini_api_key.strip()) > 0:
            return f"✅ Configured ({len(obj.gemini_api_key)} chars)"
        return "❌ Not configured"
    gemini_api_key_status.short_description = "Gemini API Key Status"
    
    def openai_api_key_status(self, obj):
        if obj.openai_api_key and len(obj.openai_api_key.strip()) > 0:
            return f"✅ Configured ({len(obj.openai_api_key)} chars)"
        return "❌ Not configured"
    openai_api_key_status.short_description = "OpenAI API Key Status"
    
    def has_auto_prompt(self, obj):
        return bool(obj.auto_prompt and obj.auto_prompt.strip())
    has_auto_prompt.boolean = True
    has_auto_prompt.short_description = 'Auto Prompt'
    
    def has_add_permission(self, request):
        # Only allow one instance (singleton pattern)
        return not GeneralSettings.objects.exists()


@admin.register(Settings)
class SettingsAdmin(admin.ModelAdmin):
    list_display = ("IR_yearly", "IR_monthly", "TR_yearly", "TR_monthly", "token1M")


# =============================================  
# CHANNELS MANAGEMENT
# =============================================

@admin.register(TelegramChannel)
class TelegramChannelAdmin(admin.ModelAdmin):
    list_display = ("bot_username", "user", "updated_at", "created_at", "is_connect")
    list_filter = ("is_connect", "created_at")
    search_fields = ("bot_username", "user__email")


@admin.register(InstagramChannel)  
class InstagramChannelAdmin(admin.ModelAdmin):
    list_display = ("username", "user", "updated_at", "created_at", "is_connect")
    list_filter = ("is_connect", "created_at")
    search_fields = ("username", "user__email")


# =============================================
# AI & AUTOMATION
# =============================================

@admin.register(AIPrompts)
class AIPromptsAdmin(admin.ModelAdmin):
    list_display = ("user", "has_manual_prompt", "created_at", "updated_at")
    search_fields = ("user__email", "user__first_name", "user__last_name", "user__username")
    list_filter = ("created_at", "updated_at")
    readonly_fields = ("created_at", "updated_at")
    
    fieldsets = (
        ('User', {
            'fields': ('user',)
        }),
        ('AI Prompts', {
            'fields': ('manual_prompt',),
            'description': 'Configure user-specific manual prompts (auto prompt is managed in General Settings)'
        }),
        ('Advanced Configuration', {
            'fields': ('knowledge_source', 'product_service', 'question_answer'),
            'classes': ('collapse',),
            'description': 'Advanced JSON configuration fields'
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def has_manual_prompt(self, obj):
        return bool(obj.manual_prompt and obj.manual_prompt.strip())
    has_manual_prompt.boolean = True
    has_manual_prompt.short_description = 'Manual Prompt'


@admin.register(BusinessPrompt)
class BusinessPromptAdmin(admin.ModelAdmin):
    list_display = ("name", "prompt_preview", "created_at", "updated_at")
    search_fields = ("name", "prompt", "ai_answer_prompt")
    list_filter = ("created_at", "updated_at")
    readonly_fields = ("created_at", "updated_at")
    list_per_page = 25
    
    fieldsets = (
        ('Business Prompt Information', {
            'fields': ('name', 'prompt', 'ai_answer_prompt'),
            'description': 'Configure business-specific prompts for various use cases'
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def prompt_preview(self, obj):
        """Show a preview of the prompt content"""
        text = (obj.prompt or '')
        if obj.ai_answer_prompt:
            # include a short marker that there are answer guidelines too
            text = f"{text}\n[ai_answer_guidelines included]"
        if text:
            preview = text[:100] + "..." if len(text) > 100 else text
            return preview
        return "No prompt"
    prompt_preview.short_description = 'Prompt Preview'


@admin.register(UpToPro)
class UpToProAdmin(admin.ModelAdmin):
    list_display = ("name", "rate", "signedup", "comment_preview", "created_at", "updated_at")
    search_fields = ("name", "comment")
    list_filter = ("rate", "created_at", "updated_at")
    readonly_fields = ("created_at", "updated_at")
    list_per_page = 25
    
    fieldsets = (
        ('User Information', {
            'fields': ('name', 'profileimage'),
            'description': 'User profile information'
        }),
        ('Rating & Activity', {
            'fields': ('rate', 'signedup', 'comment'),
            'description': 'User rating and activity details'
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def comment_preview(self, obj):
        """Show a preview of the comment"""
        if obj.comment:
            preview = obj.comment[:50] + "..." if len(obj.comment) > 50 else obj.comment
            return preview
        return "No comment"
    comment_preview.short_description = 'Comment Preview'


# =============================================
# CUSTOMER SUPPORT SYSTEM
# =============================================

@admin.register(IntercomTicketType)
class IntercomTicketTypeAdmin(admin.ModelAdmin):
    list_display = ("name", "department", "intercom_ticket_type_id", "is_active", "updated_at")
    list_filter = ("is_active", "department", "created_at")
    search_fields = ("name", "intercom_ticket_type_id")
    readonly_fields = ("created_at", "updated_at")
    list_per_page = 25
    
    fieldsets = (
        ('Ticket Type Configuration', {
            'fields': ('name', 'department', 'intercom_ticket_type_id', 'is_active'),
            'description': '''
                <p><strong>🎫 Configure Intercom Ticket Types</strong></p>
                <p>Map Fiko departments to Intercom ticket types for automatic categorization.</p>
                <ol>
                    <li>Create a Ticket Type in <a href="https://app.intercom.com" target="_blank">Intercom Dashboard</a></li>
                    <li>Go to: <strong>Settings → Messenger → Tickets</strong></li>
                    <li>Copy the Ticket Type ID from the URL (e.g., <code>2918773</code>)</li>
                    <li>Paste it here and map to a department</li>
                </ol>
                <p><em>Note: Each department can only have ONE ticket type mapping.</em></p>
            '''
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request)


class SupportMessageAttachmentInline(admin.TabularInline):
    model = SupportMessageAttachment
    extra = 0
    readonly_fields = ('original_filename', 'file_size', 'file_type', 'uploaded_at')
    fields = ('file', 'original_filename', 'file_size', 'file_type', 'uploaded_at')
    classes = ('collapse',)


class SupportMessageInline(admin.TabularInline):
    model = SupportMessage
    extra = 0
    readonly_fields = ('created_at', 'sender', 'attachment_count')
    fields = ('content', 'is_from_support', 'sender', 'attachment_count', 'created_at')
    classes = ('collapse',)
    ordering = ['-created_at']  # جدیدترین پیام‌ها اول در Admin
    
    def attachment_count(self, obj):
        return obj.attachments.count() if obj.pk else 0
    attachment_count.short_description = "Attachments"


@admin.register(SupportTicket)
class SupportTicketAdmin(admin.ModelAdmin):
    list_display = ("get_ticket_id", "title", "user", "department", "status", "message_count", "created_at", "updated_at")
    list_filter = ("department", "status", "created_at", "updated_at")
    search_fields = ("title", "user__email", "user__first_name", "user__last_name")
    readonly_fields = ("created_at", "updated_at", "message_count")
    inlines = [SupportMessageInline]
    list_per_page = 25
    
    fieldsets = (
        ('Ticket Information', {
            'fields': ('title', 'user', 'department', 'status')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'message_count'),
            'classes': ('collapse',)
        }),
    )
    
    def get_ticket_id(self, obj):
        return f"#{obj.id:03d}"
    get_ticket_id.short_description = "Ticket ID"
    get_ticket_id.admin_order_field = "id"
    
    def message_count(self, obj):
        return obj.messages.count()
    message_count.short_description = "Messages"
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user').prefetch_related('messages')


@admin.register(SupportMessage)
class SupportMessageAdmin(admin.ModelAdmin):
    list_display = ("get_ticket_info", "get_sender_info", "is_from_support", "attachment_count", "created_at")
    list_filter = ("is_from_support", "created_at", "ticket__status")
    search_fields = ("ticket__title", "content", "sender__email", "ticket__id")
    readonly_fields = ("created_at", "ticket", "sender", "attachment_count")
    list_per_page = 50
    inlines = [SupportMessageAttachmentInline]
    
    fieldsets = (
        ('Message Information', {
            'fields': ('ticket', 'content', 'sender')
        }),
        ('Message Details', {
            'fields': ('is_from_support', 'attachment_count', 'created_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_ticket_info(self, obj):
        return f"#{obj.ticket.id:03d} - {obj.ticket.title[:50]}"
    get_ticket_info.short_description = "Ticket"
    get_ticket_info.admin_order_field = "ticket__id"
    
    def get_sender_info(self, obj):
        if obj.is_from_support:
            return "🛠️ Support Team"
        elif obj.sender:
            return f"👤 {obj.sender.first_name} {obj.sender.last_name}".strip() or obj.sender.email
        return "👤 Customer"
    get_sender_info.short_description = "Sender"
    
    def attachment_count(self, obj):
        count = obj.attachments.count()
        return f"📎 {count}" if count > 0 else "📄 0"
    attachment_count.short_description = "Attachments"
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('ticket', 'sender').prefetch_related('attachments')


@admin.register(SupportMessageAttachment)
class SupportMessageAttachmentAdmin(admin.ModelAdmin):
    list_display = ("get_message_info", "original_filename", "file_type", "file_size_kb", "uploaded_at")
    list_filter = ("file_type", "uploaded_at")
    search_fields = ("original_filename", "message__content", "message__ticket__title")
    readonly_fields = ("original_filename", "file_size", "file_type", "uploaded_at")
    list_per_page = 50
    
    fieldsets = (
        ('Attachment Information', {
            'fields': ('message', 'file', 'original_filename')
        }),
        ('File Details', {
            'fields': ('file_type', 'file_size', 'uploaded_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_message_info(self, obj):
        return f"Message #{obj.message.id} in Ticket #{obj.message.ticket.id:03d}"
    get_message_info.short_description = "Message"
    get_message_info.admin_order_field = "message__id"
    
    def file_size_kb(self, obj):
        return f"{obj.file_size / 1024:.1f} KB" if obj.file_size else "0 KB"
    file_size_kb.short_description = "Size"
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('message', 'message__ticket')


# =============================================
# ADMIN SITE CUSTOMIZATION  
# =============================================

# Customize admin site header and title
admin.site.site_header = "Fiko Admin Portal"
admin.site.site_title = "Fiko Admin Portal" 
admin.site.index_title = "Welcome to Fiko Administration"