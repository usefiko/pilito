import logging
from urllib.parse import parse_qs
from django.contrib.auth.models import AnonymousUser
from django.core.cache import cache
from django.utils import timezone
from django.conf import settings
from channels.db import database_sync_to_async
from accounts.functions.jwt import validate_token, claim_token
from accounts.models import User

logger = logging.getLogger(__name__)


class WebSocketAuthMiddleware:
    """
    Custom middleware to authenticate WebSocket connections using JWT tokens
    """
    
    def __init__(self, inner):
        self.inner = inner

    async def __call__(self, scope, receive, send):
        # Only process WebSocket connections
        if scope['type'] != 'websocket':
            return await self.inner(scope, receive, send)
        
        # Get query parameters
        query_string = scope.get('query_string', b'').decode()
        query_params = parse_qs(query_string)
        
        # Extract token from query parameters
        token = None
        if 'token' in query_params:
            token = query_params['token'][0]
        
        # Set default user as anonymous
        scope['user'] = AnonymousUser()
        
        if token:
            user = await self.get_user_from_token(token)
            if user:
                scope['user'] = user
                # Log successful authentication
                logger.debug(f"WebSocket authenticated for user: {user.id}")
                
                # Rate limiting check (only in production)
                if not getattr(settings, 'DEBUG', False):
                    if not await self.check_rate_limit(user):
                        logger.warning(f"Rate limit exceeded for user: {user.id}")
                        await send({
                            'type': 'websocket.close',
                            'code': 1008,  # Policy violation
                        })
                        return
            else:
                logger.debug(f"Invalid WebSocket authentication token: {token[:20]}...")
                # In development, allow connection even with invalid token
                if getattr(settings, 'DEBUG', False):
                    logger.debug("Development mode: Allowing connection with invalid token")
                else:
                    # In production, close connection for invalid token
                    await send({
                        'type': 'websocket.close',
                        'code': 1008,  # Policy violation
                    })
                    return
        else:
            logger.debug("No authentication token provided for WebSocket")
            # In development, allow connection without token
            if getattr(settings, 'DEBUG', False):
                logger.debug("Development mode: Allowing connection without token")
            else:
                # In production, you might want to close the connection
                # For now, let the consumer handle it
                pass

        return await self.inner(scope, receive, send)

    async def get_user_from_token(self, token):
        """
        Authenticate user from JWT token with proper async/sync handling
        """
        try:
            # Validate JWT token with more flexible cache checking in development
            # These JWT functions are typically synchronous, so we need to wrap them
            check_cache = not getattr(settings, 'DEBUG', False)
            
            # Wrap synchronous JWT operations
            is_valid = await database_sync_to_async(validate_token)(token, check_time=check_cache)
            if not is_valid:
                logger.debug(f"Token validation failed for token: {token[:20]}...")
                return None
                
            payload = await database_sync_to_async(claim_token)(token)
            user_id = payload.get('user_id')
            if not user_id:
                logger.debug("No user_id in token payload")
                return None
                
            # Get user from database using async wrapper
            try:
                user = await database_sync_to_async(User.objects.get)(id=user_id)
                logger.debug(f"Successfully authenticated user: {user.id} ({user.email})")
                return user
            except User.DoesNotExist:
                logger.debug(f"User {user_id} not found in database")
                return None
                
        except Exception as e:
            logger.error(f"Error authenticating WebSocket token: {e}")
            return None

    async def check_rate_limit(self, user, max_connections=10, window_seconds=60):
        """
        Check rate limiting for WebSocket connections
        """
        try:
            cache_key = f'websocket_rate_limit_{user.id}'
            current_time = timezone.now().timestamp()
            
            # Get current connection timestamps (wrap cache operations for async safety)
            connections = await database_sync_to_async(cache.get)(cache_key, [])
            
            # Remove old connections outside the window
            connections = [ts for ts in connections if current_time - ts < window_seconds]
            
            # Check if limit exceeded
            if len(connections) >= max_connections:
                return False
            
            # Add current connection
            connections.append(current_time)
            await database_sync_to_async(cache.set)(cache_key, connections, timeout=window_seconds)
            
            return True
            
        except Exception as e:
            logger.error(f"Error checking WebSocket rate limit: {e}")
            return True  # Allow connection on error


class WebSocketSecurityMiddleware:
    """
    Additional security middleware for WebSocket connections
    """
    
    def __init__(self, inner):
        self.inner = inner

    async def __call__(self, scope, receive, send):
        if scope['type'] != 'websocket':
            return await self.inner(scope, receive, send)
        
        # Get client IP
        client_ip = self.get_client_ip(scope)
        scope['client_ip'] = client_ip
        
        # Check IP blacklist
        if await self.is_ip_blacklisted(client_ip):
            logger.warning(f"Blocked WebSocket connection from blacklisted IP: {client_ip}")
            await send({
                'type': 'websocket.close',
                'code': 1008,  # Policy violation
            })
            return
        
        # Log connection attempt (commented out to reduce verbosity)
        # logger.debug(f"WebSocket connection attempt from IP: {client_ip}")
        
        return await self.inner(scope, receive, send)

    def get_client_ip(self, scope):
        """Extract client IP from WebSocket scope"""
        try:
            # Check for forwarded headers (when behind proxy/load balancer)
            headers = dict(scope.get('headers', []))
            
            # Try X-Forwarded-For header first
            x_forwarded_for = headers.get(b'x-forwarded-for')
            if x_forwarded_for:
                return x_forwarded_for.decode().split(',')[0].strip()
            
            # Try X-Real-IP header
            x_real_ip = headers.get(b'x-real-ip')
            if x_real_ip:
                return x_real_ip.decode().strip()
            
            # Fall back to client address
            client = scope.get('client', ['unknown', 0])
            return client[0] if client else 'unknown'
            
        except Exception as e:
            logger.error(f"Error extracting client IP: {e}")
            return 'unknown'

    async def is_ip_blacklisted(self, ip):
        """Check if IP is blacklisted"""
        try:
            # Simple cache-based blacklist (wrap cache operation for async safety)
            # In production, you might want to use a database or external service
            blacklisted_ips = await database_sync_to_async(cache.get)('websocket_blacklisted_ips', set())
            return ip in blacklisted_ips
            
        except Exception as e:
            logger.error(f"Error checking IP blacklist: {e}")
            return False


# Utility functions for IP management
# Note: These are synchronous functions. When calling from async contexts,
# wrap with database_sync_to_async() decorator
def blacklist_ip(ip, duration_hours=24):
    """
    Add IP to blacklist (synchronous function)
    
    For async usage:
    await database_sync_to_async(blacklist_ip)(ip, duration_hours)
    """
    try:
        blacklisted_ips = cache.get('websocket_blacklisted_ips', set())
        blacklisted_ips.add(ip)
        cache.set('websocket_blacklisted_ips', blacklisted_ips, timeout=duration_hours * 3600)
        logger.info(f"IP {ip} blacklisted for {duration_hours} hours")
        return True
    except Exception as e:
        logger.error(f"Error blacklisting IP {ip}: {e}")
        return False


def whitelist_ip(ip):
    """
    Remove IP from blacklist (synchronous function)
    
    For async usage:
    await database_sync_to_async(whitelist_ip)(ip)
    """
    try:
        blacklisted_ips = cache.get('websocket_blacklisted_ips', set())
        blacklisted_ips.discard(ip)
        cache.set('websocket_blacklisted_ips', blacklisted_ips)
        logger.info(f"IP {ip} removed from blacklist")
        return True
    except Exception as e:
        logger.error(f"Error whitelisting IP {ip}: {e}")
        return False 