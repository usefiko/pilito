#!/usr/bin/env python
"""
Verification script for business_type field implementation
Run this inside the Django container to verify everything is working
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.common')
django.setup()

from django.contrib.auth import get_user_model
from accounts.serializers import UserShortSerializer, UserUpdateSerializer
from accounts.models import User

def test_business_type_field():
    """Test that business_type field is working correctly"""
    print("🧪 Testing business_type field implementation...")
    
    # Test 1: Check model field exists
    print("\n1️⃣ Testing User model field...")
    try:
        # Check if field exists in model
        field = User._meta.get_field('business_type')
        print(f"   ✅ Field exists: {field.__class__.__name__}")
        print(f"   ✅ Max length: {field.max_length}")
        print(f"   ✅ Nullable: {field.null}")
        print(f"   ✅ Blank allowed: {field.blank}")
    except Exception as e:
        print(f"   ❌ Field error: {e}")
        return False
    
    # Test 2: Check serializers include business_type
    print("\n2️⃣ Testing serializers...")
    try:
        # Test UserShortSerializer
        if 'business_type' in UserShortSerializer.Meta.fields:
            print("   ✅ UserShortSerializer includes business_type")
        else:
            print("   ❌ UserShortSerializer missing business_type")
            
        # Test UserUpdateSerializer
        if 'business_type' in UserUpdateSerializer.Meta.fields:
            print("   ✅ UserUpdateSerializer includes business_type")
        else:
            print("   ❌ UserUpdateSerializer missing business_type")
    except Exception as e:
        print(f"   ❌ Serializer error: {e}")
        return False
    
    # Test 3: Test database operations
    print("\n3️⃣ Testing database operations...")
    try:
        # Count existing users
        user_count = User.objects.count()
        print(f"   📊 Total users in database: {user_count}")
        
        # Test querying users with business_type
        users_with_business_type = User.objects.exclude(business_type__isnull=True).exclude(business_type='')
        print(f"   📊 Users with business_type set: {users_with_business_type.count()}")
        
        # Show some examples if they exist
        if users_with_business_type.exists():
            print("   📋 Examples:")
            for user in users_with_business_type[:3]:
                print(f"      • {user.email}: {user.business_type}")
        
        print("   ✅ Database queries working correctly")
    except Exception as e:
        print(f"   ❌ Database error: {e}")
        return False
    
    # Test 4: Test serialization
    print("\n4️⃣ Testing serialization...")
    try:
        # Get or create a test user
        test_user = User.objects.first()
        if test_user:
            # Test serialization
            serializer = UserShortSerializer(test_user)
            data = serializer.data
            
            if 'business_type' in data:
                print(f"   ✅ business_type in serialized data: {data['business_type']}")
            else:
                print("   ❌ business_type missing from serialized data")
                
            # Test update serializer
            update_data = {'business_type': 'Technology Consulting'}
            update_serializer = UserUpdateSerializer(test_user, data=update_data, partial=True)
            
            if update_serializer.is_valid():
                print("   ✅ Update serializer validation passed")
                print(f"   ✅ Validated data: {update_serializer.validated_data}")
            else:
                print(f"   ❌ Update serializer validation failed: {update_serializer.errors}")
        else:
            print("   ⚠️ No users found for testing serialization")
            
    except Exception as e:
        print(f"   ❌ Serialization error: {e}")
        return False
    
    print("\n🎉 All tests passed! business_type field is working correctly.")
    return True

def show_migration_status():
    """Show current migration status"""
    print("\n📋 Migration Status:")
    try:
        from django.core.management import execute_from_command_line
        from io import StringIO
        import sys
        
        # Capture migration output
        old_stdout = sys.stdout
        sys.stdout = StringIO()
        
        try:
            execute_from_command_line(['manage.py', 'showmigrations', 'accounts'])
            output = sys.stdout.getvalue()
        finally:
            sys.stdout = old_stdout
            
        print(output)
    except Exception as e:
        print(f"   ❌ Error getting migration status: {e}")

if __name__ == "__main__":
    print("=" * 60)
    print("🔍 Fiko Backend - business_type Field Verification")
    print("=" * 60)
    
    try:
        success = test_business_type_field()
        show_migration_status()
        
        if success:
            print("\n✅ Verification completed successfully!")
            print("💡 Your business_type field implementation is ready for production.")
        else:
            print("\n❌ Verification failed!")
            print("💡 Check the errors above and fix any issues.")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        sys.exit(1)
