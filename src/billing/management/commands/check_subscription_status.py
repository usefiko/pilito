"""
Management command to check subscription status and handle deactivation properly.
This should be run periodically via cron job instead of using aggressive signals.

Usage:
    python manage.py check_subscription_status
    python manage.py check_subscription_status --dry-run
    python manage.py check_subscription_status --warn-threshold 100
"""
import logging
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db.models import Q
from billing.models import Subscription
from billing.utils import enforce_account_deactivation_for_user

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Check subscriptions and deactivate those that have expired or depleted tokens'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be deactivated without actually doing it',
        )
        parser.add_argument(
            '--warn-threshold',
            type=int,
            default=100,
            help='Warn users when tokens fall below this threshold (default: 100)',
        )
        parser.add_argument(
            '--deactivate-zero-tokens',
            action='store_true',
            help='Actually deactivate subscriptions with zero tokens (be careful!)',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        warn_threshold = options['warn_threshold']
        deactivate_zero = options['deactivate_zero_tokens']
        
        now = timezone.now()
        
        self.stdout.write(self.style.SUCCESS(f'\n📊 Checking subscription status at {now}'))
        if dry_run:
            self.stdout.write(self.style.WARNING('🔍 DRY RUN MODE - No changes will be made\n'))
        
        # Find subscriptions that should be deactivated
        subscriptions_to_check = Subscription.objects.filter(is_active=True)
        
        expired_by_date = []
        depleted_tokens = []
        low_tokens = []
        
        for subscription in subscriptions_to_check:
            user = subscription.user
            username = user.username if user else 'unknown'
            
            # Check for date expiration
            if subscription.end_date and now > subscription.end_date:
                expired_by_date.append(subscription)
                self.stdout.write(
                    self.style.ERROR(
                        f'⏰ EXPIRED: User {username} (ID: {user.id}) - '
                        f'End date: {subscription.end_date}, Tokens: {subscription.tokens_remaining}'
                    )
                )
            
            # Check for token depletion
            elif subscription.tokens_remaining is not None and subscription.tokens_remaining <= 0:
                depleted_tokens.append(subscription)
                self.stdout.write(
                    self.style.ERROR(
                        f'🚫 NO TOKENS: User {username} (ID: {user.id}) - '
                        f'Tokens: {subscription.tokens_remaining}, End date: {subscription.end_date}'
                    )
                )
            
            # Check for low tokens (warning)
            elif subscription.tokens_remaining is not None and subscription.tokens_remaining < warn_threshold:
                low_tokens.append(subscription)
                self.stdout.write(
                    self.style.WARNING(
                        f'⚠️  LOW TOKENS: User {username} (ID: {user.id}) - '
                        f'Tokens: {subscription.tokens_remaining} (below {warn_threshold})'
                    )
                )
        
        # Summary
        self.stdout.write(self.style.SUCCESS(f'\n📈 Summary:'))
        self.stdout.write(f'  • Total active subscriptions: {subscriptions_to_check.count()}')
        self.stdout.write(f'  • Expired by date: {len(expired_by_date)}')
        self.stdout.write(f'  • Depleted tokens: {len(depleted_tokens)}')
        self.stdout.write(f'  • Low tokens (warnings): {len(low_tokens)}')
        
        # Handle deactivations
        if not dry_run:
            self.stdout.write(self.style.SUCCESS(f'\n🔧 Processing deactivations...'))
            
            # Always deactivate date-expired subscriptions
            for subscription in expired_by_date:
                self._deactivate_subscription(
                    subscription,
                    reason='Subscription end_date has passed'
                )
            
            # Only deactivate zero-token subscriptions if flag is set
            if deactivate_zero:
                for subscription in depleted_tokens:
                    self._deactivate_subscription(
                        subscription,
                        reason='Tokens depleted to zero'
                    )
                self.stdout.write(
                    self.style.SUCCESS(
                        f'✅ Deactivated {len(depleted_tokens)} subscriptions with zero tokens'
                    )
                )
            else:
                self.stdout.write(
                    self.style.WARNING(
                        f'⚠️  Skipping {len(depleted_tokens)} zero-token subscriptions '
                        f'(use --deactivate-zero-tokens to process them)'
                    )
                )
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'✅ Deactivated {len(expired_by_date)} date-expired subscriptions'
                )
            )
        else:
            self.stdout.write(
                self.style.WARNING(
                    f'\n🔍 DRY RUN: Would deactivate {len(expired_by_date)} date-expired subscriptions'
                )
            )
            if deactivate_zero:
                self.stdout.write(
                    self.style.WARNING(
                        f'🔍 DRY RUN: Would deactivate {len(depleted_tokens)} zero-token subscriptions'
                    )
                )
        
        self.stdout.write(self.style.SUCCESS(f'\n✅ Check complete!\n'))
    
    def _deactivate_subscription(self, subscription, reason):
        """Helper to deactivate a subscription with proper logging"""
        try:
            subscription.deactivate_subscription(reason=reason)
            logger.warning(
                f'Deactivated subscription {subscription.id} for user {subscription.user.username}: {reason}'
            )
        except Exception as e:
            logger.error(
                f'Error deactivating subscription {subscription.id} for user {subscription.user.username}: {e}'
            )
            self.stdout.write(
                self.style.ERROR(
                    f'❌ Error deactivating subscription {subscription.id}: {e}'
                )
            )

