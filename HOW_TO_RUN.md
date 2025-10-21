# How to Run Pilito - Quick Guide

## 🎯 Choose Your Mode

### Option 1: Development (Local Machine) 👨‍💻
**Use this for**: Coding, testing, debugging on your laptop

```bash
# Start
docker-compose up --build

# Or simpler
make dev-up

# Access at: http://localhost:8000
```

**That's it! Nothing changed from before.** ✅

---

### Option 2: Production (High Availability) 🚀
**Use this for**: Production servers, high traffic, automatic failover

```bash
# First time only
./swarm_init.sh

# Deploy
./swarm_deploy.sh

# Or simpler
make init    # (first time only)
make deploy  # (every time)

# Access at: http://localhost:8000 (load balanced across 3 servers!)
```

---

## 🤔 Which Should I Use?

```
┌─────────────────────────────────────────────────────────┐
│                                                          │
│  Are you developing/testing locally?                    │
│  ┌───────────────┐                                      │
│  │     YES       │ → Use: docker-compose up             │
│  └───────────────┘                                      │
│                                                          │
│  Is this for production/servers?                        │
│  ┌───────────────┐                                      │
│  │     YES       │ → Use: ./swarm_deploy.sh             │
│  └───────────────┘                                      │
│                                                          │
│  Do you need high availability?                         │
│  ┌───────────────┐                                      │
│  │     YES       │ → Use: Docker Swarm                  │
│  └───────────────┘                                      │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

---

## 📊 Quick Comparison

| Feature | Development | Production (Swarm) |
|---------|-------------|-------------------|
| **Command** | `docker-compose up` | `./swarm_deploy.sh` |
| **Web Servers** | 1 | 3 (load balanced) |
| **Auto-restart on crash** | No | Yes ✅ |
| **Zero-downtime updates** | No | Yes ✅ |
| **Setup complexity** | Simple ⭐ | Medium ⭐⭐⭐ |
| **Resource usage** | Low | Medium-High |
| **Best for** | Local dev | Production |

---

## 🚀 Step-by-Step: Development

### Start Development Environment

```bash
# Method 1: Classic way (still works!)
docker-compose up --build

# Method 2: New Makefile way
make dev-up

# Start in background
docker-compose up -d
# or
make dev-up
```

### Common Development Tasks

```bash
# View logs
docker-compose logs -f web

# Run migrations
docker-compose exec web python manage.py migrate

# Create superuser
docker-compose exec web python manage.py createsuperuser

# Open Django shell
docker-compose exec web python manage.py shell

# Stop everything
docker-compose down
```

### Or Use Makefile (Easier!)

```bash
make dev-up              # Start
make dev-logs            # View logs
make migrate             # Run migrations
make createsuperuser     # Create admin
make shell               # Django shell
make dev-down            # Stop
```

---

## 🚀 Step-by-Step: Production

### First Time Setup

```bash
# 1. Initialize Docker Swarm (only once)
./swarm_init.sh

# You'll see:
# [SUCCESS] Docker Swarm initialized successfully
# [SUCCESS] Overlay network created successfully
```

### Deploy Your Application

```bash
# 2. Deploy the stack
./swarm_deploy.sh

# You'll see:
# [INFO] Building latest Docker images...
# [SUCCESS] Images built successfully
# [INFO] Deploying stack 'pilito'...
# [SUCCESS] Stack deployed successfully
```

### Verify Everything Works

```bash
# 3. Check status
./swarm_status.sh
# or
make status

# 4. Run health checks
./health_check_services.sh
# or
make health

# 5. View in browser
# http://localhost:8000
```

---

## 📱 Monitoring Your Application

### Real-time Monitoring Dashboard

```bash
./continuous_monitoring.sh
# or
make monitor
```

Shows:
- Service status
- Running tasks
- Failed tasks (if any)
- Health check results
- Node status

### Check Logs

```bash
# Development
docker-compose logs -f web

# Production
docker service logs -f pilito_web
# or
make logs service=web
```

---

## 🔧 Common Tasks

### After Making Code Changes

**Development:**
```bash
# Just save your file, it auto-reloads!
# Or restart if needed:
docker-compose restart web
```

**Production:**
```bash
# Zero-downtime update
./swarm_update.sh
# or
make update
```

### Scale for High Traffic

```bash
# Scale web service to 10 servers
make scale service=web replicas=10

# Scale celery workers to 5
make scale service=celery_worker replicas=5

# Check status
make status
```

### Rollback a Bad Update

```bash
make rollback service=web
# or
./swarm_rollback.sh web
```

---

## 🆘 Troubleshooting

### Development Issues

```bash
# Service won't start?
docker-compose logs web

# Database connection error?
docker-compose logs db

# Port already in use?
sudo lsof -i :8000  # Find what's using port 8000

# Nuclear option (rebuild everything)
docker-compose down -v
docker-compose up --build
```

### Production Issues

```bash
# Check what's wrong
make status
make health

# View service logs
make logs service=web

# Restart a service
docker service update --force pilito_web
```

---

## 📋 Complete Command Reference

### Development
```bash
make dev-up              # Start development
make dev-down            # Stop development
make dev-logs            # View logs
make migrate             # Run migrations
make createsuperuser     # Create admin
make shell               # Django shell
make db-shell            # PostgreSQL shell
```

### Production
```bash
make init                # Initialize Swarm (once)
make deploy              # Deploy/update stack
make status              # Check status
make health              # Run health checks
make monitor             # Real-time monitoring
make logs service=web    # View logs
make scale service=web replicas=5  # Scale
make update              # Update services
make rollback service=web  # Rollback
```

### Both
```bash
make help                # Show all commands
make backup-db           # Backup database
make backup-media        # Backup media
```

---

## 🎯 Recommended Workflow

### For Local Development (Daily)

```bash
# Morning
make dev-up

# Code all day (auto-reload works)
# ...

# Evening
make dev-down
```

### For Production (As Needed)

```bash
# Initial deployment
make init     # (only once)
make deploy

# Regular updates
git pull
make update

# Check everything daily
make health
```

---

## ❓ FAQ

**Q: Will my existing setup still work?**  
A: Yes! `docker-compose up` works exactly as before.

**Q: Do I need Docker Swarm for development?**  
A: No! Use regular docker-compose for development.

**Q: When do I need Docker Swarm?**  
A: For production when you need high availability and auto-recovery.

**Q: Can I test Swarm on my laptop?**  
A: Yes! Run `./swarm_init.sh` and `./swarm_deploy.sh` locally.

**Q: How do I switch from Compose to Swarm?**  
A: Just stop Compose (`docker-compose down`) and start Swarm (`./swarm_deploy.sh`).

**Q: Is my data safe when switching?**  
A: Yes, but they use different volumes. Backup first: `make backup-db`

---

## 🎓 Learn More

- **[DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)** - Detailed comparison
- **[SWARM_QUICKSTART.md](SWARM_QUICKSTART.md)** - 5-minute production setup
- **[DOCKER_SWARM_GUIDE.md](DOCKER_SWARM_GUIDE.md)** - Complete guide
- **[SWARM_REFERENCE_CARD.md](SWARM_REFERENCE_CARD.md)** - Quick reference

---

## 🎉 Summary

### TL;DR

**For Development (Local):**
```bash
docker-compose up    # or: make dev-up
```

**For Production (Server):**
```bash
./swarm_init.sh      # (first time only)
./swarm_deploy.sh    # (every deployment)
# or:
make init           # (first time only)
make deploy         # (every deployment)
```

**That's it!** 🚀

---

**Need help? Run:** `make help`

