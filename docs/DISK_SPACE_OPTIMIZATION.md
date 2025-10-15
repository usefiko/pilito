# Disk Space Optimization Guide

This guide covers comprehensive disk space management and optimization strategies for the Fiko Backend deployment.

## Problem Overview

During GitHub Actions deployments, Docker images, containers, build cache, and log files accumulate, causing server disk space to fill up quickly. This document provides automated solutions to prevent and resolve disk space issues.

## Automated Solutions Implemented

### 1. Enhanced GitHub Actions Workflow

The deployment workflow (`.github/workflows/deploy.yml`) now includes:

- **Aggressive Docker cleanup** before each deployment
- **Build cache optimization** using Docker BuildKit
- **Container and image pruning** strategies
- **System-wide cleanup** including logs, temp files, and caches
- **Disk space monitoring** and reporting

#### Key Improvements:
```yaml
# Always perform aggressive cleanup before deployment
- Stop all containers and remove unused resources
- Clean Docker logs that can grow very large
- Remove temporary files and system caches
- Clean APT packages and old kernels
- Monitor disk space before and after cleanup
```

### 2. Dedicated Cleanup Script (`disk_cleanup.sh`)

A comprehensive cleanup script that can be run manually or automated:

```bash
# Manual cleanup
./disk_cleanup.sh

# Dry run to see what would be cleaned
./disk_cleanup.sh --dry-run

# Force cleanup without prompts
./disk_cleanup.sh --force
```

#### Features:
- **Docker cleanup**: Removes all unused containers, images, volumes, networks
- **System cleanup**: Cleans logs, temporary files, caches
- **Application cleanup**: Removes Python bytecode, old logs
- **Package cleanup**: Removes unnecessary packages and kernels
- **Safety checks**: Dry-run mode and disk space validation

### 3. Disk Monitoring System (`disk_monitor.sh`)

Automated monitoring with configurable thresholds:

```bash
# Check current disk usage
./disk_monitor.sh

# Setup automated monitoring (runs every 30 minutes)
./disk_monitor.sh --setup

# Verbose output with logs
./disk_monitor.sh --verbose
```

#### Features:
- **Threshold-based alerts**: 85% warning, 90% critical
- **Automatic cleanup**: Triggers cleanup when critical
- **Detailed reporting**: Shows largest directories and usage breakdown
- **Logging**: Maintains cleanup and monitoring logs
- **Alerting**: Can be extended for email/Slack notifications

### 4. Optimized Docker Images

#### Multi-stage Dockerfile
- **Builder stage**: Installs build dependencies
- **Production stage**: Only runtime dependencies
- **Size reduction**: ~40-60% smaller final images
- **Security**: Non-root user execution

#### Docker Ignore
- Excludes unnecessary files from build context
- Reduces build time and image size
- Prevents sensitive files from being included

## Usage Guide

### Initial Setup

1. **Make scripts executable**:
```bash
chmod +x disk_cleanup.sh disk_monitor.sh
```

2. **Setup automated monitoring**:
```bash
./disk_monitor.sh --setup
```

3. **Test cleanup (dry run)**:
```bash
./disk_cleanup.sh --dry-run
```

### Regular Maintenance

#### Manual Cleanup
When disk space is low:
```bash
# Check current usage
df -h

# Perform cleanup
./disk_cleanup.sh --force

# Monitor cleanup results
./disk_monitor.sh --verbose
```

#### Scheduled Cleanup
Add to crontab for weekly automated cleanup:
```bash
sudo crontab -e
# Add: 0 2 * * 0 /home/ubuntu/fiko-backend/disk_cleanup.sh --force
```

### Emergency Procedures

#### Critical Disk Space (>95% full)
1. **Immediate cleanup**:
```bash
# Emergency Docker cleanup
docker system prune -af --volumes
docker builder prune -af

# Clear logs
sudo journalctl --vacuum-time=1d
sudo truncate -s 0 /var/log/*.log
```

2. **Run full cleanup**:
```bash
./disk_cleanup.sh --force
```

3. **Identify large files**:
```bash
sudo du -h / 2>/dev/null | sort -hr | head -20
```

## Monitoring and Alerting

### Disk Usage Thresholds
- **Green**: < 85% usage - Normal operation
- **Yellow**: 85-90% usage - Warning alerts
- **Red**: > 90% usage - Critical, auto-cleanup triggered

### Log Files
- **Monitor logs**: `/var/log/disk_monitor.log`
- **Cleanup logs**: Generated during cleanup operations
- **Automatic rotation**: Logs are automatically rotated weekly

### Alert Integration
The monitoring script can be extended to send alerts via:
- Email notifications
- Slack webhooks
- Discord notifications
- SMS alerts
- Push notifications

Example Slack integration:
```bash
# Add to disk_monitor.sh
curl -X POST -H 'Content-type: application/json' \
  --data '{"text":"🚨 Fiko Server: Disk usage critical!"}' \
  "$SLACK_WEBHOOK_URL"
```

## Performance Optimizations

### Docker Build Optimizations
1. **BuildKit enabled**: Faster builds and better caching
2. **Multi-stage builds**: Smaller production images
3. **Layer optimization**: Reduces image size
4. **Build cache management**: Balances speed and space

### System Optimizations
1. **Log rotation**: Automatic cleanup of old logs
2. **Kernel cleanup**: Removes old kernel versions
3. **Package management**: Removes unnecessary packages
4. **Cache management**: Clears various system caches

## Best Practices

### Deployment Best Practices
1. **Always cleanup before deployment**
2. **Monitor disk space during deployment**
3. **Use parallel builds for faster deployment**
4. **Prune build cache periodically**

### Maintenance Best Practices
1. **Run monitoring every 30 minutes**
2. **Perform full cleanup weekly**
3. **Review large directories monthly**
4. **Update cleanup thresholds as needed**

### Security Best Practices
1. **Run containers as non-root users**
2. **Limit log file sizes**
3. **Secure cleanup scripts**
4. **Monitor for unusual disk usage patterns**

## Troubleshooting

### Common Issues

#### "No space left on device"
```bash
# Emergency cleanup
sudo rm -rf /tmp/*
docker system prune -af --volumes
./disk_cleanup.sh --force
```

#### Docker build fails due to space
```bash
# Clean Docker completely
docker system prune -af --volumes
docker builder prune -af

# Restart Docker service
sudo systemctl restart docker
```

#### Large log files
```bash
# Find large log files
sudo find /var/log -name "*.log" -size +100M

# Truncate large logs
sudo truncate -s 0 /var/log/large-file.log

# Setup log rotation
sudo logrotate /etc/logrotate.conf
```

### Diagnostic Commands

```bash
# Check disk usage by directory
sudo du -h --max-depth=1 / 2>/dev/null | sort -hr

# Check Docker space usage
docker system df

# Check largest files
sudo find / -type f -size +100M 2>/dev/null | head -20

# Check inode usage
df -i

# Check mount points
df -h
```

## Metrics and Reporting

### Key Metrics to Monitor
- **Disk usage percentage**
- **Available free space (GB)**
- **Docker space usage**
- **Log file sizes**
- **Build cache size**

### Weekly Reports
Set up automated weekly reports showing:
- Disk usage trends
- Cleanup effectiveness
- Large directory growth
- Docker image inventory

## Future Enhancements

### Planned Improvements
1. **Cloud storage integration** for logs and backups
2. **Advanced alerting** with multiple channels
3. **Predictive analysis** of disk usage trends
4. **Automated scaling** based on usage patterns
5. **Integration with monitoring tools** (Prometheus, Grafana)

### Configuration Options
The scripts support various configuration options:
- Alert thresholds
- Cleanup aggressiveness
- Monitoring frequency
- Log retention periods

## Summary

This comprehensive disk space optimization system provides:

✅ **Automated cleanup** during deployments
✅ **Proactive monitoring** with configurable alerts  
✅ **Emergency procedures** for critical situations
✅ **Optimized Docker images** for reduced space usage
✅ **Detailed logging** and reporting
✅ **Flexible configuration** for different environments

The system is designed to be maintenance-free while providing visibility and control when needed.
