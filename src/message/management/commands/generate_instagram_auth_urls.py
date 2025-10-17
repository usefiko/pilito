from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from settings.models import InstagramChannel
from urllib.parse import urlencode

User = get_user_model()

class Command(BaseCommand):
    help = 'Generate Instagram authorization URLs for users who need to reconnect'

    def add_arguments(self, parser):
        parser.add_argument(
            '--user-email',
            type=str,
            help='Generate auth URL for specific user email',
        )
        parser.add_argument(
            '--all-expired',
            action='store_true',
            help='Generate auth URLs for all users with expired tokens',
        )

    def handle(self, *args, **options):
        user_email = options.get('user_email')
        all_expired = options.get('all_expired')
        
        self.stdout.write(
            self.style.SUCCESS('🔗 Instagram Reconnection URL Generator\n')
        )

        if user_email:
            try:
                user = User.objects.get(email=user_email)
                users = [user]
                self.stdout.write(f"🎯 Generating auth URL for: {user.email}")
            except User.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f"❌ User with email {user_email} not found")
                )
                return
        elif all_expired:
            # Get all users with Instagram channels
            channel_user_ids = InstagramChannel.objects.filter(is_connect=True).values_list('user_id', flat=True)
            users = User.objects.filter(id__in=channel_user_ids)
            self.stdout.write(f"🔍 Generating auth URLs for {users.count()} users with Instagram channels")
        else:
            self.stdout.write(
                self.style.ERROR("❌ Please specify --user-email or --all-expired")
            )
            return

        if not users:
            self.stdout.write(
                self.style.WARNING("⚠️ No users found")
            )
            return

        for user in users:
            self.stdout.write(f"\n👤 User: {user.email} (ID: {user.id})")
            
            # Check if user has Instagram channel
            channel = InstagramChannel.objects.filter(user=user, is_connect=True).first()
            if channel:
                self.stdout.write(f"   📷 Instagram: @{channel.username}")
            else:
                self.stdout.write(f"   ⚠️ No connected Instagram channel found")
                continue
            
            # Generate auth URL
            auth_url = self._generate_instagram_auth_url(user.id)
            self.stdout.write(f"   🔗 Reconnection URL:")
            self.stdout.write(f"      {auth_url}")
            self.stdout.write(f"   📋 Instructions:")
            self.stdout.write(f"      1. Send this URL to the user")
            self.stdout.write(f"      2. User visits URL and authorizes Instagram access")
            self.stdout.write(f"      3. System will automatically update the token")

        self.stdout.write(f"\n💡 After users reconnect, run: python manage.py refresh_instagram_tokens --check-only")

    def _generate_instagram_auth_url(self, user_id):
        """Generate Instagram OAuth URL with user_id in state parameter"""
        base_url = "https://www.instagram.com/oauth/authorize"
        params = {
            'client_id': '1426281428401641',
            'redirect_uri': 'https://api.pilito.com/api/v1/message/instagram-callback/',
            'response_type': 'code',
            'scope': 'instagram_business_basic,instagram_business_manage_messages,instagram_business_manage_comments,instagram_business_content_publish,instagram_business_manage_insights',
            'state': str(user_id),  # Pass user_id in state parameter
            'force_reauth': 'true'  # Force re-authentication
        }
        
        return f"{base_url}?{urlencode(params)}" 