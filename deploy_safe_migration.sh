#!/bin/bash
# Simple and robust script to fix migration issue
# This pulls the latest code and lets the safe migration handle everything

set -e

SERVER="root@185.164.72.165"
PASSWORD="9188945776poST?"

echo "🚀 Deploying fixed migration to production server..."

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

cd /root/pilito

echo "📥 Step 1: Pulling latest code with safe migration..."
git pull origin main || git pull origin master

echo ""
echo "🛑 Step 2: Stopping containers..."
docker-compose down

echo ""
echo "🔨 Step 3: Rebuilding images with new code..."
export DOCKER_BUILDKIT=1
export COMPOSE_DOCKER_CLI_BUILD=1
docker-compose build --parallel

echo ""
echo "🚀 Step 4: Starting all services..."
docker-compose up -d

echo ""
echo "⏳ Waiting for services to start..."
sleep 30

echo ""
echo "🔍 Step 5: Checking Django app..."
if docker ps | grep -q django_app; then
    echo "✅ Django app container is running"
    
    echo ""
    echo "📊 Running migrations with safe migration..."
    docker exec django_app python manage.py migrate --noinput
    
    echo ""
    echo "✅ Migrations completed successfully!"
    
    echo ""
    echo "📊 Verifying migration status..."
    docker exec django_app python manage.py showmigrations accounts | tail -5
    
    echo ""
    echo "🔍 Running Django check..."
    docker exec django_app python manage.py check
    
    echo ""
    echo "✅ All checks passed!"
else
    echo "❌ Django app container failed to start"
    echo ""
    echo "📋 Container logs:"
    docker logs django_app --tail 100
    exit 1
fi

echo ""
echo "📊 Final container status:"
docker-compose ps

echo ""
echo "✅ Deployment completed successfully!"
ENDSSH

echo ""
echo "🎉 Production deployment successful!"
echo ""
echo "Next steps:"
echo "1. Verify the application is running: https://api.pilito.com/health/"
echo "2. Check the logs: docker logs django_app --tail 50"
echo "3. Monitor the services: docker-compose ps"

