#!/bin/bash
################################################################################
# AI Usage Tracking Diagnostic Script for Production Server
# 
# This script diagnoses AI usage tracking issues on production servers
# Usage: ./diagnose_ai_tracking.sh [container_id]
#
# If container_id is not provided, it will try to detect it automatically
################################################################################

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get container ID
CONTAINER_ID=${1:-$(docker ps --filter "name=fiko\|backend\|django" --format "{{.ID}}" | head -1)}

if [ -z "$CONTAINER_ID" ]; then
    echo -e "${RED}❌ Error: Could not find container${NC}"
    echo "Usage: $0 [container_id]"
    echo "Or: docker ps  # to list containers"
    exit 1
fi

echo "================================================================================"
echo "AI USAGE TRACKING DIAGNOSTIC - PRODUCTION SERVER"
echo "================================================================================"
echo -e "${BLUE}Container ID:${NC} $CONTAINER_ID"
echo ""

# Test 1: Check if models are accessible
echo -e "${YELLOW}[1/8]${NC} Checking if AI models are accessible..."
docker exec -it $CONTAINER_ID python manage.py shell -c "
from AI_model.models import AIUsageLog, AIUsageTracking
print('✅ Models are accessible')
print(f'   - AIUsageLog: {AIUsageLog._meta.db_table}')
print(f'   - AIUsageTracking: {AIUsageTracking._meta.db_table}')
" 2>/dev/null

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Models OK${NC}"
else
    echo -e "${RED}❌ Models not accessible${NC}"
    exit 1
fi
echo ""

# Test 2: Check database tables exist
echo -e "${YELLOW}[2/8]${NC} Checking database tables..."
docker exec -it $CONTAINER_ID python manage.py dbshell -c "
SELECT COUNT(*) as log_count FROM ai_usage_log;
SELECT COUNT(*) as tracking_count FROM ai_model_aiusagetracking;
" 2>/dev/null || echo -e "${RED}❌ Database check failed${NC}"
echo ""

# Test 3: Count existing records
echo -e "${YELLOW}[3/8]${NC} Counting existing records..."
docker exec -it $CONTAINER_ID python manage.py shell -c "
from AI_model.models import AIUsageLog, AIUsageTracking
from datetime import date

total_logs = AIUsageLog.objects.count()
total_tracking = AIUsageTracking.objects.count()
logs_today = AIUsageLog.objects.filter(created_at__date=date.today()).count()
tracking_today = AIUsageTracking.objects.filter(date=date.today()).count()

print(f'Total AIUsageLog entries: {total_logs}')
print(f'Total AIUsageTracking entries: {total_tracking}')
print(f'Logs created today: {logs_today}')
print(f'Tracking records for today: {tracking_today}')

if total_logs > 0:
    print('✅ Some logs exist')
else:
    print('⚠️  No logs found - tracking may not be working')
"
echo ""

# Test 4: Check if tracking service is available
echo -e "${YELLOW}[4/8]${NC} Checking tracking service..."
docker exec -it $CONTAINER_ID python manage.py shell -c "
try:
    from AI_model.services import track_ai_usage_safe
    print('✅ Tracking service is available')
    print(f'   Function: {track_ai_usage_safe.__name__}')
except ImportError as e:
    print(f'❌ Tracking service not available: {e}')
"
echo ""

# Test 5: Create test log
echo -e "${YELLOW}[5/8]${NC} Creating test log entry..."
docker exec -it $CONTAINER_ID python manage.py shell -c "
from django.contrib.auth import get_user_model
from AI_model.services import track_ai_usage_safe
from datetime import date

User = get_user_model()
user = User.objects.first()

if not user:
    print('❌ No users found in database')
else:
    print(f'Using user: {user.username} (ID: {user.id})')
    
    # Track test usage
    log, tracking = track_ai_usage_safe(
        user=user,
        section='chat',
        prompt_tokens=100,
        completion_tokens=50,
        response_time_ms=1000,
        success=True,
        metadata={'test': 'production_diagnostic', 'script': 'diagnose_ai_tracking.sh'}
    )
    
    if log and tracking:
        print(f'✅ Test log created successfully!')
        print(f'   - Log ID: {log.id}')
        print(f'   - Total tokens: {log.total_tokens}')
        print(f'   - Tracking total requests: {tracking.total_requests}')
        print(f'   - Tracking total tokens: {tracking.total_tokens}')
    else:
        print('❌ Failed to create test log')
        print('   Check Docker logs for [TRACK_ERROR] or [TRACK_EXCEPTION]')
"
echo ""

# Test 6: Check recent Docker logs for tracking activity
echo -e "${YELLOW}[6/8]${NC} Checking Docker logs for tracking activity..."
TRACK_COUNT=$(docker logs --since 1h $CONTAINER_ID 2>&1 | grep -c '\[TRACK_COMPLETE\]' || echo "0")
ERROR_COUNT=$(docker logs --since 1h $CONTAINER_ID 2>&1 | grep -cE '\[TRACK_ERROR\]|\[TRACK_EXCEPTION\]' || echo "0")

echo "Last hour:"
echo "  - Successful tracking: $TRACK_COUNT"
echo "  - Errors: $ERROR_COUNT"

if [ "$TRACK_COUNT" -gt 0 ]; then
    echo -e "${GREEN}✅ Tracking is active${NC}"
else
    echo -e "${YELLOW}⚠️  No tracking activity in last hour${NC}"
fi

if [ "$ERROR_COUNT" -gt 0 ]; then
    echo -e "${RED}⚠️  Found $ERROR_COUNT errors${NC}"
    echo ""
    echo "Recent errors:"
    docker logs --since 1h $CONTAINER_ID 2>&1 | grep -E '\[TRACK_ERROR\]|\[TRACK_EXCEPTION\]' | tail -3
fi
echo ""

# Test 7: Check API endpoints
echo -e "${YELLOW}[7/8]${NC} Testing API endpoints (requires auth token)..."
echo "You can manually test with:"
echo "  curl -X POST https://api.pilito.com/api/v1/ai/usage/logs/ \\"
echo "    -H 'Authorization: Bearer YOUR_TOKEN' \\"
echo "    -H 'Content-Type: application/json' \\"
echo "    -d '{\"section\":\"chat\",\"prompt_tokens\":100,\"completion_tokens\":50}'"
echo ""

# Test 8: Check section breakdown
echo -e "${YELLOW}[8/8]${NC} Section breakdown..."
docker exec -it $CONTAINER_ID python manage.py shell -c "
from AI_model.models import AIUsageLog
from django.db.models import Count, Sum

breakdown = AIUsageLog.objects.values('section').annotate(
    count=Count('id'),
    total_tokens=Sum('total_tokens')
).order_by('-count')

if breakdown:
    print('Logs by section:')
    for item in breakdown:
        print(f\"  - {item['section']}: {item['count']} requests, {item['total_tokens'] or 0} tokens\")
else:
    print('⚠️  No logs found')
"
echo ""

# Summary
echo "================================================================================"
echo "SUMMARY"
echo "================================================================================"

docker exec -it $CONTAINER_ID python manage.py shell -c "
from AI_model.models import AIUsageLog, AIUsageTracking
from datetime import date

total_logs = AIUsageLog.objects.count()
total_tracking = AIUsageTracking.objects.count()
logs_today = AIUsageLog.objects.filter(created_at__date=date.today()).count()

print(f'Total Logs: {total_logs}')
print(f'Total Tracking Records: {total_tracking}')
print(f'Logs Today: {logs_today}')

if total_logs > 0 and total_tracking > 0:
    print('')
    print('✅ AI Usage Tracking is WORKING!')
    if logs_today == 0:
        print('⚠️  But no logs created today - check if AI is being used')
else:
    print('')
    print('❌ AI Usage Tracking may NOT be working properly')
    print('')
    print('Troubleshooting steps:')
    print('1. Check Docker logs: docker logs --tail=100 $CONTAINER_ID | grep TRACK_')
    print('2. Check if services are instrumented (see integration guide)')
    print('3. Verify usage_tracker.py is deployed')
"

echo ""
echo "================================================================================"
echo "ADDITIONAL COMMANDS"
echo "================================================================================"
echo "View real-time tracking logs:"
echo "  docker logs -f $CONTAINER_ID | grep '\[TRACK_'"
echo ""
echo "Check for errors:"
echo "  docker logs $CONTAINER_ID | grep -E 'TRACK_ERROR|TRACK_EXCEPTION'"
echo ""
echo "Check database directly:"
echo "  docker exec -it $CONTAINER_ID python manage.py dbshell"
echo ""
echo "View admin interface:"
echo "  https://api.pilito.com/admin/AI_model/aiusagelog/"
echo "================================================================================"

