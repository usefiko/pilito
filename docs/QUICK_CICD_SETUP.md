# Quick CI/CD Setup - 5 Minutes

## 🎯 Goal
Push code → Automatic deployment to production. No manual work!

---

## ⚡ Quick Setup (5 Steps)

### 1. On Your Production Server

```bash
# SSH to your server
ssh user@your-server

# Generate SSH key for GitHub Actions
ssh-keygen -t rsa -b 4096 -f ~/.ssh/github_deploy_key -N ""

# Add it to authorized_keys
cat ~/.ssh/github_deploy_key.pub >> ~/.ssh/authorized_keys

# Copy the PRIVATE key (you'll need this)
cat ~/.ssh/github_deploy_key
# Copy everything including -----BEGIN and -----END lines
```

### 2. On GitHub

Go to your repo: **Settings** → **Secrets** → **Actions** → **New secret**

Add these 3 secrets:

| Name | Value |
|------|-------|
| `SSH_PRIVATE_KEY` | Paste the private key from step 1 |
| `SSH_HOST` | Your server IP (e.g., `123.45.67.89`) |
| `SSH_USER` | Your username (e.g., `ubuntu`, `root`) |

### 3. Create .env on Server

```bash
# On your production server
cd ~/pilito
nano .env
```

Paste:
```env
STAGE=PROD
DEBUG=False
SECRET_KEY=change-this-to-random-secret
POSTGRES_DB=pilito_prod
POSTGRES_USER=pilito_user
POSTGRES_PASSWORD=secure-password-here
POSTGRES_HOST=db
POSTGRES_PORT=5432
REDIS_URL=redis://redis:6379/0
```

### 4. Push Your Code

```bash
# On your local machine
git add .
git commit -m "Setup CI/CD"
git push origin main
```

### 5. Watch It Deploy

1. Go to GitHub → **Actions** tab
2. See your deployment running
3. ☕ Wait ~2-3 minutes
4. ✅ Done! Your code is live!

---

## 🎬 What Happens Now?

Every time you push to `main`:

```
Push Code → Tests → Build → Deploy → Health Check → ✅ Live!
```

**Fully automatic!** No SSH, no manual commands.

---

## 🔍 Check Deployment Status

- **GitHub**: Actions tab shows all deployments
- **Email**: GitHub sends you notifications
- **Server**: SSH and run `make status`

---

## 🚨 If Something Goes Wrong

### Deployment fails?
→ Automatic rollback happens! Your site stays online.

### Need to redeploy?
→ GitHub → Actions → "Manual Deploy" → Run workflow

### Need to check logs?
```bash
ssh user@your-server
cd ~/pilito
make logs service=web
```

---

## ✅ Test It Works

```bash
# Make a small change
echo "# Test" >> README.md

# Push
git add .
git commit -m "Test deployment"
git push origin main

# Watch it deploy automatically in GitHub Actions!
```

---

## 📚 Full Documentation

Need more details? See:
- **[CI_CD_SETUP.md](CI_CD_SETUP.md)** - Complete setup guide
- **[DOCKER_SWARM_GUIDE.md](DOCKER_SWARM_GUIDE.md)** - Swarm guide

---

## 🎯 Summary

```bash
# One-time setup
1. Generate SSH key on server
2. Add 3 GitHub secrets
3. Create .env on server

# Every deployment (automatic!)
git push origin main
# That's it! ✅
```

**Never SSH to deploy again!** 🚀

