import requests
import logging
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from settings.models import InstagramChannel

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Convert short-lived Instagram tokens to long-lived tokens for all channels'

    def add_arguments(self, parser):
        parser.add_argument(
            '--channel-id',
            type=int,
            help='Convert token for specific channel ID only',
        )
        parser.add_argument(
            '--check-only',
            action='store_true',
            help='Only check token status without converting',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force conversion even if token appears to be long-lived',
        )

    def handle(self, *args, **options):
        channel_id = options.get('channel_id')
        check_only = options.get('check_only')
        force = options.get('force')
        
        self.stdout.write(
            self.style.SUCCESS('🔄 Instagram Token Conversion Tool\n')
        )

        if channel_id:
            try:
                channel = InstagramChannel.objects.get(id=channel_id, is_connect=True)
                channels = [channel]
                self.stdout.write(f"🎯 Processing specific channel: {channel.username}")
            except InstagramChannel.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f"❌ Channel with ID {channel_id} not found or not connected")
                )
                return
        else:
            channels = InstagramChannel.objects.filter(is_connect=True)
            self.stdout.write(f"🔍 Found {channels.count()} connected Instagram channels")

        if not channels:
            self.stdout.write(
                self.style.WARNING("⚠️ No connected Instagram channels found")
            )
            return

        success_count = 0
        error_count = 0
        already_long_lived_count = 0

        for channel in channels:
            self.stdout.write(f"\n📷 Processing: {channel.username} (User: {channel.user.email})")
            
            if not channel.access_token:
                self.stdout.write(
                    self.style.ERROR(f"   ❌ No access token found for {channel.username}")
                )
                error_count += 1
                continue

            # Check if token is likely already long-lived
            if not force and self._is_likely_long_lived_token(channel):
                self.stdout.write(
                    self.style.SUCCESS(f"   ✅ Token appears to be long-lived for {channel.username}")
                )
                already_long_lived_count += 1
                continue

            if check_only:
                token_status = self._check_token_type(channel.access_token)
                if token_status == 'long_lived':
                    self.stdout.write(
                        self.style.SUCCESS(f"   ✅ Token is already long-lived for {channel.username}")
                    )
                    already_long_lived_count += 1
                elif token_status == 'short_lived':
                    self.stdout.write(
                        self.style.WARNING(f"   ⏱️ Token is short-lived for {channel.username} - needs conversion")
                    )
                    error_count += 1
                else:
                    self.stdout.write(
                        self.style.ERROR(f"   ❓ Cannot determine token type for {channel.username}")
                    )
                    error_count += 1
                continue

            # Convert token
            new_token, expires_in = self._convert_to_long_lived_token(channel.access_token)
            
            if new_token:
                # Update channel with new token
                old_token = channel.access_token
                channel.access_token = new_token
                
                if expires_in:
                    try:
                        expiration_time = timezone.now() + timedelta(seconds=int(expires_in))
                        channel.token_expires_at = expiration_time
                        days = expires_in // (24 * 3600)
                        hours = (expires_in % (24 * 3600)) // 3600
                        self.stdout.write(f"   📅 New token expires in: {days} days, {hours} hours")
                    except Exception:
                        self.stdout.write(f"   📅 New token expires in: {expires_in} seconds")
                
                channel.save()
                
                self.stdout.write(
                    self.style.SUCCESS(f"   ✅ Successfully converted token for {channel.username}")
                )
                success_count += 1
            else:
                self.stdout.write(
                    self.style.ERROR(f"   ❌ Failed to convert token for {channel.username}")
                )
                error_count += 1

        # Summary
        self.stdout.write(f"\n📊 Summary:")
        self.stdout.write(f"   ✅ Converted: {success_count}")
        self.stdout.write(f"   ✅ Already long-lived: {already_long_lived_count}")
        self.stdout.write(f"   ❌ Errors: {error_count}")
        
        if check_only:
            self.stdout.write(f"\n💡 Run without --check-only to convert tokens")
        if not force:
            self.stdout.write(f"💡 Use --force to convert even apparently long-lived tokens")

    def _is_likely_long_lived_token(self, channel):
        """
        Check if token is likely already long-lived based on stored data
        """
        try:
            if hasattr(channel, 'token_expires_at') and channel.token_expires_at:
                now = timezone.now()
                if channel.token_expires_at > now:
                    time_left = channel.token_expires_at - now
                    days_left = time_left.days
                    # If token expires in more than 7 days, it's likely long-lived
                    if days_left > 7:
                        return True
            return False
        except Exception:
            return False

    def _check_token_type(self, access_token):
        """
        Try to determine if token is short-lived or long-lived by testing with Instagram Graph API
        """
        try:
            # Test the token by making a simple request to Instagram Graph API
            test_url = "https://graph.instagram.com/me"
            test_params = {
                'fields': 'id,username',
                'access_token': access_token
            }
            
            response = requests.get(test_url, params=test_params, timeout=10)
            
            if response.status_code == 200:
                # Token is valid, but we can't easily determine if it's short or long-lived
                # from Instagram Graph API directly. 
                # We'll attempt to refresh it - if refresh fails, it's likely short-lived
                refresh_test = self._test_token_refresh_capability(access_token)
                
                if refresh_test == 'can_refresh':
                    return 'long_lived'  # Only long-lived tokens can be refreshed
                elif refresh_test == 'cannot_refresh':
                    return 'short_lived'  # Short-lived tokens cannot be refreshed
                else:
                    # If refresh test is inconclusive, assume it needs conversion
                    return 'short_lived'
            
            elif response.status_code == 400:
                error_data = response.json()
                error_code = error_data.get('error', {}).get('code')
                
                if error_code == 190:  # Token expired or invalid
                    return 'expired'
                    
            return 'unknown'
            
        except Exception as e:
            logger.error(f"Error checking token type: {e}")
            return 'unknown'
    
    def _test_token_refresh_capability(self, access_token):
        """
        Test if token can be refreshed (only long-lived tokens can be refreshed)
        """
        try:
            # Try to refresh the token
            refresh_url = "https://graph.instagram.com/refresh_access_token"
            refresh_params = {
                'grant_type': 'ig_refresh_token',
                'access_token': access_token
            }
            
            response = requests.get(refresh_url, params=refresh_params, timeout=10)
            
            if response.status_code == 200:
                return 'can_refresh'  # Token can be refreshed, it's long-lived
            else:
                error_data = response.json()
                error_message = error_data.get('error', {}).get('message', '')
                
                # Check for specific error messages that indicate short-lived token
                if 'short-lived' in error_message.lower() or 'cannot refresh' in error_message.lower():
                    return 'cannot_refresh'  # Token cannot be refreshed, it's short-lived
                
                return 'unknown'
                
        except Exception as e:
            logger.error(f"Error testing token refresh capability: {e}")
            return 'unknown'

    def _convert_to_long_lived_token(self, short_lived_token):
        """
        Convert short-lived token to long-lived token using Instagram Graph API
        """
        try:
            url = 'https://graph.instagram.com/access_token'
            params = {
                'grant_type': 'ig_exchange_token',
                'client_secret': '071f08aea723183951494234746982e4',
                'access_token': short_lived_token
            }
            
            self.stdout.write(f"   🔄 Converting token to long-lived...")
            response = requests.get(url, params=params, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                new_token = data.get('access_token')
                expires_in = data.get('expires_in')
                
                if new_token:
                    self.stdout.write(f"   ✅ Token converted successfully")
                    return new_token, expires_in
                else:
                    self.stdout.write(f"   ❌ No access_token in response: {data}")
                    return None, None
            else:
                error_data = response.json() if response.content else {}
                self.stdout.write(f"   ❌ Conversion failed: {response.status_code} - {error_data}")
                return None, None
                
        except Exception as e:
            self.stdout.write(f"   ❌ Error during conversion: {e}")
            return None, None