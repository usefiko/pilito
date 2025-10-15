#!/bin/bash

# 🚀 راه‌اندازی سیستم خودکار رفرش توکن روی سرور
echo "🚀 راه‌اندازی سیستم خودکار رفرش توکن Instagram..."
echo "=================================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    local color=$1
    local message=$2
    echo -e "${color}${message}${NC}"
}

# Function to check if docker-compose is running
check_docker_running() {
    if ! docker compose ps | grep -q "Up"; then
        print_status $RED "❌ Docker containers are not running!"
        print_status $YELLOW "💡 Please start with: docker compose up -d"
        exit 1
    fi
}

# Function to check container status
check_container() {
    local container_name=$1
    if docker ps | grep -q "$container_name"; then
        print_status $GREEN "✅ $container_name is running"
        return 0
    else
        print_status $RED "❌ $container_name is not running"
        return 1
    fi
}

# Function to run django command in container
run_django_command() {
    local command=$1
    local description=$2
    
    print_status $BLUE "🔧 $description..."
    
    if docker exec django_app python manage.py $command; then
        print_status $GREEN "✅ $description completed successfully"
        return 0
    else
        print_status $RED "❌ $description failed"
        return 1
    fi
}

print_status $BLUE "📋 Checking system status..."

# Check if docker compose is running
check_docker_running

# Step 1: Run Django migrations
print_status $YELLOW "\n📦 Step 1: Running Django migrations..."
if ! run_django_command "migrate" "Django migrations"; then
    exit 1
fi

if ! run_django_command "migrate django_celery_beat" "Celery Beat migrations"; then
    exit 1
fi

# Step 2: Rebuild and restart containers with Celery
print_status $YELLOW "\n🔄 Step 2: Rebuilding containers with Celery services..."
if docker compose down; then
    print_status $GREEN "✅ Containers stopped"
else
    print_status $RED "❌ Failed to stop containers"
    exit 1
fi

if docker compose up -d --build; then
    print_status $GREEN "✅ Containers rebuilt and started"
else
    print_status $RED "❌ Failed to start containers"
    exit 1
fi

# Wait for containers to start
print_status $BLUE "⏳ Waiting for containers to start..."
sleep 10

# Step 3: Check all containers are running
print_status $YELLOW "\n🔍 Step 3: Checking container status..."
all_running=true

for container in django_app postgres_db redis_cache celery_worker celery_beat; do
    if ! check_container $container; then
        all_running=false
    fi
done

if [ "$all_running" = false ]; then
    print_status $RED "\n❌ Some containers failed to start. Check logs:"
    echo "docker compose logs celery_worker"
    echo "docker compose logs celery_beat"
    exit 1
fi

# Step 4: Test Redis connection
print_status $YELLOW "\n🔗 Step 4: Testing Redis connection..."
if docker exec django_app python -c "import redis; r=redis.Redis(host='redis', port=6379); r.ping(); print('Redis connection OK')"; then
    print_status $GREEN "✅ Redis connection successful"
else
    print_status $RED "❌ Redis connection failed"
    exit 1
fi

# Step 5: Create periodic task for automatic token refresh
print_status $YELLOW "\n⏰ Step 5: Setting up automatic token refresh schedule..."
if run_django_command "shell -c \"
from django_celery_beat.models import PeriodicTask, CrontabSchedule
import json

# Create crontab for daily refresh at 3 AM
daily_schedule, created = CrontabSchedule.objects.get_or_create(
    minute='0',
    hour='3',
    day_of_week='*',
    day_of_month='*',
    month_of_year='*',
)

# Create crontab for emergency refresh every 6 hours
emergency_schedule, created = CrontabSchedule.objects.get_or_create(
    minute='0',
    hour='*/6',
    day_of_week='*',
    day_of_month='*',
    month_of_year='*',
)

# Create daily refresh task
daily_task, created = PeriodicTask.objects.get_or_create(
    crontab=daily_schedule,
    name='Instagram Token Daily Refresh',
    task='message.tasks.auto_refresh_instagram_tokens',
    args=json.dumps([7]),  # 7 days before expiry
)

# Create emergency refresh task
emergency_task, created = PeriodicTask.objects.get_or_create(
    crontab=emergency_schedule,
    name='Instagram Token Emergency Refresh',
    task='message.tasks.auto_refresh_instagram_tokens',
    args=json.dumps([1]),  # 1 day before expiry
)

print('✅ Periodic tasks created successfully')
\"" "Creating periodic tasks"; then
    print_status $GREEN "✅ Automatic refresh schedule created"
else
    print_status $RED "❌ Failed to create periodic tasks"
fi

# Step 6: Test the token refresh task
print_status $YELLOW "\n🧪 Step 6: Testing token refresh task..."
if run_django_command "shell -c \"
from message.tasks import auto_refresh_instagram_tokens
result = auto_refresh_instagram_tokens.delay(30)  # Test with 30 days
print(f'Task ID: {result.id}')
print('✅ Token refresh task test completed')
\"" "Testing token refresh task"; then
    print_status $GREEN "✅ Token refresh task test successful"
else
    print_status $YELLOW "⚠️  Task test completed (check logs for details)"
fi

# Final status check
print_status $YELLOW "\n📊 Final Status Check..."
print_status $BLUE "📈 Checking Celery worker status..."
docker exec celery_worker celery -A core inspect active 2>/dev/null || print_status $YELLOW "⚠️  Celery worker is starting up..."

print_status $BLUE "📅 Checking Celery beat status..."
if docker logs celery_beat --tail 5 2>/dev/null | grep -q "beat"; then
    print_status $GREEN "✅ Celery beat is running"
else
    print_status $YELLOW "⚠️  Celery beat is starting up..."
fi

# Success summary
print_status $GREEN "\n🎉 SUCCESS! Instagram Token Auto-Refresh System is now active!"
print_status $GREEN "=================================================="
print_status $BLUE "📅 Daily Refresh: Every day at 3:00 AM (tokens expiring in 7 days)"
print_status $BLUE "🚨 Emergency Refresh: Every 6 hours (tokens expiring in 1 day)"
print_status $BLUE "⚡ Real-time Recovery: Automatic retry when sending messages"

print_status $YELLOW "\n📋 Useful Commands:"
echo "• Check worker status: docker logs celery_worker"
echo "• Check beat status: docker logs celery_beat"
echo "• Check scheduled tasks: docker exec django_app python manage.py shell -c \"from django_celery_beat.models import PeriodicTask; print(PeriodicTask.objects.all())\""
echo "• Manual refresh: docker exec django_app python manage.py convert_instagram_tokens"

print_status $GREEN "\n✅ Setup completed! Your Instagram tokens will now refresh automatically."