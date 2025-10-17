from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
import logging
import time

User = get_user_model()
logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Monitor Google OAuth attempts and debug issues in production'

    def add_arguments(self, parser):
        parser.add_argument(
            '--watch',
            action='store_true',
            help='Watch for OAuth attempts in real-time'
        )
        parser.add_argument(
            '--check-recent',
            action='store_true',
            help='Check recent OAuth activity'
        )

    def handle(self, *args, **options):
        self.stdout.write("🔍 Google OAuth Production Monitor")
        self.stdout.write("=" * 50)
        
        if options['watch']:
            self.watch_oauth_attempts()
        elif options['check_recent']:
            self.check_recent_activity()
        else:
            self.check_recent_activity()
            self.show_monitoring_info()

    def check_recent_activity(self):
        """Check recent OAuth activity"""
        self.stdout.write("📊 Recent OAuth Activity:")
        self.stdout.write("-" * 30)
        
        # Check recent users (last 24 hours)
        recent_cutoff = timezone.now() - timedelta(hours=24)
        
        recent_users = User.objects.filter(created_at__gte=recent_cutoff)
        google_users = recent_users.filter(is_google_user=True)
        regular_users = recent_users.filter(is_google_user=False)
        
        self.stdout.write(f"📅 Last 24 hours:")
        self.stdout.write(f"   - Total new users: {recent_users.count()}")
        self.stdout.write(f"   - Google OAuth users: {google_users.count()}")
        self.stdout.write(f"   - Regular users: {regular_users.count()}")
        
        if google_users.exists():
            self.stdout.write("\n✅ Recent Google OAuth users:")
            for user in google_users.order_by('-created_at')[:5]:
                self.stdout.write(f"   - {user.email} at {user.created_at}")
        else:
            self.stdout.write("\n❌ No recent Google OAuth users found")
            
        # Check for failed attempts (users with Gmail but not OAuth)
        gmail_users = recent_users.filter(
            email__icontains='@gmail.com',
            is_google_user=False
        )
        
        if gmail_users.exists():
            self.stdout.write(f"\n⚠️  Gmail users who didn't use OAuth: {gmail_users.count()}")
            for user in gmail_users[:3]:
                self.stdout.write(f"   - {user.email}")

    def watch_oauth_attempts(self):
        """Watch for OAuth attempts in real-time"""
        self.stdout.write("👀 Watching for OAuth attempts...")
        self.stdout.write("Press Ctrl+C to stop")
        self.stdout.write("-" * 30)
        
        initial_count = User.objects.filter(is_google_user=True).count()
        self.stdout.write(f"Starting Google user count: {initial_count}")
        
        try:
            while True:
                time.sleep(5)  # Check every 5 seconds
                
                current_count = User.objects.filter(is_google_user=True).count()
                
                if current_count > initial_count:
                    # New Google user found!
                    new_users = User.objects.filter(
                        is_google_user=True,
                        created_at__gte=timezone.now() - timedelta(seconds=10)
                    ).order_by('-created_at')
                    
                    for user in new_users:
                        self.stdout.write(
                            self.style.SUCCESS(
                                f"🎉 NEW GOOGLE USER: {user.email} at {user.created_at}"
                            )
                        )
                    
                    initial_count = current_count
                
                # Show a heartbeat every minute
                if int(time.time()) % 60 == 0:
                    self.stdout.write(f"💓 Monitoring... (Google users: {current_count})")
                    
        except KeyboardInterrupt:
            self.stdout.write("\n⏹️  Monitoring stopped")

    def show_monitoring_info(self):
        """Show monitoring information"""
        self.stdout.write("\n🛠️  Production OAuth Monitoring:")
        self.stdout.write("-" * 40)
        
        from django.conf import settings
        
        self.stdout.write("📋 Current configuration:")
        self.stdout.write(f"   - Redirect URI: {settings.GOOGLE_OAUTH2_REDIRECT_URI}")
        self.stdout.write(f"   - Frontend URI: {settings.GOOGLE_OAUTH2_FRONTEND_REDIRECT}")
        
        self.stdout.write("\n🔧 Debugging commands:")
        self.stdout.write("1. Monitor OAuth in real-time:")
        self.stdout.write("   python manage.py monitor_oauth --watch")
        
        self.stdout.write("\n2. Check recent activity:")
        self.stdout.write("   python manage.py monitor_oauth --check-recent")
        
        self.stdout.write("\n3. Monitor server logs:")
        self.stdout.write("   docker logs -f <container> | grep -i 'google\\|oauth'")
        
        self.stdout.write("\n4. Test OAuth endpoint externally:")
        self.stdout.write("   curl https://api.pilito.com/api/v1/usr/google/test")
        
        self.stdout.write("\n📊 If OAuth isn't working:")
        self.stdout.write("1. Google can't reach your server (most common)")
        self.stdout.write("2. Google OAuth Console misconfiguration")
        self.stdout.write("3. SSL/TLS certificate issues")
        self.stdout.write("4. Firewall blocking Google's requests")
        
        # Show total stats
        total_users = User.objects.count()
        google_users = User.objects.filter(is_google_user=True).count()
        
        self.stdout.write(f"\n📊 Total stats:")
        self.stdout.write(f"   - Total users: {total_users}")
        self.stdout.write(f"   - Google users: {google_users}")
        self.stdout.write(f"   - Google percentage: {(google_users/total_users*100):.1f}%" if total_users > 0 else "   - Google percentage: 0%")
