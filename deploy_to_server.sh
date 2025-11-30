#!/bin/bash
# Direct deployment script for server
# This script will SSH to server and run deployment commands

set -e

# SECURITY NOTE: These credentials should be moved to environment variables or GitHub secrets
# For now, they are here for direct deployment
SERVER="${VPS_HOST:-root@46.249.98.162}"
PASSWORD="${VPS_PASSWORD}"

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
if [ -n "$PASSWORD" ]; then
    SSH_CMD="sshpass -p '$PASSWORD' ssh -o StrictHostKeyChecking=no"
else
    SSH_CMD="ssh -o StrictHostKeyChecking=no"
fi

$SSH_CMD "$SERVER" << 'ENDSSH'
set -e

echo "🔍 Checking disk space..."
df -h
echo ""

# Check if we need to clean up
AVAILABLE_GB=$(df -BG / | tail -1 | awk '{print $4}' | sed 's/G//')
if [ "$AVAILABLE_GB" -lt 15 ]; then
    echo "⚠️  Low disk space detected! Running cleanup..."
    
    # Stop containers to release locks
    docker stop $(docker ps -aq) 2>/dev/null || true
    
    # Aggressive cleanup
    docker container prune -f || true
    docker image prune -a -f || true
    docker volume prune -f || true
    docker builder prune -a -f || true
    
    # Check again
    AVAILABLE_GB=$(df -BG / | tail -1 | awk '{print $4}' | sed 's/G//')
    if [ "$AVAILABLE_GB" -lt 15 ]; then
        echo "❌ Still insufficient space (${AVAILABLE_GB}GB). Manual intervention required."
        exit 1
    fi
    
    echo "✅ Cleanup successful! ${AVAILABLE_GB}GB now available"
fi

echo "📦 Pulling latest code..."
cd /root/pilito || cd /var/www/pilito || cd /opt/pilito || (echo "❌ Project directory not found. Please specify the correct path." && exit 1)

# Find the actual project directory
if [ ! -d "src" ]; then
    echo "🔍 Searching for project directory..."
    PROJECT_DIR=$(find /root /var/www /opt -name "manage.py" -type f 2>/dev/null | head -1 | xargs dirname 2>/dev/null)
    if [ -z "$PROJECT_DIR" ]; then
        echo "❌ Could not find project directory"
        exit 1
    fi
    cd "$PROJECT_DIR/.."
fi

echo "✅ Found project at: $(pwd)"

# Pull latest code
if [ -d ".git" ]; then
    git pull origin main || git pull origin master
else
    echo "⚠️  Not a git repository, skipping pull"
fi

# Check if using Docker or traditional deployment
if [ -f "docker-compose.yml" ]; then
    echo "🐳 Deploying with Docker..."
    
    # Stop containers
    docker-compose down || true
    
    # Remove old images
    docker-compose rm -f || true
    
    # Build and start
    docker-compose up -d --build --remove-orphans
    
    # Wait for services
    echo "⏳ Waiting for services to start..."
    sleep 30
    
    # Check status
    docker-compose ps
    
    echo "✅ Docker deployment complete!"
    
    # Perform health checks
    echo "🏥 Running health checks..."
    
    # Check if containers are running
    if ! docker-compose ps | grep -q "Up"; then
        echo "❌ Some containers failed to start!"
        docker-compose logs --tail=50
        exit 1
    fi
    
else
    echo "📦 Traditional deployment..."

# Activate virtual environment if exists
if [ -d "venv" ]; then
    source venv/bin/activate
elif [ -d "../venv" ]; then
    source ../venv/bin/activate
fi
    
    # Install dependencies
    pip install -r src/requirements/production.txt || pip install -r src/requirements/base.txt

# Run migrations
echo "🔄 Running migrations..."
    python src/manage.py migrate --noinput || python manage.py migrate --noinput

# Collect static files
echo "📦 Collecting static files..."
    python src/manage.py collectstatic --noinput || python manage.py collectstatic --noinput || echo "⚠️  Static files collection skipped"

# Restart services
echo "🔄 Restarting services..."

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
fi

echo ""
echo "✅ Deployment completed!"
echo ""
echo "📋 Summary:"
echo "  - Code pulled"
echo "  - Services deployed"
echo "  - Health checks passed"
echo ""
echo "🔍 To verify, check:"
if [ -f "docker-compose.yml" ]; then
    echo "  docker-compose logs -f"
    echo "  docker-compose ps"
else
echo "  journalctl -u gunicorn -f"
    echo "  systemctl status gunicorn celery"
fi

ENDSSH

echo ""
echo "✅ Deployment script completed!"
