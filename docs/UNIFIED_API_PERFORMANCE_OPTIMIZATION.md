# Unified Node API - Performance Optimization Guide

## 📊 Performance Analysis & Optimization

### 🎯 Key Performance Metrics

#### **Response Time Targets:**
- **Node Creation**: < 200ms
- **Node Retrieval**: < 100ms  
- **Node Updates**: < 150ms
- **Bulk Operations**: < 50ms per node
- **Advanced Actions**: < 300ms

#### **Throughput Targets:**
- **Concurrent Requests**: 100+ requests/second
- **Database Queries**: < 5 queries per request
- **Memory Usage**: < 50MB per 1000 nodes

## 🚀 Optimization Strategies Implemented

### 1. Database Optimization

#### **QuerySet Optimizations:**
```python
# In UnifiedNodeViewSet.get_queryset()
queryset = queryset.select_related('workflow').prefetch_related(
    'source_connections', 'target_connections'
)
```

**Benefits:**
- ✅ Reduces N+1 query problems
- ✅ Preloads related workflow data
- ✅ Prefetches connection information

#### **Indexed Fields:**
```python
# Recommended database indexes
class WorkflowNode(models.Model):
    class Meta:
        indexes = [
            models.Index(fields=['node_type', 'workflow']),
            models.Index(fields=['is_active', 'created_at']),
            models.Index(fields=['workflow', 'position_x', 'position_y']),
        ]
```

### 2. Serializer Optimization

#### **Field Selection:**
```python
class UnifiedNodeSerializer(serializers.ModelSerializer):
    # Only include necessary fields for list view
    def to_representation(self, instance):
        data = super().to_representation(instance)
        
        # Conditional field inclusion based on context
        if self.context.get('view_type') == 'list':
            # Remove heavy fields for list view
            data.pop('connections_as_source', None)
            data.pop('connections_as_target', None)
        
        return data
```

#### **Lazy Loading:**
```python
# Connection data only loaded when specifically requested
connections_as_source = serializers.SerializerMethodField()

def get_connections_as_source(self, obj):
    # Only execute if specifically requested
    if not self.context.get('include_connections', False):
        return []
    return [...]
```

### 3. Caching Strategy

#### **Redis Caching:**
```python
from django.core.cache import cache

class UnifiedNodeViewSet(viewsets.ModelViewSet):
    
    @action(detail=False, methods=['get'])
    def types(self, request):
        """Cached node types endpoint"""
        cache_key = 'node_types_config'
        cached_result = cache.get(cache_key)
        
        if cached_result is None:
            cached_result = self._generate_node_types()
            cache.set(cache_key, cached_result, timeout=3600)  # 1 hour
        
        return Response(cached_result)
```

#### **Cache Invalidation:**
```python
def perform_create(self, serializer):
    """Clear relevant caches after creation"""
    super().perform_create(serializer)
    
    workflow_id = serializer.instance.workflow.id
    cache.delete_many([
        f'workflow_nodes_{workflow_id}',
        f'workflow_summary_{workflow_id}',
        'node_types_config'
    ])
```

### 4. Pagination Optimization

#### **Cursor Pagination:**
```python
from rest_framework.pagination import CursorPagination

class OptimizedNodePagination(CursorPagination):
    page_size = 25
    page_size_query_param = 'page_size'
    max_page_size = 100
    ordering = '-created_at'
    cursor_query_param = 'cursor'
    
    def get_paginated_response(self, data):
        return Response({
            'next': self.get_next_link(),
            'previous': self.get_previous_link(),
            'results': data,
            'count_estimate': '~' + str(len(data) * 10)  # Estimate to avoid COUNT query
        })
```

### 5. Bulk Operations Optimization

#### **Bulk Create:**
```python
@action(detail=False, methods=['post'])
def bulk_create(self, request):
    """Optimized bulk node creation"""
    nodes_data = request.data.get('nodes', [])
    
    # Validate all at once
    serializers_list = []
    for node_data in nodes_data:
        serializer = self.get_serializer(data=node_data)
        serializer.is_valid(raise_exception=True)
        serializers_list.append(serializer)
    
    # Bulk create in database
    nodes_to_create = []
    for serializer in serializers_list:
        node_type = serializer.validated_data.pop('node_type')
        
        if node_type == 'when':
            nodes_to_create.append(WhenNode(**serializer.validated_data))
        elif node_type == 'condition':
            nodes_to_create.append(ConditionNode(**serializer.validated_data))
        # ... other types
    
    # Single database transaction
    created_nodes = []
    with transaction.atomic():
        for node in nodes_to_create:
            node.save()
            created_nodes.append(node)
    
    return Response({
        'created_count': len(created_nodes),
        'nodes': [self.get_serializer(node).data for node in created_nodes]
    })
```

### 6. Connection Optimization

#### **Efficient Connection Queries:**
```python
def get_connections(self, request, pk=None):
    """Optimized connection retrieval"""
    node = self.get_object()
    
    # Single query with joins
    connections = NodeConnection.objects.filter(
        Q(source_node=node) | Q(target_node=node)
    ).select_related(
        'source_node', 'target_node', 
        'source_node__workflow', 'target_node__workflow'
    )
    
    # Process in Python to avoid multiple queries
    outgoing = []
    incoming = []
    
    for conn in connections:
        if conn.source_node_id == node.id:
            outgoing.append({
                'id': conn.id,
                'type': 'outgoing',
                'target_node': {
                    'id': conn.target_node.id,
                    'title': conn.target_node.title,
                    'node_type': conn.target_node.node_type
                }
            })
        else:
            incoming.append({
                'id': conn.id,
                'type': 'incoming',
                'source_node': {
                    'id': conn.source_node.id,
                    'title': conn.source_node.title,
                    'node_type': conn.source_node.node_type
                }
            })
    
    return Response({
        'outgoing_connections': outgoing,
        'incoming_connections': incoming,
        'total_connections': len(outgoing) + len(incoming)
    })
```

## 📈 Performance Monitoring

### 1. Request Timing Middleware

```python
import time
import logging

class NodeAPITimingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.logger = logging.getLogger('node_api_performance')

    def __call__(self, request):
        if '/api/v1/workflow/api/nodes/' in request.path:
            start_time = time.time()
            
            response = self.get_response(request)
            
            duration = (time.time() - start_time) * 1000  # milliseconds
            
            self.logger.info(
                f"Node API: {request.method} {request.path} - "
                f"{response.status_code} - {duration:.2f}ms"
            )
            
            # Add performance header
            response['X-Response-Time'] = f"{duration:.2f}ms"
            
            return response
        
        return self.get_response(request)
```

### 2. Database Query Monitoring

```python
from django.db import connection
from django.conf import settings

class QueryCountDebugMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if settings.DEBUG and '/api/v1/workflow/api/nodes/' in request.path:
            queries_before = len(connection.queries)
            
            response = self.get_response(request)
            
            queries_after = len(connection.queries)
            query_count = queries_after - queries_before
            
            response['X-DB-Queries'] = str(query_count)
            
            if query_count > 10:  # Alert threshold
                logging.warning(
                    f"High query count: {query_count} queries for {request.path}"
                )
            
            return response
        
        return self.get_response(request)
```

### 3. Memory Usage Tracking

```python
import psutil
import os

class MemoryUsageMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.process = psutil.Process(os.getpid())

    def __call__(self, request):
        if '/api/v1/workflow/api/nodes/' in request.path:
            memory_before = self.process.memory_info().rss / 1024 / 1024  # MB
            
            response = self.get_response(request)
            
            memory_after = self.process.memory_info().rss / 1024 / 1024  # MB
            memory_diff = memory_after - memory_before
            
            response['X-Memory-Usage'] = f"{memory_after:.2f}MB"
            response['X-Memory-Diff'] = f"+{memory_diff:.2f}MB"
            
            return response
        
        return self.get_response(request)
```

## 🎯 Performance Best Practices

### 1. Frontend Integration

```javascript
// Efficient node loading with pagination
async function loadNodes(workflowId, page = 1) {
    const response = await fetch(
        `/api/v1/workflow/api/nodes/by_workflow/?workflow_id=${workflowId}&page=${page}&page_size=25`,
        {
            headers: {
                'Authorization': `Bearer ${token}`,
                'Cache-Control': 'max-age=300' // 5 minutes cache
            }
        }
    );
    
    return response.json();
}

// Batch operations for better performance
async function createMultipleNodes(nodesData) {
    const requests = nodesData.map(nodeData => 
        fetch('/api/v1/workflow/api/nodes/', {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(nodeData)
        })
    );
    
    // Execute in parallel with concurrency limit
    const results = [];
    for (let i = 0; i < requests.length; i += 5) {
        const batch = requests.slice(i, i + 5);
        const batchResults = await Promise.all(batch);
        results.push(...batchResults);
    }
    
    return results;
}
```

### 2. Caching Headers

```python
from django.views.decorators.cache import cache_page
from django.utils.decorators import method_decorator

class UnifiedNodeViewSet(viewsets.ModelViewSet):
    
    @method_decorator(cache_page(60 * 5))  # 5 minutes
    @action(detail=False, methods=['get'])
    def types(self, request):
        """Cache static configuration data"""
        return Response([...])
    
    def list(self, request, *args, **kwargs):
        """Add cache headers for list views"""
        response = super().list(request, *args, **kwargs)
        
        # Add cache headers
        response['Cache-Control'] = 'max-age=300, public'  # 5 minutes
        response['Vary'] = 'Authorization'
        
        return response
```

### 3. Compression & Content Optimization

```python
# settings.py
MIDDLEWARE = [
    'django.middleware.gzip.GZipMiddleware',  # Enable compression
    # ... other middleware
]

# Enable JSON response compression
REST_FRAMEWORK = {
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
    'DEFAULT_CONTENT_NEGOTIATION_CLASS': 'rest_framework.content_negotiation.DefaultContentNegotiation',
}
```

## 📊 Performance Benchmarks

### Expected Performance Metrics

| Operation | Target Time | Queries | Memory |
|-----------|-------------|---------|---------|
| List 25 nodes | < 100ms | 2-3 | 10MB |
| Get node details | < 50ms | 1-2 | 5MB |
| Create node | < 150ms | 1-2 | 8MB |
| Update node | < 100ms | 1-2 | 7MB |
| Delete node + connections | < 200ms | 3-5 | 12MB |
| Duplicate node | < 250ms | 2-3 | 15MB |
| Get connections | < 75ms | 1 | 8MB |
| Bulk create (10 nodes) | < 500ms | 10-15 | 50MB |

### Load Testing Results

```bash
# Expected results with optimizations
ab -n 1000 -c 10 -H "Authorization: Bearer token" \
   http://localhost:8000/api/v1/workflow/api/nodes/

# Results:
# Requests per second: 150-200 RPS
# Average response time: 50-80ms  
# 95th percentile: < 150ms
# 99th percentile: < 300ms
```

## 🔧 Troubleshooting Performance Issues

### 1. Slow Queries

```sql
-- Analyze slow queries
EXPLAIN ANALYZE SELECT * FROM workflow_workflownode 
WHERE workflow_id = 'uuid' AND is_active = true;

-- Add indexes if needed
CREATE INDEX CONCURRENTLY idx_workflownode_workflow_active 
ON workflow_workflownode(workflow_id, is_active);
```

### 2. Memory Leaks

```python
# Use Django Debug Toolbar to identify issues
# Monitor object creation in views

import gc

class DebugUnifiedNodeViewSet(UnifiedNodeViewSet):
    def dispatch(self, request, *args, **kwargs):
        gc.collect()  # Force garbage collection
        objects_before = len(gc.get_objects())
        
        response = super().dispatch(request, *args, **kwargs)
        
        gc.collect()
        objects_after = len(gc.get_objects())
        
        print(f"Objects created: {objects_after - objects_before}")
        
        return response
```

### 3. N+1 Query Problems

```python
# Use select_related and prefetch_related
queryset = WorkflowNode.objects.select_related('workflow').prefetch_related(
    'source_connections__target_node',
    'target_connections__source_node'
)

# Monitor with Django Debug Toolbar
# Or use django-querycount middleware
```

---

This optimization guide ensures the Unified Node API delivers excellent performance even with large numbers of nodes and high concurrent usage! 🚀
