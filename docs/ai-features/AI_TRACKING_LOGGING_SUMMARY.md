# AI Usage Tracking - Enhanced Logging & Monitoring

## 🎯 Problem Addressed

**Issue:** AI usage tracking not capturing all user activities properly in both `AIUsageLog` and `AIUsageTracking`.

**Solution:** Added comprehensive logging and diagnostic tools to identify and fix tracking issues.

---

## ✅ What Was Added

### 1. **Enhanced Usage Tracker with Detailed Logging**
**File:** `src/AI_model/services/usage_tracker.py`

Added comprehensive logging at every step:

```python
# Before (no visibility):
def track_ai_usage(...):
    try:
        usage_log = AIUsageLog.log_usage(...)
        usage_tracking.update_stats(...)
    except Exception as e:
        logger.error(f"Error: {e}")

# After (full visibility):
def track_ai_usage(...):
    logger.debug("[TRACK_START] User: john_doe, Section: chat...")
    logger.debug("[TRACK_LOG] Creating AIUsageLog entry...")
    logger.info("[TRACK_LOG_SUCCESS] AIUsageLog created - ID: uuid...")
    logger.debug("[TRACK_AGGREGATE] Updating AIUsageTracking...")
    logger.info("[TRACK_AGGREGATE_SUCCESS] Updated - Requests: 5, Tokens: 1250")
    logger.info("[TRACK_COMPLETE] ✅ Successfully tracked AI usage")
```

#### Log Prefixes for Easy Filtering:
| Prefix | What It Means |
|--------|---------------|
| `[TRACK_START]` | Tracking function called |
| `[TRACK_LOG]` | Creating AIUsageLog |
| `[TRACK_LOG_SUCCESS]` | ✅ AIUsageLog created |
| `[TRACK_AGGREGATE]` | Updating AIUsageTracking |
| `[TRACK_AGGREGATE_NEW]` | New daily record created |
| `[TRACK_AGGREGATE_EXISTS]` | Found existing daily record |
| `[TRACK_AGGREGATE_SUCCESS]` | ✅ AIUsageTracking updated |
| `[TRACK_COMPLETE]` | ✅ Both models updated successfully |
| `[TRACK_ERROR]` | ❌ Validation error |
| `[TRACK_WARNING]` | ⚠️ Warning (e.g., invalid section) |
| `[TRACK_EXCEPTION]` | ❌ Exception with full traceback |

---

### 2. **Diagnostic Test Script**
**File:** `test_ai_usage_tracking.py`

A comprehensive diagnostic script that:
- ✅ Tests model accessibility
- ✅ Verifies user retrieval
- ✅ Counts existing logs
- ✅ Creates test log entries
- ✅ Verifies database saves
- ✅ Tests API endpoints
- ✅ Provides detailed summary

#### Run It:
```bash
cd /Users/nima/Projects/Fiko-Backend
python test_ai_usage_tracking.py
```

#### Expected Output:
```
==================================================
AI USAGE TRACKING DIAGNOSTIC SCRIPT
==================================================

✓ Test 1: Checking if models are accessible...
  ✅ Models are accessible

✓ Test 2: Getting test user...
  ✅ Using user: john_doe (ID: 1)

✓ Test 3: Checking existing logs...
  - AIUsageLog entries: 25
  - AIUsageTracking entries: 3
  ✅ Can query existing logs

✓ Test 4: Tracking test AI usage...
  ✅ Tracking successful!

✓ Test 5: Verifying data was saved...
  ✅ Latest AIUsageLog found
  ✅ Today's AIUsageTracking found

✅ AI Usage Tracking is WORKING!
```

---

### 3. **Comprehensive Monitoring Guide**
**File:** `AI_USAGE_TRACKING_MONITORING.md`

A 500+ line troubleshooting guide covering:
- 🔍 How to diagnose issues
- 📝 How to check Docker logs
- 🔎 Database queries to verify data
- 🔧 API endpoint testing
- 🐛 Common issues and solutions
- 📈 Production monitoring setup
- ✅ Verification checklist

---

## 🔍 How to Find Problems

### Method 1: Run Diagnostic Script (Easiest)

```bash
python test_ai_usage_tracking.py
```

This will tell you immediately if tracking is working.

---

### Method 2: Check Docker Logs

```bash
# Real-time monitoring
docker logs -f <container_id> | grep 'ai_usage_tracker'

# See what's happening
docker logs <container_id> | grep '\[TRACK_'

# Check for errors only
docker logs <container_id> | grep -E 'TRACK_ERROR|TRACK_EXCEPTION'
```

#### What to Look For:

**✅ Good:**
```
[TRACK_START] User: john_doe, Section: chat...
[TRACK_LOG_SUCCESS] AIUsageLog created - ID: uuid-here...
[TRACK_AGGREGATE_SUCCESS] AIUsageTracking updated...
[TRACK_COMPLETE] ✅ Successfully tracked AI usage
```

**❌ Problem:**
```
[TRACK_ERROR] User is None - cannot track usage
[TRACK_ERROR] Section is empty for user john_doe
[TRACK_WARNING] Invalid section 'chatbot' for user john_doe
[TRACK_EXCEPTION] ❌ Error tracking AI usage: IntegrityError
```

---

### Method 3: Check Database Directly

```bash
docker exec -it <container_id> python manage.py dbshell
```

```sql
-- Check if any logs exist
SELECT COUNT(*) FROM ai_usage_log;

-- Check if tracking is being updated
SELECT user_id, date, total_requests, total_tokens 
FROM ai_model_aiusagetracking 
WHERE date = CURRENT_DATE;

-- See recent activity
SELECT section, COUNT(*), SUM(total_tokens)
FROM ai_usage_log
WHERE created_at >= CURRENT_DATE
GROUP BY section;
```

---

### Method 4: Check Admin Interface

Visit:
- **Detailed Logs:** `https://api.pilito.com/admin/AI_model/aiusagelog/`
- **Daily Tracking:** `https://api.pilito.com/admin/AI_model/aiusagetracking/`

**If empty:** Tracking is not working!

---

### Method 5: Test API Endpoints

```bash
# Test retrieval
curl "https://api.pilito.com/api/v1/ai/usage/logs/" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Should return: {"count": X, "results": [...]}
# If count is 0, no tracking is happening!
```

---

## 🐛 Common Issues & Quick Fixes

### Issue 1: No Logs At All

**Cause:** Tracking function not being called

**Check:**
```bash
# Look for TRACK_START in logs
docker logs <container_id> | grep "TRACK_START"

# If empty, tracking is not being called
```

**Fix:**
Add tracking to your AI services:
```python
from AI_model.services import track_ai_usage_safe

# After your AI call
track_ai_usage_safe(
    user=user,
    section='chat',
    prompt_tokens=150,
    completion_tokens=80,
    response_time_ms=1200,
    success=True
)
```

---

### Issue 2: AIUsageLog Works, AIUsageTracking Doesn't

**Cause:** Error in update_stats()

**Check:**
```bash
docker logs <container_id> | grep "TRACK_AGGREGATE"
```

**Should see:**
```
[TRACK_AGGREGATE_SUCCESS] AIUsageTracking updated
```

**If missing:** Check for exceptions in logs

---

### Issue 3: Some Sections Missing

**Cause:** Not all AI services instrumented

**Check:**
```python
# In Django shell
from AI_model.models import AIUsageLog
AIUsageLog.objects.values('section').distinct()

# Compare with:
[choice[0] for choice in AIUsageLog.SECTION_CHOICES]
```

**Fix:** Add tracking to missing services (see integration guide)

---

## 🚀 Deployment Steps

### 1. Deploy Enhanced Tracker

```bash
cd /Users/nima/Projects/Fiko-Backend
git add src/AI_model/services/usage_tracker.py
git add test_ai_usage_tracking.py
git add AI_USAGE_TRACKING_MONITORING.md
git add AI_TRACKING_LOGGING_SUMMARY.md
git commit -m "Add comprehensive logging and monitoring for AI usage tracking"
git push origin main
```

### 2. Update Production

```bash
# On server
docker exec -it <container_id> bash -c "cd /app && git pull"
docker restart <container_id>
```

### 3. Run Diagnostic Test

```bash
# After restart
docker exec -it <container_id> python /app/test_ai_usage_tracking.py
```

### 4. Monitor Logs

```bash
# Watch for tracking activity
docker logs -f <container_id> | grep '\[TRACK_'
```

### 5. Check Admin Interface

Visit: `https://api.pilito.com/admin/AI_model/aiusagelog/`

**Should see:** New entries appearing when AI is used

---

## 📊 What Gets Logged

### For Every AI Request:

1. **Entry Point** (`[TRACK_START]`)
   - User, section, tokens, success status

2. **Validation** (`[TRACK_ERROR]`)
   - If user is None
   - If section is empty
   - If section is invalid

3. **AIUsageLog Creation** (`[TRACK_LOG]`, `[TRACK_LOG_SUCCESS]`)
   - Confirms log was created
   - Shows ID, user, section, tokens

4. **AIUsageTracking Update** (`[TRACK_AGGREGATE]`, `[TRACK_AGGREGATE_SUCCESS]`)
   - Shows if creating new or updating existing
   - Displays current totals after update

5. **Completion** (`[TRACK_COMPLETE]`)
   - Final confirmation both models updated

6. **Errors** (`[TRACK_EXCEPTION]`)
   - Full exception details
   - Complete traceback
   - Never breaks main flow

---

## 🎯 Benefits of Enhanced Logging

### Before:
```
❌ No visibility into tracking
❌ Silent failures
❌ Can't tell if tracking is working
❌ Hard to debug issues
```

### After:
```
✅ See every tracking attempt
✅ Identify exactly where failures occur
✅ Validate inputs before processing
✅ Monitor success/failure rates
✅ Easy to diagnose issues
✅ Never breaks main application flow
```

---

## 📈 Monitoring in Production

### Daily Check:
```bash
# How many logs today?
docker exec -it <container_id> python manage.py shell -c "
from AI_model.models import AIUsageLog
from datetime import date
print(f'Logs today: {AIUsageLog.objects.filter(created_at__date=date.today()).count()}')
"
```

### Weekly Check:
```bash
# Run diagnostic script
docker exec -it <container_id> python /app/test_ai_usage_tracking.py
```

### Alert If:
- No `[TRACK_COMPLETE]` logs in last hour
- Many `[TRACK_ERROR]` or `[TRACK_EXCEPTION]`
- AIUsageLog count not increasing

---

## ✅ Verification Checklist

After deploying, verify:

- [ ] Diagnostic script passes all tests
- [ ] Docker logs show `[TRACK_COMPLETE]` messages
- [ ] Admin interface shows new logs
- [ ] Admin interface shows tracking updates
- [ ] API returns data
- [ ] Database has records
- [ ] No `[TRACK_ERROR]` in logs
- [ ] All AI services instrumented

---

## 📚 Documentation Created

1. **`usage_tracker.py` (Enhanced)** - Comprehensive logging at every step
2. **`test_ai_usage_tracking.py`** - Diagnostic script
3. **`AI_USAGE_TRACKING_MONITORING.md`** - Complete troubleshooting guide
4. **`AI_TRACKING_LOGGING_SUMMARY.md`** - This document

---

## 🎉 Summary

You now have:
- ✅ Detailed logging at every step of tracking
- ✅ Diagnostic script to test the system
- ✅ Comprehensive troubleshooting guide
- ✅ Clear log prefixes for easy filtering
- ✅ Validation and error handling
- ✅ Never breaks main application flow
- ✅ Easy to monitor and debug

**Next Steps:**
1. Deploy the enhanced tracker
2. Run diagnostic script
3. Check Docker logs for `[TRACK_COMPLETE]`
4. Verify admin interface has data
5. Instrument any missing AI services

---

**Last Updated:** 2025-10-11  
**Version:** 1.0  
**Status:** ✅ Ready for Deployment

