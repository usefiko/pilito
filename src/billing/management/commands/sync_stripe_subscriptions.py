"""
Management command to sync subscriptions from Stripe
Usage: python manage.py sync_stripe_subscriptions [--user-email EMAIL]
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from billing.models import Subscription
from django.contrib.auth import get_user_model
import logging

logger = logging.getLogger(__name__)

try:
    import stripe
    from django.conf import settings
    stripe.api_key = getattr(settings, 'STRIPE_SECRET_KEY', None)
    STRIPE_AVAILABLE = True
except ImportError:
    STRIPE_AVAILABLE = False


class Command(BaseCommand):
    help = 'Sync subscriptions with Stripe to ensure database is up-to-date'

    def add_arguments(self, parser):
        parser.add_argument(
            '--user-email',
            type=str,
            help='Sync subscriptions for specific user email',
        )
        parser.add_argument(
            '--all',
            action='store_true',
            help='Sync all active subscriptions',
        )

    def handle(self, *args, **options):
        if not STRIPE_AVAILABLE or not stripe.api_key:
            self.stdout.write(self.style.ERROR('Stripe is not configured'))
            return

        User = get_user_model()
        user_email = options.get('user_email')
        sync_all = options.get('all')

        if user_email:
            # Sync specific user
            try:
                user = User.objects.get(email=user_email)
                self.sync_user_subscription(user)
            except User.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'User {user_email} not found'))
                return
        elif sync_all:
            # Sync all active subscriptions
            subscriptions = Subscription.objects.filter(
                is_active=True,
                stripe_subscription_id__isnull=False
            ).select_related('user')
            
            total = subscriptions.count()
            synced = 0
            errors = 0
            
            self.stdout.write(f'Syncing {total} subscriptions...')
            
            for sub in subscriptions:
                try:
                    self.sync_user_subscription(sub.user)
                    synced += 1
                except Exception as e:
                    errors += 1
                    self.stdout.write(
                        self.style.ERROR(f'Error syncing {sub.user.email}: {str(e)}')
                    )
            
            self.stdout.write(
                self.style.SUCCESS(f'Sync complete: {synced} synced, {errors} errors')
            )
        else:
            self.stdout.write(
                self.style.ERROR('Please specify --user-email EMAIL or --all')
            )

    def sync_user_subscription(self, user):
        """Sync a single user's subscription with Stripe"""
        try:
            subscription = Subscription.objects.get(user=user)
        except Subscription.DoesNotExist:
            self.stdout.write(
                self.style.WARNING(f'No subscription found for {user.email}')
            )
            return

        if not subscription.stripe_subscription_id:
            self.stdout.write(
                self.style.WARNING(f'No Stripe subscription ID for {user.email}')
            )
            return

        try:
            # Fetch subscription from Stripe
            stripe_sub = stripe.Subscription.retrieve(
                subscription.stripe_subscription_id
            )
            
            # Update local subscription
            old_status = subscription.status
            old_cancel_at_period_end = subscription.cancel_at_period_end
            
            subscription.status = stripe_sub.status
            subscription.cancel_at_period_end = stripe_sub.cancel_at_period_end
            
            # Update canceled_at if needed
            if stripe_sub.cancel_at_period_end and not subscription.canceled_at:
                subscription.canceled_at = timezone.now()
            elif not stripe_sub.cancel_at_period_end and subscription.canceled_at:
                subscription.canceled_at = None
            
            # Check if subscription is actually ended
            if stripe_sub.status == 'canceled':
                subscription.is_active = False
                subscription.canceled_at = timezone.now()
            
            subscription.save()
            
            # Report changes
            changes = []
            if old_status != subscription.status:
                changes.append(f'status: {old_status} → {subscription.status}')
            if old_cancel_at_period_end != subscription.cancel_at_period_end:
                changes.append(
                    f'cancel_at_period_end: {old_cancel_at_period_end} → {subscription.cancel_at_period_end}'
                )
            
            if changes:
                self.stdout.write(
                    self.style.SUCCESS(
                        f'✅ {user.email}: {", ".join(changes)}'
                    )
                )
            else:
                self.stdout.write(f'✓ {user.email}: No changes')
                
        except stripe.StripeError as e:
            self.stdout.write(
                self.style.ERROR(f'Stripe error for {user.email}: {str(e)}')
            )
            raise
