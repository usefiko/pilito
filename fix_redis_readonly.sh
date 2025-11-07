#!/bin/bash

# Script to fix Redis read-only error

echo "🔧 Fixing Redis read-only mode..."

# Check if running in Docker Swarm
if docker service ls 2>/dev/null | grep -q redis; then
    echo "📦 Detected Docker Swarm deployment"
    
    # Restart Redis service
    echo "Restarting Redis service..."
    docker service update --force pilito_redis
    
    echo "✅ Redis service restarted. Waiting for it to be ready..."
    sleep 10
    
    # Check Redis status
    REDIS_CONTAINER=$(docker ps | grep redis | awk '{print $1}')
    if [ -n "$REDIS_CONTAINER" ]; then
        echo "Testing Redis connection..."
        docker exec $REDIS_CONTAINER redis-cli ping
        docker exec $REDIS_CONTAINER redis-cli INFO replication | grep role
    fi
    
# Check if running in Docker Compose
elif docker-compose ps 2>/dev/null | grep -q redis; then
    echo "📦 Detected Docker Compose deployment"
    
    # Restart Redis container
    echo "Restarting Redis container..."
    docker-compose restart redis
    
    echo "✅ Redis container restarted. Waiting for it to be ready..."
    sleep 5
    
    # Check Redis status
    docker-compose exec -T redis redis-cli ping
    docker-compose exec -T redis redis-cli INFO replication | grep role
    
# Check if Redis is running locally
elif pgrep -f redis-server > /dev/null; then
    echo "💻 Detected local Redis instance"
    
    # Connect to Redis and disable read-only mode
    echo "Disabling read-only mode..."
    redis-cli CONFIG SET replica-read-only no
    redis-cli REPLICAOF NO ONE
    
    echo "✅ Redis is now in master mode"
    redis-cli INFO replication | grep role
else
    echo "❌ No Redis instance found!"
    echo "Please check your Redis deployment."
    exit 1
fi

echo ""
echo "✅ Done! Your Redis should now be writable."
echo "If the error persists, check your Redis configuration."

