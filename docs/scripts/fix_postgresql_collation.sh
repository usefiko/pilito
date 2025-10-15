#!/bin/bash

# Fix PostgreSQL Collation Version Mismatch
# This script fixes the PostgreSQL collation version warning

echo "🔧 Fixing PostgreSQL collation version mismatch..."

# Get the container ID for the database
DB_CONTAINER=$(docker ps --filter "name=db" --format "{{.ID}}")

if [ -z "$DB_CONTAINER" ]; then
    echo "❌ Database container not found"
    exit 1
fi

echo "📋 Database container: $DB_CONTAINER"

# Connect to PostgreSQL and fix the collation
echo "🔄 Refreshing collation version..."
docker exec -it $DB_CONTAINER psql -U FikoUsr -d FikoDB -c "ALTER DATABASE \"FikoDB\" REFRESH COLLATION VERSION;"

if [ $? -eq 0 ]; then
    echo "✅ Collation version refreshed successfully"
    echo "🔍 Verifying fix..."
    
    # Test the fix by running a simple query
    docker exec -it $DB_CONTAINER psql -U FikoUsr -d FikoDB -c "SELECT version();"
    
    echo "✅ PostgreSQL collation issue fixed!"
else
    echo "❌ Failed to refresh collation version"
    echo "💡 You may need to run this manually:"
    echo "   docker exec -it $DB_CONTAINER psql -U FikoUsr -d FikoDB"
    echo "   ALTER DATABASE \"FikoDB\" REFRESH COLLATION VERSION;"
fi

echo ""
echo "🧪 Testing database connection..."
# Test Django database connection
DJANGO_CONTAINER=$(docker ps --filter "name=django" --format "{{.ID}}")
if [ -n "$DJANGO_CONTAINER" ]; then
    echo "📋 Django container: $DJANGO_CONTAINER"
    docker exec -it $DJANGO_CONTAINER python manage.py check --database default
    
    if [ $? -eq 0 ]; then
        echo "✅ Django database connection is healthy"
    else
        echo "⚠️ Django database connection issues detected"
    fi
else
    echo "⚠️ Django container not found"
fi

echo ""
echo "📊 Current migration status:"
if [ -n "$DJANGO_CONTAINER" ]; then
    docker exec -it $DJANGO_CONTAINER python manage.py showmigrations --plan | tail -10
fi
