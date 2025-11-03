from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from accounts.models import User, Plan
from django.utils import timezone
from datetime import timedelta
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import logging

logger = logging.getLogger(__name__)

try:
    from billing.models import Subscription, FullPlan
except Exception:
    Subscription = None
    FullPlan = None

@receiver(post_save, sender=User, dispatch_uid='create_user_plan')
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
                                'price': 0,
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

@receiver(post_save, sender=User, dispatch_uid='sync_user_to_intercom')
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


# ============================================================================
# WIZARD STATUS WEBSOCKET NOTIFICATIONS
# ============================================================================

def check_and_complete_wizard(user):
    """
    Check if all wizard requirements are met and auto-complete wizard
    
    Args:
        user: User instance to check
        
    Returns:
        bool: True if wizard was auto-completed, False otherwise
    """
    from settings.models import AIPrompts, InstagramChannel, TelegramChannel
    
    # Skip if already completed
    if user.wizard_complete:
        return False
    
    # Check all requirements
    if not user.first_name:
        return False
    if not user.last_name:
        return False
    if not user.phone_number:
        return False
    if not user.business_type:
        return False
    
    # Check manual_prompt
    try:
        ai_prompts = AIPrompts.objects.get(user=user)
        if not ai_prompts.manual_prompt or not ai_prompts.manual_prompt.strip():
            return False
    except AIPrompts.DoesNotExist:
        return False
    
    # Check channels (at least one connected)
    instagram_connected = InstagramChannel.objects.filter(user=user, is_connect=True).exists()
    telegram_connected = TelegramChannel.objects.filter(user=user, is_connect=True).exists()
    
    if not (instagram_connected or telegram_connected):
        return False
    
    # All requirements met! Auto-complete wizard
    # Use QuerySet.update() to avoid triggering signals again
    User.objects.filter(pk=user.pk).update(wizard_complete=True)
    # Refresh the instance
    user.refresh_from_db()
    logger.info(f"✅ Wizard auto-completed for user {user.id} ({user.email})")
    return True


def notify_wizard_status(user_id):
    """
    Send WebSocket notification for wizard status change
    
    Args:
        user_id: ID of the user whose wizard status changed
    """
    try:
        channel_layer = get_channel_layer()
        if channel_layer:
            async_to_sync(channel_layer.group_send)(
                f'wizard_status_{user_id}',
                {'type': 'wizard_status_updated'}
            )
            logger.info(f"📡 Wizard status notification sent for user {user_id}")
    except Exception as e:
        logger.error(f"Failed to send wizard status notification for user {user_id}: {e}")


@receiver(post_save, sender=User, dispatch_uid='notify_wizard_on_user_update')
def notify_wizard_on_user_update(sender, instance, created, **kwargs):
    """
    Notify wizard status WebSocket when User model changes
    Triggers when: first_name, last_name, phone_number, business_type changes
    Also auto-completes wizard if all requirements are met
    """
    if not created:  # Only for updates, not new users
        # Check and auto-complete wizard if ready
        check_and_complete_wizard(instance)
        # Notify WebSocket
        notify_wizard_status(instance.id)


@receiver(post_save, sender='settings.AIPrompts')
def notify_wizard_on_prompts_update(sender, instance, **kwargs):
    """
    Notify wizard status WebSocket when AIPrompts model changes
    Triggers when: manual_prompt is updated
    Also auto-completes wizard if all requirements are met
    """
    # Check and auto-complete wizard if ready
    check_and_complete_wizard(instance.user)
    # Notify WebSocket
    notify_wizard_status(instance.user.id)


@receiver(post_save, sender='settings.InstagramChannel')
def notify_wizard_on_instagram_update(sender, instance, **kwargs):
    """
    Notify wizard status WebSocket when InstagramChannel model changes
    Triggers when: is_connect status changes
    Also auto-completes wizard if all requirements are met
    """
    # Check and auto-complete wizard if ready
    check_and_complete_wizard(instance.user)
    # Notify WebSocket
    notify_wizard_status(instance.user.id)


@receiver(post_save, sender='settings.TelegramChannel')
def notify_wizard_on_telegram_update(sender, instance, **kwargs):
    """
    Notify wizard status WebSocket when TelegramChannel model changes
    Triggers when: is_connect status changes
    Also auto-completes wizard if all requirements are met
    """
    # Check and auto-complete wizard if ready
    check_and_complete_wizard(instance.user)
    # Notify WebSocket
    notify_wizard_status(instance.user.id)
