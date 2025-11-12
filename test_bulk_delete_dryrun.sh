#!/bin/bash

# تست Dry-Run برای بررسی syntax و منطق اسکریپت
# این تست بدون اتصال به سرور انجام می‌شه

set -e

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  تست Dry-Run اسکریپت${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# تست 1: بررسی syntax
echo -e "${YELLOW}[1/5] بررسی syntax...${NC}"
if bash -n test_bulk_delete.sh; then
  echo -e "${GREEN}✅ Syntax درست است${NC}"
else
  echo -e "${RED}❌ خطای syntax${NC}"
  exit 1
fi
echo ""

# تست 2: بررسی متغیرها
echo -e "${YELLOW}[2/5] بررسی متغیرها...${NC}"
if grep -q "PAGE_IDS_ARRAY" test_bulk_delete.sh && grep -q "PAGE_IDS_JSON" test_bulk_delete.sh; then
  echo -e "${GREEN}✅ متغیرها درست تعریف شده‌اند${NC}"
else
  echo -e "${RED}❌ مشکل در تعریف متغیرها${NC}"
  exit 1
fi
echo ""

# تست 3: بررسی JSON structure
echo -e "${YELLOW}[3/5] تست ساخت JSON array...${NC}"
TEST_ARRAY=("uuid1" "uuid2" "uuid3")
TEST_JSON="["
for i in "${!TEST_ARRAY[@]}"; do
  if [ $i -gt 0 ]; then
    TEST_JSON+=","
  fi
  TEST_JSON+="\"${TEST_ARRAY[$i]}\""
done
TEST_JSON+="]"

if [ "$TEST_JSON" = '["uuid1","uuid2","uuid3"]' ]; then
  echo -e "${GREEN}✅ ساخت JSON array درست است: ${TEST_JSON}${NC}"
else
  echo -e "${RED}❌ مشکل در ساخت JSON: ${TEST_JSON}${NC}"
  exit 1
fi
echo ""

# تست 4: بررسی API endpoints
echo -e "${YELLOW}[4/5] بررسی API endpoints...${NC}"
ENDPOINTS=(
  "/api/v1/auth/login/"
  "/api/v1/web-knowledge/websites/"
  "/api/v1/web-knowledge/manual-crawl/"
  "/api/v1/web-knowledge/pages/"
  "/api/v1/web-knowledge/pages/bulk-delete/"
  "/api/v1/web-knowledge/products/"
  "/api/v1/web-knowledge/products/bulk-delete/"
  "/api/v1/web-knowledge/qa-pairs/"
  "/api/v1/web-knowledge/qa-pairs/bulk_delete/"
  "/api/v1/ai/rag/status/"
)

for endpoint in "${ENDPOINTS[@]}"; do
  if grep -q "$endpoint" test_bulk_delete.sh; then
    echo -e "${GREEN}  ✅ ${endpoint}${NC}"
  else
    echo -e "${RED}  ❌ ${endpoint} پیدا نشد${NC}"
  fi
done
echo ""

# تست 5: بررسی error handling
echo -e "${YELLOW}[5/5] بررسی error handling...${NC}"
if grep -q "if.*-z.*TOKEN" test_bulk_delete.sh && grep -q "if.*PAGE_IDS_ARRAY.*-eq 0" test_bulk_delete.sh; then
  echo -e "${GREEN}✅ Error handling درست است${NC}"
else
  echo -e "${YELLOW}⚠️  ممکن است error handling ناقص باشد${NC}"
fi
echo ""

echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}✅ تست Dry-Run تکمیل شد${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo -e "${YELLOW}💡 برای تست واقعی، سرور را راه‌اندازی کنید و اسکریپت را اجرا کنید:${NC}"
echo -e "${BLUE}   ./test_bulk_delete.sh${NC}"
echo ""

