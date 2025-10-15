#!/bin/bash

# Instagram Token Auto-Refresh System Startup Script
# This script starts Celery worker and beat for automatic token management

set -e

echo "🚀 Starting Instagram Token Auto-Refresh System..."

# Configuration
PROJECT_DIR="/Users/nima/Projects/Fiko-Backend"
VIRTUAL_ENV="$PROJECT_DIR/venv"
SETTINGS_MODULE="core.settings.production"

# Check if running from correct directory
if [ ! -f "src/manage.py" ]; then
    echo "❌ Error: Please run this script from the project root directory"
    exit 1
fi

# Activate virtual environment
if [ -d "$VIRTUAL_ENV" ]; then
    echo "🔧 Activating virtual environment..."
    source "$VIRTUAL_ENV/bin/activate"
else
    echo "⚠️  Virtual environment not found at $VIRTUAL_ENV"
    echo "   Please ensure virtual environment is created"
fi

# Change to src directory
cd src

# Install/upgrade requirements
echo "📦 Installing requirements..."
pip install -r requirements/base.txt

# Run Django migrations for django-celery-beat
echo "🗄️  Running Django migrations..."
python manage.py migrate django_celery_beat

# Create periodic tasks if they don't exist
echo "⏰ Setting up periodic tasks..."
python manage.py shell << 'EOF'
from django_celery_beat.models import PeriodicTask, CrontabSchedule
import json

# Create crontab schedules
daily_3am, created = CrontabSchedule.objects.get_or_create(
    minute=0,
    hour=3,
    day_of_week='*',
    day_of_month='*',
    month_of_year='*',
    timezone='UTC'
)

every_6_hours, created = CrontabSchedule.objects.get_or_create(
    minute=0,
    hour='*/6',
    day_of_week='*',
    day_of_month='*',
    month_of_year='*',
    timezone='UTC'
)

# Create periodic tasks
daily_task, created = PeriodicTask.objects.get_or_create(
    name='Auto Refresh Instagram Tokens (Daily)',
    defaults={
        'crontab': daily_3am,
        'task': 'message.tasks.auto_refresh_instagram_tokens',
        'kwargs': json.dumps({'days_before_expiry': 7}),
        'enabled': True,
    }
)

emergency_task, created = PeriodicTask.objects.get_or_create(
    name='Emergency Refresh Instagram Tokens (6-hourly)',
    defaults={
        'crontab': every_6_hours,
        'task': 'message.tasks.auto_refresh_instagram_tokens',
        'kwargs': json.dumps({'days_before_expiry': 1}),
        'enabled': True,
    }
)

print("✅ Periodic tasks configured successfully")
EOF

echo "✅ Setup completed!"
echo ""
echo "📋 To start the system:"
echo "   1. Start Redis server: redis-server"
echo "   2. Start Celery worker: celery -A core worker -Q instagram_tokens --loglevel=info"
echo "   3. Start Celery beat: celery -A core beat --loglevel=info"
echo ""
echo "🔍 To monitor:"
echo "   - Celery tasks: celery -A core flower"
echo "   - Django admin: http://localhost:8000/admin/django_celery_beat/"
echo ""
echo "🔄 The system will now automatically refresh Instagram tokens:"
echo "   - Daily at 3:00 AM (tokens expiring within 7 days)"
echo "   - Every 6 hours (emergency refresh for tokens expiring within 1 day)"