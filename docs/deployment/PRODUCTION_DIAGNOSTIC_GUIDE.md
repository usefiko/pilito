# Production Server - AI Tracking Diagnostic Guide

## 🚀 Quick Start

### Step 1: Copy Diagnostic Script to Server

```bash
# From your local machine
cd /Users/nima/Projects/Fiko-Backend
scp diagnose_ai_tracking.sh ubuntu@your-server-ip:~/
```

### Step 2: SSH to Server

```bash
ssh ubuntu@your-server-ip
```

### Step 3: Run Diagnostic

```bash
# Make it executable
chmod +x diagnose_ai_tracking.sh

# Run with container ID
./diagnose_ai_tracking.sh 7205c74c3532

# Or let it auto-detect
./diagnose_ai_tracking.sh
```

---

## 📋 What the Script Does

The diagnostic script automatically:
1. ✅ Checks if AI models are accessible
2. ✅ Verifies database tables exist
3. ✅ Counts existing records
4. ✅ Tests tracking service availability
5. ✅ Creates a test log entry
6. ✅ Checks Docker logs for tracking activity
7. ✅ Shows section breakdown
8. ✅ Provides summary and troubleshooting tips

---

## 🔍 Manual Commands (If Script Doesn't Work)

### Quick Status Check

```bash
CONTAINER_ID=7205c74c3532

echo "=== Quick AI Tracking Status ==="
echo "Total logs:"
docker exec -it $CONTAINER_ID python manage.py shell -c "
from AI_model.models import AIUsageLog
print(AIUsageLog.objects.count())
"

echo "Logs today:"
docker exec -it $CONTAINER_ID python manage.py shell -c "
from AI_model.models import AIUsageLog
from datetime import date
print(AIUsageLog.objects.filter(created_at__date=date.today()).count())
"

echo "Tracking in last hour:"
docker logs --since 1h $CONTAINER_ID 2>&1 | grep -c '\[TRACK_COMPLETE\]' || echo "0"
```

---

### Check Docker Logs

```bash
CONTAINER_ID=7205c74c3532

# Real-time tracking logs
docker logs -f $CONTAINER_ID | grep '\[TRACK_'

# Last 100 tracking events
docker logs --tail=100 $CONTAINER_ID | grep '\[TRACK_'

# Check for errors
docker logs $CONTAINER_ID | grep -E 'TRACK_ERROR|TRACK_EXCEPTION'

# Count successful tracking
docker logs --since 1h $CONTAINER_ID | grep -c 'TRACK_COMPLETE'
```

---

### Create Test Log

```bash
CONTAINER_ID=7205c74c3532

docker exec -it $CONTAINER_ID python manage.py shell << 'EOF'
from django.contrib.auth import get_user_model
from AI_model.services import track_ai_usage_safe

User = get_user_model()
user = User.objects.first()

log, tracking = track_ai_usage_safe(
    user=user,
    section='chat',
    prompt_tokens=100,
    completion_tokens=50,
    response_time_ms=1000,
    success=True,
    metadata={'test': 'manual_ssh_test'}
)

if log and tracking:
    print(f"✅ Success! Log ID: {log.id}")
    print(f"   Tracking: {tracking.total_requests} requests, {tracking.total_tokens} tokens")
else:
    print("❌ Failed - check logs")
EOF
```

---

### Check Database Directly

```bash
CONTAINER_ID=7205c74c3532

docker exec -it $CONTAINER_ID python manage.py dbshell << 'EOF'
-- Count logs
SELECT COUNT(*) as total_logs FROM ai_usage_log;

-- Logs by section
SELECT section, COUNT(*) as count, SUM(total_tokens) as tokens
FROM ai_usage_log
GROUP BY section
ORDER BY count DESC;

-- Today's tracking
SELECT u.username, date, total_requests, total_tokens
FROM ai_model_aiusagetracking a
JOIN accounts_user u ON a.user_id = u.id
WHERE date = CURRENT_DATE;

-- Recent logs
SELECT id, section, total_tokens, success, created_at
FROM ai_usage_log
ORDER BY created_at DESC
LIMIT 10;

\q
EOF
```

---

### Test API Endpoint

```bash
# Get an auth token first
TOKEN="your-auth-token-here"

# Create test log
curl -X POST https://api.fiko.net/api/v1/ai/usage/logs/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "section": "chat",
    "prompt_tokens": 100,
    "completion_tokens": 50,
    "response_time_ms": 1000,
    "success": true,
    "metadata": {"test": "api_test"}
  }'

# Get logs
curl "https://api.fiko.net/api/v1/ai/usage/logs/?limit=5" \
  -H "Authorization: Bearer $TOKEN"

# Get statistics
curl "https://api.fiko.net/api/v1/ai/usage/logs/stats/?days=7" \
  -H "Authorization: Bearer $TOKEN"
```

---

## 🎯 One-Line Quick Checks

### Check if tracking is working at all

```bash
docker logs --since 1h 7205c74c3532 | grep -c 'TRACK_COMPLETE' && echo "✅ Tracking is working" || echo "❌ No tracking detected"
```

### Count total logs

```bash
docker exec -it 7205c74c3532 python manage.py shell -c "from AI_model.models import AIUsageLog; print(f'Total logs: {AIUsageLog.objects.count()}')"
```

### Count logs today

```bash
docker exec -it 7205c74c3532 python manage.py shell -c "from AI_model.models import AIUsageLog; from datetime import date; print(f'Logs today: {AIUsageLog.objects.filter(created_at__date=date.today()).count()}')"
```

### Check for errors

```bash
docker logs --since 1h 7205c74c3532 | grep -E 'TRACK_ERROR|TRACK_EXCEPTION' | tail -5
```

---

## 🐛 Common Issues & Quick Fixes

### Issue 1: Script Shows "No tracking activity"

**Check:**
```bash
# Is tracking being called at all?
docker logs 7205c74c3532 | grep 'TRACK_START'
```

**If no output:** Tracking function is not being called
**Fix:** AI services need to be instrumented (add tracking calls)

---

### Issue 2: "User is None" Errors

**Check:**
```bash
docker logs 7205c74c3532 | grep 'User is None'
```

**Fix:** Ensure user object is passed to tracking function

---

### Issue 3: Database Empty

**Check:**
```bash
docker exec -it 7205c74c3532 python manage.py shell -c "from AI_model.models import AIUsageLog; print(AIUsageLog.objects.count())"
```

**If 0:** No logs have been created
**Fix:** Check if AI services are using the tracker

---

## 📊 Expected Output (Working System)

### Diagnostic Script Output:

```
================================================================================
AI USAGE TRACKING DIAGNOSTIC - PRODUCTION SERVER
================================================================================
Container ID: 7205c74c3532

[1/8] Checking if AI models are accessible...
✅ Models OK

[2/8] Checking database tables...
(table exists)

[3/8] Counting existing records...
Total AIUsageLog entries: 45
Total AIUsageTracking entries: 5
Logs created today: 12
Tracking records for today: 1
✅ Some logs exist

[4/8] Checking tracking service...
✅ Tracking service is available

[5/8] Creating test log entry...
Using user: john_doe (ID: 1)
✅ Test log created successfully!
   - Log ID: uuid-here
   - Total tokens: 150
   - Tracking total requests: 13
   - Tracking total tokens: 3250

[6/8] Checking Docker logs for tracking activity...
Last hour:
  - Successful tracking: 8
  - Errors: 0
✅ Tracking is active

[7/8] Testing API endpoints...
(instructions)

[8/8] Section breakdown...
Logs by section:
  - chat: 30 requests, 8500 tokens
  - rag_pipeline: 10 requests, 2800 tokens
  - prompt_generation: 5 requests, 950 tokens

================================================================================
SUMMARY
================================================================================
Total Logs: 45
Total Tracking Records: 5
Logs Today: 13

✅ AI Usage Tracking is WORKING!
```

---

### Docker Logs (Good):

```bash
$ docker logs --tail=10 7205c74c3532 | grep '\[TRACK_'

[TRACK_START] User: john_doe, Section: chat, Tokens: 150+80
[TRACK_LOG_SUCCESS] AIUsageLog created - ID: abc-123, Tokens: 230
[TRACK_AGGREGATE_SUCCESS] Total Requests: 5, Total Tokens: 1250
[TRACK_COMPLETE] ✅ Successfully tracked AI usage
```

---

## 🔧 Deploy Latest Changes

If tracking is not working, deploy the latest code:

```bash
# On production server
cd ~/fiko-backend  # or your project directory

# Pull latest code
git pull origin main

# Restart container
docker restart 7205c74c3532

# Wait 10 seconds
sleep 10

# Run diagnostic again
./diagnose_ai_tracking.sh 7205c74c3532
```

---

## 📞 Next Steps After Running Diagnostic

1. **If script shows "✅ WORKING":**
   - Great! Tracking is functioning
   - Monitor regularly with: `docker logs -f CONTAINER | grep TRACK_`

2. **If script shows errors:**
   - Note the specific error messages
   - Check the troubleshooting guide
   - Review which AI services need instrumentation

3. **If no logs at all:**
   - Tracking is not being called
   - Review AI services to add tracking calls
   - See `AI_USAGE_TRACKER_INTEGRATION.md`

---

## 🎓 Understanding the Output

| Output | Meaning |
|--------|---------|
| `✅ Some logs exist` | At least one log has been created |
| `⚠️ No logs found` | No logs ever created - tracking not working |
| `✅ Tracking is active` | Tracking happened in last hour |
| `⚠️ No tracking activity` | No tracking in last hour |
| `❌ Failed to create test log` | Test failed - check errors |

---

## 📱 Quick Commands Reference Card

```bash
# Save these for quick access

# Run full diagnostic
./diagnose_ai_tracking.sh 7205c74c3532

# Watch logs live
docker logs -f 7205c74c3532 | grep '\[TRACK_'

# Count logs
docker exec -it 7205c74c3532 python manage.py shell -c "from AI_model.models import AIUsageLog; print(AIUsageLog.objects.count())"

# Create test
docker exec -it 7205c74c3532 python manage.py shell -c "from django.contrib.auth import get_user_model; from AI_model.services import track_ai_usage_safe; u=get_user_model().objects.first(); l,t=track_ai_usage_safe(u,'chat',100,50,1000,True); print(f'Success: {l is not None}')"

# Check errors
docker logs 7205c74c3532 | grep -E 'TRACK_ERROR|TRACK_EXCEPTION'

# Restart
docker restart 7205c74c3532
```

---

**Last Updated:** 2025-10-11  
**Version:** 1.0  
**For:** Production Server Diagnostics

