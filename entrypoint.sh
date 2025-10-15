#!/bin/bash

echo "Waiting for PostgreSQL..."
while ! nc -z db 5432; do
  sleep 0.1
done
echo "PostgreSQL started."

echo "Waiting for Redis..."
while ! nc -z redis 6379; do
  sleep 0.1
done
echo "Redis started."

# Create logs directory if it doesn't exist
mkdir -p /app/logs

# Check if we're running a Celery command or a bash script (for celery_worker with metrics)
if [[ "$1" == "celery" ]] || [[ "$1" == "bash" ]]; then
    echo "Executing command: $@"
    exec "$@"
else
    # Run database migrations only for main web service
    echo "Running Django migrations..."
    python manage.py migrate

    # Run Celery Beat migrations for automatic token refresh
    echo "Running Celery Beat migrations..."
    python manage.py migrate django_celery_beat

    # Collect static files to S3 (suppress verbose output)
    echo "Collecting static files to S3..."
    python manage.py collectstatic --noinput --verbosity=1 || echo "⚠️ Warning: collectstatic failed, but continuing..."

    # Use Daphne instead of runserver for WebSocket support
    echo "Starting Daphne server for WebSocket support..."
    daphne -b 0.0.0.0 -p 8000 core.asgi:application
fi