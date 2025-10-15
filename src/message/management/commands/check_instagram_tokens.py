from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
import requests
import logging

from settings.models import InstagramChannel

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Check Instagram token status and health for all channels'

    def add_arguments(self, parser):
        parser.add_argument(
            '--fix-expired',
            action='store_true',
            help='Attempt to refresh expired tokens',
        )
        parser.add_argument(
            '--disable-expired',
            action='store_true',
            help='Disable channels with expired tokens',
        )

    def handle(self, *args, **options):
        self.stdout.write('🔍 Checking Instagram token status...\n')
        
        channels = InstagramChannel.objects.all()
        if not channels:
            self.stdout.write(self.style.WARNING('❌ No Instagram channels found'))
            return

        now = timezone.now()
        total_channels = 0
        valid_tokens = 0
        expired_tokens = 0
        unknown_tokens = 0
        issues_found = []

        for channel in channels:
            total_channels += 1
            self.stdout.write(f'\n📋 Channel: {channel.username} (User: {channel.user.email})')
            self.stdout.write(f'   ID: {channel.id}')
            self.stdout.write(f'   Connected: {channel.is_connect}')
            
            if not channel.access_token:
                self.stdout.write(self.style.ERROR('   ❌ No access token'))
                issues_found.append(f"{channel.username}: No access token")
                continue

            # Check expiration date
            if hasattr(channel, 'token_expires_at') and channel.token_expires_at:
                time_until_expiry = channel.token_expires_at - now
                
                if channel.token_expires_at <= now:
                    days_expired = (now - channel.token_expires_at).days
                    self.stdout.write(self.style.ERROR(f'   🚨 EXPIRED: {days_expired} days ago ({channel.token_expires_at})'))
                    expired_tokens += 1
                    issues_found.append(f"{channel.username}: Expired {days_expired} days ago")
                    
                    if options['disable_expired']:
                        channel.is_connect = False
                        channel.save()
                        self.stdout.write(self.style.WARNING(f'   ⚠️ Disabled channel due to expired token'))
                    
                elif time_until_expiry.days <= 7:
                    self.stdout.write(self.style.WARNING(f'   ⚠️ EXPIRING SOON: in {time_until_expiry.days} days ({channel.token_expires_at})'))
                    issues_found.append(f"{channel.username}: Expires in {time_until_expiry.days} days")
                else:
                    self.stdout.write(self.style.SUCCESS(f'   ✅ Valid for {time_until_expiry.days} more days'))
                    valid_tokens += 1
            else:
                self.stdout.write('   ⚠️ No expiration date - testing token...')
                
                # Test token by making API call
                token_valid = self._test_token(channel.access_token)
                if token_valid:
                    self.stdout.write(self.style.SUCCESS('   ✅ Token appears valid (no expiry data)'))
                    unknown_tokens += 1
                else:
                    self.stdout.write(self.style.ERROR('   ❌ Token test failed - likely expired'))
                    expired_tokens += 1
                    issues_found.append(f"{channel.username}: Token test failed")
                    
                    if options['disable_expired']:
                        channel.is_connect = False
                        channel.save()
                        self.stdout.write(self.style.WARNING(f'   ⚠️ Disabled channel due to failed token'))

            # Show last update time
            if hasattr(channel, 'updated_at'):
                days_since_update = (now - channel.updated_at).days
                self.stdout.write(f'   📅 Last updated: {days_since_update} days ago')

        # Summary
        self.stdout.write('\n' + '='*50)
        self.stdout.write('📊 SUMMARY:')
        self.stdout.write(f'   Total channels: {total_channels}')
        self.stdout.write(f'   Valid tokens: {valid_tokens}')
        self.stdout.write(f'   Expired tokens: {expired_tokens}')
        self.stdout.write(f'   Unknown status: {unknown_tokens}')

        if issues_found:
            self.stdout.write('\n🚨 ISSUES FOUND:')
            for issue in issues_found:
                self.stdout.write(f'   - {issue}')
        else:
            self.stdout.write(self.style.SUCCESS('\n✅ All tokens appear healthy!'))

        if expired_tokens > 0:
            self.stdout.write('\n💡 RECOMMENDATIONS:')
            self.stdout.write('   1. Users with expired tokens need to reconnect their Instagram accounts')
            self.stdout.write('   2. Run: python manage.py auto_refresh_instagram_tokens to attempt automatic refresh')
            self.stdout.write('   3. Check celery worker status to ensure automatic refresh tasks are running')

    def _test_token(self, access_token):
        """Test if a token is valid by making a simple API call"""
        try:
            url = "https://graph.instagram.com/me"
            params = {
                'fields': 'id,username',
                'access_token': access_token
            }
            
            response = requests.get(url, params=params, timeout=10)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Error testing token: {e}")
            return False