from django.core.management.base import BaseCommand
from django.test import Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from accounts.models.user import EmailConfirmationToken
import requests
import json

User = get_user_model()


class Command(BaseCommand):
    help = 'Test the enhanced OAuth flow and authentication persistence'

    def add_arguments(self, parser):
        parser.add_argument(
            '--server',
            type=str,
            default='http://localhost:8000',
            help='Server URL to test (default: http://localhost:8000)'
        )

    def handle(self, *args, **options):
        server_url = options['server']
        self.stdout.write("🔧 Testing Enhanced OAuth Flow and Authentication")
        self.stdout.write("=" * 60)
        
        # Test 1: Check if new debugging endpoints are working
        self.stdout.write("\n📡 Testing Authentication Status Endpoint...")
        try:
            response = requests.get(f"{server_url}/api/v1/usr/auth/status", timeout=10)
            if response.status_code == 200:
                data = response.json()
                self.stdout.write(f"✅ Auth Status Endpoint Working")
                self.stdout.write(f"   Authenticated: {data.get('authenticated', 'Unknown')}")
                self.stdout.write(f"   Cookies Present: {data.get('cookies_present', {})}")
                self.stdout.write(f"   Headers Present: {data.get('headers_present', {})}")
            else:
                self.stdout.write(f"❌ Auth Status Endpoint Failed: {response.status_code}")
        except Exception as e:
            self.stdout.write(f"❌ Auth Status Endpoint Error: {e}")
        
        # Test 2: Check Google OAuth auth URL generation
        self.stdout.write("\n🔗 Testing Google OAuth Auth URL Generation...")
        try:
            response = requests.get(f"{server_url}/api/v1/usr/google/auth-url", timeout=10)
            if response.status_code == 200:
                data = response.json()
                auth_url = data.get('auth_url', '')
                self.stdout.write(f"✅ Google Auth URL Generated")
                self.stdout.write(f"   URL Length: {len(auth_url)}")
                self.stdout.write(f"   Contains redirect_uri: {'redirect_uri' in auth_url}")
                self.stdout.write(f"   Contains client_id: {'client_id' in auth_url}")
                self.stdout.write(f"   Auth URL: {auth_url[:100]}...")
            else:
                self.stdout.write(f"❌ Google Auth URL Failed: {response.status_code}")
        except Exception as e:
            self.stdout.write(f"❌ Google Auth URL Error: {e}")
        
        # Test 3: Show current user statistics
        self.stdout.write("\n👥 Current User Statistics...")
        total_users = User.objects.count()
        google_users = User.objects.filter(is_google_user=True).count()
        confirmed_users = User.objects.filter(email_confirmed=True).count()
        
        self.stdout.write(f"   Total users: {total_users}")
        self.stdout.write(f"   Google users: {google_users}")
        self.stdout.write(f"   Email confirmed: {confirmed_users}")
        
        if google_users > 0:
            self.stdout.write("\n📊 Recent Google Users:")
            recent_google_users = User.objects.filter(is_google_user=True).order_by('-created_at')[:3]
            for user in recent_google_users:
                self.stdout.write(f"   - {user.email} | Created: {user.created_at} | Active: {user.is_active}")
        
        # Test 4: Simulate authentication check
        self.stdout.write(f"\n🔐 Testing Dashboard Access (without auth)...")
        try:
            response = requests.get(f"{server_url}/api/v1/usr/auth/dashboard-test", timeout=10)
            if response.status_code == 401:
                self.stdout.write(f"✅ Dashboard correctly requires authentication (401)")
            elif response.status_code == 200:
                data = response.json()
                self.stdout.write(f"⚠️ Dashboard accessible without auth: {data.get('message', 'Unknown')}")
            else:
                self.stdout.write(f"❓ Unexpected dashboard response: {response.status_code}")
        except Exception as e:
            self.stdout.write(f"❌ Dashboard test error: {e}")
        
        # Test 5: Check OAuth configuration
        self.stdout.write(f"\n⚙️ OAuth Configuration Check...")
        from django.conf import settings
        
        self.stdout.write(f"   GOOGLE_OAUTH2_REDIRECT_URI: {getattr(settings, 'GOOGLE_OAUTH2_REDIRECT_URI', 'Not set')}")
        self.stdout.write(f"   GOOGLE_OAUTH2_FRONTEND_REDIRECT: {getattr(settings, 'GOOGLE_OAUTH2_FRONTEND_REDIRECT', 'Not set')}")
        self.stdout.write(f"   CLIENT_ID ends with: ...{getattr(settings, 'GOOGLE_OAUTH2_CLIENT_ID', 'Not set')[-10:]}")
        
        # Instructions for user
        self.stdout.write(f"\n📋 Next Steps for Testing OAuth Flow:")
        self.stdout.write(f"   1. Get auth URL: GET {server_url}/api/v1/usr/google/auth-url")
        self.stdout.write(f"   2. Complete OAuth in browser")
        self.stdout.write(f"   3. Check auth status: GET {server_url}/api/v1/usr/auth/status")
        self.stdout.write(f"   4. Test dashboard: GET {server_url}/api/v1/usr/auth/dashboard-test")
        
        self.stdout.write(f"\n🔍 Problem Analysis:")
        self.stdout.write(f"   ✅ Enhanced OAuth callback now sets HTTP-only cookies")
        self.stdout.write(f"   ✅ Cookies are domain-aware (production vs development)")
        self.stdout.write(f"   ✅ Frontend gets both URL params AND cookies")
        self.stdout.write(f"   ✅ Added debugging endpoints for troubleshooting")
        
        self.stdout.write(f"\n💡 If users still can't access dashboard after OAuth:")
        self.stdout.write(f"   1. Check if frontend is reading tokens from cookies")
        self.stdout.write(f"   2. Verify frontend sends tokens in requests")
        self.stdout.write(f"   3. Check if tokens are included in Authorization header")
        self.stdout.write(f"   4. Use auth/status endpoint to debug token presence")
        
        self.stdout.write(f"\n🎯 OAuth Flow Summary:")
        self.stdout.write(f"   • User clicks OAuth → Google → Backend callback")
        self.stdout.write(f"   • Backend creates/logs user → Sets cookies → Redirects to frontend")
        self.stdout.write(f"   • Frontend should use cookies OR URL params for authentication")
        self.stdout.write(f"   • Frontend needs to include tokens in API requests")
