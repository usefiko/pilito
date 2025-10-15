#!/usr/bin/env python3
"""
Test script to verify customer update WebSocket notifications are working

This script simulates a customer update via API and checks if WebSocket notifications
are sent correctly to connected clients.
"""

import requests
import json
import time
import websocket
import threading
from urllib.parse import urlencode

# Configuration
BASE_URL = "http://localhost:8000"
WS_URL = "ws://localhost:8000"

def test_customer_update_websocket():
    """Test customer update WebSocket notifications"""
    print("🔧 Testing Customer Update WebSocket Notifications")
    print("=" * 60)
    
    # Test data
    test_customer_data = {
        "first_name": "John",
        "last_name": "Updated",
        "email": "john.updated@example.com",
        "description": "Updated customer information"
    }
    
    print("📝 Test Plan:")
    print("1. Connect to CustomerList WebSocket")
    print("2. Update customer via PUT API")
    print("3. Verify WebSocket receives 'customer_updated' event")
    print("4. Verify updated data is correct")
    print()
    
    # Step 1: Connect to WebSocket
    print("🔌 Connecting to CustomerList WebSocket...")
    
    websocket_connected = threading.Event()
    websocket_messages = []
    
    def on_message(ws, message):
        try:
            data = json.loads(message)
            websocket_messages.append(data)
            print(f"📩 WebSocket Message: {data.get('type', 'unknown')}")
            
            if data.get('type') == 'customer_updated':
                print("✅ SUCCESS: Received customer_updated notification!")
                print(f"   Customer ID: {data.get('customer_id')}")
                print(f"   Updated Data: {data.get('customer_data', {}).get('first_name')} {data.get('customer_data', {}).get('last_name')}")
                
        except json.JSONDecodeError:
            print(f"⚠️  Invalid JSON received: {message}")
    
    def on_open(ws):
        print("✅ WebSocket connected successfully")
        websocket_connected.set()
    
    def on_error(ws, error):
        print(f"❌ WebSocket error: {error}")
    
    def on_close(ws, close_status_code, close_msg):
        print("🔌 WebSocket connection closed")
    
    # Connect to CustomerList WebSocket
    try:
        # You may need to add authentication token here
        ws_url = f"{WS_URL}/ws/customers/"
        ws = websocket.WebSocketApp(ws_url,
                                  on_open=on_open,
                                  on_message=on_message,
                                  on_error=on_error,
                                  on_close=on_close)
        
        # Start WebSocket in background thread
        ws_thread = threading.Thread(target=ws.run_forever)
        ws_thread.daemon = True
        ws_thread.start()
        
        # Wait for connection
        if not websocket_connected.wait(timeout=10):
            print("❌ Failed to connect to WebSocket within 10 seconds")
            return False
        
        # Step 2: Update customer via API
        print(f"\n🔄 Updating customer via PUT API...")
        
        # You'll need to replace this with an actual customer ID that exists in your system
        customer_id = 1  # Replace with a real customer ID
        
        update_url = f"{BASE_URL}/api/v1/customers/{customer_id}/"
        
        # You may need to add authentication headers here
        headers = {
            'Content-Type': 'application/json',
            # 'Authorization': 'Bearer YOUR_JWT_TOKEN'  # Add your auth token
        }
        
        try:
            response = requests.put(update_url, 
                                  json=test_customer_data, 
                                  headers=headers,
                                  timeout=10)
            
            if response.status_code == 200:
                print("✅ Customer updated successfully via API")
                updated_customer = response.json()
                print(f"   Updated Name: {updated_customer.get('first_name')} {updated_customer.get('last_name')}")
            else:
                print(f"❌ Failed to update customer: {response.status_code}")
                print(f"   Response: {response.text}")
                return False
                
        except requests.exceptions.RequestException as e:
            print(f"❌ API request failed: {e}")
            return False
        
        # Step 3: Wait for WebSocket notification
        print(f"\n⏳ Waiting for WebSocket notification...")
        time.sleep(3)  # Wait for WebSocket message
        
        # Step 4: Verify results
        print(f"\n📊 Results:")
        print(f"   Total WebSocket messages received: {len(websocket_messages)}")
        
        customer_updated_messages = [msg for msg in websocket_messages if msg.get('type') == 'customer_updated']
        
        if customer_updated_messages:
            print(f"✅ SUCCESS: Received {len(customer_updated_messages)} customer_updated notification(s)")
            for msg in customer_updated_messages:
                customer_data = msg.get('customer_data', {})
                print(f"   - Customer {msg.get('customer_id')}: {customer_data.get('first_name', '')} {customer_data.get('last_name', '')}")
            return True
        else:
            print("❌ FAILURE: No customer_updated notifications received")
            print("   Available message types:", [msg.get('type') for msg in websocket_messages])
            return False
        
    except Exception as e:
        print(f"❌ Test failed with exception: {e}")
        return False
    
    finally:
        try:
            ws.close()
        except:
            pass

def print_usage_instructions():
    """Print instructions for running the test"""
    print("📋 Setup Instructions:")
    print("=" * 40)
    print("1. Make sure your Django server is running on localhost:8000")
    print("2. Update the customer_id variable in the script with a real customer ID")
    print("3. Add authentication token if required")
    print("4. Install required packages: pip install websocket-client requests")
    print("5. Run this script: python test_customer_update_websocket.py")
    print()

if __name__ == "__main__":
    print_usage_instructions()
    
    user_input = input("Press Enter to run the test (or 'q' to quit): ")
    if user_input.lower() != 'q':
        success = test_customer_update_websocket()
        
        if success:
            print("\n🎉 Test PASSED: Customer update WebSocket notifications are working!")
        else:
            print("\n💥 Test FAILED: Customer update WebSocket notifications are NOT working!")
            print("\nDebugging tips:")
            print("- Check Django server logs for errors")
            print("- Verify customer ID exists")
            print("- Check authentication is working")
            print("- Ensure WebSocket consumers are properly connected")
