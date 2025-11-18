"""
Billing decorators for token validation
"""
import logging
from functools import wraps
from rest_framework.response import Response
from rest_framework import status

from .utils import check_ai_access_for_user

logger = logging.getLogger(__name__)


def require_ai_tokens(estimated_tokens=0, feature_name="AI Feature"):
    """
    Decorator to validate token access before executing AI-powered views.
    
    Usage:
        @require_ai_tokens(estimated_tokens=1500, feature_name="Ask Question")
        def post(self, request):
            # Your AI logic here
            pass
    
    Args:
        estimated_tokens: Estimated tokens needed for the operation
        feature_name: Name of the feature (for logging)
    
    Returns:
        HTTP 402 Payment Required if access is denied
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(view_instance, request, *args, **kwargs):
            # Check if user is authenticated
            if not request.user or not request.user.is_authenticated:
                return Response({
                    'error': 'Authentication required',
                    'success': False
                }, status=status.HTTP_401_UNAUTHORIZED)
            
            # Check AI access with accurate token calculation
            access_check = check_ai_access_for_user(
                user=request.user,
                estimated_tokens=estimated_tokens,
                feature_name=feature_name
            )
            
            if not access_check['has_access']:
                logger.warning(
                    f"User {request.user.username} denied access to {feature_name}. "
                    f"Reason: {access_check['reason']}, "
                    f"Tokens remaining: {access_check['tokens_remaining']}/{access_check['original_tokens']}"
                )
                
                return Response({
                    'success': False,
                    'error': access_check['message'],
                    'error_code': access_check['reason'],
                    'tokens_remaining': access_check['tokens_remaining'],
                    'original_tokens': access_check['original_tokens'],
                    'consumed_tokens': access_check['consumed_tokens'],
                    'days_remaining': access_check['days_remaining']
                }, status=status.HTTP_402_PAYMENT_REQUIRED)
            
            # All checks passed, execute the view
            logger.debug(
                f"User {request.user.username} granted access to {feature_name}. "
                f"Tokens: {access_check['tokens_remaining']}/{access_check['original_tokens']}"
            )
            
            return view_func(view_instance, request, *args, **kwargs)
        
        return wrapper
    return decorator


def require_active_subscription(view_func):
    """
    Decorator to validate that user has an active subscription.
    
    Usage:
        @require_active_subscription
        def post(self, request):
            # Your logic here
            pass
    """
    @wraps(view_func)
    def wrapper(view_instance, request, *args, **kwargs):
        # Check if user is authenticated
        if not request.user or not request.user.is_authenticated:
            return Response({
                'error': 'Authentication required',
                'success': False
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        # Check if user has an active subscription
        from billing.models import Subscription
        
        try:
            subscription = request.user.subscription
            
            if not subscription.is_subscription_active():
                logger.warning(
                    f"User {request.user.username} subscription is not active. "
                    f"Status: {subscription.status}, "
                    f"Tokens: {subscription.tokens_remaining}, "
                    f"End date: {subscription.end_date}"
                )
                
                return Response({
                    'success': False,
                    'error': 'Active subscription required',
                    'subscription_status': subscription.status
                }, status=status.HTTP_402_PAYMENT_REQUIRED)
                
        except Subscription.DoesNotExist:
            logger.warning(f"User {request.user.username} has no subscription")
            
            return Response({
                'success': False,
                'error': 'No subscription found'
            }, status=status.HTTP_402_PAYMENT_REQUIRED)
        
        # All checks passed
        return view_func(view_instance, request, *args, **kwargs)
    
    return wrapper


def check_tokens_for_function(user, estimated_tokens=0, feature_name="AI"):
    """
    Helper function to check tokens in non-view contexts (tasks, services, etc.)
    
    Usage:
        from billing.decorators import check_tokens_for_function
        
        def my_ai_task(user_id):
            user = User.objects.get(id=user_id)
            access = check_tokens_for_function(user, estimated_tokens=1000, feature_name="Background Task")
            
            if not access['has_access']:
                # Handle insufficient tokens
                return
            
            # Proceed with AI logic
    
    Returns:
        Dict with access check results
    """
    return check_ai_access_for_user(
        user=user,
        estimated_tokens=estimated_tokens,
        feature_name=feature_name
    )

