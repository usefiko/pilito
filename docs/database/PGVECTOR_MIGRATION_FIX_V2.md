# pgvector Migration Fix Guide v2

## Problem
Migration `0003` was already applied to the database, but it needs the pgvector extension to be created first.

Error message:
```
django.db.migrations.exceptions.InconsistentMigrationHistory: Migration AI_model.0003_intentrouting_intentkeyword_sessionmemory_and_more is applied before its dependency AI_model.0002_1_enable_pgvector on database 'default'.
```

## Solution Applied

Updated the `0003` migration to include pgvector extension creation as its first operation. This avoids creating a separate migration that causes ordering conflicts.

## How to Fix

Since the migration was already partially applied, we need to roll it back and re-apply it.

### Step 1: Rollback the 0003 Migration

```bash
docker exec -it <container_id> python manage.py migrate AI_model 0002
```

This will unapply migration 0003.

### Step 2: Re-apply All Migrations

```bash
docker exec -it <container_id> python manage.py migrate
```

This will apply the updated 0003 migration with pgvector extension creation included.

### Expected Output:
```
Operations to perform:
  Apply all migrations: ...
Running migrations:
  Applying AI_model.0003_intentrouting_intentkeyword_sessionmemory_and_more... OK
  ... (other migrations)
```

## Alternative: If Tables Already Exist

If the tables were created but failed due to vector type, you might need to:

### Option A: Drop and Recreate (Safe if no data)

```bash
# Enter PostgreSQL
docker exec -it <db_container_id> psql -U postgres -d FikoDB

# Drop the tables (if they exist)
DROP TABLE IF EXISTS tenant_knowledge CASCADE;
DROP TABLE IF EXISTS session_memory CASCADE;
DROP TABLE IF EXISTS intent_keywords CASCADE;
DROP TABLE IF EXISTS intent_routing CASCADE;

# Exit
\q

# Now rollback and re-migrate
docker exec -it <container_id> python manage.py migrate AI_model 0002
docker exec -it <container_id> python manage.py migrate
```

### Option B: Fake the Migration (If Extension Exists)

If pgvector extension is already created manually:

```bash
# Check if extension exists
docker exec -it <db_container_id> psql -U postgres -d FikoDB -c "SELECT * FROM pg_extension WHERE extname = 'vector';"

# If it exists, you can fake the migration
docker exec -it <container_id> python manage.py migrate AI_model 0002
docker exec -it <container_id> python manage.py migrate --fake AI_model 0003

# Then run migrations normally
docker exec -it <container_id> python manage.py migrate
```

## Quick One-Liner Fix

If you want to just fix it quickly (assuming no important data in the new tables):

```bash
# On production server
docker exec -it <container_id> bash -c "
python manage.py migrate AI_model 0002 &&
python manage.py migrate
"
```

## Verification

After successful migration:

```bash
# Check tables exist
docker exec -it <db_container_id> psql -U postgres -d FikoDB -c "\dt"

# Check vector column
docker exec -it <db_container_id> psql -U postgres -d FikoDB -c "\d tenant_knowledge"

# Should see: tldr_embedding | vector(1536) | 
```

## If You See Collation Warning

The warning about collation version mismatch is separate and can be fixed with:

```bash
docker exec -it <db_container_id> psql -U postgres -d FikoDB

ALTER DATABASE "FikoDB" REFRESH COLLATION VERSION;

\q
```

## Files Modified
- `src/AI_model/migrations/0003_intentrouting_intentkeyword_sessionmemory_and_more.py` - Added pgvector extension creation as first operation

## Summary
The fix ensures pgvector extension is created before any tables that use vector fields. Since migration 0003 was already applied, we need to rollback and re-apply it with the updated version.
