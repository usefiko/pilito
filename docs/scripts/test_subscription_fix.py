#!/usr/bin/env python
"""
Test script to verify the subscription deactivation fix works correctly.
This ensures subscriptions are NOT deactivated unexpectedly.

Run with:
    python test_subscription_fix.py
"""
import os
import sys
import django

# Setup Django environment
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db import transaction
from billing.models import Subscription
from billing.services import consume_tokens_for_user
from message.models import Conversation

User = get_user_model()


def print_header(text):
    print(f"\n{'=' * 60}")
    print(f"  {text}")
    print('=' * 60)


def print_success(text):
    print(f"✅ {text}")


def print_error(text):
    print(f"❌ {text}")


def print_info(text):
    print(f"ℹ️  {text}")


def test_token_depletion_doesnt_auto_deactivate():
    """Test that depleting tokens doesn't automatically deactivate subscription"""
    print_header("TEST 1: Token Depletion Doesn't Auto-Deactivate")
    
    try:
        # Find a user with active subscription and tokens
        user = User.objects.filter(
            subscription__is_active=True,
            subscription__tokens_remaining__gt=100
        ).first()
        
        if not user:
            print_error("No suitable test user found (need active subscription with >100 tokens)")
            return False
        
        subscription = user.subscription
        original_tokens = subscription.tokens_remaining
        original_is_active = subscription.is_active
        
        print_info(f"Testing with user: {user.username}")
        print_info(f"Original tokens: {original_tokens}")
        print_info(f"Original is_active: {original_is_active}")
        
        # Consume 50 tokens
        success, data = consume_tokens_for_user(user, 50, 'Test consumption')
        
        if not success:
            print_error(f"Token consumption failed: {data}")
            return False
        
        # Refresh from DB
        subscription.refresh_from_db()
        
        print_info(f"After consuming 50 tokens:")
        print_info(f"  Tokens remaining: {subscription.tokens_remaining}")
        print_info(f"  is_active: {subscription.is_active}")
        
        # Verify is_active flag is still True
        if not subscription.is_active:
            print_error("FAILED: Subscription was deactivated after token consumption!")
            return False
        
        # Verify tokens were consumed
        if subscription.tokens_remaining != original_tokens - 50:
            print_error("FAILED: Tokens not properly consumed!")
            return False
        
        print_success("Token consumption doesn't trigger auto-deactivation")
        return True
        
    except Exception as e:
        print_error(f"Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_is_subscription_active_is_readonly():
    """Test that is_subscription_active() doesn't enforce deactivation"""
    print_header("TEST 2: is_subscription_active() is Read-Only")
    
    try:
        # Find user with active subscription
        user = User.objects.filter(
            subscription__is_active=True,
            subscription__tokens_remaining__gt=0
        ).first()
        
        if not user:
            print_error("No suitable test user found")
            return False
        
        subscription = user.subscription
        print_info(f"Testing with user: {user.username}")
        print_info(f"Tokens remaining: {subscription.tokens_remaining}")
        
        # Count active conversations before check
        active_convos_before = Conversation.objects.filter(
            user=user,
            status='active'
        ).count()
        
        print_info(f"Active conversations before: {active_convos_before}")
        
        # Call is_subscription_active() multiple times
        for i in range(5):
            is_active = subscription.is_subscription_active()
        
        # Refresh from DB
        subscription.refresh_from_db()
        
        # Count active conversations after checks
        active_convos_after = Conversation.objects.filter(
            user=user,
            status='active'
        ).count()
        
        print_info(f"Active conversations after: {active_convos_after}")
        
        # Verify conversations weren't changed
        if active_convos_before != active_convos_after:
            print_error("FAILED: is_subscription_active() changed conversation statuses!")
            return False
        
        # Verify subscription is_active flag wasn't changed
        if not subscription.is_active:
            print_error("FAILED: is_subscription_active() changed is_active flag!")
            return False
        
        print_success("is_subscription_active() is truly read-only")
        return True
        
    except Exception as e:
        print_error(f"Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_explicit_deactivation_works():
    """Test that explicit deactivation method works correctly"""
    print_header("TEST 3: Explicit Deactivation Works Correctly")
    
    try:
        # Find user with active subscription
        user = User.objects.filter(
            subscription__is_active=True
        ).first()
        
        if not user:
            print_error("No suitable test user found")
            return False
        
        subscription = user.subscription
        print_info(f"Testing with user: {user.username}")
        
        # Count active conversations
        active_convos_before = Conversation.objects.filter(
            user=user,
            status='active'
        ).count()
        
        print_info(f"Active conversations before: {active_convos_before}")
        
        # Use skip_enforcement flag to test deactivation without affecting real chats
        result = subscription.deactivate_subscription(
            reason='Test deactivation',
            skip_enforcement=True
        )
        
        if not result:
            print_error("deactivate_subscription() returned False")
            return False
        
        # Refresh from DB
        subscription.refresh_from_db()
        
        # Verify subscription was deactivated
        if subscription.is_active:
            print_error("FAILED: Subscription is still active after deactivation!")
            return False
        
        print_success("Explicit deactivation method works correctly")
        
        # Reactivate for next tests
        subscription.is_active = True
        subscription.save()
        print_info("Reactivated subscription for next tests")
        
        return True
        
    except Exception as e:
        print_error(f"Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_signal_doesnt_deactivate_on_token_save():
    """Test that saving subscription with 0 tokens doesn't trigger signal deactivation"""
    print_header("TEST 4: Signal Doesn't Auto-Deactivate on Token Save")
    
    try:
        # Find user with active subscription and some tokens
        user = User.objects.filter(
            subscription__is_active=True,
            subscription__tokens_remaining__gt=50
        ).first()
        
        if not user:
            print_error("No suitable test user found")
            return False
        
        subscription = user.subscription
        original_tokens = subscription.tokens_remaining
        
        print_info(f"Testing with user: {user.username}")
        print_info(f"Original tokens: {original_tokens}")
        
        # Manually set tokens to 0 and save
        subscription.tokens_remaining = 0
        subscription.save()
        
        # Refresh from DB
        subscription.refresh_from_db()
        
        print_info(f"After setting tokens to 0:")
        print_info(f"  Tokens: {subscription.tokens_remaining}")
        print_info(f"  is_active: {subscription.is_active}")
        
        # Verify is_active is still True (signal didn't deactivate it)
        if not subscription.is_active:
            print_error("FAILED: pre_save signal deactivated subscription on token save!")
            # Restore
            subscription.is_active = True
            subscription.tokens_remaining = original_tokens
            subscription.save()
            return False
        
        # Restore original tokens
        subscription.tokens_remaining = original_tokens
        subscription.save()
        print_info("Restored original token count")
        
        print_success("Signal doesn't auto-deactivate on token save")
        return True
        
    except Exception as e:
        print_error(f"Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    print("\n🧪 Testing Subscription Deactivation Fix")
    print("=" * 60)
    
    results = []
    
    # Run all tests
    results.append(("Token Depletion", test_token_depletion_doesnt_auto_deactivate()))
    results.append(("Read-Only Check", test_is_subscription_active_is_readonly()))
    results.append(("Explicit Deactivation", test_explicit_deactivation_works()))
    results.append(("Signal Behavior", test_signal_doesnt_deactivate_on_token_save()))
    
    # Print summary
    print_header("TEST SUMMARY")
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"  {test_name}: {status}")
    
    print(f"\n{'=' * 60}")
    print(f"  Total: {passed}/{total} tests passed")
    print('=' * 60)
    
    if passed == total:
        print("\n🎉 All tests passed! The subscription fix is working correctly.")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Please review the output above.")
        return 1


if __name__ == '__main__':
    sys.exit(main())

