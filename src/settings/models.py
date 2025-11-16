from django.db import models
from django.core.exceptions import ValidationError
from accounts.models import User


class TelegramChannel(models.Model):
    is_connect = models.BooleanField(default=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    bot_token = models.CharField(max_length=200,unique=True)
    bot_username = models.CharField(max_length=100,unique=True)
    profile_picture = models.ImageField(upload_to='telegram_bot_pictures/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "📱 Telegram Channel"
        verbose_name_plural = "📱 Telegram Channels"
    
    def __str__(self):
        return str(self.bot_username)


class InstagramChannel(models.Model):
    is_connect = models.BooleanField(default=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    username = models.CharField(max_length=100, unique=True)
    access_token = models.TextField(null=True, blank=True)  # Store Instagram access token
    token_expires_at = models.DateTimeField(null=True, blank=True)  # Track token expiration
    instagram_user_id = models.CharField(max_length=100, null=True, blank=True)  # Instagram user ID
    page_id = models.CharField(max_length=100, null=True, blank=True)  # Instagram page/business ID for webhooks
    account_type = models.CharField(max_length=50, null=True, blank=True)  # business/personal
    followers_count = models.IntegerField(null=True, blank=True)
    following_count = models.IntegerField(null=True, blank=True)
    media_count = models.IntegerField(null=True, blank=True)
    profile_picture_url = models.CharField(max_length=5000,null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "📷 Instagram Channel"
        verbose_name_plural = "📷 Instagram Channels"
    
    def __str__(self):
        return str(self.username)


class AIPrompts(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='ai_prompts')
    manual_prompt = models.TextField(max_length=90000000, null=True, blank=True)
    knowledge_source = models.JSONField(null=True, blank=True)
    product_service = models.JSONField(null=True, blank=True)
    question_answer = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "🤖 AI Prompt"
        verbose_name_plural = "🤖 AI Prompts"
    
    def __str__(self):
        return f"AI Prompts for {self.user.username}"
    
    @classmethod
    def get_or_create_for_user(cls, user):
        """Get or create AIPrompts for a user with default prompts"""
        prompts, created = cls.objects.get_or_create(
            user=user,
            defaults={
                'manual_prompt': '',  # Empty by default - user must fill this
            }
        )
        return prompts, created
    
    def validate_for_ai_response(self):
        """
        Validate that AIPrompts are ready for AI response generation
        Raises ValueError if manual_prompt is empty
        """
        if not self.manual_prompt or not self.manual_prompt.strip():
            raise ValueError(
                "Manual prompt is required for AI responses. "
                "Please configure your AI prompt in settings before using AI features."
            )
        return True
    
    def get_combined_prompt(self):
        """
        Get combined prompt for AI response generation
        Returns system_prompt + manual_prompt (system first for priority!)
        
        ⚠️ IMPORTANT: System prompt MUST be first because:
        - Contains core behavior rules (language, tone, length)
        - Gets trimmed to tokens, so first prompts have priority
        - Manual prompt is secondary context (business info)
        
        Now uses modular get_combined_system_prompt() for better management!
        """
        self.validate_for_ai_response()  # Ensure manual_prompt is not empty
        
        combined = ""
        
        # ✅ 1. SYSTEM PROMPT FIRST (highest priority - behavior rules)
        # Now using modular approach from GeneralSettings
        try:
            general_settings = GeneralSettings.get_settings()
            system_prompt = general_settings.get_combined_system_prompt()
            if system_prompt and system_prompt.strip():
                combined += system_prompt.strip()
        except Exception as e:
            # If GeneralSettings is not available, continue without system_prompt
            pass
        
        # ✅ 2. MANUAL PROMPT SECOND (business context)
        if self.manual_prompt and self.manual_prompt.strip():
            if combined:
                combined += "\n\n"
            combined += self.manual_prompt.strip()
        
        return combined


class IntercomTicketType(models.Model):
    """
    Intercom Ticket Type Configuration
    Maps Fiko departments to Intercom ticket types
    """
    DEPARTMENT_CHOICES = [
        ('technical_support', 'Technical Support'),
        ('billing_support', 'Billing Support'),
        ('general_inquiry', 'General Inquiry'),
        ('account_support', 'Account Support'),
    ]
    
    name = models.CharField(
        max_length=100,
        help_text="Ticket type name (e.g., 'Technical Support', 'Billing Issue')"
    )
    department = models.CharField(
        max_length=20,
        choices=DEPARTMENT_CHOICES,
        unique=True,
        help_text="Department to map this ticket type to"
    )
    intercom_ticket_type_id = models.CharField(
        max_length=50,
        help_text="Intercom Ticket Type ID from Intercom settings (e.g., '2918773')"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this ticket type is active"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['department']
        verbose_name = "🎫 Intercom Ticket Type"
        verbose_name_plural = "🎫 Intercom Ticket Types"
    
    def __str__(self):
        return f"{self.name} ({self.get_department_display()}) → ID: {self.intercom_ticket_type_id}"


class SupportTicket(models.Model):
    STATUS_CHOICES = [
        ('open', 'Open'),
        ('under_review', 'Under Review'),
        ('support_response', 'Support Response'),
        ('customer_reply', 'Customer Reply'),
        ('closed', 'Closed'),
    ]
    
    DEPARTMENT_CHOICES = IntercomTicketType.DEPARTMENT_CHOICES
    
    title = models.CharField(max_length=200)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    department = models.CharField(max_length=20, choices=DEPARTMENT_CHOICES, default='general_inquiry')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Intercom integration
    intercom_conversation_id = models.CharField(
        max_length=255, 
        blank=True, 
        null=True, 
        unique=True,
        help_text='[DEPRECATED] Old Conversations API ID - kept for backward compatibility'
    )
    
    intercom_ticket_id = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        unique=True,
        help_text='Intercom Ticket ID from Tickets API for two-way sync'
    )
    
    class Meta:
        ordering = ['-updated_at']
        verbose_name = "🎫 Support Ticket"
        verbose_name_plural = "🎫 Support Tickets"
    
    def __str__(self):
        return f"#{self.id:03d} - {self.title}"
    
    @property
    def intercom_id(self):
        """Returns ticket_id if exists, else conversation_id (backward compatibility)"""
        return self.intercom_ticket_id or self.intercom_conversation_id


class SupportMessage(models.Model):
    ticket = models.ForeignKey(SupportTicket, on_delete=models.CASCADE, related_name='messages')
    content = models.TextField()
    is_from_support = models.BooleanField(default=False)
    sender = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']  # جدیدترین پیام‌ها اول
        verbose_name = "💬 Support Message"
        verbose_name_plural = "💬 Support Messages"
    
    def __str__(self):
        sender_type = "Support" if self.is_from_support else "Customer"
        return f"{sender_type} message in ticket #{self.ticket.id:03d}"


class SupportMessageAttachment(models.Model):
    message = models.ForeignKey(SupportMessage, on_delete=models.CASCADE, related_name='attachments')
    file = models.FileField(upload_to='support_attachments/')
    original_filename = models.CharField(max_length=255)
    file_size = models.PositiveIntegerField()  # Size in bytes
    file_type = models.CharField(max_length=100)  # MIME type
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['uploaded_at']
        verbose_name = "📎 Support Message Attachment"
        verbose_name_plural = "📎 Support Message Attachments"
    
    def __str__(self):
        return f"Attachment: {self.original_filename} for message #{self.message.id}"
    
    def save(self, *args, **kwargs):
        if self.file:
            self.file_size = self.file.size
            self.original_filename = self.file.name.split('/')[-1]
            # Get file MIME type
            import mimetypes
            self.file_type = mimetypes.guess_type(self.file.name)[0] or 'application/octet-stream'
        super().save(*args, **kwargs)


# Not complete V

class SingletonModel(models.Model):
    class Meta:
        abstract = True
    def save(self, *args, **kwargs):
        if not self.pk and self.__class__.objects.exists():
            raise ValidationError('There can be only one instance of this model.')
        return super(SingletonModel, self).save(*args, **kwargs)



class GeneralSettings(SingletonModel):
    """
    General AI Settings - Modular Prompt Management (Standard Approach)
    Similar to: OpenAI ChatGPT, Intercom Fin, Zendesk AI
    
    This model uses a modular approach to manage AI prompts, allowing
    each aspect of AI behavior to be configured separately for better
    maintainability and clarity.
    """
    
    # ═══════════════════════════════════════════════════
    # 📌 SECTION 1: Core Identity & Behavior
    # ═══════════════════════════════════════════════════
    ai_role = models.TextField(
        max_length=500,
        default="""You are a sales assistant, NOT a support agent.
Your goal is to understand customer needs and recommend relevant products/services.
Always look for opportunities to suggest products that match their needs.
Be helpful, friendly, and proactive in offering solutions.""",
        verbose_name="🤖 AI Role & Identity",
        help_text=(
            "تعریف کنید هوش مصنوعی چه کسی است (مثلاً 'یک دستیار فروش دوستانه' یا 'یک مشاور فنی')\n"
            "این بخش هویت اصلی AI را مشخص می‌کند."
        )
    )
    
    # ═══════════════════════════════════════════════════
    # 📌 SECTION 2: Language & Communication Style
    # ═══════════════════════════════════════════════════
    language_rules = models.TextField(
        max_length=1000,
        default="""Always reply in Persian (Farsi).
Convert Latin names to Persian equivalents (e.g., Omid → امید).
Use everyday Persian expressions, not formal sentences.""",
        verbose_name="🌐 Language & Localization",
        help_text=(
            "قوانین زبانی و محلی‌سازی را تعریف کنید.\n"
            "مثال: 'همیشه به فارسی پاسخ بده'، 'نام‌های لاتین را به فارسی تبدیل کن'\n"
            "این قسمت تعیین می‌کند AI چه زبانی و با چه سبکی صحبت کند."
        )
    )
    
    tone_and_style = models.TextField(
        max_length=1000,
        default="""Speak casually and emotionally, not like a brochure.
Write like a person chatting on Instagram.
Keep responses under 2 short lines.""",
        verbose_name="💬 Tone & Style (لحن و سبک)",
        help_text=(
            "لحن و سبک مکالمه AI را تعیین کنید.\n"
            "مثال: 'صمیمی و احساسی صحبت کن'، 'مثل یک فرد واقعی در اینستاگرام بنویس'\n"
            "این بخش شخصیت AI را شکل می‌دهد."
        )
    )
    
    # ═══════════════════════════════════════════════════
    # 📌 SECTION 3: Response Guidelines
    # ═══════════════════════════════════════════════════
    response_length = models.CharField(
        max_length=20,
        choices=[
            ('concise', '🔹 Concise (1-2 جمله کوتاه)'),
            ('moderate', '🔸 Moderate (2-4 جمله متوسط)'),
            ('detailed', '🔶 Detailed (4+ جمله تفصیلی)'),
        ],
        default='concise',
        verbose_name="📏 Response Length (طول پاسخ)",
        help_text=(
            "تعیین کنید پاسخ‌های AI چقدر طولانی باشند.\n"
            "کوتاه: برای پیام‌های سریع (مثل اینستاگرام)\n"
            "متوسط: برای توضیحات کلی\n"
            "تفصیلی: برای پاسخ‌های کامل و جامع"
        )
    )
    
    response_guidelines = models.TextField(
        max_length=1000,
        default="""Maximum 600 characters for Instagram compatibility.
Maximum 3-4 sentences per response.
Limit emojis to 1 per message.
Avoid long introductions — go straight to the point.
If topic is complex, give a short summary. User can ask for details.

🎯 PERSONALIZATION WITH BIO:
- If customer has a bio, USE IT in your first response
- Mention their work/interest naturally to show you understand them
- Example: "دیدم استراتژیست برندینگ هستی، فیکو برات عالیه!"
- Convert Latin names to Persian (Omid → امید)

📷🎤 MEDIA MESSAGE RULE:
- If you see '[sent an image]:', the customer SENT an image (not described it)
- If you see '[sent a voice message]:', the customer SENT audio (not typed it)
- The text after is AI analysis of their media
- Respond naturally about what they sent, don't say 'you described'""",
        verbose_name="📝 Response Guidelines (راهنمای پاسخ‌دهی)",
        help_text=(
            "قوانین اضافی برای فرمت و ساختار پاسخ‌ها.\n"
            "شامل: طول پاسخ (600 کاراکتر برای اینستاگرام)، emoji limit، media rules\n"
            "این بخش جزئیات فرمت پاسخ را کنترل می‌کند."
        )
    )
    
    # ═══════════════════════════════════════════════════
    # 📌 SECTION 4: Greeting & Name Usage
    # ═══════════════════════════════════════════════════
    greeting_rules = models.TextField(
        max_length=1000,
        default="""⛔ CRITICAL RULE: Say 'سلام' or 'Hi' ONLY ONCE per conversation!

When you see "SCENARIO: FIRST_MESSAGE":
→ Greet with customer's name ONCE: "سلام [نام]!"
→ Then answer their question naturally

When you see "SCENARIO: WELCOME_BACK":
→ Say "خوش برگشتی!" ONCE (do NOT say سلام)
→ Then answer directly

When you see "SCENARIO: RECENT_CONVERSATION":
→ Do NOT greet at all
→ Answer the question DIRECTLY without any greeting word
→ Example: "بله، می‌تونم کمک کنم..."

⛔ NEVER say "دوباره سلام" or repeat any greeting!""",
        verbose_name="👋 Greeting & Name Usage (احوالپرسی و استفاده از نام)",
        help_text=(
            "قوانین برای احوالپرسی و استفاده از نام مشتری.\n"
            "شامل: first message greeting, welcome back (12+ hours), no repeat greeting\n"
            "جلوگیری از تکرار بیش از حد نام و احوالپرسی‌های مزاحم."
        )
    )
    
    welcome_back_threshold_hours = models.IntegerField(
        default=12,
        verbose_name="⏰ Welcome Back Threshold (ساعت)",
        help_text=(
            "بعد از چند ساعت، AI باید بگوید 'خوش برگشتی'؟\n"
            "پیش‌فرض: 12 ساعت\n"
            "اگر مشتری بعد از این مدت برگردد، AI می‌گوید 'خوش برگشتی!' به جای 'سلام'"
        )
    )
    
    # ═══════════════════════════════════════════════════
    # 📌 SECTION 5: Anti-Hallucination & Accuracy
    # ═══════════════════════════════════════════════════
    anti_hallucination_rules = models.TextField(
        max_length=1000,
        default="""🚨 قوانین ضد توهم‌زایی (Critical):

1) همیشه اول کانتکست و نالج را چک کن:
   - اگر chunk/FAQ/محصول/سایت در کانتکست هست → از همان استفاده کن
   - اگر چیزی در کانتکست نیست، خودت اطلاعات نساز

2) این‌ها را هرگز اختراع نکن:
   - آدرس، شماره تماس، قیمت، موجودی، لینک
   - جزئیات محصول یا خدماتی که تو کانتکست نیست
   - هیچ‌وقت نگو "الان می‌فرستم" اگر الان نداری

3) اگر اطلاعات نداری:
   - صادقانه بگو: "این اطلاعات الان تو دانش من نیست"
   - از متن knowledge_limitation_response استفاده کن

4) لینک و وب‌سایت (خیلی مهم):
   - اگر فقط یک لینک می‌بینی و محتوای صفحه در کانتکست نیست، اصلاً حدس نزن
   - بگو: "متأسفانه من نمی‌تونم محتوای این لینک را ببینم. اگر سوالی راجع بهش داری، لطفاً توضیح بده."
   
   ⚠️ CRITICAL: If user sends ONLY a URL without context:
   - NEVER guess what the link is about
   - Say you can't see the content

5) پست/ریلز اینستاگرام:
   - تو فقط caption/متن را می‌بینی، نه تصویر/ویدیو
   - بر اساس همان متن جواب بده، نه چیزی که داخل تصویر ممکن است باشد""",
        verbose_name="🚨 Anti-Hallucination Rules (قوانین ضد توهم‌زایی)",
        help_text=(
            "⚠️ بسیار مهم: قوانین برای جلوگیری از اطلاعات نادرست.\n"
            "مثال: 'هرگز نگو \"الان می‌فرستم\" اگر اطلاعات نداری'\n"
            "این قسمت از دروغ گفتن AI جلوگیری می‌کند."
        )
    )
    
    knowledge_limitation_response = models.TextField(
        max_length=500,
        default="متأسفانه این اطلاعات رو ندارم. می‌تونم بهت درباره محصولات اصلی‌مون کمک کنم، یا می‌خوای با تیم پشتیبانی صحبت کنی؟",
        verbose_name="📢 Knowledge Limitation Response (پاسخ محدودیت دانش)",
        help_text=(
            "پاسخ پیش‌فرض وقتی AI اطلاعات ندارد.\n"
            "می‌توانید از placeholder {contact_method} استفاده کنید.\n"
            "مثال: 'این اطلاعات رو ندارم، ولی از {contact_method} بپرس'"
        )
    )
    
    # ═══════════════════════════════════════════════════
    # 📌 SECTION 6: Link & URL Handling
    # ═══════════════════════════════════════════════════
    link_handling_rules = models.TextField(
        max_length=500,
        default="""Always include FULL URLs (e.g., https://example.com/pricing)
NEVER use placeholders like [link] or [URL]
If you don't have a link, say so honestly instead of making one up.""",
        verbose_name="🔗 Link & URL Handling (مدیریت لینک‌ها)",
        help_text=(
            "⚠️ بسیار مهم: قوانین برای ارسال لینک و URL.\n"
            "مثال: 'همیشه URL کامل بفرست'، 'هرگز از placeholder مثل [link] استفاده نکن'\n"
            "جلوگیری از لینک‌های ناقص یا جعلی."
        )
    )
    
    # ═══════════════════════════════════════════════════
    # 📌 SECTION 7: Advanced (Optional)
    # ═══════════════════════════════════════════════════
    custom_instructions = models.TextField(
        max_length=2000,
        blank=True,
        null=True,
        verbose_name="⚡ Custom Instructions (دستورات سفارشی - اختیاری)",
        help_text=(
            "دستورات اضافی که در بخش‌های بالا نگنجیده است.\n"
            "این بخش برای نیازهای خاص و منحصر به فرد شماست.\n"
            "اگر نیازی ندارید خالی بگذارید."
        )
    )
    
    # ═══════════════════════════════════════════════════
    # 📌 DEPRECATED FIELD (for backward compatibility)
    # ═══════════════════════════════════════════════════
    auto_prompt = models.TextField(
        max_length=5000,
        default='''You are an AI customer service representative.
Respond to customer inquiries professionally and helpfully.
Always respond in the same language the customer uses.
Keep your responses clear and concise.

🔗 CRITICAL - Links & URLs:
- Always include FULL URLs (e.g., https://fiko.net/pricing)
- NEVER use placeholders like [link] or [URL]
- Write complete clickable links in your responses''',
        blank=True,
        null=True,
        verbose_name="⚠️ [DEPRECATED] Old Auto Prompt",
        help_text=(
            "⚠️ این فیلد منسوخ شده است (Deprecated).\n"
            "از فیلدهای جدید بالا استفاده کنید.\n"
            "این فیلد فقط برای سازگاری با نسخه‌های قدیم نگه داشته شده."
        )
    )
    
    # ═══════════════════════════════════════════════════
    # 📌 API Keys
    # ═══════════════════════════════════════════════════
    gemini_api_key = models.CharField(
        max_length=200,
        null=True,
        blank=True,
        verbose_name="🔑 Gemini API Key",
        help_text="کلید API گوگل جمینای برای سرویس‌های هوش مصنوعی"
    )
    openai_api_key = models.CharField(
        max_length=200,
        null=True,
        blank=True,
        verbose_name="🔑 OpenAI API Key",
        help_text="کلید API اوپن‌ای‌آی برای embedding چندزبانه (text-embedding-3-large)"
    )
    
    # ═══════════════════════════════════════════════════
    # 📌 Metadata
    # ═══════════════════════════════════════════════════
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "⚙️ General AI Settings"
        verbose_name_plural = "⚙️ General AI Settings"

    def __str__(self):
        return "General AI Settings"
    
    def get_combined_system_prompt(self) -> str:
        """
        Combine all modular fields into one system prompt.
        This is called at runtime, NOT stored in DB.
        
        This is the STANDARD approach used by:
        - OpenAI ChatGPT
        - Intercom Fin AI
        - Zendesk AI
        
        Returns:
            str: Combined system prompt from all sections
        """
        sections = []
        
        # 1. Role & Identity
        if self.ai_role and self.ai_role.strip():
            sections.append(self.ai_role.strip())
        
        # 2. Language Rules
        if self.language_rules and self.language_rules.strip():
            sections.append(f"🧠 Language:\n{self.language_rules.strip()}")
        
        # 3. Tone & Style
        if self.tone_and_style and self.tone_and_style.strip():
            sections.append(f"💬 Style:\n{self.tone_and_style.strip()}")
        
        # 4. Response Guidelines
        if self.response_guidelines and self.response_guidelines.strip():
            guidelines = self.response_guidelines.strip()
            # Add length preference
            length_note = {
                'concise': 'Keep responses CONCISE (1-2 sentences max)',
                'moderate': 'Keep responses MODERATE (2-4 sentences)',
                'detailed': 'Provide DETAILED responses (4+ sentences when needed)'
            }.get(self.response_length, '')
            
            if length_note:
                guidelines = f"{length_note}\n{guidelines}"
            
            sections.append(f"📝 Response Guidelines:\n{guidelines}")
        
        # 5. Greeting Rules
        if self.greeting_rules and self.greeting_rules.strip():
            sections.append(f"🎯 Greeting Rules:\n{self.greeting_rules.strip()}")
        
        # 6. Anti-Hallucination (CRITICAL!)
        if self.anti_hallucination_rules and self.anti_hallucination_rules.strip():
            rules = self.anti_hallucination_rules.strip()
            
            # ✅ Hard cap at 800 characters to prevent token budget overflow
            if len(rules) > 800:
                rules = rules[:800] + "\n\n⚠️ (قوانین کامل به دلیل محدودیت توکن trim شدند - اصول کلیدی حفظ شده‌اند)"
            
            sections.append(f"🚨 CRITICAL - Anti-Hallucination:\n{rules}")
            
            if self.knowledge_limitation_response and self.knowledge_limitation_response.strip():
                sections.append(f"When lacking information, respond with:\n{self.knowledge_limitation_response.strip()}")
        
        # 7. Link Handling (CRITICAL!)
        if self.link_handling_rules and self.link_handling_rules.strip():
            sections.append(f"🔗 CRITICAL - Links & URLs:\n{self.link_handling_rules.strip()}")
        
        # 8. Custom Instructions
        if self.custom_instructions and self.custom_instructions.strip():
            sections.append(f"⚡ Additional Instructions:\n{self.custom_instructions.strip()}")
        
        # Combine all sections
        combined = "\n\n".join(sections)
        
        # Fallback to deprecated auto_prompt if nothing configured
        if not combined and self.auto_prompt:
            return self.auto_prompt
        
        return combined or "You are a helpful AI assistant."
    
    @classmethod
    def get_settings(cls):
        """Get or create the general settings instance"""
        settings, created = cls.objects.get_or_create(pk=1)
        return settings


class Settings(SingletonModel):
    IR_yearly = models.IntegerField(default=0)
    IR_monthly = models.IntegerField(default=0)
    TR_yearly = models.IntegerField(default=0)
    TR_monthly = models.IntegerField(default=0)
    EN_yearly = models.IntegerField(default=0)
    EN_monthly = models.IntegerField(default=0)
    token1M = models.IntegerField(default=0)
    token3M = models.IntegerField(default=0)
    token5M = models.IntegerField(default=0)
    token10M = models.IntegerField(default=0)
    email1K = models.IntegerField(default=0)
    email3K = models.IntegerField(default=0)
    email5K = models.IntegerField(default=0)
    email10K = models.IntegerField(default=0)

    class Meta:
        verbose_name = "💰 System Settings"
        verbose_name_plural = "💰 System Settings"

    def __str__(self):
        return str(self.IR_yearly) + " | " + str(self.IR_monthly) + " | " + str(self.EN_yearly) + " | " + str(self.EN_monthly)

class BusinessPrompt(models.Model):
    name = models.CharField(max_length=200, help_text="Name of the business prompt")
    prompt = models.TextField(help_text="The business prompt content")
    ai_answer_prompt = models.TextField(null=True, blank=True, help_text="AI answer prompt for responses")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "💼 Business Prompt"
        verbose_name_plural = "💼 Business Prompts"
        ordering = ['-updated_at']
    
    def __str__(self):
        return self.name


class UpToPro(models.Model):
    rate = models.IntegerField(help_text="Rating value")
    signedup = models.IntegerField(help_text="Number of signups")
    comment = models.TextField(help_text="User comment")
    name = models.CharField(max_length=200, help_text="User name")
    profileimage = models.ImageField(upload_to='uptopro_profiles/', null=True, blank=True, help_text="Profile image")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "⭐ UpToPro"
        verbose_name_plural = "⭐ UpToPros"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} - Rating: {self.rate}"