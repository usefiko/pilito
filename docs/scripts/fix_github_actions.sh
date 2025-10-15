#!/bin/bash

# 🔧 اسکریپت تعمیر GitHub Actions SSH مشکل

echo "🔧 تعمیر مشکل GitHub Actions SSH..."
echo "===================================="

# حل سریع - جایگزینی workflow
echo "📁 جایگزینی workflow file..."

# نسخه پشتیبان از workflow فعلی
if [ -f ".github/workflows/deploy.yml" ]; then
    cp .github/workflows/deploy.yml .github/workflows/deploy-backup.yml
    echo "✅ Backup ایجاد شد: .github/workflows/deploy-backup.yml"
fi

# جایگزینی با ورژن تعمیر شده
if [ -f "deploy-fixed-ssh.yml" ]; then
    cp deploy-fixed-ssh.yml .github/workflows/deploy.yml
    echo "✅ Workflow جدید کپی شد"
else
    echo "❌ فایل deploy-fixed-ssh.yml پیدا نشد!"
    exit 1
fi

echo ""
echo "🔍 بررسی تغییرات..."
echo "تغییرات کلیدی در workflow جدید:"
echo "• ✅ بررسی اتصال SSH با retry mechanism"
echo "• ✅ Fallback برای مشکلات ssh-keyscan"
echo "• ✅ Timeout برای تمام دستورات"
echo "• ✅ بهبود error handling"

echo ""
echo "📋 مراحل بعدی:"
echo "1. git add ."
echo "2. git commit -m '🔧 Fix GitHub Actions SSH connection issues'"
echo "3. git push origin main"

echo ""
echo "🎯 ویژگی‌های جدید workflow:"
echo "• Multiple attempts برای ssh-keyscan"
echo "• Automatic fallback به StrictHostKeyChecking=no"
echo "• Connection timeout management"
echo "• Robust error handling"

echo ""
echo "✅ آماده برای commit و push!"