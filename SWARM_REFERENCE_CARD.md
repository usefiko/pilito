# Docker Swarm Quick Reference Card

## 🚀 Essential Commands

### Initial Setup
```bash
./swarm_init.sh                    # Initialize swarm (once)
./swarm_deploy.sh                  # Deploy stack
```

### Daily Operations
```bash
make status                        # Check everything
make health                        # Run health checks
make logs service=web              # View logs
```

### Scaling
```bash
make scale service=web replicas=5  # Scale web
make scale service=celery_worker replicas=4  # Scale workers
```

### Updates & Rollback
```bash
make update                        # Update services
make rollback service=web          # Rollback if needed
```

---

## 📊 Service Overview

| Service | Port | Health Check | Replicas |
|---------|------|--------------|----------|
| Django Web | 8000 | /health/ | 3 |
| PostgreSQL | 5432 | pg_isready | 1 |
| Redis | 6379 | ping | 1 |
| Celery Worker | 9808 | inspect | 2 |
| Celery Beat | - | process | 1 |
| Prometheus | 9090 | /-/healthy | 1 |
| Grafana | 3001 | /api/health | 1 |

---

## 🔧 Management Scripts

| Script | Purpose | Usage |
|--------|---------|-------|
| `swarm_init.sh` | Initialize cluster | `./swarm_init.sh` |
| `swarm_deploy.sh` | Deploy stack | `./swarm_deploy.sh` |
| `swarm_update.sh` | Update services | `./swarm_update.sh` |
| `swarm_scale.sh` | Scale replicas | `./swarm_scale.sh web 5` |
| `swarm_rollback.sh` | Rollback | `./swarm_rollback.sh web` |
| `swarm_status.sh` | View status | `./swarm_status.sh` |
| `swarm_cleanup.sh` | Cleanup | `./swarm_cleanup.sh` |
| `health_check_services.sh` | Health check | `./health_check_services.sh` |
| `continuous_monitoring.sh` | Live monitor | `./continuous_monitoring.sh` |

---

## 🎯 Makefile Commands

### Most Used
```bash
make help          # Show all commands
make deploy        # Deploy to swarm
make status        # Check status
make health        # Health checks
make monitor       # Live dashboard
make logs service=<name>  # View logs
```

### Scaling & Updates
```bash
make scale service=web replicas=5
make update
make rollback service=web
make restart
```

### Database
```bash
make migrate
make db-shell
make backup-db
make backup-media
```

---

## 🏥 Health Endpoints

```bash
# Test all health endpoints
curl http://localhost:8000/health/     # Django
curl http://localhost:9090/-/healthy   # Prometheus
curl http://localhost:3001/api/health  # Grafana
```

---

## 📈 Monitoring URLs

- Django: http://localhost:8000
- Admin: http://localhost:8000/admin
- API Docs: http://localhost:8000/docs
- Prometheus: http://localhost:9090
- Grafana: http://localhost:3001 (admin/admin)

---

## 🔍 Troubleshooting Quick Checks

```bash
# Service not starting?
docker service ps pilito_web --no-trunc
docker service logs pilito_web

# Database issues?
docker exec $(docker ps -q -f "name=pilito_db" | head -n 1) pg_isready

# Redis issues?
docker exec $(docker ps -q -f "name=pilito_redis" | head -n 1) redis-cli ping

# Check failed tasks
docker stack ps pilito --filter "desired-state=shutdown"

# View service events
docker service inspect pilito_web --pretty
```

---

## 🎨 Service States

| State | Meaning |
|-------|---------|
| Running | Service is healthy |
| Starting | Service is initializing |
| Failed | Service crashed (will restart) |
| Shutdown | Service stopped intentionally |
| Rejected | Cannot start (resource/config issue) |

---

## 💡 Common Scenarios

### Scale for High Traffic
```bash
make scale service=web replicas=10
make scale service=celery_worker replicas=5
```

### Update After Code Change
```bash
git pull
make update
# Monitor progress automatically
```

### Something Broke? Rollback!
```bash
make rollback service=web
# Or rollback everything
./swarm_rollback.sh all
```

### Check Why Service Failed
```bash
docker service ps pilito_web --no-trunc
docker service logs pilito_web --tail 100
```

### Restart a Stuck Service
```bash
docker service update --force pilito_web
# Or use make
make restart
```

---

## 📦 Backup & Restore

### Backup
```bash
make backup-db        # Database
make backup-media     # Media files
```

### Restore Database
```bash
# Stop database service
docker service scale pilito_db=0

# Restore from backup
cat backup.sql | docker exec -i $(docker ps -q -f "name=pilito_db") \
  psql -U postgres pilito_db

# Start database
docker service scale pilito_db=1
```

---

## 🚨 Emergency Procedures

### Complete Restart
```bash
docker stack rm pilito
sleep 30
./swarm_deploy.sh
```

### View All Resources
```bash
docker node ls          # Nodes
docker service ls       # Services
docker stack ls         # Stacks
docker network ls       # Networks
docker volume ls        # Volumes
```

### Remove Everything (CAREFUL!)
```bash
./swarm_cleanup.sh
# Choose option 4 for full cleanup
```

---

## 🔐 Security Checklist

- [ ] Change SECRET_KEY in .env
- [ ] Strong database password
- [ ] Update Grafana admin password
- [ ] Set DEBUG=False for production
- [ ] Configure ALLOWED_HOSTS
- [ ] Use HTTPS with reverse proxy
- [ ] Firewall rules configured
- [ ] Regular backups scheduled

---

## 📚 Documentation

- **[Complete Guide](DOCKER_SWARM_GUIDE.md)** - Everything you need
- **[Quick Start](SWARM_QUICKSTART.md)** - Get started fast
- **[Production Checklist](PRODUCTION_CHECKLIST.md)** - Pre-deployment
- **[README](README.md)** - Main documentation

---

## 💬 Support

**Stuck?** Check these in order:
1. `make health` - Run health checks
2. `make logs service=<name>` - Check logs
3. [Troubleshooting Guide](DOCKER_SWARM_GUIDE.md#troubleshooting)
4. [GitHub Issues](https://github.com/usefiko/pilito/issues)

---

## 🎓 Learning Resources

- [Docker Swarm Docs](https://docs.docker.com/engine/swarm/)
- [Docker Service Docs](https://docs.docker.com/engine/reference/commandline/service/)
- [Docker Stack Docs](https://docs.docker.com/engine/reference/commandline/stack/)

---

**Print this and keep it handy! 📌**

