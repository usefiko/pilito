#!/usr/bin/env python3
"""
Complete test script for Wizard Auto-Complete functionality
Tests signals, WebSocket, and auto-completion
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.development')
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
django.setup()

from django.contrib.auth import get_user_model
from settings.models import AIPrompts, InstagramChannel, TelegramChannel
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

User = get_user_model()

print("\n" + "="*70)
print("🧪 Wizard Auto-Complete Test Script")
print("="*70 + "\n")

def print_section(title):
    print("\n" + "-"*70)
    print(f"📋 {title}")
    print("-"*70)

def test_user_exists():
    """Test 1: Check if test user exists"""
    print_section("Test 1: Checking User")
    
    email = input("Enter user email to test (or press Enter for default): ").strip()
    if not email:
        email = "omidlog@gmail.com"
    
    try:
        user = User.objects.get(email=email)
        print(f"✅ User found: {user.email} (ID: {user.id})")
        print(f"   - First name: {user.first_name or '❌ Empty'}")
        print(f"   - Last name: {user.last_name or '❌ Empty'}")
        print(f"   - Phone: {user.phone_number or '❌ Empty'}")
        print(f"   - Business type: {user.business_type or '❌ Empty'}")
        print(f"   - Wizard complete: {'✅ Yes' if user.wizard_complete else '❌ No'}")
        return user
    except User.DoesNotExist:
        print(f"❌ User not found: {email}")
        return None

def test_ai_prompts(user):
    """Test 2: Check AIPrompts"""
    print_section("Test 2: Checking AI Prompts")
    
    try:
        ai_prompts = AIPrompts.objects.get(user=user)
        has_prompt = bool(ai_prompts.manual_prompt and ai_prompts.manual_prompt.strip())
        print(f"{'✅' if has_prompt else '❌'} Manual Prompt: {len(ai_prompts.manual_prompt) if ai_prompts.manual_prompt else 0} chars")
        if has_prompt:
            print(f"   Preview: {ai_prompts.manual_prompt[:100]}...")
        return has_prompt
    except AIPrompts.DoesNotExist:
        print("❌ AIPrompts not found for user")
        return False

def test_channels(user):
    """Test 3: Check connected channels"""
    print_section("Test 3: Checking Channels")
    
    # Instagram
    instagram_channels = InstagramChannel.objects.filter(user=user)
    instagram_connected = instagram_channels.filter(is_connect=True).exists()
    
    print(f"Instagram: {instagram_channels.count()} channel(s)")
    for ch in instagram_channels:
        status = "✅ Connected" if ch.is_connect else "❌ Disconnected"
        print(f"   - {ch.username}: {status}")
    
    # Telegram
    telegram_channels = TelegramChannel.objects.filter(user=user)
    telegram_connected = telegram_channels.filter(is_connect=True).exists()
    
    print(f"Telegram: {telegram_channels.count()} channel(s)")
    for ch in telegram_channels:
        status = "✅ Connected" if ch.is_connect else "❌ Disconnected"
        print(f"   - {ch.bot_username}: {status}")
    
    has_channel = instagram_connected or telegram_connected
    print(f"\n{'✅' if has_channel else '❌'} At least one channel connected: {has_channel}")
    
    return has_channel

def test_requirements(user):
    """Test 4: Check all wizard requirements"""
    print_section("Test 4: Checking All Requirements")
    
    checks = {
        'First Name': bool(user.first_name),
        'Last Name': bool(user.last_name),
        'Phone Number': bool(user.phone_number),
        'Business Type': bool(user.business_type),
    }
    
    # Check manual prompt
    try:
        ai_prompts = AIPrompts.objects.get(user=user)
        checks['Manual Prompt'] = bool(ai_prompts.manual_prompt and ai_prompts.manual_prompt.strip())
    except AIPrompts.DoesNotExist:
        checks['Manual Prompt'] = False
    
    # Check channels
    instagram_connected = InstagramChannel.objects.filter(user=user, is_connect=True).exists()
    telegram_connected = TelegramChannel.objects.filter(user=user, is_connect=True).exists()
    checks['Channel Connected'] = instagram_connected or telegram_connected
    
    # Print results
    all_complete = True
    for name, status in checks.items():
        icon = "✅" if status else "❌"
        print(f"{icon} {name}: {status}")
        if not status:
            all_complete = False
    
    print(f"\n{'✅' if all_complete else '❌'} All requirements met: {all_complete}")
    print(f"Current wizard_complete status: {'✅ True' if user.wizard_complete else '❌ False'}")
    
    if all_complete and not user.wizard_complete:
        print("\n⚠️  WARNING: All requirements are met but wizard_complete is False!")
        print("   This might indicate signals are not firing properly.")
    
    return all_complete

def test_redis():
    """Test 5: Check Redis connection"""
    print_section("Test 5: Checking Redis Connection")
    
    try:
        channel_layer = get_channel_layer()
        if channel_layer is None:
            print("❌ Channel layer is None - Redis not configured")
            return False
        
        # Try to send a test message
        async_to_sync(channel_layer.group_send)(
            'test_group',
            {'type': 'test_message', 'data': 'test'}
        )
        print("✅ Redis connection OK")
        print(f"   Channel layer: {type(channel_layer).__name__}")
        return True
    except Exception as e:
        print(f"❌ Redis connection failed: {e}")
        print("\n   💡 Solution: Make sure Redis is running")
        print("   Run: redis-server")
        return False

def test_manual_trigger(user):
    """Test 6: Manually trigger wizard check"""
    print_section("Test 6: Manual Trigger Test")
    
    print("This will manually run the auto-complete check...")
    confirm = input("Proceed? (y/n): ").lower()
    
    if confirm != 'y':
        print("⏭️  Skipped")
        return
    
    from accounts.signals import check_and_complete_wizard
    
    print(f"\nBefore: wizard_complete = {user.wizard_complete}")
    
    result = check_and_complete_wizard(user)
    
    # Refresh from database
    user.refresh_from_db()
    
    print(f"After: wizard_complete = {user.wizard_complete}")
    print(f"Function returned: {result}")
    
    if result:
        print("✅ Wizard was auto-completed by manual trigger!")
    elif user.wizard_complete:
        print("ℹ️  Wizard was already completed")
    else:
        print("❌ Wizard was not completed (some requirements missing)")

def test_websocket_notification(user):
    """Test 7: Test WebSocket notification"""
    print_section("Test 7: WebSocket Notification Test")
    
    print("This will send a test notification to WebSocket...")
    
    try:
        from accounts.signals import notify_wizard_status
        notify_wizard_status(user.id)
        print(f"✅ Notification sent to group: wizard_status_{user.id}")
        print("\n   💡 If frontend is connected, it should receive this update")
    except Exception as e:
        print(f"❌ Failed to send notification: {e}")

def run_all_tests():
    """Run all tests"""
    
    # Test 1
    user = test_user_exists()
    if not user:
        print("\n❌ Cannot continue without user")
        return
    
    # Test 2
    test_ai_prompts(user)
    
    # Test 3
    test_channels(user)
    
    # Test 4
    all_requirements_met = test_requirements(user)
    
    # Test 5
    redis_ok = test_redis()
    
    # Test 6
    if all_requirements_met:
        test_manual_trigger(user)
    
    # Test 7
    if redis_ok:
        test_websocket_notification(user)
    
    # Final summary
    print("\n" + "="*70)
    print("📊 Test Summary")
    print("="*70)
    
    print(f"\n✅ User exists: Yes")
    print(f"{'✅' if all_requirements_met else '❌'} All requirements met: {all_requirements_met}")
    print(f"{'✅' if redis_ok else '❌'} Redis working: {redis_ok}")
    print(f"{'✅' if user.wizard_complete else '❌'} Wizard complete: {user.wizard_complete}")
    
    if all_requirements_met and not user.wizard_complete:
        print("\n⚠️  ISSUE DETECTED:")
        print("   All requirements are met but wizard is not complete.")
        print("\n   Possible causes:")
        print("   1. Signals not firing (check if accounts.signals is imported)")
        print("   2. Database not saved properly")
        print("   3. Manual trigger needed (run test 6)")
    
    if not redis_ok:
        print("\n⚠️  REDIS ISSUE:")
        print("   WebSocket notifications won't work without Redis")
        print("\n   Solution:")
        print("   1. Install Redis: brew install redis (Mac) or apt-get install redis (Linux)")
        print("   2. Start Redis: redis-server")
        print("   3. Test: redis-cli ping (should return PONG)")
    
    print("\n" + "="*70)
    print("✅ Tests complete!")
    print("="*70 + "\n")

if __name__ == "__main__":
    try:
        run_all_tests()
    except KeyboardInterrupt:
        print("\n\n⏹️  Tests cancelled by user")
    except Exception as e:
        print(f"\n\n❌ Error running tests: {e}")
        import traceback
        traceback.print_exc()

