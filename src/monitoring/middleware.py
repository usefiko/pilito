"""
Prometheus monitoring middleware for Django
"""
import time
from django.utils.deprecation import MiddlewareMixin
from . import metrics


class PrometheusMetricsMiddleware(MiddlewareMixin):
    """
    Middleware to collect Prometheus metrics for HTTP requests
    """

    def process_request(self, request):
        """Start timing the request"""
        request._prometheus_start_time = time.time()
        return None

    def process_response(self, request, response):
        """Record metrics after response is ready"""
        if hasattr(request, '_prometheus_start_time'):
            # Calculate request duration
            duration = time.time() - request._prometheus_start_time

            # Get request details
            method = request.method
            status = response.status_code
            
            # Clean endpoint path (remove IDs for better aggregation)
            path = self._clean_path(request.path)

            # Record metrics
            metrics.http_requests_total.labels(
                method=method,
                endpoint=path,
                status=status
            ).inc()

            metrics.http_request_duration_seconds.labels(
                method=method,
                endpoint=path,
                status=status
            ).observe(duration)

            metrics.http_responses_by_status.labels(
                status=status,
                method=method
            ).inc()

            # Record request/response sizes
            # Use CONTENT_LENGTH from headers to avoid RawPostDataException
            request_size = int(request.META.get('CONTENT_LENGTH', 0) or 0)
            metrics.http_request_size_bytes.labels(
                method=method,
                endpoint=path
            ).observe(request_size)

            if hasattr(response, 'content'):
                response_size = len(response.content)
                metrics.http_response_size_bytes.labels(
                    method=method,
                    endpoint=path,
                    status=status
                ).observe(response_size)

        return response

    def process_exception(self, request, exception):
        """Record exception metrics"""
        if hasattr(request, '_prometheus_start_time'):
            duration = time.time() - request._prometheus_start_time
            path = self._clean_path(request.path)
            
            metrics.http_requests_total.labels(
                method=request.method,
                endpoint=path,
                status=500
            ).inc()

            metrics.http_request_duration_seconds.labels(
                method=request.method,
                endpoint=path,
                status=500
            ).observe(duration)

            metrics.http_responses_by_status.labels(
                status=500,
                method=request.method
            ).inc()

        return None

    @staticmethod
    def _clean_path(path):
        """
        Clean path to remove specific IDs and make it more aggregatable
        Examples:
            /api/v1/user/123 -> /api/v1/user/{id}
            /api/v1/workflow/abc-def-123 -> /api/v1/workflow/{id}
        """
        import re
        
        # Replace UUIDs
        path = re.sub(r'/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}', '/{id}', path, flags=re.IGNORECASE)
        
        # Replace numeric IDs
        path = re.sub(r'/\d+', '/{id}', path)
        
        # Replace mixed alphanumeric IDs (keep paths like /api/v1/...)
        path = re.sub(r'/[a-zA-Z0-9_-]{16,}', '/{id}', path)
        
        return path


class DatabaseMetricsMiddleware(MiddlewareMixin):
    """
    Middleware to track database query metrics
    """

    def process_request(self, request):
        """Track database queries at request start"""
        from django.db import connection
        request._db_queries_before = len(connection.queries)
        return None

    def process_response(self, request, response):
        """Record database query metrics"""
        if hasattr(request, '_db_queries_before'):
            from django.db import connection
            queries_count = len(connection.queries) - request._db_queries_before
            
            if queries_count > 0:
                for query in connection.queries[request._db_queries_before:]:
                    query_time = float(query.get('time', 0))
                    query_type = self._get_query_type(query['sql'])
                    
                    metrics.db_query_duration_seconds.labels(
                        query_type=query_type
                    ).observe(query_time)
                    
                    metrics.db_queries_total.labels(
                        query_type=query_type,
                        status='success'
                    ).inc()

        return response

    @staticmethod
    def _get_query_type(sql):
        """Extract query type from SQL"""
        sql_upper = sql.upper().strip()
        if sql_upper.startswith('SELECT'):
            return 'SELECT'
        elif sql_upper.startswith('INSERT'):
            return 'INSERT'
        elif sql_upper.startswith('UPDATE'):
            return 'UPDATE'
        elif sql_upper.startswith('DELETE'):
            return 'DELETE'
        else:
            return 'OTHER'

