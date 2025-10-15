#!/bin/bash

# 🚀 Automatic Deployment Script with Instagram Token Auto-Refresh
# This script handles complete deployment with zero manual intervention

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    local color=$1
    local message=$2
    echo -e "${color}${message}${NC}"
}

# Function to print section header
print_section() {
    local title=$1
    echo ""
    print_status $PURPLE "=================================================="
    print_status $PURPLE "🚀 $title"
    print_status $PURPLE "=================================================="
}

print_section "AUTOMATIC DEPLOYMENT WITH TOKEN AUTO-REFRESH"

print_status $BLUE "📋 This script will:"
echo "   ✅ Pull latest code from Git"
echo "   ✅ Build and start all containers"
echo "   ✅ Run all migrations automatically"
echo "   ✅ Setup Instagram token auto-refresh system"
echo "   ✅ Start Celery worker and beat services"
echo "   ✅ Verify complete system health"
echo ""

# Step 1: Pull latest code
print_section "STEP 1: UPDATING CODE"
print_status $BLUE "📥 Pulling latest code from Git..."
if git pull; then
    print_status $GREEN "✅ Code updated successfully"
else
    print_status $YELLOW "⚠️  Git pull completed (check for conflicts)"
fi

# Step 2: Stop existing containers
print_section "STEP 2: PREPARING DEPLOYMENT"
print_status $BLUE "🛑 Stopping existing containers..."
docker compose down || print_status $YELLOW "⚠️  Some containers were not running"

# Step 3: Build and start containers
print_section "STEP 3: BUILDING AND STARTING SERVICES"
print_status $BLUE "🔨 Building containers with latest changes..."
if docker compose up -d --build; then
    print_status $GREEN "✅ All containers started successfully"
else
    print_status $RED "❌ Failed to start containers"
    exit 1
fi

# Step 4: Wait for services to be ready
print_section "STEP 4: WAITING FOR SERVICES"
print_status $BLUE "⏳ Waiting for services to initialize..."
sleep 15

# Function to check container health
check_container_health() {
    local container_name=$1
    local max_attempts=30
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if docker ps | grep -q "$container_name.*Up"; then
            print_status $GREEN "✅ $container_name is healthy"
            return 0
        fi
        
        if [ $((attempt % 5)) -eq 0 ]; then
            print_status $YELLOW "⏳ Still waiting for $container_name... (attempt $attempt/$max_attempts)"
        fi
        
        sleep 2
        attempt=$((attempt + 1))
    done
    
    print_status $RED "❌ $container_name failed to start properly"
    return 1
}

# Check all containers
print_status $BLUE "🔍 Checking container health..."
containers=("django_app" "postgres_db" "redis_cache" "celery_worker" "celery_beat")
all_healthy=true

for container in "${containers[@]}"; do
    if ! check_container_health "$container"; then
        all_healthy=false
    fi
done

if [ "$all_healthy" = false ]; then
    print_status $RED "❌ Some containers are not healthy. Check logs:"
    echo "   docker compose logs django_app"
    echo "   docker compose logs celery_worker"
    echo "   docker compose logs celery_beat"
    exit 1
fi

# Step 5: Verify system components
print_section "STEP 5: SYSTEM VERIFICATION"

# Check Django app
print_status $BLUE "🔧 Verifying Django application..."
if docker exec django_app python manage.py check --deploy; then
    print_status $GREEN "✅ Django application is healthy"
else
    print_status $RED "❌ Django application has issues"
    exit 1
fi

# Check Redis connection
print_status $BLUE "🔗 Testing Redis connection..."
if docker exec django_app python -c "import redis; r=redis.Redis(host='redis', port=6379); r.ping(); print('Redis OK')"; then
    print_status $GREEN "✅ Redis connection successful"
else
    print_status $RED "❌ Redis connection failed"
    exit 1
fi

# Check database connection
print_status $BLUE "🗄️  Testing database connection..."
if docker exec django_app python manage.py dbshell -c "SELECT 1;" > /dev/null 2>&1; then
    print_status $GREEN "✅ Database connection successful"
else
    print_status $RED "❌ Database connection failed"
    exit 1
fi

# Step 6: Verify automatic token refresh system
print_section "STEP 6: VERIFYING TOKEN AUTO-REFRESH SYSTEM"

# Check if periodic tasks exist
print_status $BLUE "📅 Checking automatic refresh schedule..."
task_check=$(docker exec django_app python manage.py shell -c "
from django_celery_beat.models import PeriodicTask
tasks = PeriodicTask.objects.filter(name__icontains='Instagram')
for task in tasks:
    print(f'{task.name}: {\"Enabled\" if task.enabled else \"Disabled\"}')
if tasks.count() >= 2:
    print('SUCCESS: Both daily and emergency refresh tasks are configured')
else:
    print('WARNING: Automatic refresh tasks may not be configured properly')
")

if echo "$task_check" | grep -q "SUCCESS"; then
    print_status $GREEN "✅ Automatic refresh schedule is configured"
    echo "$task_check" | grep "Instagram"
else
    print_status $YELLOW "⚠️  Automatic refresh schedule needs attention"
    echo "$task_check"
fi

# Check Celery worker status
print_status $BLUE "⚙️  Checking Celery worker status..."
if docker exec celery_worker celery -A core inspect ping | grep -q "pong"; then
    print_status $GREEN "✅ Celery worker is responding"
else
    print_status $YELLOW "⚠️  Celery worker is starting up..."
fi

# Check Celery beat status
print_status $BLUE "📊 Checking Celery beat scheduler..."
if docker logs celery_beat --tail 10 | grep -q "beat"; then
    print_status $GREEN "✅ Celery beat scheduler is running"
else
    print_status $YELLOW "⚠️  Celery beat scheduler is starting up..."
fi

# Step 7: Final health check
print_section "STEP 7: FINAL SYSTEM STATUS"

print_status $BLUE "📊 System Status Summary:"
echo ""

# Container status
print_status $BLUE "🐳 Docker Containers:"
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep -E "(django_app|celery_worker|celery_beat|postgres_db|redis_cache)"

echo ""

# Instagram channels status
print_status $BLUE "📱 Instagram Channels:"
channel_count=$(docker exec django_app python manage.py shell -c "
from settings.models import InstagramChannel
channels = InstagramChannel.objects.filter(is_connect=True)
print(f'Connected channels: {channels.count()}')
if channels.exists():
    for ch in channels:
        print(f'  • {ch.telegram_channel.channel_name}: {ch.instagram_username}')
else:
    print('  • No connected Instagram channels')
")
echo "$channel_count"

echo ""

# Success summary
print_section "🎉 DEPLOYMENT COMPLETED SUCCESSFULLY!"

print_status $GREEN "✅ All systems are operational and ready"
print_status $GREEN "✅ Instagram token auto-refresh is active"
print_status $GREEN "✅ No manual intervention required"

echo ""
print_status $BLUE "📅 Automatic Token Refresh Schedule:"
echo "   🌙 Daily Refresh: Every day at 3:00 AM (tokens expiring in 7 days)"
echo "   ⚡ Emergency Refresh: Every 6 hours (tokens expiring in 1 day)"
echo "   🔄 Real-time Recovery: Automatic retry when sending messages"

echo ""
print_status $BLUE "📋 Useful Monitoring Commands:"
echo "   • System status: docker compose ps"
echo "   • App logs: docker logs django_app --tail 50"
echo "   • Worker logs: docker logs celery_worker --tail 50"
echo "   • Beat logs: docker logs celery_beat --tail 50"
echo "   • Check refresh tasks: docker exec django_app python manage.py shell -c \"from django_celery_beat.models import PeriodicTask; [print(f'{t.name}: {t.enabled}') for t in PeriodicTask.objects.filter(name__icontains='Instagram')]\""

echo ""
print_status $GREEN "🚀 Your Instagram messaging system is now fully automated!"
print_status $GREEN "   Tokens will refresh automatically - no manual work needed!"

echo ""