#!/bin/bash

# 🔍 تشخیص مشکل SSH Connection در GitHub Actions

echo "🔍 تشخیص مشکل SSH..."
echo "======================"

# بررسی متغیرهای محیطی (شبیه‌سازی GitHub Actions)
echo "🔧 بررسی پیکربندی SSH..."

# تست دستور ssh-keyscan به صورت محلی
if [ ! -z "$EC2_HOST" ]; then
    echo "📡 تست ssh-keyscan برای host: $EC2_HOST"
    
    # تست 1: Basic ssh-keyscan
    echo "Test 1: Basic ssh-keyscan..."
    if ssh-keyscan -H $EC2_HOST 2>/dev/null; then
        echo "✅ ssh-keyscan موفق بود"
    else
        echo "❌ ssh-keyscan ناموفق - کد خروج: $?"
    fi
    
    # تست 2: ssh-keyscan with timeout
    echo "Test 2: ssh-keyscan با timeout..."
    if timeout 10 ssh-keyscan -H $EC2_HOST 2>/dev/null; then
        echo "✅ ssh-keyscan با timeout موفق بود"
    else
        echo "❌ ssh-keyscan با timeout ناموفق"
    fi
    
    # تست 3: Manual connection test
    echo "Test 3: تست اتصال دستی..."
    if nc -z $EC2_HOST 22 2>/dev/null; then
        echo "✅ Port 22 در دسترس است"
    else
        echo "❌ Port 22 در دسترس نیست"
    fi
    
else
    echo "⚠️ متغیر EC2_HOST تنظیم نشده"
    echo "برای تست محلی: export EC2_HOST=your-ec2-ip"
fi

echo ""
echo "🛠️ راه‌حل‌های پیشنهادی:"
echo "1. بررسی Security Group EC2 - Port 22 باز باشد"
echo "2. بررسی Network ACL"
echo "3. بررسی صحت IP address در GitHub Secrets"
echo "4. استفاده از workflow جدید با retry mechanism"

echo ""
echo "📋 برای حل مشکل:"
echo "chmod +x fix_github_actions.sh"
echo "./fix_github_actions.sh"

echo ""
echo "🔍 اگر مشکل همچنان ادامه دارد:"
echo "• بررسی GitHub Actions logs بیشتر"
echo "• تست اتصال SSH از جای دیگر"
echo "• بررسی AWS Security Groups"