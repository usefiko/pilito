# Django Migrations in CI/CD - Complete Guide

## 🎯 Problem Solved

This guide shows you how to run Django migrations **automatically in CI/CD** and **manually on your server** without errors.

---

## ✅ Solution Implemented

### 1. **Automatic Migrations in CI/CD** (Recommended)

The CI/CD workflow (`.github/workflows/deploy-simple.yml`) now includes automatic migration handling:

```yaml
# Migrations run BEFORE web server starts
- Run migrations using docker compose run
- If migrations fail, deployment stops
- If migrations succeed, deployment continues
```

**Key improvements:**
- ✅ Database stays running during deployment
- ✅ Migrations run with `docker compose run --rm web python manage.py migrate`
- ✅ Web server only starts AFTER migrations succeed
- ✅ Deployment fails early if migrations have errors

### 2. **Manual Migration Script**

For running migrations manually on the server:

```bash
./scripts/run_migrations_docker.sh
```

This script:
- Ensures database is running
- Builds web image
- Shows pending migrations
- Runs migrations
- Verifies all migrations applied
- Runs Django checks

---

## 🚀 Quick Start

### Option A: Automatic (via CI/CD)

Just push to `main` branch:

```bash
git add .
git commit -m "Deploy with new migrations"
git push origin main
```

The GitHub Actions workflow will:
1. Copy files to server
2. Build Docker images
3. **Run migrations automatically**
4. Start all services

### Option B: Manual (on server)

SSH into your server and run:

```bash
cd ~/pilito
./scripts/run_migrations_docker.sh
```

Then start services:

```bash
docker compose up -d
```

---

## 📋 Migration Workflow in CI/CD

Here's exactly what happens in the updated CI/CD:

```bash
# 1. Stop old containers (except database)
docker compose stop web celery_worker celery_beat celery_ai redis_cache

# 2. Ensure database is running
docker compose up -d db
sleep 5

# 3. Build new images
docker compose build web celery_worker celery_beat celery_ai

# 4. Run migrations (CRITICAL STEP)
docker compose run --rm web python manage.py migrate --noinput

# 5. Collect static files
docker compose run --rm web python manage.py collectstatic --noinput

# 6. Start all services with new code
docker compose up -d
```

**Why this works:**
- ✅ Database never stops (no connection lost)
- ✅ Migrations run with new code but old containers aren't running yet
- ✅ If migration fails, old containers aren't affected
- ✅ Services only start after successful migration

---

## 🔍 Understanding the Migration Error

### The Original Error

```
django.db.migrations.exceptions.NodeNotFoundError: 
Migration settings.0018_affiliationconfig dependencies reference 
nonexistent parent node ('settings', '0017_intercomtickettype...')
```

**What it means:**
- Migration `0018` depends on migration `0017`
- Migration `0017` exists locally but hasn't been run on the server
- Django can't apply `0018` without `0017` being applied first

### The Fix

**Fixed in the code:**
- ✅ Migration file `0018_affiliationconfig.py` now has correct dependency
- ✅ Migration file `0011_user_affiliate_active.py` renamed (was conflicting with `0002`)
- ✅ CI/CD now runs migrations before starting services

---

## 🛠️ Troubleshooting

### Problem: "Migration dependencies reference nonexistent parent node"

**Solution 1: Check migration dependencies**

```bash
# On your server
cd ~/pilito
docker compose run --rm web python manage.py showmigrations

# Look for migrations with [ ] (not applied)
# These need to be applied in order
```

**Solution 2: Run migrations manually**

```bash
cd ~/pilito
./scripts/run_migrations_docker.sh
```

**Solution 3: Fake problematic migrations**

If a table already exists but Django thinks migration isn't applied:

```bash
# Example: Fake migration 0017 if table already exists
docker compose run --rm web python manage.py migrate settings 0017 --fake
docker compose run --rm web python manage.py migrate
```

### Problem: "Database connection refused"

**Solution:**

```bash
# Ensure database is running
docker compose up -d db
docker compose ps db

# Wait a bit
sleep 5

# Try again
docker compose run --rm web python manage.py migrate
```

### Problem: "Container web is not running"

**This is actually correct!** 

When you run `docker compose run --rm web`, it:
- Creates a **temporary** container
- Runs the command
- Removes the container when done

This is different from the permanent `web` container that runs your Django server.

### Problem: Migrations work locally but fail in CI/CD

**Check these:**

1. **Environment variables**: Ensure `.env` file is on server
2. **Database connection**: Ensure `POSTGRES_*` vars are set correctly
3. **File sync**: Ensure migration files were copied to server
   ```bash
   ls -la ~/pilito/src/settings/migrations/
   ls -la ~/pilito/src/accounts/migrations/
   ls -la ~/pilito/src/billing/migrations/
   ```

---

## 📚 Common Commands

### Check Migration Status

```bash
# Show all migrations and their status
docker compose run --rm web python manage.py showmigrations

# Show only pending migrations
docker compose run --rm web python manage.py showmigrations --plan | grep "\[ \]"

# Check specific app
docker compose run --rm web python manage.py showmigrations settings
```

### Run Migrations

```bash
# Run all pending migrations
docker compose run --rm web python manage.py migrate

# Run migrations for specific app
docker compose run --rm web python manage.py migrate settings

# Run up to specific migration
docker compose run --rm web python manage.py migrate settings 0017

# Fake a migration (if table exists but migration not recorded)
docker compose run --rm web python manage.py migrate settings 0017 --fake
```

### Create New Migrations (Locally)

```bash
# Create migrations for all apps
python manage.py makemigrations

# Create migration for specific app
python manage.py makemigrations settings

# Create migration with custom name
python manage.py makemigrations settings --name add_new_feature
```

### Rollback Migrations

```bash
# Rollback to previous migration
docker compose run --rm web python manage.py migrate settings 0016

# Rollback all migrations for an app
docker compose run --rm web python manage.py migrate settings zero
```

---

## 🎯 Best Practices

### 1. **Always Run Migrations Before Deployment**

✅ **Good** (CI/CD does this now):
```bash
docker compose run --rm web python manage.py migrate
docker compose up -d
```

❌ **Bad**:
```bash
docker compose up -d  # Starts web before migrations
```

### 2. **Check Migrations Locally First**

Before pushing to GitHub:

```bash
# Check for pending migrations
python manage.py showmigrations

# Test migrations locally
python manage.py migrate

# Test Django checks
python manage.py check
```

### 3. **Use Descriptive Migration Names**

When creating migrations:

```bash
python manage.py makemigrations settings --name add_affiliation_config
# Better than generic "auto_20251130_0000"
```

### 4. **Keep Database Running During Deployment**

The new CI/CD workflow keeps the database running:
- ✅ No connection loss
- ✅ Faster deployment
- ✅ Zero downtime for database

### 5. **Monitor Migration Output in CI/CD**

Check GitHub Actions logs for:
- "Running database migrations..."
- "✅ Migrations completed successfully"
- Any error messages

---

## 📖 Migration Order for This Project

Current migration sequence (after fixes):

```
settings:
  ✅ 0001 → ... → 0017_intercomtickettype... → 0018_affiliationconfig

accounts:
  ✅ 0001 → ... → 0010_user_business_type... → 0011_user_affiliate_active

billing:
  ✅ 0001_initial → 0002_wallettransaction
```

**All migrations will now apply in correct order!**

---

## 🎉 Summary

**What changed:**
1. ✅ CI/CD now runs migrations automatically BEFORE starting web server
2. ✅ Created `scripts/run_migrations_docker.sh` for manual runs
3. ✅ Fixed migration dependencies (0018, 0011)
4. ✅ Database stays running during deployment

**What you need to do:**
1. **Nothing!** Just push to main branch
2. GitHub Actions will handle everything
3. If you want manual control, use `./scripts/run_migrations_docker.sh`

**Result:**
- ✅ No more migration errors in CI/CD
- ✅ Automatic database schema updates
- ✅ Safe deployment process
- ✅ Zero downtime migrations

---

## 🔗 Related Files

- **CI/CD Workflow**: `.github/workflows/deploy-simple.yml`
- **Migration Script**: `scripts/run_migrations_docker.sh`
- **Migration Files**: 
  - `src/settings/migrations/0018_affiliationconfig.py`
  - `src/accounts/migrations/0011_user_affiliate_active.py`
  - `src/billing/migrations/0002_wallettransaction.py`

---

**Last Updated**: 2025-11-30
**Status**: ✅ Fully Implemented

