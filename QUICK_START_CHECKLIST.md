# 🚀 Quick Start Checklist - CI/CD Deployment

Use this checklist to set up your CI/CD pipeline in 15 minutes.

## ☑️ Pre-Deployment Checklist

### Step 1: Prepare VPS (5 minutes)

```bash
# 1. SSH to your VPS
ssh root@185.164.72.165
# Password: 9188945776poST?

# 2. Run these commands on VPS:
apt-get update && apt-get upgrade -y
curl -fsSL https://get.docker.com -o get-docker.sh && sh get-docker.sh
apt-get install -y docker-compose git

# 3. Create project directory
mkdir -p /root/pilito && cd /root/pilito

# 4. Create .env file
nano .env
```

**Paste this into .env and customize:**
```bash
DEBUG=False
SECRET_KEY=your-secret-key-change-this
ALLOWED_HOSTS=185.164.72.165
POSTGRES_DB=pilito_db
POSTGRES_USER=pilito_user
POSTGRES_PASSWORD=your-secure-password-here
REDIS_URL=redis://redis:6379
RAPIDAPI_KEY=your-key-if-needed
```

Save (Ctrl+O, Enter, Ctrl+X)

```bash
# 5. Exit VPS
exit
```

**✅ VPS Ready**

---

### Step 2: Generate SSH Keys (2 minutes)

```bash
# On your LOCAL machine:

# Generate new SSH key
ssh-keygen -t ed25519 -C "github-actions-deploy" -f ~/.ssh/pilito_deploy
# Press Enter 3 times (no passphrase)

# Copy to VPS
ssh-copy-id -i ~/.ssh/pilito_deploy.pub root@185.164.72.165
# Enter password when prompted

# Test (should NOT ask for password)
ssh -i ~/.ssh/pilito_deploy root@185.164.72.165
# If successful: exit
```

**✅ SSH Keys Configured**

---

### Step 3: Configure GitHub Secrets (3 minutes)

Go to: `https://github.com/YOUR_USERNAME/pilito/settings/secrets/actions`

Click **"New repository secret"** for each:

#### Secret 1: VPS_SSH_PRIVATE_KEY
```bash
# On local machine, copy private key:
cat ~/.ssh/pilito_deploy
```
- Name: `VPS_SSH_PRIVATE_KEY`
- Value: [Paste ENTIRE output including BEGIN and END lines]
- Click "Add secret"

#### Secret 2: VPS_HOST
- Name: `VPS_HOST`
- Value: `185.164.72.165`
- Click "Add secret"

#### Secret 3: VPS_USER
- Name: `VPS_USER`
- Value: `root`
- Click "Add secret"

**✅ GitHub Secrets Added**

---

### Step 4: Test Locally (Optional, 3 minutes)

```bash
# On local machine in project directory:
./test_deployment_locally.sh

# If successful, visit:
# http://localhost:8000

# Stop local containers:
docker-compose down
```

**✅ Local Test Passed** (or skip this step)

---

### Step 5: Deploy! (2 minutes)

```bash
# Make sure you're on main branch
git branch

# Commit and push
git add .
git commit -m "Setup CI/CD deployment"
git push origin main
```

**Watch deployment:**
- Go to: `https://github.com/YOUR_USERNAME/pilito/actions`
- Click on the running workflow
- Watch real-time logs

**✅ Deployed!**

---

## 🎯 Post-Deployment Verification

After deployment completes:

### 1. Check GitHub Actions
- [ ] Workflow shows green checkmark ✅
- [ ] All steps completed successfully

### 2. Check Services
```bash
ssh root@185.164.72.165
cd /root/pilito
docker-compose ps
```

You should see all containers "Up":
- [ ] django_app
- [ ] postgres_db
- [ ] redis_cache
- [ ] celery_worker
- [ ] celery_beat
- [ ] prometheus
- [ ] grafana

### 3. Access Your Services

Visit in browser:
- [ ] Django API: http://185.164.72.165:8000
- [ ] Django Admin: http://185.164.72.165:8000/admin
- [ ] Grafana: http://185.164.72.165:3001 (admin/admin)
- [ ] Prometheus: http://185.164.72.165:9090

### 4. Create Django Superuser

```bash
ssh root@185.164.72.165
cd /root/pilito
docker exec -it django_app python manage.py createsuperuser
```

**✅ All Services Running**

---

## 📋 Daily Usage

### Deploy Changes
```bash
git add .
git commit -m "Your changes"
git push origin main
# Automatic deployment starts!
```

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

### Check Status
```bash
docker-compose ps
```

---

## 🔧 Quick Commands Reference

| Task | Command |
|------|---------|
| SSH to VPS | `ssh root@185.164.72.165` |
| View all logs | `docker-compose logs -f` |
| View Django logs | `docker logs django_app -f` |
| Restart all | `docker-compose restart` |
| Check status | `docker-compose ps` |
| Run Django command | `docker exec django_app python manage.py <cmd>` |
| Access database | `docker exec -it postgres_db psql -U pilito_user -d pilito_db` |
| Check disk space | `df -h` |
| Clean up disk | `cd /root/pilito && ./cleanup.sh` |

---

## 🚨 Troubleshooting

### Deployment Failed
1. Check GitHub Actions logs
2. SSH to VPS: `ssh root@185.164.72.165`
3. Check logs: `cd /root/pilito && docker-compose logs`

### Container Not Running
```bash
docker logs <container_name> --tail=100
docker-compose restart <service_name>
```

### Out of Disk Space
```bash
cd /root/pilito
./cleanup.sh
```

### Need Help?
- Check: `docs/deployment/CICD_QUICK_REFERENCE.md`
- Check: `docs/deployment/VPS_CICD_SETUP.md`

---

## ✅ Success Indicators

You're good when:
- ✅ GitHub Actions shows green checkmark
- ✅ All containers running (`docker-compose ps`)
- ✅ Can access http://185.164.72.165:8000
- ✅ Django admin accessible
- ✅ No errors in logs

---

## 📞 Emergency Commands

### Stop Everything
```bash
docker-compose down
```

### Restart Everything
```bash
docker-compose restart
```

### Rebuild Everything
```bash
docker-compose down
docker-compose up -d --build
```

### View Recent Logs
```bash
docker-compose logs --tail=100
```

---

## 🎉 You're Done!

- Every push to `main` = automatic deployment
- Check GitHub Actions for deployment status
- Monitor with Grafana at http://185.164.72.165:3001
- View metrics in Prometheus at http://185.164.72.165:9090

**Happy deploying! 🚀**

---

**Time to Complete:** ~15 minutes  
**Difficulty:** Easy  
**Support:** See `DEPLOYMENT_README.md` for detailed guide

