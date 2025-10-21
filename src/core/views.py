from django.shortcuts import render
from django.http import JsonResponse
from django.db import connection
from django.core.cache import cache
import logging

logger = logging.getLogger(__name__)

def index(request):
    return render(request, 'index.html')

def health_check(request):
    """
    Health check endpoint for Docker Swarm and load balancers.
    Checks database and cache connectivity.
    """
    status = {
        'status': 'healthy',
        'checks': {}
    }
    http_status = 200
    
    # Check database
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        status['checks']['database'] = 'ok'
    except Exception as e:
        logger.error(f"Health check database error: {e}")
        status['checks']['database'] = 'error'
        status['status'] = 'unhealthy'
        http_status = 503
    
    # Check cache (Redis)
    try:
        cache.set('health_check', 'ok', 10)
        if cache.get('health_check') == 'ok':
            status['checks']['cache'] = 'ok'
        else:
            raise Exception("Cache read/write failed")
    except Exception as e:
        logger.error(f"Health check cache error: {e}")
        status['checks']['cache'] = 'error'
        status['status'] = 'unhealthy'
        http_status = 503
    
    return JsonResponse(status, status=http_status)