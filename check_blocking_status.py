#!/usr/bin/env python
"""Check blocking status and system instruction"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

print('\n' + '='*80)
print('🔍 CHECKING SYSTEM INSTRUCTION & BLOCKING STATUS')
print('='*80)

# بررسی کد فعلی
print('\n1️⃣ Checking current code:')
import inspect
from AI_model.services import gemini_service

# بررسی system_instruction
source = inspect.getsource(gemini_service.GeminiChatService.__init__)

if 'various types of businesses' in source:
    print('   ✅ NEW system_instruction FOUND')
    print('   ✅ Generic instruction for all business types')
else:
    print('   ❌ OLD system_instruction (short version)')

if 'CONTENT PROCESSING GUIDELINES' in source:
    print('   ✅ Content guidelines section FOUND')
else:
    print('   ❌ Content guidelines MISSING')

# بررسی لاگ‌های اخیر
print('\n2️⃣ Recent blocking statistics:')
from AI_model.models import AIUsageLog
from accounts.models import User
from datetime import timedelta
from django.utils import timezone

user = User.objects.get(email='y_motahedin@yahoo.com')

# آخرین 20 AI call
recent_calls = AIUsageLog.objects.filter(
    user=user,
    section='chat',
    created_at__gte=timezone.now() - timedelta(hours=2)
).order_by('-created_at')[:20]

total = recent_calls.count()
failed = recent_calls.filter(success=False).count()
success = recent_calls.filter(success=True).count()

print(f'   Last 2 hours: {total} calls')
print(f'   Success: {success} ({success/total*100 if total else 0:.1f}%)')
print(f'   Failed: {failed} ({failed/total*100 if total else 0:.1f}%)')

# بررسی metadata برای blocking
blocked_count = 0
for log in recent_calls:
    if log.metadata and ('blocked' in str(log.metadata).lower() or 'fallback' in str(log.metadata).lower()):
        blocked_count += 1

print(f'   Blocked/Fallback: {blocked_count} ({blocked_count/total*100 if total else 0:.1f}%)')

print('\n✅ Check complete!')

