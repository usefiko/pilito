#!/usr/bin/env python3
"""
Test the Google OAuth state field fix
"""

import json


def test_serializer_fix():
    """Test that the serializer now handles missing state properly"""
    
    print("🧪 Testing Google OAuth State Field Fix")
    print("=" * 40)
    
    # Simulate the data that would be passed to the serializer
    test_cases = [
        {'code': 'test_code_123', 'state': None},
        {'code': 'test_code_123', 'state': ''},
        {'code': 'test_code_123'},  # No state field at all
        {'code': 'test_code_123', 'state': 'valid_state'},
    ]
    
    print("Testing different state field scenarios:")
    
    for i, test_data in enumerate(test_cases, 1):
        print(f"\n{i}. Test data: {test_data}")
        
        try:
            # This simulates what happens in the OAuth callback
            from accounts.serializers.google_oauth import GoogleOAuthCodeSerializer
            
            serializer = GoogleOAuthCodeSerializer(data=test_data)
            is_valid = serializer.is_valid()
            
            if is_valid:
                print(f"   ✅ Serializer validation passed")
                print(f"   📋 Validated data: {serializer.validated_data}")
            else:
                print(f"   ❌ Serializer validation failed: {serializer.errors}")
                
        except Exception as e:
            print(f"   💥 Exception: {e}")
    
    print("\n" + "=" * 40)
    print("🎯 Expected results:")
    print("- All test cases should pass validation")
    print("- Missing or null state should be handled gracefully")


if __name__ == "__main__":
    # Set up Django environment
    import os
    import sys
    import django
    
    # Add the src directory to the Python path
    sys.path.insert(0, '/app')
    
    # Configure Django settings
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
    django.setup()
    
    # Run the test
    test_serializer_fix()
