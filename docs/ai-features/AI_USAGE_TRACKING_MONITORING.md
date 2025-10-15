# AI Usage Tracking - Monitoring & Troubleshooting Guide

## 🔍 Overview

This guide helps you monitor and troubleshoot the AI Usage Tracking system to ensure **all** AI activities are being captured in both `AIUsageLog` and `AIUsageTracking`.

---

## 🚨 Problem: Tracking Not Working?

If you notice that AI usage is not being logged properly, follow these steps to diagnose and fix the issue.

---

## 📊 Step 1: Run the Diagnostic Script

### Quick Test
```bash
cd /Users/nima/Projects/Fiko-Backend
python test_ai_usage_tracking.py
```

This script will:
- ✅ Check if models are accessible
- ✅ Test user retrieval
- ✅ Count existing logs
- ✅ Create a test log entry
- ✅ Verify data was saved
- ✅ Test API endpoints
- ✅ Show summary statistics

### Expected Output
```
==================================================
AI USAGE TRACKING DIAGNOSTIC SCRIPT
====================================================

✓ Test 1: Checking if models are accessible...
  ✅ Models are accessible

✓ Test 2: Getting test user...
  ✅ Using user: john_doe (ID: 1)

✓ Test 3: Checking existing logs...
  - AIUsageLog entries for this user: 5
  - AIUsageTracking entries for this user: 2
  ✅ Can query existing logs

✓ Test 4: Tracking test AI usage...
  ✅ Tracking successful!
     - AIUsageLog created: ID=uuid-here
       • Total tokens: 150
       • Section: chat
       • Success: True

✓ Test 5: Verifying data was saved to database...
  ✅ Latest AIUsageLog found
  ✅ Today's AIUsageTracking found

✅ AI Usage Tracking is WORKING!
```

---

## 📝 Step 2: Check Docker Logs

### View AI Usage Tracker Logs
```bash
# Real-time logs
docker logs -f <container_id> | grep 'ai_usage_tracker'

# Last 100 lines
docker logs --tail=100 <container_id> | grep 'ai_usage_tracker'

# Search for errors
docker logs <container_id> | grep -i 'TRACK_ERROR\|TRACK_EXCEPTION'
```

### Log Format
All tracking logs are prefixed with `[TRACK_*]`:

| Prefix | Meaning |
|--------|---------|
| `[TRACK_START]` | Function called |
| `[TRACK_LOG]` | Creating AIUsageLog |
| `[TRACK_LOG_SUCCESS]` | AIUsageLog created successfully |
| `[TRACK_AGGREGATE]` | Updating AIUsageTracking |
| `[TRACK_AGGREGATE_SUCCESS]` | AIUsageTracking updated successfully |
| `[TRACK_COMPLETE]` | ✅ Both models updated |
| `[TRACK_ERROR]` | ❌ Validation error |
| `[TRACK_EXCEPTION]` | ❌ Exception occurred |

### Example Good Log
```
2025-10-11 12:00:00 [DEBUG] ai_usage_tracker: [TRACK_START] User: john_doe, Section: chat, Tokens: 150+80, Success: True
2025-10-11 12:00:00 [DEBUG] ai_usage_tracker: [TRACK_LOG] Creating AIUsageLog entry...
2025-10-11 12:00:00 [INFO] ai_usage_tracker: [TRACK_LOG_SUCCESS] AIUsageLog created - ID: uuid-here, User: john_doe, Section: chat, Tokens: 230
2025-10-11 12:00:00 [DEBUG] ai_usage_tracker: [TRACK_AGGREGATE] Getting/Creating AIUsageTracking for user john_doe, date 2025-10-11
2025-10-11 12:00:00 [INFO] ai_usage_tracker: [TRACK_AGGREGATE_SUCCESS] AIUsageTracking updated - User: john_doe, Date: 2025-10-11, Total Requests: 5, Total Tokens: 1250
2025-10-11 12:00:00 [INFO] ai_usage_tracker: [TRACK_COMPLETE] ✅ Successfully tracked AI usage - User: john_doe, Section: chat, Tokens: 230, Status: SUCCESS
```

### Example Error Log
```
2025-10-11 12:00:00 [ERROR] ai_usage_tracker: [TRACK_ERROR] User is None - cannot track usage
```

---

## 🔎 Step 3: Check Database Directly

### Connect to Database
```bash
# Via Docker
docker exec -it <container_id> python manage.py dbshell

# Or using psql directly
psql -h localhost -U your_user -d FikoDB
```

### Check AIUsageLog
```sql
-- Count total logs
SELECT COUNT(*) as total_logs FROM ai_usage_log;

-- Count logs per user
SELECT u.username, COUNT(*) as log_count 
FROM ai_usage_log a
JOIN accounts_user u ON a.user_id = u.id
GROUP BY u.username
ORDER BY log_count DESC;

-- Check recent logs
SELECT 
    id, 
    user_id, 
    section, 
    total_tokens, 
    success, 
    created_at
FROM ai_usage_log
ORDER BY created_at DESC
LIMIT 10;

-- Check logs by section
SELECT section, COUNT(*) as count, SUM(total_tokens) as total_tokens
FROM ai_usage_log
GROUP BY section
ORDER BY count DESC;
```

### Check AIUsageTracking
```sql
-- Count tracking records
SELECT COUNT(*) FROM ai_model_aiusagetracking;

-- Check today's usage
SELECT 
    u.username,
    date,
    total_requests,
    total_tokens,
    successful_requests,
    failed_requests
FROM ai_model_aiusagetracking a
JOIN accounts_user u ON a.user_id = u.id
WHERE date = CURRENT_DATE
ORDER BY total_requests DESC;

-- Check total usage per user
SELECT 
    u.username,
    SUM(total_requests) as total_requests,
    SUM(total_tokens) as total_tokens,
    ROUND(AVG(average_response_time_ms)) as avg_response_time
FROM ai_model_aiusagetracking a
JOIN accounts_user u ON a.user_id = u.id
GROUP BY u.username
ORDER BY total_requests DESC;
```

---

## 🔧 Step 4: Check API Endpoints

### Test Logging Endpoint
```bash
curl -X POST https://api.fiko.net/api/v1/ai/usage/logs/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "section": "chat",
    "prompt_tokens": 100,
    "completion_tokens": 50,
    "response_time_ms": 1000,
    "success": true,
    "metadata": {"test": "manual_test"}
  }' \
  -v
```

**Expected:** HTTP 201 Created

### Test Retrieval Endpoint
```bash
curl "https://api.fiko.net/api/v1/ai/usage/logs/?limit=10" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -v
```

**Expected:** HTTP 200 with list of logs

### Test Statistics Endpoint
```bash
curl "https://api.fiko.net/api/v1/ai/usage/logs/stats/?days=7" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -v
```

**Expected:** HTTP 200 with statistics

---

## 🎯 Step 5: Check If AI Services Are Instrumented

### Services That SHOULD Have Tracking

Check these files to ensure they're calling the tracker:

#### 1. Gemini Chat Service
**File:** `src/AI_model/services/gemini_service.py`

```python
# Should have this import
from AI_model.services import track_ai_usage_safe

# Should call this after AI requests
track_ai_usage_safe(
    user=self.user,
    section='chat',
    prompt_tokens=...,
    completion_tokens=...,
    response_time_ms=...,
    success=True
)
```

#### 2. RAG Service
**File:** `src/AI_model/services/context_retriever.py` or similar

Should track with `section='rag_pipeline'`

#### 3. Session Memory
**File:** `src/AI_model/services/session_memory_manager_v2.py`

Should track with `section='session_memory'`

#### 4. Message Integration
**File:** `src/AI_model/services/message_integration.py`

Should track automatic message processing

### Quick Search
```bash
# Check which files import the tracker
grep -r "track_ai_usage" src/AI_model/

# Check which files DON'T have tracking
grep -r "gemini\|openai\|generate" src/AI_model/services/ | grep -v "track_ai_usage"
```

---

## 🐛 Common Issues & Solutions

### Issue 1: No Logs Being Created

**Symptoms:**
- Empty admin interface
- API returns empty results
- Database has no records

**Possible Causes:**
1. ❌ Tracking function not being called
2. ❌ User is None
3. ❌ Section name invalid

**Solutions:**
```bash
# 1. Check if tracking is being called
docker logs <container_id> | grep "TRACK_START"

# If no output, tracking is not being called at all

# 2. Add tracking to your AI service
# See AI_USAGE_TRACKER_INTEGRATION.md

# 3. Check for validation errors
docker logs <container_id> | grep "TRACK_ERROR"
```

---

### Issue 2: AIUsageLog Created but AIUsageTracking Not Updated

**Symptoms:**
- AIUsageLog has entries
- AIUsageTracking is empty or not incrementing

**Check Logs:**
```bash
docker logs <container_id> | grep "TRACK_AGGREGATE"
```

**Look for:**
- `[TRACK_AGGREGATE_SUCCESS]` - Should appear after each log
- `[TRACK_EXCEPTION]` - Indicates an error

**Solution:**
```python
# Check if AIUsageTracking.update_stats() is working
from AI_model.models import AIUsageTracking
from django.contrib.auth import get_user_model
from datetime import date

User = get_user_model()
user = User.objects.first()

# Get or create today's tracking
tracking, created = AIUsageTracking.objects.get_or_create(
    user=user,
    date=date.today(),
    defaults={'total_requests': 0, 'total_tokens': 0}
)

# Try updating
tracking.update_stats(prompt_tokens=100, completion_tokens=50, success=True)
print(f"Total requests: {tracking.total_requests}")
```

---

### Issue 3: Some AI Requests Not Being Tracked

**Symptoms:**
- Some logs appear, but not all
- Certain sections missing

**Check:**
1. Which AI services are instrumented?
2. Are there any errors for specific sections?

```bash
# Check which sections have logs
docker exec -it <container_id> python manage.py shell
>>> from AI_model.models import AIUsageLog
>>> AIUsageLog.objects.values('section').distinct()

# Compare with expected sections
>>> [choice[0] for choice in AIUsageLog.SECTION_CHOICES]
```

**Solution:**
Instrument the missing AI services following `AI_USAGE_TRACKER_INTEGRATION.md`

---

### Issue 4: Tracking Errors Breaking AI Service

**Symptoms:**
- AI requests fail when tracking is added
- Exceptions from tracking service

**This should NEVER happen** because we use `track_ai_usage_safe()`

**If it does:**
```bash
# Check logs for exceptions
docker logs <container_id> | grep "TRACK_EXCEPTION"

# Verify you're using the safe version
grep -r "track_ai_usage_safe" src/
```

**Solution:**
Always use `track_ai_usage_safe()` not `track_ai_usage()`

---

## 📈 Step 6: Monitor in Production

### Set Up Alerts

Create alerts for:
1. **No logs in last hour** - AI might not be working
2. **High failure rate** - Check `success=False` logs
3. **Slow response times** - Monitor `response_time_ms`

### Regular Checks

**Daily:**
```bash
# Check today's total usage
curl "https://api.fiko.net/api/v1/ai/usage/logs/stats/?days=1" \
  -H "Authorization: Bearer ADMIN_TOKEN"
```

**Weekly:**
```bash
# Check section breakdown
curl "https://api.fiko.net/api/v1/ai/usage/logs/stats/?days=7" \
  -H "Authorization: Bearer ADMIN_TOKEN"
```

**Monthly:**
```bash
# Check global usage
curl "https://api.fiko.net/api/v1/ai/usage/logs/global/?days=30" \
  -H "Authorization: Bearer ADMIN_TOKEN"
```

---

## 🔧 Step 7: Enable Debug Logging

### Temporarily Enable Debug Logging

**File:** `src/core/settings/common.py` or `production.py`

```python
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'ai_usage_tracker': {
            'handlers': ['console'],
            'level': 'DEBUG',  # Changed from INFO
            'propagate': False,
        },
    },
}
```

**Restart:**
```bash
docker restart <container_id>
```

---

## ✅ Verification Checklist

Use this checklist to verify everything is working:

- [ ] Diagnostic script passes all tests
- [ ] `docker logs` shows `[TRACK_COMPLETE]` messages
- [ ] Admin interface shows logs: `/admin/AI_model/aiusagelog/`
- [ ] Admin interface shows tracking: `/admin/AI_model/aiusagetracking/`
- [ ] API endpoints return data
- [ ] Database queries show records
- [ ] All AI services are instrumented
- [ ] No `[TRACK_ERROR]` or `[TRACK_EXCEPTION]` in logs

---

## 🆘 Still Not Working?

If tracking still isn't working after following this guide:

### 1. Collect Diagnostic Information
```bash
# Run diagnostic script
python test_ai_usage_tracking.py > diagnostic_output.txt 2>&1

# Get recent logs
docker logs --tail=500 <container_id> | grep "ai_usage_tracker" > tracker_logs.txt

# Check database
docker exec -it <container_id> python manage.py shell -c "
from AI_model.models import AIUsageLog, AIUsageTracking
print(f'AIUsageLog count: {AIUsageLog.objects.count()}')
print(f'AIUsageTracking count: {AIUsageTracking.objects.count()}')
" > db_counts.txt
```

### 2. Check Files Are Deployed
```bash
# Verify usage_tracker.py exists
docker exec -it <container_id> ls -la /app/src/AI_model/services/usage_tracker.py

# Verify it's the latest version
docker exec -it <container_id> cat /app/src/AI_model/services/usage_tracker.py | grep "TRACK_START"
```

### 3. Manual Test
```bash
docker exec -it <container_id> python manage.py shell

>>> from AI_model.services import track_ai_usage_safe
>>> from django.contrib.auth import get_user_model
>>> User = get_user_model()
>>> user = User.objects.first()
>>> log, tracking = track_ai_usage_safe(user, 'chat', 100, 50, 1000, True)
>>> print(f"Log: {log}, Tracking: {tracking}")
```

---

## 📞 Need Help?

Contact the development team with:
1. Output from `test_ai_usage_tracking.py`
2. Recent logs from `docker logs`
3. Database query results
4. Manual test results

---

**Last Updated:** 2025-10-11  
**Version:** 1.0

