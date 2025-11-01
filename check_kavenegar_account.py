#!/usr/bin/env python
"""
Check Kavenegar account info and find available sender numbers
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

def check_account():
    """Check Kavenegar account information"""
    
    print("=" * 60)
    print("Kavenegar Account Information")
    print("=" * 60)
    
    # Check API key
    api_key = settings.KAVENEGAR_API_KEY
    current_sender = settings.KAVENEGAR_SENDER
    
    print(f"\n📋 Current Configuration:")
    print(f"   API Key: {'*' * 10}{api_key[-4:] if api_key else 'NOT SET'}")
    print(f"   Sender:  {current_sender}")
    
    if not api_key:
        print("\n❌ ERROR: KAVENEGAR_API_KEY is not set!")
        return False
    
    try:
        api = KavenegarAPI(api_key)
        
        # Get account info
        print("\n🔍 Fetching account information...")
        account_info = api.account_info()
        
        print("\n✅ Account Info Retrieved:")
        print(f"   {account_info}")
        
        # Try to get account config
        print("\n🔍 Fetching account config...")
        try:
            config = api.account_config()
            print(f"   {config}")
        except Exception as e:
            print(f"   ⚠️  Could not fetch config: {e}")
        
        print("\n" + "=" * 60)
        print("✅ Account is active!")
        print("\n📝 To find your sender number:")
        print("   1. Go to: https://panel.kavenegar.com/")
        print("   2. Click on 'خطوط ارسالی' (Sender Lines)")
        print("   3. Copy your active sender number")
        print("   4. Update .env file:")
        print("      KAVENEGAR_SENDER=your_sender_number")
        print("=" * 60)
        
        return True
        
    except APIException as e:
        error_msg = str(e)
        try:
            if isinstance(error_msg, bytes):
                error_msg = error_msg.decode('utf-8')
        except:
            pass
        
        print(f"\n❌ Kavenegar API Error:")
        print(f"   {error_msg}")
        
        if '401' in error_msg:
            print("\n   💡 Solution: Your API key is invalid")
            print("      1. Go to: https://panel.kavenegar.com/client/setting/account")
            print("      2. Get your correct API key")
            print("      3. Update .env file")
        
        return False
        
    except HTTPException as e:
        print(f"\n❌ HTTP Error: {e}")
        return False
        
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        print(traceback.format_exc())
        return False

if __name__ == '__main__':
    try:
        check_account()
    except KeyboardInterrupt:
        print("\n\nCancelled by user.")
        sys.exit(0)

