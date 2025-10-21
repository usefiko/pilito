# Pilito-Backend
## Resolve customer requests instantly with AI customer service. 

[![](https://img.shields.io/badge/Python-3.12.4-orange)](https://www.python.org/)
[![](https://img.shields.io/badge/Django-5.2.1-green)](https://www.djangoproject.com/)
[![](https://img.shields.io/badge/Docker-Swarm-blue)](https://docs.docker.com/engine/swarm/)

---

## 🐍 Django Dockerized Project 
This project is a Django application containerized with Docker, using PostgreSQL as the database and Redis for caching and async task queuing. The Django source code is located inside the `src/` directory.

**NEW**: Production-ready Docker Swarm deployment with high availability and automatic failover!

---

## 🚀 Features

### CI/CD & Automation
- **Automatic Deployment** via GitHub Actions
- **Zero-touch production updates** on git push
- **Automated testing** on every PR
- **Automatic rollback** on deployment failures
- **Manual deployment triggers** when needed

### Application Stack
- Django 5.2+ (inside `src/`)
- PostgreSQL 15 with pgvector extension
- Redis 7 for caching and message broker
- Celery for background task processing
- Celery Beat for scheduled tasks
- WebSocket support via Channels

### Infrastructure & Deployment
- **Docker & Docker Compose** for local development
- **Docker Swarm** for production high availability
- **Automatic health checks** and container recovery
- **Zero-downtime deployments** with rolling updates
- **Load balancing** across multiple service replicas
- **Auto-scaling** capabilities

### Monitoring & Observability
- **Prometheus** for metrics collection
- **Grafana** for visualization and dashboards
- **Service health monitoring** with automated checks
- **Real-time performance metrics**

### Development Features
- Environment-based configuration
- Volume persistence for database, media, and static files
- Hot-reload for development
- Comprehensive test suite

---

## 📁 Project Structure

```
.
├── Dockerfile                      # Multi-stage optimized Dockerfile
├── docker-compose.yml              # Local development setup
├── docker-compose.swarm.yml        # Production Swarm stack
├── entrypoint.sh                   # Container initialization
├── Makefile                        # Convenient management commands
├── .env                            # Environment configuration
├── .dockerignore                   # Docker build exclusions
│
├── src/                            # Django application source
│   ├── manage.py
│   ├── core/                       # Core Django settings
│   ├── accounts/                   # User authentication
│   ├── message/                    # Messaging & WebSocket
│   ├── AI_model/                   # AI integration
│   ├── workflow/                   # Workflow management
│   ├── billing/                    # Payment processing
│   ├── monitoring/                 # Metrics & monitoring
│   └── ...
│
├── monitoring/                     # Monitoring configuration
│   ├── prometheus/
│   └── grafana/
│
├── swarm_*.sh                      # Docker Swarm management scripts
├── health_check_services.sh        # Health check automation
├── continuous_monitoring.sh        # Real-time monitoring
│
├── DOCKER_SWARM_GUIDE.md          # Complete Swarm deployment guide
├── SWARM_QUICKSTART.md            # Quick start guide
└── PRODUCTION_CHECKLIST.md        # Production readiness checklist
```

---

## 🧩 Requirements

### For Local Development
- [Docker](https://www.docker.com/) 20.10+
- [Docker Compose](https://docs.docker.com/compose/) 2.0+

### For Production (Docker Swarm)
- Linux server (Ubuntu 20.04+, Debian 10+, CentOS 7+) or macOS
- Docker 20.10+ with Swarm mode
- Minimum 8GB RAM (16GB recommended)
- Minimum 4 CPU cores (8+ recommended)

---

## ⚙️ Setup

### Quick Start - Local Development

#### 1. Clone the repository

```bash
git clone https://github.com/usefiko/pilito.git
cd pilito
```

#### 2. Create your `.env` file

```env
# .env
STAGE="DEV"
DEBUG=True
SECRET_KEY=your_secret_key_change_this_in_production
DJANGO_ALLOWED_HOSTS=localhost 127.0.0.1 [::1]

# Database
POSTGRES_DB=pilito_db
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_secure_password
POSTGRES_HOST=db
POSTGRES_PORT=5432

# Redis
REDIS_URL=redis://redis:6379/0

# Security
CSRF_TRUSTED_ORIGINS=http://localhost:8000
CSRF_COOKIE_DOMAIN=localhost

# Static & Media
STATIC_URL=/static/
MEDIA_URL=/media/
```

#### 3. Build and run with Docker Compose

```bash
# Using Makefile (recommended)
make dev-up

# Or using docker-compose directly
docker-compose up --build
```

This will:
- Build the Django app
- Run migrations automatically
- Collect static files
- Start the app on `http://localhost:8000`

#### 4. Create a superuser

```bash
make createsuperuser
# Or: docker-compose exec web python manage.py createsuperuser
```

#### 5. Access the application

- **Application**: http://localhost:8000
- **Admin Panel**: http://localhost:8000/admin
- **API Documentation**: http://localhost:8000/docs
- **Grafana**: http://localhost:3001 (admin/admin)
- **Prometheus**: http://localhost:9090

---

## 🚀 Production Deployment with Docker Swarm

For production environments requiring high availability, automatic failover, and zero-downtime deployments, use Docker Swarm.

### Quick Start - Production

```bash
# 1. Initialize Docker Swarm
make init
# Or: ./swarm_init.sh

# 2. Deploy the stack
make deploy
# Or: ./swarm_deploy.sh

# 3. Check status
make status
# Or: ./swarm_status.sh

# 4. Run health checks
make health
# Or: ./health_check_services.sh
```

### Production Features

✅ **High Availability**: 3 Django server replicas prevent single point of failure  
✅ **Automatic Recovery**: Containers restart automatically on crash  
✅ **Load Balancing**: Built-in load balancing across replicas  
✅ **Zero-Downtime Updates**: Rolling deployments keep service running  
✅ **Health Monitoring**: Unhealthy containers automatically replaced  
✅ **Easy Scaling**: Scale services with one command  

### Complete Production Guide

For comprehensive production deployment instructions, see:
- **[Docker Swarm Guide](DOCKER_SWARM_GUIDE.md)** - Complete deployment guide
- **[Quick Start Guide](SWARM_QUICKSTART.md)** - Get running in 5 minutes
- **[Production Checklist](PRODUCTION_CHECKLIST.md)** - Pre-deployment checklist

---

## 📦 Common Commands

### Using Makefile (Recommended)

```bash
# Development
make help              # Show all available commands
make dev-up            # Start development environment
make dev-down          # Stop development environment
make dev-logs          # View development logs

# Production (Docker Swarm)
make deploy            # Deploy/update stack
make status            # Show cluster status
make health            # Run health checks
make monitor           # Real-time monitoring dashboard
make logs service=web  # View service logs
make scale service=web replicas=5  # Scale service

# Database
make migrate           # Run Django migrations
make createsuperuser   # Create Django superuser
make db-shell          # Open PostgreSQL shell
make backup-db         # Backup database
make backup-media      # Backup media files

# Utilities
make shell             # Open shell in web container
make redis-cli         # Open Redis CLI
make test-health       # Test health endpoints
```

### Using Docker Compose (Development)

```bash
# Build and start
docker-compose up --build

# Run in background
docker-compose up -d

# View logs
docker-compose logs -f web

# Execute commands
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py createsuperuser

# Stop services
docker-compose down
```

### Using Docker Swarm Scripts (Production)

```bash
# Deployment
./swarm_deploy.sh              # Deploy the stack
./swarm_update.sh              # Update services
./swarm_scale.sh web 5         # Scale to 5 replicas
./swarm_rollback.sh web        # Rollback on failure

# Monitoring
./swarm_status.sh              # Comprehensive status
./health_check_services.sh     # Health checks
./continuous_monitoring.sh     # Real-time monitoring

# Cleanup
./swarm_cleanup.sh             # Remove stack
```

---

## 🏗️ Architecture

### Development Architecture
```
┌─────────────────────────────────────┐
│      Docker Compose (Dev)           │
│                                      │
│  ┌──────────┐  ┌──────────┐        │
│  │  Django  │  │PostgreSQL│        │
│  │   Web    │──│    DB    │        │
│  └──────────┘  └──────────┘        │
│       │                              │
│  ┌──────────┐  ┌──────────┐        │
│  │  Celery  │──│  Redis   │        │
│  │  Worker  │  │  Cache   │        │
│  └──────────┘  └──────────┘        │
│                                      │
│  ┌──────────┐  ┌──────────┐        │
│  │Prometheus│  │ Grafana  │        │
│  └──────────┘  └──────────┘        │
└─────────────────────────────────────┘
```

### Production Architecture (Docker Swarm)
```
┌────────────────────────────────────────────────────┐
│           Docker Swarm Cluster                      │
│                                                      │
│  ┌──────────────┐       ┌──────────────┐          │
│  │Manager Node  │       │ Worker Node  │          │
│  │              │       │              │          │
│  │- PostgreSQL  │       │- Django x3   │          │
│  │- Redis       │       │- Celery x2   │          │
│  │- Monitoring  │       │  (replicas)  │          │
│  └──────────────┘       └──────────────┘          │
│         │                       │                   │
│         └──Overlay Network─────┘                   │
│           (Load Balanced)                           │
│                                                      │
│  Features:                                          │
│  • Automatic failover & recovery                   │
│  • Health checks every 30s                         │
│  • Rolling updates with zero downtime              │
│  • Resource limits & reservations                  │
│  • Distributed across multiple nodes               │
└────────────────────────────────────────────────────┘
```

---

## 🗂️ Volumes

### Persistent Data
- `postgres_data`: PostgreSQL database storage
- `redis_data`: Redis persistence
- `static_volume`: Django static files
- `media_volume`: User uploads and media
- `prometheus_data`: Metrics history
- `grafana_data`: Dashboard configurations

---

## 📊 Monitoring & Health Checks

### Health Endpoints

- **Django**: http://localhost:8000/health/
- **Prometheus**: http://localhost:9090/-/healthy
- **Grafana**: http://localhost:3001/api/health

### Metrics

Access Prometheus metrics at:
- **Django metrics**: http://localhost:8000/api/v1/metrics
- **Celery metrics**: http://localhost:9808/metrics
- **Redis metrics**: http://localhost:9121/metrics
- **PostgreSQL metrics**: http://localhost:9187/metrics

### Automated Health Checks

```bash
# Run comprehensive health check
./health_check_services.sh

# Continuous monitoring
./continuous_monitoring.sh
```

---

## 🔧 Management & Scaling

### Scaling Services

```bash
# Scale web service to 5 replicas (high traffic)
make scale service=web replicas=5

# Scale celery workers based on workload
make scale service=celery_worker replicas=10

# View current replica status
make services
```

### Updates & Rollbacks

```bash
# Update with zero downtime
make update

# Rollback if something goes wrong
make rollback service=web

# Force restart a service
make restart
```

---

## 🔐 Security Notes

### For Production:

1. **Change default credentials**
   - Update `SECRET_KEY` to a strong random value
   - Change Grafana admin password
   - Use strong database passwords

2. **Environment Variables**
   - Never commit `.env` to version control
   - Use Docker secrets for sensitive data in production

3. **Network Security**
   - Configure firewall rules
   - Use reverse proxy with SSL (Nginx, Traefik)
   - Restrict database and Redis access

4. **Regular Updates**
   - Keep Docker images updated
   - Apply security patches
   - Update dependencies regularly

---

## 🐛 Troubleshooting

### Common Issues

**Services not starting?**
```bash
make status
make logs service=web
```

**Database connection errors?**
```bash
make db-shell
# Or check database logs
make logs service=db
```

**Port conflicts?**
```bash
# Check what's using the port
sudo lsof -i :8000
```

**Container keeps restarting?**
```bash
# Check health status
make health

# View detailed service info
docker service ps pilito_web --no-trunc
```

### Getting Help

1. Check service logs: `make logs service=<name>`
2. Run health checks: `make health`
3. Review [Docker Swarm Guide](DOCKER_SWARM_GUIDE.md)
4. Check [Troubleshooting section](DOCKER_SWARM_GUIDE.md#troubleshooting)

---

## 🤖 CI/CD Automatic Deployment

### Setup Automatic Deployment (5 Minutes!)

Never manually deploy again! Push code and GitHub automatically deploys to production.

```bash
# Quick setup (see QUICK_CICD_SETUP.md for details)
1. Generate SSH key on production server
2. Add 3 GitHub secrets (SSH_PRIVATE_KEY, SSH_HOST, SSH_USER)
3. Push code to main branch
4. ✅ Automatic deployment happens!
```

**What you get:**
- ✅ Push to `main` → Auto-deploy to production
- ✅ Pull requests → Auto-run tests  
- ✅ Deployment fails → Auto-rollback
- ✅ Manual deploy option available
- ✅ Email notifications

**Quick Start:**
- **[QUICK_CICD_SETUP.md](QUICK_CICD_SETUP.md)** ← **Start here!** 5-minute setup
- **[CI_CD_SETUP.md](CI_CD_SETUP.md)** - Complete CI/CD documentation

---

## 📚 Documentation

### Getting Started
- **[HOW_TO_RUN.md](HOW_TO_RUN.md)** - How to run the project (dev & prod)
- **[DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)** - Dev vs Production comparison

### Production Deployment
- **[SWARM_QUICKSTART.md](SWARM_QUICKSTART.md)** - 5-minute production setup
- **[DOCKER_SWARM_GUIDE.md](DOCKER_SWARM_GUIDE.md)** - Complete Swarm guide
- **[SWARM_REFERENCE_CARD.md](SWARM_REFERENCE_CARD.md)** - Quick command reference
- **[PRODUCTION_CHECKLIST.md](PRODUCTION_CHECKLIST.md)** - Pre-deployment checklist

### CI/CD & Automation
- **[QUICK_CICD_SETUP.md](QUICK_CICD_SETUP.md)** - 5-minute auto-deployment setup
- **[CI_CD_SETUP.md](CI_CD_SETUP.md)** - Complete CI/CD guide

### Architecture & Implementation
- **[ARCHITECTURE.md](ARCHITECTURE.md)** - System architecture diagrams
- **[SWARM_IMPLEMENTATION_SUMMARY.md](SWARM_IMPLEMENTATION_SUMMARY.md)** - Technical details
- **[Monitoring README](monitoring/README.md)** - Monitoring stack setup

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

---

## 📄 License

This project is licensed under the Pilito License.

---

## 📞 Support

For questions or support:
- Email: contact@pilito.com
- Documentation: See guides above
- Issues: GitHub Issues

---

## 🎉 Quick Commands Reference

```bash
# Development
make dev-up              # Start dev environment
make dev-logs            # View logs
make createsuperuser     # Create admin

# Production
make deploy              # Deploy to swarm
make status              # Check status
make health              # Health checks
make monitor             # Live monitoring

# Scaling
make scale service=web replicas=5

# Backup
make backup-db           # Backup database
make backup-media        # Backup media

# Help
make help                # Show all commands
```

---

**Enjoy building with Pilito! 🚀**
