import logging
from typing import Dict, Any, List, Optional
from django.db.models import QuerySet

logger = logging.getLogger(__name__)


class WebSocketPagination:
    """
    WebSocket pagination utility class that mimics DRF's CustomPagination
    for consistent pagination across WebSocket consumers.
    
    Similar to CustomPagination(PageNumberPagination):
    - page_size = 10 (default)
    - page_size_query_param = 'page_size'
    - max_page_size = 500
    
    But adapted for WebSocket filter parameters using limit/offset pattern.
    """
    
    default_page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 500
    
    def __init__(self, filters: Optional[Dict[str, Any]] = None):
        """
        Initialize pagination with filters from WebSocket message
        
        Args:
            filters: Dictionary containing pagination parameters:
                - page_size: Number of items per page (default: 10)
                - page: Page number (1-based, default: 1)
                - limit: Alternative to page_size (for backward compatibility)
                - offset: Alternative to page-based pagination
        """
        self.filters = filters or {}
        logger.debug(f"WebSocketPagination initialized with filters: {self.filters}")
        self.page_size = self._get_page_size()
        self.page = self._get_page()
        self.offset = self._get_offset()
        logger.debug(f"WebSocketPagination calculated: page_size={self.page_size}, page={self.page}, offset={self.offset}")
        
    def _get_page_size(self) -> int:
        """Get page size from filters with validation"""
        # Check for page_size parameter first (preferred)
        page_size = self.filters.get(self.page_size_query_param)
        
        # Fallback to limit parameter for backward compatibility
        if page_size is None:
            page_size = self.filters.get('limit')
            
        # Use default if not specified
        if page_size is None:
            return self.default_page_size
            
        try:
            page_size = int(page_size)
            # Ensure page_size is within valid bounds
            if page_size <= 0:
                return self.default_page_size
            if page_size > self.max_page_size:
                return self.max_page_size
            return page_size
        except (ValueError, TypeError):
            logger.warning(f"Invalid page_size value: {page_size}, using default")
            return self.default_page_size
    
    def _get_page(self) -> int:
        """Get page number from filters with validation"""
        page = self.filters.get('page', 1)
        try:
            page = int(page)
            return max(1, page)  # Ensure page is at least 1
        except (ValueError, TypeError):
            logger.warning(f"Invalid page value: {page}, using default")
            return 1
    
    def _get_offset(self) -> int:
        """Calculate offset from page number or use direct offset"""
        # Check if offset is directly specified (for backward compatibility)
        direct_offset = self.filters.get('offset')
        if direct_offset is not None:
            try:
                return max(0, int(direct_offset))
            except (ValueError, TypeError):
                logger.warning(f"Invalid offset value: {direct_offset}, calculating from page")
        
        # Calculate offset from page number
        return (self.page - 1) * self.page_size
    
    def paginate_queryset(self, queryset: QuerySet) -> QuerySet:
        """
        Apply pagination to a Django QuerySet
        
        Args:
            queryset: Django QuerySet to paginate
            
        Returns:
            Paginated QuerySet
        """
        return queryset[self.offset:self.offset + self.page_size]
    
    def get_pagination_metadata(self, total_count: int, paginated_count: int) -> Dict[str, Any]:
        """
        Generate pagination metadata similar to DRF's paginated responses
        
        Args:
            total_count: Total number of items in the full queryset
            paginated_count: Number of items in the current page
            
        Returns:
            Dictionary containing pagination metadata
        """
        has_next = (self.offset + self.page_size) < total_count
        has_previous = self.offset > 0
        
        total_pages = (total_count + self.page_size - 1) // self.page_size if total_count > 0 else 1
        
        return {
            'count': total_count,
            'page_count': paginated_count,
            'page_size': self.page_size,
            'page': self.page,
            'total_pages': total_pages,
            'has_next': has_next,
            'has_previous': has_previous,
            'offset': self.offset,
            'limit': self.page_size,  # For backward compatibility
        }
    
    def paginate_data(self, queryset: QuerySet, serializer_class, **serializer_kwargs) -> Dict[str, Any]:
        """
        Complete pagination workflow: paginate queryset and return data with metadata
        
        Args:
            queryset: Django QuerySet to paginate
            serializer_class: Serializer class to use for data serialization
            **serializer_kwargs: Additional arguments for serializer
            
        Returns:
            Dictionary containing paginated data and metadata
        """
        # Get total count before pagination
        total_count = queryset.count()
        
        # Apply pagination
        paginated_queryset = self.paginate_queryset(queryset)
        
        # Serialize data
        serializer = serializer_class(paginated_queryset, many=True, **serializer_kwargs)
        serialized_data = serializer.data
        
        # Get pagination metadata
        pagination_metadata = self.get_pagination_metadata(total_count, len(serialized_data))
        
        return {
            'data': serialized_data,
            'pagination': pagination_metadata
        }


def create_websocket_paginator(filters: Optional[Dict[str, Any]] = None) -> WebSocketPagination:
    """
    Factory function to create WebSocketPagination instances
    
    Args:
        filters: WebSocket filters containing pagination parameters
        
    Returns:
        WebSocketPagination instance
    """
    return WebSocketPagination(filters)


# Backward compatibility functions for existing code
def get_websocket_pagination_params(filters: Optional[Dict[str, Any]] = None) -> Dict[str, int]:
    """
    Get pagination parameters in the old format for backward compatibility
    
    Returns:
        Dictionary with 'limit', 'offset', 'page', 'page_size'
    """
    paginator = WebSocketPagination(filters)
    return {
        'limit': paginator.page_size,
        'offset': paginator.offset,
        'page': paginator.page,
        'page_size': paginator.page_size
    }
