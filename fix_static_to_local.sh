#!/bin/bash
# ========================================
# 🔧 Fix Static Files - Serve from VPS Locally
# ========================================
# این اسکریپت:
# 1. Nginx رو تنظیم میکنه تا static files رو از VPS محلی سرو کنه
# 2. collectstatic رو اجرا میکنه تا فایل‌های استاتیک جمع‌آوری بشن
# 3. Django رو restart میکنه
# ========================================

set -e  # Exit on error

echo "🔧 Fixing Static Files Configuration..."

# 1. تنظیم Nginx برای سرو static files از محلی
echo "📝 Configuring Nginx for local static files..."

# Backup قبل از تغییر
cp /etc/nginx/sites-available/api.pilito.com /etc/nginx/sites-available/api.pilito.com.backup.$(date +%Y%m%d_%H%M%S)

# Uncomment the static location block
cat > /etc/nginx/sites-available/api.pilito.com << 'EOF'
server {
    listen 80;
    server_name api.pilito.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name api.pilito.com;

    ssl_certificate /etc/letsencrypt/live/api.pilito.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.pilito.com/privkey.pem;
    include /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;

    client_max_body_size 100M;

    # ✅ Static files - سرو محلی از VPS
    location /static/ {
        alias /root/pilito/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # ✅ Media files - Proxy به Arvan Cloud (اختیاری، چون URL مستقیم داریم)
    # اگر میخوای media هم از Nginx رد بشه:
    # location /media/ {
    #     proxy_pass https://pilito.s3.ir-thr-at1.arvanstorage.ir/media/;
    #     proxy_set_header Host pilito.s3.ir-thr-at1.arvanstorage.ir;
    # }

    # Backend Django
    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 60s;
    }

    # WebSocket support
    location /ws/ {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 3600s;
    }
}
EOF

# Test Nginx configuration
echo "🧪 Testing Nginx configuration..."
nginx -t

if [ $? -eq 0 ]; then
    echo "✅ Nginx configuration is valid"
    systemctl reload nginx
    echo "✅ Nginx reloaded"
else
    echo "❌ Nginx configuration test failed!"
    echo "Restoring backup..."
    cp /etc/nginx/sites-available/api.pilito.com.backup.$(date +%Y%m%d)* /etc/nginx/sites-available/api.pilito.com
    exit 1
fi

# 2. جمع‌آوری فایل‌های استاتیک
echo "📦 Collecting static files..."
cd /root/pilito
docker-compose exec -T django_app python manage.py collectstatic --noinput --clear

# 3. بررسی مجوزها
echo "🔐 Setting correct permissions..."
chmod -R 755 /root/pilito/staticfiles/
chown -R root:root /root/pilito/staticfiles/

# 4. Restart Django (اختیاری)
echo "🔄 Restarting Django container..."
docker-compose restart django_app

echo ""
echo "✅ ========================================="
echo "✅ Static Files Configuration Complete!"
echo "✅ ========================================="
echo ""
echo "📋 Summary:"
echo "  - Nginx: Serving static files from /root/pilito/staticfiles/"
echo "  - Django: Serving media files from Arvan Cloud"
echo "  - Static URL: https://api.pilito.com/static/"
echo "  - Media URL: https://pilito.s3.ir-thr-at1.arvanstorage.ir/media/"
echo ""
echo "🧪 Test:"
echo "  curl -I https://api.pilito.com/static/admin/css/base.css"
echo ""

