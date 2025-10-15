from django.urls import path
from . import views

app_name = 'workflow_template'

urlpatterns = [
    # Language endpoints
    path('languages/', views.LanguageListAPIView.as_view(), name='language-list'),
    
    # Type endpoints
    path('types/', views.TypeListAPIView.as_view(), name='type-list'),
    
    # Tag endpoints
    path('tags/', views.TagListAPIView.as_view(), name='tag-list'),
    
    # Template utility endpoints (must come before detail endpoint to avoid UUID matching)
    path('templates/recent/', views.recent_templates, name='recent-templates'),
    path('templates/search/', views.search_templates, name='search-templates'),
    path('templates/statistics/', views.template_statistics, name='template-statistics'),
    
    # Template endpoints
    path('templates/', views.TemplateListAPIView.as_view(), name='template-list'),
    path('templates/<uuid:id>/', views.TemplateDetailAPIView.as_view(), name='template-detail'),
]
