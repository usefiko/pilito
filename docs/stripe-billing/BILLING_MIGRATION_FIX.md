# Billing Migration Fix Guide

## Problem
Migration `billing.0008` is trying to add columns that already exist in the database.

Error message:
```
psycopg2.errors.DuplicateColumn: column "queued_full_plan_id" of relation "billing_subscription" already exists
```

## Why This Happens
The columns (`queued_full_plan_id`, `queued_token_plan_id`, `queued_tokens_amount`) already exist in your database, but Django's migration tracker thinks they haven't been added yet. This usually happens when:
- Migrations were applied manually to the database
- Migrations were partially applied
- There was a previous migration conflict

## Solution: Fake the Migration

Since the columns already exist, we tell Django to mark the migration as applied without actually running it.

---

## Quick Fix (Recommended)

### Option 1: Automated Script

```bash
# On your production server
cd /path/to/Fiko-Backend
./fix_billing_migration.sh
```

### Option 2: Manual Commands

```bash
# Step 1: Fake the problematic migration
docker exec -it 4b82d77fb3e5 python manage.py migrate billing 0008 --fake

# Step 2: Apply remaining migrations
docker exec -it 4b82d77fb3e5 python manage.py migrate
```

### Option 3: One-Liner

```bash
docker exec -it 4b82d77fb3e5 sh -c "python manage.py migrate billing 0008 --fake && python manage.py migrate"
```

---

## Expected Output

```
Operations to perform:
  Apply all migrations: ...
Running migrations:
  Applying billing.0008_subscription_queued_full_plan_and_more... FAKED
  ... (other migrations will run normally)
  
✅ All migrations completed successfully!
```

---

## Verification

After successful migration, verify the columns exist:

```bash
# Enter PostgreSQL
docker exec -it <db_container> psql -U postgres -d FikoDB

# Check subscription table structure
\d billing_subscription

# You should see:
# - queued_full_plan_id
# - queued_token_plan_id  
# - queued_tokens_amount

# Exit
\q
```

---

## If You Still Get Errors

If you encounter other migration errors, you can check which migrations are applied:

```bash
docker exec -it 4b82d77fb3e5 python manage.py showmigrations
```

Look for migrations marked with `[ ]` (not applied) vs `[X]` (applied).

### To fake multiple migrations:

```bash
docker exec -it 4b82d77fb3e5 python manage.py migrate <app_name> <migration_number> --fake
```

---

## What is --fake?

The `--fake` flag tells Django:
- Mark this migration as applied in the database
- Don't actually run the SQL operations
- Useful when the database changes already exist

**When to use:**
- ✅ When columns/tables already exist
- ✅ When you manually created database objects
- ✅ When migrating existing databases

**When NOT to use:**
- ❌ For normal migrations
- ❌ When you're not sure if changes exist
- ❌ On new/empty databases

---

## Summary

1. The billing migration is trying to add existing columns
2. Solution: Fake the migration to mark it as applied
3. Then continue with remaining migrations normally

This is a safe operation since the database already has the correct structure!

