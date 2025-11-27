# Pilito Production Server - Disk Space Emergency Fix

## Problem
Your production server ran out of disk space while deploying Docker containers with PyTorch/CUDA libraries.

## Error
```
failed to extract layer sha256:... write .../libtorch_cuda.so: no space left on device
```

## Immediate Solutions

### Option 1: Run Emergency Cleanup (RECOMMENDED)

```bash
# From your local machine
cd /Users/nima/Projects/pilito
bash scripts/emergency_fix.sh
```

This will SSH to your server and:
- Stop all containers
- Remove unused Docker images
- Clean build cache
- Free up disk space

### Option 2: Manual Cleanup on Server

SSH to your server and run:

```bash
ssh root@46.249.98.162

# Check disk space
df -h

# Stop all containers
docker stop $(docker ps -aq)

# Remove everything Docker (nuclear option)
docker system prune -a -f --volumes

# Check if you have space now
df -h

# You should have at least 15GB free
```

### Option 3: Use Optimized Dockerfile (Reduces Size by 70%)

The current Dockerfile installs PyTorch with CUDA (~7GB). Most servers don't need GPU support.

Replace your Dockerfile with the optimized version:

```bash
# Backup current Dockerfile
mv Dockerfile Dockerfile.backup

# Use optimized version (CPU-only PyTorch)
mv Dockerfile.optimized Dockerfile

# Commit and push
git add Dockerfile
git commit -m "Use optimized CPU-only PyTorch to reduce image size"
git push origin main
```

This reduces image size from ~7GB to ~2GB!

## Long-term Solutions

### 1. Update GitHub Actions (Already Done)

Your `.github/workflows/deploy-production.yml` now includes:
- Automatic disk cleanup before deployment
- Disk space verification (checks for 15GB minimum)
- Post-deployment cleanup

### 2. Set Up Cron Job for Maintenance

On your server, create a weekly cleanup:

```bash
ssh root@46.249.98.162

# Create maintenance script
cat > /root/docker-maintenance.sh << 'EOF'
#!/bin/bash
docker system prune -a -f
docker volume prune -f
docker builder prune -a -f
apt-get clean
journalctl --vacuum-time=7d
EOF

chmod +x /root/docker-maintenance.sh

# Add to crontab (runs every Sunday at 3 AM)
(crontab -l 2>/dev/null; echo "0 3 * * 0 /root/docker-maintenance.sh >> /var/log/docker-maintenance.log 2>&1") | crontab -
```

### 3. Monitor Disk Space

Add disk space monitoring to avoid this in the future:

```bash
# Check disk space
df -h

# Check Docker usage
docker system df

# Check largest directories
du -sh /* | sort -rh | head -10
```

### 4. Increase Server Disk Size

If cleanup doesn't help, consider upgrading your server disk:
- Current: Likely 20-40GB
- Recommended: 60-100GB for ML workloads with PyTorch

## Server Details

**Production Server:**
- IP: `46.249.98.162`
- User: `root`
- Project path: `~/pilito` (or check `/var/www/pilito` or `/opt/pilito`)

## Verification Steps

After cleanup, verify deployment works:

```bash
# On your local machine
git add .
git commit -m "Fix disk space issues with optimized Docker setup"
git push origin main

# Monitor deployment
# Check GitHub Actions: https://github.com/YOUR_USERNAME/pilito/actions

# Or deploy manually on server
ssh root@46.249.98.162
cd ~/pilito
docker-compose down
docker-compose up -d --build
docker-compose ps
```

## Health Check

After deployment:

```bash
# Check services
docker ps

# Check logs
docker logs django_app
docker logs celery_worker
docker logs celery_ai

# Check disk space
df -h

# Check Docker usage
docker system df
```

## Emergency Contacts

If deployment fails after cleanup:

1. **Check logs:**
   ```bash
   docker-compose logs --tail=100
   ```

2. **Rollback:**
   ```bash
   cd ~/pilito
   git pull origin main
   docker-compose down
   docker-compose up -d
   ```

3. **Nuclear option (start fresh):**
   ```bash
   docker-compose down -v
   docker system prune -a -f --volumes
   docker-compose up -d --build
   ```

## Prevention Checklist

- [ ] Run `scripts/emergency_fix.sh` to clean current server
- [ ] Replace Dockerfile with optimized version
- [ ] Set up weekly cron job for maintenance
- [ ] Verify GitHub Actions deployment works
- [ ] Monitor disk space regularly
- [ ] Consider upgrading server disk if issues persist

## Need More Help?

If you still have issues:
1. Check available disk: `df -h`
2. Check Docker usage: `docker system df`
3. Find large files: `du -sh /* | sort -rh`
4. Consider: Increasing disk size or using Docker image registry

