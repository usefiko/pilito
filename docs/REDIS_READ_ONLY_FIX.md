# Redis Read-Only Error Fix Guide

## Problem
```
redis.exceptions.ReadOnlyError: You can't write against a read only replica. script: 8d28fb4c84249684940e751f9f15170eb9a96e1a, on @user_script:6.
```

This error occurs when your application tries to write to a Redis instance that's in read-only mode (configured as a replica/slave).

## Causes
1. **Redis is configured as a replica/slave** instead of master
2. **Failover occurred** and Redis switched to read-only mode
3. **Connection string points to a replica** instead of the primary instance
4. **Redis ran out of memory** and switched to read-only mode automatically

---

## Quick Fixes

### Solution 1: Using the Automated Script (Recommended)

Run the automated fix script:

```bash
cd /Users/nima/Projects/pilito
./fix_redis_readonly.sh
```

This script will:
- Detect your deployment type (Swarm, Compose, or Local)
- Restart Redis or disable read-only mode
- Verify Redis is in master mode

---

### Solution 2: Manual Fix for Docker Swarm

If you're using Docker Swarm (production):

```bash
# Restart the Redis service
docker service update --force pilito_redis

# Wait for it to restart
sleep 10

# Check if Redis is writable
REDIS_CONTAINER=$(docker ps | grep redis | awk '{print $1}')
docker exec $REDIS_CONTAINER redis-cli CONFIG GET replica-read-only
docker exec $REDIS_CONTAINER redis-cli INFO replication | grep role
```

Expected output: `role:master`

---

### Solution 3: Manual Fix for Docker Compose

If you're using Docker Compose (local/staging):

```bash
# Restart Redis container
docker-compose restart redis

# Check Redis status
docker-compose exec redis redis-cli ping
docker-compose exec redis redis-cli INFO replication | grep role
```

Expected output: `role:master`

---

### Solution 4: Manual Fix for Local Redis

If Redis is running locally:

```bash
# Connect to Redis and disable read-only mode
redis-cli CONFIG SET replica-read-only no
redis-cli REPLICAOF NO ONE

# Verify
redis-cli INFO replication | grep role
```

Expected output: `role:master`

---

### Solution 5: Fix Memory Issues

If Redis is in read-only mode due to memory limits:

```bash
# Check memory usage
docker exec $(docker ps | grep redis | awk '{print $1}') redis-cli INFO memory

# Option 1: Clear some data
docker exec -it $(docker ps | grep redis | awk '{print $1}') redis-cli
> FLUSHDB  # Clears current database
> FLUSHALL # Clears all databases (use with caution!)

# Option 2: Increase memory limit in docker-compose.yml or docker-compose.swarm.yml
# Change: --maxmemory 512mb to --maxmemory 1024mb
```

---

## Permanent Prevention

### 1. Updated Configuration

The following configurations have been updated in your project:

**File: `src/core/settings/common.py`**
- Added retry logic for Redis connections
- Added socket keepalive settings
- Added health check interval

**File: `src/core/settings/production.py`**
- Added connection retry mechanisms
- Added channel capacity settings
- Added health check configuration

### 2. Redis Configuration in Docker

**File: `docker-compose.yml`**
```yaml
redis:
  image: redis:7
  command: redis-server --appendonly yes --maxmemory 256mb --maxmemory-policy allkeys-lru
```

**File: `docker-compose.swarm.yml`**
```yaml
redis:
  image: redis:7-alpine
  command: redis-server --maxmemory 512mb --maxmemory-policy allkeys-lru --save 60 1000 --appendonly yes
```

### 3. Ensure Redis is NOT a Replica

Add this to your Redis configuration to ensure it never becomes a replica:

```bash
# In docker-compose.yml or docker-compose.swarm.yml
redis:
  command: redis-server --maxmemory 512mb --maxmemory-policy allkeys-lru --save 60 1000 --appendonly yes --replica-read-only no
```

---

## Verification Steps

After applying any fix, verify Redis is working:

```bash
# 1. Check Redis role (should be "master")
docker exec $(docker ps | grep redis | awk '{print $1}') redis-cli INFO replication | grep role

# 2. Test write operation
docker exec $(docker ps | grep redis | awk '{print $1}') redis-cli SET test_key "test_value"
docker exec $(docker ps | grep redis | awk '{print $1}') redis-cli GET test_key

# 3. Check application logs
docker logs -f django_app | grep -i redis
```

---

## Monitoring Redis Health

### Check Redis Status

```bash
# Full Redis info
docker exec $(docker ps | grep redis | awk '{print $1}') redis-cli INFO

# Check specific sections
docker exec $(docker ps | grep redis | awk '{print $1}') redis-cli INFO replication
docker exec $(docker ps | grep redis | awk '{print $1}') redis-cli INFO memory
docker exec $(docker ps | grep redis | awk '{print $1}') redis-cli INFO stats
```

### Monitor Redis in Real-Time

```bash
# Monitor all commands
docker exec -it $(docker ps | grep redis | awk '{print $1}') redis-cli MONITOR

# Monitor memory usage
watch -n 1 'docker exec $(docker ps | grep redis | awk '\''print $1'\'') redis-cli INFO memory | grep used_memory_human'
```

---

## Troubleshooting

### Error Persists After Restart

If the error continues after restarting Redis:

1. **Check Redis logs:**
```bash
docker logs $(docker ps | grep redis | awk '{print $1}')
```

2. **Check if Redis is actually running:**
```bash
docker ps | grep redis
```

3. **Check network connectivity:**
```bash
docker exec django_app ping redis -c 3
```

4. **Verify REDIS_URL environment variable:**
```bash
docker exec django_app env | grep REDIS_URL
```

### Multiple Redis Instances

If you have multiple Redis instances:

```bash
# List all Redis containers
docker ps | grep redis

# Check each one
docker exec <container-id> redis-cli INFO replication
```

### Redis Master-Slave Setup

If you intentionally have a master-slave setup:

1. **Ensure your application connects to the MASTER, not the slave**
2. **Update REDIS_URL to point to the master instance**
3. **Use Redis Sentinel for automatic failover**

---

## After Fixing

After fixing the issue:

1. **Restart your Django application:**
```bash
# For Docker Compose
docker-compose restart web

# For Docker Swarm
docker service update --force pilito_web
```

2. **Test WebSocket connections:**
- Open your application in a browser
- Try connecting via WebSocket
- Check for errors in browser console and Django logs

3. **Monitor logs:**
```bash
# Django logs
docker logs -f django_app | grep -i "redis\|websocket\|channel"

# Redis logs
docker logs -f $(docker ps | grep redis | awk '{print $1}')
```

---

## Contact & Support

If the issue persists after trying all solutions:

1. Check Redis version compatibility with channels-redis
2. Review your Redis network configuration
3. Consider using Redis Cluster or Sentinel for high availability
4. Check for disk space issues on the Redis container

---

## Related Files Modified

- ✅ `src/core/settings/common.py` - Added retry and keepalive settings
- ✅ `src/core/settings/production.py` - Enhanced connection options
- ✅ `fix_redis_readonly.sh` - Automated fix script
- ✅ `docs/REDIS_READ_ONLY_FIX.md` - This documentation

---

## Prevention Checklist

- [ ] Redis is configured as master (not replica)
- [ ] Adequate memory allocated to Redis
- [ ] Connection retry logic enabled
- [ ] Health checks configured
- [ ] Monitoring in place (Prometheus/Grafana)
- [ ] Backup and recovery plan documented
- [ ] High availability setup (if needed)

---

**Last Updated:** November 7, 2025

