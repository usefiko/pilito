from django.urls import path
from . import views

app_name = 'academy'

urlpatterns = [
    # Video endpoints with filtering and search
    path('videos/', views.VideoListView.as_view(), name='video-list'),
    path('videos/<int:pk>/', views.VideoDetailView.as_view(), name='video-detail'),
    path('videos/by-status/', views.videos_by_status, name='videos-by-status'),
    path('videos/all-details/', views.AllVideoDetailsAPIView.as_view(), name='all-video-details'),
    # Video file endpoints
    path('videos/<int:video_id>/stream/', views.stream_video, name='stream-video'),
    path('videos/<int:video_id>/download/', views.download_video, name='download-video'),
    # User progress endpoints with filtering and search
    path('progress/', views.UserProgressListView.as_view(), name='user-progress-list'),
    path('videos/<int:video_id>/progress/', views.user_video_progress, name='user-video-progress'),
    path('videos/<int:video_id>/update-progress/', views.update_video_progress, name='update-video-progress'),
    # User statistics with filtering
    path('statistics/', views.user_statistics, name='user-statistics'),
]