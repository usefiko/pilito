# 🚀 Fiko Backend - Disk Management Quick Guide

## Problem Solved ✅
Server disk space filling up after multiple GitHub Actions deployments due to accumulating Docker images, containers, logs, and build cache.

## Automated Solutions Implemented

### 1. Enhanced GitHub Actions Workflow
- **Aggressive cleanup** before every deployment
- **Optimized Docker builds** with BuildKit
- **Automatic monitoring** and alerting setup
- **Post-deployment cleanup** and health checks

### 2. Disk Cleanup Script (`disk_cleanup.sh`)
```bash
# Manual cleanup
./disk_cleanup.sh --force

# See what would be cleaned (safe)
./disk_cleanup.sh --dry-run
```

### 3. Disk Monitor (`disk_monitor.sh`)
```bash
# Check current status
./disk_monitor.sh

# Setup automated monitoring
./disk_monitor.sh --setup
```

## Quick Commands for Emergencies

### Immediate Docker Cleanup
```bash
# Emergency cleanup (run when disk is >95% full)
docker stop $(docker ps -aq) 2>/dev/null || true
docker system prune -af --volumes
docker builder prune -af
```

### System Cleanup
```bash
# Clear logs and temp files
sudo journalctl --vacuum-time=1d
sudo rm -rf /tmp/*
sudo apt-get clean && sudo apt-get autoremove -y
```

### Check Disk Usage
```bash
# Current usage
df -h

# Largest directories
sudo du -h / 2>/dev/null | sort -hr | head -10

# Docker space usage
docker system df
```

## Automated Features

✅ **Every 30 minutes**: Disk monitoring and alerts  
✅ **Every deployment**: Comprehensive cleanup  
✅ **Weekly**: Full system cleanup  
✅ **Daily**: Docker log truncation  

## Monitoring Thresholds

- 🟢 **< 85%**: Normal operation
- 🟡 **85-90%**: Warning alerts  
- 🔴 **> 90%**: Critical - auto cleanup triggered

## Files Added/Modified

- `.github/workflows/deploy.yml` - Enhanced with cleanup
- `disk_cleanup.sh` - Comprehensive cleanup script
- `disk_monitor.sh` - Monitoring and alerting
- `Dockerfile` - Multi-stage optimized build
- `.dockerignore` - Reduced build context
- `docs/DISK_SPACE_OPTIMIZATION.md` - Complete guide

## Key Benefits

🔹 **Automatic**: No manual intervention needed  
🔹 **Proactive**: Prevents disk full situations  
🔹 **Safe**: Dry-run options and safety checks  
🔹 **Comprehensive**: Cleans Docker, system, logs, cache  
🔹 **Monitored**: Continuous tracking and alerting  
🔹 **Optimized**: Smaller images and faster builds  

## Emergency Contact

If disk is critically full (>95%), run:
```bash
./disk_cleanup.sh --force && ./disk_monitor.sh --verbose
```

## Logs Location
- Monitor logs: `/var/log/disk_monitor.log`
- Weekly cleanup: `/tmp/weekly-cleanup.log`
- Deployment logs: GitHub Actions output

---
💡 **Note**: All cleanup operations are now automated via GitHub Actions [[memory:4943267]] and require no manual management [[memory:4943021]].
