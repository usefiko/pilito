#!/bin/bash

# ====================================================
# 🔧 Fix Email Images & Static Files Cache
# ====================================================
# این اسکریپت:
# 1. Static files جدید رو جمع‌آوری می‌کنه
# 2. Cache nginx رو clear می‌کنه
# 3. مجوزهای فایل‌ها رو درست می‌کنه
# ====================================================

set -e

echo "🔧 Fixing Email Images & Static Files..."
echo "========================================"

# 1. Pull latest changes
echo ""
echo "📥 Step 1: Pulling latest changes from Git..."
cd /root/pilito
git pull origin main

# 2. Collect static files (با clear برای حذف فایل‌های قدیمی)
echo ""
echo "📦 Step 2: Collecting static files..."
docker-compose exec -T django_app python manage.py collectstatic --noinput --clear

# 3. Fix permissions
echo ""
echo "🔐 Step 3: Fixing file permissions..."
chmod -R 755 /root/pilito/staticfiles/
chown -R root:root /root/pilito/staticfiles/

# 4. Check if new files exist
echo ""
echo "✅ Step 4: Verifying new image files..."
if [ -f "/root/pilito/staticfiles/email_assets/logo.png" ]; then
    echo "✅ Logo found: $(ls -lh /root/pilito/staticfiles/email_assets/logo.png)"
else
    echo "⚠️  Logo not found!"
fi

if [ -f "/root/pilito/staticfiles/email_assets/facebook.png" ]; then
    echo "✅ Facebook icon found"
else
    echo "⚠️  Facebook icon not found!"
fi

if [ -f "/root/pilito/staticfiles/email_assets/instagram.png" ]; then
    echo "✅ Instagram icon found"
else
    echo "⚠️  Instagram icon not found!"
fi

if [ -f "/root/pilito/staticfiles/email_assets/telegram.png" ]; then
    echo "✅ Telegram icon found"
else
    echo "⚠️  Telegram icon not found!"
fi

if [ -f "/root/pilito/staticfiles/email_assets/bg.jpg" ]; then
    echo "✅ Background image found"
else
    echo "⚠️  Background image not found!"
fi

# 5. Clear Nginx cache (reload nginx)
echo ""
echo "🔄 Step 5: Clearing Nginx cache..."
systemctl reload nginx
echo "✅ Nginx reloaded"

# 6. Restart Django to clear any internal cache
echo ""
echo "🔄 Step 6: Restarting Django..."
docker-compose restart django_app

echo ""
echo "⏳ Waiting for Django to start..."
sleep 10

# 7. Test static file serving
echo ""
echo "🧪 Step 7: Testing static file access..."
echo "Testing logo.png..."
curl -I https://api.pilito.com/static/email_assets/logo.png 2>&1 | head -5

echo ""
echo "Testing facebook.png..."
curl -I https://api.pilito.com/static/email_assets/facebook.png 2>&1 | head -5

echo ""
echo "========================================"
echo "✅ Done!"
echo "========================================"
echo ""
echo "📝 Next steps:"
echo "1. Test email sending again"
echo "2. Clear browser cache (Ctrl+Shift+R)"
echo "3. Check email in different email client"
echo ""
echo "💡 If images still don't load:"
echo "   - Wait 5-10 minutes for email client cache to expire"
echo "   - Try accessing: https://api.pilito.com/static/email_assets/logo.png directly"
echo ""

