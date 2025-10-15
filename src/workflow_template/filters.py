import django_filters
from django.db.models import Q
from .models import Template, Language, Type, Tag


class TemplateFilter(django_filters.FilterSet):
    """
    Advanced filter for workflow templates with comprehensive filtering options
    
    Available filters:
    - name: Exact match on template name
    - name__icontains: Case-insensitive substring search in name
    - description__icontains: Case-insensitive substring search in description
    - language: Filter by language UUID
    - language_name: Filter by language name (case-insensitive)
    - type: Filter by type UUID
    - type_name: Filter by type name (case-insensitive)
    - tag: Filter by tag UUID
    - tag_name: Filter by tag name (case-insensitive)
    - status: Filter by template status (new, popular, none)
    - is_active: Filter by active status (true/false)
    - created_at__gte: Templates created on or after this date
    - created_at__lte: Templates created on or before this date
    - updated_at__gte: Templates updated on or after this date
    - updated_at__lte: Templates updated on or before this date
    """
    
    # Name filters
    name__icontains = django_filters.CharFilter(field_name='name', lookup_expr='icontains')
    description__icontains = django_filters.CharFilter(field_name='description', lookup_expr='icontains')
    
    # Language filters
    language_name = django_filters.CharFilter(field_name='language__name', lookup_expr='icontains')
    
    # Type filters
    type_name = django_filters.CharFilter(field_name='type__name', lookup_expr='icontains')
    
    # Tag filters
    tag_name = django_filters.CharFilter(field_name='tag__name', lookup_expr='icontains')
    
    # Date range filters
    created_at__gte = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='gte')
    created_at__lte = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='lte')
    updated_at__gte = django_filters.DateTimeFilter(field_name='updated_at', lookup_expr='gte')
    updated_at__lte = django_filters.DateTimeFilter(field_name='updated_at', lookup_expr='lte')
    
    # Search across multiple fields
    search = django_filters.CharFilter(method='filter_search', label='Search')
    
    class Meta:
        model = Template
        fields = {
            'language': ['exact'],
            'type': ['exact'],
            'tag': ['exact'],
            'status': ['exact'],
            'is_active': ['exact'],
        }
    
    def filter_search(self, queryset, name, value):
        """
        Custom search filter that searches across name and description
        """
        if value:
            return queryset.filter(
                Q(name__icontains=value) |
                Q(description__icontains=value)
            )
        return queryset


class LanguageFilter(django_filters.FilterSet):
    """
    Filter for languages
    """
    name__icontains = django_filters.CharFilter(field_name='name', lookup_expr='icontains')
    
    class Meta:
        model = Language
        fields = {
            'is_active': ['exact'],
        }


class TypeFilter(django_filters.FilterSet):
    """
    Filter for types
    """
    name__icontains = django_filters.CharFilter(field_name='name', lookup_expr='icontains')
    description__icontains = django_filters.CharFilter(field_name='description', lookup_expr='icontains')
    
    class Meta:
        model = Type
        fields = {
            'is_active': ['exact'],
        }


class TagFilter(django_filters.FilterSet):
    """
    Filter for tags
    """
    name__icontains = django_filters.CharFilter(field_name='name', lookup_expr='icontains')
    description__icontains = django_filters.CharFilter(field_name='description', lookup_expr='icontains')
    
    class Meta:
        model = Tag
        fields = {
            'is_active': ['exact'],
        }

