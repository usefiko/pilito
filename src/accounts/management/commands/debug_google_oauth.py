from django.core.management.base import BaseCommand
from accounts.services.google_oauth import GoogleOAuthService
from accounts.serializers.google_oauth import GoogleOAuthCodeSerializer, GoogleOAuthLoginSerializer
from django.contrib.auth import get_user_model
from django.db import transaction
import logging
import traceback

User = get_user_model()
logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Debug Google OAuth user creation issues'

    def add_arguments(self, parser):
        parser.add_argument(
            '--test-user-creation',
            action='store_true',
            help='Test user creation with mock Google data'
        )
        parser.add_argument(
            '--check-database',
            action='store_true',
            help='Check database for Google users'
        )
        parser.add_argument(
            '--simulate-callback',
            action='store_true',
            help='Simulate Google callback with mock data'
        )

    def handle(self, *args, **options):
        self.stdout.write("🔍 Debugging Google OAuth user creation...")
        
        if options['check_database']:
            self.check_google_users()
        
        if options['test_user_creation']:
            self.test_user_creation()
        
        if options['simulate_callback']:
            self.simulate_callback()
        
        if not any([options['check_database'], options['test_user_creation'], options['simulate_callback']]):
            self.check_google_users()
            self.test_user_creation()

    def check_google_users(self):
        """Check existing Google users in database"""
        self.stdout.write("📊 Checking existing Google users...")
        
        google_users = User.objects.filter(is_google_user=True)
        total_users = User.objects.count()
        
        self.stdout.write(f"👥 Total users: {total_users}")
        self.stdout.write(f"🔗 Google users: {google_users.count()}")
        
        if google_users.exists():
            self.stdout.write("📋 Recent Google users:")
            for user in google_users.order_by('-created_at')[:5]:
                self.stdout.write(f"  - {user.email} (ID: {user.id}, Google ID: {user.google_id})")
        else:
            self.stdout.write("❌ No Google users found")

    def test_user_creation(self):
        """Test user creation with mock Google data"""
        self.stdout.write("🧪 Testing user creation with mock Google data...")
        
        # Mock user data that would come from Google
        mock_user_data = {
            'google_id': f'test_google_id_{__import__("time").time()}',
            'email': f'test_{int(__import__("time").time())}@example.com',
            'first_name': 'Test',
            'last_name': 'User',
            'google_avatar_url': 'https://example.com/avatar.jpg',
            'email_verified': True
        }
        
        try:
            # Test the _create_google_user method from serializer
            serializer = GoogleOAuthLoginSerializer()
            
            self.stdout.write(f"📧 Creating user with email: {mock_user_data['email']}")
            self.stdout.write(f"🆔 Google ID: {mock_user_data['google_id']}")
            
            with transaction.atomic():
                user = serializer._create_google_user(mock_user_data)
                
                self.stdout.write(self.style.SUCCESS("✅ User created successfully!"))
                self.stdout.write(f"👤 User ID: {user.id}")
                self.stdout.write(f"📧 Email: {user.email}")
                self.stdout.write(f"👤 Name: {user.first_name} {user.last_name}")
                self.stdout.write(f"🆔 Google ID: {user.google_id}")
                self.stdout.write(f"🔗 Is Google user: {user.is_google_user}")
                self.stdout.write(f"✉️ Email confirmed: {user.email_confirmed}")
                self.stdout.write(f"🔐 Has usable password: {user.has_usable_password()}")
                
                # Test login token generation
                from accounts.functions.jwt import login
                access_token, refresh_token = login(user)
                self.stdout.write(f"🎫 Tokens generated successfully")
                
                # Clean up test user
                user.delete()
                self.stdout.write("🗑️ Test user cleaned up")
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ User creation failed: {str(e)}"))
            self.stdout.write(self.style.ERROR(f"📋 Full error:\n{traceback.format_exc()}"))

    def simulate_callback(self):
        """Simulate the Google OAuth callback process"""
        self.stdout.write("🔄 Simulating Google OAuth callback...")
        
        # Mock data that would come from a real Google OAuth callback
        mock_user_data = {
            'google_id': f'callback_test_{int(__import__("time").time())}',
            'email': f'callback_{int(__import__("time").time())}@gmail.com',
            'first_name': 'Callback',
            'last_name': 'Test',
            'google_avatar_url': 'https://lh3.googleusercontent.com/test',
            'email_verified': True
        }
        
        try:
            # Simulate the complete callback flow
            self.stdout.write("1️⃣ Testing user lookup by Google ID...")
            
            # Check if user exists by Google ID (should not exist)
            try:
                existing_user = User.objects.get(google_id=mock_user_data['google_id'])
                self.stdout.write(f"👤 Found existing user by Google ID: {existing_user.email}")
            except User.DoesNotExist:
                self.stdout.write("✅ No existing user found by Google ID (expected)")
            
            self.stdout.write("2️⃣ Testing user lookup by email...")
            
            # Check if user exists by email
            try:
                existing_user = User.objects.get(email=mock_user_data['email'])
                self.stdout.write(f"👤 Found existing user by email: {existing_user.email}")
                self.stdout.write("🔗 Would link existing account with Google")
            except User.DoesNotExist:
                self.stdout.write("✅ No existing user found by email (expected for new user)")
            
            self.stdout.write("3️⃣ Testing complete OAuth flow...")
            
            # Test the complete serializer flow
            serializer = GoogleOAuthLoginSerializer()
            
            with transaction.atomic():
                # Simulate the validated_data that would come from token verification
                validated_data = {'id_token': mock_user_data}
                
                result = serializer.create(validated_data)
                
                self.stdout.write(self.style.SUCCESS("✅ Complete OAuth flow successful!"))
                self.stdout.write(f"👤 User: {result['user'].email}")
                self.stdout.write(f"🎫 Access token: {result['access_token'][:20]}...")
                self.stdout.write(f"🔄 Refresh token: {result['refresh_token'][:20]}...")
                self.stdout.write(f"💬 Message: {result['message']}")
                
                # Clean up
                result['user'].delete()
                self.stdout.write("🗑️ Test user cleaned up")
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Callback simulation failed: {str(e)}"))
            self.stdout.write(self.style.ERROR(f"📋 Full error:\n{traceback.format_exc()}"))

    def check_configuration(self):
        """Check Google OAuth configuration"""
        self.stdout.write("⚙️ Checking Google OAuth configuration...")
        
        from django.conf import settings
        
        config_items = [
            ('GOOGLE_OAUTH2_CLIENT_ID', getattr(settings, 'GOOGLE_OAUTH2_CLIENT_ID', None)),
            ('GOOGLE_OAUTH2_CLIENT_SECRET', getattr(settings, 'GOOGLE_OAUTH2_CLIENT_SECRET', None)),
            ('GOOGLE_OAUTH2_REDIRECT_URI', getattr(settings, 'GOOGLE_OAUTH2_REDIRECT_URI', None)),
            ('GOOGLE_OAUTH2_FRONTEND_REDIRECT', getattr(settings, 'GOOGLE_OAUTH2_FRONTEND_REDIRECT', None)),
        ]
        
        for name, value in config_items:
            if value:
                display_value = value if 'SECRET' not in name else '*' * 20
                self.stdout.write(f"✅ {name}: {display_value}")
            else:
                self.stdout.write(self.style.ERROR(f"❌ {name}: Not configured"))
