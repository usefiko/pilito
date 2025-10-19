# 🚀 Pilito - Automated VPS Deployment Guide

Complete guide for setting up CI/CD deployment from GitHub to your VPS server.

## 📋 Overview

This project is configured for automated deployment using GitHub Actions. Every push to the `main` branch will automatically deploy your Django application to your VPS.

**VPS Details:**
- IP: 185.164.72.165
- User: root
- Deployment path: /root/pilito

## 🎯 Quick Start (5 Steps)

### Step 1: Set Up Your VPS

SSH into your VPS and run the setup script:

```bash
# SSH to VPS (using password: 9188945776poST?)
ssh root@185.164.72.165

# Download and run setup script
# OR manually copy setup_vps.sh to VPS and run:
chmod +x setup_vps.sh
./setup_vps.sh

# Edit .env file with your configuration
nano /root/pilito/.env
```

### Step 2: Set Up SSH Key Authentication (Recommended)

On your **local machine**:

```bash
# Generate SSH key pair
ssh-keygen -t ed25519 -C "github-actions-deploy" -f ~/.ssh/pilito_deploy

# Copy public key to VPS
ssh-copy-id -i ~/.ssh/pilito_deploy.pub root@185.164.72.165

# Test connection (should work without password)
ssh -i ~/.ssh/pilito_deploy root@185.164.72.165
```

### Step 3: Configure GitHub Secrets

Go to your GitHub repository: **Settings → Secrets and variables → Actions → New repository secret**

Add these 3 secrets:

1. **VPS_SSH_PRIVATE_KEY**
   ```bash
   # Copy private key content
   cat ~/.ssh/pilito_deploy
   # Paste the entire output into GitHub secret
   ```

2. **VPS_HOST**
   - Value: `185.164.72.165`

3. **VPS_USER**
   - Value: `root`

### Step 4: Test Locally (Optional but Recommended)

Before deploying to production:

```bash
# Run local test
./test_deployment_locally.sh

# If successful, check services at:
# http://localhost:8000
```

### Step 5: Deploy!

```bash
git add .
git commit -m "Initial deployment setup"
git push origin main
```

✅ Your deployment will start automatically! Watch progress at:
`https://github.com/YOUR_USERNAME/pilito/actions`

## 📁 Project Structure

```
pilito/
├── .github/
│   └── workflows/
│       └── deploy.yml              # GitHub Actions CI/CD workflow
├── docs/
│   └── deployment/
│       ├── VPS_CICD_SETUP.md       # Detailed setup guide
│       └── CICD_QUICK_REFERENCE.md # Quick command reference
├── src/                            # Django application
├── docker-compose.yml              # Docker services configuration
├── Dockerfile                      # Docker image definition
├── setup_vps.sh                    # VPS setup script
├── test_deployment_locally.sh      # Local testing script
└── DEPLOYMENT_README.md            # This file
```

## 🔧 Services Deployed

Your deployment includes:

1. **Django App (Daphne)** - Main application server (port 8000)
2. **PostgreSQL + pgvector** - Database
3. **Redis** - Cache and message broker
4. **Celery Worker** - Background task processing
5. **Celery Beat** - Scheduled task scheduler
6. **Prometheus** - Metrics collection (port 9090)
7. **Grafana** - Monitoring dashboard (port 3001)
8. **Redis Exporter** - Redis metrics
9. **Postgres Exporter** - Database metrics

## 🌐 Access Points

After deployment, access your services:

| Service | URL | Credentials |
|---------|-----|-------------|
| Django API | http://185.164.72.165:8000 | - |
| Django Admin | http://185.164.72.165:8000/admin | Your superuser |
| Grafana | http://185.164.72.165:3001 | admin/admin |
| Prometheus | http://185.164.72.165:9090 | - |

## 🔄 Deployment Process

When you push to `main`, GitHub Actions will:

1. ✅ Checkout your code
2. ✅ Set up SSH authentication
3. ✅ Sync files to VPS (excluding .git, cache, etc.)
4. ✅ Perform aggressive disk cleanup
5. ✅ Stop existing containers
6. ✅ Build new Docker images
7. ✅ Start all services
8. ✅ Run database migrations
9. ✅ Collect static files
10. ✅ Perform health checks
11. ✅ Verify all services

## 📊 Monitoring Deployment

### Via GitHub Actions
1. Go to your repository
2. Click **Actions** tab
3. Click on the latest workflow run
4. View real-time deployment logs

### Via SSH
```bash
# SSH to VPS
ssh root@185.164.72.165

# Check container status
cd /root/pilito
docker-compose ps

# View logs
docker-compose logs -f

# Check specific service
docker logs django_app -f
```

## 🛠️ Common Tasks

### View Logs
```bash
ssh root@185.164.72.165
cd /root/pilito
docker-compose logs -f
```

### Restart Service
```bash
docker-compose restart web
```

### Run Django Command
```bash
docker exec django_app python manage.py <command>
```

### Database Backup
```bash
docker exec postgres_db pg_dump -U pilito_user pilito_db > backup.sql
```

### Manual Cleanup
```bash
cd /root/pilito && ./cleanup.sh
```

## 🔐 Environment Variables

Create `/root/pilito/.env` on your VPS with:

```bash
# Django Settings
DEBUG=False
SECRET_KEY=your-secret-key-here
ALLOWED_HOSTS=185.164.72.165,your-domain.com

# Database
POSTGRES_DB=pilito_db
POSTGRES_USER=pilito_user
POSTGRES_PASSWORD=your-secure-password

# Redis
REDIS_URL=redis://redis:6379

# Add your other variables...
```

**Important:** Never commit `.env` to Git!

## 🐛 Troubleshooting

### Deployment Failed
```bash
# Check GitHub Actions logs first
# Then SSH to VPS and check:
docker-compose logs --tail=100
```

### Container Won't Start
```bash
docker logs <container_name> --tail=100
docker-compose restart <service_name>
```

### Out of Disk Space
```bash
# Run cleanup script
./cleanup.sh

# Or manually
docker system prune -af --volumes
```

### Database Issues
```bash
# Check database
docker exec postgres_db pg_isready

# View logs
docker logs postgres_db

# Restart
docker-compose restart db
```

For more troubleshooting, see: [`docs/deployment/CICD_QUICK_REFERENCE.md`](docs/deployment/CICD_QUICK_REFERENCE.md)

## 📚 Documentation

- **[VPS CI/CD Setup Guide](docs/deployment/VPS_CICD_SETUP.md)** - Complete setup instructions
- **[Quick Reference](docs/deployment/CICD_QUICK_REFERENCE.md)** - Common commands and troubleshooting
- **[Main README](README.md)** - Project documentation

## 🔒 Security Best Practices

1. ✅ Use SSH keys instead of passwords
2. ✅ Keep `.env` file secure (never commit)
3. ✅ Use strong passwords for services
4. ✅ Enable firewall (UFW)
5. ✅ Regular system updates
6. ✅ Monitor access logs
7. ✅ Use HTTPS in production (setup Nginx + SSL)

## 🌟 Advanced Features

### Automated Cleanup
The deployment sets up cron jobs for:
- Weekly Docker cleanup (Sunday 2 AM)
- Daily log rotation (3 AM)
- Daily system cleanup (4 AM)

View: `cat /etc/cron.d/pilito-cleanup`

### Disk Space Monitoring
Automatically checks disk space and warns if < 2GB available

### Health Checks
Verifies all services are running and healthy after deployment

## 🚨 Emergency Commands

### Stop Everything
```bash
docker-compose down
```

### Rollback
```bash
cd /root/pilito
git log --oneline
git checkout <previous-commit>
docker-compose up -d --build
```

### Force Rebuild
```bash
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

## 📞 Support

1. Check deployment logs in GitHub Actions
2. Check container logs: `docker-compose logs`
3. Review documentation in `docs/deployment/`
4. Check system resources: `docker stats` and `df -h`

## ✅ Checklist

Before first deployment:

- [ ] VPS setup script executed
- [ ] `.env` file configured on VPS
- [ ] SSH key generated
- [ ] Public key added to VPS
- [ ] GitHub secrets configured (VPS_SSH_PRIVATE_KEY, VPS_HOST, VPS_USER)
- [ ] Local test passed (optional)
- [ ] Firewall configured
- [ ] First push to main branch

## 🎉 Success!

Once everything is set up:
- Push to `main` → Automatic deployment
- Check GitHub Actions for status
- Access your services at the URLs above
- Monitor with Grafana and Prometheus

Happy deploying! 🚀

---

**Note:** For production use with a domain name, see the domain setup section in [VPS_CICD_SETUP.md](docs/deployment/VPS_CICD_SETUP.md)

