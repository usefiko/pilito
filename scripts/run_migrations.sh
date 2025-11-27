#!/bin/bash
# Run Django migrations on production server

SERVER_IP="46.249.98.162"
SERVER_USER="root"

echo "🔄 Running Django migrations on production server..."
echo "===================================================="
echo ""

ssh -o StrictHostKeyChecking=no ${SERVER_USER}@${SERVER_IP} << 'ENDSSH'
set -e

cd ~/pilito

echo "📊 Current status:"
docker-compose ps

echo ""
echo "🔄 Running migrations..."
docker-compose exec -T web python manage.py migrate

echo ""
echo "✅ Migrations completed!"

echo ""
echo "🔄 Restarting services to apply changes..."
docker-compose restart web celery_worker celery_ai celery_beat

echo ""
echo "⏳ Waiting for services to restart..."
sleep 10

echo ""
echo "📊 Final status:"
docker-compose ps

echo ""
echo "✅ All done! Your application should be working now."

ENDSSH

echo ""
echo "✅ Migrations applied successfully!"
echo ""
echo "Test your API:"
echo "  curl https://api.pilito.com/health/"

