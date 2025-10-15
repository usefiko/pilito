from django.core.management.base import BaseCommand
import asyncio
import websockets
import json


class Command(BaseCommand):
    help = 'Simple WebSocket connection test'

    def add_arguments(self, parser):
        parser.add_argument('--host', default='localhost:8000', help='Host to connect to')
        parser.add_argument('--token', help='JWT token (optional)')
        parser.add_argument('--conversation-id', default='TEST123', help='Conversation ID to test')

    def handle(self, *args, **options):
        asyncio.run(self.test_websocket(options))

    async def test_websocket(self, options):
        host = options['host']
        token = options.get('token', '')
        conversation_id = options['conversation_id']
        
        # Test both endpoints
        endpoints = [
            f"ws://{host}/ws/conversations/",
            f"ws://{host}/ws/chat/{conversation_id}/"
        ]
        
        for endpoint in endpoints:
            await self.test_endpoint(endpoint, token)

    async def test_endpoint(self, endpoint, token):
        try:
            # Add token if provided
            url = f"{endpoint}?token={token}" if token else endpoint
            
            self.stdout.write(f"\n🔌 Testing: {url}")
            
            async with websockets.connect(url) as websocket:
                self.stdout.write(self.style.SUCCESS("✅ Connection successful!"))
                
                # Send a test message
                test_message = {
                    "type": "chat_message",
                    "content": "Hello from test!"
                }
                
                await websocket.send(json.dumps(test_message))
                self.stdout.write("📤 Sent test message")
                
                # Try to receive a response (with timeout)
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    self.stdout.write(f"📥 Received: {response}")
                except asyncio.TimeoutError:
                    self.stdout.write("⏰ No response received (timeout)")
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Connection failed: {e}")) 