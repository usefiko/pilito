import requests
import logging
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from settings.models import InstagramChannel

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Refresh Instagram access tokens for all connected channels'

    def add_arguments(self, parser):
        parser.add_argument(
            '--channel-id',
            type=int,
            help='Refresh token for specific channel ID only',
        )
        parser.add_argument(
            '--check-only',
            action='store_true',
            help='Only check token status without refreshing',
        )

    def handle(self, *args, **options):
        channel_id = options.get('channel_id')
        check_only = options.get('check_only')
        
        self.stdout.write(
            self.style.SUCCESS('🔄 Instagram Token Management Tool\n')
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

        for channel in channels:
            self.stdout.write(f"\n📷 Processing: {channel.username} (User: {channel.user.email})")
            
            # Show current expiration if available
            try:
                if hasattr(channel, 'token_expires_at') and channel.token_expires_at:
                    now = timezone.now()
                    if channel.token_expires_at > now:
                        time_left = channel.token_expires_at - now
                        days_left = time_left.days
                        hours_left = time_left.seconds // 3600
                        self.stdout.write(f"   📅 Current token expires in: {days_left} days, {hours_left} hours")
                    else:
                        self.stdout.write(
                            self.style.WARNING(f"   ⏰ Token expired {abs((channel.token_expires_at - now).days)} days ago")
                        )
                else:
                    self.stdout.write(f"   📅 Token expiration: Unknown")
            except Exception:
                # Field doesn't exist yet
                self.stdout.write(f"   📅 Token expiration: Unknown (pending migration)")
            
            if not channel.access_token:
                self.stdout.write(
                    self.style.ERROR(f"   ❌ No access token found for {channel.username}")
                )
                error_count += 1
                continue

            # Check token status first
            token_status = self._check_token_status(channel.access_token)
            
            if token_status == 'valid':
                self.stdout.write(
                    self.style.SUCCESS(f"   ✅ Token is valid for {channel.username}")
                )
                if not check_only:
                    # Still try to refresh to extend expiration
                    new_token = self._refresh_token(channel)
                    if new_token:
                        self.stdout.write(
                            self.style.SUCCESS(f"   🔄 Token refreshed for {channel.username}")
                        )
                        success_count += 1
                    else:
                        error_count += 1
                else:
                    success_count += 1
                    
            elif token_status == 'expired':
                self.stdout.write(
                    self.style.ERROR(f"   ⏰ Token expired for {channel.username}")
                )
                if not check_only:
                    new_token = self._refresh_token(channel)
                    if new_token:
                        self.stdout.write(
                            self.style.SUCCESS(f"   ✅ Expired token refreshed for {channel.username}")
                        )
                        success_count += 1
                    else:
                        self.stdout.write(
                            self.style.ERROR(f"   ❌ Failed to refresh expired token for {channel.username}")
                        )
                        self.stdout.write(
                            self.style.WARNING(f"   🔗 User may need to reconnect their Instagram account")
                        )
                        error_count += 1
                else:
                    error_count += 1
                    
            else:  # 'invalid'
                self.stdout.write(
                    self.style.ERROR(f"   ❌ Invalid token for {channel.username}")
                )
                if not check_only:
                    self.stdout.write(
                        self.style.WARNING(f"   🔗 User needs to reconnect their Instagram account")
                    )
                error_count += 1

        # Summary
        self.stdout.write(f"\n📊 Summary:")
        self.stdout.write(f"   ✅ Success: {success_count}")
        self.stdout.write(f"   ❌ Errors: {error_count}")
        
        if check_only:
            self.stdout.write(f"\n💡 Run without --check-only to refresh tokens")
        else:
            self.stdout.write(f"\n💡 Use --check-only to only check status without refreshing")

    def _check_token_status(self, access_token):
        """Check if token is valid by making a test API call"""
        try:
            url = "https://graph.instagram.com/me"
            params = {
                'fields': 'id,username',
                'access_token': access_token
            }
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                return 'valid'
            elif response.status_code == 400:
                error_data = response.json()
                error_code = error_data.get('error', {}).get('code')
                if error_code == 190:  # Token expired/invalid
                    error_subcode = error_data.get('error', {}).get('error_subcode')
                    if error_subcode == 463:  # Token expired
                        return 'expired'
                    else:
                        return 'invalid'
            return 'invalid'
            
        except Exception as e:
            logger.error(f"Error checking token status: {e}")
            return 'invalid'

    def _refresh_token(self, channel):
        """Refresh Instagram token for a channel"""
        try:
            url = "https://graph.instagram.com/refresh_access_token"
            
            params = {
                'grant_type': 'ig_refresh_token',
                'access_token': channel.access_token
            }
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                new_token = data.get('access_token')
                expires_in = data.get('expires_in', None)
                
                if new_token:
                    # Update the token in database
                    channel.access_token = new_token
                    
                    # Calculate and save expiration time
                    if expires_in:
                        try:
                            expiration_time = timezone.now() + timedelta(seconds=int(expires_in))
                            channel.token_expires_at = expiration_time
                            days = expires_in // (24 * 3600)
                            hours = (expires_in % (24 * 3600)) // 3600
                            self.stdout.write(f"   📅 New token expires in: {days} days, {hours} hours")
                            self.stdout.write(f"   📅 Expiration date: {expiration_time.strftime('%Y-%m-%d %H:%M:%S %Z')}")
                        except Exception:
                            # Field doesn't exist yet
                            days = expires_in // (24 * 3600)
                            hours = (expires_in % (24 * 3600)) // 3600
                            self.stdout.write(f"   📅 New token expires in: {days} days, {hours} hours")
                            self.stdout.write(f"   📅 Expiration tracking: Pending migration")
                    else:
                        self.stdout.write(f"   📅 New token expiration: Unknown")
                    
                    channel.save()
                    return new_token
                else:
                    self.stdout.write(f"   ❌ No access_token in response")
                    return None
            else:
                error_data = response.json() if response.content else {}
                self.stdout.write(f"   ❌ Refresh failed: {response.status_code} - {error_data}")
                return None
                
        except Exception as e:
            self.stdout.write(f"   ❌ Error refreshing token: {e}")
            return None 