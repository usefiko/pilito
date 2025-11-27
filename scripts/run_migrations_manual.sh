#!/bin/bash
# Run this on the server to manually apply migrations

echo "🔍 Checking Django web container status..."
docker compose ps web

echo ""
echo "🔄 Running Django migrations manually..."
docker compose exec web python manage.py migrate

echo ""
echo "✅ Migrations complete! Restarting services..."
docker compose restart web celery_worker celery_ai celery_beat

echo ""
echo "📊 Checking status..."
docker compose ps

echo ""
echo "✅ Done! Check logs:"
echo "  docker compose logs -f web"

