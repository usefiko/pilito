# 🐳 Docker Container Proliferation Fix

## Problem

You're seeing many temporary `pilito-web-run-*` containers because you're using `docker compose run` which creates a **new temporary container** for each command.

## Why This Happens

```bash
# This creates a NEW container each time ❌
docker compose run web python manage.py migrate
docker compose run web python manage.py makemigrations
docker compose run web python manage.py createsuperuser
```

Each command:
1. Creates a new container (e.g., `pilito-web-run-f2036b6a4dfe`)
2. Runs the command
3. Exits but **leaves the container** (not removed automatically)

Result: **10+ stopped containers** accumulating over time! 😰

## Solutions

### ✅ Solution 1: Use `docker compose exec` (RECOMMENDED)

Execute commands in the **existing running container**:

```bash
# Migrate database
docker compose exec web python manage.py migrate

# Make migrations
docker compose exec web python manage.py makemigrations

# Create superuser
docker compose exec web python manage.py createsuperuser

# Collect static files
docker compose exec web python manage.py collectstatic --noinput

# Run Django shell
docker compose exec web python manage.py shell

# Run tests
docker compose exec web python manage.py test
```

**Benefits:**
- ✅ No new containers created
- ✅ Faster (no startup time)
- ✅ Uses existing environment
- ✅ No cleanup needed

### ✅ Solution 2: Use the Helper Script

We created `manage.sh` to simplify this:

```bash
# Usage: ./manage.sh <command>
./manage.sh migrate
./manage.sh makemigrations
./manage.sh createsuperuser
./manage.sh shell
```

This script automatically:
- Checks if services are running
- Uses `docker compose exec` instead of `run`
- No temporary containers created

### ✅ Solution 3: If You Must Use `run`, Add `--rm`

For one-off tasks, use `--rm` flag to auto-remove:

```bash
docker compose run --rm web python manage.py migrate
```

## Cleanup Existing Containers

### Quick Cleanup

Remove all stopped containers:

```bash
# Remove all stopped containers (safe)
docker container prune -f
```

### Targeted Cleanup

Remove only `pilito-web-run` containers:

```bash
# List them first
docker ps -a | grep "pilito-web-run"

# Remove them
docker ps -a | grep "pilito-web-run" | awk '{print $1}' | xargs docker rm

# Or using Docker Desktop: 
# Select multiple containers → Click trash icon
```

### Automated Cleanup Script

Create `cleanup_containers.sh`:

```bash
#!/bin/bash
echo "🧹 Cleaning up temporary pilito containers..."

# Count before
BEFORE=$(docker ps -a | grep "pilito-web-run" | wc -l)
echo "Found $BEFORE temporary containers"

# Remove them
docker ps -a | grep "pilito-web-run" | awk '{print $1}' | xargs docker rm 2>/dev/null

# Count after
AFTER=$(docker ps -a | grep "pilito-web-run" | wc -l)
echo "✅ Cleaned up $(($BEFORE - $AFTER)) containers"
```

## Makefile Integration

Add these to your `Makefile`:

```makefile
# Django management commands (no temporary containers)
migrate:
	docker compose exec web python manage.py migrate

makemigrations:
	docker compose exec web python manage.py makemigrations

shell:
	docker compose exec web python manage.py shell

createsuperuser:
	docker compose exec web python manage.py createsuperuser

collectstatic:
	docker compose exec web python manage.py collectstatic --noinput

# Cleanup
cleanup-containers:
	@echo "🧹 Cleaning up temporary containers..."
	@docker ps -a | grep "pilito-web-run" | awk '{print $$1}' | xargs docker rm 2>/dev/null || echo "No containers to clean"

# Remove all stopped containers
prune:
	docker container prune -f
	docker image prune -f
	docker volume prune -f
```

Then use:

```bash
make migrate
make makemigrations
make shell
make cleanup-containers
```

## Understanding the Difference

### `docker compose run` vs `docker compose exec`

| Feature | `docker compose run` | `docker compose exec` |
|---------|---------------------|----------------------|
| **Creates new container** | ✅ Yes (temporary) | ❌ No |
| **Requires service running** | ❌ No | ✅ Yes |
| **Cleanup needed** | ✅ Yes (unless `--rm`) | ❌ No |
| **Startup time** | Slower | Faster |
| **Best for** | One-off tasks | Regular commands |

### When to Use Each

**Use `docker compose exec`:** (90% of the time)
- Database migrations
- Making migrations
- Running Django shell
- Creating superuser
- Collecting static files
- Any regular development task

**Use `docker compose run --rm`:** (10% of the time)
- Service not running yet
- Need different environment variables
- Need to override the command completely
- One-off scripts that shouldn't affect running services

## Best Practices

### 1. Default to `exec`

Always use `docker compose exec` for Django management commands:

```bash
# Good ✅
docker compose exec web python manage.py migrate

# Bad ❌ (creates temporary container)
docker compose run web python manage.py migrate
```

### 2. Use `--rm` with `run`

If you must use `run`, always add `--rm`:

```bash
docker compose run --rm web python manage.py migrate
```

### 3. Use Helper Script

Use `./manage.sh` for convenience:

```bash
./manage.sh migrate
./manage.sh shell
```

### 4. Regular Cleanup

Add to your workflow:

```bash
# Weekly cleanup
docker container prune -f
docker image prune -f
```

### 5. Monitor Container Count

```bash
# See all containers
docker ps -a

# Count temporary containers
docker ps -a | grep "pilito-web-run" | wc -l
```

## Quick Reference

```bash
# ✅ RECOMMENDED: Use existing container
docker compose exec web python manage.py <command>

# ✅ ALTERNATIVE: Use helper script
./manage.sh <command>

# ⚠️ IF NEEDED: Run with auto-remove
docker compose run --rm web python manage.py <command>

# 🧹 CLEANUP: Remove temporary containers
docker container prune -f
```

## Preventing Future Issues

### Update `.gitignore`

Ensure your `.gitignore` has:

```gitignore
# Docker
*.log
.dockerignore
```

### Add to Documentation

Update your README with:

```markdown
## Running Django Commands

Use `docker compose exec` to run commands in the existing container:

\`\`\`bash
docker compose exec web python manage.py migrate
docker compose exec web python manage.py makemigrations
\`\`\`

Or use the helper script:

\`\`\`bash
./manage.sh migrate
\`\`\`
```

### Team Communication

Let your team know:
- ✅ Use `docker compose exec` for regular commands
- ❌ Don't use `docker compose run` without `--rm`
- 🧹 Run cleanup weekly

## Summary

**Problem:** 10+ temporary containers from using `docker compose run`

**Solution:**
1. ✅ Use `docker compose exec web python manage.py <command>` 
2. ✅ Use `./manage.sh <command>` helper script
3. ✅ If using `run`, add `--rm` flag
4. 🧹 Cleanup: `docker container prune -f`

**Result:** Clean Docker environment with only necessary containers! 🎉

---

**Created:** November 25, 2025  
**Issue:** Multiple temporary containers from `docker compose run`  
**Fix:** Use `docker compose exec` instead

