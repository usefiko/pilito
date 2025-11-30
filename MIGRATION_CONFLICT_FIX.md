# 🚨 URGENT FIX: Conflicting Migrations

## The Error

```
CommandError: Conflicting migrations detected; multiple leaf nodes in the 
migration graph: (0002_user_affiliate_active, 0011_user_affiliate_active in accounts).
To fix them run 'python manage.py makemigrations --merge'
```

## 🎯 Root Cause

When we renamed the migration from `0002_user_affiliate_active.py` to `0011_user_affiliate_active.py` locally, the old `0002` file still exists on the server. Django sees both files and thinks they're conflicting migrations.

---

## ✅ IMMEDIATE FIX (Run on Server NOW)

SSH into your server and run:

```bash
ssh root@46.249.98.162
cd ~/pilito

# Remove the old duplicate migration file
rm -f src/accounts/migrations/0002_user_affiliate_active.py
rm -f src/accounts/migrations/__pycache__/0002_user_affiliate_active.cpython-*.pyc

# Now run migrations
docker compose run --rm web python manage.py migrate

# Start services
docker compose up -d
```

**OR use the fix script:**

```bash
ssh root@46.249.98.162
cd ~/pilito
./scripts/fix_migration_conflict.sh
docker compose up -d
```

---

## 🔧 What the Fix Does

1. **Removes the old file**: Deletes `0002_user_affiliate_active.py` from the server
2. **Cleans up cache**: Removes compiled `.pyc` files
3. **Keeps the new file**: `0011_user_affiliate_active.py` stays (correct one)
4. **Resolves conflict**: Django now only sees one migration for that change

---

## 🚀 Long-Term Solution (Already Implemented)

The CI/CD workflow has been updated to **automatically clean up old migration files** on every deployment:

```yaml
# Clean up conflicting migration files
echo "🔧 Cleaning up old migration files..."
rm -f src/accounts/migrations/0002_user_affiliate_active.py || true
rm -f src/accounts/migrations/__pycache__/0002_user_affiliate_active.cpython-*.pyc || true
echo "✅ Old migration files cleaned"
```

This runs **before** migrations, so you won't see this error again!

---

## 📋 Migration Timeline

### What Happened:

1. **Created locally**: `0002_user_affiliate_active.py` (wrong - conflicts with existing 0002)
2. **Renamed locally**: `0002` → `0011_user_affiliate_active.py` (correct)
3. **Pushed to GitHub**: Only `0011` in repo now
4. **Server has both**: Old `0002` still on server + new `0011` from push
5. **Django confused**: Sees two migrations trying to add same field

### What We Fixed:

1. ✅ Deleted old `0002` file locally
2. ✅ Only `0011` exists in repo now
3. ✅ CI/CD now removes `0002` on server before migrations
4. ✅ Future deployments will work automatically

---

## 🔍 Why NOT Use `makemigrations --merge`?

Django suggests running `python manage.py makemigrations --merge`, but that's **NOT the right solution** here because:

1. ❌ This isn't a real conflict - it's a duplicate file
2. ❌ Merging would create a new migration file unnecessarily
3. ❌ The real issue is file cleanup, not migration merging
4. ✅ Just deleting the old file is simpler and correct

---

## 📊 Verify Fix Worked

After running the fix, check:

```bash
# List migration files (should only see 0011, not 0002)
ls -la src/accounts/migrations/*.py | grep affiliate

# Expected output:
# 0011_user_affiliate_active.py  ← Only this one

# Run migrations (should work now)
docker compose run --rm web python manage.py migrate

# Check migration status
docker compose run --rm web python manage.py showmigrations accounts
```

Expected output:
```
accounts
 [X] 0001_initial
 [X] 0002_alter_user_age          ← Different migration
 [X] 0003_alter_user_phone_number
 ...
 [X] 0010_user_business_type_user_email_confirmed_and_more
 [X] 0011_user_affiliate_active   ← NEW (not 0002!)
```

---

## 🎉 Summary

**Problem**: Old `0002_user_affiliate_active.py` file on server conflicting with new `0011_user_affiliate_active.py`

**Solution**: Delete the old `0002` file from the server

**Prevention**: CI/CD now automatically cleans up old migration files

**Status**: ✅ Fixed! Next deployment will work automatically

---

## 🆘 Still Having Issues?

If you still see the error after running the fix:

1. **Check files on server**:
   ```bash
   ls -la ~/pilito/src/accounts/migrations/*affiliate*.py
   ```
   
   Should only show `0011_user_affiliate_active.py`

2. **Clear Python cache**:
   ```bash
   find ~/pilito/src -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
   ```

3. **Restart Docker containers**:
   ```bash
   docker compose down
   docker compose up -d
   ```

4. **Check migration graph**:
   ```bash
   docker compose run --rm web python manage.py showmigrations accounts --plan
   ```

---

**Quick Command Summary:**

```bash
# SSH to server
ssh root@46.249.98.162

# Fix conflict
cd ~/pilito
rm -f src/accounts/migrations/0002_user_affiliate_active.py
rm -f src/accounts/migrations/__pycache__/0002_user_affiliate_active.cpython-*.pyc

# Run migrations
docker compose run --rm web python manage.py migrate

# Start services
docker compose up -d
```

Done! 🚀

