import json
import sys
from django.core.management.base import BaseCommand
from django.conf import settings
from accounts.functions.jwt import login, validate_token, claim_token
from accounts.models import User
from message.models import Conversation, Customer
import redis
from django.test.utils import override_settings
from channels.testing import ChannelsLiveServerTestCase


class Command(BaseCommand):
    help = 'Check WebSocket configuration and connectivity without external websockets library'

    def add_arguments(self, parser):
        parser.add_argument(
            '--user-email',
            type=str,
            help='Email of user to test with'
        )
        parser.add_argument(
            '--conversation-id',
            type=str,
            help='Conversation ID to test'
        )

    def handle(self, *args, **options):
        self.stdout.write("🔍 Checking WebSocket Configuration...")
        
        # Test Redis connection
        redis_ok = self.test_redis_connection()
        
        # Test Django settings
        settings_ok = self.test_django_settings()
        
        # Test user and conversation if provided
        auth_ok = True
        if options['user_email'] and options['conversation_id']:
            auth_ok = self.test_user_conversation_access(
                options['user_email'], 
                options['conversation_id']
            )
        
        # Test JWT token generation
        token_ok = self.test_jwt_generation(options.get('user_email'))
        
        # Overall status
        self.stdout.write("\n" + "="*50)
        if redis_ok and settings_ok and auth_ok and token_ok:
            self.stdout.write(
                self.style.SUCCESS("✅ همه تنظیمات صحیح است! WebSocket باید کار کند.")
            )
            self.stdout.write(
                "\n💡 اگر هنوز خطای 403 می‌گیرید، احتمالاً مشکل از:"
            )
            self.stdout.write("   - پیکربندی Nginx")
            self.stdout.write("   - CORS origins در frontend")
            self.stdout.write("   - Mixed content (HTTP/HTTPS)")
            
        else:
            self.stdout.write(
                self.style.ERROR("❌ برخی تنظیمات مشکل دارند. لطفاً موارد بالا را بررسی کنید.")
            )

    def test_redis_connection(self):
        """Test Redis connectivity"""
        self.stdout.write("\n📊 Testing Redis connection...")
        
        try:
            # Get Redis URL from settings
            channel_layers = getattr(settings, 'CHANNEL_LAYERS', {})
            default_config = channel_layers.get('default', {})
            redis_hosts = default_config.get('CONFIG', {}).get('hosts', ['redis://localhost:6379'])
            redis_url = redis_hosts[0] if redis_hosts else 'redis://localhost:6379'
            
            self.stdout.write(f"   Redis URL: {redis_url}")
            
            # Connect to Redis
            r = redis.from_url(redis_url)
            r.ping()
            
            # Test basic operations
            test_key = 'websocket_config_test'
            r.set(test_key, 'success', ex=10)  # Expire in 10 seconds
            result = r.get(test_key)
            r.delete(test_key)
            
            if result == b'success':
                self.stdout.write(
                    self.style.SUCCESS("   ✅ Redis connection successful")
                )
                return True
            else:
                self.stdout.write(
                    self.style.ERROR("   ❌ Redis operation failed")
                )
                return False
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"   ❌ Redis connection failed: {e}")
            )
            self.stdout.write(
                self.style.WARNING(
                    "   💡 Suggestion: Check REDIS_URL environment variable and Redis server status"
                )
            )
            return False

    def test_django_settings(self):
        """Test Django settings for WebSocket"""
        self.stdout.write("\n⚙️  Testing Django settings...")
        
        issues = []
        
        # Check ALLOWED_HOSTS
        allowed_hosts = getattr(settings, 'ALLOWED_HOSTS', [])
        if not allowed_hosts:
            issues.append("ALLOWED_HOSTS is empty")
        elif '*' in allowed_hosts:
            self.stdout.write(
                self.style.WARNING("   ⚠️  ALLOWED_HOSTS includes '*' - consider being more specific in production")
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(f"   ✅ ALLOWED_HOSTS configured: {allowed_hosts}")
            )
        
        # Check CHANNEL_LAYERS
        channel_layers = getattr(settings, 'CHANNEL_LAYERS', {})
        if not channel_layers:
            issues.append("CHANNEL_LAYERS not configured")
        else:
            backend = channel_layers.get('default', {}).get('BACKEND')
            if 'redis' in backend.lower():
                self.stdout.write(
                    self.style.SUCCESS("   ✅ CHANNEL_LAYERS configured with Redis")
                )
            else:
                issues.append(f"CHANNEL_LAYERS backend not Redis: {backend}")
        
        # Check ASGI_APPLICATION
        asgi_app = getattr(settings, 'ASGI_APPLICATION', None)
        if not asgi_app:
            issues.append("ASGI_APPLICATION not configured")
        elif 'core.asgi' in asgi_app or 'core.routing' in asgi_app:
            self.stdout.write(
                self.style.SUCCESS(f"   ✅ ASGI_APPLICATION configured: {asgi_app}")
            )
        else:
            self.stdout.write(
                self.style.WARNING(f"   ⚠️  Unexpected ASGI_APPLICATION: {asgi_app}")
            )
        
        # Check CORS settings
        cors_origins = getattr(settings, 'CORS_ALLOWED_ORIGINS', [])
        cors_allow_all = getattr(settings, 'CORS_ORIGIN_ALLOW_ALL', False)
        
        if cors_allow_all:
            self.stdout.write(
                self.style.WARNING("   ⚠️  CORS_ORIGIN_ALLOW_ALL is True - not recommended for production")
            )
        elif cors_origins:
            self.stdout.write(
                self.style.SUCCESS(f"   ✅ CORS_ALLOWED_ORIGINS configured: {len(cors_origins)} origins")
            )
            for origin in cors_origins[:3]:  # Show first 3
                self.stdout.write(f"      - {origin}")
        else:
            issues.append("CORS_ALLOWED_ORIGINS not configured")
        
        # Check if in DEBUG mode
        debug_mode = getattr(settings, 'DEBUG', False)
        if debug_mode:
            self.stdout.write(
                self.style.WARNING("   ⚠️  DEBUG=True - make sure this is intended")
            )
        
        if issues:
            for issue in issues:
                self.stdout.write(self.style.ERROR(f"   ❌ {issue}"))
            return False
        
        return True

    def test_user_conversation_access(self, user_email, conversation_id):
        """Test user access to conversation"""
        self.stdout.write("\n👤 Testing user and conversation access...")
        
        try:
            # Check user exists
            user = User.objects.get(email=user_email)
            self.stdout.write(
                self.style.SUCCESS(f"   ✅ User found: {user.email}")
            )
            
            # Check conversation exists and user has access
            try:
                conversation = Conversation.objects.get(id=conversation_id, user=user)
                self.stdout.write(
                    self.style.SUCCESS(f"   ✅ User has access to conversation {conversation_id}")
                )
                
                # Show conversation details
                customer_name = f"{conversation.customer.first_name} {conversation.customer.last_name}".strip()
                self.stdout.write(f"      Customer: {customer_name}")
                self.stdout.write(f"      Source: {conversation.source}")
                self.stdout.write(f"      Status: {conversation.status}")
                
                return True
                
            except Conversation.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f"   ❌ User {user_email} does not have access to conversation {conversation_id}")
                )
                
                # Show available conversations for this user
                user_conversations = Conversation.objects.filter(user=user)[:5]
                if user_conversations:
                    self.stdout.write("   📋 Available conversations for this user:")
                    for conv in user_conversations:
                        customer_name = f"{conv.customer.first_name} {conv.customer.last_name}".strip()
                        self.stdout.write(f"      - {conv.id}: {customer_name} ({conv.source})")
                else:
                    self.stdout.write("   📋 No conversations found for this user")
                
                return False
                
        except User.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f"   ❌ User {user_email} not found")
            )
            
            # Show available users (first 5)
            users = User.objects.all()[:5]
            if users:
                self.stdout.write("   📋 Available users (first 5):")
                for user in users:
                    self.stdout.write(f"      - {user.email}")
            
            return False

    def test_jwt_generation(self, user_email=None):
        """Test JWT token generation"""
        self.stdout.write("\n🔑 Testing JWT token generation...")
        
        try:
            if user_email:
                user = User.objects.get(email=user_email)
            else:
                # Use first available user
                user = User.objects.first()
                if not user:
                    self.stdout.write(
                        self.style.ERROR("   ❌ No users found in database")
                    )
                    return False
            
            # Generate tokens using login function
            access_token, refresh_token = login(user)
            
            if access_token and len(access_token) > 20:  # Basic validation
                self.stdout.write(
                    self.style.SUCCESS("   ✅ JWT token generated successfully")
                )
                self.stdout.write(f"      Access token length: {len(access_token)} characters")
                self.stdout.write(f"      Token starts with: {access_token[:20]}...")
                
                # Validate token
                if validate_token(access_token):
                    payload = claim_token(access_token)
                    self.stdout.write(
                        self.style.SUCCESS("   ✅ JWT token validation successful")
                    )
                    self.stdout.write(f"      User ID in token: {payload.get('user_id')}")
                    return True
                else:
                    self.stdout.write(
                        self.style.ERROR("   ❌ JWT token validation failed")
                    )
                    return False
            else:
                self.stdout.write(
                    self.style.ERROR("   ❌ JWT token generation failed")
                )
                return False
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"   ❌ JWT token test failed: {e}")
            )
            return False

    def provide_troubleshooting_tips(self):
        """Provide specific troubleshooting tips"""
        self.stdout.write("\n🔧 Troubleshooting Tips:")
        
        self.stdout.write("1. Frontend Connection:")
        self.stdout.write("   const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';")
        self.stdout.write("   const wsUrl = `${protocol}//${window.location.host}/ws/chat/${conversationId}/?token=${token}`;")
        
        self.stdout.write("\n2. Check Browser Console:")
        self.stdout.write("   F12 > Network Tab > Filter WS > Check WebSocket connections")
        
        self.stdout.write("\n3. Test with curl:")
        self.stdout.write("   curl -i -N -H 'Connection: Upgrade' -H 'Upgrade: websocket' \\")
        self.stdout.write("        -H 'Sec-WebSocket-Key: test' -H 'Sec-WebSocket-Version: 13' \\")
        self.stdout.write("        'https://your-domain.com/ws/chat/CONV_ID/?token=TOKEN'")
        
        self.stdout.write("\n4. Check Nginx logs:")
        self.stdout.write("   sudo tail -f /var/log/nginx/error.log")
        
        self.stdout.write("\n5. Check Django logs:")
        self.stdout.write("   tail -f /app/logs/django.log")

    def list_example_usage(self):
        """Show example usage"""
        self.stdout.write("\n📝 Example Usage:")
        self.stdout.write("   python manage.py check_websocket_config")
        self.stdout.write("   python manage.py check_websocket_config --user-email user@example.com --conversation-id ABC123") 