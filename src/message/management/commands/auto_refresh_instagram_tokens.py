import requests
import logging
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from settings.models import InstagramChannel

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Automatically refresh Instagram tokens that are close to expiration'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days-before-expiry',
            type=int,
            default=7,
            help='Refresh tokens that expire within this many days (default: 7)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be refreshed without actually doing it',
        )
        parser.add_argument(
            '--force-all',
            action='store_true',
            help='Refresh all tokens regardless of expiry status',
        )

    def handle(self, *args, **options):
        days_before_expiry = options['days_before_expiry']
        dry_run = options['dry_run']
        force_all = options['force_all']
        
        self.stdout.write(
            self.style.SUCCESS('🔄 Automatic Instagram Token Refresh\n')
        )

        # Get all connected Instagram channels
        channels = InstagramChannel.objects.filter(is_connect=True)
        self.stdout.write(f"🔍 Found {channels.count()} connected Instagram channels")

        if not channels:
            self.stdout.write(
                self.style.WARNING("⚠️ No connected Instagram channels found")
            )
            return

        # Determine which tokens need refreshing
        channels_to_refresh = []
        now = timezone.now()
        threshold_date = now + timedelta(days=days_before_expiry)

        for channel in channels:
            should_refresh = False
            reason = ""

            if not channel.access_token:
                self.stdout.write(f"❌ {channel.username}: No access token")
                continue

            if force_all:
                should_refresh = True
                reason = "forced refresh"
            elif hasattr(channel, 'token_expires_at') and channel.token_expires_at:
                if channel.token_expires_at <= threshold_date:
                    should_refresh = True
                    if channel.token_expires_at <= now:
                        reason = f"expired {abs((channel.token_expires_at - now).days)} days ago"
                    else:
                        days_left = (channel.token_expires_at - now).days
                        hours_left = ((channel.token_expires_at - now).seconds // 3600)
                        reason = f"expires in {days_left} days, {hours_left} hours"
                else:
                    days_left = (channel.token_expires_at - now).days
                    self.stdout.write(f"✅ {channel.username}: Token valid for {days_left} more days")
            else:
                # No expiration data - check token validity and potentially refresh
                if self._should_refresh_unknown_expiry_token(channel):
                    should_refresh = True
                    reason = "unknown expiry, token validation suggested refresh"
                else:
                    self.stdout.write(f"✅ {channel.username}: Token appears valid (no expiry data)")

            if should_refresh:
                channels_to_refresh.append((channel, reason))
                self.stdout.write(f"🔄 {channel.username}: Scheduled for refresh ({reason})")

        if not channels_to_refresh:
            self.stdout.write(
                self.style.SUCCESS("\n✅ All tokens are up to date!")
            )
            return

        self.stdout.write(f"\n📋 {len(channels_to_refresh)} tokens scheduled for refresh")

        if dry_run:
            self.stdout.write(
                self.style.WARNING("\n🔍 DRY RUN - No actual changes will be made")
            )
            for channel, reason in channels_to_refresh:
                self.stdout.write(f"   Would refresh: {channel.username} ({reason})")
            return

        # Perform actual refresh
        success_count = 0
        error_count = 0

        for channel, reason in channels_to_refresh:
            self.stdout.write(f"\n🔄 Refreshing: {channel.username} ({reason})")
            
            success = self._refresh_channel_token(channel)
            if success:
                success_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f"   ✅ Successfully refreshed token for {channel.username}")
                )
            else:
                error_count += 1
                self.stdout.write(
                    self.style.ERROR(f"   ❌ Failed to refresh token for {channel.username}")
                )

        # Summary
        self.stdout.write(f"\n📊 Refresh Summary:")
        self.stdout.write(f"   ✅ Successful: {success_count}")
        self.stdout.write(f"   ❌ Failed: {error_count}")
        
        if error_count > 0:
            self.stdout.write(
                self.style.WARNING(f"\n⚠️ {error_count} tokens failed to refresh. Users may need to reconnect.")
            )

    def _should_refresh_unknown_expiry_token(self, channel):
        """
        Check if a token with unknown expiry should be refreshed
        """
        try:
            # Simple test - try to make an API call to see if token works
            url = f"https://graph.instagram.com/me"
            params = {
                'fields': 'id,username',
                'access_token': channel.access_token
            }
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                # Token works, but we might want to refresh it proactively
                # Check if channel was created recently (might have short-lived token)
                if hasattr(channel, 'updated_at'):
                    time_since_update = timezone.now() - channel.updated_at
                    if time_since_update.days < 1:  # Updated less than 24 hours ago
                        return True  # Might be a fresh short-lived token
                return False  # Token works and isn't fresh
            elif response.status_code == 400:
                error_data = response.json()
                error_code = error_data.get('error', {}).get('code')
                if error_code == 190:  # Token expired/invalid
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking token validity for {channel.username}: {e}")
            return False

    def _refresh_channel_token(self, channel):
        """
        Refresh token for a specific channel
        """
        try:
            # Try Facebook Graph API first (for short-lived to long-lived conversion)
            new_token, expires_in = self._exchange_for_long_lived_token(channel.access_token)
            
            if new_token:
                self._update_channel_token(channel, new_token, expires_in)
                return True
            
            # If Facebook API failed, try Instagram API
            new_token, expires_in = self._refresh_long_lived_instagram_token(channel.access_token)
            
            if new_token:
                self._update_channel_token(channel, new_token, expires_in)
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error refreshing token for {channel.username}: {e}")
            return False

    def _exchange_for_long_lived_token(self, short_lived_token):
        """Exchange short-lived token for long-lived token using Instagram Graph API"""
        try:
            url = 'https://graph.instagram.com/access_token'
            params = {
                'grant_type': 'ig_exchange_token',
                'client_secret': '071f08aea723183951494234746982e4',
                'access_token': short_lived_token
            }
            
            response = requests.get(url, params=params, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                return data.get('access_token'), data.get('expires_in')
            else:
                return None, None
                
        except Exception:
            return None, None

    def _refresh_long_lived_instagram_token(self, current_token):
        """Refresh Instagram long-lived token"""
        try:
            url = "https://graph.instagram.com/refresh_access_token"
            params = {
                'grant_type': 'ig_refresh_token',
                'access_token': current_token
            }
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                return data.get('access_token'), data.get('expires_in')
            else:
                return None, None
                
        except Exception:
            return None, None

    def _update_channel_token(self, channel, new_token, expires_in):
        """Update channel with new token and expiry"""
        try:
            channel.access_token = new_token
            
            if expires_in:
                expiration_time = timezone.now() + timedelta(seconds=int(expires_in))
                channel.token_expires_at = expiration_time
                days = expires_in // (24 * 3600)
                hours = (expires_in % (24 * 3600)) // 3600
                self.stdout.write(f"   📅 New token expires in: {days} days, {hours} hours")
            
            channel.save()
            
        except Exception as e:
            logger.error(f"Error updating channel token: {e}")
            raise