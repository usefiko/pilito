from django.db import models
from django.contrib.auth import get_user_model
from django.conf import settings
from django.core.validators import MinValueValidator, FileExtensionValidator
import os


def video_upload_path(instance, filename):
    """
    Generate upload path for video files
    """
    import uuid
    # Generate unique filename to avoid conflicts
    ext = filename.split('.')[-1] if '.' in filename else 'mp4'
    unique_filename = f'{uuid.uuid4().hex}.{ext}'
    return os.path.join('videos', unique_filename)



def video_upload_path_persian(instance, filename):
    """Generate upload path for Persian video files"""
    import uuid
    ext = filename.split('.')[-1] if '.' in filename else 'mp4'
    unique_filename = f'{uuid.uuid4().hex}.{ext}'
    return os.path.join('videos', 'persian', unique_filename)


def video_upload_path_arabic(instance, filename):
    """Generate upload path for Arabic video files"""
    import uuid
    ext = filename.split('.')[-1] if '.' in filename else 'mp4'
    unique_filename = f'{uuid.uuid4().hex}.{ext}'
    return os.path.join('videos', 'arabic', unique_filename)


def video_upload_path_english(instance, filename):
    """Generate upload path for English video files"""
    import uuid
    ext = filename.split('.')[-1] if '.' in filename else 'mp4'
    unique_filename = f'{uuid.uuid4().hex}.{ext}'
    return os.path.join('videos', 'english', unique_filename)


def video_upload_path_turkish(instance, filename):
    """Generate upload path for Turkish video files"""
    import uuid
    ext = filename.split('.')[-1] if '.' in filename else 'mp4'
    unique_filename = f'{uuid.uuid4().hex}.{ext}'
    return os.path.join('videos', 'turkish', unique_filename)


def thumbnail_upload_path(instance, filename):
    """
    Generate upload path for default thumbnail files
    """
    import uuid
    # Generate unique filename to avoid conflicts
    ext = filename.split('.')[-1] if '.' in filename else 'jpg'
    unique_filename = f'{uuid.uuid4().hex}.{ext}'
    return os.path.join('thumbnails', unique_filename)


def thumbnail_upload_path_persian(instance, filename):
    """Generate upload path for Persian thumbnail files"""
    import uuid
    ext = filename.split('.')[-1] if '.' in filename else 'jpg'
    unique_filename = f'{uuid.uuid4().hex}.{ext}'
    return os.path.join('thumbnails', 'persian', unique_filename)


def thumbnail_upload_path_arabic(instance, filename):
    """Generate upload path for Arabic thumbnail files"""
    import uuid
    ext = filename.split('.')[-1] if '.' in filename else 'jpg'
    unique_filename = f'{uuid.uuid4().hex}.{ext}'
    return os.path.join('thumbnails', 'arabic', unique_filename)


def thumbnail_upload_path_english(instance, filename):
    """Generate upload path for English thumbnail files"""
    import uuid
    ext = filename.split('.')[-1] if '.' in filename else 'jpg'
    unique_filename = f'{uuid.uuid4().hex}.{ext}'
    return os.path.join('thumbnails', 'english', unique_filename)


def thumbnail_upload_path_turkish(instance, filename):
    """Generate upload path for Turkish thumbnail files"""
    import uuid
    ext = filename.split('.')[-1] if '.' in filename else 'jpg'
    unique_filename = f'{uuid.uuid4().hex}.{ext}'
    return os.path.join('thumbnails', 'turkish', unique_filename)


class Video(models.Model):
    """
    Model to store course videos with metadata in multiple languages
    """
    LANGUAGE_CHOICES = [
        ('persian', 'Persian (فارسی)'),
        ('arabic', 'Arabic (العربية)'),
        ('english', 'English'),
        ('turkish', 'Turkish (Türkçe)'),
    ]
    
    # Default title and description (will be used as fallback)
    title = models.CharField(max_length=255, help_text="Title of the video")
    description = models.TextField(help_text="Description of the video content")
    
    # Persian content
    title_persian = models.CharField(max_length=255, help_text="Persian title", blank=True)
    description_persian = models.TextField(help_text="Persian description", blank=True)
    
    # Arabic content
    title_arabic = models.CharField(max_length=255, help_text="Arabic title", blank=True)
    description_arabic = models.TextField(help_text="Arabic description", blank=True)
    
    # English content
    title_english = models.CharField(max_length=255, help_text="English title", blank=True)
    description_english = models.TextField(help_text="English description", blank=True)
    
    # Turkish content
    title_turkish = models.CharField(max_length=255, help_text="Turkish title", blank=True)
    description_turkish = models.TextField(help_text="Turkish description", blank=True)
    
    tag = models.CharField(max_length=100, help_text="Tag or category for the video")
    
    # Default video file (for backward compatibility)
    video_file = models.FileField(
        upload_to=video_upload_path,
        validators=[
            FileExtensionValidator(
                allowed_extensions=['mp4', 'avi', 'mov', 'wmv', 'flv', 'webm', 'mkv']
            )
        ],
        help_text="Default video file (supported formats: MP4, AVI, MOV, WMV, FLV, WebM, MKV)",
        null=True,
        blank=True
    )
    
    # Language-specific video files
    video_file_persian = models.FileField(
        upload_to=video_upload_path_persian,
        validators=[
            FileExtensionValidator(
                allowed_extensions=['mp4', 'avi', 'mov', 'wmv', 'flv', 'webm', 'mkv']
            )
        ],
        help_text="Persian video file",
        null=True,
        blank=True
    )
    
    video_file_arabic = models.FileField(
        upload_to=video_upload_path_arabic,
        validators=[
            FileExtensionValidator(
                allowed_extensions=['mp4', 'avi', 'mov', 'wmv', 'flv', 'webm', 'mkv']
            )
        ],
        help_text="Arabic video file",
        null=True,
        blank=True
    )
    
    video_file_english = models.FileField(
        upload_to=video_upload_path_english,
        validators=[
            FileExtensionValidator(
                allowed_extensions=['mp4', 'avi', 'mov', 'wmv', 'flv', 'webm', 'mkv']
            )
        ],
        help_text="English video file",
        null=True,
        blank=True
    )
    
    video_file_turkish = models.FileField(
        upload_to=video_upload_path_turkish,
        validators=[
            FileExtensionValidator(
                allowed_extensions=['mp4', 'avi', 'mov', 'wmv', 'flv', 'webm', 'mkv']
            )
        ],
        help_text="Turkish video file",
        null=True,
        blank=True
    )
    
    # Default thumbnail (for backward compatibility)
    thumbnail = models.ImageField(
        upload_to=thumbnail_upload_path,
        help_text="Default thumbnail image (supported formats: JPG, PNG, WEBP)",
        null=True,
        blank=True
    )
    
    # Language-specific thumbnails
    thumbnail_persian = models.ImageField(
        upload_to=thumbnail_upload_path_persian,
        help_text="Persian thumbnail image",
        null=True,
        blank=True
    )
    
    thumbnail_arabic = models.ImageField(
        upload_to=thumbnail_upload_path_arabic,
        help_text="Arabic thumbnail image",
        null=True,
        blank=True
    )
    
    thumbnail_english = models.ImageField(
        upload_to=thumbnail_upload_path_english,
        help_text="English thumbnail image",
        null=True,
        blank=True
    )
    
    thumbnail_turkish = models.ImageField(
        upload_to=thumbnail_upload_path_turkish,
        help_text="Turkish thumbnail image",
        null=True,
        blank=True
    )
    
    video_minutes = models.PositiveIntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        help_text="Duration of the video in minutes"
    )
    video_seconds = models.PositiveIntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        help_text="Duration of the video in seconds (0-59)"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Video"
        verbose_name_plural = "Videos"

    def get_localized_title(self, language='persian'):
        """
        Get title in the specified language, fallback to default title
        """
        if language in ['persian', 'arabic', 'english', 'turkish']:
            title_field = f'title_{language}'
            localized_title = getattr(self, title_field, '')
            if localized_title:
                return localized_title
        
        # Fallback to default title
        return self.title
    
    def get_localized_description(self, language='persian'):
        """
        Get description in the specified language, fallback to default description
        """
        if language in ['persian', 'arabic', 'english', 'turkish']:
            description_field = f'description_{language}'
            localized_description = getattr(self, description_field, '')
            if localized_description:
                return localized_description
        
        # Fallback to default description
        return self.description
    
    def get_localized_video_file(self, language='persian'):
        """
        Get video file in the specified language, fallback to default video file
        """
        if language in ['persian', 'arabic', 'english', 'turkish']:
            video_file_field = f'video_file_{language}'
            localized_video_file = getattr(self, video_file_field, None)
            
            # If localized video file exists and has content, return it
            if localized_video_file:
                return localized_video_file
        
        # Fallback to default video file
        return self.video_file
    
    def get_localized_video_file_url(self, language='persian', request=None):
        """
        Get video file URL in the specified language
        """
        video_file = self.get_localized_video_file(language)
        if video_file:
            if request:
                return request.build_absolute_uri(video_file.url)
            return video_file.url
        return None
    
    def get_localized_thumbnail(self, language='persian'):
        """
        Get thumbnail in the specified language, fallback to default thumbnail
        """
        if language in ['persian', 'arabic', 'english', 'turkish']:
            thumbnail_field = f'thumbnail_{language}'
            localized_thumbnail = getattr(self, thumbnail_field, None)
            
            # If localized thumbnail exists and has content, return it
            if localized_thumbnail:
                return localized_thumbnail
        
        # Fallback to default thumbnail
        return self.thumbnail
    
    def get_localized_thumbnail_url(self, language='persian', request=None):
        """
        Get thumbnail URL in the specified language
        """
        thumbnail = self.get_localized_thumbnail(language)
        if thumbnail:
            if request:
                return request.build_absolute_uri(thumbnail.url)
            return thumbnail.url
        return None
    
    def get_available_languages(self):
        """
        Get list of languages that have content for this video
        """
        available_languages = []
        
        # Check each language for title, video file, or thumbnail
        for lang_code, lang_name in self.LANGUAGE_CHOICES:
            title_field = f'title_{lang_code}'
            video_field = f'video_file_{lang_code}'
            thumbnail_field = f'thumbnail_{lang_code}'
            
            has_title = bool(getattr(self, title_field, ''))
            has_video = bool(getattr(self, video_field, None))
            has_thumbnail = bool(getattr(self, thumbnail_field, None))
            
            if has_title or has_video or has_thumbnail:
                available_languages.append(lang_code)
        
        return available_languages
    
    def __str__(self):
        # Use Persian title as default, fallback to default title
        title = self.get_localized_title('persian')
        return f"{title} ({self.video_minutes}m {self.video_seconds}s)"


class UserVideoProgress(models.Model):
    """
    Model to track user's progress for each video in each language
    """
    PROGRESS_CHOICES = [
        ('not_started', 'Not Started'),
        ('in_progress', 'In Progress'),
        ('complete', 'Complete'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='video_progress')
    video = models.ForeignKey(Video, on_delete=models.CASCADE, related_name='user_progress')
    language = models.CharField(
        max_length=10, 
        choices=Video.LANGUAGE_CHOICES, 
        default='persian',
        help_text="Language for which progress is tracked"
    )
    status = models.CharField(
        max_length=15, 
        choices=PROGRESS_CHOICES, 
        default='not_started',
        help_text="Current viewing status of the video"
    )
    progress_percentage = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=0.00,
        validators=[MinValueValidator(0.00)],
        help_text="Percentage of video watched (0-100)"
    )
    last_watched_at = models.DateTimeField(null=True, blank=True, help_text="Last time the video was watched")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'video', 'language')
        ordering = ['-updated_at']
        verbose_name = "User Video Progress"
        verbose_name_plural = "User Video Progress"

    def __str__(self):
        return f"{self.user.username} - {self.video.get_localized_title(self.language)} ({self.language}) - {self.status}"

    def save(self, *args, **kwargs):
        """
        Auto-update status based on progress percentage
        """
        if self.progress_percentage == 0:
            self.status = 'not_started'
        elif self.progress_percentage >= 100:
            self.status = 'complete'
        else:
            self.status = 'in_progress'
        
        super().save(*args, **kwargs)