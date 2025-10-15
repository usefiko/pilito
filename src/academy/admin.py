from django.contrib import admin
from django.utils.html import format_html
from .models import Video, UserVideoProgress

@admin.register(Video)
class VideoAdmin(admin.ModelAdmin):
    """
    Admin interface for Video model with multi-language support
    """
    list_display = ('get_localized_title_display', 'tag', 'get_duration_display', 
                   'has_video_files', 'has_thumbnails', 'video_file_status', 'thumbnail_status', 
                   'available_languages_display', 'created_at')
    list_filter = ('tag', 'created_at', 'video_minutes')
    search_fields = ('title', 'description', 'tag', 'title_persian', 'title_arabic', 
                    'title_english', 'title_turkish', 'description_persian', 
                    'description_arabic', 'description_english', 'description_turkish')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at')

    fieldsets = (
        ('Basic Information', {
            'fields': ('tag', 'video_minutes', 'video_seconds')
        }),
        ('Default Content', {
            'fields': ('title', 'description', 'video_file', 'thumbnail'),
            'description': 'Default content used as fallback when language-specific content is not available'
        }),
        ('Persian Content (فارسی)', {
            'fields': ('title_persian', 'description_persian', 'video_file_persian', 'thumbnail_persian'),
            'classes': ('collapse',)
        }),
        ('Arabic Content (العربية)', {
            'fields': ('title_arabic', 'description_arabic', 'video_file_arabic', 'thumbnail_arabic'),
            'classes': ('collapse',)
        }),
        ('English Content', {
            'fields': ('title_english', 'description_english', 'video_file_english', 'thumbnail_english'),
            'classes': ('collapse',)
        }),
        ('Turkish Content (Türkçe)', {
            'fields': ('title_turkish', 'description_turkish', 'video_file_turkish', 'thumbnail_turkish'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def get_localized_title_display(self, obj):
        """
        Display localized title (prefer Persian, fallback to default)
        """
        return obj.get_localized_title('persian') or obj.title or f"Video #{obj.id}"
    get_localized_title_display.short_description = 'Title'

    def get_duration_display(self, obj):
        """
        Display video duration in minutes and seconds format
        """
        return f"{obj.video_minutes}m {obj.video_seconds}s"
    get_duration_display.short_description = 'Duration'

    def available_languages_display(self, obj):
        """
        Display available languages for this video
        """
        languages = obj.get_available_languages()
        if not languages:
            return "None"
        
        lang_names = {
            'persian': 'FA',
            'arabic': 'AR', 
            'english': 'EN',
            'turkish': 'TR'
        }
        
        display_names = [lang_names.get(lang, lang.upper()) for lang in languages]
        return format_html(' | '.join(f'<span style="background: #28a745; color: white; padding: 2px 6px; border-radius: 3px; font-size: 11px;">{name}</span>' for name in display_names))
    available_languages_display.short_description = 'Available Languages'

    def has_video_files(self, obj):
        """
        Check if video has any files uploaded
        """
        files = [obj.video_file, obj.video_file_persian, obj.video_file_arabic, 
                obj.video_file_english, obj.video_file_turkish]
        return any(bool(f) for f in files)
    has_video_files.boolean = True
    has_video_files.short_description = 'Has Video Files'

    def has_thumbnails(self, obj):
        """
        Check if video has any thumbnails uploaded
        """
        thumbnails = [obj.thumbnail, obj.thumbnail_persian, obj.thumbnail_arabic, 
                     obj.thumbnail_english, obj.thumbnail_turkish]
        return any(bool(t) for t in thumbnails)
    has_thumbnails.boolean = True
    has_thumbnails.short_description = 'Has Thumbnails'

    def video_file_status(self, obj):
        """
        Show which language video files are available
        """
        status = []
        files = {
            'Default': obj.video_file,
            'FA': obj.video_file_persian,
            'AR': obj.video_file_arabic,
            'EN': obj.video_file_english,
            'TR': obj.video_file_turkish,
        }
        
        for lang, file_field in files.items():
            if file_field:
                status.append(f'<span style="color: green; font-weight: bold;">{lang}</span>')
            else:
                status.append(f'<span style="color: red;">{lang}</span>')
        
        return format_html(' | '.join(status))
    video_file_status.short_description = 'File Status'

    def thumbnail_status(self, obj):
        """
        Show which language thumbnails are available
        """
        status = []
        thumbnails = {
            'Default': obj.thumbnail,
            'FA': obj.thumbnail_persian,
            'AR': obj.thumbnail_arabic,
            'EN': obj.thumbnail_english,
            'TR': obj.thumbnail_turkish,
        }
        
        for lang, thumbnail_field in thumbnails.items():
            if thumbnail_field:
                status.append(f'<span style="color: green; font-weight: bold;">{lang}</span>')
            else:
                status.append(f'<span style="color: #ccc;">{lang}</span>')
        
        return format_html(' | '.join(status))
    thumbnail_status.short_description = 'Thumbnail Status'

    def has_persian_video(self, obj):
        return bool(obj.video_file_persian)
    has_persian_video.boolean = True
    has_persian_video.short_description = 'Persian Video'

    def has_arabic_video(self, obj):
        return bool(obj.video_file_arabic)
    has_arabic_video.boolean = True
    has_arabic_video.short_description = 'Arabic Video'

    def has_english_video(self, obj):
        return bool(obj.video_file_english)
    has_english_video.boolean = True
    has_english_video.short_description = 'English Video'

    def has_turkish_video(self, obj):
        return bool(obj.video_file_turkish)
    has_turkish_video.boolean = True
    has_turkish_video.short_description = 'Turkish Video'


@admin.register(UserVideoProgress)
class UserVideoProgressAdmin(admin.ModelAdmin):
    """
    Admin interface for UserVideoProgress model with language support
    """
    list_display = ('user', 'get_video_title', 'language', 'status', 'progress_percentage', 
                   'last_watched_at', 'updated_at')
    list_filter = ('status', 'language', 'video__tag', 'created_at', 'updated_at')
    search_fields = ('user__username', 'user__email', 'video__title', 'video__title_persian',
                    'video__title_arabic', 'video__title_english', 'video__title_turkish')
    ordering = ('-updated_at',)
    readonly_fields = ('created_at', 'updated_at')

    fieldsets = (
        ('Progress Information', {
            'fields': ('user', 'video', 'language', 'status', 'progress_percentage', 'last_watched_at')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def get_video_title(self, obj):
        """
        Get localized video title based on progress language
        """
        return obj.video.get_localized_title(obj.language) or obj.video.title or f"Video #{obj.video.id}"
    get_video_title.short_description = 'Video Title'

    def get_queryset(self, request):
        """
        Optimize queryset with select_related for better performance
        """
        queryset = super().get_queryset(request)
        return queryset.select_related('user', 'video')

    def save_model(self, request, obj, form, change):
        """
        Custom save to ensure language compatibility
        """
        # If no language is specified, default to persian
        if not obj.language:
            obj.language = 'persian'
        super().save_model(request, obj, form, change)

