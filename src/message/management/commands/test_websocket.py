import asyncio
import websockets
import json
import sys
from django.core.management.base import BaseCommand
from django.conf import settings
from accounts.functions.jwt import login
from accounts.models import User
from message.models import Conversation
import redis


class Command(BaseCommand):
    help = 'Test WebSocket connections and diagnose 403 errors'

    def add_arguments(self, parser):
        parser.add_argument(
            '--host',
            type=str,
            default='localhost:8000',
            help='WebSocket host to test (default: localhost:8000)'
        )
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
        parser.add_argument(
            '--ssl',
            action='store_true',
            help='Use WSS instead of WS'
        )

    def handle(self, *args, **options):
        self.stdout.write("🔍 Testing WebSocket Connection...")
        
        # Test Redis connection first
        self.test_redis_connection()
        
        # Test Django settings
        self.test_django_settings()
        
        # Test WebSocket connection
        if options['user_email'] and options['conversation_id']:
            asyncio.run(self.test_websocket_connection(
                host=options['host'],
                user_email=options['user_email'],
                conversation_id=options['conversation_id'],
                use_ssl=options['ssl']
            ))
        else:
            self.stdout.write(
                self.style.WARNING(
                    "⚠️  برای تست کامل WebSocket، --user-email و --conversation-id را ارائه دهید"
                )
            )

    def test_redis_connection(self):
        """Test Redis connectivity"""
        self.stdout.write("📊 Testing Redis connection...")
        
        try:
            # Get Redis URL from settings
            redis_url = getattr(settings, 'CHANNEL_LAYERS', {}).get('default', {}).get('CONFIG', {}).get('hosts', ['redis://localhost:6379'])[0]
            
            # Connect to Redis
            r = redis.from_url(redis_url)
            r.ping()
            
            # Test basic operations
            r.set('websocket_test', 'success')
            result = r.get('websocket_test')
            r.delete('websocket_test')
            
            if result == b'success':
                self.stdout.write(
                    self.style.SUCCESS("✅ Redis connection successful")
                )
            else:
                self.stdout.write(
                    self.style.ERROR("❌ Redis operation failed")
                )
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"❌ Redis connection failed: {e}")
            )
            self.stdout.write(
                self.style.WARNING(
                    "💡 Suggestion: Check REDIS_URL environment variable and Redis server status"
                )
            )

    def test_django_settings(self):
        """Test Django settings for WebSocket"""
        self.stdout.write("⚙️  Testing Django settings...")
        
        # Check ALLOWED_HOSTS
        allowed_hosts = getattr(settings, 'ALLOWED_HOSTS', [])
        if '*' in allowed_hosts:
            self.stdout.write(
                self.style.WARNING("⚠️  ALLOWED_HOSTS includes '*' - consider being more specific in production")
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(f"✅ ALLOWED_HOSTS configured: {allowed_hosts}")
            )
        
        # Check CHANNEL_LAYERS
        channel_layers = getattr(settings, 'CHANNEL_LAYERS', {})
        if channel_layers:
            self.stdout.write(
                self.style.SUCCESS("✅ CHANNEL_LAYERS configured")
            )
        else:
            self.stdout.write(
                self.style.ERROR("❌ CHANNEL_LAYERS not configured")
            )
        
        # Check ASGI_APPLICATION
        asgi_app = getattr(settings, 'ASGI_APPLICATION', None)
        if asgi_app:
            self.stdout.write(
                self.style.SUCCESS(f"✅ ASGI_APPLICATION configured: {asgi_app}")
            )
        else:
            self.stdout.write(
                self.style.ERROR("❌ ASGI_APPLICATION not configured")
            )
        
        # Check CORS settings
        cors_origins = getattr(settings, 'CORS_ALLOWED_ORIGINS', [])
        if cors_origins:
            self.stdout.write(
                self.style.SUCCESS(f"✅ CORS_ALLOWED_ORIGINS configured: {len(cors_origins)} origins")
            )
        else:
            self.stdout.write(
                self.style.WARNING("⚠️  CORS_ALLOWED_ORIGINS not configured")
            )

    async def test_websocket_connection(self, host, user_email, conversation_id, use_ssl=False):
        """Test actual WebSocket connection"""
        self.stdout.write("🔌 Testing WebSocket connection...")
        
        try:
            # Get user and generate token
            user = User.objects.get(email=user_email)
            access_token, refresh_token = login(user)
            token = access_token
            
            # Check conversation access
            try:
                conversation = Conversation.objects.get(id=conversation_id, user=user)
                self.stdout.write(
                    self.style.SUCCESS(f"✅ User has access to conversation {conversation_id}")
                )
            except Conversation.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f"❌ User {user_email} does not have access to conversation {conversation_id}")
                )
                return
            
            # Build WebSocket URL
            protocol = 'wss' if use_ssl else 'ws'
            ws_url = f"{protocol}://{host}/ws/chat/{conversation_id}/?token={token}"
            
            self.stdout.write(f"🔗 Connecting to: {ws_url}")
            
            # Test connection
            async with websockets.connect(
                ws_url,
                timeout=10,
                extra_headers={
                    'Origin': f"{'https' if use_ssl else 'http'}://{host.split(':')[0]}",
                }
            ) as websocket:
                self.stdout.write(
                    self.style.SUCCESS("✅ WebSocket connection successful!")
                )
                
                # Test sending a message
                test_message = {
                    'type': 'chat_message',
                    'content': 'Test message from management command'
                }
                
                await websocket.send(json.dumps(test_message))
                self.stdout.write("📤 Test message sent")
                
                # Wait for response
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=5)
                    response_data = json.loads(response)
                    
                    if response_data.get('type') == 'chat_message':
                        self.stdout.write(
                            self.style.SUCCESS("✅ Received valid response")
                        )
                    else:
                        self.stdout.write(
                            self.style.WARNING(f"⚠️  Unexpected response type: {response_data.get('type')}")
                        )
                        
                except asyncio.TimeoutError:
                    self.stdout.write(
                        self.style.WARNING("⚠️  No response received within 5 seconds")
                    )
                
        except User.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f"❌ User {user_email} not found")
            )
        except websockets.exceptions.ConnectionClosed as e:
            self.stdout.write(
                self.style.ERROR(f"❌ WebSocket connection closed: {e.code} - {e.reason}")
            )
            self.provide_403_troubleshooting()
        except websockets.exceptions.InvalidHandshake as e:
            self.stdout.write(
                self.style.ERROR(f"❌ WebSocket handshake failed: {e}")
            )
            self.provide_403_troubleshooting()
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"❌ WebSocket connection failed: {e}")
            )
            self.provide_403_troubleshooting()

    def provide_403_troubleshooting(self):
        """Provide troubleshooting suggestions for 403 errors"""
        self.stdout.write("\n🔧 Troubleshooting 403 WebSocket Errors:")
        self.stdout.write("1. Check ALLOWED_HOSTS includes your domain")
        self.stdout.write("2. Check CORS_ALLOWED_ORIGINS includes your frontend origin")
        self.stdout.write("3. Verify JWT token is valid and not expired")
        self.stdout.write("4. Check nginx configuration if using reverse proxy")
        self.stdout.write("5. Ensure Redis is running and accessible")
        self.stdout.write("6. Check that user has access to the conversation")
        self.stdout.write("7. Verify Origin header matches allowed origins")
        self.stdout.write("\n📋 Common nginx WebSocket configuration:")
        self.stdout.write("""
location /ws/ {
    proxy_pass http://backend;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}
        """) 