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

