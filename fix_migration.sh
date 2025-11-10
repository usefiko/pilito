#!/bin/bash
# Fix migration conflict on server

echo "🔧 Fixing migration conflict..."

# Navigate to project
cd /root/pilito2/Untitled

# Remove conflicting migration file
echo "📝 Removing 0999 migration file..."
rm -f src/web_knowledge/migrations/0999_add_external_fields_to_product.py
rm -rf src/web_knowledge/migrations/__pycache__

# Remove from git if tracked
git rm src/web_knowledge/migrations/0999_add_external_fields_to_product.py --cached 2>/dev/null || true

# Commit the removal
git add -A
git commit -m "fix: remove conflicting migration 0999" || echo "Nothing to commit"

# Clean Python cache in containers
echo "🧹 Cleaning Python cache in containers..."
docker compose exec -T web find /app -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
docker compose exec -T web find /app -name "*.pyc" -delete 2>/dev/null || true

# Restart only Django container
echo "🔄 Restarting Django container..."
docker compose restart web

echo "✅ Done! Checking status..."
docker compose ps web

echo "📋 If still having issues, check logs:"
echo "docker compose logs web --tail=50"

