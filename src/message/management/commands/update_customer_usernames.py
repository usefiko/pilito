from django.core.management.base import BaseCommand
from django.db import transaction
from message.models import Customer
from settings.models import TelegramChannel, InstagramChannel
from message.services.telegram_service import TelegramService
from message.insta import InstaWebhook
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Update existing customers with usernames from Telegram and Instagram'

    def add_arguments(self, parser):
        parser.add_argument(
            '--source',
            type=str,
            choices=['telegram', 'instagram', 'all'],
            default='all',
            help='Source to update usernames from (default: all)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Perform a dry run without making changes'
        )

    def handle(self, *args, **options):
        source = options['source']
        dry_run = options['dry_run']
        
        if dry_run:
            self.stdout.write("🔍 DRY RUN MODE - No changes will be made")
        
        self.stdout.write(f"🚀 Starting username update for source: {source}")
        
        if source in ['telegram', 'all']:
            self.update_telegram_usernames(dry_run)
        
        if source in ['instagram', 'all']:
            self.update_instagram_usernames(dry_run)
        
        self.stdout.write("✅ Username update completed!")

    def update_telegram_usernames(self, dry_run=False):
        """Update usernames for Telegram customers"""
        self.stdout.write("📱 Updating Telegram customer usernames...")
        
        telegram_customers = Customer.objects.filter(
            source='telegram',
            username__isnull=True  # Only update customers without usernames
        )
        
        self.stdout.write(f"Found {telegram_customers.count()} Telegram customers without usernames")
        
        # Get first available Telegram channel for API access
        telegram_channel = TelegramChannel.objects.filter(is_connect=True).first()
        if not telegram_channel:
            self.stdout.write("❌ No connected Telegram channels found")
            return
        
        telegram_service = TelegramService(telegram_channel.bot_token)
        updated_count = 0
        
        for customer in telegram_customers:
            try:
                if customer.source_id:
                    # Try to get user info from Telegram API
                    user_info = telegram_service.get_user_info(customer.source_id)
                    if user_info and user_info.get('username'):
                        username = user_info['username']
                        self.stdout.write(f"  Found username @{username} for {customer}")
                        
                        if not dry_run:
                            customer.username = username
                            customer.save()
                        
                        updated_count += 1
                    else:
                        self.stdout.write(f"  No username found for {customer}")
                        
            except Exception as e:
                logger.error(f"Error updating Telegram customer {customer.id}: {e}")
                self.stdout.write(f"  ❌ Error updating {customer}: {e}")
        
        action = "Would update" if dry_run else "Updated"
        self.stdout.write(f"📱 {action} {updated_count} Telegram customers")

    def update_instagram_usernames(self, dry_run=False):
        """Update usernames for Instagram customers"""
        self.stdout.write("📷 Updating Instagram customer usernames...")
        
        instagram_customers = Customer.objects.filter(
            source='instagram',
            username__isnull=True  # Only update customers without usernames
        )
        
        self.stdout.write(f"Found {instagram_customers.count()} Instagram customers without usernames")
        
        # Get first available Instagram channel for API access
        instagram_channel = InstagramChannel.objects.filter(
            is_connect=True,
            access_token__isnull=False
        ).first()
        
        if not instagram_channel:
            self.stdout.write("❌ No connected Instagram channels with access tokens found")
            return
        
        insta_webhook = InstaWebhook()
        updated_count = 0
        
        for customer in instagram_customers:
            try:
                if customer.source_id:
                    # Try to get user info from Instagram Graph API
                    user_details = insta_webhook._get_instagram_user_details(
                        customer.source_id, 
                        instagram_channel.access_token
                    )
                    
                    if user_details and user_details.get('username'):
                        username = user_details['username']
                        self.stdout.write(f"  Found username @{username} for {customer}")
                        
                        if not dry_run:
                            customer.username = username
                            customer.save()
                        
                        updated_count += 1
                    else:
                        self.stdout.write(f"  No username found for {customer}")
                        
            except Exception as e:
                logger.error(f"Error updating Instagram customer {customer.id}: {e}")
                self.stdout.write(f"  ❌ Error updating {customer}: {e}")
        
        action = "Would update" if dry_run else "Updated"
        self.stdout.write(f"📷 {action} {updated_count} Instagram customers") 