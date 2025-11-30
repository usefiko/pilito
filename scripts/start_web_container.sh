#!/bin/bash

###############################################################################
# Quick Fix: Start Django Web Container
# Run this on the server when web container fails to start after migrations
###############################################################################

set -e

echo "======================================================================"
echo "🚀 Starting Django Web Container"
echo "======================================================================"
echo ""

cd ~/pilito

echo "📋 Step 1: Checking current container status..."
docker compose ps

echo ""
echo "📋 Step 2: Checking if web container exists but is stopped..."
if docker compose ps -a | grep -q "web.*Exit"; then
    echo "⚠️  Web container exited with error"
    echo "📋 Showing web container logs:"
    docker compose logs --tail=100 web
fi

echo ""
echo "🔄 Step 3: Starting all services..."
docker compose up -d

echo ""
echo "⏳ Step 4: Waiting for services to start..."
sleep 10

echo ""
echo "📋 Step 5: Checking container status..."
docker compose ps

echo ""
echo "🔍 Step 6: Checking web container specifically..."
if docker compose ps | grep -q "web.*Up"; then
    echo "✅ Web container is running!"
    
    # Try Django check
    echo ""
    echo "🧪 Step 7: Running Django health check..."
    docker compose exec -T web python manage.py check || echo "⚠️  Django check returned warnings (may be okay)"
    
else
    echo "❌ Web container failed to start"
    echo ""
    echo "📋 Web container logs:"
    docker compose logs --tail=50 web
    echo ""
    echo "💡 Try manually: docker compose up web"
fi

echo ""
echo "======================================================================"
echo "📊 Final Status:"
echo "======================================================================"
docker compose ps

echo ""
echo "🌐 If web is running, access your app at:"
echo "   http://46.249.98.162:8000"
echo ""

