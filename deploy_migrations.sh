#!/bin/bash
echo "🔄 Running migrations in production..."
docker exec django_app python manage.py migrate settings

echo ""
echo "✅ Migrations complete! Restarting services..."
docker-compose restart django_app celery_worker celery_beat

echo ""
echo "🎉 Done! Check if AI is working now."
