"""
Admin configuration for web_knowledge app
"""
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import WebsiteSource, WebsitePage, QAPair, CrawlJob, Product


@admin.register(WebsiteSource)
class WebsiteSourceAdmin(admin.ModelAdmin):
    """
    Admin interface for WebsiteSource
    """
    list_display = [
        'name', 'url', 'user', 'crawl_status', 'pages_crawled', 
        'total_qa_pairs', 'crawl_progress', 'last_crawl_at'
    ]
    list_filter = ['crawl_status', 'include_external_links', 'created_at']
    search_fields = ['name', 'url', 'description', 'user__username']
    readonly_fields = [
        'crawl_status', 'pages_crawled', 'total_qa_pairs', 'crawl_progress',
        'last_crawl_at', 'crawl_started_at', 'crawl_completed_at',
        'created_at', 'updated_at'
    ]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('user', 'name', 'url', 'description')
        }),
        ('Crawl Settings', {
            'fields': ('max_pages', 'crawl_depth', 'include_external_links')
        }),
        ('Status & Progress', {
            'fields': (
                'crawl_status', 'crawl_progress', 'pages_crawled', 'total_qa_pairs',
                'last_crawl_at', 'crawl_started_at', 'crawl_completed_at',
                'crawl_error_message'
            ),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')


@admin.register(WebsitePage)
class WebsitePageAdmin(admin.ModelAdmin):
    """
    Admin interface for WebsitePage
    """
    list_display = [
        'title_short', 'url_short', 'website', 'processing_status', 
        'word_count', 'qa_pairs_count', 'crawled_at'
    ]
    list_filter = ['processing_status', 'website', 'crawled_at']
    search_fields = ['title', 'url', 'cleaned_content', 'website__name']
    readonly_fields = [
        'processing_status', 'word_count', 'crawled_at', 'processed_at',
        'created_at', 'updated_at', 'qa_pairs_count'
    ]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('website', 'url', 'title')
        }),
        ('Content', {
            'fields': ('cleaned_content', 'summary', 'word_count'),
            'classes': ('collapse',)
        }),
        ('SEO & Metadata', {
            'fields': ('meta_description', 'meta_keywords', 'h1_tags', 'h2_tags'),
            'classes': ('collapse',)
        }),
        ('Processing', {
            'fields': (
                'processing_status', 'processing_error', 'crawled_at', 
                'processed_at', 'qa_pairs_count'
            ),
            'classes': ('collapse',)
        }),
        ('Raw Data', {
            'fields': ('raw_content', 'links'),
            'classes': ('collapse',)
        })
    )
    
    def title_short(self, obj):
        """Short version of title for list display"""
        return obj.title[:50] + '...' if len(obj.title) > 50 else obj.title
    title_short.short_description = 'Title'
    
    def url_short(self, obj):
        """Short version of URL for list display"""
        url = obj.url
        if len(url) > 50:
            return format_html('<a href="{}" target="_blank">{}</a>', url, url[:47] + '...')
        return format_html('<a href="{}" target="_blank">{}</a>', url, url)
    url_short.short_description = 'URL'
    url_short.allow_tags = True
    
    def qa_pairs_count(self, obj):
        """Count of Q&A pairs for this page"""
        count = obj.qa_pairs.filter(generation_status='completed').count()
        if count > 0:
            return format_html(
                '<a href="{}?page__id__exact={}">{} Q&A pairs</a>',
                reverse('admin:web_knowledge_qapair_changelist'),
                obj.id,
                count
            )
        return '0 Q&A pairs'
    qa_pairs_count.short_description = 'Q&A Pairs'
    qa_pairs_count.allow_tags = True
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('website')


@admin.register(QAPair)
class QAPairAdmin(admin.ModelAdmin):
    """
    Admin interface for QAPair
    """
    list_display = [
        'question_short', 'page', 'confidence_score', 'generation_status',
        'is_featured', 'view_count', 'created_at'
    ]
    list_filter = [
        'generation_status', 'is_featured', 'page__website',
        'confidence_score', 'created_at'
    ]
    search_fields = ['question', 'answer', 'context', 'page__title', 'page__url']
    readonly_fields = [
        'generation_status', 'view_count', 'created_at', 'updated_at'
    ]
    list_editable = ['is_featured']
    
    fieldsets = (
        ('Q&A Content', {
            'fields': ('page', 'question', 'answer', 'context')
        }),
        ('Metadata', {
            'fields': (
                'confidence_score', 'generation_status', 'generation_error',
                'is_featured', 'view_count'
            )
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def question_short(self, obj):
        """Short version of question for list display"""
        return obj.question[:80] + '...' if len(obj.question) > 80 else obj.question
    question_short.short_description = 'Question'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('page', 'page__website')


@admin.register(CrawlJob)
class CrawlJobAdmin(admin.ModelAdmin):
    """
    Admin interface for CrawlJob
    """
    list_display = [
        'website', 'job_status', 'progress_percentage', 'pages_crawled',
        'qa_pairs_generated', 'started_at', 'completed_at'
    ]
    list_filter = ['job_status', 'website', 'started_at']
    search_fields = ['website__name', 'website__url', 'celery_task_id']
    readonly_fields = [
        'celery_task_id', 'progress_percentage', 'started_at', 'completed_at',
        'created_at', 'updated_at'
    ]
    
    fieldsets = (
        ('Job Information', {
            'fields': ('website', 'celery_task_id', 'job_status')
        }),
        ('Progress', {
            'fields': (
                'pages_to_crawl', 'pages_crawled', 'pages_processed',
                'qa_pairs_generated', 'progress_percentage'
            )
        }),
        ('Timing', {
            'fields': ('started_at', 'completed_at', 'estimated_completion')
        }),
        ('Error Handling', {
            'fields': ('error_message', 'error_pages'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('website')


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    """
    Admin interface for Product model
    """
    list_display = [
        'title', 'product_type', 'user', 'is_active', 
        'has_link', 'price', 'created_at'
    ]
    list_filter = [
        'product_type', 'is_active', 'created_at'
    ]
    search_fields = ['title', 'description', 'user__username']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('user', 'title', 'product_type', 'description')
        }),
        ('Details', {
            'fields': ('link', 'price', 'tags', 'is_active')
        }),
        ('Media', {
            'fields': ('image', 'main_image', 'images'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def has_link(self, obj):
        """Display if product has a link"""
        if obj.link:
            return format_html(
                '<a href="{}" target="_blank">🔗 View</a>',
                obj.link
            )
        return '❌ No link'
    has_link.short_description = 'Link'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')