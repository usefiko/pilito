# Docker Swarm Deployment Fix Guide

## 🚨 Problem: Mixed Docker Compose and Swarm Deployment

If you see errors like:
```
nc: getaddrinfo for host "db" port 5432: Name or service not known
```

And you see both regular Docker containers AND Swarm services running:
```bash
docker ps
# Shows: postgres_db, redis_cache, celery_beat, AND pilito_celery_beat.1.xxx
```

This means you have a **mixed deployment** - some services running via `docker-compose up` and others via `docker stack deploy`. These create separate networks that cannot communicate with each other.

## ✅ Solution: Use the Fix Script

We've created a comprehensive script to fix this issue automatically.

### Quick Fix (Recommended)

Run this script on your server:

```bash
cd /root  # or wherever your project is located
./fix_mixed_deployment.sh
```

This script will:
1. ✅ Check current deployment state
2. ✅ Stop all Docker Compose containers
3. ✅ Remove existing Swarm stacks
4. ✅ Wait for cleanup to complete
5. ✅ Verify Swarm is active
6. ✅ Build the Docker image
7. ✅ Deploy the full stack via Swarm
8. ✅ Monitor deployment progress
9. ✅ Check service health
10. ✅ Display status and next steps

### Manual Fix (If Script Fails)

If the script fails or you prefer manual steps:

```bash
# 1. Stop Docker Compose containers
docker-compose down

# 2. Remove Swarm stack
docker stack rm pilito

# 3. Wait for cleanup
sleep 30

# 4. Verify cleanup
docker ps -a

# 5. Remove any remaining containers (if needed)
docker ps -a -q | xargs -r docker rm -f

# 6. Build the image
docker build -t pilito_web:latest .

# 7. Deploy via Swarm
docker stack deploy -c docker-compose.swarm.yml pilito

# 8. Monitor deployment
watch -n 2 'docker stack ps pilito'
```

## 📊 Monitoring Tools

### 1. Monitor Swarm Stack

Quick status overview with auto-refresh:

```bash
./monitor_swarm.sh
```

This shows:
- Service status and replicas
- Task states
- Failed tasks (if any)
- Network information
- Service URLs
- Useful commands

### 2. View Service Logs

Quick access to service logs:

```bash
./quick_swarm_logs.sh web          # Last 50 lines of web service
./quick_swarm_logs.sh web 100      # Last 100 lines
./quick_swarm_logs.sh celery_beat  # Celery beat logs
```

To follow logs in real-time:
```bash
docker service logs -f pilito_web
docker service logs -f pilito_celery_beat
docker service logs -f pilito_celery_worker
```

## 🔍 Troubleshooting

### Check Service Status

```bash
docker stack services pilito
```

### Check Task Status (detailed)

```bash
docker stack ps pilito --no-trunc
```

### Check Failed Tasks

```bash
docker stack ps pilito --filter "desired-state=running" | grep -i "failed\|rejected"
```

### Check Service Logs

```bash
# Web service
docker service logs pilito_web --tail 100

# Celery beat
docker service logs pilito_celery_beat --tail 100

# Celery worker
docker service logs pilito_celery_worker --tail 100

# Database
docker service logs pilito_db --tail 50
```

### Check Networks

```bash
docker network ls | grep pilito
docker network inspect pilito_pilito_network
```

### Check if Services Can Communicate

```bash
# Test from web service to database
docker exec -it $(docker ps -q -f name=pilito_web) nc -zv db 5432

# Test from web service to redis
docker exec -it $(docker ps -q -f name=pilito_web) nc -zv redis 6379
```

## 🎯 Best Practices

### DO ✅

1. **Always use Swarm for production:**
   ```bash
   docker stack deploy -c docker-compose.swarm.yml pilito
   ```

2. **Monitor deployment:**
   ```bash
   ./monitor_swarm.sh
   ```

3. **Check logs before making changes:**
   ```bash
   ./quick_swarm_logs.sh web
   ```

4. **Scale services properly:**
   ```bash
   docker service scale pilito_web=3
   docker service scale pilito_celery_worker=2
   ```

5. **Update services with zero downtime:**
   ```bash
   docker service update --image pilito_web:latest pilito_web
   ```

### DON'T ❌

1. **Don't use `docker-compose up` in production** - Use Swarm instead
2. **Don't mix Compose and Swarm** - Pick one (Swarm for production)
3. **Don't force remove containers** without checking dependencies
4. **Don't skip the cleanup step** when switching between Compose and Swarm
5. **Don't modify `.env` without redeploying** - Changes won't apply automatically

## 🔄 Common Operations

### Restart a Service

```bash
# Force update to restart (no downtime)
docker service update --force pilito_web
```

### Scale Services

```bash
# Scale web service to 3 replicas
docker service scale pilito_web=3

# Scale celery workers to 4 replicas
docker service scale pilito_celery_worker=4
```

### Update Service Image

```bash
# Build new image
docker build -t pilito_web:latest .

# Update service (rolling update)
docker service update --image pilito_web:latest pilito_web
```

### Rollback a Service

```bash
docker service rollback pilito_web
```

### Remove Stack

```bash
docker stack rm pilito
```

### Full Redeployment

```bash
# Remove stack
docker stack rm pilito

# Wait for cleanup
sleep 30

# Rebuild image
docker build -t pilito_web:latest .

# Deploy again
docker stack deploy -c docker-compose.swarm.yml pilito
```

## 📝 Service URLs

After successful deployment, access:

- **Web App:** http://localhost:8000
- **Grafana:** http://localhost:3001 (admin/admin)
- **Prometheus:** http://localhost:9090
- **Redis:** localhost:6379

## 🆘 Getting Help

If you encounter issues:

1. Run the monitoring script: `./monitor_swarm.sh`
2. Check logs: `./quick_swarm_logs.sh <service_name>`
3. Check task status: `docker stack ps pilito --no-trunc`
4. Check service logs: `docker service logs pilito_<service_name>`

## 📚 Additional Resources

- [Docker Swarm Documentation](https://docs.docker.com/engine/swarm/)
- [Docker Stack Deploy](https://docs.docker.com/engine/reference/commandline/stack_deploy/)
- [Docker Service Commands](https://docs.docker.com/engine/reference/commandline/service/)

---

**Created:** 2025-10-29  
**Purpose:** Fix mixed Docker Compose and Swarm deployment issues  
**Scripts:**
- `fix_mixed_deployment.sh` - Automated fix
- `monitor_swarm.sh` - Status monitoring
- `quick_swarm_logs.sh` - Log viewing

