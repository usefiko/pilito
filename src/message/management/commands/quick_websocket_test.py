import requests
import json
from django.core.management.base import BaseCommand
from django.conf import settings
from accounts.functions.jwt import login
from accounts.models import User
from message.models import Conversation


class Command(BaseCommand):
    help = 'Quick WebSocket handshake test using requests (no websockets library needed)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--host',
            type=str,
            default='localhost:8000',
            help='Host to test (e.g., api.pilito.com)'
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
            help='Use HTTPS/WSS'
        )

    def handle(self, *args, **options):
        self.stdout.write("🚀 Quick WebSocket Test...")
        
        if not options['user_email'] or not options['conversation_id']:
            self.stdout.write(
                self.style.ERROR("❌ --user-email و --conversation-id الزامی هستند")
            )
            return
        
        # Test WebSocket handshake
        success = self.test_websocket_handshake(
            host=options['host'],
            user_email=options['user_email'],
            conversation_id=options['conversation_id'],
            use_ssl=options['ssl']
        )
        
        if success:
            self.stdout.write(
                self.style.SUCCESS("✅ WebSocket handshake successful! سیستم باید کار کند.")
            )
        else:
            self.stdout.write(
                self.style.ERROR("❌ WebSocket handshake failed! لطفاً تنظیمات را بررسی کنید.")
            )

    def test_websocket_handshake(self, host, user_email, conversation_id, use_ssl=False):
        """Test WebSocket handshake using HTTP upgrade request"""
        self.stdout.write(f"\n🔌 Testing WebSocket handshake to {host}...")
        
        try:
            # Get user and generate token
            user = User.objects.get(email=user_email)
            access_token, refresh_token = login(user)
            token = access_token
            
            # Check conversation access
            try:
                conversation = Conversation.objects.get(id=conversation_id, user=user)
                self.stdout.write(
                    self.style.SUCCESS(f"   ✅ User has access to conversation {conversation_id}")
                )
            except Conversation.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f"   ❌ User {user_email} cannot access conversation {conversation_id}")
                )
                return False
            
            # Build URL
            protocol = 'https' if use_ssl else 'http'
            url = f"{protocol}://{host}/ws/chat/{conversation_id}/?token={token}"
            
            self.stdout.write(f"   🔗 Testing URL: {url}")
            
            # WebSocket handshake headers
            headers = {
                'Connection': 'Upgrade',
                'Upgrade': 'websocket',
                'Sec-WebSocket-Key': 'dGhlIHNhbXBsZSBub25jZQ==',
                'Sec-WebSocket-Version': '13',
                'Origin': f"{protocol}://{host.split(':')[0]}",
                'User-Agent': 'Django-WebSocket-Test/1.0'
            }
            
            # Try WebSocket handshake
            try:
                response = requests.get(url, headers=headers, timeout=10, allow_redirects=False)
                
                self.stdout.write(f"   📊 Response Status: {response.status_code}")
                self.stdout.write(f"   📋 Response Headers:")
                
                for key, value in response.headers.items():
                    if key.lower() in ['connection', 'upgrade', 'sec-websocket-accept', 'sec-websocket-protocol']:
                        self.stdout.write(f"      {key}: {value}")
                
                # Check response
                if response.status_code == 101:
                    self.stdout.write(
                        self.style.SUCCESS("   ✅ WebSocket handshake successful (101 Switching Protocols)")
                    )
                    return True
                elif response.status_code == 403:
                    self.stdout.write(
                        self.style.ERROR("   ❌ 403 Forbidden - اشکال در احراز هویت یا دسترسی")
                    )
                    self.diagnose_403_error(response)
                    return False
                elif response.status_code == 404:
                    self.stdout.write(
                        self.style.ERROR("   ❌ 404 Not Found - مسیر WebSocket پیدا نشد")
                    )
                    return False
                elif response.status_code == 400:
                    self.stdout.write(
                        self.style.ERROR("   ❌ 400 Bad Request - درخواست نامعتبر")
                    )
                    return False
                else:
                    self.stdout.write(
                        self.style.WARNING(f"   ⚠️  Unexpected status: {response.status_code}")
                    )
                    if response.text:
                        self.stdout.write(f"   📄 Response body: {response.text[:200]}...")
                    return False
                    
            except requests.exceptions.ConnectionError:
                self.stdout.write(
                    self.style.ERROR("   ❌ Connection Error - سرور در دسترس نیست")
                )
                return False
            except requests.exceptions.Timeout:
                self.stdout.write(
                    self.style.ERROR("   ❌ Timeout - سرور پاسخ نمی‌دهد")
                )
                return False
            except requests.exceptions.SSLError:
                self.stdout.write(
                    self.style.ERROR("   ❌ SSL Error - مشکل گواهینامه SSL")
                )
                return False
                
        except User.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f"   ❌ User {user_email} not found")
            )
            return False
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"   ❌ Test failed: {e}")
            )
            return False

    def diagnose_403_error(self, response):
        """Diagnose 403 error causes"""
        self.stdout.write("\n🔍 Diagnosing 403 Error:")
        
        # Check response body for clues
        if response.text:
            body = response.text.lower()
            if 'cors' in body:
                self.stdout.write("   💡 Possible CORS issue")
            elif 'token' in body or 'auth' in body:
                self.stdout.write("   💡 Possible authentication issue")
            elif 'origin' in body:
                self.stdout.write("   💡 Possible origin validation issue")
        
        self.stdout.write("\n🛠️  Common fixes for 403:")
        self.stdout.write("   1. Check ALLOWED_HOSTS in Django settings")
        self.stdout.write("   2. Check CORS_ALLOWED_ORIGINS")
        self.stdout.write("   3. Verify JWT token is valid")
        self.stdout.write("   4. Check Origin header matches allowed origins")
        self.stdout.write("   5. Review Nginx configuration for WebSocket proxying")
        
        # Test regular HTTP endpoint
        self.stdout.write("\n🧪 Testing regular HTTP endpoint...")
        try:
            host = response.url.split('/ws/')[0]
            test_url = f"{host}/admin/"  # Test admin endpoint
            test_response = requests.get(test_url, timeout=5)
            self.stdout.write(f"   📊 Admin endpoint status: {test_response.status_code}")
            if test_response.status_code == 200:
                self.stdout.write("   ✅ Server is reachable - problem is WebSocket specific")
            else:
                self.stdout.write("   ⚠️  Server might have general connectivity issues")
        except:
            self.stdout.write("   ❌ Cannot reach server at all")

    def show_example_frontend_code(self):
        """Show example frontend code for testing"""
        self.stdout.write("\n💻 Test this in your browser console:")
        self.stdout.write("""
const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
const wsUrl = `${protocol}//YOUR_DOMAIN/ws/chat/CONVERSATION_ID/?token=YOUR_TOKEN`;
const ws = new WebSocket(wsUrl);

ws.onopen = () => console.log('✅ Connected');
ws.onerror = (error) => console.error('❌ Error:', error);
ws.onclose = (event) => console.log('❌ Closed:', event.code, event.reason);
ws.onmessage = (event) => console.log('📨 Message:', JSON.parse(event.data));

// Send test message
ws.send(JSON.stringify({
    type: 'chat_message',
    content: 'Test message from browser'
}));
        """)

    def show_curl_test(self, host, conversation_id, token, use_ssl):
        """Show curl command for testing"""
        protocol = 'https' if use_ssl else 'http'
        self.stdout.write(f"\n🧪 Test with curl:")
        self.stdout.write(f"""
curl -i -N \\
  -H "Connection: Upgrade" \\
  -H "Upgrade: websocket" \\
  -H "Sec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==" \\
  -H "Sec-WebSocket-Version: 13" \\
  -H "Origin: {protocol}://{host.split(':')[0]}" \\
  "{protocol}://{host}/ws/chat/{conversation_id}/?token={token}"
        """) 