from django.db import models
from django.conf import settings
from django.utils import timezone
from django.contrib.postgres.fields import ArrayField
import json
import uuid

# Import pgvector for vector fields
try:
    from pgvector.django import VectorField, CosineDistance
    PGVECTOR_AVAILABLE = True
except ImportError:
    VectorField = None
    CosineDistance = None
    PGVECTOR_AVAILABLE = False

class AIGlobalConfig(models.Model):
    """
    Global AI configuration - single instance for all users
    Everyone uses gemini-flash-latest
    """
    model_name = models.CharField(max_length=50, default="gemini-flash-latest", help_text="Gemini model to use")
    temperature = models.FloatField(default=0.7, help_text="Response creativity (0.0-1.0)")
    max_tokens = models.IntegerField(default=1000, help_text="Maximum tokens in response")
    auto_response_enabled = models.BooleanField(default=True, help_text="Enable automatic responses globally")
    response_delay_seconds = models.IntegerField(default=2, help_text="Delay before auto response")
    business_hours_only = models.BooleanField(default=False, help_text="Only respond during business hours")
    business_start_time = models.TimeField(default="09:00", help_text="Business start time")
    business_end_time = models.TimeField(default="17:00", help_text="Business end time")
    timezone = models.CharField(max_length=50, default="UTC", help_text="Business timezone")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "🤖 AI Global Config"
        verbose_name_plural = "🤖 AI Global Config"

    def __str__(self):
        return f"Global AI Config: {self.model_name}"
    
    @classmethod
    def get_config(cls):
        """Get or create the global AI configuration"""
        config, created = cls.objects.get_or_create(
            pk=1,  # Always use ID 1 for singleton
            defaults={
                'model_name': 'gemini-flash-latest',
                'temperature': 0.7,
                'max_tokens': 1000,
                'auto_response_enabled': True,
                'response_delay_seconds': 2
            }
        )
        return config

class AIUsageLog(models.Model):
    """
    Detailed per-request AI usage tracking with section/feature information
    Records every AI interaction across all modules for transparency and analytics
    """
    SECTION_CHOICES = [
        ('chat', 'Customer Chat'),
        ('prompt_generation', 'Prompt Generation'),
        ('marketing_workflow', 'Marketing Workflow'),
        ('knowledge_qa', 'Knowledge Base Q&A'),
        ('product_recommendation', 'Product Recommendation'),
        ('rag_pipeline', 'RAG Pipeline'),
        ('web_knowledge', 'Web Knowledge Processing'),
        ('session_memory', 'Session Memory Summary'),
        ('intent_detection', 'Intent Detection'),
        ('embedding_generation', 'Embedding Generation'),
        ('other', 'Other'),
    ]
    
    # Identifiers
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='ai_usage_logs',
        db_index=True,
        help_text="User who triggered the AI request"
    )
    
    # Section/Feature tracking
    section = models.CharField(
        max_length=50,
        choices=SECTION_CHOICES,
        db_index=True,
        help_text="Feature or module that used AI"
    )
    
    # Token usage
    prompt_tokens = models.IntegerField(default=0, help_text="Input tokens used")
    completion_tokens = models.IntegerField(default=0, help_text="Output tokens used")
    total_tokens = models.IntegerField(default=0, help_text="Total tokens used")
    
    # Performance metrics
    response_time_ms = models.IntegerField(default=0, help_text="Response time in milliseconds")
    success = models.BooleanField(default=True, help_text="Whether the request was successful")
    
    # Additional context
    model_name = models.CharField(
        max_length=100,
        blank=True,
        default="gemini-flash-latest",
        help_text="AI model used (e.g., gemini-flash-latest, gpt-4)"
    )
    error_message = models.TextField(blank=True, null=True, help_text="Error details if request failed")
    
    # Metadata
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text="Additional context (conversation_id, message_id, etc.)"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    
    class Meta:
        db_table = 'ai_usage_log'
        verbose_name = "📝 AI Usage Log"
        verbose_name_plural = "📝 AI Usage Logs"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'section', 'created_at']),
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['section', 'created_at']),
            models.Index(fields=['created_at']),
            models.Index(fields=['success']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.get_section_display()} - {self.total_tokens} tokens"
    
    @classmethod
    def log_usage(cls, user, section, prompt_tokens=0, completion_tokens=0, 
                  response_time_ms=0, success=True, model_name="gemini-flash-latest",
                  error_message=None, metadata=None):
        """
        Convenience method to log AI usage
        
        Args:
            user: User instance
            section: Section/feature name (must be in SECTION_CHOICES)
            prompt_tokens: Number of input tokens
            completion_tokens: Number of output tokens
            response_time_ms: Response time in milliseconds
            success: Whether the request was successful
            model_name: AI model used
            error_message: Error details if failed
            metadata: Additional context dictionary
        
        Returns:
            AIUsageLog instance
        """
        return cls.objects.create(
            user=user,
            section=section,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=prompt_tokens + completion_tokens,
            response_time_ms=response_time_ms,
            success=success,
            model_name=model_name,
            error_message=error_message,
            metadata=metadata or {}
        )


class AIUsageTracking(models.Model):
    """
    Track AI usage statistics per user with shared API key
    Daily aggregated statistics (maintained for backward compatibility)
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    date = models.DateField(default=timezone.now)
    total_requests = models.IntegerField(default=0)
    total_prompt_tokens = models.IntegerField(default=0)
    total_completion_tokens = models.IntegerField(default=0)
    total_tokens = models.IntegerField(default=0)
    total_response_time_ms = models.BigIntegerField(default=0)
    average_response_time_ms = models.FloatField(default=0)
    successful_requests = models.IntegerField(default=0)
    failed_requests = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "📊 AI Usage Tracking"
        verbose_name_plural = "📊 AI Usage Tracking"
        unique_together = ['user', 'date']
        indexes = [
            models.Index(fields=['user', 'date']),
            models.Index(fields=['date']),
        ]

    def __str__(self):
        return f"AI Usage: {self.user.username} - {self.date}"

    def update_stats(self, prompt_tokens=0, completion_tokens=0, response_time_ms=0, success=True):
        """Update usage statistics"""
        self.total_requests += 1
        self.total_prompt_tokens += prompt_tokens
        self.total_completion_tokens += completion_tokens
        self.total_tokens += prompt_tokens + completion_tokens
        self.total_response_time_ms += response_time_ms
        
        if success:
            self.successful_requests += 1
        else:
            self.failed_requests += 1
            
        # Calculate average response time
        if self.total_requests > 0:
            self.average_response_time_ms = self.total_response_time_ms / self.total_requests
            
        self.save()


class TenantKnowledge(models.Model):
    """
    Vector store for RAG: FAQ, Manual Prompt, Products, Website
    Uses pgvector for semantic search with OpenAI text-embedding-3-large (3072 dimensions)
    """
    CHUNK_TYPE_CHOICES = [
        ('faq', 'FAQ'),
        ('manual', 'Manual Prompt'),
        ('product', 'Product'),
        ('website', 'Website Page'),
    ]
    
    # Primary key
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Owner (tenant)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='knowledge_chunks',
        db_index=True
    )
    
    # Source reference
    chunk_type = models.CharField(max_length=20, choices=CHUNK_TYPE_CHOICES, db_index=True)
    source_id = models.UUIDField(
        null=True,
        blank=True,
        help_text="Reference to original FAQ/Product/WebsitePage ID"
    )
    
    # Hierarchical structure (for large manual_prompt chunking)
    document_id = models.UUIDField(
        null=True,
        blank=True,
        db_index=True,
        help_text="Group chunks from same document"
    )
    section_title = models.TextField(
        null=True,
        blank=True,
        help_text="Section or paragraph title"
    )
    
    # Content
    full_text = models.TextField(help_text="Full chunk text")
    tldr = models.TextField(
        null=True,
        blank=True,
        help_text="TL;DR summary (80-120 words) for efficient retrieval"
    )
    
    # Embeddings (OpenAI text-embedding-3-small = 1536 dimensions)
    # Note: Using 3-small instead of 3-large because PostgreSQL 15 ivfflat
    # index supports max 2000 dimensions. 3-small is faster, cheaper, and works!
    if PGVECTOR_AVAILABLE:
        tldr_embedding = VectorField(
            dimensions=1536,
            null=True,
            blank=True
        )
        full_embedding = VectorField(
            dimensions=1536,
            null=True,
            blank=True
        )
    else:
        tldr_embedding = models.JSONField(null=True, blank=True)
        full_embedding = models.JSONField(null=True, blank=True)
    
    # Metadata
    language = models.CharField(
        max_length=5,
        null=True,
        blank=True,
        help_text="fa, en, ar, tr"
    )
    word_count = models.IntegerField(default=0)
    metadata = models.JSONField(default=dict, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'tenant_knowledge'
        verbose_name = "📚 Tenant Knowledge (RAG)"
        verbose_name_plural = "📚 Tenant Knowledge (RAG)"
        indexes = [
            models.Index(fields=['user', 'chunk_type']),
            models.Index(fields=['user', 'document_id']),
            models.Index(fields=['created_at']),
        ]
        # ✅ Prevent duplicate chunks from race conditions
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'source_id', 'chunk_type'],
                condition=models.Q(source_id__isnull=False),
                name='unique_chunk_per_source',
                violation_error_message='این صفحه قبلاً chunk شده است'
            )
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.chunk_type} - {self.section_title or 'Chunk'}"


class SessionMemory(models.Model):
    """
    Rolling conversation summaries (Lean RAG v2.1)
    One summary per conversation, updated every 5 messages
    CRITICAL: Summary is REPLACED not APPENDED to prevent accumulation
    """
    # Link to conversation (OneToOne)
    conversation = models.OneToOneField(
        'message.Conversation',
        on_delete=models.CASCADE,
        related_name='session_memory',
        primary_key=True
    )
    
    # Owner (for filtering and billing)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='session_memories',
        db_index=True
    )
    
    # Memory content
    cumulative_summary = models.TextField(
        help_text="Rolling summary of entire conversation (target: ≤150 tokens)",
        blank=True,
        default=''
    )
    
    message_count = models.IntegerField(
        default=0,
        help_text="Number of messages at last summary update"
    )
    
    # Timestamps
    last_updated = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'session_memory'
        verbose_name = "🧠 Session Memory"
        verbose_name_plural = "🧠 Session Memories"
        indexes = [
            models.Index(fields=['user', 'last_updated']),
        ]
    
    def __str__(self):
        return f"Memory: {self.conversation_id} ({self.message_count} msgs)"


class IntentKeyword(models.Model):
    """
    Dynamic intent keywords (optional - for admin panel management)
    Supports multilingual keyword management (FA, EN, AR, TR)
    """
    INTENT_CHOICES = [
        ('pricing', 'Pricing & Plans'),
        ('product', 'Product Info'),
        ('howto', 'How-to & Tutorial'),
        ('contact', 'Contact & Support'),
        ('general', 'General Question'),
    ]
    
    LANGUAGE_CHOICES = [
        ('fa', 'فارسی'),
        ('en', 'English'),
        ('ar', 'العربية'),
        ('tr', 'Türkçe'),
    ]
    
    intent = models.CharField(max_length=20, choices=INTENT_CHOICES, db_index=True)
    language = models.CharField(max_length=5, choices=LANGUAGE_CHOICES, db_index=True)
    keyword = models.CharField(max_length=100)
    weight = models.FloatField(
        default=1.0,
        help_text="Keyword importance (0.1-3.0). Higher = more important"
    )
    
    # Optional: per-user keywords (leave blank for global)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='custom_keywords',
        help_text="Leave blank for global keywords"
    )
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'intent_keywords'
        verbose_name = "🔑 Intent Keyword"
        verbose_name_plural = "🔑 Intent Keywords"
        unique_together = ['intent', 'language', 'keyword', 'user']
        indexes = [
            models.Index(fields=['intent', 'language', 'is_active']),
            models.Index(fields=['user', 'is_active']),
        ]
    
    def __str__(self):
        global_or_user = f"[{self.user.username}]" if self.user else "[Global]"
        return f"{global_or_user} {self.get_language_display()} - {self.get_intent_display()}: {self.keyword}"


class IntentRouting(models.Model):
    """
    Intent routing configuration (optional)
    Maps intents → primary/secondary sources and token budgets
    """
    INTENT_CHOICES = IntentKeyword.INTENT_CHOICES
    
    SOURCE_CHOICES = [
        ('faq', 'FAQ'),
        ('manual', 'Manual Prompt'),
        ('products', 'Products'),
        ('website', 'Website'),
    ]
    
    intent = models.CharField(
        max_length=20,
        choices=INTENT_CHOICES,
        unique=True,
        primary_key=True
    )
    
    primary_source = models.CharField(max_length=20, choices=SOURCE_CHOICES)
    
    secondary_sources = ArrayField(
        models.CharField(max_length=20),
        default=list,
        blank=True,
        help_text="Comma-separated list of secondary sources"
    )
    
    # Token budgets
    primary_token_budget = models.IntegerField(
        default=800,
        help_text="Max tokens for primary source (default: 800)"
    )
    
    secondary_token_budget = models.IntegerField(
        default=300,
        help_text="Max tokens for secondary sources (default: 300)"
    )
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'intent_routing'
        verbose_name = "🧭 Intent Routing"
        verbose_name_plural = "🧭 Intent Routing"
    
    def __str__(self):
        return f"{self.get_intent_display()} → {self.primary_source} (budget: {self.primary_token_budget})"