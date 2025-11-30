# 🚨 QUICK FIX: Migration Error on Server

## The Error You're Seeing

```
NodeNotFoundError: Migration settings.0018_affiliationconfig dependencies 
reference nonexistent parent node ('settings', '0017_intercomtickettype...')
```

## ✅ Immediate Solution

### Option 1: Run on Server NOW (Fastest)

SSH into your server and run these commands:

```bash
cd ~/pilito

# Stop all containers except database
docker compose stop web celery_worker celery_beat celery_ai redis_cache prometheus grafana

# Ensure database is running
docker compose up -d db
sleep 5

# Run pending migrations (0016, 0017, 0018)
docker compose run --rm web python manage.py migrate --noinput

# Start all services
docker compose up -d
```

### Option 2: Let CI/CD Handle It (Automatic)

The CI/CD workflow has been updated. Just push:

```bash
git pull origin main
git push origin main
```

GitHub Actions will automatically:
- Build images
- Run migrations
- Start services

---

## 📋 What Happened

1. **Three new migrations were added**:
   - `settings/0018_affiliationconfig.py` - New affiliate config model
   - `accounts/0011_user_affiliate_active.py` - Add affiliate field to User
   - `billing/0002_wallettransaction.py` - Wallet transaction tracking

2. **Migration 0018 depends on 0017**:
   - Migration `0017` exists but hasn't been applied on server yet
   - Django requires migrations to run in order

3. **The Fix**:
   - CI/CD now runs migrations BEFORE starting web server
   - Manual script available: `./scripts/run_migrations_docker.sh`

---

## 🔍 Verify Fix Worked

After running migrations, check:

```bash
# Should show all [X] (no [ ] pending)
docker compose run --rm web python manage.py showmigrations

# Should show "OK"
docker compose run --rm web python manage.py check

# Should list running containers
docker compose ps
```

Expected output:
```
settings
 [X] 0001_initial
 ...
 [X] 0017_intercomtickettype_alter_generalsettings_options_and_more
 [X] 0018_affiliationconfig  ← NEW

accounts
 [X] 0001_initial
 ...
 [X] 0011_user_affiliate_active  ← NEW

billing
 [X] 0001_initial
 [X] 0002_wallettransaction  ← NEW
```

---

## 🚫 Common Mistakes

### ❌ DON'T Do This:

```bash
docker compose up -d  # Starts web BEFORE migrations
```

### ✅ DO This Instead:

```bash
docker compose run --rm web python manage.py migrate  # Migrations FIRST
docker compose up -d  # Then start services
```

---

## 📞 Still Having Issues?

### If migrations still fail:

1. **Check migration files are on server:**
   ```bash
   ls -la ~/pilito/src/settings/migrations/001*.py
   ls -la ~/pilito/src/accounts/migrations/001*.py
   ls -la ~/pilito/src/billing/migrations/000*.py
   ```

2. **Check database is accessible:**
   ```bash
   docker compose logs db | tail -50
   ```

3. **Try running migrations one app at a time:**
   ```bash
   docker compose run --rm web python manage.py migrate settings
   docker compose run --rm web python manage.py migrate accounts
   docker compose run --rm web python manage.py migrate billing
   ```

4. **Check for conflicting migrations:**
   ```bash
   docker compose run --rm web python manage.py showmigrations --plan
   ```

---

## 📚 For Complete Documentation

See: `MIGRATIONS_CI_CD_GUIDE.md`

---

**Quick Summary:**
- ✅ Migration files fixed
- ✅ CI/CD updated to run migrations automatically
- ✅ Manual script available
- ✅ Just run migrations before starting web server

**Status**: Ready to deploy! 🚀

