#!/bin/bash

# Fix pgvector migration issue
# This script rolls back and re-applies the AI_model.0003 migration with pgvector extension support

set -e  # Exit on error

echo "🔧 Fixing pgvector migration issue..."
echo ""

# Find the web container ID
WEB_CONTAINER=$(docker ps --filter "name=web" --format "{{.ID}}" | head -n 1)

if [ -z "$WEB_CONTAINER" ]; then
    echo "❌ Error: Could not find web container"
    echo "Please make sure your Docker containers are running: docker compose up -d"
    exit 1
fi

echo "✅ Found web container: $WEB_CONTAINER"
echo ""

# Step 1: Rollback migration 0003
echo "📦 Step 1: Rolling back AI_model migration to 0002..."
docker exec -it $WEB_CONTAINER python manage.py migrate AI_model 0002

if [ $? -ne 0 ]; then
    echo ""
    echo "⚠️  Rollback failed. The migration might not have been applied yet."
    echo "Continuing with regular migration..."
fi

echo ""

# Step 2: Apply all migrations
echo "📦 Step 2: Applying all migrations (including updated 0003)..."
docker exec -it $WEB_CONTAINER python manage.py migrate

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Success! Migrations applied successfully."
    echo ""
    echo "🔍 Verifying pgvector extension..."
    
    # Find the db container
    DB_CONTAINER=$(docker ps --filter "name=db" --format "{{.ID}}" | head -n 1)
    
    if [ -n "$DB_CONTAINER" ]; then
        docker exec -it $DB_CONTAINER psql -U postgres -d FikoDB -c "SELECT extname, extversion FROM pg_extension WHERE extname = 'vector';" 2>/dev/null || true
    fi
    
    echo ""
    echo "✅ pgvector migration fix completed!"
else
    echo ""
    echo "❌ Migration failed. Please check the error message above."
    echo ""
    echo "📚 For manual troubleshooting, see: PGVECTOR_MIGRATION_FIX_V2.md"
    exit 1
fi
