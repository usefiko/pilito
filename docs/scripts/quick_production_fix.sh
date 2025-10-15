#!/bin/bash

# Quick Production Fix - One-liner for PostgreSQL Collation Version Mismatch
# Run this on your production server: ubuntu@ip-172-31-8-229

echo "🔧 Quick PostgreSQL Collation Fix for Production"
echo "================================================"

# Find PostgreSQL container
POSTGRES_CONTAINER=$(docker ps --filter "name=db" --format "{{.ID}}" | head -1)

if [ -z "$POSTGRES_CONTAINER" ]; then
    POSTGRES_CONTAINER=$(docker ps --filter "ancestor=postgres" --format "{{.ID}}" | head -1)
fi

if [ -z "$POSTGRES_CONTAINER" ]; then
    echo "❌ PostgreSQL container not found!"
    echo "Available containers:"
    docker ps --format "table {{.Names}}\t{{.Image}}"
    exit 1
fi

echo "✅ Found PostgreSQL container: $POSTGRES_CONTAINER"

# Execute the fix
echo "🔄 Fixing collation version mismatch..."
docker exec $POSTGRES_CONTAINER psql -U FikoUsr -d FikoDB -c "ALTER DATABASE \"FikoDB\" REFRESH COLLATION VERSION;"

if [ $? -eq 0 ]; then
    echo "✅ Collation version fixed successfully!"
    echo ""
    echo "🔄 Now restart your web services:"
    echo "   docker-compose restart web"
    echo "   # OR"
    echo "   docker compose restart web"
    echo ""
    echo "📊 Check logs after restart:"
    echo "   docker-compose logs web | grep -i collation"
else
    echo "❌ Fix failed. Try manual approach:"
    echo "   docker exec -it $POSTGRES_CONTAINER psql -U FikoUsr -d FikoDB"
    echo "   ALTER DATABASE \"FikoDB\" REFRESH COLLATION VERSION;"
fi
