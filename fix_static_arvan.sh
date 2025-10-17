#!/bin/bash

# 🔧 اسکریپت خودکار برای حل مشکل Static Files با Arvan Cloud
# این اسکریپت رو در VPS اجرا کن

set -e

echo "🔧 Starting Arvan Cloud Static Files Fix..."

# رنگ‌ها برای خروجی
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# بررسی اینکه در دایرکتوری پروژه هستیم
if [ ! -f "docker-compose.yml" ]; then
    echo -e "${RED}❌ Error: docker-compose.yml not found!${NC}"
    echo "Please run this script from /root/pilito directory"
    exit 1
fi

echo "📁 Current directory: $(pwd)"

# قدم 1: بررسی Environment Variables
echo ""
echo "📝 Step 1: Checking Environment Variables..."

if [ ! -f ".env" ]; then
    echo -e "${RED}❌ Error: .env file not found!${NC}"
    exit 1
fi

# چک کردن متغیرهای مورد نیاز
REQUIRED_VARS=(
    "AWS_ACCESS_KEY_ID"
    "AWS_SECRET_ACCESS_KEY"
    "AWS_STORAGE_BUCKET_NAME"
    "AWS_S3_ENDPOINT_URL"
    "AWS_S3_CUSTOM_DOMAIN"
)

for var in "${REQUIRED_VARS[@]}"; do
    if grep -q "^${var}=" .env; then
        value=$(grep "^${var}=" .env | cut -d '=' -f 2-)
        if [ -z "$value" ]; then
            echo -e "${RED}❌ ${var} is empty in .env${NC}"
            exit 1
        else
            echo -e "${GREEN}✅ ${var} is set${NC}"
        fi
    else
        echo -e "${RED}❌ ${var} not found in .env${NC}"
        echo ""
        echo "Please add it to .env file:"
        echo "${var}=your-value-here"
        exit 1
    fi
done

# قدم 2: Restart Docker Containers
echo ""
echo "🔄 Step 2: Restarting Docker containers..."
docker-compose down
sleep 2
docker-compose up -d

# انتظار برای start شدن containers
echo "⏳ Waiting for containers to start..."
sleep 10

# بررسی وضعیت containers
if ! docker-compose ps | grep -q "Up"; then
    echo -e "${RED}❌ Error: Containers failed to start!${NC}"
    echo "Check logs with: docker-compose logs"
    exit 1
fi

echo -e "${GREEN}✅ Containers are running${NC}"

# قدم 3: بررسی Django App
echo ""
echo "🔍 Step 3: Checking Django app..."

if ! docker exec django_app python manage.py check --deploy --fail-level WARNING 2>/dev/null; then
    echo -e "${YELLOW}⚠️  Warning: Django check found some issues${NC}"
    echo "Continuing anyway..."
else
    echo -e "${GREEN}✅ Django check passed${NC}"
fi

# قدم 4: اجرای Collectstatic
echo ""
echo "📦 Step 4: Running collectstatic..."
echo "This will upload static files to Arvan Cloud..."

if docker exec django_app python manage.py collectstatic --noinput --clear; then
    echo -e "${GREEN}✅ Collectstatic completed successfully${NC}"
else
    echo -e "${RED}❌ Collectstatic failed!${NC}"
    echo ""
    echo "Common issues:"
    echo "1. Check AWS credentials in .env"
    echo "2. Check Arvan Cloud bucket is Public"
    echo "3. Check endpoint URL is correct"
    echo ""
    echo "View logs:"
    echo "docker logs django_app --tail 50"
    exit 1
fi

# قدم 5: تست اتصال به Arvan Cloud
echo ""
echo "🧪 Step 5: Testing connection to Arvan Cloud..."

BUCKET_NAME=$(grep "^AWS_STORAGE_BUCKET_NAME=" .env | cut -d '=' -f 2-)
ENDPOINT=$(grep "^AWS_S3_CUSTOM_DOMAIN=" .env | cut -d '=' -f 2-)

TEST_URL="https://${ENDPOINT}/static/admin/css/base.css"

echo "Testing URL: $TEST_URL"

HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$TEST_URL" || echo "000")

if [ "$HTTP_CODE" = "200" ]; then
    echo -e "${GREEN}✅ Static files are accessible!${NC}"
    echo "URL: $TEST_URL"
elif [ "$HTTP_CODE" = "403" ]; then
    echo -e "${RED}❌ 403 Forbidden - Bucket is not Public or credentials are wrong${NC}"
    echo ""
    echo "Fix:"
    echo "1. Go to Arvan Cloud panel"
    echo "2. Make bucket Public"
    echo "3. Check Access Keys are correct"
elif [ "$HTTP_CODE" = "404" ]; then
    echo -e "${RED}❌ 404 Not Found - File doesn't exist${NC}"
    echo ""
    echo "This means collectstatic didn't upload files."
    echo "Check logs: docker logs django_app --tail 50"
else
    echo -e "${RED}❌ Error: HTTP $HTTP_CODE${NC}"
    echo "Check network connection and endpoint URL"
fi

# قدم 6: بررسی CORS (اختیاری)
echo ""
echo "🔍 Step 6: Checking CORS headers..."

CORS_HEADER=$(curl -s -I "$TEST_URL" | grep -i "access-control-allow-origin" || echo "")

if [ -n "$CORS_HEADER" ]; then
    echo -e "${GREEN}✅ CORS headers are set${NC}"
    echo "$CORS_HEADER"
else
    echo -e "${YELLOW}⚠️  CORS headers not found${NC}"
    echo ""
    echo "To fix:"
    echo "1. Go to Arvan Cloud panel → Bucket Settings → CORS"
    echo "2. Add rule:"
    echo "   - AllowedOrigins: *"
    echo "   - AllowedMethods: GET, HEAD"
fi

# خلاصه نهایی
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 Summary"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

if [ "$HTTP_CODE" = "200" ]; then
    echo -e "${GREEN}✅ SUCCESS: Static files are working!${NC}"
    echo ""
    echo "🎉 You can now access your Django admin:"
    echo "   http://185.164.72.165:8000/admin/"
    echo ""
    echo "CSS and static files should load correctly."
else
    echo -e "${RED}❌ FAILED: Static files are not accessible${NC}"
    echo ""
    echo "Next steps:"
    echo "1. Check logs: docker logs django_app --tail 50"
    echo "2. Verify Arvan Cloud credentials"
    echo "3. Make sure bucket is Public"
    echo "4. Check CORS settings"
    echo ""
    echo "For detailed guide, see: FIX_STATIC_FILES_ARVAN.md"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

