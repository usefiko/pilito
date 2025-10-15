# VPS CI/CD Deployment Setup Guide

This guide will help you set up automated deployment to your VPS using GitHub Actions.

## 📋 Prerequisites

- GitHub repository for your project
- VPS server access (185.164.72.165)
- Docker and Docker Compose installed on VPS
- Git installed on VPS

## 🔐 Security Setup (SSH Key Authentication)

### Step 1: Generate SSH Key Pair (on your local machine)

```bash
# Generate a new SSH key pair specifically for GitHub Actions
ssh-keygen -t ed25519 -C "github-actions-deploy" -f ~/.ssh/pilito_deploy

# This creates two files:
# - ~/.ssh/pilito_deploy (private key) - for GitHub Secrets
# - ~/.ssh/pilito_deploy.pub (public key) - for VPS
```

### Step 2: Add Public Key to VPS

```bash
# Copy the public key to your VPS
ssh-copy-id -i ~/.ssh/pilito_deploy.pub root@185.164.72.165

# Or manually:
# 1. SSH into your VPS with password
ssh root@185.164.72.165

# 2. Add the public key
mkdir -p ~/.ssh
chmod 700 ~/.ssh
echo "YOUR_PUBLIC_KEY_CONTENT" >> ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys
```

### Step 3: Test SSH Key Authentication

```bash
# Test the connection (should work without password)
ssh -i ~/.ssh/pilito_deploy root@185.164.72.165

# If successful, exit
exit
```

## ⚙️ GitHub Repository Setup

### Step 4: Add GitHub Secrets

Go to your GitHub repository → Settings → Secrets and variables → Actions → New repository secret

Add the following secrets:

1. **VPS_SSH_PRIVATE_KEY**
   ```bash
   # On your local machine, copy the private key content:
   cat ~/.ssh/pilito_deploy
   # Copy the entire output including "-----BEGIN OPENSSH PRIVATE KEY-----" and "-----END OPENSSH PRIVATE KEY-----"
   ```
   - Name: `VPS_SSH_PRIVATE_KEY`
   - Value: [paste the private key content]

2. **VPS_HOST**
   - Name: `VPS_HOST`
   - Value: `185.164.72.165`

3. **VPS_USER**
   - Name: `VPS_USER`
   - Value: `root`

### Step 5: Prepare VPS Server

SSH into your VPS and set up the environment:

```bash
ssh root@185.164.72.165

# Update system
apt-get update
apt-get upgrade -y

# Install Docker if not installed
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Install Docker Compose if not installed
apt-get install docker-compose -y

# Create project directory
mkdir -p /root/pilito
cd /root/pilito

# Create .env file with your environment variables
nano .env
```

### Step 6: Configure Environment Variables

Create `/root/pilito/.env` file on your VPS with the following content:

```bash
# Django Settings
DEBUG=False
SECRET_KEY=your-secret-key-here
ALLOWED_HOSTS=185.164.72.165,your-domain.com

# Database Configuration
POSTGRES_DB=pilito_db
POSTGRES_USER=pilito_user
POSTGRES_PASSWORD=your-secure-password-here

# Redis
REDIS_URL=redis://redis:6379

# RapidAPI
RAPIDAPI_KEY=your-rapidapi-key

# Email Configuration
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=email-smtp.us-east-2.amazonaws.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email-user
EMAIL_HOST_PASSWORD=your-email-password

# Google OAuth (if applicable)
GOOGLE_OAUTH2_CLIENT_ID=your-client-id
GOOGLE_OAUTH2_CLIENT_SECRET=your-client-secret
GOOGLE_OAUTH2_REDIRECT_URI=https://your-domain.com/api/v1/usr/google/callback

# Add any other environment variables your project needs
```

## 🚀 Deployment Process

### Automatic Deployment

The deployment will automatically trigger when you push to the `main` branch:

```bash
git add .
git commit -m "Your commit message"
git push origin main
```

GitHub Actions will:
1. ✅ Checkout your code
2. ✅ Set up SSH authentication
3. ✅ Sync files to VPS (excluding .git, __pycache__, etc.)
4. ✅ Perform disk cleanup
5. ✅ Stop existing containers
6. ✅ Build new Docker images
7. ✅ Start all services
8. ✅ Run health checks
9. ✅ Run migrations
10. ✅ Collect static files
11. ✅ Verify all services are running

### Manual Deployment

If you need to deploy manually:

```bash
# SSH into VPS
ssh root@185.164.72.165

# Navigate to project directory
cd /root/pilito

# Pull latest changes
git pull origin main

# Stop containers
docker-compose down

# Rebuild and start
docker-compose up -d --build

# Check status
docker-compose ps
```

## 📊 Monitoring Deployment

### View GitHub Actions Workflow

1. Go to your GitHub repository
2. Click on "Actions" tab
3. Click on the latest workflow run
4. View real-time logs

### Check Services on VPS

```bash
# SSH into VPS
ssh root@185.164.72.165

# Check running containers
docker-compose ps

# View logs
docker-compose logs -f

# View specific service logs
docker logs django_app
docker logs celery_worker
docker logs postgres_db

# Check disk space
df -h

# Check Docker resource usage
docker stats
```

## 🔧 Troubleshooting

### Deployment Failed

1. **Check GitHub Actions logs** for error messages
2. **SSH into VPS** and check container logs:
   ```bash
   docker-compose logs --tail=100
   ```

### Containers Not Starting

```bash
# Check container status
docker-compose ps

# View specific container logs
docker logs django_app --tail=100

# Restart specific service
docker-compose restart web
```

### Disk Space Issues

```bash
# Check disk usage
df -h

# Manual cleanup
docker system prune -af --volumes

# Check what's using space
du -sh /* | sort -hr | head -10
```

### Database Connection Issues

```bash
# Check if database is running
docker exec postgres_db pg_isready

# Check database logs
docker logs postgres_db --tail=50

# Access database
docker exec -it postgres_db psql -U pilito_user -d pilito_db
```

### Port Conflicts

```bash
# Check what's using a port
netstat -tuln | grep 8000

# Kill process using a port
lsof -ti:8000 | xargs kill -9
```

## 🛡️ Security Best Practices

1. **Never commit `.env` file** - it's in `.gitignore`
2. **Use strong passwords** for database and other services
3. **Keep SSH keys secure** - never share private keys
4. **Regular updates**:
   ```bash
   apt-get update && apt-get upgrade -y
   ```
5. **Set up firewall**:
   ```bash
   ufw allow 22/tcp
   ufw allow 80/tcp
   ufw allow 443/tcp
   ufw allow 8000/tcp
   ufw enable
   ```

## 🔄 Automated Cleanup

The deployment automatically sets up cron jobs for:
- Weekly Docker cleanup (Sunday 2 AM)
- Daily log rotation (3 AM)
- Daily system log cleanup (4 AM)

Check cleanup configuration:
```bash
cat /etc/cron.d/pilito-cleanup
```

## 📝 Service Endpoints

After deployment, your services will be available at:

- **Django API**: http://185.164.72.165:8000
- **Prometheus**: http://185.164.72.165:9090
- **Grafana**: http://185.164.72.165:3001
- **Redis Exporter**: http://185.164.72.165:9121
- **Postgres Exporter**: http://185.164.72.165:9187
- **Celery Metrics**: http://185.164.72.165:9808

## 🌐 Domain Setup (Optional)

To use a custom domain:

1. **Point your domain** to `185.164.72.165`
2. **Install Nginx**:
   ```bash
   apt-get install nginx -y
   ```
3. **Configure reverse proxy** (create `/etc/nginx/sites-available/pilito`):
   ```nginx
   server {
       listen 80;
       server_name your-domain.com;
       
       location / {
           proxy_pass http://localhost:8000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           proxy_set_header X-Forwarded-Proto $scheme;
       }
   }
   ```
4. **Enable site**:
   ```bash
   ln -s /etc/nginx/sites-available/pilito /etc/nginx/sites-enabled/
   nginx -t
   systemctl restart nginx
   ```
5. **Install SSL** with Let's Encrypt:
   ```bash
   apt-get install certbot python3-certbot-nginx -y
   certbot --nginx -d your-domain.com
   ```

## 📞 Support

If you encounter any issues:
1. Check GitHub Actions logs
2. Check VPS container logs
3. Review this documentation
4. Check Django/Docker documentation

## 🎉 Success!

Your CI/CD pipeline is now set up! Every push to `main` will automatically deploy to your VPS.

