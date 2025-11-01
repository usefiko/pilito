# Production Deployment Checklist for Docker Swarm

Use this checklist before deploying Pilito to production with Docker Swarm.

## Pre-Deployment Checklist

### Infrastructure

- [ ] **Minimum 3 manager nodes** configured for high availability
- [ ] **Multiple worker nodes** for load distribution
- [ ] **Firewall rules** configured:
  - [ ] Allow 2377/tcp (cluster management)
  - [ ] Allow 7946/tcp & 7946/udp (node communication)
  - [ ] Allow 4789/udp (overlay network)
  - [ ] Allow 80/tcp & 443/tcp (HTTP/HTTPS)
  - [ ] Restrict admin ports (9090, 3001) to VPN/internal only

- [ ] **DNS** configured for your domain
- [ ] **SSL certificates** obtained (Let's Encrypt recommended)
- [ ] **Backup system** in place for persistent data
- [ ] **Monitoring** system configured (Prometheus, Grafana)

### Configuration

- [ ] **Environment variables** properly set in `.env`:
  - [ ] `DEBUG=False`
  - [ ] `SECRET_KEY` is a strong random value (not the default)
  - [ ] `ALLOWED_HOSTS` includes your domain
  - [ ] Database credentials are secure
  - [ ] Redis password configured
  - [ ] Email settings configured
  - [ ] OAuth credentials for production

- [ ] **Docker Swarm secrets** created for sensitive data:
  ```bash
  echo "your-secret" | docker secret create db_password -
  echo "your-secret" | docker secret create django_secret_key -
  echo "your-secret" | docker secret create redis_password -
  ```

- [ ] **Resource limits** reviewed and adjusted in `docker-compose.swarm.yml`
- [ ] **Replica counts** appropriate for expected load
- [ ] **Health check intervals** configured appropriately

### Security

- [ ] **Database** not exposed to public internet
- [ ] **Redis** not exposed to public internet or password protected
- [ ] **Admin panel** protected (strong password, 2FA if possible)
- [ ] **CORS** settings configured for production domains only
- [ ] **HTTPS** enforced (redirect HTTP to HTTPS)
- [ ] **Security headers** configured in reverse proxy
- [ ] **Rate limiting** configured
- [ ] **File upload limits** configured
- [ ] **Static files** served via CDN or optimized hosting

### Data Management

- [ ] **Database migrations** tested in staging
- [ ] **Initial data** loaded (if needed)
- [ ] **Backup strategy** implemented:
  - [ ] Database backups automated
  - [ ] Media files backed up
  - [ ] Backup restoration tested
  - [ ] Off-site backup storage configured

- [ ] **Volume strategy** decided:
  - [ ] Local volumes (single node)
  - [ ] NFS/GlusterFS (multi-node)
  - [ ] Cloud storage (S3, etc.) for media

### Performance

- [ ] **Database** tuned for production workload
- [ ] **Redis** configured with appropriate memory limits
- [ ] **Static files** optimized and compressed
- [ ] **Caching** strategy implemented
- [ ] **CDN** configured for static/media files
- [ ] **Database indexes** created for common queries
- [ ] **N+1 query problems** identified and resolved

### Monitoring & Logging

- [ ] **Prometheus** collecting metrics from all services
- [ ] **Grafana** dashboards configured
- [ ] **Alerts** configured for:
  - [ ] Service down
  - [ ] High CPU usage
  - [ ] High memory usage
  - [ ] Disk space low
  - [ ] Database connection errors
  - [ ] Failed tasks accumulating
  - [ ] Health check failures

- [ ] **Log aggregation** system in place (ELK, Loki, etc.)
- [ ] **Error tracking** configured (Sentry, etc.)
- [ ] **Uptime monitoring** from external service
- [ ] **Log rotation** configured

### Testing

- [ ] **Load testing** performed
- [ ] **Failover testing** performed (kill nodes, kill containers)
- [ ] **Update/rollback** tested in staging
- [ ] **Backup restoration** tested
- [ ] **Health checks** verified
- [ ] **Monitoring alerts** tested

## Deployment Steps

### 1. Initial Setup

```bash
# On each manager node
./swarm_init.sh

# On worker nodes (use token from init)
docker swarm join --token <token> <manager-ip>:2377

# Verify cluster
docker node ls
```

### 2. Configure Secrets

```bash
# Create Docker secrets
cat .env | grep SECRET_KEY | cut -d= -f2 | docker secret create django_secret_key -
cat .env | grep POSTGRES_PASSWORD | cut -d= -f2 | docker secret create db_password -
cat .env | grep REDIS_PASSWORD | cut -d= -f2 | docker secret create redis_password -
```

### 3. Deploy Stack

```bash
# Deploy to production
./swarm_deploy.sh

# Monitor deployment
watch -n 2 'docker stack ps pilito'
```

### 4. Verify Deployment

```bash
# Run health checks
./health_check_services.sh

# Check all services are running
docker stack services pilito

# Test endpoints
curl https://yourdomain.com/health/
curl https://yourdomain.com/api/v1/
```

### 5. Post-Deployment

```bash
# Create superuser (if needed)
docker exec -it $(docker ps -q -f "name=pilito_web" | head -n 1) \
  python manage.py createsuperuser

# Verify backups are working
# Check monitoring dashboards
# Configure alerts
```

## Post-Deployment Checklist

- [ ] **All services** showing correct replica counts
- [ ] **Health checks** passing
- [ ] **Website** accessible via HTTPS
- [ ] **Admin panel** accessible and secure
- [ ] **API endpoints** responding correctly
- [ ] **Monitoring** showing data
- [ ] **Logs** being collected
- [ ] **Alerts** configured and tested
- [ ] **Backup** job running
- [ ] **Documentation** updated with production URLs/credentials

## Monitoring After Deployment

### First 24 Hours

- [ ] Check health status every hour
- [ ] Monitor error rates
- [ ] Watch resource usage trends
- [ ] Review logs for errors
- [ ] Test automatic container recovery (kill a container)

### First Week

- [ ] Daily health checks
- [ ] Review performance metrics
- [ ] Check backup success
- [ ] Monitor disk usage
- [ ] Review and tune resource limits

### Ongoing

- [ ] Weekly health check reports
- [ ] Monthly security updates
- [ ] Quarterly disaster recovery testing
- [ ] Regular backup restoration tests

## Emergency Contacts

Document your emergency procedures:

```
Primary Contact: ___________________
Secondary Contact: _________________
Infrastructure Provider: ___________
Escalation Path: ___________________
```

## Rollback Plan

If deployment fails:

```bash
# Immediate rollback
./swarm_rollback.sh all

# Or rollback specific service
./swarm_rollback.sh web

# If stack is broken, remove and redeploy previous version
docker stack rm pilito
git checkout <previous-tag>
./swarm_deploy.sh
```

## Production URLs to Document

- [ ] **Main Application**: _______________________________
- [ ] **Admin Panel**: ___________________________________
- [ ] **API Documentation**: _____________________________
- [ ] **Grafana Dashboard**: _____________________________
- [ ] **Prometheus**: ____________________________________
- [ ] **Status Page**: ___________________________________

## Credentials to Secure

Store securely (e.g., password manager, vault):

- [ ] Django admin credentials
- [ ] Grafana admin credentials
- [ ] Database credentials
- [ ] Redis password
- [ ] SSL certificate locations
- [ ] Cloud provider credentials
- [ ] Backup storage credentials

## Compliance & Legal

- [ ] **Data privacy** compliance (GDPR, etc.)
- [ ] **Terms of Service** deployed
- [ ] **Privacy Policy** deployed
- [ ] **Cookie consent** implemented (if required)
- [ ] **Data retention** policies configured
- [ ] **Audit logging** enabled

## Performance Benchmarks

Document baseline metrics for future comparison:

- [ ] Average response time: ___________ ms
- [ ] 95th percentile response time: ___________ ms
- [ ] Requests per second capacity: ___________
- [ ] Concurrent users tested: ___________
- [ ] Database query time (avg): ___________ ms
- [ ] CPU usage (avg): ___________ %
- [ ] Memory usage (avg): ___________ MB

## Support & Maintenance

- [ ] **Maintenance window** defined and communicated
- [ ] **On-call rotation** established
- [ ] **Runbooks** created for common issues
- [ ] **Escalation procedures** documented
- [ ] **Team trained** on Docker Swarm management

---

## Sign-off

| Role | Name | Date | Signature |
|------|------|------|-----------|
| DevOps Lead | | | |
| Technical Lead | | | |
| Product Owner | | | |
| Security Officer | | | |

---

**Last Updated**: [Date]
**Environment**: Production
**Deployment Date**: [Date]
**Deployed Version**: [Version/Tag]

