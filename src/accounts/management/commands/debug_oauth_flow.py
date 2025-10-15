from django.core.management.base import BaseCommand
from accounts.services.google_oauth import GoogleOAuthService
from django.conf import settings
import requests
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Debug Google OAuth flow step by step'

    def add_arguments(self, parser):
        parser.add_argument(
            '--test-code',
            type=str,
            help='Test with a specific authorization code'
        )

    def handle(self, *args, **options):
        self.stdout.write("🔍 Debugging Google OAuth Flow...")
        
        # Step 1: Check configuration
        self.check_configuration()
        
        # Step 2: Test auth URL generation
        self.test_auth_url_generation()
        
        # Step 3: Test code exchange if provided
        if options['test_code']:
            self.test_code_exchange(options['test_code'])
        
        # Step 4: Show debugging info
        self.show_debugging_info()

    def check_configuration(self):
        """Check Google OAuth configuration"""
        self.stdout.write("\n⚙️ Configuration Check:")
        self.stdout.write("-" * 30)
        
        client_id = settings.GOOGLE_OAUTH2_CLIENT_ID
        client_secret = settings.GOOGLE_OAUTH2_CLIENT_SECRET
        redirect_uri = settings.GOOGLE_OAUTH2_REDIRECT_URI
        
        self.stdout.write(f"🆔 Client ID: {client_id}")
        self.stdout.write(f"🔐 Client Secret: {'*' * 20 if client_secret else 'NOT SET'}")
        self.stdout.write(f"🔄 Redirect URI: {redirect_uri}")
        
        # Validate configuration
        issues = []
        if not client_id:
            issues.append("Client ID not configured")
        if not client_secret:
            issues.append("Client Secret not configured")
        if not redirect_uri:
            issues.append("Redirect URI not configured")
        elif not redirect_uri.startswith('https://'):
            issues.append("Redirect URI should use HTTPS in production")
        
        if issues:
            for issue in issues:
                self.stdout.write(self.style.ERROR(f"❌ {issue}"))
        else:
            self.stdout.write(self.style.SUCCESS("✅ Configuration looks good"))

    def test_auth_url_generation(self):
        """Test auth URL generation"""
        self.stdout.write("\n🔗 Auth URL Generation:")
        self.stdout.write("-" * 30)
        
        try:
            auth_url = GoogleOAuthService.generate_auth_url("test_state")
            self.stdout.write("✅ Auth URL generated successfully")
            self.stdout.write(f"URL: {auth_url}")
            
            # Parse and validate the URL
            from urllib.parse import urlparse, parse_qs
            parsed = urlparse(auth_url)
            params = parse_qs(parsed.query)
            
            self.stdout.write("\n📋 Auth URL Parameters:")
            for key, value in params.items():
                self.stdout.write(f"  {key}: {value[0] if value else 'N/A'}")
            
            # Check critical parameters
            expected_params = ['client_id', 'redirect_uri', 'scope', 'response_type']
            for param in expected_params:
                if param in params:
                    self.stdout.write(f"✅ {param}: Present")
                else:
                    self.stdout.write(self.style.ERROR(f"❌ {param}: Missing"))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Auth URL generation failed: {e}"))

    def test_code_exchange(self, code):
        """Test authorization code exchange"""
        self.stdout.write(f"\n🔄 Testing Code Exchange:")
        self.stdout.write("-" * 30)
        self.stdout.write(f"Code: {code[:20]}...")
        
        try:
            # Test the raw token exchange
            token_url = "https://oauth2.googleapis.com/token"
            data = {
                'client_id': settings.GOOGLE_OAUTH2_CLIENT_ID,
                'client_secret': settings.GOOGLE_OAUTH2_CLIENT_SECRET,
                'code': code,
                'grant_type': 'authorization_code',
                'redirect_uri': settings.GOOGLE_OAUTH2_REDIRECT_URI,
            }
            
            self.stdout.write("📤 Sending token exchange request...")
            self.stdout.write(f"  URL: {token_url}")
            self.stdout.write(f"  Client ID: {data['client_id']}")
            self.stdout.write(f"  Redirect URI: {data['redirect_uri']}")
            self.stdout.write(f"  Grant Type: {data['grant_type']}")
            
            response = requests.post(token_url, data=data)
            
            self.stdout.write(f"📥 Response Status: {response.status_code}")
            
            if response.status_code == 200:
                token_data = response.json()
                self.stdout.write("✅ Token exchange successful!")
                self.stdout.write(f"  Access Token: {token_data.get('access_token', 'N/A')[:20]}...")
                self.stdout.write(f"  ID Token: {'Present' if token_data.get('id_token') else 'Missing'}")
                self.stdout.write(f"  Refresh Token: {'Present' if token_data.get('refresh_token') else 'Missing'}")
            else:
                error_data = response.json() if response.content else {}
                self.stdout.write(self.style.ERROR(f"❌ Token exchange failed"))
                self.stdout.write(self.style.ERROR(f"  Error: {error_data.get('error', 'Unknown')}"))
                self.stdout.write(self.style.ERROR(f"  Description: {error_data.get('error_description', 'No description')}"))
                
                # Common error explanations
                error_type = error_data.get('error', '')
                if error_type == 'invalid_grant':
                    self.stdout.write("\n💡 Common causes of 'invalid_grant':")
                    self.stdout.write("  1. Authorization code has expired (they expire in ~10 minutes)")
                    self.stdout.write("  2. Code has already been used")
                    self.stdout.write("  3. Redirect URI mismatch between auth URL and token exchange")
                    self.stdout.write("  4. Client ID/Secret mismatch")
                elif error_type == 'invalid_client':
                    self.stdout.write("\n💡 'invalid_client' usually means:")
                    self.stdout.write("  1. Client ID or Client Secret is incorrect")
                    self.stdout.write("  2. Client is not properly configured in Google Console")
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Code exchange error: {e}"))

    def show_debugging_info(self):
        """Show debugging information"""
        self.stdout.write("\n🔧 Debugging Information:")
        self.stdout.write("-" * 30)
        
        self.stdout.write("📋 To debug OAuth issues:")
        self.stdout.write("1. Check Google OAuth Console configuration:")
        self.stdout.write("   - Authorized redirect URIs must match exactly")
        self.stdout.write("   - Client ID and Secret must be correct")
        self.stdout.write("2. Monitor server logs during OAuth attempts:")
        self.stdout.write("   docker logs -f <container> | grep -i 'google\\|oauth'")
        self.stdout.write("3. Test with fresh authorization codes:")
        self.stdout.write("   - Authorization codes expire quickly")
        self.stdout.write("   - Each code can only be used once")
        
        self.stdout.write(f"\n📊 Current redirect URI: {settings.GOOGLE_OAUTH2_REDIRECT_URI}")
        self.stdout.write("⚠️  This MUST match exactly in Google OAuth Console!")
        
        # Show test URLs
        self.stdout.write("\n🔗 Test URLs:")
        base_url = "https://api.fiko.net" if "api.fiko.net" in settings.GOOGLE_OAUTH2_REDIRECT_URI else "http://localhost:8000"
        self.stdout.write(f"  Auth URL: {base_url}/api/v1/usr/google/auth-url")
        self.stdout.write(f"  Test endpoint: {base_url}/api/v1/usr/google/test")
        self.stdout.write(f"  Callback URL: {settings.GOOGLE_OAUTH2_REDIRECT_URI}")
