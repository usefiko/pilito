"""
Prometheus metrics definitions for the Fiko Backend application
"""
from prometheus_client import Counter, Histogram, Gauge, Info
import os

# Application Info
app_info = Info('django_app', 'Django Application Information')
app_info.info({
    'version': '1.0.0',
    'environment': os.getenv('ENVIRONMENT', 'development')
})

# HTTP Request Metrics
http_requests_total = Counter(
    'django_http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

http_request_duration_seconds = Histogram(
    'django_http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint', 'status'],
    buckets=(0.01, 0.025, 0.05, 0.075, 0.1, 0.25, 0.5, 0.75, 1.0, 2.5, 5.0, 7.5, 10.0)
)

http_responses_by_status = Counter(
    'django_http_responses_total_by_status_total',
    'Total HTTP responses by status code',
    ['status', 'method']
)

http_request_size_bytes = Histogram(
    'django_http_request_size_bytes',
    'HTTP request size in bytes',
    ['method', 'endpoint']
)

http_response_size_bytes = Histogram(
    'django_http_response_size_bytes',
    'HTTP response size in bytes',
    ['method', 'endpoint', 'status']
)

# Database Metrics
db_query_duration_seconds = Histogram(
    'django_db_query_duration_seconds',
    'Database query duration in seconds',
    ['query_type'],
    buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5)
)

db_queries_total = Counter(
    'django_db_queries_total',
    'Total database queries',
    ['query_type', 'status']
)

db_connections_active = Gauge(
    'django_db_connections_active',
    'Number of active database connections'
)

# Cache Metrics
cache_hits_total = Counter(
    'django_cache_hits_total',
    'Total cache hits',
    ['cache_name']
)

cache_misses_total = Counter(
    'django_cache_misses_total',
    'Total cache misses',
    ['cache_name']
)

cache_operations_duration_seconds = Histogram(
    'django_cache_operations_duration_seconds',
    'Cache operation duration in seconds',
    ['operation', 'cache_name']
)

# Authentication Metrics
auth_login_total = Counter(
    'django_auth_login_total',
    'Total login attempts',
    ['status', 'method']
)

auth_active_sessions = Gauge(
    'django_auth_active_sessions',
    'Number of active user sessions'
)

auth_failed_attempts = Counter(
    'django_auth_failed_attempts_total',
    'Total failed authentication attempts',
    ['reason']
)

# WebSocket Metrics
websocket_connections_active = Gauge(
    'django_websocket_connections_active',
    'Number of active WebSocket connections',
    ['consumer']
)

websocket_messages_total = Counter(
    'django_websocket_messages_total',
    'Total WebSocket messages',
    ['consumer', 'direction', 'message_type']
)

websocket_connection_duration_seconds = Histogram(
    'django_websocket_connection_duration_seconds',
    'WebSocket connection duration in seconds',
    ['consumer']
)

# Celery Task Metrics
celery_tasks_total = Counter(
    'django_celery_tasks_total',
    'Total Celery tasks',
    ['task_name', 'status']
)

celery_task_duration_seconds = Histogram(
    'django_celery_task_duration_seconds',
    'Celery task duration in seconds',
    ['task_name'],
    buckets=(0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0, 120.0, 300.0)
)

# Note: celery_queue_length is provided by celery_prometheus_exporter library
# to avoid duplicate metric registration

# AI Model Metrics
ai_requests_total = Counter(
    'django_ai_requests_total',
    'Total AI model requests',
    ['model', 'status']
)

ai_request_duration_seconds = Histogram(
    'django_ai_request_duration_seconds',
    'AI model request duration in seconds',
    ['model'],
    buckets=(0.5, 1.0, 2.0, 5.0, 10.0, 20.0, 30.0, 60.0)
)

ai_tokens_consumed = Counter(
    'django_ai_tokens_consumed_total',
    'Total AI tokens consumed',
    ['model', 'token_type']
)

# Billing Metrics
billing_transactions_total = Counter(
    'django_billing_transactions_total',
    'Total billing transactions',
    ['status', 'payment_method']
)

billing_revenue_total = Counter(
    'django_billing_revenue_total',
    'Total revenue',
    ['currency', 'plan']
)

billing_subscription_changes = Counter(
    'django_billing_subscription_changes_total',
    'Total subscription changes',
    ['action', 'plan']
)

# Workflow Metrics
workflow_executions_total = Counter(
    'django_workflow_executions_total',
    'Total workflow executions',
    ['workflow_id', 'status']
)

workflow_execution_duration_seconds = Histogram(
    'django_workflow_execution_duration_seconds',
    'Workflow execution duration in seconds',
    ['workflow_id']
)

workflow_actions_total = Counter(
    'django_workflow_actions_total',
    'Total workflow actions executed',
    ['action_type', 'status']
)

# User Activity Metrics
user_registrations_total = Counter(
    'django_user_registrations_total',
    'Total user registrations',
    ['registration_method']
)

user_active_total = Gauge(
    'django_user_active_total',
    'Number of active users',
    ['time_period']
)

# Instagram/Social Media Metrics
instagram_api_calls_total = Counter(
    'django_instagram_api_calls_total',
    'Total Instagram API calls',
    ['endpoint', 'status']
)

instagram_messages_processed = Counter(
    'django_instagram_messages_processed_total',
    'Total Instagram messages processed',
    ['message_type', 'status']
)

# System Resource Metrics
system_memory_usage_bytes = Gauge(
    'django_system_memory_usage_bytes',
    'System memory usage in bytes',
    ['type']
)

system_cpu_usage_percent = Gauge(
    'django_system_cpu_usage_percent',
    'System CPU usage percentage'
)

# Custom Business Metrics
academy_video_views_total = Counter(
    'django_academy_video_views_total',
    'Total academy video views',
    ['video_id']
)

academy_video_completion_rate = Gauge(
    'django_academy_video_completion_rate',
    'Video completion rate',
    ['video_id']
)

