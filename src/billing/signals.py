from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone
from datetime import timedelta
from .models import Subscription, Payment


@receiver(pre_save, sender=Subscription)
def auto_calculate_end_date(sender, instance, **kwargs):
    """
    Token plans don't imply duration; end_date must be set explicitly elsewhere.
    """
    pass


@receiver(post_save, sender=Payment)
def handle_payment_completion(sender, instance, created, **kwargs):
    """
    Handle subscription creation/renewal when payment is completed
    """
    if instance.status == 'completed' and instance.subscription:
        subscription = instance.subscription
        
        # Ensure subscription is active when payment is completed
        if not subscription.is_active:
            subscription.is_active = True
            subscription.save()


@receiver(pre_save, sender=Subscription)
def check_subscription_expiry(sender, instance, **kwargs):
    """
    Check subscription expiry - but DON'T automatically deactivate on token depletion.
    Only deactivate if end_date has truly passed (for time-based subscriptions).
    Token depletion should be handled explicitly through controlled deactivation.
    
    IMPORTANT: For Free Trial subscriptions, tokens are burned (set to 0) when expired.
    """
    import logging
    logger = logging.getLogger(__name__)
    
    # Only deactivate if end_date has passed (for time-based subscriptions)
    if instance.end_date and timezone.now() > instance.end_date:
        instance.is_active = False
        
        # ✅ CRITICAL: For Free Trial subscriptions, burn tokens when expired
        # This ensures AI responses are blocked even if tokens_remaining > 0
        if instance.full_plan and instance.full_plan.name == 'Free Trial':
            if instance.tokens_remaining and instance.tokens_remaining > 0:
                logger.warning(
                    f"🔥 Burning tokens for expired Free Trial subscription {instance.id} "
                    f"(user: {instance.user.username}). "
                    f"Tokens before: {instance.tokens_remaining}, after: 0"
                )
                instance.tokens_remaining = 0
    
    # REMOVED: Automatic deactivation on zero tokens
    # This was causing sudden unexpected deactivations and chat conversions
    # Token-based deactivation should be handled explicitly with proper logging


@receiver(post_save, sender=Subscription)
def enforce_workflow_state_on_subscription_change(sender, instance, created, **kwargs):
    """
    When a subscription becomes inactive (expired or 0 tokens), pause all workflows for that user.
    """
    try:
        from workflow.models import Workflow
    except Exception:
        return

    # If subscription is inactive, ensure user's workflows are paused
    if not instance.is_active:
        try:
            Workflow.objects.filter(created_by=instance.user, status='ACTIVE').update(status='PAUSED')
        except Exception:
            pass
