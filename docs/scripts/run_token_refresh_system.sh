#!/bin/bash

# Quick Start Script for Instagram Token Auto-Refresh System
# This script starts everything needed for automatic token management

set -e

echo "🚀 Instagram Token Auto-Refresh System - Quick Start"
echo "================================================="

# Configuration
PROJECT_DIR="/Users/nima/Projects/Fiko-Backend"
VIRTUAL_ENV="$PROJECT_DIR/venv"

# Function to check if process is running
check_process() {
    pgrep -f "$1" > /dev/null 2>&1
}

# Function to start process in background
start_background() {
    local name="$1"
    local command="$2"
    local logfile="$3"
    
    if check_process "$command"; then
        echo "✅ $name is already running"
        return 0
    fi
    
    echo "🔧 Starting $name..."
    nohup bash -c "$command" > "$logfile" 2>&1 &
    sleep 2
    
    if check_process "$command"; then
        echo "✅ $name started successfully"
        echo "   Log: $logfile"
    else
        echo "❌ Failed to start $name"
        echo "   Check log: $logfile"
        return 1
    fi
}

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
fi

# Create logs directory
mkdir -p logs

# Change to src directory for Django commands
cd src

# 1. Check Redis
echo ""
echo "1️⃣ Checking Redis..."
if check_process "redis-server"; then
    echo "✅ Redis is running"
else
    echo "🔧 Starting Redis..."
    if command -v redis-server > /dev/null; then
        start_background "Redis" "redis-server" "../logs/redis.log"
    else
        echo "❌ Redis not found. Please install Redis or start it manually"
        echo "   On macOS: brew install redis && redis-server"
        echo "   On Ubuntu: sudo apt install redis-server && sudo systemctl start redis"
        exit 1
    fi
fi

# 2. Setup Django
echo ""
echo "2️⃣ Setting up Django..."
echo "🗄️  Running migrations..."
python manage.py migrate --verbosity=0

# Create superuser if needed (optional)
echo "👤 Checking for superuser..."
python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(is_superuser=True).exists():
    print('No superuser found. Creating one...')
    User.objects.create_superuser('admin', 'admin@fiko.net', 'admin123')
    print('Superuser created: admin/admin123')
else:
    print('Superuser already exists')
" 2>/dev/null || echo "⚠️  Could not check/create superuser"

# 3. Setup Celery Beat tables
echo ""
echo "3️⃣ Setting up Celery Beat..."
python manage.py migrate django_celery_beat --verbosity=0

# Setup periodic tasks
python manage.py shell << 'EOF' 2>/dev/null || echo "⚠️  Could not setup periodic tasks"
from django_celery_beat.models import PeriodicTask, CrontabSchedule
import json

# Create crontab schedules
daily_3am, created = CrontabSchedule.objects.get_or_create(
    minute=0, hour=3, day_of_week='*', day_of_month='*', month_of_year='*'
)

every_6_hours, created = CrontabSchedule.objects.get_or_create(
    minute=0, hour='*/6', day_of_week='*', day_of_month='*', month_of_year='*'
)

# Create or update periodic tasks
daily_task, created = PeriodicTask.objects.update_or_create(
    name='Auto Refresh Instagram Tokens (Daily)',
    defaults={
        'crontab': daily_3am,
        'task': 'message.tasks.auto_refresh_instagram_tokens',
        'kwargs': json.dumps({'days_before_expiry': 7}),
        'enabled': True,
    }
)

emergency_task, created = PeriodicTask.objects.update_or_create(
    name='Emergency Refresh Instagram Tokens (6-hourly)',
    defaults={
        'crontab': every_6_hours,
        'task': 'message.tasks.auto_refresh_instagram_tokens',
        'kwargs': json.dumps({'days_before_expiry': 1}),
        'enabled': True,
    }
)

print("✅ Periodic tasks configured")
EOF

# 4. Start Celery Worker
echo ""
echo "4️⃣ Starting Celery Worker..."
start_background "Celery Worker" "celery -A core worker -Q instagram_tokens --loglevel=info" "../logs/celery_worker.log"

# 5. Start Celery Beat
echo ""
echo "5️⃣ Starting Celery Beat..."
start_background "Celery Beat" "celery -A core beat --loglevel=info" "../logs/celery_beat.log"

# 6. Test the system
echo ""
echo "6️⃣ Testing the system..."
echo "🧪 Running a test token refresh..."
python manage.py shell -c "
from message.tasks import auto_refresh_instagram_tokens
try:
    result = auto_refresh_instagram_tokens.delay(days_before_expiry=365)  # Test with large threshold
    print(f'✅ Test task queued: {result.id}')
    print('   Check logs/celery_worker.log for results')
except Exception as e:
    print(f'❌ Test failed: {e}')
" 2>/dev/null || echo "⚠️  Could not run test task"

echo ""
echo "================================================="
echo "🎉 Instagram Token Auto-Refresh System Started!"
echo "================================================="
echo ""
echo "📊 System Status:"
echo "   ✅ Redis: Running"
echo "   ✅ Celery Worker: Running (Queue: instagram_tokens)"
echo "   ✅ Celery Beat: Running (Periodic tasks)"
echo ""
echo "📅 Automatic Schedule:"
echo "   🕒 Daily at 3:00 AM: Refresh tokens expiring within 7 days"
echo "   ⚡ Every 6 hours: Emergency refresh for tokens expiring within 1 day"
echo ""
echo "📋 Monitoring:"
echo "   📄 Worker Log: logs/celery_worker.log"
echo "   📄 Beat Log: logs/celery_beat.log"
echo "   📄 Redis Log: logs/redis.log"
echo "   🌐 Django Admin: http://localhost:8000/admin/django_celery_beat/"
echo ""
echo "🛠️  Manual Commands:"
echo "   📊 Check status: python src/manage.py convert_instagram_tokens --check-only"
echo "   🔄 Manual refresh: python src/manage.py auto_refresh_instagram_tokens"
echo "   🔧 Stop all: ./stop_token_system.sh"
echo ""
echo "✨ The system is now fully automated! Tokens will be refreshed automatically."

# Return to original directory
cd ..

echo ""
echo "💡 Tip: You can now close this terminal. The system runs in the background."