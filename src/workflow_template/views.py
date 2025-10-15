from rest_framework import generics, status, filters
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q, Count
from django.utils import timezone

from .models import Language, Type, Tag, Template
from .serializers import LanguageSerializer, TypeSerializer, TagSerializer, TemplateSerializer, TemplateListSerializer
from .filters import TemplateFilter, LanguageFilter, TypeFilter, TagFilter


class CustomPagination(PageNumberPagination):
    """
    Custom pagination class for workflow template APIs
    """
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 500


class LanguageListAPIView(generics.ListAPIView):
    """
    API endpoint to list all active languages with search, filtering, and pagination
    
    Query Parameters:
    - search: Search in language names
    - name__icontains: Filter by language name (case-insensitive)
    - is_active: Filter by active status (true/false)
    - ordering: Sort by fields (name, -name, created_at, -created_at)
    - page: Page number for pagination
    - page_size: Number of items per page (default: 10, max: 500)
    """
    queryset = Language.objects.filter(is_active=True)
    serializer_class = LanguageSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = CustomPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = LanguageFilter
    search_fields = ['name']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']


class TypeListAPIView(generics.ListAPIView):
    """
    API endpoint to list all active types with search, filtering, and pagination
    
    Query Parameters:
    - search: Search in type names and descriptions
    - name__icontains: Filter by type name (case-insensitive)
    - description__icontains: Filter by description (case-insensitive)
    - is_active: Filter by active status (true/false)
    - ordering: Sort by fields (name, -name, created_at, -created_at)
    - page: Page number for pagination
    - page_size: Number of items per page (default: 10, max: 500)
    """
    queryset = Type.objects.filter(is_active=True)
    serializer_class = TypeSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = CustomPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = TypeFilter
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']


class TagListAPIView(generics.ListAPIView):
    """
    API endpoint to list all active tags with search, filtering, and pagination
    
    Query Parameters:
    - search: Search in tag names and descriptions
    - name__icontains: Filter by tag name (case-insensitive)
    - description__icontains: Filter by description (case-insensitive)
    - is_active: Filter by active status (true/false)
    - ordering: Sort by fields (name, -name, created_at, -created_at)
    - page: Page number for pagination
    - page_size: Number of items per page (default: 10, max: 500)
    """
    queryset = Tag.objects.filter(is_active=True)
    serializer_class = TagSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = CustomPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = TagFilter
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']


class TemplateListAPIView(generics.ListCreateAPIView):
    """
    API endpoint to list and create workflow templates with comprehensive filtering, search, and pagination
    
    Query Parameters:
    - search: Multi-field search in template names and descriptions
    - name__icontains: Filter by template name (case-insensitive)
    - description__icontains: Filter by description (case-insensitive)
    - language: Filter by language UUID
    - language_name: Filter by language name (case-insensitive)
    - type: Filter by type UUID
    - type_name: Filter by type name (case-insensitive)
    - tag: Filter by tag UUID
    - tag_name: Filter by tag name (case-insensitive)
    - status: Filter by template status (new, popular, none)
    - is_active: Filter by active status (true/false)
    - created_at__gte: Filter templates created on or after this date (ISO format)
    - created_at__lte: Filter templates created on or before this date (ISO format)
    - updated_at__gte: Filter templates updated on or after this date (ISO format)
    - updated_at__lte: Filter templates updated on or before this date (ISO format)
    - ordering: Sort by fields (name, -name, created_at, -created_at, updated_at, -updated_at)
    - page: Page number for pagination
    - page_size: Number of items per page (default: 10, max: 500)
    
    Examples:
    1. Search and filter:
       GET /api/workflow-template/templates/?search=workflow&status=popular&language_name=english&ordering=-created_at&page=1&page_size=20
    
    2. Date range:
       GET /api/workflow-template/templates/?created_at__gte=2024-01-01&created_at__lte=2024-12-31
    
    3. Multiple filters:
       GET /api/workflow-template/templates/?language_name=english&type_name=automation&is_active=true
    """
    queryset = Template.objects.select_related('language', 'type', 'tag').all()
    serializer_class = TemplateSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = CustomPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = TemplateFilter
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at', 'updated_at']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        if self.request.method == 'GET':
            return TemplateListSerializer
        return TemplateSerializer


class TemplateDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    """
    API endpoint to retrieve, update, or delete a specific workflow template
    """
    queryset = Template.objects.select_related('language', 'type', 'tag')
    serializer_class = TemplateSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'id'




@api_view(['GET'])
@permission_classes([IsAuthenticated])
def template_statistics(request):
    """
    API endpoint to get template statistics
    """
    total_templates = Template.objects.count()
    active_templates = Template.objects.filter(is_active=True).count()
    
    # Templates by language
    language_stats = Template.objects.filter(is_active=True).values('language__name').annotate(
        count=Count('id')
    ).order_by('-count')
    
    # Templates by type
    type_stats = Template.objects.filter(is_active=True).values('type__name').annotate(
        count=Count('id')
    ).order_by('-count')
    
    return Response({
        'total_templates': total_templates,
        'active_templates': active_templates,
        'language_distribution': list(language_stats),
        'type_distribution': list(type_stats)
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def recent_templates(request):
    """
    API endpoint to get recent templates with pagination
    
    Query Parameters:
    - page: Page number for pagination
    - page_size: Number of items per page (default: 10, max: 500)
    - limit: Maximum number of results to return (overrides pagination)
    
    Example:
    GET /api/workflow-template/templates/recent/?page=1&page_size=20
    """
    limit = request.query_params.get('limit')
    
    queryset = Template.objects.filter(
        is_active=True
    ).select_related('language', 'type', 'tag').order_by('-created_at')
    
    # If limit is specified, return that many results without pagination
    if limit:
        try:
            limit = int(limit)
            queryset = queryset[:limit]
            serializer = TemplateListSerializer(queryset, many=True)
            return Response(serializer.data)
        except ValueError:
            pass
    
    # Otherwise use pagination
    paginator = CustomPagination()
    paginated_queryset = paginator.paginate_queryset(queryset, request)
    serializer = TemplateListSerializer(paginated_queryset, many=True)
    return paginator.get_paginated_response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def search_templates(request):
    """
    API endpoint for advanced template search with pagination
    
    Query Parameters:
    - q: Search query (searches in name and description)
    - language: Filter by language name (case-insensitive)
    - type: Filter by type name (case-insensitive)
    - tag: Filter by tag name (case-insensitive)
    - status: Filter by template status (new, popular, none)
    - is_active: Filter by active status (true/false, default: true)
    - ordering: Sort by fields (name, -name, created_at, -created_at)
    - page: Page number for pagination
    - page_size: Number of items per page (default: 10, max: 500)
    
    Example:
    GET /api/workflow-template/templates/search/?q=automation&language=english&status=popular&page=1
    """
    query = request.query_params.get('q', '')
    language = request.query_params.get('language')
    type_filter = request.query_params.get('type')
    tag_filter = request.query_params.get('tag')
    status_filter = request.query_params.get('status')
    is_active = request.query_params.get('is_active', 'true').lower() == 'true'
    ordering = request.query_params.get('ordering', '-created_at')
    
    queryset = Template.objects.filter(is_active=is_active).select_related('language', 'type', 'tag')
    
    # Text search
    if query:
        queryset = queryset.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query)
        )
    
    # Language filter
    if language:
        queryset = queryset.filter(language__name__icontains=language)
    
    # Type filter
    if type_filter:
        queryset = queryset.filter(type__name__icontains=type_filter)
    
    # Tag filter
    if tag_filter:
        queryset = queryset.filter(tag__name__icontains=tag_filter)
    
    # Status filter
    if status_filter:
        queryset = queryset.filter(status=status_filter)
    
    # Apply ordering
    valid_ordering_fields = ['name', '-name', 'created_at', '-created_at', 'updated_at', '-updated_at']
    if ordering in valid_ordering_fields:
        queryset = queryset.order_by(ordering)
    else:
        queryset = queryset.order_by('-created_at')
    
    # Apply pagination
    paginator = CustomPagination()
    paginated_queryset = paginator.paginate_queryset(queryset, request)
    serializer = TemplateListSerializer(paginated_queryset, many=True)
    return paginator.get_paginated_response(serializer.data)