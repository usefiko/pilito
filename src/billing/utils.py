"""
Billing utility functions for subscription and token validation
"""
import logging
from typing import Dict, Any
from django.utils import timezone

logger = logging.getLogger(__name__)


def check_ai_access_for_user(user, estimated_tokens: int = 0, feature_name: str = "AI") -> Dict[str, Any]:
    """
    Check if user has access to AI features based on subscription and tokens
    
    This function validates:
    1. User has an active subscription
    2. Subscription is not expired (end_date check)
    3. User has remaining tokens (> 0)
    4. User has enough tokens for the estimated usage
    
    Args:
        user: User instance
        estimated_tokens: Estimated tokens needed for the operation (default: 0)
        feature_name: Name of the feature being accessed (for logging)
    
    Returns:
        Dict with:
            - has_access: bool - Whether user can access AI
            - reason: str - Reason code if access denied
            - message: str - Human-readable message
            - tokens_remaining: int - Current tokens remaining
            - days_remaining: int|None - Days until subscription expires
    """
    from billing.models import Subscription
    
    try:
        subscription = user.subscription
    except Subscription.DoesNotExist:
        logger.warning(f"User {user.username} has no subscription for {feature_name}")
        return {
            'has_access': False,
            'reason': 'no_subscription',
            'message': 'No active subscription found',
            'tokens_remaining': 0,
            'days_remaining': None
        }
    
    # Check if subscription is active (checks is_active flag, tokens, and end_date)
    if not subscription.is_subscription_active():
        # Determine specific reason for inactive subscription
        reason = 'subscription_inactive'
        message = 'Subscription is not active'
        
        # Check specific conditions
        if not subscription.is_active:
            reason = 'subscription_deactivated'
            message = 'Subscription has been deactivated'
        elif subscription.tokens_remaining is None or subscription.tokens_remaining <= 0:
            reason = 'no_tokens_remaining'
            message = 'No tokens remaining in subscription'
        elif subscription.end_date and timezone.now() > subscription.end_date:
            reason = 'subscription_expired'
            message = 'Subscription has expired'
        
        logger.warning(
            f"User {user.username} subscription is not active for {feature_name}. "
            f"Reason: {reason}, Status: {subscription.status}, "
            f"Tokens: {subscription.tokens_remaining}, "
            f"End date: {subscription.end_date}"
        )
        
        return {
            'has_access': False,
            'reason': reason,
            'message': message,
            'tokens_remaining': subscription.tokens_remaining or 0,
            'days_remaining': subscription.days_remaining()
        }
    
    # Check if user has any tokens remaining
    tokens_remaining = subscription.tokens_remaining or 0
    if tokens_remaining <= 0:
        logger.warning(
            f"User {user.username} has no tokens remaining for {feature_name}. "
            f"Tokens: {tokens_remaining}"
        )
        return {
            'has_access': False,
            'reason': 'no_tokens_remaining',
            'message': 'No tokens remaining in subscription',
            'tokens_remaining': 0,
            'days_remaining': subscription.days_remaining()
        }
    
    # Check if user has enough tokens for estimated usage
    if estimated_tokens > 0 and tokens_remaining < estimated_tokens:
        logger.warning(
            f"User {user.username} has insufficient tokens for {feature_name}. "
            f"Required: {estimated_tokens}, Available: {tokens_remaining}"
        )
        return {
            'has_access': False,
            'reason': 'insufficient_tokens',
            'message': f'Insufficient tokens. Required: {estimated_tokens}, Available: {tokens_remaining}',
            'tokens_remaining': tokens_remaining,
            'days_remaining': subscription.days_remaining()
        }
    
    # All checks passed
    logger.debug(
        f"User {user.username} has access to {feature_name}. "
        f"Tokens remaining: {tokens_remaining}, Days remaining: {subscription.days_remaining()}"
    )
    
    return {
        'has_access': True,
        'reason': None,
        'message': 'Access granted',
        'tokens_remaining': tokens_remaining,
        'days_remaining': subscription.days_remaining()
    }


def free_trial_days_left_for_user(user) -> int:
    """
    Calculate days left in free trial for a user
    
    Args:
        user: User instance
    
    Returns:
        int: Days remaining in free trial (0 if not on trial or expired)
    """
    from billing.models import Subscription
    
    try:
        subscription = user.subscription
        
        # Check if user is on free trial
        if subscription.full_plan and subscription.full_plan.name == 'Free Trial':
            if subscription.end_date:
                days_left = subscription.days_remaining()
                return max(0, days_left) if days_left is not None else 0
        
        return 0
    except Subscription.DoesNotExist:
        return 0


def days_left_from_now(end_date) -> int:
    """
    Calculate days left from now to end_date
    
    Args:
        end_date: datetime object
    
    Returns:
        int: Days remaining (can be negative if expired)
    """
    if not end_date:
        return None
    
    now = timezone.now()
    delta = end_date - now
    return delta.days
