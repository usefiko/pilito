# Migration Error Fix - GitHub Action Deployment

## Problem
The GitHub Action deployment was failing with this error:
```
django.db.utils.ProgrammingError: column "email_confirmed" of relation "accounts_user" already exists
```

This occurred because migration `0013_user_email_confirmed_user_invite_code_and_more` was trying to add columns that already exist in the production database.

## Root Cause
The columns (`email_confirmed`, `invite_code`, `referred_by`, `wallet_balance`) were likely added manually to the production database without running migrations, or the migration was partially applied.

## Solutions

### Solution 1: Fix the Migration (RECOMMENDED)
I've already updated the migration file to be safe. You need to push this change to GitHub:

1. **Grant push access to the repository** (or push manually):
   ```bash
   git push origin main
   ```

2. **The GitHub Action will automatically run** and deploy with the fixed migration.

### Solution 2: Quick Fix on Server (IMMEDIATE)
If you need to fix the server immediately without waiting for GitHub access:

1. Run the fix script:
   ```bash
   ./fix_migration_on_server.sh
   ```

   This will mark migration 0013 as "fake applied" (since the columns already exist).

2. Then manually deploy:
   ```bash
   ./deploy_to_server.sh
   ```

### Solution 3: Manual Fix via SSH
If you prefer to do it manually:

```bash
ssh root@185.164.72.165

cd /root/pilito

# Check current migration status
docker exec django_app python manage.py showmigrations accounts

# Mark migration 0013 as fake (since columns already exist)
docker exec django_app python manage.py migrate accounts 0013 --fake

# Verify it's marked as applied
docker exec django_app python manage.py showmigrations accounts

# Now restart the deployment
docker-compose restart web celery_worker celery_beat celery_ai
```

## What I Changed

### Modified: `src/accounts/migrations/0013_user_email_confirmed_user_invite_code_and_more.py`

**Before:** Used Django's `AddField` operations which fail if columns exist.

**After:** 
- Uses `RunPython` migrations with SQL checks
- Checks if each column exists before adding it
- Skips adding columns that already exist
- Prevents "column already exists" errors
- Works on both fresh databases and production

The new migration:
1. ✅ Checks if `email_confirmed` column exists before adding
2. ✅ Checks if `invite_code` column exists before adding
3. ✅ Checks if `wallet_balance` column exists before adding
4. ✅ Checks if `referred_by_id` column exists before adding
5. ✅ Safely alters `business_type` and `phone_number` fields
6. ✅ Creates `EmailConfirmationToken` and `OTPToken` tables if they don't exist

## Testing

To test the migration locally:
```bash
cd /Users/nima/Projects/pilito
python src/manage.py migrate accounts --fake-initial
python src/manage.py migrate accounts
```

## GitHub Action Status

Once you push the changes, the GitHub Action will:
1. ✅ Run tests
2. ✅ Deploy to production
3. ✅ Run the safe migration (which will skip existing columns)
4. ✅ Restart services

## Monitoring

After deployment, check:
```bash
# SSH to server
ssh root@185.164.72.165

# Check migration status
docker exec django_app python manage.py showmigrations accounts

# Check container logs
docker logs django_app --tail 100

# Check all services are running
docker-compose ps
```

## Prevention

To prevent this issue in the future:
1. Always run migrations through Django's management commands
2. Never manually add columns to production databases
3. Use `--fake` flag only when you're certain the schema matches
4. Test migrations on a staging environment first

## Files Created/Modified

1. ✅ Modified: `src/accounts/migrations/0013_user_email_confirmed_user_invite_code_and_more.py`
2. ✅ Created: `fix_migration_on_server.sh` (quick fix script)
3. ✅ Created: `MIGRATION_FIX_README.md` (this file)

## Next Steps

Choose one of the solutions above and execute it. I recommend:
1. **Immediate fix**: Run `./fix_migration_on_server.sh`
2. **Long-term fix**: Push the updated migration to GitHub (need repository access)

