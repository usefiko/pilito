# 🚨 IMMEDIATE ACTION REQUIRED: Fix Redis Read-Only Error

## What Happened?
Your Redis instance is in **READ-ONLY mode**, causing WebSocket connections to fail with:
```
redis.exceptions.ReadOnlyError: You can't write against a read only replica.
```

---

## ⚡ IMMEDIATE FIX (Choose One)

### Option 1: Run the Automated Script (Fastest)
```bash
cd /Users/nima/Projects/pilito
chmod +x fix_redis_readonly.sh
./fix_redis_readonly.sh
```

### Option 2: Manual Fix for Docker Swarm
```bash
docker service update --force pilito_redis
sleep 10
docker exec $(docker ps | grep redis | awk '{print $1}') redis-cli INFO replication | grep role
```
Expected: `role:master`

### Option 3: Manual Fix for Docker Compose
```bash
cd /Users/nima/Projects/pilito
docker-compose restart redis
docker-compose exec redis redis-cli INFO replication | grep role
```
Expected: `role:master`

---

## ✅ Verify the Fix

After running one of the above commands:

```bash
# 1. Test Redis write
docker exec $(docker ps | grep redis | awk '{print $1}') redis-cli SET test_key "hello"

# 2. Restart Django app
docker-compose restart web
# OR for Swarm:
docker service update --force pilito_web

# 3. Check logs
docker logs -f django_app | grep -i redis
```

---

## 🛠️ What Was Updated

I've already made the following changes to prevent this issue:

1. ✅ **Updated** `src/core/settings/common.py`
   - Added retry logic for Redis connections
   - Added socket keepalive settings
   - Added health check interval

2. ✅ **Updated** `src/core/settings/production.py`
   - Enhanced connection retry mechanisms
   - Added channel capacity settings
   - Added health check configuration

3. ✅ **Created** `fix_redis_readonly.sh`
   - Automated script to fix read-only mode

4. ✅ **Created** `docs/REDIS_READ_ONLY_FIX.md`
   - Comprehensive documentation

---

## 🔍 Root Cause Analysis

The error occurred because:
- Redis was configured as a **replica/slave** instead of **master**
- OR Redis failed over and switched to read-only mode
- OR Redis ran out of memory

---

## 📋 Next Steps

1. **NOW**: Run one of the immediate fixes above
2. **VERIFY**: Test WebSocket connections work
3. **MONITOR**: Keep an eye on Redis logs for 24 hours
4. **REVIEW**: Read `docs/REDIS_READ_ONLY_FIX.md` for prevention tips

---

## 🆘 If Error Persists

If the error continues after the fix:

```bash
# Check Redis logs
docker logs $(docker ps | grep redis | awk '{print $1}')

# Check Redis memory
docker exec $(docker ps | grep redis | awk '{print $1}') redis-cli INFO memory | grep used_memory_human

# Check Redis configuration
docker exec $(docker ps | grep redis | awk '{print $1}') redis-cli CONFIG GET "*"
```

Then check:
- Disk space: `df -h`
- Memory: `free -h`
- Network: `docker exec django_app ping redis -c 3`

---

## 📚 Documentation

For detailed information, see:
- `docs/REDIS_READ_ONLY_FIX.md` - Complete guide
- `fix_redis_readonly.sh` - Automated fix script

---

**Status:** ⚠️ ACTION REQUIRED
**Priority:** 🔴 HIGH
**Impact:** WebSocket connections are failing
**Resolution Time:** ~2 minutes

---

Last Updated: November 7, 2025

