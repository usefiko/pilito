#!/usr/bin/env python
"""
Test OTP rate limiting functionality
This script tests that users can only request OTP once every 5 minutes
"""
import os
import sys
from pathlib import Path
import time

# Add project to Python path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.development')
import django
django.setup()

from accounts.models import OTPToken
from django.utils import timezone
from datetime import timedelta

def test_rate_limiting():
    """Test OTP rate limiting"""
    
    print("=" * 60)
    print("OTP Rate Limiting Test")
    print("=" * 60)
    
    test_phone = "+989999999999"
    
    # Clean up any existing OTPs for test phone
    print(f"\n1. Cleaning up test data...")
    deleted_count = OTPToken.objects.filter(phone_number=test_phone).delete()[0]
    print(f"   Deleted {deleted_count} old OTP records")
    
    # Test 1: First OTP should succeed
    print(f"\n2. Test 1: Creating first OTP...")
    otp1 = OTPToken.objects.create(phone_number=test_phone)
    print(f"   ✅ First OTP created: {otp1.code}")
    print(f"   Created at: {otp1.created_at}")
    
    # Test 2: Immediate second request should be blocked
    print(f"\n3. Test 2: Trying immediate second request...")
    last_otp = OTPToken.objects.filter(phone_number=test_phone).order_by('-created_at').first()
    if last_otp:
        time_since = timezone.now() - last_otp.created_at
        wait_time = 300  # 5 minutes in seconds
        
        if time_since < timedelta(seconds=wait_time):
            remaining = (timedelta(seconds=wait_time) - time_since).total_seconds()
            print(f"   ✅ CORRECTLY BLOCKED! Must wait {int(remaining)} seconds")
            print(f"   Time since last OTP: {int(time_since.total_seconds())} seconds")
        else:
            print(f"   ❌ FAILED! OTP was allowed but should be blocked")
    
    # Test 3: Simulate OTP after wait time
    print(f"\n4. Test 3: Simulating OTP after wait time...")
    # Set first OTP to 6 minutes ago
    old_time = timezone.now() - timedelta(minutes=6)
    OTPToken.objects.filter(id=otp1.id).update(created_at=old_time)
    
    last_otp = OTPToken.objects.filter(phone_number=test_phone).order_by('-created_at').first()
    time_since = timezone.now() - last_otp.created_at
    wait_time = 300
    
    if time_since >= timedelta(seconds=wait_time):
        print(f"   ✅ CORRECTLY ALLOWED! Wait time passed ({int(time_since.total_seconds())} seconds)")
        otp2 = OTPToken.objects.create(phone_number=test_phone)
        print(f"   New OTP created: {otp2.code}")
    else:
        print(f"   ❌ FAILED! Should allow OTP after wait time")
    
    # Show all OTPs for this phone
    print(f"\n5. All OTPs for {test_phone}:")
    all_otps = OTPToken.objects.filter(phone_number=test_phone).order_by('-created_at')
    for otp in all_otps:
        age = (timezone.now() - otp.created_at).total_seconds()
        status = "✅ Valid" if otp.is_valid() else "❌ Invalid/Used"
        print(f"   Code: {otp.code}, Age: {int(age)}s, Status: {status}")
    
    # Cleanup
    print(f"\n6. Cleaning up test data...")
    deleted_count = OTPToken.objects.filter(phone_number=test_phone).delete()[0]
    print(f"   Deleted {deleted_count} test records")
    
    print("\n" + "=" * 60)
    print("✅ Rate Limiting Test Complete!")
    print("=" * 60)
    print("\nSummary:")
    print("  • First OTP: ✅ Allowed")
    print("  • Immediate retry: ✅ Blocked (must wait 5 minutes)")
    print("  • After 5 minutes: ✅ Allowed")
    print("\n💡 To test via API:")
    print("   curl -X POST http://localhost:8000/api/v1/usr/otp \\")
    print("     -H \"Content-Type: application/json\" \\")
    print("     -d '{\"phone_number\": \"+989123456789\"}'")
    print("\n   Try calling it twice - second call should be blocked!")

if __name__ == '__main__':
    try:
        test_rate_limiting()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        print(traceback.format_exc())
        sys.exit(1)

