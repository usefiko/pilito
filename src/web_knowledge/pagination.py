"""
Custom pagination classes for web_knowledge app
"""
from rest_framework.pagination import PageNumberPagination


class WebsitesPagination(PageNumberPagination):
    """
    Pagination for websites list
    Allows frontend to control page_size via query parameter
    
    Usage:
    GET /api/v1/web-knowledge/websites/?page=1&page_size=50
    """
    page_size = 10  # Default page size
    page_size_query_param = 'page_size'  # Allow client to override (e.g. ?page_size=50)
    max_page_size = 100  # Maximum allowed page_size (prevents abuse)

