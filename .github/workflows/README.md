# GitHub Actions Workflows

## Available Workflows

### 1. deploy.yml (CURRENTLY ACTIVE)
**Your existing deployment workflow**

- **Trigger**: Push to `main` branch
- **Purpose**: Deploy using docker-compose
- **Secrets**: VPS_SSH_PRIVATE_KEY, VPS_HOST, VPS_USER
- **Status**: ✅ Active and working

### 2. deploy-production.yml (NEW - Docker Swarm)
**High availability deployment**

- **Trigger**: Push to `main` branch (disabled by default)
- **Purpose**: Deploy using Docker Swarm with 3 replicas
- **Secrets**: SSH_PRIVATE_KEY, SSH_HOST, SSH_USER
- **Features**: 
  - Runs tests first
  - Deploys with zero downtime
  - Automatic rollback on failure
  - Health checks after deployment
- **Status**: 🔄 Ready (rename secrets or workflow)

### 3. test-pr.yml
**Pull request testing**

- **Trigger**: Pull requests to `main`
- **Purpose**: Run tests and code quality checks
- **Status**: ✅ Ready

### 4. manual-deploy.yml
**Manual deployment trigger**

- **Trigger**: Manual from GitHub Actions tab
- **Purpose**: Deploy on-demand with options
- **Status**: ✅ Ready

---

## Which One is Running?

Currently **deploy.yml** runs automatically on every push to `main`.

To switch to **deploy-production.yml** (Docker Swarm):

1. Rename or disable `deploy.yml`:
   ```bash
   mv .github/workflows/deploy.yml .github/workflows/deploy.yml.disabled
   ```

2. Update secrets in `deploy-production.yml` to match yours:
   ```yaml
   SSH_PRIVATE_KEY: ${{ secrets.VPS_SSH_PRIVATE_KEY }}
   SSH_HOST: ${{ secrets.VPS_HOST }}
   SSH_USER: ${{ secrets.VPS_USER }}
   ```

3. Initialize Swarm on server:
   ```bash
   ./swarm_init.sh
   ```

4. Push to trigger deployment

---

## Recent Updates

### Docker Compose V2 Fix
All workflows updated to use `docker compose` (V2) instead of `docker-compose` (V1) for compatibility with GitHub Actions runners.

---

## Documentation

See [AUTOMATED_DEPLOYMENT.md](../../AUTOMATED_DEPLOYMENT.md) for complete guide.
