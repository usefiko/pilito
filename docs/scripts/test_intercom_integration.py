#!/usr/bin/env python
"""
Test script for Intercom JWT integration.

This script tests the Intercom JWT service functionality.
Run this script from the project root: python test_intercom_integration.py
"""

import os
import sys
import django
from pathlib import Path

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.development')
django.setup()

from accounts.services.intercom import IntercomJWTService
from accounts.models import User
from django.conf import settings
import json


def test_intercom_jwt_service():
    """Test the Intercom JWT service functionality."""
    
    print("🔧 Testing Intercom JWT Integration")
    print("=" * 50)
    
    # Check configuration
    print("1. Checking Configuration...")
    
    if not hasattr(settings, 'INTERCOM_APP_ID') or not settings.INTERCOM_APP_ID:
        print("❌ INTERCOM_APP_ID is not configured")
        print("   Add INTERCOM_APP_ID to your environment variables")
        return False
    
    if not hasattr(settings, 'INTERCOM_API_SECRET') or not settings.INTERCOM_API_SECRET:
        print("❌ INTERCOM_API_SECRET is not configured")
        print("   Add INTERCOM_API_SECRET to your environment variables")
        return False
    
    print(f"✅ App ID: {settings.INTERCOM_APP_ID}")
    print(f"✅ API Secret: {'*' * (len(settings.INTERCOM_API_SECRET) - 4) + settings.INTERCOM_API_SECRET[-4:]}")
    
    # Test configuration service
    print("\n2. Testing Configuration Service...")
    config = IntercomJWTService.get_intercom_config()
    print(f"✅ Config: {json.dumps(config, indent=2)}")
    
    # Find a test user
    print("\n3. Finding Test User...")
    user = User.objects.first()
    
    if not user:
        print("❌ No users found in database")
        print("   Please create a user first or run migrations")
        return False
    
    print(f"✅ Test User: {user.email} (ID: {user.id})")
    
    # Test JWT generation
    print("\n4. Testing JWT Generation...")
    
    # Test with default parameters
    jwt_token = IntercomJWTService.generate_user_jwt(user)
    
    if not jwt_token:
        print("❌ Failed to generate JWT token")
        return False
    
    print(f"✅ Generated JWT: {jwt_token[:50]}...")
    
    # Test with custom attributes
    custom_attrs = {
        "subscription_plan": "pro",
        "last_login": "2024-01-15",
        "feature_flags": ["chat_enabled", "support_priority"]
    }
    
    jwt_with_attrs = IntercomJWTService.generate_user_jwt(
        user=user,
        expiration_minutes=10,
        custom_attributes=custom_attrs
    )
    
    if not jwt_with_attrs:
        print("❌ Failed to generate JWT with custom attributes")
        return False
    
    print(f"✅ Generated JWT with custom attrs: {jwt_with_attrs[:50]}...")
    
    # Test JWT validation
    print("\n5. Testing JWT Validation...")
    
    payload = IntercomJWTService.validate_user_jwt(jwt_token)
    
    if not payload:
        print("❌ Failed to validate JWT token")
        return False
    
    print("✅ JWT validation successful!")
    print(f"   User ID: {payload.get('user_id')}")
    print(f"   Email: {payload.get('email')}")
    print(f"   Expires: {payload.get('exp')}")
    
    # Test user hash generation (legacy)
    print("\n6. Testing User Hash Generation (Legacy)...")
    
    user_hash = IntercomJWTService.generate_user_hash(str(user.id))
    
    if not user_hash:
        print("❌ Failed to generate user hash")
        return False
    
    print(f"✅ Generated user hash: {user_hash[:20]}...")
    
    # Test invalid token validation
    print("\n7. Testing Invalid Token Validation...")
    
    invalid_payload = IntercomJWTService.validate_user_jwt("invalid.jwt.token")
    
    if invalid_payload:
        print("❌ Invalid token was incorrectly validated")
        return False
    
    print("✅ Invalid token correctly rejected")
    
    print("\n" + "=" * 50)
    print("🎉 All Intercom JWT tests passed!")
    print("\n📋 Next Steps:")
    print("1. Set your environment variables:")
    print("   - INTERCOM_APP_ID=your_app_id")
    print("   - INTERCOM_API_SECRET=your_api_secret")
    print("2. Test the API endpoints:")
    print("   - POST /api/v1/accounts/intercom/jwt")
    print("   - GET /api/v1/accounts/intercom/config")
    print("3. Integrate with your frontend using the provided examples")
    
    return True


if __name__ == "__main__":
    try:
        success = test_intercom_jwt_service()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
