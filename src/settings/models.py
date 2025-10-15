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
        Returns manual_prompt + auto_prompt (from GeneralSettings) combined
        """
        self.validate_for_ai_response()  # Ensure manual_prompt is not empty
        
        combined = ""
        if self.manual_prompt and self.manual_prompt.strip():
            combined += self.manual_prompt.strip()
        
        # Get auto_prompt from GeneralSettings
        try:
            general_settings = GeneralSettings.get_settings()
            auto_prompt = general_settings.auto_prompt
            if auto_prompt and auto_prompt.strip():
                if combined:
                    combined += "\n\n"
                combined += auto_prompt.strip()
        except Exception as e:
            # If GeneralSettings is not available, continue without auto_prompt
            pass
        
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
    General application settings that can be updated from admin panel
    """
    gemini_api_key = models.CharField(
        max_length=200,
        null=True,
        blank=True,
        help_text="Gemini API key for AI services"
    )
    openai_api_key = models.CharField(
        max_length=200,
        null=True,
        blank=True,
        help_text="OpenAI API key for multilingual embedding (text-embedding-3-large)"
    )
    auto_prompt = models.TextField(
        max_length=5000,
        default='''You are an AI customer service representative.
Respond to customer inquiries professionally and helpfully.
Always respond in the same language the customer uses.
Keep your responses clear and concise.''',
        help_text="Default auto prompt for AI responses - applies to all users"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "⚙️ General Settings"
        verbose_name_plural = "⚙️ General Settings"

    def __str__(self):
        return "General Settings"
    
    @classmethod
    def get_settings(cls):
        """Get or create the general settings instance"""
        settings, created = cls.objects.get_or_create(
            pk=1,
            defaults={
                'auto_prompt': '''You are an AI customer service representative.
Respond to customer inquiries professionally and helpfully.
Always respond in the same language the customer uses.
Keep your responses clear and concise.'''
            }
        )
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