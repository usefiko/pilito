# Deployment Guide - Local vs Production

## Overview

Your Pilito project now supports **two deployment modes**:

| Mode | Use Case | File | High Availability |
|------|----------|------|-------------------|
| **Development** | Local coding & testing | `docker-compose.yml` | No (single containers) |
| **Production** | Production deployment | `docker-compose.swarm.yml` | Yes (multiple replicas) |

Both configurations work independently and can coexist!

---

## 🔧 Local Development (Same as Before)

### Quick Start

```bash
# Start development environment
docker-compose up --build

# Or using Makefile (recommended)
make dev-up
```

### What Runs

- 1× Django web server (port 8000)
- 1× PostgreSQL database
- 1× Redis cache
- 1× Celery worker
- 1× Celery beat
- 1× Prometheus
- 1× Grafana

### Common Commands

```bash
# Start in background
docker-compose up -d

# View logs
docker-compose logs -f web
# or
make dev-logs

# Run migrations
docker-compose exec web python manage.py migrate
# or
make migrate

# Create superuser
docker-compose exec web python manage.py createsuperuser
# or
make createsuperuser

# Stop everything
docker-compose down
# or
make dev-down

# Rebuild after code changes
docker-compose up --build
```

### Access Points (Development)

- **Application**: http://localhost:8000
- **Admin**: http://localhost:8000/admin
- **API Docs**: http://localhost:8000/docs
- **Grafana**: http://localhost:3001
- **Prometheus**: http://localhost:9090

---

## 🚀 Production Deployment (Docker Swarm)

### First-Time Setup

```bash
# 1. Initialize Docker Swarm (only once)
./swarm_init.sh
# or
make init

# 2. Deploy the stack
./swarm_deploy.sh
# or
make deploy

# 3. Verify deployment
make health
```

### What Runs

- **3× Django web servers** (load balanced)
- **2× Celery workers** (parallel processing)
- 1× PostgreSQL database (with optimization)
- 1× Redis cache (with persistence)
- 1× Celery beat scheduler
- 1× Prometheus metrics
- 1× Grafana dashboards

### Daily Operations

```bash
# Check status
make status
./swarm_status.sh

# View logs
make logs service=web
docker service logs -f pilito_web

# Scale services
make scale service=web replicas=5
./swarm_scale.sh web 5

# Update after code changes
make update
./swarm_update.sh

# Rollback if needed
make rollback service=web
./swarm_rollback.sh web

# Real-time monitoring
make monitor
./continuous_monitoring.sh

# Health checks
make health
./health_check_services.sh
```

### Access Points (Production)

Same URLs as development, but now load-balanced across multiple containers:
- **Application**: http://localhost:8000 (→ 3 replicas)
- **Admin**: http://localhost:8000/admin
- **API Docs**: http://localhost:8000/docs
- **Grafana**: http://localhost:3001
- **Prometheus**: http://localhost:9090

---

## 🔄 Switching Between Modes

### From Development to Production

```bash
# 1. Stop development environment
docker-compose down
# or
make dev-down

# 2. Initialize and deploy to Swarm
./swarm_init.sh
./swarm_deploy.sh
```

### From Production to Development

```bash
# 1. Remove Swarm stack
docker stack rm pilito
# or
make clean

# 2. Start development environment
docker-compose up
# or
make dev-up
```

### Running Both (Different Ports)

You can run both simultaneously by changing ports in `docker-compose.yml`:

```yaml
# In docker-compose.yml, change ports:
services:
  web:
    ports:
      - "8001:8000"  # Development on 8001
```

Then Swarm uses 8000, development uses 8001.

---

## 🎯 When to Use Each

### Use Development Mode When:

✅ Writing and testing code locally  
✅ Running on your laptop/desktop  
✅ Debugging issues  
✅ Making database migrations  
✅ Testing new features  
✅ Quick iteration needed  

**Command**: `make dev-up` or `docker-compose up`

### Use Production Mode When:

✅ Deploying to a server  
✅ Need high availability  
✅ Handling real user traffic  
✅ Need automatic failover  
✅ Zero-downtime updates required  
✅ Multiple servers/nodes available  

**Command**: `make deploy` or `./swarm_deploy.sh`

---

## 📦 Deployment Comparison

### Development (docker-compose.yml)
```
Pros:
✅ Simple and fast startup
✅ Easy debugging
✅ Hot reload works
✅ Low resource usage
✅ Familiar workflow

Cons:
❌ No high availability
❌ Single point of failure
❌ Manual restart on crash
❌ Downtime during updates
```

### Production (docker-compose.swarm.yml)
```
Pros:
✅ High availability (3 web servers)
✅ Automatic failover
✅ Load balancing
✅ Zero-downtime updates
✅ Self-healing
✅ Easy scaling

Cons:
❌ More complex setup
❌ Higher resource usage
❌ Requires Swarm initialization
```

---

## 🔧 Configuration Files

### docker-compose.yml (Development)
- Single instance of each service
- Volume mounts for hot reload
- Development-friendly settings
- Lower resource requirements

### docker-compose.swarm.yml (Production)
- Multiple replicas for web/celery
- Health checks configured
- Resource limits set
- Production optimizations
- Rolling update strategy
- Automatic rollback

### Both Share
- Same Docker images (Dockerfile)
- Same application code (src/)
- Same environment variables (.env)
- Same networks and volumes

---

## 🚨 Important Notes

### 1. Environment Variables
Both modes use the same `.env` file. Make sure to:
- Set `DEBUG=True` for development
- Set `DEBUG=False` for production

### 2. Database Data
Both modes use separate volumes:
- Development: `postgres_data`
- Production: `pilito_postgres_data` (stack prefix)

They won't conflict, but data is separate!

### 3. Port Conflicts
Both try to use the same ports by default. Run only one at a time, or change ports in `docker-compose.yml`.

### 4. Resource Usage
Production mode uses more resources (3 web + 2 celery = 5 main containers vs 2 in dev).

---

## 📝 Quick Reference

### Development Commands
```bash
make dev-up              # Start dev environment
make dev-down            # Stop dev environment
make dev-logs            # View logs
make shell               # Open Django shell
make migrate             # Run migrations
make createsuperuser     # Create admin user
```

### Production Commands
```bash
make init                # Initialize Swarm (once)
make deploy              # Deploy/update stack
make status              # Check status
make health              # Run health checks
make monitor             # Real-time monitoring
make scale service=web replicas=5  # Scale
make update              # Update services
make rollback service=web  # Rollback
make clean               # Remove stack
```

### Universal Commands
```bash
make help                # Show all commands
make backup-db           # Backup database
make backup-media        # Backup media files
```

---

## 🎓 Typical Workflows

### Daily Development
```bash
# Start your day
make dev-up

# Make code changes
# (hot reload works automatically)

# Run migrations when needed
make migrate

# View logs
make dev-logs

# End of day
make dev-down
```

### Production Deployment
```bash
# Initial deployment
make init
make deploy
make health

# After code changes
git pull
make update

# If update causes issues
make rollback service=web

# Regular monitoring
make status
make health
```

### Handling Issues
```bash
# Development
docker-compose logs web
docker-compose restart web

# Production
make logs service=web
make restart  # Auto-restarts anyway
```

---

## 🔄 Migration Path

### Migrating from Docker Compose to Docker Swarm

1. **Test locally first**
   ```bash
   # On your dev machine
   ./swarm_init.sh
   ./swarm_deploy.sh
   make health
   ```

2. **Backup your data**
   ```bash
   make backup-db
   make backup-media
   ```

3. **Deploy to production server**
   ```bash
   # On production server
   git clone your-repo
   cd your-repo
   
   # Copy .env file
   # Update production settings
   
   ./swarm_init.sh
   ./swarm_deploy.sh
   make health
   ```

4. **Monitor and verify**
   ```bash
   make monitor
   make health
   ```

---

## ❓ FAQ

### Q: Do I need to change my development workflow?
**A**: No! Keep using `docker-compose up` as before.

### Q: When should I use Docker Swarm?
**A**: For production deployments where you need high availability.

### Q: Can I test Swarm locally?
**A**: Yes! Run `./swarm_init.sh` on your local machine.

### Q: Will my GitHub Actions still work?
**A**: Yes, if they use `docker-compose.yml`. Update them if deploying to Swarm.

### Q: How do I update my app in production?
**A**: `make update` - zero downtime, automatic rollback on failure.

### Q: What if a container crashes in production?
**A**: Swarm automatically restarts it. No manual intervention needed!

### Q: How do I scale up for high traffic?
**A**: `make scale service=web replicas=10`

### Q: How do I rollback a bad deployment?
**A**: `make rollback service=web`

---

## 📚 Next Steps

1. **For Development**: Keep using `docker-compose up` as usual
2. **For Production**: Follow [SWARM_QUICKSTART.md](SWARM_QUICKSTART.md)
3. **Before Production Deploy**: Review [PRODUCTION_CHECKLIST.md](PRODUCTION_CHECKLIST.md)
4. **Complete Guide**: Read [DOCKER_SWARM_GUIDE.md](DOCKER_SWARM_GUIDE.md)

---

**Remember**: Development and Production modes are independent. Use what fits your needs! 🚀

