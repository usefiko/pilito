# Docker Swarm Deployment Guide for Pilito

## Table of Contents
1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Prerequisites](#prerequisites)
4. [Initial Setup](#initial-setup)
5. [Deployment](#deployment)
6. [Management](#management)
7. [Monitoring](#monitoring)
8. [Troubleshooting](#troubleshooting)
9. [Best Practices](#best-practices)

---

## Overview

This guide provides comprehensive instructions for deploying the Pilito Django application using Docker Swarm for high availability, fault tolerance, and automatic container recovery.

### What is Docker Swarm?

Docker Swarm is Docker's native clustering and orchestration solution that turns a pool of Docker hosts into a single, virtual Docker host. It provides:

- **High Availability**: Multiple replicas of services across nodes
- **Automatic Recovery**: Restarts failed containers automatically
- **Load Balancing**: Built-in load balancing across service replicas
- **Rolling Updates**: Zero-downtime deployments
- **Service Discovery**: Automatic DNS-based service discovery
- **Fault Tolerance**: Services continue running even if nodes fail

### Benefits for Pilito

1. **Container Crash Prevention**: Automatic restart policies ensure services recover from failures
2. **High Availability**: Multiple Django server replicas prevent single point of failure
3. **Scalability**: Easily scale services up or down based on demand
4. **Zero-Downtime Deployments**: Update services without service interruption
5. **Resource Management**: Efficient resource allocation and limits

---

## Architecture

### Service Configuration

| Service | Replicas | Resource Limits | Placement |
|---------|----------|-----------------|-----------|
| **web** (Django) | 3 | 2 CPU, 2GB RAM | Worker nodes |
| **celery_worker** | 2 | 1.5 CPU, 1.5GB RAM | Worker nodes |
| **db** (PostgreSQL) | 1 | 2 CPU, 2GB RAM | Manager node |
| **redis** | 1 | 1 CPU, 768MB RAM | Manager node |
| **celery_beat** | 1 | 0.5 CPU, 512MB RAM | Manager node |
| **prometheus** | 1 | 1 CPU, 1GB RAM | Manager node |
| **grafana** | 1 | 1 CPU, 512MB RAM | Manager node |

### Network Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Docker Swarm Cluster                      │
│                                                               │
│  ┌──────────────┐         ┌──────────────┐                  │
│  │ Manager Node │         │ Worker Node  │                  │
│  │              │         │              │                  │
│  │ - PostgreSQL │         │ - Django x3  │                  │
│  │ - Redis      │         │ - Celery x2  │                  │
│  │ - Monitoring │         │              │                  │
│  └──────────────┘         └──────────────┘                  │
│         │                         │                          │
│         └────────Overlay Network──┘                         │
│              (pilito_network - 10.0.10.0/24)                │
└─────────────────────────────────────────────────────────────┘
```

### Health Checks

All services include comprehensive health checks:

- **Django Web**: HTTP health endpoint (`/health/`)
- **PostgreSQL**: `pg_isready` command
- **Redis**: `redis-cli ping` command
- **Celery Workers**: Celery inspect ping
- **Monitoring Stack**: HTTP health endpoints

---

## Prerequisites

### System Requirements

- **OS**: Linux (Ubuntu 20.04+, Debian 10+, CentOS 7+) or macOS
- **Docker**: Version 20.10+ with Swarm mode
- **RAM**: Minimum 8GB (16GB recommended for production)
- **CPU**: Minimum 4 cores (8+ recommended for production)
- **Disk**: 50GB+ free space

### Software Requirements

```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Verify installations
docker --version
docker-compose --version
```

### Network Requirements

- Ports that need to be open:
  - **2377/tcp**: Swarm cluster management
  - **7946/tcp, 7946/udp**: Node communication
  - **4789/udp**: Overlay network traffic
  - **8000/tcp**: Django application
  - **9090/tcp**: Prometheus
  - **3001/tcp**: Grafana

---

## Initial Setup

### 1. Clone and Configure

```bash
# Navigate to project directory
cd /path/to/pilito

# Ensure .env file exists with proper configuration
cp .env.example .env
# Edit .env with your settings
nano .env
```

### 2. Initialize Docker Swarm

```bash
# Run the initialization script
./swarm_init.sh
```

This script will:
- Initialize Docker Swarm mode
- Configure the manager node
- Create overlay network
- Build Docker images
- Display join tokens for additional nodes

**Expected Output:**
```
[INFO] Starting Docker Swarm initialization...
[SUCCESS] Pre-flight checks passed
[INFO] Initializing Docker Swarm...
[SUCCESS] Docker Swarm initialized successfully
[INFO] Labeling current node as manager...
[SUCCESS] Node labeled successfully
[INFO] Creating overlay network for services...
[SUCCESS] Overlay network created successfully
```

### 3. Add Worker Nodes (Optional)

If you want to run a multi-node cluster:

```bash
# On worker machines, run the join command from init output:
docker swarm join --token SWMTKN-1-xxxxx <manager-ip>:2377

# Verify nodes from manager:
docker node ls
```

---

## Deployment

### Deploy the Stack

```bash
# Deploy all services
./swarm_deploy.sh
```

This script will:
1. Build updated Docker images
2. Deploy the stack to Swarm
3. Wait for services to start
4. Display service status

**Expected Output:**
```
[INFO] Running pre-deployment checks...
[SUCCESS] Pre-deployment checks passed
[INFO] Building latest Docker images...
[SUCCESS] Images built successfully
[INFO] Deploying stack 'pilito'...
Creating service pilito_web
Creating service pilito_db
Creating service pilito_redis
Creating service pilito_celery_worker
Creating service pilito_celery_beat
Creating service pilito_prometheus
Creating service pilito_grafana
[SUCCESS] Stack deployed successfully
```

### Verify Deployment

```bash
# Check service status
docker stack services pilito

# Check running tasks
docker stack ps pilito

# View service logs
docker service logs -f pilito_web
```

### Access Services

Once deployed, access your services at:

- **Django API**: http://localhost:8000
- **Django Admin**: http://localhost:8000/admin
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health/
- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3001 (admin/admin)

---

## Management

### Scaling Services

#### Scale Web Service

```bash
# Scale to 5 replicas
./swarm_scale.sh web 5

# Or use Docker directly
docker service scale pilito_web=5
```

#### Scale Celery Workers

```bash
# Scale to 4 workers
./swarm_scale.sh celery_worker 4
```

#### Scaling Recommendations

- **Web Service**: 3-5 replicas for production
- **Celery Workers**: 2-10 based on workload
- **Database**: Keep at 1 (stateful service)
- **Redis**: Keep at 1 (or configure Redis Cluster separately)
- **Celery Beat**: Keep at 1 (scheduler should be single instance)

### Updating Services

#### Update All Services

```bash
./swarm_update.sh
# Choose 'all' when prompted
```

#### Update Specific Service

```bash
./swarm_update.sh
# Enter service name (e.g., 'web')
```

#### Rolling Update Process

The update strategy ensures zero downtime:
1. New containers start (start-first)
2. Health checks verify new containers
3. Old containers stop
4. Process repeats for remaining replicas

### Rollback

If an update causes issues:

```bash
# Rollback specific service
./swarm_rollback.sh web

# Rollback all services
./swarm_rollback.sh all
```

Docker Swarm automatically keeps the previous version and can rollback instantly.

---

## Monitoring

### Status Dashboard

```bash
# View comprehensive status
./swarm_status.sh
```

This displays:
- Swarm cluster status
- Node information
- Service replica status
- Task distribution
- Resource usage
- Health check endpoints

### Continuous Monitoring

```bash
# Real-time monitoring dashboard
./continuous_monitoring.sh
```

Features:
- Auto-refreshing service status
- Failed task detection
- Health check results
- Quick statistics
- Periodic comprehensive health checks

### Health Checks

```bash
# Run comprehensive health checks
./health_check_services.sh
```

Checks include:
- Swarm status
- Service replica readiness
- HTTP endpoint availability
- Database connectivity
- Redis connectivity
- Failed task detection
- Node health

### Viewing Logs

```bash
# View logs for specific service
docker service logs -f pilito_web

# View last 100 lines
docker service logs --tail 100 pilito_web

# View logs with timestamps
docker service logs -f --timestamps pilito_web

# View logs for all tasks of a service
docker service logs pilito_celery_worker
```

### Prometheus Metrics

Access Prometheus at http://localhost:9090

Key metrics to monitor:
- `django_http_requests_total`: Request count
- `django_http_requests_latency_seconds`: Response times
- `celery_tasks_total`: Celery task count
- `redis_connected_clients`: Redis connections
- `postgresql_up`: Database status

### Grafana Dashboards

Access Grafana at http://localhost:3001 (admin/admin)

Pre-configured dashboards monitor:
- Application performance
- Celery task metrics
- Database performance
- Redis metrics
- Container resource usage

---

## Troubleshooting

### Common Issues

#### Services Not Starting

```bash
# Check service events
docker service ps pilito_web --no-trunc

# Check service inspect
docker service inspect pilito_web

# View detailed logs
docker service logs pilito_web
```

#### Database Connection Issues

```bash
# Check database service
docker service ps pilito_db

# Test database connectivity
docker exec $(docker ps -q -f "name=pilito_db" | head -n 1) \
  pg_isready -U postgres

# View database logs
docker service logs pilito_db
```

#### Redis Connection Issues

```bash
# Test Redis
docker exec $(docker ps -q -f "name=pilito_redis" | head -n 1) \
  redis-cli ping

# View Redis logs
docker service logs pilito_redis
```

#### Port Conflicts

```bash
# Check what's using a port
sudo lsof -i :8000

# Stop conflicting service or change port in docker-compose.swarm.yml
```

#### Out of Resources

```bash
# Check node resources
docker node ls
docker node inspect <node-name>

# Reduce service resource requirements in docker-compose.swarm.yml
```

#### Failed Tasks Accumulating

```bash
# View failed tasks
docker stack ps pilito --filter "desired-state=shutdown"

# Check error messages
docker stack ps pilito --no-trunc --filter "desired-state=shutdown"

# Force update to clear old tasks
docker service update --force pilito_web
```

### Emergency Procedures

#### Restart Individual Service

```bash
docker service update --force pilito_web
```

#### Complete Stack Restart

```bash
# Remove stack
docker stack rm pilito

# Wait for cleanup
sleep 30

# Redeploy
./swarm_deploy.sh
```

#### Node Failure Recovery

If a node goes down:
1. Swarm automatically reschedules tasks to healthy nodes
2. Monitor with: `watch docker service ps pilito_web`
3. Once node is back, tasks may rebalance automatically

#### Database Recovery

```bash
# If database is corrupted, restore from backup
docker service scale pilito_db=0
# Restore volume from backup
docker service scale pilito_db=1
```

---

## Best Practices

### Production Deployment

1. **Use Multiple Nodes**
   - Minimum 3 manager nodes for quorum
   - Multiple worker nodes for load distribution

2. **Resource Limits**
   - Always set resource limits and reservations
   - Monitor resource usage and adjust

3. **Volume Management**
   - Use volume drivers for shared storage (NFS, GlusterFS)
   - Regular backups of PostgreSQL data
   - Consider external managed databases for production

4. **Secrets Management**
   - Use Docker secrets instead of environment variables
   - Rotate secrets regularly

5. **Update Strategy**
   - Test updates in staging environment
   - Use rolling updates with health checks
   - Keep rollback plan ready

### Security

1. **Network Security**
   ```bash
   # Use encrypted overlay network
   docker network create --opt encrypted pilito_network
   ```

2. **TLS/SSL**
   - Add reverse proxy (Nginx/Traefik) with SSL certificates
   - Use Let's Encrypt for automated certificate management

3. **Access Control**
   - Limit Swarm manager access
   - Use firewall rules
   - Regular security updates

### Backup Strategy

```bash
# Backup PostgreSQL data
docker exec $(docker ps -q -f "name=pilito_db" | head -n 1) \
  pg_dump -U postgres pilito_db > backup_$(date +%Y%m%d).sql

# Backup volumes
docker run --rm -v pilito_postgres_data:/data -v $(pwd):/backup \
  alpine tar czf /backup/postgres_backup.tar.gz /data

# Backup media files
docker run --rm -v pilito_media_volume:/data -v $(pwd):/backup \
  alpine tar czf /backup/media_backup.tar.gz /data
```

### Monitoring Best Practices

1. **Set Up Alerts**
   - Configure Prometheus alerts for critical metrics
   - Set up email/Slack notifications

2. **Regular Health Checks**
   - Schedule health checks via cron
   - Monitor failed task trends

3. **Log Aggregation**
   - Consider ELK stack or similar for log management
   - Set up log rotation

### Performance Optimization

1. **Database Tuning**
   - PostgreSQL configuration is optimized in swarm stack
   - Monitor slow queries
   - Regular VACUUM and ANALYZE

2. **Redis Configuration**
   - Memory limits configured
   - Persistence enabled
   - Monitor memory usage

3. **Application Optimization**
   - Enable Django caching
   - Optimize database queries
   - Use CDN for static files

---

## Maintenance

### Regular Tasks

**Daily:**
- Check service health: `./health_check_services.sh`
- Review failed tasks
- Monitor resource usage

**Weekly:**
- Review logs for errors
- Check disk space
- Verify backups

**Monthly:**
- Update Docker and images
- Security patches
- Performance review
- Backup testing

### Cleanup

```bash
# Remove old images
docker image prune -a

# Remove unused volumes (CAREFUL!)
docker volume prune

# Remove unused networks
docker network prune

# System-wide cleanup
docker system prune -a
```

---

## Advanced Topics

### Multi-Node Setup

```bash
# On each worker node
docker swarm join --token <worker-token> <manager-ip>:2377

# On manager, label nodes
docker node update --label-add type=app node1
docker node update --label-add type=database node2

# Use labels in placement constraints
# See docker-compose.swarm.yml for examples
```

### Using Docker Secrets

```bash
# Create secret
echo "mysecretpassword" | docker secret create db_password -

# Use in service
docker service update \
  --secret-add db_password \
  pilito_db
```

### External Load Balancer

For production, add Nginx or HAProxy:

```yaml
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
    deploy:
      replicas: 2
      placement:
        constraints:
          - node.role == worker
```

---

## Quick Reference

### Essential Commands

```bash
# Stack Management
docker stack deploy -c docker-compose.swarm.yml pilito
docker stack ls
docker stack services pilito
docker stack ps pilito
docker stack rm pilito

# Service Management
docker service ls
docker service ps <service>
docker service logs -f <service>
docker service scale <service>=<replicas>
docker service update --force <service>
docker service rollback <service>

# Node Management
docker node ls
docker node inspect <node>
docker node update --availability drain <node>
docker node update --availability active <node>

# Monitoring
docker service ps pilito_web
docker service logs --tail 100 pilito_web
docker stats $(docker ps -q)
```

### Script Reference

| Script | Purpose |
|--------|---------|
| `swarm_init.sh` | Initialize Docker Swarm cluster |
| `swarm_deploy.sh` | Deploy/update stack |
| `swarm_scale.sh` | Scale service replicas |
| `swarm_update.sh` | Update services with zero downtime |
| `swarm_rollback.sh` | Rollback to previous version |
| `swarm_status.sh` | View comprehensive status |
| `swarm_cleanup.sh` | Clean up stack and resources |
| `health_check_services.sh` | Run health checks |
| `continuous_monitoring.sh` | Real-time monitoring dashboard |

---

## Support and Resources

### Documentation
- [Docker Swarm Official Docs](https://docs.docker.com/engine/swarm/)
- [Docker Compose Spec](https://docs.docker.com/compose/compose-file/)
- [Django Deployment Checklist](https://docs.djangoproject.com/en/4.2/howto/deployment/checklist/)

### Monitoring
- Prometheus: http://localhost:9090
- Grafana: http://localhost:3001
- Health endpoint: http://localhost:8000/health/

### Getting Help

If you encounter issues:
1. Check logs: `docker service logs pilito_<service>`
2. Run health check: `./health_check_services.sh`
3. Check service events: `docker service ps <service> --no-trunc`
4. Review this documentation
5. Consult Docker Swarm documentation

---

## Changelog

### Version 1.0.0 (Initial Release)
- Docker Swarm configuration for all services
- Health checks for all services
- Management scripts for deployment and scaling
- Comprehensive monitoring setup
- High availability with multiple replicas
- Zero-downtime update strategy
- Automatic rollback on failures

---

**Last Updated**: October 2025
**Maintainer**: Pilito DevOps Team

