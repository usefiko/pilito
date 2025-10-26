#!/usr/bin/env python
"""
Test script to verify wizard signals are working correctly
Run with: docker exec -it django_app python test_wizard_signals.py
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.production')
sys.path.insert(0, '/app')
django.setup()

from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

User = get_user_model()

print("=" * 70)
print("🧪 WIZARD SIGNALS TEST SCRIPT")
print("=" * 70)

# Test 1: Check signal registration
print("\n📊 Test 1: Checking signal registration...")
receivers = post_save._live_receivers(User)
print(f"   Total User.post_save receivers: {len(receivers)}")

expected_receivers = ['create_user_plan', 'sync_user_to_intercom', 'notify_wizard_on_user_update']
print(f"   Expected receivers: {expected_receivers}")

if len(receivers) >= 3:
    print("   ✅ PASS: At least 3 receivers registered")
else:
    print(f"   ❌ FAIL: Only {len(receivers)} receivers (expected 3+)")

# Test 2: Get test user
print("\n👤 Test 2: Getting test user...")
try:
    user = User.objects.get(email='omidlog@gmail.com')
    print(f"   ✅ Found user: {user.email} (ID: {user.id})")
    print(f"      - first_name: {user.first_name}")
    print(f"      - last_name: {user.last_name}")
    print(f"      - phone_number: {user.phone_number}")
    print(f"      - business_type: {user.business_type}")
    print(f"      - wizard_complete: {user.wizard_complete}")
except User.DoesNotExist:
    print("   ❌ FAIL: User not found!")
    sys.exit(1)

# Test 3: Update user and trigger signal
print("\n🔧 Test 3: Updating user to trigger signal...")
print(f"   Current first_name: '{user.first_name}'")

import time
timestamp = int(time.time())
new_name = f"Test {timestamp}"

print(f"   Setting first_name to: '{new_name}'")
user.first_name = new_name
user.save()

user.refresh_from_db()
print(f"   New first_name: '{user.first_name}'")

if user.first_name == new_name:
    print("   ✅ PASS: User updated successfully")
else:
    print("   ❌ FAIL: User update failed")

# Test 4: Check logs
print("\n📝 Test 4: Check Docker logs for signal output")
print("   Run this command to see signal logs:")
print("   docker logs django_app --tail 30 | grep -E '(Intercom sync|Wizard status)'")

# Test 5: Manual signal test
print("\n🎯 Test 5: Testing signal functions directly...")
try:
    from accounts.signals import check_and_complete_wizard, notify_wizard_status
    
    print("   Calling check_and_complete_wizard()...")
    result = check_and_complete_wizard(user)
    print(f"   Result: {result}")
    
    print("   Calling notify_wizard_status()...")
    notify_wizard_status(user.id)
    print("   ✅ PASS: Signal functions executed without errors")
except Exception as e:
    print(f"   ❌ FAIL: {e}")

print("\n" + "=" * 70)
print("✅ TEST COMPLETE!")
print("=" * 70)
print("\n💡 Next steps:")
print("1. Check Docker logs: docker logs django_app --tail 50")
print("2. Look for: '📡 Wizard status notification sent for user'")
print("3. If you see the log, backend is working!")
print("4. If not, there's an issue with signal registration")
print("=" * 70)

