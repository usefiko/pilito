#!/bin/bash

# Nginx Setup Script for VPS
# Run this ON THE VPS server after SSH'ing in

set -e

echo "🌐 Setting up Nginx for api.pilito.com"
echo "======================================"

# Update system
echo "📦 Updating system packages..."
apt-get update -qq

# Install Nginx
echo "📥 Installing Nginx..."
apt-get install nginx -y

# Create Nginx configuration
echo "⚙️  Creating Nginx configuration..."
cat > /etc/nginx/sites-available/api.pilito.com << 'EOF'
server {
    listen 80;
    listen [::]:80;
    server_name api.pilito.com;

    client_max_body_size 100M;

    access_log /var/log/nginx/api.pilito.com.access.log;
    error_log /var/log/nginx/api.pilito.com.error.log;

    location / {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    location /static/ {
        alias /root/pilito/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    location /media/ {
        alias /root/pilito/media/;
        expires 30d;
    }
}
EOF

# Enable the site
echo "🔗 Enabling site..."
ln -sf /etc/nginx/sites-available/api.pilito.com /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# Test configuration
echo "🧪 Testing Nginx configuration..."
nginx -t

# Configure firewall
echo "🛡️  Configuring firewall..."
ufw allow 80/tcp
ufw allow 443/tcp

# Restart Nginx
echo "🔄 Restarting Nginx..."
systemctl restart nginx
systemctl enable nginx

# Check status
echo ""
echo "✅ Nginx Status:"
systemctl status nginx --no-pager | head -10

# Test local connection
echo ""
echo "🧪 Testing local connection to Django..."
curl -I http://localhost:8000 2>/dev/null || echo "⚠️  Django app might not be running on port 8000"

echo ""
echo "======================================"
echo "🎉 Nginx setup complete!"
echo "======================================"
echo ""
echo "📋 Next steps:"
echo "1. Make sure Django is running: docker ps | grep django_app"
echo "2. Test from browser: http://api.pilito.com"
echo "3. Check logs: tail -f /var/log/nginx/api.pilito.com.error.log"
echo ""
echo "🔒 To add SSL (HTTPS), run:"
echo "   apt-get install certbot python3-certbot-nginx -y"
echo "   certbot --nginx -d api.pilito.com"
echo ""

