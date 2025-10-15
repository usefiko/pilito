# CI/CD Quick Reference Guide

Quick commands and troubleshooting for your VPS deployment.

## 🎯 Quick Commands

### Deploy to VPS
```bash
# Automatic deployment (push to main)
git add .
git commit -m "Your message"
git push origin main

# Watch deployment progress on GitHub Actions
# Go to: https://github.com/YOUR_USERNAME/YOUR_REPO/actions
```

### SSH into VPS
```bash
# Using SSH key
ssh -i ~/.ssh/pilito_deploy root@185.164.72.165

# Or if key is added to ssh-agent
ssh root@185.164.72.165
```

### Check Service Status
```bash
# On VPS
cd /root/pilito

# Check all containers
docker-compose ps

# Check specific service
docker ps | grep django_app
docker ps | grep celery_worker
docker ps | grep postgres_db
```

### View Logs
```bash
# All services
docker-compose logs -f

# Specific service
docker logs django_app -f
docker logs celery_worker -f
docker logs postgres_db -f

# Last 100 lines
docker logs django_app --tail=100

# Since specific time
docker logs django_app --since 30m
```

### Restart Services
```bash
# Restart all services
docker-compose restart

# Restart specific service
docker-compose restart web
docker-compose restart celery_worker

# Full restart (rebuild)
docker-compose down
docker-compose up -d --build
```

### Database Operations
```bash
# Run migrations
docker exec django_app python manage.py migrate

# Create superuser
docker exec -it django_app python manage.py createsuperuser

# Access database shell
docker exec -it postgres_db psql -U pilito_user -d pilito_db

# Backup database
docker exec postgres_db pg_dump -U pilito_user pilito_db > backup_$(date +%Y%m%d).sql

# Restore database
cat backup_20240115.sql | docker exec -i postgres_db psql -U pilito_user -d pilito_db
```

### Django Management Commands
```bash
# Run any Django management command
docker exec django_app python manage.py <command>

# Examples:
docker exec django_app python manage.py collectstatic --noinput
docker exec django_app python manage.py check
docker exec django_app python manage.py showmigrations
docker exec django_app python manage.py shell
```

### Celery Operations
```bash
# Check Celery worker status
docker exec celery_worker celery -A core inspect active

# Check Celery stats
docker exec celery_worker celery -A core inspect stats

# Purge all tasks
docker exec celery_worker celery -A core purge

# List scheduled tasks
docker exec django_app python manage.py shell -c "from django_celery_beat.models import PeriodicTask; print(PeriodicTask.objects.all())"
```

### Disk Space Management
```bash
# Check disk usage
df -h

# Check Docker disk usage
docker system df

# Manual cleanup
cd /root/pilito && ./cleanup.sh

# Or step by step:
docker system prune -af --volumes
docker image prune -af
docker container prune -f
docker volume prune -f
```

### Monitor Resources
```bash
# Real-time Docker stats
docker stats

# System resources
htop

# Check memory
free -h

# Check disk I/O
iostat -x 1
```

## 🔧 Troubleshooting

### Issue: Deployment Failed

**Check GitHub Actions:**
1. Go to GitHub → Actions tab
2. Click on failed workflow
3. Read error messages

**Check on VPS:**
```bash
ssh root@185.164.72.165
cd /root/pilito
docker-compose logs --tail=100
```

### Issue: Container Won't Start

```bash
# Check container status
docker-compose ps

# Check container logs
docker logs <container_name> --tail=100

# Try to start manually
docker-compose up <service_name>

# Rebuild container
docker-compose up -d --build <service_name>
```

### Issue: Database Connection Error

```bash
# Check if database is running
docker ps | grep postgres

# Check database logs
docker logs postgres_db --tail=50

# Test database connection
docker exec postgres_db pg_isready -U pilito_user

# Restart database
docker-compose restart db
```

### Issue: Out of Disk Space

```bash
# Check space
df -h

# Quick cleanup
docker system prune -af --volumes

# Find large directories
du -sh /* | sort -hr | head -10

# Clean logs
find /var/log -name "*.log" -type f -mtime +1 -delete
journalctl --vacuum-time=1d
```

### Issue: Port Already in Use

```bash
# Find process using port 8000
lsof -ti:8000

# Kill process
lsof -ti:8000 | xargs kill -9

# Or stop all Docker containers
docker stop $(docker ps -aq)
```

### Issue: Environment Variables Not Working

```bash
# Check .env file exists
ls -la /root/pilito/.env

# View environment in container
docker exec django_app env | grep DJANGO

# Restart containers to reload .env
docker-compose down
docker-compose up -d
```

### Issue: Static Files Not Loading

```bash
# Collect static files
docker exec django_app python manage.py collectstatic --noinput

# Check static volume
docker volume inspect pilito_static_volume

# Check settings
docker exec django_app python manage.py diffsettings | grep STATIC
```

### Issue: Celery Tasks Not Running

```bash
# Check worker is running
docker ps | grep celery_worker

# Check worker logs
docker logs celery_worker --tail=100

# Ping worker
docker exec celery_worker celery -A core inspect ping

# Check beat scheduler
docker logs celery_beat --tail=50

# Restart Celery
docker-compose restart celery_worker celery_beat
```

## 📊 Monitoring URLs

After deployment, access these URLs:

- **Django API**: http://185.164.72.165:8000
- **Django Admin**: http://185.164.72.165:8000/admin
- **Grafana Dashboard**: http://185.164.72.165:3001 (admin/admin)
- **Prometheus**: http://185.164.72.165:9090
- **API Docs**: http://185.164.72.165:8000/swagger or /redoc

## 🔐 Security Commands

### Update System
```bash
apt-get update
apt-get upgrade -y
```

### Check Firewall
```bash
ufw status verbose
```

### View Failed Login Attempts
```bash
grep "Failed password" /var/log/auth.log | tail -20
```

### Change Root Password
```bash
passwd root
```

### Rotate SSH Keys
```bash
# Generate new key pair locally
ssh-keygen -t ed25519 -f ~/.ssh/pilito_deploy_new

# Add new key to VPS
ssh-copy-id -i ~/.ssh/pilito_deploy_new.pub root@185.164.72.165

# Update GitHub secret VPS_SSH_PRIVATE_KEY with new private key

# Remove old key from VPS
nano ~/.ssh/authorized_keys
# (delete old key line)
```

## 📝 Useful File Locations

```bash
# Project files
/root/pilito/

# Environment variables
/root/pilito/.env

# Docker Compose file
/root/pilito/docker-compose.yml

# Cleanup script
/root/pilito/cleanup.sh

# Cron jobs
/etc/cron.d/pilito-cleanup

# Docker volumes
/var/lib/docker/volumes/

# Nginx config (if installed)
/etc/nginx/sites-available/pilito

# SSL certificates (if using Let's Encrypt)
/etc/letsencrypt/live/
```

## 🔄 Update Workflow

### Update GitHub Actions Workflow
```bash
# Edit locally
nano .github/workflows/deploy.yml

# Commit and push
git add .github/workflows/deploy.yml
git commit -m "Update deployment workflow"
git push origin main
```

### Update Docker Compose
```bash
# Edit locally
nano docker-compose.yml

# Commit and push (will trigger deployment)
git add docker-compose.yml
git commit -m "Update Docker Compose configuration"
git push origin main
```

### Update Environment Variables
```bash
# SSH to VPS
ssh root@185.164.72.165

# Edit .env
nano /root/pilito/.env

# Restart services
cd /root/pilito
docker-compose down
docker-compose up -d
```

## 🚨 Emergency Commands

### Stop Everything
```bash
docker-compose down
```

### Rollback to Previous Version
```bash
cd /root/pilito
git log --oneline  # Find previous commit
git checkout <commit-hash>
docker-compose down
docker-compose up -d --build
```

### Complete Reset
```bash
# ⚠️ WARNING: This will delete ALL data!
cd /root/pilito
docker-compose down -v
docker system prune -af --volumes
docker-compose up -d --build
```

### Force Rebuild Everything
```bash
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

## 📞 Getting Help

1. **Check logs first**: `docker-compose logs --tail=100`
2. **Check GitHub Actions**: Repository → Actions tab
3. **Check documentation**: `/docs/deployment/VPS_CICD_SETUP.md`
4. **System health**: `docker stats` and `df -h`

## 💡 Best Practices

1. **Always check logs** before and after deployment
2. **Monitor disk space** regularly: `df -h`
3. **Keep backups** of database and .env file
4. **Test locally** before pushing to main
5. **Use descriptive commit messages**
6. **Monitor resource usage**: `docker stats`
7. **Review failed deployments** in GitHub Actions
8. **Keep Docker images updated**: `docker-compose pull`

## 🎯 Performance Tips

```bash
# Check container resource limits
docker inspect celery_worker | grep -A 10 Resources

# Limit container memory
# Edit docker-compose.yml and add:
# deploy:
#   resources:
#     limits:
#       memory: 1G

# Clean build cache regularly
docker builder prune -af

# Optimize images
docker images
docker image prune -af
```

