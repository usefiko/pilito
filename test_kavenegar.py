#!/usr/bin/env python
"""
Test script for Kavenegar SMS integration
This script helps debug Kavenegar API issues
"""
import os
import sys
from pathlib import Path

# Add project to Python path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.development')
import django
django.setup()

from django.conf import settings
from kavenegar import KavenegarAPI, APIException, HTTPException

def test_kavenegar():
    """Test Kavenegar API connection and SMS sending"""
    
    print("=" * 60)
    print("Kavenegar SMS Test")
    print("=" * 60)
    
    # Check API key
    api_key = settings.KAVENEGAR_API_KEY
    sender = settings.KAVENEGAR_SENDER
    
    print(f"\n1. Checking Configuration:")
    print(f"   API Key: {'*' * 10}{api_key[-4:] if api_key else 'NOT SET'}")
    print(f"   Sender: {sender}")
    
    if not api_key:
        print("\n❌ ERROR: KAVENEGAR_API_KEY is not set!")
        print("   Set it in your .env file:")
        print("   KAVENEGAR_API_KEY=your_api_key_here")
        return False
    
    # Test phone number (replace with your test number)
    test_phone = input("\n2. Enter test phone number (e.g., 09123456789): ").strip()
    if not test_phone:
        print("❌ No phone number provided!")
        return False
    
    # Normalize phone number
    test_phone = test_phone.replace('+', '')
    if test_phone.startswith('0'):
        test_phone = '98' + test_phone[1:]
    
    print(f"\n3. Sending test SMS to: {test_phone}")
    
    try:
        api = KavenegarAPI(api_key)
        
        # Prepare message
        message = "تست ارسال پیامک - کد تایید: 123456"
        
        print(f"   Message: {message}")
        print(f"   Sender: {sender}")
        print(f"   Receptor: {test_phone}")
        
        # Method 1: Using dictionary
        print("\n4. Attempting to send SMS (Method 1: Dictionary)...")
        try:
            params = {
                'sender': sender,
                'receptor': test_phone,
                'message': message,
            }
            response = api.sms_send(params)
            print("✅ SUCCESS (Method 1)!")
            print(f"   Response: {response}")
            return True
        except Exception as e1:
            print(f"❌ Method 1 failed: {e1}")
            print(f"   Error type: {type(e1).__name__}")
            
            # Method 2: Using positional arguments
            print("\n5. Attempting to send SMS (Method 2: Positional args)...")
            try:
                response = api.sms_send(sender, test_phone, message)
                print("✅ SUCCESS (Method 2)!")
                print(f"   Response: {response}")
                return True
            except Exception as e2:
                print(f"❌ Method 2 failed: {e2}")
                print(f"   Error type: {type(e2).__name__}")
                
                # Method 3: Using receptor as list
                print("\n6. Attempting to send SMS (Method 3: Receptor as list)...")
                try:
                    params = {
                        'sender': sender,
                        'receptor': [test_phone],
                        'message': message,
                    }
                    response = api.sms_send(params)
                    print("✅ SUCCESS (Method 3)!")
                    print(f"   Response: {response}")
                    return True
                except Exception as e3:
                    print(f"❌ Method 3 failed: {e3}")
                    print(f"   Error type: {type(e3).__name__}")
                    
                    raise e3
    
    except APIException as e:
        print(f"\n❌ Kavenegar API Exception:")
        print(f"   Status: {e.status}")
        print(f"   Message: {e.message}")
        print(f"   Error Code: {getattr(e, 'code', 'N/A')}")
        return False
    
    except HTTPException as e:
        print(f"\n❌ HTTP Exception:")
        print(f"   {str(e)}")
        return False
    
    except Exception as e:
        print(f"\n❌ Unexpected error:")
        print(f"   {str(e)}")
        print(f"   Type: {type(e).__name__}")
        import traceback
        print(f"\n   Traceback:")
        print(traceback.format_exc())
        return False

if __name__ == '__main__':
    try:
        success = test_kavenegar()
        if success:
            print("\n" + "=" * 60)
            print("✅ Test completed successfully!")
            print("=" * 60)
        else:
            print("\n" + "=" * 60)
            print("❌ Test failed!")
            print("=" * 60)
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n\nTest cancelled by user.")
        sys.exit(0)

