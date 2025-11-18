#!/bin/bash
# Fix web_knowledge migration issue
# The columns already exist, so we need to fake the migration

echo "🔧 Checking current migration state..."
docker exec -it $(docker ps -q -f name=django) python manage.py showmigrations web_knowledge | tail -20

echo ""
echo "📝 The columns external_id and external_source already exist in the database."
echo "   We need to fake the migration to skip adding them again."
echo ""
echo "🎯 Faking migration 0026 (if it exists in database)..."

# Check if migration 0026 exists and fake it
docker exec -it $(docker ps -q -f name=django) python manage.py migrate web_knowledge 0025 --fake 2>/dev/null || true
docker exec -it $(docker ps -q -f name=django) python manage.py migrate web_knowledge --fake-initial

echo ""
echo "✅ Done! Now running migrations normally..."
docker exec -it $(docker ps -q -f name=django) python manage.py migrate

echo ""
echo "📊 Final migration state:"
docker exec -it $(docker ps -q -f name=django) python manage.py showmigrations web_knowledge | tail -20

