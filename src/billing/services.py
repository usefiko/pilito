from django.db import transaction


def consume_tokens_for_user(user, tokens: int, description: str = 'AI usage', allow_partial: bool = True):
    """
    Deduct tokens from the user's active subscription and record TokenUsage.

    Returns (success: bool, data_or_error: Any).
    If allow_partial is True, will consume up to available tokens when insufficient.
    """
    if not user:
        return False, 'No user provided'

    # Lazy import to avoid circular imports at import time
    try:
        from .models import Subscription, TokenUsage
    except Exception as e:
        return False, f'Billing models unavailable: {e}'

    try:
        subscription = user.subscription
    except Subscription.DoesNotExist:
        return False, 'No subscription found'

    if not subscription.is_subscription_active():
        return False, 'Subscription is not active'

    if tokens is None or tokens <= 0:
        return True, {'tokens_consumed': 0, 'tokens_remaining': subscription.tokens_remaining}

    with transaction.atomic():
        available = max(0, subscription.tokens_remaining or 0)
        if available <= 0:
            tokens_to_consume = 0
        else:
            tokens_to_consume = min(available, int(tokens)) if allow_partial else int(tokens)

        # Only update if there is anything to consume
        if tokens_to_consume > 0:
            new_remaining = max(0, available - tokens_to_consume)
            subscription.tokens_remaining = new_remaining
            
            # CHANGED: Don't immediately deactivate on zero tokens
            # This prevents sudden unexpected deactivations
            # Instead, just save the token count and let explicit checks handle deactivation
            subscription.save(update_fields=['tokens_remaining', 'updated_at'])

            TokenUsage.objects.create(
                subscription=subscription,
                used_tokens=tokens_to_consume,
                description=description
            )
            
            # If tokens depleted, log a warning but don't auto-deactivate
            if new_remaining == 0:
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(
                    f"User {user.username} (ID: {user.id}) has depleted all tokens. "
                    f"Subscription ID: {subscription.id}. Consider manual review."
                )

        return True, {
            'tokens_consumed': tokens_to_consume,
            'tokens_remaining': subscription.tokens_remaining
        }


