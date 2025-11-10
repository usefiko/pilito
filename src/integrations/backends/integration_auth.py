from rest_framework import authentication
from rest_framework.exceptions import AuthenticationFailed
from integrations.models import IntegrationToken
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)


class IntegrationTokenAuthentication(authentication.BaseAuthentication):
    """
    Custom authentication for Integration Tokens
    
    Header: Authorization: Bearer wc_sk_live_...
    """
    
    keyword = 'Bearer'
    
    def authenticate(self, request):
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        
        if not auth_header:
            return None
        
        if not auth_header.startswith(self.keyword + ' '):
            return None
        
        token_string = auth_header[len(self.keyword) + 1:]
        
        if not token_string:
            raise AuthenticationFailed('No token provided')
        
        return self.authenticate_credentials(token_string, request)
    
    def authenticate_credentials(self, token_string, request):
        try:
            token = IntegrationToken.objects.select_related('user').get(
                token=token_string
            )
        except IntegrationToken.DoesNotExist:
            logger.warning(f"Invalid token attempt: {token_string[:20]}...")
            raise AuthenticationFailed('Invalid token')
        
        if not token.is_active:
            logger.warning(f"Inactive token used: {token.id}")
            raise AuthenticationFailed('Token is inactive')
        
        if token.expires_at and token.expires_at < timezone.now():
            logger.warning(f"Expired token used: {token.id}")
            raise AuthenticationFailed('Token has expired')
        
        # Optional: Check IP whitelist
        if token.allowed_ips:
            client_ip = self.get_client_ip(request)
            if client_ip not in token.allowed_ips:
                logger.warning(f"IP not whitelisted: {client_ip} for token {token.id}")
                raise AuthenticationFailed('IP address not allowed')
        
        # Update usage stats
        token.last_used_at = timezone.now()
        token.usage_count += 1
        token.save(update_fields=['last_used_at', 'usage_count'])
        
        logger.info(f"Token authenticated: {token.id} (user: {token.user.email})")
        
        return (token.user, token)
    
    def authenticate_header(self, request):
        return self.keyword
    
    @staticmethod
    def get_client_ip(request):
        """Get client IP from request"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

