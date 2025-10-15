"""
Views for Prometheus metrics endpoint
"""
from django.http import HttpResponse
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST, CollectorRegistry, multiprocess, REGISTRY
from prometheus_client import Gauge
import os
import psutil


def metrics_view(request):
    """
    Expose Prometheus metrics endpoint
    This endpoint should be called by Prometheus scraper
    """
    # Update system metrics before generating output
    update_system_metrics()
    
    # Generate and return Prometheus metrics
    metrics = generate_latest(REGISTRY)
    return HttpResponse(
        metrics,
        content_type=CONTENT_TYPE_LATEST
    )


def update_system_metrics():
    """
    Update system-level metrics like CPU and memory usage
    """
    from . import metrics as app_metrics
    
    # Get current process
    process = psutil.Process(os.getpid())
    
    # Memory usage
    memory_info = process.memory_info()
    app_metrics.system_memory_usage_bytes.labels(type='rss').set(memory_info.rss)
    app_metrics.system_memory_usage_bytes.labels(type='vms').set(memory_info.vms)
    
    # CPU usage
    cpu_percent = process.cpu_percent(interval=0.1)
    app_metrics.system_cpu_usage_percent.set(cpu_percent)
    
    # Database connections (if available)
    try:
        from django.db import connection
        app_metrics.db_connections_active.set(len(connection.queries))
    except Exception:
        pass


def health_check(request):
    """
    Simple health check endpoint
    """
    return HttpResponse("OK", status=200)

