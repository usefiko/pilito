#!/usr/bin/env python
"""
AI Usage Tracking Diagnostic Script

This script tests and diagnoses the AI usage tracking system.
Run it to verify that both AIUsageLog and AIUsageTracking are working correctly.

Usage:
    python test_ai_usage_tracking.py
"""

import os
import sys
import django

# Setup Django
sys.path.insert(0, 'src')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.development')
django.setup()

from django.contrib.auth import get_user_model
from AI_model.models import AIUsageLog, AIUsageTracking
from AI_model.services import track_ai_usage_safe
from datetime import date
import logging

# Configure logging to see what's happening
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)

User = get_user_model()

print("=" * 80)
print("AI USAGE TRACKING DIAGNOSTIC SCRIPT")
print("=" * 80)
print()

# Test 1: Check if models exist
print("✓ Test 1: Checking if models are accessible...")
try:
    print(f"  - AIUsageLog model: {AIUsageLog}")
    print(f"  - AIUsageTracking model: {AIUsageTracking}")
    print("  ✅ Models are accessible\n")
except Exception as e:
    print(f"  ❌ Error accessing models: {e}\n")
    sys.exit(1)

# Test 2: Get a test user
print("✓ Test 2: Getting test user...")
try:
    user = User.objects.first()
    if not user:
        print("  ❌ No users found in database. Please create a user first.")
        sys.exit(1)
    print(f"  ✅ Using user: {user.username} (ID: {user.id})\n")
except Exception as e:
    print(f"  ❌ Error getting user: {e}\n")
    sys.exit(1)

# Test 3: Check existing logs count
print("✓ Test 3: Checking existing logs...")
try:
    log_count = AIUsageLog.objects.filter(user=user).count()
    tracking_count = AIUsageTracking.objects.filter(user=user).count()
    print(f"  - AIUsageLog entries for this user: {log_count}")
    print(f"  - AIUsageTracking entries for this user: {tracking_count}")
    print("  ✅ Can query existing logs\n")
except Exception as e:
    print(f"  ❌ Error querying logs: {e}\n")

# Test 4: Track a test AI usage
print("✓ Test 4: Tracking test AI usage...")
print("  Creating test log with:")
print("    - Section: chat")
print("    - Prompt tokens: 100")
print("    - Completion tokens: 50")
print("    - Response time: 1000ms")
print("    - Success: True")
print()

try:
    log, tracking = track_ai_usage_safe(
        user=user,
        section='chat',
        prompt_tokens=100,
        completion_tokens=50,
        response_time_ms=1000,
        success=True,
        metadata={'test': 'diagnostic_run'}
    )
    
    if log and tracking:
        print(f"  ✅ Tracking successful!")
        print(f"     - AIUsageLog created: ID={log.id}")
        print(f"       • Total tokens: {log.total_tokens}")
        print(f"       • Section: {log.section}")
        print(f"       • Success: {log.success}")
        print(f"       • Created at: {log.created_at}")
        print()
        print(f"     - AIUsageTracking updated: Date={tracking.date}")
        print(f"       • Total requests: {tracking.total_requests}")
        print(f"       • Total tokens: {tracking.total_tokens}")
        print(f"       • Successful requests: {tracking.successful_requests}")
        print(f"       • Failed requests: {tracking.failed_requests}")
        print()
    else:
        print(f"  ❌ Tracking returned None!")
        print(f"     - Check logs above for errors")
        print()
except Exception as e:
    print(f"  ❌ Error during tracking: {e}")
    import traceback
    print(traceback.format_exc())
    print()

# Test 5: Verify data was saved
print("✓ Test 5: Verifying data was saved to database...")
try:
    # Check AIUsageLog
    latest_log = AIUsageLog.objects.filter(user=user).order_by('-created_at').first()
    if latest_log:
        print(f"  ✅ Latest AIUsageLog found:")
        print(f"     - ID: {latest_log.id}")
        print(f"     - Section: {latest_log.section}")
        print(f"     - Tokens: {latest_log.total_tokens}")
        print(f"     - Created: {latest_log.created_at}")
    else:
        print(f"  ❌ No AIUsageLog entries found")
    print()
    
    # Check AIUsageTracking
    today_tracking = AIUsageTracking.objects.filter(user=user, date=date.today()).first()
    if today_tracking:
        print(f"  ✅ Today's AIUsageTracking found:")
        print(f"     - Date: {today_tracking.date}")
        print(f"     - Total requests: {today_tracking.total_requests}")
        print(f"     - Total tokens: {today_tracking.total_tokens}")
        print(f"     - Success rate: {(today_tracking.successful_requests / today_tracking.total_requests * 100):.1f}%")
    else:
        print(f"  ❌ No AIUsageTracking entry for today")
    print()
    
except Exception as e:
    print(f"  ❌ Error verifying data: {e}\n")

# Test 6: Test API endpoint
print("✓ Test 6: Testing API endpoints...")
try:
    from rest_framework.test import APIClient
    from rest_framework.authtoken.models import Token
    
    client = APIClient()
    
    # Create or get token for user
    token, _ = Token.objects.get_or_create(user=user)
    client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')
    
    # Test logs endpoint
    response = client.get('/api/v1/ai/usage/logs/')
    print(f"  - GET /api/v1/ai/usage/logs/: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"    ✅ Count: {data.get('count', 0)} logs")
    else:
        print(f"    ❌ Failed: {response.data}")
    
    # Test stats endpoint
    response = client.get('/api/v1/ai/usage/logs/stats/')
    print(f"  - GET /api/v1/ai/usage/logs/stats/: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"    ✅ Total requests: {data.get('total_requests', 0)}")
        print(f"    ✅ Total tokens: {data.get('total_tokens', 0)}")
    else:
        print(f"    ❌ Failed: {response.data}")
    print()
    
except Exception as e:
    print(f"  ⚠️  Could not test API endpoints: {e}\n")

# Test 7: Summary
print("=" * 80)
print("SUMMARY")
print("=" * 80)

try:
    total_logs = AIUsageLog.objects.filter(user=user).count()
    total_tracking = AIUsageTracking.objects.filter(user=user).count()
    today_logs = AIUsageLog.objects.filter(user=user, created_at__date=date.today()).count()
    
    print(f"User: {user.username}")
    print(f"  - Total AIUsageLog entries: {total_logs}")
    print(f"  - Total AIUsageTracking entries: {total_tracking}")
    print(f"  - AIUsageLog entries today: {today_logs}")
    
    if total_logs > 0 and total_tracking > 0:
        print(f"\n✅ AI Usage Tracking is WORKING!")
    else:
        print(f"\n⚠️  AI Usage Tracking may not be working properly")
        print(f"   Please check the logs above for errors")
    
except Exception as e:
    print(f"❌ Error in summary: {e}")

print("\n" + "=" * 80)
print("To see detailed logs, check:")
print("  - Docker logs: docker logs <container_id> | grep 'ai_usage_tracker'")
print("  - Application logs: Check your Django log files")
print("  - Admin interface: https://api.fiko.net/admin/AI_model/aiusagelog/")
print("=" * 80)

