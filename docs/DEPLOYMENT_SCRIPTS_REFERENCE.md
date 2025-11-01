# Deployment Scripts Reference Card

Quick reference for the deployment management scripts.

## 🚀 Quick Start

### First Time Setup or Fix Issues
```bash
./fix_mixed_deployment.sh
```

### Check Health
```bash
./check_deployment_health.sh
```

### Monitor Status
```bash
./monitor_swarm.sh
```

### View Logs
```bash
./quick_swarm_logs.sh web
```

---

## 📋 Script Details

### 1. `fix_mixed_deployment.sh` ⭐
**Purpose:** Fixes mixed Docker Compose and Swarm deployment issues

**When to use:**
- Initial deployment
- After accidentally running `docker-compose up`
- When services can't communicate
- When you see "Name or service not known" errors

**What it does:**
- ✅ Stops Docker Compose containers
- ✅ Removes Swarm stacks
- ✅ Cleans up conflicting resources
- ✅ Builds Docker image
- ✅ Deploys via Swarm
- ✅ Verifies deployment

**Usage:**
```bash
./fix_mixed_deployment.sh
```

**Duration:** ~3-5 minutes

---

### 2. `check_deployment_health.sh`
**Purpose:** Diagnoses deployment issues

**When to use:**
- Before making changes
- After deployment
- When troubleshooting
- Regular health checks

**What it checks:**
- ✅ Docker Compose containers
- ✅ Swarm services
- ✅ Mixed deployment detection
- ✅ Network configuration
- ✅ Failed services
- ✅ Port conflicts
- ✅ Container health

**Usage:**
```bash
./check_deployment_health.sh
```

**Exit codes:**
- `0` = All healthy
- `>0` = Number of issues found

---

### 3. `monitor_swarm.sh`
**Purpose:** Real-time Swarm stack monitoring

**When to use:**
- During deployment
- After updates
- Regular monitoring
- Checking service status

**What it shows:**
- 📊 Service overview
- 📊 Task status
- 📊 Failed tasks
- 📊 Network info
- 📊 Quick stats
- 🌐 Service URLs

**Usage:**
```bash
./monitor_swarm.sh
```

**Features:**
- Auto-refreshes every 5 seconds
- Color-coded status
- Helpful commands

---

### 4. `quick_swarm_logs.sh`
**Purpose:** Quick access to service logs

**When to use:**
- Debugging errors
- Checking service output
- Investigating issues
- Viewing recent activity

**Usage:**
```bash
# Show available services
./quick_swarm_logs.sh

# View specific service (last 50 lines)
./quick_swarm_logs.sh web

# View more lines
./quick_swarm_logs.sh web 100

# Other services
./quick_swarm_logs.sh celery_beat
./quick_swarm_logs.sh celery_worker
./quick_swarm_logs.sh db
./quick_swarm_logs.sh redis
```

**Examples:**
```bash
# Web service errors
./quick_swarm_logs.sh web

# Celery beat scheduler
./quick_swarm_logs.sh celery_beat

# Database logs
./quick_swarm_logs.sh db 20
```

---

## 🔄 Common Workflows

### Initial Deployment
```bash
# 1. Fix/Deploy
./fix_mixed_deployment.sh

# 2. Monitor
./monitor_swarm.sh

# 3. Check health
./check_deployment_health.sh
```

### Troubleshooting
```bash
# 1. Check health
./check_deployment_health.sh

# 2. View logs
./quick_swarm_logs.sh web

# 3. If issues found, fix
./fix_mixed_deployment.sh

# 4. Monitor recovery
./monitor_swarm.sh
```

### Regular Monitoring
```bash
# Quick check
./check_deployment_health.sh

# Detailed status
./monitor_swarm.sh

# Check specific service
./quick_swarm_logs.sh celery_worker
```

### After Code Changes
```bash
# 1. Rebuild and redeploy
./fix_mixed_deployment.sh

# 2. Monitor deployment
./monitor_swarm.sh

# 3. Check logs
./quick_swarm_logs.sh web

# 4. Verify health
./check_deployment_health.sh
```

---

## 🆘 Emergency Procedures

### Services Not Starting
```bash
# 1. Check what's wrong
./check_deployment_health.sh

# 2. View detailed logs
./quick_swarm_logs.sh <service_name> 200

# 3. If network issues, redeploy
./fix_mixed_deployment.sh
```

### Database Connection Issues
```bash
# 1. Check if DB is running
docker service ls | grep db

# 2. Check DB logs
./quick_swarm_logs.sh db

# 3. Test connectivity
docker exec -it $(docker ps -q -f name=pilito_web) nc -zv db 5432

# 4. If fails, redeploy
./fix_mixed_deployment.sh
```

### Celery Not Processing Tasks
```bash
# 1. Check celery services
docker service ls | grep celery

# 2. Check worker logs
./quick_swarm_logs.sh celery_worker

# 3. Check beat logs
./quick_swarm_logs.sh celery_beat

# 4. Restart workers
docker service update --force pilito_celery_worker
docker service update --force pilito_celery_beat
```

### Port Already in Use
```bash
# 1. Find conflicting services
./check_deployment_health.sh

# 2. Stop Docker Compose if running
docker-compose down

# 3. Redeploy via Swarm
./fix_mixed_deployment.sh
```

---

## 📊 Manual Commands

### Swarm Management
```bash
# List stacks
docker stack ls

# List services
docker stack services pilito

# List tasks
docker stack ps pilito

# Remove stack
docker stack rm pilito

# Deploy stack
docker stack deploy -c docker-compose.swarm.yml pilito
```

### Service Management
```bash
# List services
docker service ls

# View service logs
docker service logs pilito_web
docker service logs -f pilito_web  # follow

# Update service
docker service update pilito_web

# Scale service
docker service scale pilito_web=3

# Restart service
docker service update --force pilito_web

# Rollback service
docker service rollback pilito_web
```

### Container Management
```bash
# List containers
docker ps

# View container logs
docker logs <container_id>
docker logs -f <container_id>  # follow

# Execute command in container
docker exec -it <container_id> bash

# Stop all containers
docker stop $(docker ps -q)
```

---

## 🌐 Service URLs

After deployment, services are available at:

| Service | URL | Credentials |
|---------|-----|-------------|
| Web App | http://localhost:8000 | - |
| Grafana | http://localhost:3001 | admin/admin |
| Prometheus | http://localhost:9090 | - |
| Redis | localhost:6379 | - |

---

## 📝 File Locations

```
pilito/
├── fix_mixed_deployment.sh      # Main fix script
├── check_deployment_health.sh   # Health check
├── monitor_swarm.sh             # Monitoring
├── quick_swarm_logs.sh          # Log viewer
├── docker-compose.swarm.yml     # Swarm config
├── docker-compose.yml           # Compose config (dev only)
├── Dockerfile                   # Image definition
└── SWARM_FIX_GUIDE.md          # Detailed guide
```

---

## 🔔 Best Practices

### DO ✅
- Run health checks regularly
- Monitor during deployments
- Check logs before changes
- Use Swarm for production
- Keep scripts up to date

### DON'T ❌
- Mix Compose and Swarm
- Skip health checks
- Ignore warnings
- Force remove without checking
- Run `docker-compose up` in production

---

## 📚 Additional Resources

- **Detailed Guide:** `SWARM_FIX_GUIDE.md`
- **Docker Swarm Docs:** https://docs.docker.com/engine/swarm/
- **Stack Deploy:** https://docs.docker.com/engine/reference/commandline/stack_deploy/

---

**Last Updated:** 2025-10-29  
**Version:** 1.0  
**Maintainer:** DevOps Team

