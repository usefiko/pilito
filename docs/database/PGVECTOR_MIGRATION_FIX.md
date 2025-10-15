# pgvector Migration Fix Guide

## Problem
Migration failed with error: `type "vector" does not exist`

This happens because the pgvector extension needs to be created in PostgreSQL before running migrations that use vector fields.

## Solution Applied

### 1. Created Migration for pgvector Extension
Created a new migration file: `src/AI_model/migrations/0002_1_enable_pgvector.py`

This migration creates the pgvector extension in PostgreSQL before other migrations try to use it.

### 2. Updated Dependencies
Updated `0003_intentrouting_intentkeyword_sessionmemory_and_more.py` to depend on the new pgvector migration.

## How to Apply the Fix

### Step 1: Run Migrations
The migrations should now work properly in the correct order:

```bash
docker compose exec web python manage.py migrate
```

### Expected Output:
```
Operations to perform:
  Apply all migrations: ...
Running migrations:
  Applying message.0009_message_input_tokens_message_output_tokens_and_more... OK
  Applying AI_model.0002_1_enable_pgvector... OK
  Applying AI_model.0003_intentrouting_intentkeyword_sessionmemory_and_more... OK
  ... (other migrations)
```

## If Migration Still Fails

If you still get errors, the PostgreSQL database might need the pgvector extension installed at the system level first.

### Option 1: Check if pgvector is available in PostgreSQL
```bash
# Enter PostgreSQL container
docker compose exec db psql -U postgres -d your_database_name

# Check if vector extension exists
SELECT * FROM pg_available_extensions WHERE name = 'vector';

# If it shows up, you can exit
\q
```

### Option 2: If pgvector is not available (rare case)
Your PostgreSQL image might not have pgvector compiled in. You would need to:

1. Use a PostgreSQL image with pgvector pre-installed:
   ```yaml
   # In docker-compose.yml
   db:
     image: pgvector/pgvector:pg15
     # or
     image: ankane/pgvector:latest
   ```

2. Or install pgvector in your current PostgreSQL container (not recommended for production)

### Option 3: Manual Extension Creation (if needed)
```bash
# Enter PostgreSQL
docker compose exec db psql -U postgres -d your_database_name

# Create extension manually
CREATE EXTENSION IF NOT EXISTS vector;

# Verify
SELECT * FROM pg_extension WHERE extname = 'vector';
# Should return 1 row

# Exit
\q

# Then run migrations
docker compose exec web python manage.py migrate
```

## Verification

After successful migration, verify the tables were created:

```bash
docker compose exec db psql -U postgres -d your_database_name

# List tables
\dt

# Check tenant_knowledge table structure (should have vector column)
\d tenant_knowledge

# Exit
\q
```

You should see `tldr_embedding` column with type `vector(1536)` or similar.

## Files Modified
1. `src/AI_model/migrations/0002_1_enable_pgvector.py` - NEW: Creates pgvector extension
2. `src/AI_model/migrations/0003_intentrouting_intentkeyword_sessionmemory_and_more.py` - Updated dependencies

## Next Steps
Once migrations are successful, you're ready to use the RAG system with vector embeddings!

