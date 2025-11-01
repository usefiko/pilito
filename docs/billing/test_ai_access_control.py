"""
Test Script for AI Access Control

This script tests that users cannot access Gemini AI features when:
1. They have no remaining tokens
2. Their subscription has expired
3. Their subscription is inactive

Run this script from Django shell:
    python manage.py shell < docs/billing/test_ai_access_control.py
"""

import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from billing.utils import check_ai_access_for_user
from billing.models import Subscription

User = get_user_model()

def print_header(text):
    print("\n" + "=" * 80)
    print(f"  {text}")
    print("=" * 80)

def print_success(text):
    print(f"✅ {text}")

def print_error(text):
    print(f"❌ {text}")

def print_info(text):
    print(f"ℹ️  {text}")

def test_no_tokens():
    """Test that users with 0 tokens cannot access AI"""
    print_header("TEST 1: User with 0 tokens")
    
    # Find a user with active subscription
    user = User.objects.filter(
        subscription__is_active=True,
        subscription__tokens_remaining__gt=0
    ).first()
    
    if not user:
        print_error("No suitable test user found")
        return False
    
    print_info(f"Testing with user: {user.username}")
    
    # Save original state
    subscription = user.subscription
    original_tokens = subscription.tokens_remaining
    
    try:
        # Set tokens to 0
        subscription.tokens_remaining = 0
        subscription.save()
        
        print_info(f"Set tokens_remaining to 0")
        
        # Test access
        access_check = check_ai_access_for_user(
            user=user,
            estimated_tokens=1000,
            feature_name="Test Feature"
        )
        
        # Verify access is denied
        if not access_check['has_access']:
            if access_check['reason'] == 'no_tokens_remaining':
                print_success("Access correctly denied due to no tokens")
                print_info(f"Reason: {access_check['reason']}")
                print_info(f"Message: {access_check['message']}")
                return True
            else:
                print_error(f"Access denied but wrong reason: {access_check['reason']}")
                return False
        else:
            print_error("Access was granted when it should be denied!")
            return False
    
    finally:
        # Restore original state
        subscription.tokens_remaining = original_tokens
        subscription.save()
        print_info(f"Restored tokens_remaining to {original_tokens}")

def test_expired_subscription():
    """Test that users with expired subscription cannot access AI"""
    print_header("TEST 2: User with expired subscription")
    
    # Find a user with active subscription
    user = User.objects.filter(
        subscription__is_active=True,
        subscription__tokens_remaining__gt=0,
        subscription__end_date__isnull=False
    ).first()
    
    if not user:
        print_error("No suitable test user found")
        return False
    
    print_info(f"Testing with user: {user.username}")
    
    # Save original state
    subscription = user.subscription
    original_end_date = subscription.end_date
    
    try:
        # Set end_date to past
        subscription.end_date = timezone.now() - timedelta(days=1)
        subscription.save()
        
        print_info(f"Set end_date to {subscription.end_date}")
        
        # Test access
        access_check = check_ai_access_for_user(
            user=user,
            estimated_tokens=1000,
            feature_name="Test Feature"
        )
        
        # Verify access is denied
        if not access_check['has_access']:
            if access_check['reason'] == 'subscription_expired':
                print_success("Access correctly denied due to expired subscription")
                print_info(f"Reason: {access_check['reason']}")
                print_info(f"Message: {access_check['message']}")
                return True
            else:
                print_error(f"Access denied but wrong reason: {access_check['reason']}")
                return False
        else:
            print_error("Access was granted when it should be denied!")
            return False
    
    finally:
        # Restore original state
        subscription.end_date = original_end_date
        subscription.save()
        print_info(f"Restored end_date to {original_end_date}")

def test_insufficient_tokens():
    """Test that users with insufficient tokens cannot access AI"""
    print_header("TEST 3: User with insufficient tokens")
    
    # Find a user with active subscription
    user = User.objects.filter(
        subscription__is_active=True,
        subscription__tokens_remaining__gt=0
    ).first()
    
    if not user:
        print_error("No suitable test user found")
        return False
    
    print_info(f"Testing with user: {user.username}")
    
    # Save original state
    subscription = user.subscription
    original_tokens = subscription.tokens_remaining
    
    try:
        # Set tokens to 500 (less than required 1000)
        subscription.tokens_remaining = 500
        subscription.save()
        
        print_info(f"Set tokens_remaining to 500")
        
        # Test access with 1000 token requirement
        access_check = check_ai_access_for_user(
            user=user,
            estimated_tokens=1000,
            feature_name="Test Feature"
        )
        
        # Verify access is denied
        if not access_check['has_access']:
            if access_check['reason'] == 'insufficient_tokens':
                print_success("Access correctly denied due to insufficient tokens")
                print_info(f"Reason: {access_check['reason']}")
                print_info(f"Message: {access_check['message']}")
                return True
            else:
                print_error(f"Access denied but wrong reason: {access_check['reason']}")
                return False
        else:
            print_error("Access was granted when it should be denied!")
            return False
    
    finally:
        # Restore original state
        subscription.tokens_remaining = original_tokens
        subscription.save()
        print_info(f"Restored tokens_remaining to {original_tokens}")

def test_inactive_subscription():
    """Test that users with inactive subscription cannot access AI"""
    print_header("TEST 4: User with inactive subscription")
    
    # Find a user with active subscription
    user = User.objects.filter(
        subscription__is_active=True,
        subscription__tokens_remaining__gt=0
    ).first()
    
    if not user:
        print_error("No suitable test user found")
        return False
    
    print_info(f"Testing with user: {user.username}")
    
    # Save original state
    subscription = user.subscription
    original_is_active = subscription.is_active
    
    try:
        # Set is_active to False
        subscription.is_active = False
        subscription.save()
        
        print_info(f"Set is_active to False")
        
        # Test access
        access_check = check_ai_access_for_user(
            user=user,
            estimated_tokens=1000,
            feature_name="Test Feature"
        )
        
        # Verify access is denied
        if not access_check['has_access']:
            if access_check['reason'] == 'subscription_deactivated':
                print_success("Access correctly denied due to inactive subscription")
                print_info(f"Reason: {access_check['reason']}")
                print_info(f"Message: {access_check['message']}")
                return True
            else:
                print_error(f"Access denied but wrong reason: {access_check['reason']}")
                return False
        else:
            print_error("Access was granted when it should be denied!")
            return False
    
    finally:
        # Restore original state
        subscription.is_active = original_is_active
        subscription.save()
        print_info(f"Restored is_active to {original_is_active}")

def test_valid_access():
    """Test that users with valid subscription CAN access AI"""
    print_header("TEST 5: User with valid subscription (should have access)")
    
    # Find a user with active subscription
    user = User.objects.filter(
        subscription__is_active=True,
        subscription__tokens_remaining__gt=1000
    ).first()
    
    if not user:
        print_error("No suitable test user found")
        return False
    
    print_info(f"Testing with user: {user.username}")
    
    subscription = user.subscription
    print_info(f"Tokens remaining: {subscription.tokens_remaining}")
    print_info(f"End date: {subscription.end_date}")
    print_info(f"Is active: {subscription.is_active}")
    
    # Test access
    access_check = check_ai_access_for_user(
        user=user,
        estimated_tokens=1000,
        feature_name="Test Feature"
    )
    
    # Verify access is granted
    if access_check['has_access']:
        print_success("Access correctly granted for valid subscription")
        print_info(f"Tokens remaining: {access_check['tokens_remaining']}")
        print_info(f"Days remaining: {access_check['days_remaining']}")
        return True
    else:
        print_error(f"Access was denied when it should be granted!")
        print_error(f"Reason: {access_check['reason']}")
        print_error(f"Message: {access_check['message']}")
        return False

def run_all_tests():
    """Run all tests and report results"""
    print_header("AI ACCESS CONTROL TEST SUITE")
    print_info("Testing that users cannot access AI without valid subscription/tokens")
    
    tests = [
        ("No Tokens", test_no_tokens),
        ("Expired Subscription", test_expired_subscription),
        ("Insufficient Tokens", test_insufficient_tokens),
        ("Inactive Subscription", test_inactive_subscription),
        ("Valid Access", test_valid_access),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print_error(f"Test '{test_name}' failed with exception: {e}")
            import traceback
            traceback.print_exc()
            results.append((test_name, False))
    
    # Print summary
    print_header("TEST RESULTS SUMMARY")
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        if result:
            print_success(f"{test_name}: PASSED")
        else:
            print_error(f"{test_name}: FAILED")
    
    print("\n" + "=" * 80)
    if passed == total:
        print_success(f"ALL TESTS PASSED ({passed}/{total})")
    else:
        print_error(f"SOME TESTS FAILED ({passed}/{total} passed)")
    print("=" * 80)
    
    return passed == total

if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)

