#!/bin/bash
# اسکریپت برای جمع‌آوری لاگ‌های Workflow duplicate

echo "=== جمع‌آوری لاگ‌های مشکل تکرار Workflow ==="
echo ""

# پیدا کردن Container ID
CONTAINER_ID=$(docker ps | grep pilito | awk '{print $1}' | head -1)

if [ -z "$CONTAINER_ID" ]; then
    echo "❌ Container پیدا نشد!"
    echo "لطفاً Container ID را دستی وارد کنید:"
    echo "docker logs CONTAINER_ID > workflow_logs.txt"
    exit 1
fi

echo "✅ Container ID: $CONTAINER_ID"
echo ""

echo "۱. لاگ‌های ارسال Workflow (آخرین ۵۰ خط):"
docker logs $CONTAINER_ID 2>&1 | grep -E "(\[Workflow\]|\[Node\])" | tail -50

echo ""
echo "---"
echo ""

echo "۲. لاگ‌های Duplicate Detection (آخرین ۵۰ خط):"
docker logs $CONTAINER_ID 2>&1 | grep -E "(Checking for duplicate|DUPLICATE DETECTED)" | tail -50

echo ""
echo "---"
echo ""

echo "۳. لاگ‌های Cached message (آخرین ۳۰ خط):"
docker logs $CONTAINER_ID 2>&1 | grep "Cached sent" | tail -30

echo ""
echo "---"
echo ""

echo "۴. لاگ‌های Text message created (آخرین ۳۰ خط):"
docker logs $CONTAINER_ID 2>&1 | grep "Text message created" | tail -30

echo ""
echo "=== پایان لاگ‌ها ==="
echo ""
echo "برای ذخیره در فایل:"
echo "bash check_workflow_logs.sh > workflow_debug.txt"

