# Deployment Tools Summary

## 🎯 Problem Solved

Your server had a **mixed deployment** issue where both Docker Compose containers and Docker Swarm services were running simultaneously. This caused network isolation - services couldn't communicate because they were on different networks.

**Symptom:**
```
nc: getaddrinfo for host "db" port 5432: Name or service not known
```

**Root Cause:**
- Docker Compose creates a default bridge network
- Docker Swarm creates an overlay network (`pilito_network`)
- Services on different networks cannot communicate

## ✅ Solution Created

I've created a comprehensive toolkit to fix and manage your deployment:

### 📦 Scripts Created

| Script | Purpose | Usage |
|--------|---------|-------|
| **fix_mixed_deployment.sh** | Main fix script - stops Compose, deploys via Swarm | `./fix_mixed_deployment.sh` |
| **check_deployment_health.sh** | Diagnoses issues and checks health | `./check_deployment_health.sh` |
| **monitor_swarm.sh** | Real-time monitoring with auto-refresh | `./monitor_swarm.sh` |
| **quick_swarm_logs.sh** | Quick access to service logs | `./quick_swarm_logs.sh web` |

### 📚 Documentation Created

| Document | Description |
|----------|-------------|
| **SWARM_FIX_GUIDE.md** | Comprehensive guide with troubleshooting |
| **DEPLOYMENT_SCRIPTS_REFERENCE.md** | Detailed script reference and workflows |
| **QUICK_COMMANDS.txt** | One-page cheat sheet for quick reference |
| **DEPLOYMENT_TOOLS_SUMMARY.md** | This file - overview of everything |

## 🚀 How to Use

### On Your Server

1. **Upload the scripts to your server:**
   ```bash
   scp fix_mixed_deployment.sh root@srv2390071582:~/
   scp check_deployment_health.sh root@srv2390071582:~/
   scp monitor_swarm.sh root@srv2390071582:~/
   scp quick_swarm_logs.sh root@srv2390071582:~/
   ```

2. **SSH into your server:**
   ```bash
   ssh root@srv2390071582
   ```

3. **Make scripts executable:**
   ```bash
   chmod +x fix_mixed_deployment.sh check_deployment_health.sh monitor_swarm.sh quick_swarm_logs.sh
   ```

4. **Run the fix script:**
   ```bash
   ./fix_mixed_deployment.sh
   ```

This will:
- ✅ Stop all Docker Compose containers
- ✅ Remove conflicting Swarm stacks
- ✅ Clean up networks
- ✅ Build the Docker image
- ✅ Deploy everything via Swarm
- ✅ Verify deployment health

## 📊 What Each Script Does

### 1. fix_mixed_deployment.sh (⭐ Main Script)

**Purpose:** Automated fix for mixed deployment issues

**Steps it performs:**
1. Checks current deployment state
2. Stops Docker Compose containers
3. Removes existing Swarm stacks
4. Waits for cleanup (30 seconds)
5. Verifies Docker Swarm is active
6. Builds Docker image (`pilito_web:latest`)
7. Deploys stack via Swarm
8. Monitors deployment progress
9. Checks service health
10. Displays status and next steps

**When to use:**
- First time deployment
- After accidentally running `docker-compose up`
- When services show network errors
- When doing a clean redeployment

**Duration:** ~3-5 minutes

---

### 2. check_deployment_health.sh

**Purpose:** Comprehensive health check and diagnostics

**Checks performed:**
1. ✅ Docker Compose containers (should be 0)
2. ✅ Docker Swarm services
3. ✅ Mixed deployment detection
4. ✅ Network configuration
5. ✅ Failed services/tasks
6. ✅ Port conflicts
7. ✅ Container health status

**Exit codes:**
- `0` = All healthy
- `>0` = Number of issues found

**When to use:**
- Before making changes
- After deployment
- Regular monitoring
- Troubleshooting

---

### 3. monitor_swarm.sh

**Purpose:** Real-time stack monitoring

**Features:**
- Service status overview
- Task states (running/failed)
- Network information
- Quick statistics
- Service URLs
- Auto-refresh every 5 seconds
- Color-coded output

**When to use:**
- During deployment
- After updates
- Regular monitoring
- Checking service status

---

### 4. quick_swarm_logs.sh

**Purpose:** Quick access to service logs

**Features:**
- Lists available services
- Shows last N lines (default: 50)
- Formatted output
- Easy syntax

**Examples:**
```bash
./quick_swarm_logs.sh              # Show available services
./quick_swarm_logs.sh web          # Last 50 lines of web
./quick_swarm_logs.sh web 100      # Last 100 lines of web
./quick_swarm_logs.sh celery_beat  # Celery beat logs
```

---

## 🔄 Typical Workflow

### Initial Deployment
```bash
./fix_mixed_deployment.sh     # Deploy everything
./monitor_swarm.sh            # Watch it come up
./check_deployment_health.sh  # Verify health
```

### After Code Changes
```bash
cd /path/to/pilito
git pull                      # Get latest code
./fix_mixed_deployment.sh     # Rebuild and deploy
./monitor_swarm.sh            # Monitor
```

### Regular Monitoring
```bash
./check_deployment_health.sh  # Quick check
./monitor_swarm.sh            # Detailed status
```

### Troubleshooting
```bash
./check_deployment_health.sh      # Identify issues
./quick_swarm_logs.sh web         # Check logs
./fix_mixed_deployment.sh         # Fix if needed
```

---

## 🌐 Architecture After Fix

After running the fix script, your deployment will look like this:

```
Docker Swarm Stack: pilito
├── pilito_network (overlay network - 10.0.10.0/24)
│
├── Services:
│   ├── pilito_web (3 replicas)
│   ├── pilito_db (1 replica)
│   ├── pilito_redis (1 replica)
│   ├── pilito_celery_worker (2 replicas)
│   ├── pilito_celery_beat (1 replica)
│   ├── pilito_prometheus (1 replica)
│   ├── pilito_grafana (1 replica)
│   ├── pilito_redis_exporter (1 replica)
│   └── pilito_postgres_exporter (1 replica)
│
└── All services on same network = can communicate ✅
```

**Key points:**
- All services are on the `pilito_network` overlay
- Services can reach each other by name (e.g., `db`, `redis`)
- No more "Name or service not known" errors
- Proper health checks and monitoring

---

## 🎯 Key Benefits

### Before (Mixed Deployment)
- ❌ Docker Compose + Swarm running together
- ❌ Services on different networks
- ❌ Cannot communicate
- ❌ "Name or service not known" errors
- ❌ Inconsistent state

### After (Swarm Only)
- ✅ All services via Swarm
- ✅ All on same overlay network
- ✅ Full communication
- ✅ Health checks working
- ✅ Monitoring enabled
- ✅ Easy scaling
- ✅ Zero-downtime updates
- ✅ Automated recovery

---

## 📝 Important Notes

### DO ✅
- Use `./fix_mixed_deployment.sh` for deployment
- Monitor with `./monitor_swarm.sh`
- Check health with `./check_deployment_health.sh`
- View logs with `./quick_swarm_logs.sh`
- Use Swarm for production

### DON'T ❌
- Don't run `docker-compose up` in production
- Don't mix Compose and Swarm
- Don't skip health checks
- Don't force remove without checking

---

## 🆘 Common Issues & Solutions

### Issue: "Name or service not known"
**Cause:** Mixed deployment
**Fix:** `./fix_mixed_deployment.sh`

### Issue: Port already in use
**Cause:** Docker Compose still running
**Fix:** 
```bash
docker-compose down
./fix_mixed_deployment.sh
```

### Issue: Service keeps restarting
**Cause:** Configuration or dependency issue
**Fix:**
```bash
./quick_swarm_logs.sh <service_name>
# Check logs, fix config, then:
./fix_mixed_deployment.sh
```

### Issue: Can't connect to database
**Cause:** Database not ready or network issue
**Fix:**
```bash
./check_deployment_health.sh
# Check if db service is running
docker service logs pilito_db
```

---

## 📊 Service URLs

After successful deployment:

| Service | URL | Credentials |
|---------|-----|-------------|
| Web App | http://localhost:8000 | - |
| Grafana | http://localhost:3001 | admin/admin |
| Prometheus | http://localhost:9090 | - |
| Redis | localhost:6379 | - |

---

## 🔧 Advanced Usage

### Scale Services
```bash
docker service scale pilito_web=5
docker service scale pilito_celery_worker=4
```

### Update Service
```bash
docker build -t pilito_web:latest .
docker service update --image pilito_web:latest pilito_web
```

### Rollback Service
```bash
docker service rollback pilito_web
```

### View Detailed Status
```bash
docker stack ps pilito --no-trunc
```

---

## 📚 Documentation Files

1. **QUICK_COMMANDS.txt** - One-page cheat sheet (print this!)
2. **DEPLOYMENT_SCRIPTS_REFERENCE.md** - Detailed script reference
3. **SWARM_FIX_GUIDE.md** - Comprehensive troubleshooting guide
4. **DEPLOYMENT_TOOLS_SUMMARY.md** - This file

---

## 🎓 Learning Resources

- [Docker Swarm Documentation](https://docs.docker.com/engine/swarm/)
- [Docker Stack Deploy](https://docs.docker.com/engine/reference/commandline/stack_deploy/)
- [Docker Service Commands](https://docs.docker.com/engine/reference/commandline/service/)

---

## ✨ Quick Reference

**Most common commands:**
```bash
./fix_mixed_deployment.sh        # Fix everything
./check_deployment_health.sh     # Check health
./monitor_swarm.sh               # Monitor status
./quick_swarm_logs.sh web        # View logs
```

**For more details:**
```bash
cat QUICK_COMMANDS.txt           # Cheat sheet
cat SWARM_FIX_GUIDE.md           # Full guide
```

---

**Created:** 2025-10-29  
**Purpose:** Fix mixed Docker Compose and Swarm deployment  
**Status:** Ready to use  
**Next Step:** Run `./fix_mixed_deployment.sh` on your server

