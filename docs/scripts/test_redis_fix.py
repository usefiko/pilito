#!/usr/bin/env python3
"""
Test Redis Configuration Fix
Usage: python test_redis_fix.py
"""

import os
import sys
import django

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.common')
django.setup()

from django.core.cache import cache
from django.test.utils import override_settings
import logging

logger = logging.getLogger(__name__)

def test_cache_operations():
    """Test basic cache operations"""
    print("🧪 Testing Redis Cache Operations...")
    
    try:
        # Test set operation
        cache.set('test_key', 'test_value', timeout=60)
        print("✅ Cache SET operation successful")
        
        # Test get operation
        value = cache.get('test_key')
        if value == 'test_value':
            print("✅ Cache GET operation successful")
        else:
            print(f"❌ Cache GET failed: expected 'test_value', got '{value}'")
            return False
        
        # Test delete operation
        cache.delete('test_key')
        deleted_value = cache.get('test_key')
        if deleted_value is None:
            print("✅ Cache DELETE operation successful")
        else:
            print(f"❌ Cache DELETE failed: key still exists with value '{deleted_value}'")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Cache operations failed: {e}")
        return False

def test_user_presence_operations():
    """Test user presence cache operations like the WebSocket consumers use"""
    print("\n🧪 Testing User Presence Cache Operations...")
    
    try:
        from django.utils import timezone
        
        # Test setting user online (like in WebSocket consumers)
        cache_key = 'user_global_online_test_user'
        cache.set(cache_key, {
            'timestamp': timezone.now().isoformat(),
            'status': 'online'
        }, timeout=300)
        print("✅ User presence SET operation successful")
        
        # Test getting user status
        status = cache.get(cache_key)
        if status and status.get('status') == 'online':
            print("✅ User presence GET operation successful")
        else:
            print(f"❌ User presence GET failed: {status}")
            return False
        
        # Test deleting user status
        cache.delete(cache_key)
        deleted_status = cache.get(cache_key)
        if deleted_status is None:
            print("✅ User presence DELETE operation successful")
        else:
            print(f"❌ User presence DELETE failed: {deleted_status}")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ User presence operations failed: {e}")
        return False

def main():
    """Main test function"""
    print("🔧 Redis Configuration Fix Test")
    print("=" * 50)
    
    # Test basic cache operations
    cache_test = test_cache_operations()
    
    # Test user presence operations (what was failing in WebSockets)
    presence_test = test_user_presence_operations()
    
    print("\n📊 Test Results:")
    print("=" * 50)
    
    if cache_test and presence_test:
        print("✅ All tests passed!")
        print("✅ Redis configuration is working correctly")
        print("✅ WebSocket user presence operations should now work")
        print("\n🚀 You can now restart your Django server:")
        print("   python src/manage.py runserver")
        print("   or")
        print("   docker-compose restart")
        return True
    else:
        print("❌ Some tests failed!")
        print("❌ Redis configuration needs further investigation")
        return False

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"💥 Unexpected error: {e}")
        sys.exit(1)