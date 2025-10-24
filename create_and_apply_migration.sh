#!/bin/bash
echo "📝 Step 1: Check current migration files..."
ls -la src/settings/migrations/ | tail -10

echo ""
echo "🔄 Step 2: Making new migrations..."
docker exec $(docker ps --filter "name=django" --format "{{.Names}}" | head -1) python manage.py makemigrations settings

echo ""
echo "✅ Step 3: Applying migrations..."
docker exec $(docker ps --filter "name=django" --format "{{.Names}}" | head -1) python manage.py migrate settings

echo ""
echo "🔄 Step 4: Restarting services..."
docker ps --format "{{.Names}}" | grep -E "(django|celery)" | xargs -I {} docker restart {}

echo ""
echo "🎉 Done! Check the logs now."
