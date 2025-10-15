#!/usr/bin/env python3
"""
WebSocket Debug Script - Test WebSocket connections and performance
Usage: python debug_websockets.py
"""

import asyncio
import websockets
import json
import time
import sys

# Configuration
WS_BASE_URL = "ws://localhost:8000"  # Change to your server URL
JWT_TOKEN = "your_jwt_token_here"  # Replace with actual JWT token

async def test_connection(ws_url, test_name, test_messages):
    """Test a single WebSocket connection with timeout"""
    print(f"\n🧪 Testing {test_name}...")
    
    try:
        # Connect with timeout
        ws = await asyncio.wait_for(
            websockets.connect(ws_url),
            timeout=10.0
        )
        print(f"✅ Connected to {test_name}")
        
        # Send test messages
        for i, message in enumerate(test_messages):
            print(f"📤 Sending message {i+1}: {message['type']}")
            await ws.send(json.dumps(message))
            
            # Wait for response with timeout
            try:
                response = await asyncio.wait_for(ws.recv(), timeout=15.0)
                data = json.loads(response)
                print(f"📨 Received: {data.get('type', 'unknown')} ({len(response)} chars)")
                
                if data.get('type') == 'error':
                    print(f"❌ Error: {data.get('message')}")
                
            except asyncio.TimeoutError:
                print(f"⏰ Timeout waiting for response to message {i+1}")
                break
            except Exception as e:
                print(f"❌ Error receiving response: {e}")
                break
        
        # Close connection gracefully
        await ws.close()
        print(f"✅ {test_name} connection closed gracefully")
        
    except asyncio.TimeoutError:
        print(f"⏰ Connection timeout for {test_name}")
    except Exception as e:
        print(f"❌ Connection failed for {test_name}: {e}")

async def test_all_websockets():
    """Test all WebSocket endpoints"""
    print("🚀 Starting WebSocket tests...")
    
    # Test Customer List WebSocket
    customer_messages = [
        {"type": "get_customers"},
        {"type": "get_filter_options"},
        {"type": "filter_customers", "filters": {"search": "test"}}
    ]
    
    await test_connection(
        f"{WS_BASE_URL}/ws/customers/?token={JWT_TOKEN}",
        "Customer List WebSocket",
        customer_messages
    )
    
    # Test Conversation List WebSocket
    conversation_messages = [
        {"type": "get_conversations"},
        {"type": "get_conversation_filter_options"},
        {"type": "filter_conversations", "filters": {"status": "open"}}
    ]
    
    await test_connection(
        f"{WS_BASE_URL}/ws/conversations/?token={JWT_TOKEN}",
        "Conversation List WebSocket",
        conversation_messages
    )
    
    # Test Chat WebSocket (replace with actual conversation ID)
    chat_messages = [
        {"type": "mark_read"}
    ]
    
    await test_connection(
        f"{WS_BASE_URL}/ws/chat/test_conversation_id/?token={JWT_TOKEN}",
        "Chat WebSocket",
        chat_messages
    )

async def stress_test():
    """Stress test with multiple concurrent connections"""
    print("\n💪 Running stress test with 5 concurrent connections...")
    
    async def single_stress_test(connection_id):
        try:
            ws_url = f"{WS_BASE_URL}/ws/customers/?token={JWT_TOKEN}"
            ws = await asyncio.wait_for(
                websockets.connect(ws_url),
                timeout=10.0
            )
            
            # Send a message
            await ws.send(json.dumps({"type": "get_customers"}))
            
            # Wait for response
            response = await asyncio.wait_for(ws.recv(), timeout=15.0)
            data = json.loads(response)
            
            await ws.close()
            print(f"✅ Connection {connection_id} completed successfully")
            return True
            
        except Exception as e:
            print(f"❌ Connection {connection_id} failed: {e}")
            return False
    
    # Run 5 concurrent connections
    tasks = [single_stress_test(i) for i in range(1, 6)]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    success_count = sum(1 for r in results if r is True)
    print(f"📊 Stress test results: {success_count}/5 connections successful")

def main():
    """Main function"""
    print("🔧 WebSocket Debug Tool")
    print("=" * 50)
    
    if JWT_TOKEN == "your_jwt_token_here":
        print("⚠️  Please set a valid JWT_TOKEN in the script")
        print("You can get a token by logging into your app and checking the browser's local storage")
        return
    
    try:
        # Run basic tests
        asyncio.run(test_all_websockets())
        
        # Run stress test
        asyncio.run(stress_test())
        
        print("\n🎉 All tests completed!")
        print("\n📋 What to look for:")
        print("- No timeout errors")
        print("- No 'took too long to shut down' warnings in server logs")
        print("- All connections close gracefully")
        print("- Response times under 15 seconds")
        
    except KeyboardInterrupt:
        print("\n👋 Tests interrupted by user")
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")

if __name__ == "__main__":
    main()