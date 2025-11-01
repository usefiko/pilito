#!/usr/bin/env python
"""
Quick diagnostic script to check OTP configuration
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

print("=" * 60)
print("OTP Configuration Diagnostic")
print("=" * 60)

# Check Kavenegar settings
print("\n📋 Kavenegar Configuration:")
print(f"   KAVENEGAR_API_KEY: {'✅ SET' if settings.KAVENEGAR_API_KEY else '❌ NOT SET'}")
if settings.KAVENEGAR_API_KEY:
    print(f"                      ({'*' * 10}{settings.KAVENEGAR_API_KEY[-4:]})")
print(f"   KAVENEGAR_SENDER:  {settings.KAVENEGAR_SENDER}")

# Check OTP settings
print("\n⚙️  OTP Settings:")
print(f"   OTP_EXPIRY_TIME:   {settings.OTP_EXPIRY_TIME} seconds ({settings.OTP_EXPIRY_TIME // 60} minutes)")
print(f"   OTP_MAX_ATTEMPTS:  {settings.OTP_MAX_ATTEMPTS}")

# Check if kavenegar is installed
print("\n📦 Package Check:")
try:
    import kavenegar
    print(f"   kavenegar:         ✅ Installed (version: {getattr(kavenegar, '__version__', 'unknown')})")
except ImportError:
    print(f"   kavenegar:         ❌ NOT INSTALLED")
    print(f"                      Run: pip install kavenegar==1.1.2")

# Check database
print("\n🗄️  Database Check:")
try:
    from accounts.models import OTPToken
    count = OTPToken.objects.count()
    print(f"   OTPToken model:    ✅ Ready")
    print(f"   Total OTP records: {count}")
    
    # Show recent OTPs
    recent = OTPToken.objects.all()[:5]
    if recent:
        print(f"\n   📝 Recent OTP records:")
        for otp in recent:
            status = "✅ Valid" if otp.is_valid() else "❌ Invalid/Used"
            print(f"      {otp.phone_number}: {otp.code} - {status}")
except Exception as e:
    print(f"   OTPToken model:    ❌ ERROR: {e}")

# Check API endpoints
print("\n🌐 API Endpoints:")
print(f"   Send OTP:          POST /api/v1/usr/otp")
print(f"   Verify OTP:        POST /api/v1/usr/otp/verify")

# Summary
print("\n" + "=" * 60)
if settings.KAVENEGAR_API_KEY:
    print("✅ Configuration looks good!")
    print("\n   Next steps:")
    print("   1. Run: python test_kavenegar.py")
    print("   2. Or test via API:")
    print('      curl -X POST http://localhost:8000/api/v1/usr/otp \\')
    print('        -H "Content-Type: application/json" \\')
    print('        -d \'{"phone_number": "+989123456789"}\'')
else:
    print("❌ Configuration incomplete!")
    print("\n   Required action:")
    print("   1. Add to .env file:")
    print("      KAVENEGAR_API_KEY=your_api_key_here")
    print("   2. Restart Django server")
print("=" * 60)

