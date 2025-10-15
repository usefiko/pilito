"""
URL configuration for web_knowledge app
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    WebsiteSourceViewSet,
    WebsitePageViewSet,
    QAPairViewSet,
    QASearchAPIView,
    ManualQAGenerationAPIView,
    EnhancedQAGenerationAPIView,
    PartialQACreateAPIView,
    ProductViewSet,
    PageSummaryUpdateAPIView,
    GeneratePromptAPIView,
    GeneratePromptAsyncAPIView,
    GeneratePromptStatusAPIView,
)

router = DefaultRouter()
router.register(r'websites', WebsiteSourceViewSet, basename='website-source')
router.register(r'pages', WebsitePageViewSet, basename='website-page')
router.register(r'qa-pairs', QAPairViewSet, basename='qa-pair')
router.register(r'products', ProductViewSet, basename='product')

app_name = 'web_knowledge'

urlpatterns = [
    # Custom API endpoints (these must come before router URLs to avoid conflicts)
    path('search/', QASearchAPIView.as_view(), name='qa-search'),
    path('manual-qa-generation/', ManualQAGenerationAPIView.as_view(), name='manual-qa-generation'),
    path('generate-enhanced-qa/', EnhancedQAGenerationAPIView.as_view(), name='enhanced-qa-generation'),
    path('qa-pairs/create/', PartialQACreateAPIView.as_view(), name='partial-qa-create'),
    path('pages/update-summary/', PageSummaryUpdateAPIView.as_view(), name='page-summary-update'),
    
    # Prompt Generation - Sync and Async
    path('generate-prompt/', GeneratePromptAPIView.as_view(), name='generate-prompt'),  # Synchronous (legacy)
    path('generate-prompt-async/', GeneratePromptAsyncAPIView.as_view(), name='generate-prompt-async'),  # Async (recommended)
    path('generate-prompt-async/status/<str:task_id>/', GeneratePromptStatusAPIView.as_view(), name='generate-prompt-status'),  # Status check
    
    # Router URLs (these come last to avoid catching specific endpoints)
    path('', include(router.urls)),
]
