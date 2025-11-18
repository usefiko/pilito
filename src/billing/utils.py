"""
Billing utility functions for subscription and token validation
"""
import logging
from typing import Dict, Any, Tuple
from django.utils import timezone
from django.db.models import Sum

logger = logging.getLogger(__name__)


def get_accurate_tokens_remaining(user) -> Tuple[int, int, int]:
    """
    Calculate ACCURATE tokens remaining based on actual AI usage from AIUsageLog.
    
    This is the SINGLE SOURCE OF TRUTH for token calculations.
    
    Returns:
        Tuple of (original_tokens, consumed_tokens, remaining_tokens)
    """
    from billing.models import Subscription
    from AI_model.models import AIUsageLog
    
    try:
        subscription = user.subscription
    except Subscription.DoesNotExist:
        return (0, 0, 0)
    
    # Calculate original tokens from the plan
    original_tokens = 0
    if subscription.token_plan:
        original_tokens = subscription.token_plan.tokens_included
    elif subscription.full_plan:
        original_tokens = subscription.full_plan.tokens_included
    
    # Calculate total AI tokens used by this user since subscription started
    ai_tokens_used = AIUsageLog.objects.filter(
        user=user,
        created_at__gte=subscription.start_date,
        success=True  # Only count successful requests
    ).aggregate(
        total=Sum('total_tokens')
    )['total'] or 0
    
    # Calculate actual remaining tokens
    actual_tokens_remaining = max(0, original_tokens - ai_tokens_used)
    
    return (original_tokens, ai_tokens_used, actual_tokens_remaining)


def check_ai_access_for_user(user, estimated_tokens: int = 0, feature_name: str = "AI") -> Dict[str, Any]:
    """
    Check if user has access to AI features based on subscription and tokens.
    
    CRITICAL: This function uses ACTUAL token consumption from AIUsageLog,
    not the subscription.tokens_remaining database field.
    
    This function validates:
    1. User has an active subscription
    2. Subscription is not expired (end_date check)
    3. User has remaining tokens based on ACTUAL AI usage (> 0)
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
            - tokens_remaining: int - ACCURATE tokens remaining based on actual usage
            - original_tokens: int - Total tokens included in plan
            - consumed_tokens: int - Total tokens consumed so far
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
            'original_tokens': 0,
            'consumed_tokens': 0,
            'days_remaining': None
        }
    
    # Get ACCURATE token counts from actual AI usage
    original_tokens, consumed_tokens, tokens_remaining = get_accurate_tokens_remaining(user)
    
    # Check if subscription is_active flag is False
    if not subscription.is_active:
        logger.warning(
            f"User {user.username} subscription is deactivated for {feature_name}. "
            f"is_active: False"
        )
        return {
            'has_access': False,
            'reason': 'subscription_deactivated',
            'message': 'Subscription has been deactivated',
            'tokens_remaining': tokens_remaining,
            'original_tokens': original_tokens,
            'consumed_tokens': consumed_tokens,
            'days_remaining': subscription.days_remaining()
        }
    
    # Check if subscription is expired
    if subscription.end_date and timezone.now() > subscription.end_date:
        logger.warning(
            f"User {user.username} subscription is expired for {feature_name}. "
            f"End date: {subscription.end_date}"
        )
        return {
            'has_access': False,
            'reason': 'subscription_expired',
            'message': 'Subscription has expired',
            'tokens_remaining': tokens_remaining,
            'original_tokens': original_tokens,
            'consumed_tokens': consumed_tokens,
            'days_remaining': 0
        }
    
    # Check if user has any tokens remaining (based on ACTUAL usage)
    if tokens_remaining <= 0:
        logger.warning(
            f"User {user.username} has no tokens remaining for {feature_name}. "
            f"Consumed: {consumed_tokens}/{original_tokens} tokens"
        )
        return {
            'has_access': False,
            'reason': 'no_tokens_remaining',
            'message': 'No tokens remaining in subscription',
            'tokens_remaining': 0,
            'original_tokens': original_tokens,
            'consumed_tokens': consumed_tokens,
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
            'original_tokens': original_tokens,
            'consumed_tokens': consumed_tokens,
            'days_remaining': subscription.days_remaining()
        }
    
    # All checks passed
    logger.debug(
        f"User {user.username} has access to {feature_name}. "
        f"Tokens remaining: {tokens_remaining}/{original_tokens}, "
        f"Days remaining: {subscription.days_remaining()}"
    )
    
    return {
        'has_access': True,
        'reason': None,
        'message': 'Access granted',
        'tokens_remaining': tokens_remaining,
        'original_tokens': original_tokens,
        'consumed_tokens': consumed_tokens,
        'days_remaining': subscription.days_remaining()
    }


def free_trial_days_left_for_user(user) -> int:
    """
    Calculate free trial days left for user
    """
    from billing.models import Subscription
    
    try:
        subscription = user.subscription
        if subscription.trial_end:
            days_left = (subscription.trial_end - timezone.now()).days
            return max(0, days_left)
    except Subscription.DoesNotExist:
        pass
    
    return 0


def enforce_account_deactivation_for_user(user):
    """
    Enforce account-level changes when subscription becomes inactive
    """
    from workflow.models import Workflow
    from message.models import Conversation
    
    logger.info(f"Enforcing account deactivation for user {user.username}")
    
    # Disable AI-powered workflows
    workflows = Workflow.objects.filter(user=user, is_active=True)
    for workflow in workflows:
        # Check if workflow uses AI actions
        if workflow.has_ai_actions():
            workflow.is_active = False
            workflow.save()
            logger.info(f"Disabled AI workflow {workflow.id} for user {user.username}")
    
    # Convert AI-powered conversations to manual mode
    conversations = Conversation.objects.filter(user=user, ai_enabled=True)
    for conversation in conversations:
        conversation.ai_enabled = False
        conversation.save()
        logger.info(f"Disabled AI for conversation {conversation.id} for user {user.username}")
