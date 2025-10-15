from django.utils import timezone
from math import ceil
from django.db import transaction


def days_left_from_now(end_datetime, now=None):
    """
    Return number of days left between now and end_datetime using ceil on seconds.
    If end_datetime is None, return None.
    """
    if end_datetime is None:
        return None
    if now is None:
        now = timezone.now()
    remaining = end_datetime - now
    total_seconds = max(0, remaining.total_seconds())
    return int(ceil(total_seconds / 86400))


def format_days_left_value(days):
    """
    Format integer days into a human-readable string like "3 days left".
    If days is None or 0, return "0 days left".
    """
    if not days:
        return "0 days left"
    return f"{days} {'day' if days == 1 else 'days'} left"


def free_trial_days_left_for_user(user):
    """
    Calculate formatted free trial days left for a user based on the subscription end_date
    and "Free Trial" plan. Uses ceil-based day calculation.
    """
    try:
        subscription = user.subscription
        now = timezone.now()
        if (
            subscription.end_date
            and subscription.full_plan
            and subscription.full_plan.name == 'Free Trial'
            and now <= subscription.end_date
        ):
            days = days_left_from_now(subscription.end_date, now=now)
            return format_days_left_value(days)
    except Exception:
        pass
    return "0 days left"


def enforce_account_deactivation_for_user(user):
    """
    When a user has no active plan (no tokens or time left), enforce product-wide restrictions:
    - Set all conversations status to "support_active"
    - Set user's default_reply_handler to "Manual"
    - Set all workflows to an inactive state (use status='PAUSED')
    """
    from message.models import Conversation
    try:
        from workflow.models import Workflow
    except Exception:
        Workflow = None

    with transaction.atomic():
        # Update user reply handler
        if getattr(user, 'default_reply_handler', None) != 'Manual':
            user.default_reply_handler = 'Manual'
            user.save(update_fields=['default_reply_handler'])

        # Update all conversations for the user
        Conversation.objects.filter(user=user).exclude(status='support_active').update(status='support_active')

        # Update workflows (if workflow app is present)
        if Workflow is not None:
            Workflow.objects.filter(created_by=user).exclude(status='PAUSED').update(status='PAUSED')



