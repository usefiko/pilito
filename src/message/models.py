from django.db import models
import shortuuid
from accounts.models import User


def generate_short_uuid():
    return shortuuid.uuid()[:6]

class Tag(models.Model):
    name = models.CharField(max_length=100)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tags', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    
    def __str__(self):
        return self.name

class Customer(models.Model):
    SOURCE_CHOICES = [
        ('unknown', 'unknown'),
        ('telegram', 'telegram'),
        ('instagram', 'instagram'),
    ]
    first_name = models.CharField(max_length=100,null=True,blank=True)
    last_name = models.CharField(max_length=100, null=True, blank=True)
    username = models.CharField(max_length=100, null=True, blank=True)
    phone_number = models.CharField(max_length=100, null=True, blank=True)
    description = models.TextField(max_length=1000,null=True,blank=True)
    profile_picture = models.ImageField(default="customer_img/default.png", upload_to="customer_img", blank=True, null=True)
    tag = models.ManyToManyField(Tag, related_name='customers', blank=True)
    email = models.EmailField(max_length=250, null=True, blank=True)
    source = models.CharField(max_length=90,choices=SOURCE_CHOICES,default='unknown')
    source_id = models.CharField(max_length=90,unique=True,null=True,blank=True)
    
    # Persona & Bio (for personalization - Instagram only)
    bio = models.TextField(
        max_length=500,
        null=True,
        blank=True,
        help_text="User's biography from Instagram (only for Instagram source, Business accounts)"
    )
    persona_data = models.JSONField(
        null=True,
        blank=True,
        help_text="Auto-extracted persona info from bio: interests, tone_preference, profession"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        name = f"{self.first_name or ''} {self.last_name or ''}".strip()
        username_part = f"@{self.username}" if self.username else ""
        if name and username_part:
            return f"{name} ({username_part}) | {self.source}"
        elif name:
            return f"{name} | {self.source}"
        elif username_part:
            return f"{username_part} | {self.source}"
        else:
            return f"Customer {self.id} | {self.source}"

class Conversation(models.Model):
    STATUS_CHOICES = [
        ('active', 'active'),
        ('support_active', 'support_active'),
        ('marketing_active', 'marketing_active'),
        ('closed', 'closed'),
    ]
    SOURCE_CHOICES = [
        ('unknown', 'unknown'),
        ('telegram', 'telegram'),
        ('instagram', 'instagram'),
    ]
    title = models.CharField(max_length=100,null=True,blank=True)
    status = models.CharField(max_length=60, choices=STATUS_CHOICES, default='active')
    is_active = models.BooleanField(default=True)
    id = models.CharField(primary_key=True, max_length=10, default=generate_short_uuid, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='conversations')
    source = models.CharField(max_length=90,choices=SOURCE_CHOICES,default='unknown')
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='conversations')
    priority = models.PositiveSmallIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        # Automatically set title if not manually set
        if not self.title:
            self.title = f"{self.source} - {self.customer}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Conversation with {self.customer} by {self.user} (Status: {self.status})"


class Message(models.Model):
    TYPE_CHOICES = [
        ('customer', 'customer'),
        ('AI', 'AI'),
        ('support', 'support'),
        ('marketing', 'marketing'),
    ]
    FEEDBACK_CHOICES = [
        ('none', 'No feedback'),
        ('positive', '👍 Positive'),
        ('negative', '👎 Negative'),
    ]
    MESSAGE_TYPE_CHOICES = [
        ('text', 'Text Message'),
        ('voice', 'Voice Message'),
        ('image', 'Image Message'),
        ('video', 'Video Message'),  # Future
        ('share', 'Post/Reel Share'),  # Instagram post/reel share
    ]
    PROCESSING_STATUS_CHOICES = [
        ('completed', 'Completed'),
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('failed', 'Failed'),
    ]
    
    type = models.CharField(max_length=60, choices=TYPE_CHOICES, default='customer')
    id = models.CharField(primary_key=True, max_length=10, default=generate_short_uuid, editable=False)
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    customer = models.ForeignKey(Customer,on_delete=models.CASCADE,null=True,blank=True)
    content = models.TextField(max_length=1000)
    is_ai_response = models.BooleanField(default=False)
    is_answered = models.BooleanField(default=False)
    metadata = models.JSONField(null=True, blank=True, help_text="Additional metadata for the message (e.g., AI response metadata)")
    
    # ✅ CTA Buttons for multi-channel support (Instagram/WhatsApp/Telegram)
    buttons = models.JSONField(
        null=True,
        blank=True,
        help_text="CTA buttons for this message (Instagram/WhatsApp Button Template). Max 3 buttons. Format: [{'type': 'web_url', 'title': 'عنوان', 'url': 'https://...'}]"
    )
    
    # Token tracking for AI responses
    input_tokens = models.IntegerField(null=True, blank=True, help_text="Number of input tokens used (for AI responses)")
    output_tokens = models.IntegerField(null=True, blank=True, help_text="Number of output tokens generated (for AI responses)")
    total_tokens = models.IntegerField(null=True, blank=True, help_text="Total tokens used (input + output)")
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Response Quality Feedback (Phase 1 - Feature 2)
    feedback = models.CharField(
        max_length=10,
        choices=FEEDBACK_CHOICES,
        default='none',
        help_text="Customer feedback on AI response quality"
    )
    feedback_comment = models.TextField(
        max_length=500,
        blank=True,
        default='',
        help_text="Optional comment from customer about the response"
    )
    feedback_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Timestamp when feedback was submitted"
    )
    
    # ============== Voice & Media Support Fields ==============
    # Message Content Type
    message_type = models.CharField(
        max_length=20,
        choices=MESSAGE_TYPE_CHOICES,
        default='text',
        help_text="Type of message content"
    )
    
    # Media Storage
    media_file = models.FileField(
        upload_to='message_media/%Y/%m/%d/',
        null=True,
        blank=True,
        help_text="Downloaded media file (voice/image)"
    )
    
    media_url = models.URLField(
        max_length=500,
        null=True,
        blank=True,
        help_text="External media URL from platform"
    )
    
    # AI Processing Results
    transcription = models.TextField(
        null=True,
        blank=True,
        help_text="Voice transcription or image description"
    )
    
    # Processing State
    processing_status = models.CharField(
        max_length=20,
        choices=PROCESSING_STATUS_CHOICES,
        default='completed',
        help_text="Media processing status"
    )
    
    processing_error = models.TextField(
        null=True,
        blank=True,
        help_text="Error message if processing failed"
    )
    
    # Processing Metadata
    processed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When media processing completed"
    )
    
    processing_duration_ms = models.IntegerField(
        null=True,
        blank=True,
        help_text="Processing time in milliseconds"
    )

    def __str__(self):
        return f"{self.content} | {self.content}"


class CustomerData(models.Model):
    """
    Model to store custom key-value data for customers.
    Each user can assign custom data fields to any customer.
    """
    customer = models.ForeignKey(
        Customer, 
        on_delete=models.CASCADE, 
        related_name='custom_data'
    )
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='customer_data'
    )
    key = models.CharField(
        max_length=255, 
        help_text="Name of the data field (e.g., 'birthday', 'company', 'notes')"
    )
    value = models.TextField(
        help_text="Value of the data field"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Customer Data"
        verbose_name_plural = "Customer Data"
        unique_together = ['customer', 'user', 'key']  # Each user can only have one value per key per customer
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.customer} | {self.key}: {self.value[:50]}..."