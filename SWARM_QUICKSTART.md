# Docker Swarm Quick Start Guide

Get your Pilito application running in Docker Swarm in 5 minutes!

## Prerequisites

- Docker 20.10+ installed
- At least 8GB RAM
- Ports 8000, 9090, 3001 available

## Quick Start

### 1. Initialize Swarm (First Time Only)

```bash
./swarm_init.sh
```

Wait for the initialization to complete. You'll see output like:
```
[SUCCESS] Docker Swarm initialized successfully
[SUCCESS] Overlay network created successfully
```

### 2. Deploy the Stack

```bash
./swarm_deploy.sh
```

This will:
- Build Docker images
- Deploy all services
- Start health checks

Wait ~60 seconds for all services to be healthy.

### 3. Verify Everything Works

```bash
# Check service status
docker stack services pilito

# All services should show desired replicas running
# Example: pilito_web  3/3  (means 3 replicas running)

# Test health endpoint
curl http://localhost:8000/health/
# Should return: {"status":"healthy","checks":{"database":"ok","cache":"ok"}}
```

### 4. Access Your Application

Open in your browser:
- **Application**: http://localhost:8000
- **Admin Panel**: http://localhost:8000/admin
- **API Docs**: http://localhost:8000/docs
- **Grafana**: http://localhost:3001 (admin/admin)
- **Prometheus**: http://localhost:9090

## Common Tasks

### View Service Logs

```bash
# Django web service
docker service logs -f pilito_web

# Celery workers
docker service logs -f pilito_celery_worker

# Database
docker service logs -f pilito_db
```

### Scale Services

```bash
# Scale web service to 5 replicas
./swarm_scale.sh web 5

# Scale celery workers to 4 replicas
./swarm_scale.sh celery_worker 4
```

### Monitor Everything

```bash
# Real-time monitoring dashboard
./continuous_monitoring.sh

# Or run health checks manually
./health_check_services.sh
```

### Update After Code Changes

```bash
./swarm_update.sh
# Choose 'all' or specific service name
```

### Rollback if Something Goes Wrong

```bash
./swarm_rollback.sh web
```

## Quick Reference

### Status Commands

```bash
# Service overview
docker stack services pilito

# Detailed task status
docker stack ps pilito

# Comprehensive status report
./swarm_status.sh
```

### Troubleshooting

**Services not starting?**
```bash
docker service ps pilito_web --no-trunc
docker service logs pilito_web
```

**Database connection issues?**
```bash
docker service logs pilito_db
docker exec $(docker ps -q -f "name=pilito_db" | head -n 1) pg_isready
```

**Port already in use?**
```bash
sudo lsof -i :8000
# Kill the conflicting process or change port in docker-compose.swarm.yml
```

## Cleanup

### Remove Stack (Keep Data)

```bash
docker stack rm pilito
```

### Full Cleanup (Deletes Data)

```bash
./swarm_cleanup.sh
# Choose option 2 or 4
```

## What's Next?

- Read the [Full Documentation](./DOCKER_SWARM_GUIDE.md) for advanced features
- Set up monitoring alerts in Prometheus
- Configure SSL/TLS for production
- Add more worker nodes to the cluster

## Architecture at a Glance

```
┌─────────────────────────────────────────┐
│         Docker Swarm Cluster             │
│                                          │
│  ┌────────────────────────────────┐    │
│  │  Django Web (3 replicas)       │    │
│  │  - Auto-restart on failure     │    │
│  │  - Load balanced               │    │
│  │  - Health checked              │    │
│  └────────────────────────────────┘    │
│                                          │
│  ┌────────────────────────────────┐    │
│  │  Celery Workers (2 replicas)   │    │
│  │  - Background task processing  │    │
│  │  - Scalable                    │    │
│  └────────────────────────────────┘    │
│                                          │
│  ┌────────────────────────────────┐    │
│  │  PostgreSQL + Redis            │    │
│  │  - Persistent data             │    │
│  │  - Health monitored            │    │
│  └────────────────────────────────┘    │
│                                          │
│  ┌────────────────────────────────┐    │
│  │  Prometheus + Grafana          │    │
│  │  - Real-time metrics           │    │
│  │  - Visual dashboards           │    │
│  └────────────────────────────────┘    │
└─────────────────────────────────────────┘
```

## Benefits You Get

✅ **Automatic Recovery**: Containers restart automatically on failure  
✅ **High Availability**: 3 Django servers = no single point of failure  
✅ **Zero Downtime Updates**: Rolling updates keep service running  
✅ **Load Balancing**: Requests distributed across all replicas  
✅ **Health Monitoring**: Unhealthy containers are automatically replaced  
✅ **Easy Scaling**: Scale services with one command  
✅ **Resource Management**: CPU and memory limits prevent resource exhaustion  

## Need Help?

- **Full Guide**: See [DOCKER_SWARM_GUIDE.md](./DOCKER_SWARM_GUIDE.md)
- **Check Logs**: `docker service logs pilito_<service>`
- **Health Check**: `./health_check_services.sh`
- **Status**: `./swarm_status.sh`

---

**Pro Tip**: Run `./continuous_monitoring.sh` in a separate terminal to keep an eye on everything!

