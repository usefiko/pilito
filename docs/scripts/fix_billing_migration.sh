#!/bin/bash

# Fix billing migration issue - column already exists
# This script fakes the problematic migration and continues with the rest

set -e  # Exit on error

echo "🔧 Fixing billing migration issue (column already exists)..."
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

# Fake the problematic migration since columns already exist
echo "📦 Faking billing.0008 migration (columns already exist)..."
docker exec -it $WEB_CONTAINER python manage.py migrate billing 0008 --fake

if [ $? -eq 0 ]; then
    echo "✅ Successfully faked billing.0008 migration"
    echo ""
    
    # Now run all remaining migrations
    echo "📦 Applying remaining migrations..."
    docker exec -it $WEB_CONTAINER python manage.py migrate
    
    if [ $? -eq 0 ]; then
        echo ""
        echo "✅ All migrations completed successfully!"
        echo ""
        echo "🎉 Your database is now up to date!"
    else
        echo ""
        echo "❌ Some migrations failed. Check error messages above."
        exit 1
    fi
else
    echo ""
    echo "❌ Failed to fake migration. Please check the error message above."
    exit 1
fi
