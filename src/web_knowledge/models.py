from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.conf import settings
import uuid

User = get_user_model()





class WebsiteSource(models.Model):
    """
    Model to store website sources that users want to crawl and analyze
    """
    CRAWL_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('crawling', 'Crawling'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('paused', 'Paused'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='website_sources')
    name = models.CharField(max_length=255, help_text="Display name for the website")
    url = models.URLField(help_text="Main URL of the website to crawl")
    description = models.TextField(blank=True, help_text="Optional description of the website")
    
    # Crawl settings
    max_pages = models.PositiveIntegerField(default=200, help_text="Maximum number of pages to crawl")
    crawl_depth = models.PositiveIntegerField(default=5, help_text="Maximum depth to crawl")
    include_external_links = models.BooleanField(default=False, help_text="Include links to external domains")
    
    # Auto-extraction settings
    auto_extract_products = models.BooleanField(
        default=True,  # ✅ Always ON - Pre-filter decides if page has products/services
        help_text="Automatically extract products/services from crawled pages using AI"
    )
    
    # Status and metadata
    crawl_status = models.CharField(max_length=20, choices=CRAWL_STATUS_CHOICES, default='pending')
    pages_crawled = models.PositiveIntegerField(default=0)
    total_qa_pairs = models.PositiveIntegerField(default=0)
    last_crawl_at = models.DateTimeField(null=True, blank=True)
    crawl_started_at = models.DateTimeField(null=True, blank=True)
    crawl_completed_at = models.DateTimeField(null=True, blank=True)
    crawl_error_message = models.TextField(blank=True)
    
    # Progress tracking
    crawl_progress = models.FloatField(default=0.0, help_text="Crawl progress percentage (0.0 to 100.0)")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Website Source"
        verbose_name_plural = "Website Sources"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'crawl_status']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.url})"
    
    def update_progress(self):
        """Update crawl progress and total Q&A pairs"""
        self.pages_crawled = self.pages.count()
        self.total_qa_pairs = QAPair.objects.filter(page__website=self).count()
        
        # Only update crawl_progress if crawl is not completed
        # When crawl is completed, progress should stay at 100%
        if self.crawl_status != 'completed':
            if self.max_pages > 0:
                self.crawl_progress = min((self.pages_crawled / self.max_pages) * 100, 100.0)
            else:
                self.crawl_progress = 0.0
            save_fields = ['pages_crawled', 'total_qa_pairs', 'crawl_progress']
        else:
            # Don't update progress when completed
            save_fields = ['pages_crawled', 'total_qa_pairs']
        
        self.save(update_fields=save_fields)


class WebsitePage(models.Model):
    """
    Model to store individual pages crawled from a website
    یا صفحات/نوشته‌های WordPress که sync شدن
    """
    PROCESSING_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    SOURCE_TYPE_CHOICES = [
        ('crawled', 'Crawled'),
        ('wordpress', 'WordPress Sync'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    website = models.ForeignKey(WebsiteSource, on_delete=models.CASCADE, related_name='pages')
    url = models.URLField(unique=True)
    title = models.CharField(max_length=500, blank=True)
    
    # Source type (crawled یا WordPress sync)
    source_type = models.CharField(max_length=20, choices=SOURCE_TYPE_CHOICES, default='crawled')
    wordpress_post_id = models.IntegerField(null=True, blank=True, help_text="WordPress Post ID if synced")
    
    # Content
    raw_content = models.TextField(help_text="Raw HTML content")
    cleaned_content = models.TextField(help_text="Cleaned text content")
    summary = models.TextField(blank=True, help_text="AI-generated summary of the page")
    
    # Metadata
    meta_description = models.TextField(blank=True)
    meta_keywords = models.TextField(blank=True)
    word_count = models.PositiveIntegerField(default=0)
    
    # Processing status
    processing_status = models.CharField(max_length=20, choices=PROCESSING_STATUS_CHOICES, default='pending')
    processing_error = models.TextField(blank=True)
    
    # SEO and structure data
    h1_tags = models.JSONField(default=list, help_text="List of H1 tags found")
    h2_tags = models.JSONField(default=list, help_text="List of H2 tags found")
    links = models.JSONField(default=list, help_text="List of links found on the page")
    
    # Timestamps
    crawled_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    last_updated = models.DateTimeField(null=True, blank=True, help_text="Last modified date from HTTP headers")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Website Page"
        verbose_name_plural = "Website Pages"
        ordering = ['-crawled_at']
        indexes = [
            models.Index(fields=['website', 'processing_status']),
            models.Index(fields=['url']),
            models.Index(fields=['crawled_at']),
        ]
    
    def __str__(self):
        return f"{self.title or self.url}"
    
    def save(self, *args, **kwargs):
        # Update word count
        if self.cleaned_content:
            self.word_count = len(self.cleaned_content.split())
        super().save(*args, **kwargs)


class QAPair(models.Model):
    """
    Model to store AI-generated Q&A pairs based on website content
    """
    GENERATION_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('generating', 'Generating'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    page = models.ForeignKey(WebsitePage, on_delete=models.CASCADE, related_name='qa_pairs', null=True, blank=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='qa_pairs', null=True, blank=True)
    
    # Q&A content
    question = models.TextField(help_text="AI-generated question")
    answer = models.TextField(help_text="AI-generated answer")
    context = models.TextField(help_text="Source text used to generate the Q&A", blank=True, default='')
    
    # Metadata
    confidence_score = models.FloatField(default=0.0, help_text="AI confidence score (0.0 to 1.0)")
    generation_status = models.CharField(max_length=20, choices=GENERATION_STATUS_CHOICES, default='pending')
    generation_error = models.TextField(blank=True)
    
    # Categories and metadata
    question_type = models.CharField(
        max_length=20,
        choices=[
            ('factual', 'Factual'),
            ('procedural', 'Procedural'),
            ('explanatory', 'Explanatory'),
            ('comparison', 'Comparison'),
            ('practical', 'Practical'),
            ('problem_solving', 'Problem Solving'),
        ],
        default='factual',
        help_text="Type of question"
    )
    category = models.CharField(
        max_length=20,
        choices=[
            ('general', 'General'),
            ('contact', 'Contact'),
            ('services', 'Services'),
            ('pricing', 'Pricing'),
            ('support', 'Support'),
            ('policies', 'Policies'),
            ('location', 'Location'),
        ],
        default='general',
        help_text="Category of the Q&A"
    )
    keywords = models.JSONField(default=list, help_text="Keywords for search and categorization")
    
    # Analytics
    view_count = models.PositiveIntegerField(default=0)
    is_featured = models.BooleanField(default=False, help_text="Mark as featured Q&A")
    is_approved = models.BooleanField(default=True, help_text="Manual approval status")
    created_by_ai = models.BooleanField(default=True, help_text="Whether created by AI or manually")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Q&A Pair"
        verbose_name_plural = "Q&A Pairs"
        ordering = ['-confidence_score', '-created_at']
        indexes = [
            models.Index(fields=['page', 'generation_status']),
            models.Index(fields=['confidence_score']),
            models.Index(fields=['is_featured']),
            models.Index(fields=['category']),
            models.Index(fields=['question_type']),
            models.Index(fields=['is_approved']),
            models.Index(fields=['created_at']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['page', 'question'],
                name='unique_question_per_page'
            ),
        ]
    
    def __str__(self):
        return f"Q: {self.question[:100]}..."
    
    def increment_view_count(self):
        """Increment view count for analytics"""
        self.view_count += 1
        self.save(update_fields=['view_count'])


class CrawlJob(models.Model):
    """
    Model to track crawl jobs and their status
    """
    JOB_STATUS_CHOICES = [
        ('queued', 'Queued'),
        ('running', 'Running'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    website = models.ForeignKey(WebsiteSource, on_delete=models.CASCADE, related_name='crawl_jobs')
    
    # Job details
    celery_task_id = models.CharField(max_length=255, blank=True, help_text="Celery task ID")
    job_status = models.CharField(max_length=20, choices=JOB_STATUS_CHOICES, default='queued')
    
    # Progress tracking
    pages_to_crawl = models.PositiveIntegerField(default=0)
    pages_crawled = models.PositiveIntegerField(default=0)
    pages_processed = models.PositiveIntegerField(default=0)
    qa_pairs_generated = models.PositiveIntegerField(default=0)
    
    # Timing
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    estimated_completion = models.DateTimeField(null=True, blank=True)
    
    # Error handling
    error_message = models.TextField(blank=True)
    error_pages = models.JSONField(default=list, help_text="List of URLs that failed to crawl")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Crawl Job"
        verbose_name_plural = "Crawl Jobs"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['website', 'job_status']),
            models.Index(fields=['celery_task_id']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"Crawl job for {self.website.name} - {self.job_status}"
    
    @property
    def progress_percentage(self):
        """Calculate progress percentage"""
        if self.pages_to_crawl == 0:
            # If no target set yet, return 0 or use a fallback calculation
            if self.pages_crawled > 0:
                # Rough estimate based on typical crawl patterns
                return min(self.pages_crawled * 2, 100.0)
            return 0.0
        return min((self.pages_crawled / self.pages_to_crawl) * 100, 100.0)
    
    def update_progress(self):
        """Update progress counters"""
        self.pages_crawled = self.website.pages.count()
        self.pages_processed = self.website.pages.filter(processing_status='completed').count()
        self.qa_pairs_generated = QAPair.objects.filter(
            page__website=self.website,
            generation_status='completed'
        ).count()
        self.save(update_fields=['pages_crawled', 'pages_processed', 'qa_pairs_generated'])
    
    def __str__(self):
        return f"Crawl Job {self.id} - {self.website.name}"


class Product(models.Model):
    """
    Enhanced model to store products and services for the knowledge base
    Supports both manual entry and AI auto-extraction from websites
    """
    PRODUCT_TYPE_CHOICES = [
        ('service', 'Service'),
        ('product', 'Product'),
        ('software', 'Software'),
        ('consultation', 'Consultation'),
        ('course', 'Course'),
        ('tool', 'Tool'),
        ('other', 'Other'),
    ]
    
    CURRENCY_CHOICES = [
        ('USD', 'US Dollar'),
        ('EUR', 'Euro'),
        ('TRY', 'Turkish Lira'),
        ('AED', 'UAE Dirham'),
        ('SAR', 'Saudi Riyal'),
        ('IRR', 'Iranian Rial'),
        ('IRT', 'Iranian Toman'),
    ]
    
    BILLING_PERIOD_CHOICES = [
        ('one_time', 'One-time Purchase'),
        ('monthly', 'Monthly'),
        ('yearly', 'Yearly'),
        ('weekly', 'Weekly'),
        ('daily', 'Daily'),
    ]
    
    EXTRACTION_METHOD_CHOICES = [
        ('manual', 'Manual Entry'),
        ('ai_auto', 'AI Auto-extracted'),
        ('ai_assisted', 'AI Assisted'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='products')
    
    # ========== Basic Product Information ==========
    title = models.CharField(max_length=255, help_text="Product or service title")
    product_type = models.CharField(
        max_length=20, 
        choices=PRODUCT_TYPE_CHOICES, 
        default='product',
        help_text="Type of product or service"
    )
    description = models.TextField(help_text="Detailed description of the product/service")
    short_description = models.CharField(
        max_length=500,
        blank=True,
        help_text="Brief description for listing pages"
    )
    long_description = models.TextField(
        blank=True,
        help_text="Extended description with full details"
    )
    link = models.URLField(blank=True, help_text="Link to product page, documentation, or more info")
    
    # ========== Pricing Information ==========
    price = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        null=True, 
        blank=True,
        help_text="Current price (used by AI extraction, keep null for manual entry)"
    )
    sale_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Sale price (final price after discount, used for manual entry)"
    )
    original_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Original price before discount"
    )
    discount_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Discount percentage (0-100)"
    )
    discount_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Discount amount in currency"
    )
    currency = models.CharField(
        max_length=3,
        choices=CURRENCY_CHOICES,
        default='USD',
        help_text="Currency code"
    )
    billing_period = models.CharField(
        max_length=20,
        choices=BILLING_PERIOD_CHOICES,
        null=True,
        blank=True,
        help_text="Billing period for subscriptions"
    )
    
    # ========== Product Features & Details ==========
    features = models.JSONField(
        default=list,
        blank=True,
        help_text="List of key features"
    )
    specifications = models.JSONField(
        default=dict,
        blank=True,
        help_text="Technical specifications (key-value pairs)"
    )
    
    # ========== Categorization ==========
    category = models.CharField(
        max_length=100,
        blank=True,
        help_text="Product category"
    )
    brand = models.CharField(
        max_length=100,
        blank=True,
        help_text="Product brand"
    )
    tags = models.JSONField(default=list, help_text="Tags for categorization and search")
    keywords = models.JSONField(
        default=list,
        blank=True,
        help_text="SEO keywords"
    )
    
    # ========== Availability ==========
    is_active = models.BooleanField(default=True, help_text="Whether the product is currently active")
    in_stock = models.BooleanField(
        default=True,
        help_text="Whether the product is in stock"
    )
    stock_quantity = models.IntegerField(
        null=True,
        blank=True,
        help_text="Stock quantity (optional)"
    )
    
    # ========== Media ==========
    image = models.ImageField(
        upload_to='products/images/',
        blank=True,
        null=True,
        help_text="Product image file upload"
    )
    main_image = models.URLField(
        blank=True,
        help_text="URL of main product image"
    )
    images = models.JSONField(
        default=list,
        blank=True,
        help_text="Array of image URLs"
    )
    
    # ========== SEO ==========
    meta_title = models.CharField(
        max_length=200,
        blank=True,
        help_text="Meta title for SEO"
    )
    meta_description = models.TextField(
        max_length=500,
        blank=True,
        help_text="Meta description for SEO"
    )
    
    # ========== Auto-Extraction Source Tracking ==========
    source_website = models.ForeignKey(
        'WebsiteSource',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='auto_extracted_products',
        help_text="Source website (if auto-extracted)"
    )
    source_page = models.ForeignKey(
        'WebsitePage',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='extracted_products',
        help_text="Source page (if auto-extracted)"
    )
    extraction_method = models.CharField(
        max_length=20,
        choices=EXTRACTION_METHOD_CHOICES,
        default='manual',
        help_text="How this product was created"
    )
    extraction_confidence = models.FloatField(
        default=1.0,
        help_text="AI extraction confidence (0-1)"
    )
    extraction_metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text="Extraction metadata (model, timestamp, etc.)"
    )
    
    # ========== External Integration (WooCommerce, Shopify, etc.) ==========
    external_id = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        db_index=True,
        help_text="External product ID (e.g., woo_414, shopify_789)"
    )
    external_source = models.CharField(
        max_length=20,
        blank=True,
        default='manual',
        help_text="Source of the product (woocommerce, shopify, manual)"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Product/Service"
        verbose_name_plural = "Products/Services"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'product_type']),
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['created_at']),
            models.Index(fields=['extraction_method']),
            models.Index(fields=['source_website']),
            models.Index(fields=['user', 'external_source', 'is_active'], name='idx_product_external'),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'external_id'],
                condition=models.Q(external_id__isnull=False),
                name='unique_external_product_per_user',
                violation_error_message='این محصول خارجی قبلاً برای این کاربر وجود دارد'
            )
        ]
    
    def __str__(self):
        return f"{self.title} ({self.get_product_type_display()})"
    
    @property
    def has_link(self):
        """Check if product has a valid link"""
        return bool(self.link and self.link.strip())
    
    @property
    def final_price(self):
        """Calculate final price after discount
        
        Priority:
        1. sale_price (for manual entry)
        2. price (for AI extraction)
        3. Calculate from original_price - discount
        """
        # Priority 1: sale_price (manual entry)
        if self.sale_price:
            return self.sale_price
        
        # Priority 2: price (AI extraction)
        if self.price:
            if self.discount_amount:
                return self.price - self.discount_amount
            elif self.discount_percentage:
                discount = (self.price * self.discount_percentage) / 100
                return self.price - discount
            return self.price
        
        # Priority 3: Calculate from original_price
        if self.original_price:
            if self.discount_amount:
                return self.original_price - self.discount_amount
            elif self.discount_percentage:
                discount = (self.original_price * self.discount_percentage) / 100
                return self.original_price - discount
            return self.original_price
        
        return None
    
    @property
    def has_discount(self):
        """Check if product has a discount"""
        return bool(self.discount_amount or self.discount_percentage)
    
    @property
    def discount_info(self):
        """Get human-readable discount information"""
        if self.discount_percentage:
            return f"{self.discount_percentage}% OFF"
        elif self.discount_amount:
            return f"-{self.discount_amount} {self.currency}"
        return None
    
    @property
    def is_auto_extracted(self):
        """Check if this product was auto-extracted"""
        return self.extraction_method in ['ai_auto', 'ai_assisted']
    
    def get_display_price(self):
        """Get formatted price for display"""
        final = self.final_price
        if final:
            if self.has_discount:
                return f"~~{self.price}~~ {final} {self.currency}"
            return f"{final} {self.currency}"
        return "Price on request"
    
    def get_tags_display(self):
        """Get tags as comma-separated string"""
        return ", ".join(self.tags) if self.tags else "No tags"