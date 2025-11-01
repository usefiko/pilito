# GitHub Actions Fix - Docker Compose V2

## Problem

GitHub Actions workflows were failing with:
```
docker-compose: command not found
Error: Process completed with exit code 127
```

## Root Cause

GitHub Actions runners use **Docker Compose V2** which uses the command:
```bash
docker compose  # V2 (new, without hyphen)
```

But the workflows were written for Docker Compose V1:
```bash
docker-compose  # V1 (old, with hyphen)
```

## Solution

Updated all workflow files to use V2 syntax:

### Files Fixed:
- ✅ `.github/workflows/deploy-production.yml`
- ✅ `.github/workflows/test-pr.yml`
- ✅ `.github/workflows/manual-deploy.yml`

### Changes:
```yaml
# Before (V1):
run: docker-compose build
run: docker-compose up -d
run: docker-compose down -v

# After (V2):
run: docker compose build
run: docker compose up -d
run: docker compose down -v
```

## Status

✅ **Fixed!** All workflows now use Docker Compose V2 syntax.

## Testing

To verify the fix works, push this change to GitHub:

```bash
git add .
git commit -m "Fix: Update workflows to use Docker Compose V2"
git push origin main
```

Then check the GitHub Actions tab to see tests pass.

---

## Note for Server Deployments

Your production server can use either:
- `docker-compose` (V1) - older servers
- `docker compose` (V2) - newer installations

The workflow will use V2, but your server deployment scripts (`swarm_deploy.sh`, etc.) will detect and use whichever is available.

---

**Status**: ✅ Ready to push and test!

