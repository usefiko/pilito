from django.core.management.base import BaseCommand
from accounts.services.google_oauth import GoogleOAuthService
from accounts.serializers.google_oauth import GoogleOAuthCodeSerializer
from django.contrib.auth import get_user_model
import logging

User = get_user_model()
logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Test Google OAuth functionality'

    def add_arguments(self, parser):
        parser.add_argument(
            '--test-config',
            action='store_true',
            help='Test Google OAuth configuration'
        )
        parser.add_argument(
            '--test-token',
            type=str,
            help='Test ID token verification (provide test ID token)'
        )
        parser.add_argument(
            '--test-code',
            type=str,
            help='Test authorization code exchange (provide authorization code)'
        )

    def handle(self, *args, **options):
        self.stdout.write("🧪 Testing Google OAuth functionality...")
        
        if options['test_config']:
            self.test_configuration()
        
        if options['test_token']:
            self.test_id_token(options['test_token'])
        
        if options['test_code']:
            self.test_authorization_code(options['test_code'])
        
        if not any([options['test_config'], options['test_token'], options['test_code']]):
            self.test_configuration()

    def test_configuration(self):
        """Test Google OAuth configuration"""
        self.stdout.write("⚙️  Testing Google OAuth configuration...")
        
        from django.conf import settings
        
        client_id = getattr(settings, 'GOOGLE_OAUTH2_CLIENT_ID', None)
        client_secret = getattr(settings, 'GOOGLE_OAUTH2_CLIENT_SECRET', None)
        redirect_uri = getattr(settings, 'GOOGLE_OAUTH2_REDIRECT_URI', None)
        
        self.stdout.write(f"📋 Client ID: {client_id}")
        self.stdout.write(f"🔐 Client Secret: {'*' * 20 if client_secret else 'Not set'}")
        self.stdout.write(f"🔄 Redirect URI: {redirect_uri}")
        
        if not client_id:
            self.stdout.write(self.style.ERROR("❌ GOOGLE_OAUTH2_CLIENT_ID not configured"))
            return False
        
        if not client_secret:
            self.stdout.write(self.style.ERROR("❌ GOOGLE_OAUTH2_CLIENT_SECRET not configured"))
            return False
        
        if not redirect_uri:
            self.stdout.write(self.style.ERROR("❌ GOOGLE_OAUTH2_REDIRECT_URI not configured"))
            return False
        
        # Test auth URL generation
        try:
            auth_url = GoogleOAuthService.generate_auth_url()
            self.stdout.write(f"🔗 Generated auth URL: {auth_url[:100]}...")
            self.stdout.write(self.style.SUCCESS("✅ Configuration looks good!"))
            return True
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Error generating auth URL: {e}"))
            return False

    def test_id_token(self, id_token):
        """Test ID token verification"""
        self.stdout.write(f"🎫 Testing ID token verification...")
        
        try:
            user_data = GoogleOAuthService.verify_google_token(id_token)
            self.stdout.write(f"✅ Token verified successfully!")
            self.stdout.write(f"👤 User data: {user_data}")
            
            # Test user creation/login
            serializer = GoogleOAuthCodeSerializer()
            user = serializer._create_google_user(user_data)
            self.stdout.write(f"✅ User created: {user.email}")
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Token verification failed: {e}"))

    def test_authorization_code(self, code):
        """Test authorization code exchange"""
        self.stdout.write(f"🔄 Testing authorization code exchange...")
        
        try:
            token_data = GoogleOAuthService.exchange_code_for_tokens(code)
            self.stdout.write(f"✅ Code exchange successful!")
            self.stdout.write(f"🎫 Received tokens and user data")
            
            # Test serializer
            serializer = GoogleOAuthCodeSerializer(data={'code': code})
            if serializer.is_valid():
                result = serializer.create(serializer.validated_data)
                self.stdout.write(f"✅ User login/creation successful: {result['user'].email}")
            else:
                self.stdout.write(self.style.ERROR(f"❌ Serializer validation failed: {serializer.errors}"))
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Code exchange failed: {e}"))

    def test_user_creation_flow(self):
        """Test the complete user creation flow"""
        self.stdout.write("👤 Testing user creation flow...")
        
        # Mock user data that would come from Google
        mock_user_data = {
            'google_id': 'test_google_id_123',
            'email': 'test@example.com',
            'first_name': 'Test',
            'last_name': 'User',
            'google_avatar_url': 'https://example.com/avatar.jpg',
            'email_verified': True
        }
        
        try:
            # Check if user already exists
            if User.objects.filter(email=mock_user_data['email']).exists():
                User.objects.filter(email=mock_user_data['email']).delete()
                self.stdout.write("🗑️  Cleaned up existing test user")
            
            # Test user creation
            from accounts.serializers.google_oauth import GoogleOAuthLoginSerializer
            serializer = GoogleOAuthLoginSerializer()
            user = serializer._create_google_user(mock_user_data)
            
            self.stdout.write(f"✅ Test user created successfully!")
            self.stdout.write(f"📧 Email: {user.email}")
            self.stdout.write(f"👤 Name: {user.first_name} {user.last_name}")
            self.stdout.write(f"🆔 Google ID: {user.google_id}")
            self.stdout.write(f"✉️  Email confirmed: {user.email_confirmed}")
            
            # Clean up
            user.delete()
            self.stdout.write("🗑️  Cleaned up test user")
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ User creation test failed: {e}"))
            import traceback
            self.stdout.write(traceback.format_exc())
