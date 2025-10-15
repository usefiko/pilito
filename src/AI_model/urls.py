from django.urls import path
from . import views

app_name = 'AI_model'

urlpatterns = [
    # Question & Answer API
    path('ask/', views.AskQuestionAPIView.as_view(), name='ask_question'),
    
    # AI Configuration
    path('config/', views.AIGlobalConfigAPIView.as_view(), name='ai_global_config'),
    path('config/status/', views.AIConfigurationStatusAPIView.as_view(), name='ai_config_status'),
    
    # Conversation Status Management
    path('conversations/<str:conversation_id>/status/', views.ConversationStatusAPIView.as_view(), name='conversation_status'),
    path('conversations/bulk-status/', views.BulkConversationStatusAPIView.as_view(), name='bulk_conversation_status'),
    
    # User Default Handler
    path('default-handler/', views.UserDefaultHandlerAPIView.as_view(), name='user_default_handler'),
    
    # Usage Statistics (Legacy - Daily Aggregates)
    path('usage/stats/', views.AIUsageStatsAPIView.as_view(), name='usage_stats'),
    path('usage/global/', views.GlobalUsageStatsAPIView.as_view(), name='global_usage_stats'),
    
    # AI Usage Log - Detailed Per-Request Tracking
    path('usage/logs/', views.AIUsageLogAPIView.as_view(), name='usage_logs'),
    path('usage/logs/stats/', views.AIUsageLogStatsAPIView.as_view(), name='usage_log_stats'),
    path('usage/logs/global/', views.GlobalAIUsageLogStatsAPIView.as_view(), name='global_usage_log_stats'),
    
    # RAG System Status
    path('rag/status/', views.RAGStatusAPIView.as_view(), name='rag_status'),
    
    # Process AI Response (Debug)
    path('process-response/<str:message_id>/', views.ProcessAIResponseAPIView.as_view(), name='process_ai_response'),
]