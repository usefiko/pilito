from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from rest_framework.pagination import PageNumberPagination
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.http import HttpResponse, Http404, FileResponse
from django.views.decorators.http import require_GET
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Case, When, Value, CharField
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from django.http import HttpResponseRedirect
from django.urls import reverse
import os
from .models import Video, UserVideoProgress
from .serializers import (
    VideoSerializer, 
    UserVideoProgressSerializer, 
    VideoWithProgressSerializer,
    UpdateProgressSerializer
)


class CustomPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 500


class VideoListView(generics.ListAPIView):
    """
    List all videos with user progress information, with comprehensive filtering and search
    
    Query Parameters:
    - lang/language: Language filter (persian, arabic, english, turkish)
    - status: Progress status filter (not_started, in_progress, complete)
    - tag: Filter by video tag (case-insensitive)
    - search: Search in titles and descriptions across all languages
    - ordering: Sort by fields (created_at, -created_at, video_minutes, -video_minutes)
    """
    serializer_class = VideoWithProgressSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = CustomPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'description', 'title_persian', 'description_persian', 
                    'title_arabic', 'description_arabic', 'title_english', 'description_english',
                    'title_turkish', 'description_turkish', 'tag']
    ordering_fields = ['created_at', 'video_minutes', 'updated_at']
    ordering = ['-created_at']

    def get_queryset(self):
        """
        Filter videos by tag, language availability, and user progress status
        """
        queryset = Video.objects.all()
        user = self.request.user
        
        # Filter by tag
        tag = self.request.query_params.get('tag')
        if tag:
            queryset = queryset.filter(tag__icontains=tag)
        
        # Filter by language availability
        language = self.request.query_params.get('lang') or self.request.query_params.get('language')
        if language and language in ['persian', 'arabic', 'english', 'turkish']:
            # Filter videos that have content in the specified language
            title_field = f'title_{language}'
            video_field = f'video_file_{language}'
            
            language_filter = Q(**{f'{title_field}__isnull': False}) & Q(**{f'{title_field}__gt': ''})
            language_filter |= Q(**{f'{video_field}__isnull': False})
            
            queryset = queryset.filter(language_filter)
        
        # Filter by progress status
        status_filter = self.request.query_params.get('status')
        if status_filter and status_filter in ['not_started', 'in_progress', 'complete']:
            if status_filter == 'not_started':
                # Videos with no progress record or status = 'not_started'
                queryset = queryset.filter(
                    Q(user_progress__user=user, user_progress__status='not_started') |
                    Q(user_progress__isnull=True)
                ).distinct()
            else:
                # Videos with specific progress status
                queryset = queryset.filter(
                    user_progress__user=user,
                    user_progress__status=status_filter
                ).distinct()
        
        return queryset


class VideoDetailView(generics.RetrieveAPIView):
    """
    Retrieve a specific video with user progress information
    """
    queryset = Video.objects.all()
    serializer_class = VideoWithProgressSerializer
    permission_classes = [IsAuthenticated]


class UserProgressListView(generics.ListAPIView):
    """
    List user's progress for all videos with comprehensive filtering and search
    
    Query Parameters:
    - lang/language: Language filter (persian, arabic, english, turkish)
    - status: Progress status filter (not_started, in_progress, complete)
    - search: Search in video titles, descriptions, and tags
    - tag: Filter by video tag (case-insensitive)
    - ordering: Sort by fields (updated_at, progress_percentage, last_watched_at)
    """
    serializer_class = UserVideoProgressSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = CustomPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['video__title', 'video__description', 'video__tag',
                    'video__title_persian', 'video__description_persian',
                    'video__title_arabic', 'video__description_arabic', 
                    'video__title_english', 'video__description_english',
                    'video__title_turkish', 'video__description_turkish']
    ordering_fields = ['updated_at', 'progress_percentage', 'last_watched_at', 'created_at']
    ordering = ['-updated_at']

    def get_queryset(self):
        """
        Return progress for the current user with comprehensive filtering
        """
        queryset = UserVideoProgress.objects.filter(user=self.request.user).select_related('video')
        
        # Filter by language
        language = self.request.query_params.get('lang') or self.request.query_params.get('language')
        if language and language in ['persian', 'arabic', 'english', 'turkish']:
            queryset = queryset.filter(language=language)
        
        # Filter by status
        status_filter = self.request.query_params.get('status')
        if status_filter and status_filter in ['not_started', 'in_progress', 'complete']:
            queryset = queryset.filter(status=status_filter)
        
        # Filter by video tag
        tag = self.request.query_params.get('tag')
        if tag:
            queryset = queryset.filter(video__tag__icontains=tag)
            
        return queryset


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def update_video_progress(request, video_id):
    """
    Update user's progress for a specific video in a specific language
    """
    video = get_object_or_404(Video, id=video_id)
    serializer = UpdateProgressSerializer(data=request.data)
    
    if serializer.is_valid():
        progress_percentage = serializer.validated_data['progress_percentage']
        language = serializer.validated_data.get('language', 'persian')
        
        # Get or create user progress record for specific language
        progress, created = UserVideoProgress.objects.get_or_create(
            user=request.user,
            video=video,
            language=language,
            defaults={'progress_percentage': progress_percentage}
        )
        
        if not created:
            progress.progress_percentage = progress_percentage
        
        progress.last_watched_at = timezone.now()
        progress.save()  # This will auto-update the status based on progress_percentage
        
        return Response({
            'message': 'Progress updated successfully',
            'language': progress.language,
            'status': progress.status,
            'progress_percentage': progress.progress_percentage,
            'last_watched_at': progress.last_watched_at
        }, status=status.HTTP_200_OK)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_video_progress(request, video_id):
    """
    Get user's progress for a specific video in a specific language
    """
    video = get_object_or_404(Video, id=video_id)
    language = request.query_params.get('lang') or request.query_params.get('language') or 'persian'
    
    try:
        progress = UserVideoProgress.objects.get(user=request.user, video=video, language=language)
        serializer = UserVideoProgressSerializer(progress)
        return Response(serializer.data, status=status.HTTP_200_OK)
    except UserVideoProgress.DoesNotExist:
        return Response({
            'status': 'not_started',
            'progress_percentage': 0.00,
            'last_watched_at': None,
            'language': language,
            'video': video_id,
            'user': request.user.id
        }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_statistics(request):
    """
    Get user's overall learning statistics with comprehensive filtering
    
    Query Parameters:
    - lang/language: Language filter (persian, arabic, english, turkish)
    - tag: Filter by video tag (case-insensitive)
    """
    language = request.query_params.get('lang') or request.query_params.get('language')
    tag = request.query_params.get('tag')
    
    # Filter user progress by language if specified
    user_progress = UserVideoProgress.objects.filter(user=request.user)
    total_videos_query = Video.objects.all()
    
    if language:
        user_progress = user_progress.filter(language=language)
        # Filter videos that have content in the specified language
        title_field = f'title_{language}'
        video_field = f'video_file_{language}'
        
        language_filter = Q(**{f'{title_field}__isnull': False}) & Q(**{f'{title_field}__gt': ''})
        language_filter |= Q(**{f'{video_field}__isnull': False})
        
        total_videos_query = total_videos_query.filter(language_filter)
    
    if tag:
        user_progress = user_progress.filter(video__tag__icontains=tag)
        total_videos_query = total_videos_query.filter(tag__icontains=tag)
    
    total_videos = total_videos_query.count()
    completed_videos = user_progress.filter(status='complete').count()
    in_progress_videos = user_progress.filter(status='in_progress').count()
    
    # Calculate not started videos more accurately
    # For videos that have progress, count those with not_started status
    # For videos without progress records, they are also not_started
    videos_with_progress = user_progress.values_list('video_id', flat=True).distinct()
    total_video_ids = set(total_videos_query.values_list('id', flat=True))
    videos_without_progress = total_video_ids - set(videos_with_progress)
    not_started_with_progress = user_progress.filter(status='not_started').count()
    not_started_videos = len(videos_without_progress) + not_started_with_progress
    
    total_minutes_completed = 0
    total_seconds_completed = 0
    for progress in user_progress.filter(status='complete').select_related('video'):
        total_minutes_completed += progress.video.video_minutes
        total_seconds_completed += progress.video.video_seconds
    
    # Convert excess seconds to minutes
    total_minutes_completed += total_seconds_completed // 60
    total_seconds_completed = total_seconds_completed % 60
    
    # Calculate total available duration
    total_minutes_available = 0
    total_seconds_available = 0
    for video in total_videos_query:
        total_minutes_available += video.video_minutes
        total_seconds_available += video.video_seconds
    
    # Convert excess seconds to minutes
    total_minutes_available += total_seconds_available // 60
    total_seconds_available = total_seconds_available % 60
    
    # Convert to total seconds for percentage calculation
    total_duration_completed_seconds = total_minutes_completed * 60 + total_seconds_completed
    total_duration_available_seconds = total_minutes_available * 60 + total_seconds_available
    
    statistics = {
        'total_videos': total_videos,
        'completed_videos': completed_videos,
        'in_progress_videos': in_progress_videos,
        'not_started_videos': not_started_videos,
        'total_minutes_completed': total_minutes_completed,
        'total_seconds_completed': total_seconds_completed,
        'total_duration_completed': f"{total_minutes_completed}m {total_seconds_completed}s",
        'total_minutes_available': total_minutes_available,
        'total_seconds_available': total_seconds_available,
        'total_duration_available': f"{total_minutes_available}m {total_seconds_available}s",
        'completion_percentage': round((completed_videos / total_videos * 100), 2) if total_videos > 0 else 0,
        'duration_completion_percentage': round((total_duration_completed_seconds / total_duration_available_seconds * 100), 2) if total_duration_available_seconds > 0 else 0
    }
    
    # Add filter information to response
    if language:
        statistics['language'] = language
    if tag:
        statistics['tag'] = tag
    
    return Response(statistics, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def videos_by_status(request):
    """
    Get videos filtered by progress status for the current user
    
    Query Parameters (Required):
    - status: Progress status (not_started, in_progress, complete)
    - lang/language: Language filter (persian, arabic, english, turkish) - optional
    - search: Search in titles and descriptions - optional
    - tag: Filter by video tag - optional
    - page: Page number for pagination - optional
    """
    status_filter = request.query_params.get('status')
    if not status_filter or status_filter not in ['not_started', 'in_progress', 'complete']:
        return Response({
            'error': 'Status parameter is required and must be one of: not_started, in_progress, complete'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    language = request.query_params.get('lang') or request.query_params.get('language') or 'persian'
    search = request.query_params.get('search', '')
    tag = request.query_params.get('tag', '')
    
    user = request.user
    queryset = Video.objects.all()
    
    # Apply search filter
    if search:
        search_filter = (
            Q(title__icontains=search) |
            Q(description__icontains=search) |
            Q(title_persian__icontains=search) |
            Q(description_persian__icontains=search) |
            Q(title_arabic__icontains=search) |
            Q(description_arabic__icontains=search) |
            Q(title_english__icontains=search) |
            Q(description_english__icontains=search) |
            Q(title_turkish__icontains=search) |
            Q(description_turkish__icontains=search) |
            Q(tag__icontains=search)
        )
        queryset = queryset.filter(search_filter)
    
    # Apply tag filter
    if tag:
        queryset = queryset.filter(tag__icontains=tag)
    
    # Filter by progress status
    if status_filter == 'not_started':
        # Videos with no progress record or status = 'not_started'
        queryset = queryset.filter(
            Q(user_progress__user=user, user_progress__language=language, user_progress__status='not_started') |
            Q(user_progress__isnull=True)
        ).distinct()
    else:
        # Videos with specific progress status
        queryset = queryset.filter(
            user_progress__user=user,
            user_progress__language=language,
            user_progress__status=status_filter
        ).distinct()
    
    # Apply pagination
    paginator = CustomPagination()
    paginated_queryset = paginator.paginate_queryset(queryset, request)
    
    # Serialize the data
    serializer = VideoWithProgressSerializer(
        paginated_queryset, 
        many=True, 
        context={'request': request}
    )
    
    return paginator.get_paginated_response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def stream_video(request, video_id):
    """
    Stream video file with range support for better video playback in requested language
    """
    video = get_object_or_404(Video, id=video_id)
    language = request.query_params.get('lang') or request.query_params.get('language') or 'persian'
    
    # Get localized video file
    video_file = video.get_localized_video_file(language)
    
    if not video_file:
        return Response({
            'error': 'Video file not found for the requested language'
        }, status=status.HTTP_404_NOT_FOUND)
    
    # Check if file exists in storage
    if not video_file.storage.exists(video_file.name):
        return Response({
            'error': 'Video file not found on server'
        }, status=status.HTTP_404_NOT_FOUND)
    
    try:
        # For S3 storage, generate a pre-signed URL and redirect
        if hasattr(video_file.storage, 'bucket_name'):  # S3 storage
            # Generate pre-signed URL for direct access
            signed_url = video_file.storage.url(video_file.name)
            return HttpResponseRedirect(signed_url)
        else:
            # For local storage, use FileResponse
            response = FileResponse(
                open(video_file.path, 'rb'),
                content_type='video/mp4'
            )
            
            # Set headers for video streaming
            response['Accept-Ranges'] = 'bytes'
            response['Content-Length'] = os.path.getsize(video_file.path)
            
            # Use localized title for filename
            localized_title = video.get_localized_title(language)
            response['Content-Disposition'] = f'inline; filename="{localized_title}.mp4"'
            
            return response
            
    except Exception as e:
        return Response({
            'error': f'Error accessing video file: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def download_video(request, video_id):
    """
    Download video file in requested language
    """
    video = get_object_or_404(Video, id=video_id)
    language = request.query_params.get('lang') or request.query_params.get('language') or 'persian'
    
    # Get localized video file
    video_file = video.get_localized_video_file(language)
    
    if not video_file:
        return Response({
            'error': 'Video file not found for the requested language'
        }, status=status.HTTP_404_NOT_FOUND)
    
    # Check if file exists in storage
    if not video_file.storage.exists(video_file.name):
        return Response({
            'error': 'Video file not found on server'
        }, status=status.HTTP_404_NOT_FOUND)
    
    # Use localized title for filename
    localized_title = video.get_localized_title(language)
    file_extension = video_file.name.split('.')[-1]
    
    try:
        # For S3 storage, generate a pre-signed URL with download headers
        if hasattr(video_file.storage, 'bucket_name'):  # S3 storage
            # Generate pre-signed URL for download
            signed_url = video_file.storage.url(video_file.name)
            # For S3, we redirect to the signed URL
            # The browser will handle the download based on Content-Disposition header set by S3
            return HttpResponseRedirect(signed_url)
        else:
            # For local storage, use FileResponse
            response = FileResponse(
                open(video_file.path, 'rb'),
                as_attachment=True,
                filename=f"{localized_title}.{file_extension}"
            )
            return response
            
    except Exception as e:
        return Response({
            'error': f'Error accessing video file: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AllVideoDetailsAPIView(APIView):
    """
    API to get all video details without pagination
    Returns comprehensive information about all videos including multi-language support
    """
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Get all video details with complete information",
        manual_parameters=[
            openapi.Parameter(
                'lang',
                openapi.IN_QUERY,
                description="Language for localized content (persian, arabic, english, turkish)",
                type=openapi.TYPE_STRING,
                enum=['persian', 'arabic', 'english', 'turkish'],
                default='persian'
            ),
            openapi.Parameter(
                'include_progress',
                openapi.IN_QUERY,
                description="Include user progress information",
                type=openapi.TYPE_BOOLEAN,
                default=True
            )
        ],
        responses={
            200: openapi.Response(
                description="Complete list of video details",
                examples={
                    "application/json": {
                        "total_count": 1,
                        "results": [
                            {
                                "id": 1,
                                "localized_title": "Introduction to Python",
                                "localized_description": "Learn the basics of Python programming",
                                "localized_video_file_url": "https://example.com/video1.mp4",
                                "localized_thumbnail_url": "https://example.com/thumb1.jpg",
                                "tag": "programming",
                                "video_minutes": 45,
                                "video_seconds": 30,
                                "duration_formatted": "45m 30s",
                                "available_languages": ["persian", "english"],
                                "created_at": "2024-01-01T00:00:00Z",
                                "updated_at": "2024-01-01T00:00:00Z",
                                "user_progress": {
                                    "language": "persian",
                                    "status": "in_progress",
                                    "progress_percentage": 75.50,
                                    "last_watched_at": "2024-01-01T12:00:00Z"
                                }
                            }
                        ]
                    }
                }
            )
        }
    )
    def get(self, request):
        """Get all video details with optional user progress"""
        try:
            # Get all videos
            videos = Video.objects.all().order_by('-created_at')
            
            # Check if user wants progress information included
            include_progress = request.query_params.get('include_progress', 'true').lower() == 'true'
            
            # Use appropriate serializer based on progress requirement
            if include_progress:
                serializer = VideoWithProgressSerializer(
                    videos, 
                    many=True, 
                    context={'request': request}
                )
            else:
                serializer = VideoSerializer(
                    videos, 
                    many=True, 
                    context={'request': request}
                )
            
            return Response({
                'total_count': videos.count(),
                'results': serializer.data
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'error': f'Failed to get video details: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)