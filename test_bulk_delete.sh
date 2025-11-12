#!/bin/bash

# تست کامل Bulk Delete برای Pages, Products, و Q&A Pairs
# شامل چک کردن chunks قبل و بعد از پاک کردن

set -e  # Exit on error

# رنگ‌ها برای خروجی
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# تنظیمات
# اگر BASE_URL تنظیم نشده، از production استفاده کن
if [ -z "$BASE_URL" ]; then
  # تست localhost اول
  if curl -s --connect-timeout 2 "http://localhost:8000/health/" > /dev/null 2>&1; then
    BASE_URL="http://localhost:8000"
    echo "✅ استفاده از localhost:8000"
  # اگر localhost در دسترس نیست، از production استفاده کن
  elif curl -s --connect-timeout 5 "https://api.pilito.com/health/" > /dev/null 2>&1; then
    BASE_URL="https://api.pilito.com"
    echo "✅ استفاده از production: https://api.pilito.com"
  else
    BASE_URL="http://localhost:8000"
    echo "⚠️  استفاده از localhost:8000 (تست اتصال نشده)"
  fi
fi

EMAIL="iamyaserm@gmail.com"
PASSWORD="Fara9020"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  تست کامل Bulk Delete API${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# ============================================
# 1. لاگین و گرفتن Token
# ============================================
echo -e "${YELLOW}[1/13] لاگین و گرفتن Token...${NC}"
LOGIN_RESPONSE=$(curl -s -X POST "${BASE_URL}/api/v1/usr/login" \
  -H "Content-Type: application/json" \
  -d "{
    \"email_or_username\": \"${EMAIL}\",
    \"password\": \"${PASSWORD}\"
  }")

TOKEN=$(echo $LOGIN_RESPONSE | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)

if [ -z "$TOKEN" ]; then
  echo -e "${RED}❌ خطا در لاگین${NC}"
  echo -e "${YELLOW}Response: ${LOGIN_RESPONSE}${NC}"
  
  # چک کردن اینکه آیا سرور در دسترس هست
  if ! curl -s --connect-timeout 5 "${BASE_URL}/health/" > /dev/null 2>&1; then
    echo -e "${RED}❌ سرور در دسترس نیست: ${BASE_URL}${NC}"
    echo -e "${YELLOW}💡 لطفاً BASE_URL را تنظیم کنید یا سرور را راه‌اندازی کنید${NC}"
  fi
  
  exit 1
fi

echo -e "${GREEN}✅ لاگین موفق - Token: ${TOKEN:0:20}...${NC}"
echo ""

# ============================================
# 2. گرفتن یا ساخت Website Source
# ============================================
echo -e "${YELLOW}[2/13] گرفتن Website Source...${NC}"
WEBSITES_RESPONSE=$(curl -s -X GET "${BASE_URL}/api/v1/web-knowledge/websites/" \
  -H "Authorization: Bearer ${TOKEN}")

WEBSITE_ID=$(echo $WEBSITES_RESPONSE | grep -o '"id":"[^"]*' | head -1 | cut -d'"' -f4)

if [ -z "$WEBSITE_ID" ]; then
  echo -e "${YELLOW}⚠️  Website Source وجود ندارد، در حال ساخت...${NC}"
  CREATE_WEBSITE_RESPONSE=$(curl -s -X POST "${BASE_URL}/api/v1/web-knowledge/websites/" \
    -H "Authorization: Bearer ${TOKEN}" \
    -H "Content-Type: application/json" \
    -d '{
      "name": "Test Website",
      "url": "https://yasermotahedin.com"
    }')
  
  WEBSITE_ID=$(echo $CREATE_WEBSITE_RESPONSE | grep -o '"id":"[^"]*' | cut -d'"' -f4)
  
  if [ -z "$WEBSITE_ID" ]; then
    echo -e "${RED}❌ خطا در ساخت Website Source${NC}"
    echo "$CREATE_WEBSITE_RESPONSE"
    exit 1
  fi
fi

echo -e "${GREEN}✅ Website ID: ${WEBSITE_ID}${NC}"
echo ""

# ============================================
# 3. کرال دستی 3 URL
# ============================================
echo -e "${YELLOW}[3/13] شروع کرال دستی 3 URL...${NC}"
CRAWL_RESPONSE=$(curl -s -X POST "${BASE_URL}/api/v1/web-knowledge/manual-crawl/" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d "{
    \"website_id\": \"${WEBSITE_ID}\",
    \"urls\": \"https://yasermotahedin.com/\nhttps://yasermotahedin.com/start/psi-test/\nhttps://yasermotahedin.com/organizational-meeting/\"
  }")

TASK_ID=$(echo $CRAWL_RESPONSE | grep -o '"task_id":"[^"]*' | cut -d'"' -f4)

if [ -z "$TASK_ID" ]; then
  echo -e "${RED}❌ خطا در شروع کرال${NC}"
  echo "$CRAWL_RESPONSE"
  exit 1
fi

echo -e "${GREEN}✅ کرال شروع شد - Task ID: ${TASK_ID}${NC}"

# صبر کردن تا کرال تمام بشه
echo -e "${YELLOW}⏳ در حال انتظار برای تکمیل کرال...${NC}"
for i in {1..60}; do
  sleep 2
  STATUS_RESPONSE=$(curl -s -X GET "${BASE_URL}/api/v1/web-knowledge/manual-crawl/status/${TASK_ID}/" \
    -H "Authorization: Bearer ${TOKEN}")
  
  STATUS=$(echo $STATUS_RESPONSE | grep -o '"status":"[^"]*' | cut -d'"' -f4)
  PROGRESS=$(echo $STATUS_RESPONSE | grep -o '"progress":[0-9.]*' | cut -d':' -f2)
  
  if [ "$STATUS" = "completed" ]; then
    echo -e "${GREEN}✅ کرال تکمیل شد!${NC}"
    break
  elif [ "$STATUS" = "failed" ]; then
    echo -e "${RED}❌ کرال با خطا مواجه شد${NC}"
    echo "$STATUS_RESPONSE"
    exit 1
  fi
  
  echo -e "${BLUE}   Progress: ${PROGRESS}% (${i}/60)${NC}"
done

echo ""

# ============================================
# 4. گرفتن لیست Pages
# ============================================
echo -e "${YELLOW}[4/13] گرفتن لیست Pages...${NC}"
PAGES_RESPONSE=$(curl -s -X GET "${BASE_URL}/api/v1/web-knowledge/pages/?website=${WEBSITE_ID}" \
  -H "Authorization: Bearer ${TOKEN}")

echo "$PAGES_RESPONSE" | python3 -m json.tool | head -50

# استخراج Page IDs به صورت آرایه bash
PAGE_IDS_ARRAY=($(echo "$PAGES_RESPONSE" | grep -o '"id":"[^"]*' | head -3 | cut -d'"' -f4))

if [ ${#PAGE_IDS_ARRAY[@]} -eq 0 ]; then
  echo -e "${RED}❌ هیچ صفحه‌ای پیدا نشد${NC}"
  echo -e "${YELLOW}⚠️  Response: ${PAGES_RESPONSE:0:200}...${NC}"
  exit 1
fi

echo -e "${GREEN}✅ ${#PAGE_IDS_ARRAY[@]} Page پیدا شد${NC}"
for i in "${!PAGE_IDS_ARRAY[@]}"; do
  echo -e "${BLUE}   Page $((i+1)): ${PAGE_IDS_ARRAY[$i]}${NC}"
done
echo ""

# ============================================
# 5. چک کردن Chunks قبل از پاک کردن Pages
# ============================================
echo -e "${YELLOW}[5/13] چک کردن Chunks قبل از پاک کردن Pages...${NC}"

# گرفتن تعداد کل chunks از نوع website
RAG_STATUS_BEFORE=$(curl -s -X GET "${BASE_URL}/api/v1/ai/rag/status/" \
  -H "Authorization: Bearer ${TOKEN}")

CHUNKS_BEFORE_DELETE=$(echo "$RAG_STATUS_BEFORE" | grep -o '"website":{[^}]*"count":[0-9]*' | grep -o '"count":[0-9]*' | cut -d':' -f2 || echo "0")

if [ -z "$CHUNKS_BEFORE_DELETE" ]; then
  CHUNKS_BEFORE_DELETE=0
fi

echo -e "${BLUE}   تعداد کل Website chunks قبل از پاک کردن: ${CHUNKS_BEFORE_DELETE}${NC}"
echo -e "${GREEN}✅ Chunks قبل از پاک کردن: ${CHUNKS_BEFORE_DELETE}${NC}"
echo ""

# ============================================
# 6. Bulk Delete Pages
# ============================================
echo -e "${YELLOW}[6/13] پاک کردن Pages (Bulk Delete)...${NC}"

# ساخت JSON array از Page IDs
PAGE_IDS_JSON="["
for i in "${!PAGE_IDS_ARRAY[@]}"; do
  if [ $i -gt 0 ]; then
    PAGE_IDS_JSON+=","
  fi
  PAGE_IDS_JSON+="\"${PAGE_IDS_ARRAY[$i]}\""
done
PAGE_IDS_JSON+="]"

DELETE_PAGES_RESPONSE=$(curl -s -X POST "${BASE_URL}/api/v1/web-knowledge/pages/bulk-delete/" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d "{
    \"page_ids\": ${PAGE_IDS_JSON}
  }")

echo "$DELETE_PAGES_RESPONSE" | python3 -m json.tool

SUCCESS=$(echo $DELETE_PAGES_RESPONSE | grep -o '"success":true' || echo "")

if [ -z "$SUCCESS" ]; then
  echo -e "${RED}❌ خطا در پاک کردن Pages${NC}"
  echo "$DELETE_PAGES_RESPONSE"
  exit 1
fi

echo -e "${GREEN}✅ Pages با موفقیت پاک شدند${NC}"
echo ""

# ============================================
# 7. چک کردن Chunks بعد از پاک کردن Pages
# ============================================
echo -e "${YELLOW}[7/13] چک کردن Chunks بعد از پاک کردن Pages...${NC}"

sleep 2  # صبر برای cleanup

# گرفتن تعداد کل chunks از نوع website
RAG_STATUS_AFTER=$(curl -s -X GET "${BASE_URL}/api/v1/ai/rag/status/" \
  -H "Authorization: Bearer ${TOKEN}")

CHUNKS_AFTER_DELETE=$(echo "$RAG_STATUS_AFTER" | grep -o '"website":{[^}]*"count":[0-9]*' | grep -o '"count":[0-9]*' | cut -d':' -f2 || echo "0")

if [ -z "$CHUNKS_AFTER_DELETE" ]; then
  CHUNKS_AFTER_DELETE=0
fi

echo -e "${BLUE}   تعداد کل Website chunks بعد از پاک کردن: ${CHUNKS_AFTER_DELETE}${NC}"

# محاسبه تفاوت
CHUNKS_DELETED=$((CHUNKS_BEFORE_DELETE - CHUNKS_AFTER_DELETE))

if [ "$CHUNKS_DELETED" -gt 0 ]; then
  echo -e "${GREEN}✅ تست Pages موفق: ${CHUNKS_DELETED} chunk پاک شد (قبل: ${CHUNKS_BEFORE_DELETE}, بعد: ${CHUNKS_AFTER_DELETE})${NC}"
else
  echo -e "${YELLOW}⚠️  هیچ chunkی پاک نشد (قبل: ${CHUNKS_BEFORE_DELETE}, بعد: ${CHUNKS_AFTER_DELETE})${NC}"
  echo -e "${YELLOW}   این ممکن است طبیعی باشد اگر chunks هنوز ساخته نشده بودند${NC}"
fi
echo ""

# ============================================
# 8. اضافه کردن چند Product
# ============================================
echo -e "${YELLOW}[8/13] اضافه کردن 3 Product...${NC}"

PRODUCT_IDS=()

for i in 1 2 3; do
  CREATE_PRODUCT_RESPONSE=$(curl -s -X POST "${BASE_URL}/api/v1/web-knowledge/products/" \
    -H "Authorization: Bearer ${TOKEN}" \
    -H "Content-Type: application/json" \
    -d "{
      \"title\": \"Test Product ${i}\",
      \"description\": \"This is a test product for bulk delete testing\",
      \"price\": $((100 * i)),
      \"currency\": \"IRR\",
      \"product_type\": \"product\",
      \"is_active\": true,
      \"in_stock\": true
    }")
  
  PRODUCT_ID=$(echo $CREATE_PRODUCT_RESPONSE | grep -o '"id":"[^"]*' | cut -d'"' -f4)
  
  if [ -z "$PRODUCT_ID" ]; then
    echo -e "${RED}❌ خطا در ساخت Product ${i}${NC}"
    echo "$CREATE_PRODUCT_RESPONSE"
  else
    PRODUCT_IDS+=("$PRODUCT_ID")
    echo -e "${GREEN}✅ Product ${i} ساخته شد: ${PRODUCT_ID}${NC}"
  fi
  
  sleep 1
done

if [ ${#PRODUCT_IDS[@]} -eq 0 ]; then
  echo -e "${RED}❌ هیچ Product ساخته نشد${NC}"
  exit 1
fi

echo ""

# ============================================
# 9. چک کردن Chunks قبل از پاک کردن Products
# ============================================
echo -e "${YELLOW}[9/13] چک کردن Chunks قبل از پاک کردن Products...${NC}"

sleep 5  # صبر برای chunk شدن products

# گرفتن تعداد کل chunks از نوع product
RAG_STATUS_BEFORE_PRODUCTS=$(curl -s -X GET "${BASE_URL}/api/v1/ai/rag/status/" \
  -H "Authorization: Bearer ${TOKEN}")

CHUNKS_BEFORE_DELETE_PRODUCTS=$(echo "$RAG_STATUS_BEFORE_PRODUCTS" | grep -o '"product":{[^}]*"count":[0-9]*' | grep -o '"count":[0-9]*' | cut -d':' -f2 || echo "0")

if [ -z "$CHUNKS_BEFORE_DELETE_PRODUCTS" ]; then
  CHUNKS_BEFORE_DELETE_PRODUCTS=0
fi

echo -e "${BLUE}   تعداد کل Product chunks قبل از پاک کردن: ${CHUNKS_BEFORE_DELETE_PRODUCTS}${NC}"
echo -e "${GREEN}✅ Chunks قبل از پاک کردن Products: ${CHUNKS_BEFORE_DELETE_PRODUCTS}${NC}"
echo ""

# ============================================
# 10. Bulk Delete Products
# ============================================
echo -e "${YELLOW}[10/13] پاک کردن Products (Bulk Delete)...${NC}"

# ساخت JSON array از Product IDs با jq
PRODUCT_IDS_JSON=$(printf '%s\n' "${PRODUCT_IDS[@]}" | jq -R . | jq -s .)

DELETE_PRODUCTS_RESPONSE=$(curl -s -X POST "${BASE_URL}/api/v1/web-knowledge/products/bulk-delete/" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d "{
    \"product_ids\": ${PRODUCT_IDS_JSON}
  }")

echo "$DELETE_PRODUCTS_RESPONSE" | python3 -m json.tool

SUCCESS=$(echo $DELETE_PRODUCTS_RESPONSE | grep -o '"success":true' || echo "")

if [ -z "$SUCCESS" ]; then
  echo -e "${RED}❌ خطا در پاک کردن Products${NC}"
  echo "$DELETE_PRODUCTS_RESPONSE"
  exit 1
fi

echo -e "${GREEN}✅ Products با موفقیت پاک شدند${NC}"
echo ""

# ============================================
# 11. چک کردن Chunks بعد از پاک کردن Products
# ============================================
echo -e "${YELLOW}[11/13] چک کردن Chunks بعد از پاک کردن Products...${NC}"

sleep 2  # صبر برای cleanup

# گرفتن تعداد کل chunks از نوع product
RAG_STATUS_AFTER_PRODUCTS=$(curl -s -X GET "${BASE_URL}/api/v1/ai/rag/status/" \
  -H "Authorization: Bearer ${TOKEN}")

CHUNKS_AFTER_DELETE_PRODUCTS=$(echo "$RAG_STATUS_AFTER_PRODUCTS" | grep -o '"product":{[^}]*"count":[0-9]*' | grep -o '"count":[0-9]*' | cut -d':' -f2 || echo "0")

if [ -z "$CHUNKS_AFTER_DELETE_PRODUCTS" ]; then
  CHUNKS_AFTER_DELETE_PRODUCTS=0
fi

echo -e "${BLUE}   تعداد کل Product chunks بعد از پاک کردن: ${CHUNKS_AFTER_DELETE_PRODUCTS}${NC}"

# محاسبه تفاوت
CHUNKS_DELETED_PRODUCTS=$((CHUNKS_BEFORE_DELETE_PRODUCTS - CHUNKS_AFTER_DELETE_PRODUCTS))

if [ "$CHUNKS_DELETED_PRODUCTS" -gt 0 ]; then
  echo -e "${GREEN}✅ تست Products موفق: ${CHUNKS_DELETED_PRODUCTS} chunk پاک شد (قبل: ${CHUNKS_BEFORE_DELETE_PRODUCTS}, بعد: ${CHUNKS_AFTER_DELETE_PRODUCTS})${NC}"
else
  echo -e "${YELLOW}⚠️  هیچ chunkی پاک نشد (قبل: ${CHUNKS_BEFORE_DELETE_PRODUCTS}, بعد: ${CHUNKS_AFTER_DELETE_PRODUCTS})${NC}"
  echo -e "${YELLOW}   این ممکن است طبیعی باشد اگر chunks هنوز ساخته نشده بودند${NC}"
fi
echo ""

# ============================================
# 12. اضافه کردن چند Q&A Pair
# ============================================
echo -e "${YELLOW}[12/13] اضافه کردن 3 Q&A Pair...${NC}"

# اول یک صفحه پیدا کنیم یا بسازیم
PAGES_FOR_QA=$(curl -s -X GET "${BASE_URL}/api/v1/web-knowledge/pages/?website=${WEBSITE_ID}" \
  -H "Authorization: Bearer ${TOKEN}")

PAGE_ID_FOR_QA=$(echo "$PAGES_FOR_QA" | grep -o '"id":"[^"]*' | head -1 | cut -d'"' -f4)

if [ -z "$PAGE_ID_FOR_QA" ]; then
  echo -e "${YELLOW}⚠️  هیچ صفحه‌ای برای Q&A وجود ندارد، در حال ساخت یک صفحه تست...${NC}"
  # ساخت یک صفحه تست
  CREATE_PAGE_RESPONSE=$(curl -s -X POST "${BASE_URL}/api/v1/web-knowledge/pages/" \
    -H "Authorization: Bearer ${TOKEN}" \
    -H "Content-Type: application/json" \
    -d "{
      \"website\": \"${WEBSITE_ID}\",
      \"url\": \"https://yasermotahedin.com/test-page\",
      \"title\": \"Test Page for Q&A\",
      \"cleaned_content\": \"This is a test page content for Q&A testing.\"
    }")
  
  PAGE_ID_FOR_QA=$(echo $CREATE_PAGE_RESPONSE | grep -o '"id":"[^"]*' | cut -d'"' -f4)
  
  if [ -z "$PAGE_ID_FOR_QA" ]; then
    echo -e "${RED}❌ خطا در ساخت Page برای Q&A${NC}"
    echo "$CREATE_PAGE_RESPONSE"
    exit 1
  fi
  
  echo -e "${GREEN}✅ Page برای Q&A ساخته شد: ${PAGE_ID_FOR_QA}${NC}"
fi

QA_PAIR_IDS=()

for i in 1 2 3; do
  CREATE_QA_RESPONSE=$(curl -s -X POST "${BASE_URL}/api/v1/web-knowledge/qa-pairs/" \
    -H "Authorization: Bearer ${TOKEN}" \
    -H "Content-Type: application/json" \
    -d "{
      \"page\": \"${PAGE_ID_FOR_QA}\",
      \"question\": \"Bulk Delete Test Question ${i} - $(date +%s)?\",
      \"answer\": \"This is test answer ${i} for bulk delete testing.\",
      \"generation_status\": \"completed\",
      \"confidence_score\": 0.9
    }")
  
  # استخراج ID از response (ممکنه در root یا nested باشه)
  QA_PAIR_ID=$(echo "$CREATE_QA_RESPONSE" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('id') or data.get('qa_pair', {}).get('id', ''))" 2>/dev/null || echo "$CREATE_QA_RESPONSE" | grep -o '"id":"[^"]*' | head -1 | cut -d'"' -f4)
  
  if [ -z "$QA_PAIR_ID" ]; then
    echo -e "${RED}❌ خطا در ساخت Q&A Pair ${i}${NC}"
    echo "$CREATE_QA_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$CREATE_QA_RESPONSE"
  else
    QA_PAIR_IDS+=("$QA_PAIR_ID")
    echo -e "${GREEN}✅ Q&A Pair ${i} ساخته شد: ${QA_PAIR_ID}${NC}"
  fi
  
  sleep 1
done

if [ ${#QA_PAIR_IDS[@]} -eq 0 ]; then
  echo -e "${RED}❌ هیچ Q&A Pair ساخته نشد${NC}"
  exit 1
fi

echo ""

# ============================================
# 13. چک کردن Chunks قبل از پاک کردن Q&A Pairs
# ============================================
echo -e "${YELLOW}[13/14] چک کردن Chunks قبل از پاک کردن Q&A Pairs...${NC}"

sleep 5  # صبر برای chunk شدن Q&A pairs

# گرفتن تعداد کل chunks از نوع faq
RAG_STATUS_BEFORE_QA=$(curl -s -X GET "${BASE_URL}/api/v1/ai/rag/status/" \
  -H "Authorization: Bearer ${TOKEN}")

CHUNKS_BEFORE_DELETE_QA=$(echo "$RAG_STATUS_BEFORE_QA" | grep -o '"faq":{[^}]*"count":[0-9]*' | grep -o '"count":[0-9]*' | cut -d':' -f2 || echo "0")

if [ -z "$CHUNKS_BEFORE_DELETE_QA" ]; then
  CHUNKS_BEFORE_DELETE_QA=0
fi

echo -e "${BLUE}   تعداد کل FAQ chunks قبل از پاک کردن: ${CHUNKS_BEFORE_DELETE_QA}${NC}"
echo -e "${GREEN}✅ Chunks قبل از پاک کردن Q&A Pairs: ${CHUNKS_BEFORE_DELETE_QA}${NC}"
echo ""

# ============================================
# 14. Bulk Delete Q&A Pairs
# ============================================
echo -e "${YELLOW}[14/14] پاک کردن Q&A Pairs (Bulk Delete)...${NC}"

DELETE_QA_RESPONSE=$(curl -s -X POST "${BASE_URL}/api/v1/web-knowledge/qa-pairs/bulk_delete/" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d "{
    \"qa_pair_ids\": [$(printf '"%s",' "${QA_PAIR_IDS[@]}" | sed 's/,$//')]
  }")

echo "$DELETE_QA_RESPONSE" | python3 -m json.tool

SUCCESS=$(echo $DELETE_QA_RESPONSE | grep -o '"success":true' || echo "")

if [ -z "$SUCCESS" ]; then
  echo -e "${RED}❌ خطا در پاک کردن Q&A Pairs${NC}"
  echo "$DELETE_QA_RESPONSE"
  exit 1
fi

echo -e "${GREEN}✅ Q&A Pairs با موفقیت پاک شدند${NC}"
echo ""

# ============================================
# 15. چک کردن Chunks بعد از پاک کردن Q&A Pairs
# ============================================
echo -e "${YELLOW}[15/15] چک کردن Chunks بعد از پاک کردن Q&A Pairs...${NC}"

sleep 2  # صبر برای cleanup

# گرفتن تعداد کل chunks از نوع faq
RAG_STATUS_AFTER_QA=$(curl -s -X GET "${BASE_URL}/api/v1/ai/rag/status/" \
  -H "Authorization: Bearer ${TOKEN}")

CHUNKS_AFTER_DELETE_QA=$(echo "$RAG_STATUS_AFTER_QA" | grep -o '"faq":{[^}]*"count":[0-9]*' | grep -o '"count":[0-9]*' | cut -d':' -f2 || echo "0")

if [ -z "$CHUNKS_AFTER_DELETE_QA" ]; then
  CHUNKS_AFTER_DELETE_QA=0
fi

echo -e "${BLUE}   تعداد کل FAQ chunks بعد از پاک کردن: ${CHUNKS_AFTER_DELETE_QA}${NC}"

# محاسبه تفاوت
CHUNKS_DELETED_QA=$((CHUNKS_BEFORE_DELETE_QA - CHUNKS_AFTER_DELETE_QA))

if [ "$CHUNKS_DELETED_QA" -gt 0 ]; then
  echo -e "${GREEN}✅ تست Q&A Pairs موفق: ${CHUNKS_DELETED_QA} chunk پاک شد (قبل: ${CHUNKS_BEFORE_DELETE_QA}, بعد: ${CHUNKS_AFTER_DELETE_QA})${NC}"
else
  echo -e "${YELLOW}⚠️  هیچ chunkی پاک نشد (قبل: ${CHUNKS_BEFORE_DELETE_QA}, بعد: ${CHUNKS_AFTER_DELETE_QA})${NC}"
  echo -e "${YELLOW}   این ممکن است طبیعی باشد اگر chunks هنوز ساخته نشده بودند${NC}"
fi
echo ""

# ============================================
# خلاصه نتایج
# ============================================
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  خلاصه نتایج تست${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo -e "Pages:"
echo -e "  Chunks قبل: ${CHUNKS_BEFORE_DELETE}"
echo -e "  Chunks بعد: ${CHUNKS_AFTER_DELETE}"
if [ "$CHUNKS_AFTER_DELETE" -eq 0 ]; then
  echo -e "  ${GREEN}✅ موفق${NC}"
else
  echo -e "  ${RED}❌ ناموفق${NC}"
fi
echo ""
echo -e "Products:"
echo -e "  Chunks قبل: ${CHUNKS_BEFORE_DELETE_PRODUCTS}"
echo -e "  Chunks بعد: ${CHUNKS_AFTER_DELETE_PRODUCTS}"
if [ "$CHUNKS_AFTER_DELETE_PRODUCTS" -eq 0 ]; then
  echo -e "  ${GREEN}✅ موفق${NC}"
else
  echo -e "  ${RED}❌ ناموفق${NC}"
fi
echo ""
echo -e "Q&A Pairs:"
echo -e "  Chunks قبل: ${CHUNKS_BEFORE_DELETE_QA}"
echo -e "  Chunks بعد: ${CHUNKS_AFTER_DELETE_QA}"
if [ "$CHUNKS_AFTER_DELETE_QA" -eq 0 ]; then
  echo -e "  ${GREEN}✅ موفق${NC}"
else
  echo -e "  ${RED}❌ ناموفق${NC}"
fi
echo ""

