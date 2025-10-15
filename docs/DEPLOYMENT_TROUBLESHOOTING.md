# Deployment Troubleshooting Guide

## Common Django Import Error Fix

### Problem
```
ImportError: Couldn't import Django. Are you sure it's installed and available on your PYTHONPATH environment variable?
ModuleNotFoundError: No module named 'django'
```

### Root Cause
This error typically occurs when:
1. Docker multi-stage builds don't properly copy Python packages
2. Virtual environment paths are incorrect in Docker
3. Requirements installation fails silently
4. User permissions prevent package access

### Solution Applied

#### 1. Simplified Dockerfile
**Before (Multi-stage):**
```dockerfile
FROM python:3.12-slim as builder
# Complex multi-stage build with --user installs
```

**After (Single-stage):**
```dockerfile
FROM python:3.12-slim
# Direct package installation in system Python
```

#### 2. Package Installation Fix
- Removed `--user` flag that was causing path issues
- Ensured packages install to system Python location
- Removed user switching that complicated package access

#### 3. GitHub Actions Debugging
Added comprehensive error reporting:
- Container logs (50 lines)
- Environment variables
- Installed packages list
- Better health check reporting

### Verification Steps

#### Local Testing
```bash
# Test Docker build locally
./test_docker_build.sh

# Manual verification
docker-compose build
docker-compose run --rm web python -c "import django; print('Django OK')"
```

#### Deployment Monitoring
The GitHub Actions now provides detailed debugging:
- Build logs
- Container startup logs
- Package installation verification
- Environment variable inspection

### Quick Fixes for Similar Issues

#### 1. Requirements File Issues
```bash
# Verify requirements file exists and is readable
cat src/requirements/base.txt | head -5

# Check for hidden characters
od -c src/requirements/base.txt | head -3
```

#### 2. Docker Build Context Issues
```bash
# Clean Docker build
docker system prune -af
docker-compose build --no-cache --pull
```

#### 3. Package Installation Verification
```bash
# Check if packages are installed correctly
docker-compose run --rm web pip list
docker-compose run --rm web python -c "import django, rest_framework, channels"
```

### Prevention

#### 1. Keep Dockerfile Simple
- Avoid complex multi-stage builds unless necessary
- Use system Python installation for reliability
- Minimize user permission changes

#### 2. Requirements Management
- Pin exact package versions
- Test requirements file locally before deployment
- Use consistent Python version across environments

#### 3. Deployment Monitoring
- Enhanced error reporting in CI/CD
- Comprehensive health checks
- Container log collection

### Emergency Recovery

If deployment fails:

1. **Rollback to last working version:**
```bash
git revert HEAD
git push origin main
```

2. **Quick Docker fixes:**
```bash
# SSH to server and manually fix
ssh user@server
cd /path/to/app
docker-compose down
docker system prune -af
docker-compose build --no-cache
docker-compose up -d
```

3. **Debug mode deployment:**
```bash
# Temporarily disable health checks
# Add debug output to entrypoint.sh
# Use development settings for more verbose errors
```

## Files Modified for Fix

- `Dockerfile` - Simplified to single-stage build
- `.github/workflows/deploy.yml` - Enhanced debugging
- `test_docker_build.sh` - Local testing script
- This troubleshooting guide

## Prevention for Future

1. Always test Docker builds locally before deployment
2. Use the provided test script: `./test_docker_build.sh`
3. Monitor deployment logs for early warning signs
4. Keep Docker configuration as simple as possible
5. Pin all dependency versions in requirements files
