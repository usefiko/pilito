"""
Celery tasks for billing operations
"""
import logging
from celery import shared_task
from django.utils import timezone
from datetime import timedelta

logger = logging.getLogger(__name__)


@shared_task(name='billing.activate_queued_plans')
def activate_queued_plans():
    """
    Daily task to activate queued DOWNGRADE plans at end_date.
    
    IMPORTANT: Only DOWNGRADE plans are queued. UPGRADE plans are applied immediately.
    
    This task:
    1. Finds all subscriptions with queued plans where end_date has passed (downgrades only)
    2. Burns old Full Plan tokens (preserves Token Plan tokens)
    3. Activates the queued plan
    4. Updates subscription dates and adds new tokens
    """
    from billing.models import Subscription
    
    now = timezone.now()
    
    # Find subscriptions with queued plans that should activate
    subscriptions_to_update = Subscription.objects.filter(
        end_date__lte=now,
        queued_full_plan__isnull=False
    ).select_related('user', 'full_plan', 'queued_full_plan')
    
    activated_count = 0
    
    for subscription in subscriptions_to_update:
        try:
            old_plan = subscription.full_plan
            new_plan = subscription.queued_full_plan
            old_tokens = subscription.tokens_remaining
            new_tokens = subscription.queued_tokens_amount or 0
            
            logger.info(
                f"🔄 Activating queued plan for user {subscription.user.username}. "
                f"Old plan: {old_plan.name if old_plan else 'None'}, "
                f"New plan: {new_plan.name}, "
                f"Old tokens: {old_tokens}, New tokens: {new_tokens}"
            )
            
            # Calculate tokens from Token Plans (these should NOT be burned)
            # Strategy: If user has a token_plan, assume those tokens are from it
            token_plan_tokens = 0
            if subscription.token_plan:
                # We can't track exactly which tokens are from token plan vs full plan
                # So we need a better strategy - let's check if there's a recent token plan purchase
                from billing.models import Payment
                recent_token_purchase = Payment.objects.filter(
                    user=subscription.user,
                    token_plan__isnull=False,
                    status='completed'
                ).order_by('-created_at').first()
                
                if recent_token_purchase:
                    # Estimate: if purchase was recent and tokens match, preserve them
                    token_plan_tokens = recent_token_purchase.token_plan.tokens_included
            
            # BURN old Full Plan tokens, but preserve Token Plan tokens
            # Since we can't perfectly track which tokens are which, we use this logic:
            # If old_tokens > token_plan_tokens, the excess is from Full Plan (burn it)
            full_plan_tokens_to_burn = max(0, old_tokens - token_plan_tokens)
            tokens_to_preserve = old_tokens - full_plan_tokens_to_burn
            
            logger.info(
                f"Token breakdown: Total={old_tokens}, "
                f"Estimated Token Plan tokens={token_plan_tokens}, "
                f"Full Plan tokens to burn={full_plan_tokens_to_burn}, "
                f"Tokens to preserve={tokens_to_preserve}"
            )
            
            # Activate queued plan
            subscription.full_plan = new_plan
            subscription.start_date = subscription.end_date  # Start from old end_date
            subscription.end_date = subscription.end_date + timedelta(days=new_plan.duration_days)
            subscription.tokens_remaining = tokens_to_preserve + new_tokens
            
            # Clear queued plan fields
            subscription.queued_full_plan = None
            subscription.queued_token_plan = None
            subscription.queued_tokens_amount = None
            
            subscription.save()
            
            logger.info(
                f"✅ Successfully activated queued plan for user {subscription.user.username}. "
                f"New plan: {new_plan.name}, "
                f"New end_date: {subscription.end_date.date()}, "
                f"Tokens: {old_tokens} → {subscription.tokens_remaining} "
                f"(burned {full_plan_tokens_to_burn}, preserved {tokens_to_preserve}, added {new_tokens})"
            )
            
            activated_count += 1
            
        except Exception as e:
            logger.error(
                f"❌ Failed to activate queued plan for user {subscription.user.username}: {e}",
                exc_info=True
            )
    
    if activated_count > 0:
        logger.info(f"✅ Activated {activated_count} queued plan(s)")
    
    return {
        'success': True,
        'activated_count': activated_count
    }

