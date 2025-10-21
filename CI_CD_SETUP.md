# CI/CD Automatic Deployment Setup

## 🎯 What This Does

When you push code to GitHub, it will **automatically**:
1. ✅ Run tests to make sure everything works
2. 🔨 Build new Docker images
3. 📦 Deploy to your production server using Docker Swarm
4. 🏥 Run health checks
5. 🔄 Rollback automatically if deployment fails

**You don't need to do anything manually!** Just push your code.

---

## 📋 Prerequisites

Before setting up automatic deployment, you need:

1. **A production server** (VPS, cloud instance, etc.)
   - Docker and Docker Compose installed
   - SSH access enabled
   - At least 8GB RAM, 4 CPU cores

2. **GitHub repository** with your code

3. **SSH key pair** for authentication

---

## 🚀 Setup Instructions

### Step 1: Prepare Your Production Server

SSH into your production server and run:

```bash
# Install Docker (if not already installed)
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Add your user to docker group
sudo usermod -aG docker $USER
newgrp docker

# Create project directory
mkdir -p ~/pilito
cd ~/pilito

# Create .env file with production settings
nano .env
```

**Important**: Create your `.env` file with production values:
```env
STAGE=PROD
DEBUG=False
SECRET_KEY=your-super-secret-production-key-change-this
POSTGRES_DB=pilito_prod
POSTGRES_USER=pilito_user
POSTGRES_PASSWORD=your-secure-database-password
POSTGRES_HOST=db
POSTGRES_PORT=5432
REDIS_URL=redis://redis:6379/0
ALLOWED_HOSTS=your-domain.com,your-server-ip
# Add other production settings...
```

### Step 2: Generate SSH Key for GitHub Actions

On your **production server**, create an SSH key:

```bash
# Generate SSH key (press Enter for all prompts)
ssh-keygen -t rsa -b 4096 -f ~/.ssh/github_deploy_key -N ""

# Add the public key to authorized_keys
cat ~/.ssh/github_deploy_key.pub >> ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys

# Display the private key (you'll need this for GitHub)
cat ~/.ssh/github_deploy_key
```

**Copy the entire private key output** (including `-----BEGIN` and `-----END` lines).

### Step 3: Configure GitHub Secrets

Go to your GitHub repository:

1. Go to **Settings** → **Secrets and variables** → **Actions**
2. Click **"New repository secret"**
3. Add these secrets:

| Secret Name | Value | Description |
|-------------|-------|-------------|
| `SSH_PRIVATE_KEY` | The private key you copied | SSH private key for deployment |
| `SSH_HOST` | Your server IP or domain | Example: `123.45.67.89` or `server.example.com` |
| `SSH_USER` | Your server username | Example: `ubuntu`, `root`, or your username |

**How to add secrets:**

```
SSH_PRIVATE_KEY:
-----BEGIN OPENSSH PRIVATE KEY-----
b3BlbnNzaC1rZXktdjEAAAAABG5vbmUAAAAEbm9uZQAAAAAAAAABAAABlwAAAAdzc2gtcn
... (paste the entire private key)
-----END OPENSSH PRIVATE KEY-----

SSH_HOST:
123.45.67.89

SSH_USER:
ubuntu
```

### Step 4: Test SSH Connection

From your **local machine**, test if GitHub Actions can connect:

```bash
# Test SSH connection (replace with your values)
ssh -i path/to/private/key username@your-server-ip

# If it works, you're good to go!
```

### Step 5: Push to GitHub

Once secrets are configured:

```bash
# Add all files
git add .

# Commit
git commit -m "Add CI/CD for automatic deployment"

# Push to main/master branch
git push origin main
```

**That's it!** GitHub Actions will automatically:
1. Run tests
2. Deploy to production
3. Run health checks
4. Notify you of success/failure

---

## 🎬 How It Works

### Workflow Triggers

#### 1. **Automatic Deployment** (deploy-production.yml)
Triggers on every push to `main` or `master` branch:

```
Code Push → Tests → Build → Deploy → Health Check → ✅
```

If deployment fails, automatic rollback happens!

#### 2. **Pull Request Testing** (test-pr.yml)
Runs tests on every pull request:

```
Pull Request → Tests → Code Quality Check → ✅ or ❌
```

#### 3. **Manual Deployment** (manual-deploy.yml)
Deploy manually from GitHub Actions tab:

```
GitHub → Actions → Manual Deploy → Run workflow
```

---

## 📊 Deployment Process

### What Happens When You Push Code:

```
┌─────────────────────────────────────────────────┐
│  1. You push code to GitHub                     │
└─────────────────┬───────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────┐
│  2. GitHub Actions starts automatically         │
│     - Checkout code                              │
│     - Create test environment                    │
└─────────────────┬───────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────┐
│  3. Run Tests                                    │
│     - Build Docker images                        │
│     - Start services                             │
│     - Run Django tests                           │
│     - Check health endpoint                      │
└─────────────────┬───────────────────────────────┘
                  │
         ┌────────┴────────┐
         │   Tests Pass?    │
         └────────┬────────┘
                  │
         ┌────────▼────────┐
         │       Yes       │
         └────────┬────────┘
                  │
┌─────────────────▼───────────────────────────────┐
│  4. Connect to Production Server via SSH        │
│     - Copy files to server                       │
│     - Build new Docker images                    │
└─────────────────┬───────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────┐
│  5. Deploy to Docker Swarm                       │
│     - Initialize Swarm (if needed)               │
│     - Run ./swarm_deploy.sh                      │
│     - Rolling update (zero downtime)             │
└─────────────────┬───────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────┐
│  6. Health Checks                                │
│     - Verify all services are healthy            │
│     - Check service replicas                     │
└─────────────────┬───────────────────────────────┘
                  │
         ┌────────▼────────┐
         │  Deployment OK?  │
         └────────┬────────┘
                  │
         ┌────────▼────────┐
         │       Yes       │
         └────────┬────────┘
                  │
┌─────────────────▼───────────────────────────────┐
│  7. ✅ Deployment Complete!                     │
│     - Notification sent                          │
│     - Services running with 3 replicas           │
└─────────────────────────────────────────────────┘

         If deployment fails at any step:
                  │
┌─────────────────▼───────────────────────────────┐
│  🔄 Automatic Rollback                          │
│     - Rollback to previous version               │
│     - Services continue running                  │
│     - Notification sent                          │
└─────────────────────────────────────────────────┘
```

---

## 🔍 Monitoring Your Deployments

### View Deployment Status

1. Go to your GitHub repository
2. Click the **"Actions"** tab
3. See all your workflows and their status

### Deployment Logs

Click on any workflow run to see:
- Test results
- Build logs
- Deployment progress
- Health check results
- Any errors

### Email Notifications

GitHub automatically sends you emails:
- ✅ When deployment succeeds
- ❌ When deployment fails
- 🔄 When rollback occurs

---

## 🛠️ Customization

### Change Deployment Branch

Edit `.github/workflows/deploy-production.yml`:

```yaml
on:
  push:
    branches:
      - main          # Deploy on push to main
      - production    # Add more branches
```

### Skip Tests (Not Recommended)

In manual deployment workflow, you can skip tests:
1. Go to Actions → Manual Deploy
2. Check "Skip tests"
3. Run workflow

### Add Slack/Discord Notifications

Add notification steps to workflows:

```yaml
- name: Notify Slack
  uses: 8398a7/action-slack@v3
  with:
    status: ${{ job.status }}
    webhook_url: ${{ secrets.SLACK_WEBHOOK }}
```

---

## 🔐 Security Best Practices

### 1. Never Commit Secrets

✅ **DO**: Store in GitHub Secrets  
❌ **DON'T**: Commit `.env` files or secrets to Git

```bash
# Make sure .env is in .gitignore
echo ".env" >> .gitignore
```

### 2. Rotate SSH Keys Regularly

Every 3-6 months:
1. Generate new SSH key
2. Update GitHub secret
3. Remove old key from server

### 3. Use Different Keys for Different Environments

- One key for production
- One key for staging
- Never reuse keys

### 4. Limit SSH Key Permissions

On your server:

```bash
# Restrict SSH key to specific commands (advanced)
echo 'command="cd ~/pilito && ./swarm_deploy.sh" ssh-rsa AAAA...' >> ~/.ssh/authorized_keys
```

---

## 🧪 Testing the CI/CD Pipeline

### Test 1: Push a Small Change

```bash
# Make a small change
echo "# Test" >> README.md

# Commit and push
git add .
git commit -m "Test CI/CD pipeline"
git push origin main

# Go to GitHub Actions tab and watch it deploy!
```

### Test 2: Manual Deployment

1. Go to GitHub → Actions
2. Click "Manual Deploy to Production"
3. Click "Run workflow"
4. Choose options and run

### Test 3: Pull Request Testing

```bash
# Create a new branch
git checkout -b test-feature

# Make changes
echo "# New feature" >> README.md

# Push and create PR
git add .
git commit -m "Add new feature"
git push origin test-feature

# Create PR on GitHub - tests will run automatically
```

---

## 🚨 Troubleshooting

### Deployment Fails: "Permission Denied"

**Problem**: SSH authentication failed

**Solution**:
1. Check `SSH_PRIVATE_KEY` secret is correct
2. Verify public key is in `~/.ssh/authorized_keys` on server
3. Check file permissions: `chmod 600 ~/.ssh/authorized_keys`

### Deployment Fails: "Connection Refused"

**Problem**: Can't connect to server

**Solution**:
1. Check `SSH_HOST` is correct
2. Verify server firewall allows SSH (port 22)
3. Test connection manually: `ssh user@host`

### Deployment Succeeds but Site is Down

**Problem**: Services not healthy

**Solution**:
1. SSH to server: `ssh user@your-server`
2. Check status: `make status`
3. Check logs: `make logs service=web`
4. Run health check: `make health`

### Tests Fail in CI but Pass Locally

**Problem**: Different environment

**Solution**:
1. Check if `.env` values are correct in workflow
2. Ensure all dependencies are in `requirements/base.txt`
3. Check Docker Compose configuration

---

## 📚 Workflow Files Explained

### 1. deploy-production.yml
- **Triggers**: Push to main/master
- **Does**: Tests → Deploy → Verify
- **Rollback**: Automatic on failure

### 2. test-pr.yml
- **Triggers**: Pull requests
- **Does**: Tests → Code quality checks
- **Purpose**: Catch issues before merging

### 3. manual-deploy.yml
- **Triggers**: Manual trigger
- **Does**: Deploy on-demand
- **Use case**: Emergency deployments

---

## ✅ Success Checklist

Before going live with CI/CD:

- [ ] Production server has Docker installed
- [ ] `.env` file configured on server
- [ ] SSH key generated and added to server
- [ ] GitHub secrets configured (SSH_PRIVATE_KEY, SSH_HOST, SSH_USER)
- [ ] Tested SSH connection works
- [ ] Pushed code to test the pipeline
- [ ] Verified deployment in Actions tab
- [ ] Checked website is accessible
- [ ] Health checks passing

---

## 🎉 You're Done!

Now whenever you:
1. **Push to main** → Automatic deployment
2. **Create PR** → Automatic testing
3. **Need manual deploy** → One-click deployment

**No more manual deployment!** 🚀

---

## 📞 Support

If you encounter issues:
1. Check GitHub Actions logs
2. SSH to server and check logs: `make logs service=web`
3. Run health checks: `make health`
4. Review this guide

---

## 🔄 Typical Development Workflow

```bash
# 1. Develop locally
make dev-up
# ... code code code ...
make dev-down

# 2. Commit your changes
git add .
git commit -m "Add new feature"

# 3. Push to GitHub
git push origin main

# 4. ☕ Grab coffee while GitHub deploys automatically
# 5. ✅ Get notification: Deployment successful!
# 6. Your production site is updated!
```

**It's that simple!** 🎯

