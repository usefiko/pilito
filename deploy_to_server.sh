#!/bin/bash
# Direct deployment script for server
# This script will SSH to server and run deployment commands

set -e

SERVER="root@185.164.72.165"
PASSWORD="9188945776poST?"

echo "🚀 Connecting to server and deploying..."
echo "=========================================="

# Check if sshpass is installed
if ! command -v sshpass &> /dev/null; then
    echo "❌ sshpass is not installed. Installing..."
    if [[ "$OSTYPE" == "darwin"* ]]; then
        brew install hudochenkov/sshpass/sshpass
    else
        echo "Please install sshpass manually"
        exit 1
    fi
fi

# SSH commands to run on server
sshpass -p "$PASSWORD" ssh -o StrictHostKeyChecking=no "$SERVER" << 'ENDSSH'
set -e

echo "📦 Pulling latest code..."
cd /root/pilito || cd /var/www/pilito || cd /opt/pilito || (echo "❌ Project directory not found. Please specify the correct path." && exit 1)

# Find the actual project directory
if [ ! -d "src" ]; then
    echo "🔍 Searching for project directory..."
    PROJECT_DIR=$(find /root /var/www /opt -name "manage.py" -type f 2>/dev/null | head -1 | xargs dirname)
    if [ -z "$PROJECT_DIR" ]; then
        echo "❌ Could not find project directory"
        exit 1
    fi
    cd "$PROJECT_DIR"
fi

echo "✅ Found project at: $(pwd)"

# Pull latest code
if [ -d ".git" ]; then
    git pull origin main || git pull origin master
else
    echo "⚠️  Not a git repository, skipping pull"
fi

# Activate virtual environment if exists
if [ -d "venv" ]; then
    source venv/bin/activate
elif [ -d "../venv" ]; then
    source ../venv/bin/activate
fi

# Run migrations
echo "🔄 Running migrations..."
python manage.py migrate --noinput

# Seed default keywords
echo "🌱 Seeding default keywords..."
python manage.py seed_default_keywords

# Verify keywords
echo "✅ Verifying keywords..."
python manage.py test_keywords

# Collect static files
echo "📦 Collecting static files..."
python manage.py collectstatic --noinput || echo "⚠️  Static files collection skipped"

# Restart services
echo "🔄 Restarting services..."

# Try Docker first
if command -v docker-compose &> /dev/null; then
    docker-compose restart web celery worker || echo "⚠️  Docker restart failed"
elif command -v docker &> /dev/null && docker ps | grep -q pilito; then
    docker restart $(docker ps | grep pilito | awk '{print $1}') || echo "⚠️  Docker restart failed"
fi

# Try systemd
if systemctl is-active --quiet gunicorn 2>/dev/null; then
    systemctl restart gunicorn || echo "⚠️  Gunicorn restart failed"
fi

if systemctl is-active --quiet celery 2>/dev/null; then
    systemctl restart celery || echo "⚠️  Celery restart failed"
fi

# Try supervisor
if command -v supervisorctl &> /dev/null; then
    supervisorctl restart all || echo "⚠️  Supervisor restart failed"
fi

echo "✅ Deployment completed!"
echo ""
echo "📋 Summary:"
echo "  - Code pulled"
echo "  - Migrations run"
echo "  - Keywords seeded"
echo "  - Services restarted"
echo ""
echo "🔍 To verify, check logs:"
echo "  docker logs -f <container>"
echo "  or"
echo "  journalctl -u gunicorn -f"

ENDSSH

echo ""
echo "✅ Deployment script completed!"

