from django.contrib import admin
from django.utils.html import format_html
from settings.models import Settings, GeneralSettings, TelegramChannel, InstagramChannel, AIPrompts, IntercomTicketType, SupportTicket, SupportMessage, SupportMessageAttachment, BusinessPrompt, UpToPro, AIBehaviorSettings, AffiliationConfig

# =============================================
# SYSTEM CONFIGURATION
# =============================================

@admin.register(GeneralSettings)
class GeneralSettingsAdmin(admin.ModelAdmin):
    list_display = ("__str__", "gemini_api_key_status", "openai_api_key_status", "prompt_sections_configured", "updated_at")
    readonly_fields = ("created_at", "updated_at", "preview_combined_prompt")
    
    class Media:
        css = {
            'all': ('admin/css/generalsettings_admin.css',)
        }
    
    fieldsets = (
        ('📌 SECTION 1: Core Identity & Behavior', {
            'fields': ('ai_role',),
            'description': '🤖 هویت AI: تعریف کنید هوش مصنوعی چه کسی است. مثلاً: "یک دستیار فروش دوستانه" یا "یک مشاور فنی" - این بخش شخصیت اصلی AI را شکل می‌دهد.'
        }),
        ('📌 SECTION 2: Language & Communication Style', {
            'fields': ('language_rules', 'tone_and_style'),
            'description': '🌐 زبان و لحن: Language Rules = تعیین کنید AI به چه زبانی صحبت کند (مثلاً فارسی، انگلیسی) | Tone & Style = سبک مکالمه را مشخص کنید (صمیمی، رسمی، حرفه‌ای، شاد) - این بخش تعیین می‌کند AI چطور با مشتریان صحبت کند.'
        }),
        ('📌 SECTION 3: Response Guidelines', {
            'fields': ('response_length', 'response_guidelines'),
            'description': '📝 راهنمای پاسخ‌دهی: Response Length = طول پاسخ‌ها (کوتاه برای اینستاگرام، بلند برای ایمیل) | Guidelines = قوانین اضافی مثل "حداکثر 1 ایموجی" یا "بدون مقدمه طولانی" - این بخش فرمت و ساختار پاسخ‌ها را کنترل می‌کند.'
        }),
        ('📌 SECTION 4: Greeting & Name Usage', {
            'fields': ('greeting_rules', 'welcome_back_threshold_hours'),
            'description': '👋 احوالپرسی: Greeting Rules = قوانین برای احوالپرسی و استفاده از نام مشتری | Welcome Back Threshold = بعد از چند ساعت AI بگوید "خوش برگشتی"؟ - جلوگیری از تکرار مزاحم "سلام" و نام مشتری.'
        }),
        ('📌 SECTION 5: Anti-Hallucination & Accuracy ⚠️ بسیار مهم', {
            'fields': ('anti_hallucination_rules', 'knowledge_limitation_response'),
            'description': '🚨 قوانین ضد توهم‌زایی (بسیار مهم!): Anti-Hallucination Rules = جلوگیری از دروغ گفتن AI (مثلاً "الان می‌فرستم" وقتی اطلاعات ندارد) | Knowledge Limitation = پاسخ پیش‌فرض وقتی AI اطلاعات ندارد - ⚠️ این بخش از اطلاعات نادرست جلوگیری می‌کند.',
            'classes': ('wide',)
        }),
        ('📌 SECTION 6: Link & URL Handling ⚠️ بسیار مهم', {
            'fields': ('link_handling_rules',),
            'description': '🔗 مدیریت لینک‌ها (بسیار مهم!): همیشه URL کامل ارسال شود (مثلاً https://example.com/pricing) | هرگز از placeholder مثل [link] یا [URL] استفاده نشود | اگر لینک ندارد، صادقانه بگوید به جای جعل کردن - ⚠️ جلوگیری از لینک‌های ناقص یا جعلی.',
            'classes': ('wide',)
        }),
        ('📌 SECTION 7: Advanced (Optional)', {
            'fields': ('custom_instructions',),
            'description': '⚡ دستورات سفارشی (اختیاری): برای نیازهای خاص و منحصر به فرد که در بخش‌های بالا نگنجیده است - اگر نیازی ندارید، خالی بگذارید.',
            'classes': ('collapse',)
        }),
        ('⚠️ [DEPRECATED] Old Auto Prompt (منسوخ شده)', {
            'fields': ('auto_prompt',),
            'description': '⚠️ توجه: این فیلد منسوخ شده است (Deprecated) - لطفاً از فیلدهای جدید بالا استفاده کنید. این فیلد فقط برای سازگاری با نسخه‌های قدیم نگه داشته شده.',
            'classes': ('collapse',)
        }),
        ('🔑 API Configuration', {
            'fields': ('gemini_api_key', 'openai_api_key'),
            'description': 'کلیدهای API برای سرویس‌های هوش مصنوعی',
            'classes': ('collapse',)
        }),
        ('📊 Preview & Timestamps', {
            'fields': ('preview_combined_prompt', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def gemini_api_key_status(self, obj):
        if obj.gemini_api_key and len(obj.gemini_api_key.strip()) > 0:
            return f"✅ Configured ({len(obj.gemini_api_key)} chars)"
        return "❌ Not configured"
    gemini_api_key_status.short_description = "Gemini API"
    
    def openai_api_key_status(self, obj):
        if obj.openai_api_key and len(obj.openai_api_key.strip()) > 0:
            return f"✅ Configured ({len(obj.openai_api_key)} chars)"
        return "❌ Not configured"
    openai_api_key_status.short_description = "OpenAI API"
    
    def prompt_sections_configured(self, obj):
        """Show how many prompt sections are configured"""
        sections = []
        if obj.ai_role and obj.ai_role.strip():
            sections.append("Role")
        if obj.language_rules and obj.language_rules.strip():
            sections.append("Language")
        if obj.tone_and_style and obj.tone_and_style.strip():
            sections.append("Tone")
        if obj.response_guidelines and obj.response_guidelines.strip():
            sections.append("Guidelines")
        if obj.greeting_rules and obj.greeting_rules.strip():
            sections.append("Greeting")
        if obj.anti_hallucination_rules and obj.anti_hallucination_rules.strip():
            sections.append("Anti-Hallucination")
        if obj.link_handling_rules and obj.link_handling_rules.strip():
            sections.append("Links")
        
        return f"✅ {len(sections)}/7 sections" if sections else "❌ Not configured"
    prompt_sections_configured.short_description = 'Prompt Sections'
    
    def preview_combined_prompt(self, obj):
        """Preview the combined system prompt"""
        try:
            combined = obj.get_combined_system_prompt()
            if combined:
                preview = combined[:500] + "..." if len(combined) > 500 else combined
                return format_html(
                    '<pre style="background: #f5f5f5; padding: 10px; border-radius: 5px; white-space: pre-wrap;">{}</pre>',
                    preview
                )
            return "No prompt configured"
        except Exception as e:
            return f"Error: {e}"
    preview_combined_prompt.short_description = "🔍 Preview Combined Prompt"
    
    def has_add_permission(self, request):
        # Only allow one instance (singleton pattern)
        return not GeneralSettings.objects.exists()
    
    def has_delete_permission(self, request, obj=None):
        # Cannot delete singleton
        return False


@admin.register(Settings)
class SettingsAdmin(admin.ModelAdmin):
    list_display = ("IR_yearly", "IR_monthly", "TR_yearly", "TR_monthly", "token1M")


@admin.register(AffiliationConfig)
class AffiliationConfigAdmin(admin.ModelAdmin):
    """
    Admin interface for Affiliation/Referral Configuration
    
    Singleton model - only one instance can exist.
    Configure the commission percentage and validity period for affiliate rewards.
    """
    list_display = ("__str__", "percentage", "validity_display", "is_active", "total_referrals", "total_commissions", "updated_at")
    readonly_fields = ("created_at", "updated_at", "total_referrals", "total_commissions", "example_calculation", "validity_info")
    
    fieldsets = (
        ('🤝 Affiliate System Configuration', {
            'fields': ('percentage', 'commission_validity_days', 'is_active'),
            'description': '''
                <p><strong>💰 Configure Affiliate Commission System</strong></p>
                <p>When a referred user makes a payment, their referrer automatically receives a commission.</p>
                <ul>
                    <li><strong>Percentage:</strong> Commission percentage (e.g., 10 = 10%)</li>
                    <li><strong>Validity Days:</strong> Number of days after registration during which payments qualify for commission (0 = unlimited)</li>
                    <li><strong>Active:</strong> Enable or disable the entire affiliate system</li>
                </ul>
                <p><em>Note: Users must enable their affiliate system in their profile to receive commissions.</em></p>
            '''
        }),
        ('📊 Statistics', {
            'fields': ('total_referrals', 'total_commissions', 'example_calculation', 'validity_info'),
            'classes': ('collapse',)
        }),
        ('📅 Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def total_referrals(self, obj):
        """Show total number of users who have referrers"""
        from accounts.models import User
        count = User.objects.filter(referred_by__isnull=False).count()
        return f"{count} users"
    total_referrals.short_description = "Total Referrals"
    
    def total_commissions(self, obj):
        """Show total commissions paid out"""
        from billing.models import WalletTransaction
        from django.db.models import Sum
        total = WalletTransaction.objects.filter(
            transaction_type='commission'
        ).aggregate(total=Sum('amount'))['total'] or 0
        return f"{total:,.2f}"
    total_commissions.short_description = "Total Commissions Paid"
    
    def example_calculation(self, obj):
        """Show example commission calculation"""
        examples = [
            (100, obj.calculate_commission(100)),
            (500, obj.calculate_commission(500)),
            (1000, obj.calculate_commission(1000)),
        ]
        html = "<table style='margin-top:10px; border-collapse: collapse;'>"
        html += "<tr style='background: #f5f5f5;'><th style='padding: 8px; border: 1px solid #ddd;'>Payment Amount</th><th style='padding: 8px; border: 1px solid #ddd;'>Commission ({0}%)</th></tr>".format(obj.percentage)
        for amount, commission in examples:
            html += f"<tr><td style='padding: 8px; border: 1px solid #ddd;'>{amount:,}</td><td style='padding: 8px; border: 1px solid #ddd; color: green;'>{commission:,.2f}</td></tr>"
        html += "</table>"
        return format_html(html)
    example_calculation.short_description = "Example Calculations"
    
    def validity_display(self, obj):
        """Show validity period in list display"""
        return obj.get_validity_display()
    validity_display.short_description = "Validity Period"
    
    def validity_info(self, obj):
        """Show detailed validity information"""
        if obj.commission_validity_days == 0:
            return format_html(
                '<div style="background: #e8f5e9; padding: 10px; border-radius: 5px;">'
                '<strong>⏰ Validity:</strong> Unlimited - commissions apply to all payments forever'
                '</div>'
            )
        else:
            return format_html(
                '<div style="background: #fff3e0; padding: 10px; border-radius: 5px;">'
                '<p><strong>⏰ Validity Period:</strong> {} days after registration</p>'
                '<p><strong>Example:</strong></p>'
                '<ul>'
                '<li>User registers on Jan 1</li>'
                '<li>Commissions apply until: Jan {} (inclusive)</li>'
                '<li>Payments after {} days do NOT generate commissions</li>'
                '</ul>'
                '</div>',
                obj.commission_validity_days,
                obj.commission_validity_days,
                obj.commission_validity_days
            )
    validity_info.short_description = "Validity Details"
    
    def has_add_permission(self, request):
        # Only allow one instance (singleton pattern)
        return not AffiliationConfig.objects.exists()
    
    def has_delete_permission(self, request, obj=None):
        # Cannot delete singleton
        return False


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

# =============================================
# AI BEHAVIOR SETTINGS
# =============================================

@admin.register(AIBehaviorSettings)
class AIBehaviorSettingsAdmin(admin.ModelAdmin):
    """
    Admin interface for AI Behavior Settings
    
    Allows admins to view and manage per-user AI behavior configurations.
    Each business owner can customize how their AI assistant behaves.
    """
    list_display = [
        'user',
        'tone',
        'emoji_usage',
        'response_length',
        'use_customer_name',
        'use_bio_context',
        'persuasive_selling_enabled',
        'updated_at',
    ]
    
    list_filter = [
        'tone',
        'emoji_usage',
        'response_length',
        'persuasive_selling_enabled',
        'use_customer_name',
        'use_bio_context',
        'created_at',
        'updated_at',
    ]
    
    search_fields = [
        'user__username',
        'user__email',
        'user__first_name',
        'user__last_name',
        'custom_instructions',
    ]
    
    readonly_fields = ['created_at', 'updated_at', 'preview_prompt_flags']
    
    fieldsets = (
        ('👤 کاربر', {
            'fields': ('user',),
            'description': 'کاربر / صاحب کسب‌وکار که این تنظیمات به او تعلق دارد'
        }),
        
        ('🎭 شخصیت AI (Persona)', {
            'fields': (
                'tone',
                'emoji_usage',
                'response_length',
            ),
            'description': (
                '🎨 لحن صحبت: رسمی، دوستانه، پرانرژی یا همدلانه<br>'
                '😊 استفاده از ایموجی: هیچ، متعادل یا زیاد<br>'
                '📏 طول پاسخ: کوتاه (1-2 جمله)، متعادل (3-4 جمله)، یا تفصیلی (5-7 جمله)'
            )
        }),
        
        ('⚙️ کنترل‌های رفتاری (Behavioral Controls)', {
            'fields': (
                'use_customer_name',
                'use_bio_context',
            ),
            'description': (
                '✅ استفاده از نام مشتری: AI نام مشتری را در سلام صدا می‌زند<br>'
                '✅ استفاده از بیو: AI از اطلاعات بیو مشتری برای شخصی‌سازی استفاده می‌کند'
            )
        }),
        
        ('💰 فروش فعال (Persuasive Selling)', {
            'fields': (
                'persuasive_selling_enabled',
                'persuasive_cta_text',
            ),
            'description': (
                '✅ فعال‌سازی: AI به صورت فعال محصولات را پیشنهاد می‌دهد<br>'
                '📣 متن CTA: متنی که AI به صورت طبیعی در پیام‌های فروش می‌گنجاند (حداکثر 300 کاراکتر)'
            )
        }),
        
        ('📝 قوانین پاسخ (Response Rules)', {
            'fields': (
                'unknown_fallback_text',
                'custom_instructions',
            ),
            'description': (
                '❓ پاسخ عدم اطلاع: متنی که وقتی AI جواب ندارد برمی‌گرداند (حداکثر 500 کاراکتر)<br>'
                '⚡ دستورات اضافی: قوانین اضافی به زبان انگلیسی (اختیاری، حداکثر 1000 کاراکتر)'
            ),
            'classes': ('wide',)
        }),
        
        ('🔍 پیش‌نمایش (Preview)', {
            'fields': ('preview_prompt_flags',),
            'description': 'پیش‌نمایش flag های که به AI ارسال می‌شوند',
            'classes': ('collapse',)
        }),
        
        ('📅 اطلاعات تکمیلی', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def preview_prompt_flags(self, obj):
        """
        Show preview of how the flags will be sent to AI
        """
        if obj.pk:
            flags = obj.get_prompt_additions()
            return format_html(
                '<pre style="background:#f5f5f5;padding:10px;border-radius:4px;white-space:pre-wrap;">{}</pre>',
                flags
            )
        return "ذخیره کنید تا پیش‌نمایش نمایش داده شود"
    
    preview_prompt_flags.short_description = "پیش‌نمایش Flag های AI"
    
    def get_queryset(self, request):
        """Optimize queryset with select_related"""
        qs = super().get_queryset(request)
        return qs.select_related('user')


# Customize admin site header and title
admin.site.site_header = "Fiko Admin Portal"
admin.site.site_title = "Fiko Admin Portal" 
admin.site.index_title = "Welcome to Fiko Administration"