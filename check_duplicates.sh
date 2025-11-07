#!/bin/bash
# راهنمای Debug برای مشکل پیام‌های تکراری

echo "=== چک کردن لاگ‌های Instagram Webhook ==="
echo ""
echo "۱. لاگ‌های دریافت webhook:"
tail -100 /var/log/django.log | grep "Instagram Webhook Data"

echo ""
echo "۲. لاگ‌های چک duplicate:"
tail -100 /var/log/django.log | grep "Checking for duplicate"

echo ""
echo "۳. لاگ‌های DUPLICATE DETECTED:"
tail -100 /var/log/django.log | grep "DUPLICATE DETECTED"

echo ""
echo "۴. لاگ‌های ایجاد AI message:"
tail -100 /var/log/django.log | grep "AI message created"

echo ""
echo "۵. لاگ‌های ایجاد Text message:"
tail -100 /var/log/django.log | grep "Text message created"

echo ""
echo "=== چک کردن پیام‌های اخیر در دیتابیس ==="

