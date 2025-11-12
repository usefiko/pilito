"""
Serializers for web_knowledge app
"""
from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import WebsiteSource, WebsitePage, QAPair, CrawlJob, Product

User = get_user_model()


class WebsiteSourceSerializer(serializers.ModelSerializer):
    """
    Serializer for WebsiteSource model
    """
    pages_crawled = serializers.ReadOnlyField()
    total_qa_pairs = serializers.ReadOnlyField()
    crawl_progress = serializers.ReadOnlyField()
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    page_titles = serializers.SerializerMethodField()
    
    class Meta:
        model = WebsiteSource
        fields = [
            'id', 'user', 'name', 'url', 'description',
            'max_pages', 'crawl_depth', 'include_external_links',
            'auto_extract_products',  # NEW: Auto product extraction toggle
            'crawl_status', 'pages_crawled', 'total_qa_pairs',
            'last_crawl_at', 'crawl_started_at', 'crawl_completed_at',
            'crawl_error_message', 'crawl_progress',
            'page_titles', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'crawl_status', 'pages_crawled', 'total_qa_pairs',
            'last_crawl_at', 'crawl_started_at', 'crawl_completed_at',
            'crawl_error_message', 'crawl_progress',
            'created_at', 'updated_at'
        ]
    
    def validate_url(self, value):
        """Validate URL format"""
        if not value.startswith(('http://', 'https://')):
            raise serializers.ValidationError("URL must start with http:// or https://")
        return value
    
    def validate_max_pages(self, value):
        """Validate max_pages limit"""
        if value > 500:  # Reasonable limit
            raise serializers.ValidationError("Maximum pages cannot exceed 500")
        if value < 1:
            raise serializers.ValidationError("Maximum pages must be at least 1")
        return value
    
    def validate_crawl_depth(self, value):
        """Validate crawl depth"""
        if value > 5:  # Reasonable depth limit
            raise serializers.ValidationError("Crawl depth cannot exceed 5")
        if value < 1:
            raise serializers.ValidationError("Crawl depth must be at least 1")
        return value
    
    def get_page_titles(self, obj):
        """Get list of page titles for this website"""
        pages = obj.pages.filter(processing_status='completed').order_by('-crawled_at')[:10]
        return [
            {
                'id': str(page.id),
                'title': page.title,
                'url': page.url,
                'summary': page.summary,
                'word_count': page.word_count,
                'qa_pairs_count': page.qa_pairs.filter(generation_status='completed').count(),
                'crawled_at': page.crawled_at
            }
            for page in pages
        ]


class WebsiteSourceCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating new website sources
    """
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    
    class Meta:
        model = WebsiteSource
        fields = [
            'user', 'name', 'url', 'description',
            'max_pages', 'crawl_depth', 'include_external_links'
        ]
    
    def validate_url(self, value):
        """Validate URL format"""
        if not value.startswith(('http://', 'https://')):
            raise serializers.ValidationError("URL must start with http:// or https://")
        return value


class ProductCompactSerializer(serializers.ModelSerializer):
    """
    Compact serializer for Product listings (e.g., in WebsitePage details)
    """
    product_type_display = serializers.ReadOnlyField(source='get_product_type_display')
    final_price = serializers.ReadOnlyField()
    currency_display = serializers.SerializerMethodField()
    
    class Meta:
        model = Product
        fields = [
            'id', 'title', 'product_type', 'product_type_display',
            'description', 'short_description', 'link',
            'price', 'final_price', 'currency', 'currency_display',
            'image', 'main_image', 'is_active', 'in_stock',
            'extraction_method', 'created_at'
        ]
    
    def get_currency_display(self, obj):
        """Get human-readable currency name"""
        currency_dict = dict(Product.CURRENCY_CHOICES)
        return currency_dict.get(obj.currency, obj.currency)


class WebsitePageSerializer(serializers.ModelSerializer):
    """
    Serializer for WebsitePage model with product extraction info
    Now includes cleaned_content for frontend display (summary generation removed)
    """
    website_name = serializers.CharField(source='website.name', read_only=True)
    qa_pairs_count = serializers.SerializerMethodField()
    products_count = serializers.SerializerMethodField()
    
    class Meta:
        model = WebsitePage
        fields = [
            'id', 'website', 'website_name', 'url', 'title',
            'cleaned_content',  # ✅ Added: Full cleaned content for display
            'meta_description', 'meta_keywords',
            'word_count', 'processing_status', 'processing_error',
            'h1_tags', 'h2_tags', 
            'qa_pairs_count', 'products_count',
            'crawled_at', 'processed_at', 'last_updated',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'processing_status', 'processing_error',
            'crawled_at', 'processed_at', 'last_updated',
            'created_at', 'updated_at'
        ]
    
    def get_qa_pairs_count(self, obj):
        """Get number of Q&A pairs for this page"""
        return obj.qa_pairs.filter(generation_status='completed').count()
    
    def get_products_count(self, obj):
        """Get number of products extracted from this page"""
        return obj.extracted_products.filter(is_active=True).count()


class WebsitePageUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating WebsitePage objects
    
    Note: 'summary' field removed - not generated anymore, use cleaned_content instead
    """
    class Meta:
        model = WebsitePage
        fields = [
            'title', 'cleaned_content', 'meta_description', 'meta_keywords',
            'h1_tags', 'h2_tags'
        ]
    
    def validate_title(self, value):
        """Validate title length"""
        if len(value.strip()) < 3:
            raise serializers.ValidationError("Title must be at least 3 characters long")
        return value.strip()
    
    def validate_cleaned_content(self, value):
        """Validate content length"""
        if len(value.strip()) < 50:
            raise serializers.ValidationError("Content must be at least 50 characters long")
        return value.strip()
    
    def update(self, instance, validated_data):
        """Update page and recalculate word count"""
        # Update fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        # Recalculate word count if content changed
        if 'cleaned_content' in validated_data:
            instance.word_count = len(validated_data['cleaned_content'].split())
        
        instance.save()
        return instance


class WebsitePageDetailSerializer(WebsitePageSerializer):
    """
    Detailed serializer for WebsitePage including content and extracted products
    """
    qa_pairs = serializers.SerializerMethodField()
    extracted_products = serializers.SerializerMethodField()
    
    class Meta(WebsitePageSerializer.Meta):
        fields = WebsitePageSerializer.Meta.fields + [
            'cleaned_content', 'links', 'qa_pairs', 'extracted_products'
        ]
    
    def get_qa_pairs(self, obj):
        """Get Q&A pairs for this page"""
        qa_pairs = obj.qa_pairs.filter(generation_status='completed').order_by('-confidence_score')[:10]
        return QAPairSerializer(qa_pairs, many=True).data
    
    def get_extracted_products(self, obj):
        """Get products extracted from this page"""
        products = obj.extracted_products.filter(is_active=True).order_by('-created_at')[:10]
        return ProductCompactSerializer(products, many=True).data


class QAPairSerializer(serializers.ModelSerializer):
    """
    Serializer for QAPair model
    """
    page_title = serializers.CharField(source='page.title', read_only=True)
    page_url = serializers.CharField(source='page.url', read_only=True)
    website_name = serializers.CharField(source='page.website.name', read_only=True)
    
    class Meta:
        model = QAPair
        fields = [
            'id', 'page', 'page_title', 'page_url', 'website_name',
            'question', 'answer', 'context', 'confidence_score',
            'question_type', 'category', 'keywords',
            'generation_status', 'generation_error',
            'view_count', 'is_featured', 'is_approved', 'created_by_ai',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'generation_status', 'generation_error', 'view_count',
            'created_at', 'updated_at'
        ]


class QAPairCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating Q&A pairs manually
    """
    class Meta:
        model = QAPair
        fields = [
            'page', 'question', 'answer', 'context',
            'question_type', 'category', 'keywords',
            'confidence_score', 'is_featured'
        ]
        extra_kwargs = {
            'page': {'required': False, 'allow_null': True},
            'context': {'required': False},
            'question_type': {'required': False},
            'category': {'required': False},
            'keywords': {'required': False},
            'confidence_score': {'required': False},
            'is_featured': {'required': False},
        }
    
    def validate_page(self, value):
        """Validate that the page belongs to the current user"""
        if value is None:
            return value
            
        request = self.context.get('request')
        if request and request.user:
            if value.website.user != request.user:
                raise serializers.ValidationError("You can only add Q&A pairs to your own websites")
        return value
    
    def create(self, validated_data):
        """Create a manually added Q&A pair"""
        # If no page provided, try to assign user's latest website/page
        if 'page' not in validated_data or validated_data['page'] is None:
            request = self.context.get('request')
            if request and request.user:
                # Get user's latest website
                latest_website = WebsiteSource.objects.filter(user=request.user).order_by('-created_at').first()
                if latest_website:
                    # Get or create a general page for this website
                    page, created = WebsitePage.objects.get_or_create(
                        website=latest_website,
                        url=f"{latest_website.url}/general",
                        defaults={
                            'title': 'General Information',
                            'raw_content': 'General Q&A content',
                            'cleaned_content': 'General Q&A content',
                            'processing_status': 'completed',
                            'word_count': 3
                        }
                    )
                    validated_data['page'] = page
        
        # Check for existing Q&A with same question on same page
        page = validated_data.get('page')
        question = validated_data.get('question')
        
        if page and question:
            existing_qa = QAPair.objects.filter(page=page, question=question).first()
            if existing_qa:
                # Instead of creating a new one, update the existing Q&A with new answer
                from django.utils import timezone
                for key, value in validated_data.items():
                    if key not in ['page', 'question']:  # Don't update page and question
                        setattr(existing_qa, key, value)
                
                # Update metadata
                existing_qa.updated_at = timezone.now()
                existing_qa.save()
                return existing_qa
        
        # Set the user field
        request = self.context.get('request')
        if request and request.user:
            validated_data['user'] = request.user
            
        validated_data['created_by_ai'] = False
        validated_data['is_approved'] = True
        validated_data['generation_status'] = 'completed'
        return super().create(validated_data)


class QAPairPartialCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating Q&A pairs manually with minimal requirements (only question and answer required)
    """
    website_id = serializers.UUIDField(write_only=True, required=False)
    page_id = serializers.UUIDField(write_only=True, required=False, allow_null=True)
    context = serializers.CharField(required=False, allow_blank=True)
    question_type = serializers.CharField(required=False)
    category = serializers.CharField(required=False)
    keywords = serializers.CharField(required=False, allow_blank=True)
    confidence_score = serializers.FloatField(required=False)
    is_featured = serializers.BooleanField(required=False)
    
    class Meta:
        model = QAPair
        fields = [
            'website_id', 'page_id', 'question', 'answer', 'context',
            'question_type', 'category', 'keywords',
            'confidence_score', 'is_featured'
        ]
    
    def validate_website_id(self, value):
        """Validate that the website belongs to the current user"""
        if not value:
            return value
            
        request = self.context.get('request')
        if request and request.user:
            try:
                website = WebsiteSource.objects.get(id=value, user=request.user)
                return value
            except WebsiteSource.DoesNotExist:
                raise serializers.ValidationError("Website not found or access denied")
        return value
    
    def create(self, validated_data):
        """Create a Q&A pair with minimal requirements (only question and answer required)"""
        website_id = validated_data.pop('website_id', None)
        page_id = validated_data.pop('page_id', None)
        
        # Handle page assignment
        if page_id:
            # If page_id is provided, use it directly
            try:
                page = WebsitePage.objects.get(id=page_id)
                # Verify the page belongs to the current user
                request = self.context.get('request')
                if request and request.user and page.website.user != request.user:
                    raise serializers.ValidationError("You can only add Q&A pairs to your own pages")
                validated_data['page'] = page
            except WebsitePage.DoesNotExist:
                raise serializers.ValidationError("Page not found")
        elif website_id:
            # If website_id provided, create a general page entry or use existing
            website = WebsiteSource.objects.get(id=website_id)
            # Try to find an existing general page or create one
            page, created = WebsitePage.objects.get_or_create(
                website=website,
                url=f"{website.url}/general",
                defaults={
                    'title': 'General Information',
                    'content': 'General Q&A content',
                    'cleaned_content': 'General Q&A content',
                    'processing_status': 'completed',
                    'word_count': 3
                }
            )
            validated_data['page'] = page
        else:
            # Neither website_id nor page provided - try to assign user's latest website/page
            request = self.context.get('request')
            if request and request.user:
                # Get user's latest website
                latest_website = WebsiteSource.objects.filter(user=request.user).order_by('-created_at').first()
                if latest_website:
                    # Get or create a general page for this website
                    page, created = WebsitePage.objects.get_or_create(
                        website=latest_website,
                        url=f"{latest_website.url}/general",
                        defaults={
                            'title': 'General Information',
                            'raw_content': 'General Q&A content',
                            'cleaned_content': 'General Q&A content',
                            'processing_status': 'completed',
                            'word_count': 3
                        }
                    )
                    validated_data['page'] = page
                else:
                    # If user has no websites, page can be None
                    validated_data['page'] = None
            else:
                validated_data['page'] = None
        
        # Check for existing Q&A with same question on same page
        page = validated_data.get('page')
        question = validated_data.get('question')
        
        if page and question:
            existing_qa = QAPair.objects.filter(page=page, question=question).first()
            if existing_qa:
                # Instead of creating a new one, update the existing Q&A with new answer
                from django.utils import timezone
                
                # Set default values for optional fields first
                validated_data.setdefault('context', '')
                validated_data.setdefault('question_type', 'factual')
                validated_data.setdefault('category', 'general')
                validated_data.setdefault('keywords', '')
                validated_data.setdefault('confidence_score', 1.0)
                validated_data.setdefault('is_featured', False)
                
                for key, value in validated_data.items():
                    if key not in ['page', 'question']:  # Don't update page and question
                        setattr(existing_qa, key, value)
                
                # Update metadata
                existing_qa.updated_at = timezone.now()
                existing_qa.save()
                return existing_qa
        
        # Set the user field
        request = self.context.get('request')
        if request and request.user:
            validated_data['user'] = request.user
        
        # Set default values for manual creation
        validated_data['created_by_ai'] = False
        validated_data['is_approved'] = True
        validated_data['generation_status'] = 'completed'
        
        # Set default values for optional fields
        validated_data.setdefault('context', '')
        validated_data.setdefault('question_type', 'factual')
        validated_data.setdefault('category', 'general')
        validated_data.setdefault('keywords', '')
        validated_data.setdefault('confidence_score', 1.0)
        validated_data.setdefault('is_featured', False)
        
        return super().create(validated_data)


class QAPairBulkCreateSerializer(serializers.Serializer):
    """
    Serializer for bulk creating Q&A pairs for a website
    """
    website_id = serializers.UUIDField()
    max_qa_per_page = serializers.IntegerField(default=8, min_value=3, max_value=15)
    categories = serializers.MultipleChoiceField(
        choices=[
            'general', 'contact', 'services', 'pricing', 
            'support', 'policies', 'location'
        ],
        default=['general', 'contact', 'services']
    )
    question_types = serializers.MultipleChoiceField(
        choices=[
            'factual', 'procedural', 'explanatory', 
            'comparison', 'practical', 'problem_solving'
        ],
        default=['factual', 'procedural', 'explanatory']
    )
    
    def validate_website_id(self, value):
        """Validate that website exists and belongs to user"""
        request = self.context.get('request')
        if not request or not request.user:
            raise serializers.ValidationError("Authentication required")
        
        try:
            from .models import WebsiteSource
            website = WebsiteSource.objects.get(id=value, user=request.user)
        except WebsiteSource.DoesNotExist:
            raise serializers.ValidationError("Website not found or access denied")
        
        return value


class CrawlJobSerializer(serializers.ModelSerializer):
    """
    Serializer for CrawlJob model
    """
    website_name = serializers.CharField(source='website.name', read_only=True)
    progress_percentage = serializers.ReadOnlyField()
    
    class Meta:
        model = CrawlJob
        fields = [
            'id', 'website', 'website_name', 'celery_task_id',
            'job_status', 'pages_to_crawl', 'pages_crawled',
            'pages_processed', 'qa_pairs_generated',
            'progress_percentage', 'started_at', 'completed_at',
            'estimated_completion', 'error_message', 'error_pages',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'celery_task_id', 'progress_percentage',
            'created_at', 'updated_at'
        ]


class StartCrawlSerializer(serializers.Serializer):
    """
    Serializer for starting a crawl job
    """
    website_id = serializers.UUIDField()
    force_recrawl = serializers.BooleanField(default=False)
    
    def validate_website_id(self, value):
        """Validate that website exists and belongs to user"""
        request = self.context.get('request')
        if not request or not request.user:
            raise serializers.ValidationError("Authentication required")
        
        try:
            website = WebsiteSource.objects.get(id=value, user=request.user)
        except WebsiteSource.DoesNotExist:
            raise serializers.ValidationError("Website not found or access denied")
        
        return value


class QASearchSerializer(serializers.Serializer):
    """
    Serializer for Q&A search requests
    """
    query = serializers.CharField(max_length=500)
    website_id = serializers.UUIDField(required=False)
    limit = serializers.IntegerField(default=10, min_value=1, max_value=50)
    include_context = serializers.BooleanField(default=True)


class BulkQAGenerationSerializer(serializers.Serializer):
    """
    Serializer for bulk Q&A generation
    """
    website_id = serializers.UUIDField()
    pages_per_batch = serializers.IntegerField(default=5, min_value=1, max_value=20)
    max_qa_per_page = serializers.IntegerField(default=5, min_value=1, max_value=10)
    
    def validate_website_id(self, value):
        """Validate that website exists and belongs to user"""
        request = self.context.get('request')
        if not request or not request.user:
            raise serializers.ValidationError("Authentication required")
        
        try:
            website = WebsiteSource.objects.get(id=value, user=request.user)
        except WebsiteSource.DoesNotExist:
            raise serializers.ValidationError("Website not found or access denied")
        
        return value


class WebsiteAnalyticsSerializer(serializers.Serializer):
    """
    Serializer for website analytics data
    """
    total_pages = serializers.IntegerField()
    total_qa_pairs = serializers.IntegerField()
    avg_confidence_score = serializers.FloatField()
    top_pages_by_qa = serializers.ListField()
    recent_activity = serializers.ListField()
    crawl_history = serializers.ListField()


class QAFeedbackSerializer(serializers.Serializer):
    """
    Serializer for Q&A feedback
    """
    qa_pair_id = serializers.UUIDField()
    is_helpful = serializers.BooleanField()
    feedback_text = serializers.CharField(max_length=1000, required=False, allow_blank=True)
    
    def validate_qa_pair_id(self, value):
        """Validate that Q&A pair exists and is accessible"""
        request = self.context.get('request')
        if not request or not request.user:
            raise serializers.ValidationError("Authentication required")
        
        try:
            qa_pair = QAPair.objects.get(
                id=value,
                page__website__user=request.user
            )
        except QAPair.DoesNotExist:
            raise serializers.ValidationError("Q&A pair not found or access denied")
        
        return value


class ProductSerializer(serializers.ModelSerializer):
    """
    Comprehensive serializer for Product model with full auto-extraction support
    """
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    has_link = serializers.ReadOnlyField()
    tags_display = serializers.ReadOnlyField(source='get_tags_display')
    product_type_display = serializers.ReadOnlyField(source='get_product_type_display')
    final_price = serializers.ReadOnlyField()
    has_discount = serializers.ReadOnlyField()
    discount_info = serializers.ReadOnlyField()
    is_auto_extracted = serializers.ReadOnlyField()
    
    # Additional read-only fields for frontend display
    source_website_name = serializers.CharField(source='source_website.name', read_only=True, allow_null=True)
    source_page_url = serializers.CharField(source='source_page.url', read_only=True, allow_null=True)
    currency_display = serializers.SerializerMethodField()
    billing_period_display = serializers.SerializerMethodField()
    
    class Meta:
        model = Product
        fields = [
            'id', 'user', 
            # Basic Information
            'title', 'product_type', 'product_type_display',
            'description', 'short_description', 'long_description',
            'link', 'has_link', 
            # Pricing
            'price', 'sale_price', 'original_price', 'currency', 'currency_display', 'final_price',
            'discount_percentage', 'discount_amount', 'has_discount', 'discount_info',
            'billing_period', 'billing_period_display',
            # Product Details
            'features', 'specifications',
            'category', 'brand', 'tags', 'tags_display', 'keywords',
            # Availability
            'is_active', 'in_stock', 'stock_quantity',
            # Media
            'image', 'main_image', 'images',
            # SEO
            'meta_title', 'meta_description',
            # Auto-extraction info
            'extraction_method', 'extraction_confidence', 'extraction_metadata',
            'is_auto_extracted', 'source_website', 'source_website_name',
            'source_page', 'source_page_url',
            # External Integration (WooCommerce, Shopify, etc.)
            'external_id', 'external_source',
            # Timestamps
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'created_at', 'updated_at', 'final_price', 'has_discount', 
            'discount_info', 'is_auto_extracted'
        ]
    
    def get_currency_display(self, obj):
        """Get human-readable currency name"""
        currency_dict = dict(Product.CURRENCY_CHOICES)
        return currency_dict.get(obj.currency, obj.currency)
    
    def get_billing_period_display(self, obj):
        """Get human-readable billing period"""
        if not obj.billing_period:
            return None
        billing_dict = dict(Product.BILLING_PERIOD_CHOICES)
        return billing_dict.get(obj.billing_period, obj.billing_period)
    
    def validate_title(self, value):
        """Validate product title"""
        if len(value.strip()) < 3:
            raise serializers.ValidationError("Title must be at least 3 characters long")
        return value.strip()
    
    def validate_description(self, value):
        """Validate product description"""
        if len(value.strip()) < 10:
            raise serializers.ValidationError("Description must be at least 10 characters long")
        return value.strip()
    
    def validate_link(self, value):
        """Validate product link"""
        if value and not value.startswith(('http://', 'https://')):
            raise serializers.ValidationError("Link must start with http:// or https://")
        return value
    
    def validate_price(self, value):
        """Validate price"""
        if value is not None and value < 0:
            raise serializers.ValidationError("Price cannot be negative")
        return value
    
    def validate_discount_percentage(self, value):
        """Validate discount percentage"""
        if value is not None and (value < 0 or value > 100):
            raise serializers.ValidationError("Discount percentage must be between 0 and 100")
        return value


class ProductCreateSerializer(serializers.ModelSerializer):
    """
    Comprehensive serializer for creating new products with full field support
    """
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    
    class Meta:
        model = Product
        fields = [
            'user', 
            # Basic Information
            'title', 'product_type', 'description', 'short_description', 'long_description',
            'link',
            # Pricing
            'price', 'sale_price', 'original_price', 'currency', 'discount_percentage', 'discount_amount',
            'billing_period',
            # Product Details
            'features', 'specifications',
            'category', 'brand', 'tags', 'keywords',
            # Availability
            'is_active', 'in_stock', 'stock_quantity',
            # Media
            'image', 'main_image', 'images',
            # SEO
            'meta_title', 'meta_description',
            # Auto-extraction (for API-created products)
            'extraction_method', 'extraction_confidence', 'extraction_metadata',
            'source_website', 'source_page'
        ]
        extra_kwargs = {
            'short_description': {'required': False},
            'long_description': {'required': False},
            'link': {'required': False},
            'price': {'required': False},
            'sale_price': {'required': False},
            'original_price': {'required': False},
            'discount_percentage': {'required': False},
            'discount_amount': {'required': False},
            'billing_period': {'required': False},
            'features': {'required': False},
            'specifications': {'required': False},
            'category': {'required': False},
            'brand': {'required': False},
            'keywords': {'required': False},
            'stock_quantity': {'required': False},
            'image': {'required': False},
            'main_image': {'required': False},
            'images': {'required': False},
            'meta_title': {'required': False},
            'meta_description': {'required': False},
            'extraction_method': {'required': False},
            'extraction_confidence': {'required': False},
            'extraction_metadata': {'required': False},
            'source_website': {'required': False},
            'source_page': {'required': False},
        }
    
    def validate_title(self, value):
        """Validate product title"""
        if len(value.strip()) < 3:
            raise serializers.ValidationError("Title must be at least 3 characters long")
        return value.strip()
    
    def validate_description(self, value):
        """Validate product description"""
        if len(value.strip()) < 10:
            raise serializers.ValidationError("Description must be at least 10 characters long")
        return value.strip()
    
    def validate_link(self, value):
        """Validate product link"""
        if value and not value.startswith(('http://', 'https://')):
            raise serializers.ValidationError("Link must start with http:// or https://")
        return value
    
    def validate_price(self, value):
        """Validate price"""
        if value is not None and value < 0:
            raise serializers.ValidationError("Price cannot be negative")
        return value
    
    def validate_sale_price(self, value):
        """Validate sale price"""
        if value is not None and value < 0:
            raise serializers.ValidationError("Sale price cannot be negative")
        return value
    
    def validate_discount_percentage(self, value):
        """Validate discount percentage"""
        if value is not None and (value < 0 or value > 100):
            raise serializers.ValidationError("Discount percentage must be between 0 and 100")
        return value


class ProductUpdateSerializer(serializers.ModelSerializer):
    """
    Comprehensive serializer for updating products with full field support
    """
    class Meta:
        model = Product
        fields = [
            # Basic Information
            'title', 'product_type', 'description', 'short_description', 'long_description',
            'link',
            # Pricing
            'price', 'sale_price', 'original_price', 'currency', 'discount_percentage', 'discount_amount',
            'billing_period',
            # Product Details
            'features', 'specifications',
            'category', 'brand', 'tags', 'keywords',
            # Availability
            'is_active', 'in_stock', 'stock_quantity',
            # Media
            'image', 'main_image', 'images',
            # SEO
            'meta_title', 'meta_description',
        ]
    
    def validate_title(self, value):
        """Validate product title"""
        if value and len(value.strip()) < 3:
            raise serializers.ValidationError("Title must be at least 3 characters long")
        return value.strip() if value else value
    
    def validate_description(self, value):
        """Validate product description"""
        if value and len(value.strip()) < 10:
            raise serializers.ValidationError("Description must be at least 10 characters long")
        return value.strip() if value else value
    
    def validate_link(self, value):
        """Validate product link"""
        if value and not value.startswith(('http://', 'https://')):
            raise serializers.ValidationError("Link must start with http:// or https://")
        return value
    
    def validate_price(self, value):
        """Validate price"""
        if value is not None and value < 0:
            raise serializers.ValidationError("Price cannot be negative")
        return value
    
    def validate_sale_price(self, value):
        """Validate sale price"""
        if value is not None and value < 0:
            raise serializers.ValidationError("Sale price cannot be negative")
        return value
    
    def validate_discount_percentage(self, value):
        """Validate discount percentage"""
        if value is not None and (value < 0 or value > 100):
            raise serializers.ValidationError("Discount percentage must be between 0 and 100")
        return value


class GeneratePromptSerializer(serializers.Serializer):
    """
    Serializer for generating AI prompts
    """
    # Optional parameters for customizing prompt generation
    manual_prompt = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text="Optional user-provided manual prompt (lowest priority)"
    )
    include_website_data = serializers.BooleanField(
        default=True, 
        help_text="Whether to include website source and page data in the prompt"
    )
    include_products = serializers.BooleanField(
        default=True,
        help_text="Whether to include product/service information in the prompt"
    )
    max_pages = serializers.IntegerField(
        default=10,
        min_value=1,
        max_value=50,
        help_text="Maximum number of website pages to include in prompt"
    )
    max_products = serializers.IntegerField(
        default=5,
        min_value=1,
        max_value=20,
        help_text="Maximum number of products/services to include in prompt"
    )
