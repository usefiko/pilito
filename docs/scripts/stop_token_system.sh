#!/bin/bash

# Stop Script for Instagram Token Auto-Refresh System

echo "🛑 Stopping Instagram Token Auto-Refresh System..."
echo "=============================================="

# Function to stop process
stop_process() {
    local name="$1"
    local pattern="$2"
    
    echo "🔧 Stopping $name..."
    
    # Find and kill processes
    pids=$(pgrep -f "$pattern" 2>/dev/null || true)
    
    if [ -z "$pids" ]; then
        echo "   ℹ️  $name was not running"
        return 0
    fi
    
    # Try graceful shutdown first
    echo "   📤 Sending TERM signal to $name..."
    echo "$pids" | xargs kill -TERM 2>/dev/null || true
    
    # Wait a bit
    sleep 3
    
    # Check if still running
    pids=$(pgrep -f "$pattern" 2>/dev/null || true)
    if [ -z "$pids" ]; then
        echo "   ✅ $name stopped gracefully"
        return 0
    fi
    
    # Force kill if still running
    echo "   🔨 Force killing $name..."
    echo "$pids" | xargs kill -KILL 2>/dev/null || true
    sleep 1
    
    # Final check
    pids=$(pgrep -f "$pattern" 2>/dev/null || true)
    if [ -z "$pids" ]; then
        echo "   ✅ $name stopped (forced)"
    else
        echo "   ❌ Failed to stop $name"
        return 1
    fi
}

echo ""
echo "1️⃣ Stopping Celery Beat..."
stop_process "Celery Beat" "celery.*beat"

echo ""
echo "2️⃣ Stopping Celery Worker..."
stop_process "Celery Worker" "celery.*worker"

echo ""
echo "3️⃣ Stopping Redis (if started by our scripts)..."
# Only stop Redis if it seems to be started by our script (check if running without config)
if pgrep -f "redis-server.*6379" > /dev/null && ! pgrep -f "redis-server.*conf" > /dev/null; then
    stop_process "Redis" "redis-server"
else
    echo "   ℹ️  Redis appears to be system-managed, skipping"
fi

echo ""
echo "4️⃣ Cleaning up..."

# Remove any leftover PID files
if [ -f "celerybeat.pid" ]; then
    rm -f celerybeat.pid
    echo "   🗑️  Removed celerybeat.pid"
fi

if [ -f "celeryd.pid" ]; then
    rm -f celeryd.pid
    echo "   🗑️  Removed celeryd.pid"
fi

# Show final status
echo ""
echo "🔍 Final Status Check:"

if pgrep -f "celery.*beat" > /dev/null; then
    echo "   ⚠️  Celery Beat: Still running"
else
    echo "   ✅ Celery Beat: Stopped"
fi

if pgrep -f "celery.*worker" > /dev/null; then
    echo "   ⚠️  Celery Worker: Still running"
else
    echo "   ✅ Celery Worker: Stopped"
fi

if pgrep -f "redis-server" > /dev/null; then
    echo "   ⚠️  Redis: Still running (this is usually OK)"
else
    echo "   ✅ Redis: Stopped"
fi

echo ""
echo "=============================================="
echo "🎯 Instagram Token Auto-Refresh System Stopped"
echo "=============================================="
echo ""
echo "💡 Notes:"
echo "   - Redis may still be running (normal for system Redis)"
echo "   - Logs are preserved in logs/ directory"
echo "   - To restart: ./run_token_refresh_system.sh"
echo ""
echo "📊 To check if any tokens need manual attention:"
echo "   python src/manage.py convert_instagram_tokens --check-only"