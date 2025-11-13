#!/bin/bash
set -e

echo "🚀 Starting entrypoint script..."

# Set defaults for PostgreSQL connection
POSTGRES_HOST="${POSTGRES_HOST:-db}"
POSTGRES_PORT="${POSTGRES_PORT:-5432}"

echo "⏳ Waiting for PostgreSQL at $POSTGRES_HOST:$POSTGRES_PORT..."

while ! nc -z "$POSTGRES_HOST" "$POSTGRES_PORT"; do
    echo "PostgreSQL is unavailable - sleeping"
    sleep 1
done

echo "✅ PostgreSQL is up and running!"

# Wait for Redis to be ready
echo "⏳ Waiting for Redis..."

while ! nc -z redis 6379; do
    echo "Redis is unavailable - sleeping"
    sleep 1
done

echo "✅ Redis is up and running!"

# Only run migrations and collectstatic for web service
if [[ "$1" == "gunicorn"* ]]; then
    echo "🔄 Running Django migrations..."
    
    # Clean up conflicting migration files from server
    echo "🧹 Cleaning up old conflicting migrations..."
    rm -f /app/src/web_knowledge/migrations/0023_change_qapair_page_to_set_null.py || true
    rm -f /app/src/web_knowledge/migrations/0025_change_qapair_page_to_set_null.py || true
    
    # Remove migration 0025 from database if exists
    echo "🗑️ Removing migration 0025 from database if exists..."
    python manage.py shell << "PYEOF" 2>/dev/null || true
from django.db import connection
cursor = connection.cursor()
cursor.execute("DELETE FROM django_migrations WHERE app = 'web_knowledge' AND name = '0025_change_qapair_page_to_set_null';")
connection.commit()
PYEOF
    
    # Check and fake migration 0023 if it already exists with different content
    echo "🔧 Checking migration web_knowledge 0023..."
    if python manage.py showmigrations web_knowledge 2>/dev/null | grep -q "\[X\] 0023"; then
        echo "Migration 0023 already applied, faking to match local state..."
        python manage.py migrate web_knowledge 0023 --fake || true
    fi
    
    python manage.py migrate --noinput
    
    echo "📦 Collecting static files..."
    python manage.py collectstatic --noinput --clear
    
    echo "✅ Django setup complete!"
fi

# For celery workers, just wait a bit for migrations to complete
if [[ "$1" == "celery"* ]]; then
    echo "⏳ Celery worker waiting for migrations..."
    sleep 5
    echo "✅ Ready to start Celery!"
fi

echo "🎯 Executing command: $@"
exec "$@"

