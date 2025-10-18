#!/bin/bash
# ========================================
# 🔧 Fix Daphne Crash - Switch to Gunicorn + Uvicorn
# ========================================
# مشکل: Daphne با "Illegal Instruction" crash می‌کنه روی سرورهای قدیمی
# راه‌حل: استفاده از Gunicorn + Uvicorn workers (سازگارتر)
# ========================================

set -e  # Exit on error

echo "🔧 Fixing Daphne crash issue..."
echo ""

# 1. رفتن به مسیر پروژه
if [ ! -d "/root/pilito" ]; then
    echo "❌ Error: /root/pilito directory not found!"
    echo "Please run this script on the VPS server."
    exit 1
fi

cd /root/pilito

# 2. Backup قبل از تغییر
echo "📦 Creating backup..."
timestamp=$(date +%Y%m%d_%H%M%S)
cp docker-compose.yml docker-compose.yml.backup.$timestamp || true
cp entrypoint.sh entrypoint.sh.backup.$timestamp || true

# 3. Pull آخرین تغییرات
echo "📥 Pulling latest changes from repository..."
if [ -d ".git" ]; then
    git pull origin main
else
    echo "⚠️ Warning: Not a git repository. Skipping git pull."
    echo "Please manually update docker-compose.yml and entrypoint.sh"
    exit 1
fi

# 4. Stop و remove کردن container های قدیمی
echo "🛑 Stopping old containers..."
docker-compose stop web || true
docker-compose rm -f web || true

# 5. Rebuild کردن image با تغییرات جدید
echo "🏗️ Rebuilding Django image..."
docker-compose build --no-cache web

# 6. Start کردن container جدید
echo "🚀 Starting Django with Gunicorn + Uvicorn..."
docker-compose up -d web

# 7. بررسی وضعیت
echo ""
echo "⏳ Waiting for container to start..."
sleep 5

if docker-compose ps web | grep -q "Up"; then
    echo ""
    echo "✅ ========================================="
    echo "✅ Django is running successfully!"
    echo "✅ ========================================="
    echo ""
    echo "📋 Container status:"
    docker-compose ps web
    echo ""
    echo "📝 Recent logs:"
    docker-compose logs --tail=20 web
    echo ""
    echo "🧪 Test the API:"
    echo "  curl -I https://api.pilito.com/admin/"
    echo ""
else
    echo ""
    echo "❌ ========================================="
    echo "❌ Failed to start Django container!"
    echo "❌ ========================================="
    echo ""
    echo "📝 Container logs:"
    docker-compose logs --tail=50 web
    echo ""
    echo "🔄 Restoring backup..."
    cp docker-compose.yml.backup.$timestamp docker-compose.yml
    cp entrypoint.sh.backup.$timestamp entrypoint.sh
    docker-compose up -d web
    exit 1
fi

echo ""
echo "✅ All done! Your Django app is now running with Gunicorn + Uvicorn."
echo "✅ This setup is more stable on older CPU architectures."
echo ""

