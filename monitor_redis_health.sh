#!/bin/bash

# Redis Health Monitor
# Monitors Redis status and alerts if issues are detected

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "🔍 Redis Health Monitor"
echo "======================="
echo ""

# Find Redis container
REDIS_CONTAINER=$(docker ps | grep redis | awk '{print $1}')

if [ -z "$REDIS_CONTAINER" ]; then
    echo -e "${RED}❌ No Redis container found!${NC}"
    echo "Please start your Redis container first."
    exit 1
fi

echo -e "${GREEN}✅ Redis container found: $REDIS_CONTAINER${NC}"
echo ""

# Function to get Redis info
get_redis_info() {
    docker exec $REDIS_CONTAINER redis-cli $1 2>&1
}

# 1. Check if Redis is responding
echo "1️⃣  Checking Redis connectivity..."
PING_RESULT=$(get_redis_info "PING")
if [ "$PING_RESULT" = "PONG" ]; then
    echo -e "${GREEN}   ✅ Redis is responding${NC}"
else
    echo -e "${RED}   ❌ Redis is not responding: $PING_RESULT${NC}"
    exit 1
fi
echo ""

# 2. Check Redis role (master/slave)
echo "2️⃣  Checking Redis role..."
ROLE=$(get_redis_info "INFO replication" | grep "role:" | cut -d: -f2 | tr -d '\r\n')
if [ "$ROLE" = "master" ]; then
    echo -e "${GREEN}   ✅ Redis is in MASTER mode${NC}"
elif [ "$ROLE" = "slave" ]; then
    echo -e "${RED}   ❌ Redis is in SLAVE/REPLICA mode (READ-ONLY!)${NC}"
    echo "   This is the cause of your write errors."
    echo "   Run: ./fix_redis_readonly.sh to fix"
else
    echo -e "${YELLOW}   ⚠️  Unknown role: $ROLE${NC}"
fi
echo ""

# 3. Check memory usage
echo "3️⃣  Checking memory usage..."
USED_MEMORY=$(get_redis_info "INFO memory" | grep "used_memory_human:" | cut -d: -f2 | tr -d '\r\n ')
MAX_MEMORY=$(get_redis_info "CONFIG GET maxmemory" | tail -n 1 | tr -d '\r\n')
if [ "$MAX_MEMORY" = "0" ]; then
    MAX_MEMORY="unlimited"
else
    MAX_MEMORY=$(echo "scale=2; $MAX_MEMORY/1024/1024" | bc)"M"
fi

echo "   Used Memory: $USED_MEMORY"
echo "   Max Memory: $MAX_MEMORY"

# Get memory percentage
USED_MEMORY_BYTES=$(get_redis_info "INFO memory" | grep "used_memory:" | grep -v "human" | head -n 1 | cut -d: -f2 | tr -d '\r\n ')
MAX_MEMORY_BYTES=$(get_redis_info "CONFIG GET maxmemory" | tail -n 1 | tr -d '\r\n')

if [ "$MAX_MEMORY_BYTES" != "0" ] && [ -n "$USED_MEMORY_BYTES" ] && [ -n "$MAX_MEMORY_BYTES" ]; then
    MEMORY_PCT=$(echo "scale=2; ($USED_MEMORY_BYTES/$MAX_MEMORY_BYTES)*100" | bc)
    if (( $(echo "$MEMORY_PCT > 90" | bc -l) )); then
        echo -e "${RED}   ❌ Memory usage is critical: ${MEMORY_PCT}%${NC}"
        echo "   Consider increasing maxmemory or clearing data"
    elif (( $(echo "$MEMORY_PCT > 75" | bc -l) )); then
        echo -e "${YELLOW}   ⚠️  Memory usage is high: ${MEMORY_PCT}%${NC}"
    else
        echo -e "${GREEN}   ✅ Memory usage is healthy: ${MEMORY_PCT}%${NC}"
    fi
else
    echo -e "${GREEN}   ✅ No memory limit set${NC}"
fi
echo ""

# 4. Check connected clients
echo "4️⃣  Checking connected clients..."
CONNECTED_CLIENTS=$(get_redis_info "INFO clients" | grep "connected_clients:" | cut -d: -f2 | tr -d '\r\n ')
echo "   Connected clients: $CONNECTED_CLIENTS"
if [ "$CONNECTED_CLIENTS" -gt 100 ]; then
    echo -e "${YELLOW}   ⚠️  High number of clients${NC}"
else
    echo -e "${GREEN}   ✅ Normal client count${NC}"
fi
echo ""

# 5. Check key count
echo "5️⃣  Checking database stats..."
DB_KEYS=$(get_redis_info "DBSIZE" | tr -d '\r\n')
echo "   Total keys: $DB_KEYS"
echo ""

# 6. Check for errors
echo "6️⃣  Checking for recent errors..."
REJECTED_CONNECTIONS=$(get_redis_info "INFO stats" | grep "rejected_connections:" | cut -d: -f2 | tr -d '\r\n ')
EVICTED_KEYS=$(get_redis_info "INFO stats" | grep "evicted_keys:" | cut -d: -f2 | tr -d '\r\n ')

if [ "$REJECTED_CONNECTIONS" != "0" ] && [ -n "$REJECTED_CONNECTIONS" ]; then
    echo -e "${RED}   ❌ Rejected connections: $REJECTED_CONNECTIONS${NC}"
else
    echo -e "${GREEN}   ✅ No rejected connections${NC}"
fi

if [ "$EVICTED_KEYS" != "0" ] && [ -n "$EVICTED_KEYS" ]; then
    echo -e "${YELLOW}   ⚠️  Evicted keys: $EVICTED_KEYS (consider increasing memory)${NC}"
else
    echo -e "${GREEN}   ✅ No evicted keys${NC}"
fi
echo ""

# 7. Check uptime
echo "7️⃣  Checking uptime..."
UPTIME_SECONDS=$(get_redis_info "INFO server" | grep "uptime_in_seconds:" | cut -d: -f2 | tr -d '\r\n ')
UPTIME_DAYS=$(echo "scale=2; $UPTIME_SECONDS/86400" | bc)
echo "   Uptime: ${UPTIME_DAYS} days (${UPTIME_SECONDS} seconds)"
echo ""

# 8. Test write operation
echo "8️⃣  Testing write operation..."
WRITE_TEST=$(get_redis_info "SET health_check_test 'OK'" 2>&1)
if [ "$WRITE_TEST" = "OK" ]; then
    echo -e "${GREEN}   ✅ Write operation successful${NC}"
    get_redis_info "DEL health_check_test" > /dev/null
else
    echo -e "${RED}   ❌ Write operation failed: $WRITE_TEST${NC}"
    echo "   This confirms Redis is in READ-ONLY mode"
    echo "   Run: ./fix_redis_readonly.sh to fix"
fi
echo ""

# Summary
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 Summary"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━"

ISSUES=0

if [ "$ROLE" != "master" ]; then
    echo -e "${RED}🔴 CRITICAL: Redis is not in master mode${NC}"
    ((ISSUES++))
fi

if [ "$WRITE_TEST" != "OK" ]; then
    echo -e "${RED}🔴 CRITICAL: Cannot write to Redis${NC}"
    ((ISSUES++))
fi

if [ "$ISSUES" -eq 0 ]; then
    echo -e "${GREEN}✅ All checks passed! Redis is healthy.${NC}"
else
    echo -e "${RED}⚠️  Found $ISSUES critical issue(s)${NC}"
    echo ""
    echo "To fix Redis read-only error, run:"
    echo "  ./fix_redis_readonly.sh"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "💡 Tip: Run this script regularly to monitor Redis health"
echo "   Example: watch -n 60 ./monitor_redis_health.sh"

