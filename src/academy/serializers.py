from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Video, UserVideoProgress

User = get_user_model()


class VideoSerializer(serializers.ModelSerializer):
    """
    Serializer for Video model with language support
    """
    # Only show localized content based on request language parameter
    localized_title = serializers.SerializerMethodField()
    localized_description = serializers.SerializerMethodField()
    localized_video_file_url = serializers.SerializerMethodField()
    localized_thumbnail_url = serializers.SerializerMethodField()
    available_languages = serializers.SerializerMethodField()
    duration_formatted = serializers.SerializerMethodField()
    
    class Meta:
        model = Video
        fields = [
            'id', 'localized_title', 'localized_description', 'localized_video_file_url',
            'localized_thumbnail_url', 'tag', 'video_minutes', 'video_seconds', 'duration_formatted', 'available_languages', 
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'localized_title', 'localized_description', 'localized_video_file_url', 'localized_thumbnail_url', 'available_languages']

    def get_available_languages(self, obj):
        """
        Get list of available languages for this video
        """
        return obj.get_available_languages()

    def get_localized_title(self, obj):
        """
        Get title in the requested language
        """
        request = self.context.get('request')
        language = 'persian'  # Default language
        if request:
            language = request.query_params.get('lang') or request.query_params.get('language') or 'persian'
        return obj.get_localized_title(language)
    
    def get_localized_description(self, obj):
        """
        Get description in the requested language
        """
        request = self.context.get('request')
        language = 'persian'  # Default language
        if request:
            language = request.query_params.get('lang') or request.query_params.get('language') or 'persian'
        return obj.get_localized_description(language)
    
    def get_localized_video_file_url(self, obj):
        """
        Get video file URL in the requested language
        """
        request = self.context.get('request')
        language = 'persian'  # Default language
        if request:
            language = request.query_params.get('lang') or request.query_params.get('language') or 'persian'
        return obj.get_localized_video_file_url(language, request)
    
    def get_localized_thumbnail_url(self, obj):
        """
        Get thumbnail URL in the requested language
        """
        request = self.context.get('request')
        language = 'persian'  # Default language
        if request:
            language = request.query_params.get('lang') or request.query_params.get('language') or 'persian'
        return obj.get_localized_thumbnail_url(language, request)
    
    def get_duration_formatted(self, obj):
        """
        Get duration in formatted string (e.g., "5m 30s")
        """
        return f"{obj.video_minutes}m {obj.video_seconds}s"


class UserVideoProgressSerializer(serializers.ModelSerializer):
    """
    Serializer for UserVideoProgress model with language support
    """
    video_title = serializers.SerializerMethodField()
    video_thumbnail_url = serializers.SerializerMethodField()
    video_tag = serializers.CharField(source='video.tag', read_only=True)
    video_minutes = serializers.IntegerField(source='video.video_minutes', read_only=True)
    video_seconds = serializers.IntegerField(source='video.video_seconds', read_only=True)
    video_duration_formatted = serializers.SerializerMethodField()
    
    class Meta:
        model = UserVideoProgress
        fields = [
            'id', 'user', 'video', 'language', 'video_title', 'video_thumbnail_url', 
            'video_tag', 'video_minutes', 'video_seconds', 'video_duration_formatted', 'status', 'progress_percentage', 'last_watched_at', 
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_video_title(self, obj):
        """
        Get localized video title based on progress language
        """
        return obj.video.get_localized_title(obj.language)
    
    def get_video_thumbnail_url(self, obj):
        """
        Get localized video thumbnail URL based on progress language
        """
        request = self.context.get('request')
        return obj.video.get_localized_thumbnail_url(obj.language, request)
    
    def get_video_duration_formatted(self, obj):
        """
        Get video duration in formatted string
        """
        return f"{obj.video.video_minutes}m {obj.video.video_seconds}s"

    def validate_progress_percentage(self, value):
        """
        Validate that progress percentage is between 0 and 100
        """
        if value < 0 or value > 100:
            raise serializers.ValidationError("Progress percentage must be between 0 and 100.")
        return value


class VideoWithProgressSerializer(serializers.ModelSerializer):
    """
    Serializer for Video model that includes user progress information for specific language
    """
    user_progress = serializers.SerializerMethodField()
    localized_title = serializers.SerializerMethodField()
    localized_description = serializers.SerializerMethodField()
    localized_video_file_url = serializers.SerializerMethodField()
    localized_thumbnail_url = serializers.SerializerMethodField()
    available_languages = serializers.SerializerMethodField()
    duration_formatted = serializers.SerializerMethodField()
    
    class Meta:
        model = Video
        fields = [
            'id', 'localized_title', 'localized_description', 'localized_video_file_url',
            'localized_thumbnail_url', 'tag', 'video_minutes', 'video_seconds', 'duration_formatted', 'available_languages', 
            'created_at', 'updated_at', 'user_progress'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'localized_title', 'localized_description', 'localized_video_file_url', 'localized_thumbnail_url', 'available_languages']

    def get_available_languages(self, obj):
        """
        Get list of available languages for this video
        """
        return obj.get_available_languages()
    
    def get_localized_title(self, obj):
        """
        Get title in the requested language
        """
        request = self.context.get('request')
        language = 'persian'  # Default language
        if request:
            language = request.query_params.get('lang') or request.query_params.get('language') or 'persian'
        return obj.get_localized_title(language)
    
    def get_localized_description(self, obj):
        """
        Get description in the requested language
        """
        request = self.context.get('request')
        language = 'persian'  # Default language
        if request:
            language = request.query_params.get('lang') or request.query_params.get('language') or 'persian'
        return obj.get_localized_description(language)
    
    def get_localized_video_file_url(self, obj):
        """
        Get video file URL in the requested language
        """
        request = self.context.get('request')
        language = 'persian'  # Default language
        if request:
            language = request.query_params.get('lang') or request.query_params.get('language') or 'persian'
        return obj.get_localized_video_file_url(language, request)

    def get_localized_thumbnail_url(self, obj):
        """
        Get thumbnail URL in the requested language
        """
        request = self.context.get('request')
        language = 'persian'  # Default language
        if request:
            language = request.query_params.get('lang') or request.query_params.get('language') or 'persian'
        return obj.get_localized_thumbnail_url(language, request)
    
    def get_duration_formatted(self, obj):
        """
        Get duration in formatted string (e.g., "5m 30s")
        """
        return f"{obj.video_minutes}m {obj.video_seconds}s"

    def get_user_progress(self, obj):
        """
        Get user progress for the current video in the requested language
        """
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            # Get language from request parameter, default to persian
            language = request.query_params.get('lang') or request.query_params.get('language') or 'persian'
            
            try:
                progress = UserVideoProgress.objects.get(user=request.user, video=obj, language=language)
                return {
                    'language': progress.language,
                    'status': progress.status,
                    'progress_percentage': progress.progress_percentage,
                    'last_watched_at': progress.last_watched_at
                }
            except UserVideoProgress.DoesNotExist:
                return {
                    'language': language,
                    'status': 'not_started',
                    'progress_percentage': 0.00,
                    'last_watched_at': None
                }
        return None


class UpdateProgressSerializer(serializers.Serializer):
    """
    Serializer for updating video progress with language support
    """
    progress_percentage = serializers.DecimalField(max_digits=5, decimal_places=2, min_value=0, max_value=100)
    language = serializers.ChoiceField(choices=Video.LANGUAGE_CHOICES, required=False, default='persian')
    
    def validate_progress_percentage(self, value):
        """
        Validate that progress percentage is between 0 and 100
        """
        if value < 0 or value > 100:
            raise serializers.ValidationError("Progress percentage must be between 0 and 100.")
        return value