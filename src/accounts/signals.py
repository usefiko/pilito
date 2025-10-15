from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from accounts.models import User, Plan
from django.utils import timezone
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)

try:
    from billing.models import Subscription, FullPlan
except Exception:
    Subscription = None
    FullPlan = None

@receiver(post_save, sender=User)
def create_user_plan(sender, instance, created, **kwargs):
    if created:
        Plan.objects.create(user=instance)
        # Create a trialing subscription synced with billing system
        if Subscription is not None:
            try:
                # Avoid duplicate creation if any other signal created one
                Subscription.objects.get(user=instance)
            except Subscription.DoesNotExist:
                now = timezone.now()
                # Prefer plan-based free trial
                free_trial_plan = None
                if FullPlan is not None:
                    try:
                        free_trial_plan, _ = FullPlan.objects.get_or_create(
                            name='Free Trial',
                            defaults={
                                'tokens_included': 5000,
                                'duration_days': 14,
                                'is_recommended': False,
                                'is_yearly': False,
                                'price_en': 0,
                                'price_tr': 0,
                                'price_ar': 0,
                                'is_active': True,
                                'description': 'Automatic free trial plan for new users',
                            }
                        )
                    except Exception:
                        free_trial_plan = None

                duration_days = 14
                tokens_included = 5000
                if free_trial_plan is not None:
                    duration_days = free_trial_plan.duration_days
                    tokens_included = free_trial_plan.tokens_included

                trial_end = now + timedelta(days=duration_days)

                Subscription.objects.create(
                    user=instance,
                    token_plan=None,
                    full_plan=free_trial_plan,
                    start_date=now,
                    end_date=trial_end,
                    tokens_remaining=tokens_included,
                    is_active=True,
                    status='trialing',
                    trial_end=trial_end,
                )


# ============================================================================
# INTERCOM INTEGRATION SIGNALS
# ============================================================================

@receiver(post_save, sender=User)
def sync_user_to_intercom_on_save(sender, instance, created, **kwargs):
    """
    Automatically sync user to Intercom when created or updated.
    
    This runs asynchronously via Celery to avoid blocking the request.
    """
    from accounts.tasks import sync_user_to_intercom_async
    from django.conf import settings
    
    # Only sync if Intercom is configured
    if not settings.INTERCOM_ACCESS_TOKEN:
        return
    
    # Skip if user doesn't have email
    if not instance.email:
        logger.warning(f"Skipping Intercom sync for user {instance.id} - no email")
        return
    
    try:
        # Trigger async sync
        sync_user_to_intercom_async.delay(instance.id)
        
        if created:
            logger.info(f"🔄 Triggered Intercom sync for new user {instance.id} ({instance.email})")
        else:
            logger.info(f"🔄 Triggered Intercom sync for updated user {instance.id} ({instance.email})")
            
    except Exception as e:
        logger.error(f"❌ Failed to trigger Intercom sync for user {instance.id}: {str(e)}")


@receiver(post_delete, sender=User)
def delete_intercom_contact_on_user_delete(sender, instance, **kwargs):
    """
    Automatically delete Intercom contact when user is deleted.
    
    This runs asynchronously via Celery.
    """
    from accounts.tasks import delete_intercom_contact_async
    from django.conf import settings
    
    # Only delete if Intercom is configured
    if not settings.INTERCOM_ACCESS_TOKEN:
        return
    
    try:
        # Trigger async deletion
        delete_intercom_contact_async.delay(instance.id)
        logger.info(f"🗑️ Triggered Intercom contact deletion for user {instance.id}")
        
    except Exception as e:
        logger.error(f"❌ Failed to trigger Intercom contact deletion for user {instance.id}: {str(e)}")