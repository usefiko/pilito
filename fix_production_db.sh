#!/bin/bash

# Pilito Production Server - PostgreSQL Fix Script
# This script fixes the missing PostgreSQL container issue

set -e  # Exit on any error

echo "🔍 Checking current container status..."
docker ps -a

echo ""
echo "📍 Finding docker-compose.yml location..."
# Common locations to check
COMPOSE_LOCATIONS=(
    "/root/pilito"
    "/opt/pilito"
    "/app/pilito"
    "/home/pilito"
    "$(pwd)"
)

COMPOSE_FILE=""
for location in "${COMPOSE_LOCATIONS[@]}"; do
    if [ -f "$location/docker-compose.yml" ]; then
        COMPOSE_FILE="$location"
        echo "✅ Found docker-compose.yml in: $COMPOSE_FILE"
        break
    fi
done

if [ -z "$COMPOSE_FILE" ]; then
    echo "❌ Could not find docker-compose.yml"
    echo "Please run this script from the directory containing docker-compose.yml"
    exit 1
fi

cd "$COMPOSE_FILE"

echo ""
echo "🛑 Stopping all running containers..."
docker-compose down || true

echo ""
echo "🗑️  Removing orphaned containers..."
docker-compose down --remove-orphans || true

echo ""
echo "🔄 Starting PostgreSQL database..."
docker-compose up -d db

echo "⏳ Waiting for PostgreSQL to be ready (30 seconds)..."
sleep 10
echo "⏳ 20 seconds remaining..."
sleep 10
echo "⏳ 10 seconds remaining..."
sleep 10

echo ""
echo "🔍 Checking PostgreSQL status..."
docker-compose ps db
docker logs $(docker ps -qf "name=postgres") --tail 20

echo ""
echo "🔄 Starting Redis..."
docker-compose up -d redis
sleep 5

echo ""
echo "🔄 Starting Django web application..."
docker-compose up -d web

echo "⏳ Waiting for Django to initialize (15 seconds)..."
sleep 15

echo ""
echo "🔄 Running database migrations..."
docker-compose exec -T web python manage.py migrate

echo ""
echo "🔄 Starting Celery workers..."
docker-compose up -d celery_worker celery_ai celery_beat

echo ""
echo "🔄 Starting monitoring services..."
docker-compose up -d prometheus grafana redis_exporter postgres_exporter

echo ""
echo "✅ All services started! Checking status..."
docker-compose ps

echo ""
echo "🔍 Checking Django container logs (last 30 lines)..."
docker logs $(docker ps -qf "name=django_app") --tail 30

echo ""
echo "=========================================="
echo "✅ Setup Complete!"
echo "=========================================="
echo "Services should now be running."
echo "Check application: curl http://localhost:8000/health/"
echo ""
echo "To view logs:"
echo "  docker-compose logs -f web"
echo ""
echo "To check specific service:"
echo "  docker-compose logs -f [service_name]"
echo "=========================================="

