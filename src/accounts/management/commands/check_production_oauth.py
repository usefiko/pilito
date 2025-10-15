from django.core.management.base import BaseCommand
from django.conf import settings
from django.contrib.auth import get_user_model
from accounts.services.google_oauth import GoogleOAuthService
import requests
import logging

User = get_user_model()
logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Check production Google OAuth configuration and recent activity'

    def handle(self, *args, **options):
        self.stdout.write("🔍 Production Google OAuth Diagnostic")
        self.stdout.write("="*50)
        
        # Check configuration
        self.check_configuration()
        
        # Check recent activity
        self.check_recent_activity()
        
        # Check database
        self.check_database()
        
        # Provide recommendations
        self.provide_recommendations()

    def check_configuration(self):
        """Check Google OAuth configuration"""
        self.stdout.write("\n⚙️ Configuration Check:")
        self.stdout.write("-" * 30)
        
        config_items = [
            ('CLIENT_ID', settings.GOOGLE_OAUTH2_CLIENT_ID),
            ('CLIENT_SECRET', bool(settings.GOOGLE_OAUTH2_CLIENT_SECRET)),
            ('REDIRECT_URI', settings.GOOGLE_OAUTH2_REDIRECT_URI),
            ('FRONTEND_REDIRECT', settings.GOOGLE_OAUTH2_FRONTEND_REDIRECT),
        ]
        
        for name, value in config_items:
            if value:
                display_value = value if name != 'CLIENT_SECRET' else '✓ Configured'
                self.stdout.write(f"✅ {name}: {display_value}")
            else:
                self.stdout.write(self.style.ERROR(f"❌ {name}: Not configured"))
        
        # Test auth URL generation
        try:
            auth_url = GoogleOAuthService.generate_auth_url()
            self.stdout.write(f"✅ Auth URL generation: Working")
            self.stdout.write(f"   URL: {auth_url[:80]}...")
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Auth URL generation failed: {e}"))

    def check_recent_activity(self):
        """Check recent OAuth activity in logs"""
        self.stdout.write("\n📊 Recent OAuth Activity:")
        self.stdout.write("-" * 30)
        
        # Check recent Google users (last 24 hours)
        from django.utils import timezone
        from datetime import timedelta
        
        recent_cutoff = timezone.now() - timedelta(hours=24)
        recent_google_users = User.objects.filter(
            is_google_user=True,
            created_at__gte=recent_cutoff
        )
        
        self.stdout.write(f"🕐 Google users in last 24h: {recent_google_users.count()}")
        
        if recent_google_users.exists():
            for user in recent_google_users:
                self.stdout.write(f"  ✅ {user.email} (created: {user.created_at})")
        else:
            self.stdout.write("  ❌ No recent Google OAuth logins")

    def check_database(self):
        """Check database for Google users"""
        self.stdout.write("\n💾 Database Check:")
        self.stdout.write("-" * 30)
        
        total_users = User.objects.count()
        google_users = User.objects.filter(is_google_user=True)
        
        self.stdout.write(f"👥 Total users: {total_users}")
        self.stdout.write(f"🔗 Google users: {google_users.count()}")
        
        if google_users.exists():
            latest_google_user = google_users.order_by('-created_at').first()
            self.stdout.write(f"📅 Latest Google user: {latest_google_user.email}")
            self.stdout.write(f"   Created: {latest_google_user.created_at}")
        
        # Check for users with failed OAuth attempts (users without google_id but with certain patterns)
        potential_failed_oauth = User.objects.filter(
            email__icontains='@gmail.com',
            is_google_user=False
        ).exclude(google_id__isnull=False)
        
        if potential_failed_oauth.exists():
            self.stdout.write(f"⚠️  Potential failed OAuth attempts: {potential_failed_oauth.count()}")

    def provide_recommendations(self):
        """Provide troubleshooting recommendations"""
        self.stdout.write("\n💡 Troubleshooting Recommendations:")
        self.stdout.write("-" * 40)
        
        # Check if any Google users exist
        google_users_exist = User.objects.filter(is_google_user=True).exists()
        
        if not google_users_exist:
            self.stdout.write("🚨 No Google users found - OAuth callback likely not working")
            self.stdout.write("\n📋 Check these items:")
            self.stdout.write("1. Google OAuth Console configuration:")
            self.stdout.write("   - Authorized redirect URIs must include:")
            self.stdout.write("     https://api.fiko.net/api/v1/usr/google/callback")
            self.stdout.write("2. DNS resolution:")
            self.stdout.write("   - Ensure api.fiko.net points to your server")
            self.stdout.write("3. SSL certificate:")
            self.stdout.write("   - Ensure HTTPS is working properly")
            self.stdout.write("4. Server accessibility:")
            self.stdout.write("   - Ensure port 443 is open and accessible")
            self.stdout.write("5. Network/firewall:")
            self.stdout.write("   - Ensure Google can reach your callback URL")
        else:
            latest_oauth = User.objects.filter(is_google_user=True).order_by('-created_at').first()
            time_since_last = timezone.now() - latest_oauth.created_at
            
            if time_since_last.days > 1:
                self.stdout.write(f"⚠️ Last Google OAuth was {time_since_last.days} days ago")
                self.stdout.write("   This might indicate a recent configuration issue")
            else:
                self.stdout.write("✅ Recent Google OAuth activity detected")
        
        self.stdout.write("\n🔧 Debugging commands:")
        self.stdout.write("- Monitor logs: docker logs -f <container> | grep -i google")
        self.stdout.write("- Test endpoint: curl https://api.fiko.net/api/v1/usr/google/test")
        self.stdout.write("- Check auth URL: curl https://api.fiko.net/api/v1/usr/google/auth-url")
        
        self.stdout.write(f"\n📊 Production OAuth Status: {'✅ Working' if google_users_exist else '❌ Not Working'}")
