#!/bin/bash

# Test script to clear customer tags directly via API
# This will help us see if the backend is working correctly

# Configuration
BASE_URL="${BASE_URL:-http://localhost:8000}"
CUSTOMER_ID="${CUSTOMER_ID:-6}"

echo "=========================================="
echo "Testing Customer Tag Clear via API"
echo "=========================================="
echo ""
echo "Please provide your JWT token:"
read -r TOKEN

if [ -z "$TOKEN" ]; then
    echo "Error: Token is required"
    exit 1
fi

# Test 1: Get current customer
echo ""
echo "1. Getting current customer data..."
curl -s -X GET \
  "${BASE_URL}/api/v1/message/customer-item/${CUSTOMER_ID}/" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" | python3 -m json.tool

# Test 2: Clear tags with empty array
echo ""
echo "2. Clearing tags (sending empty array)..."
echo "Request body: {\"tag_ids\": []}"
RESPONSE=$(curl -s -w "\nHTTP_STATUS:%{http_code}" -X PATCH \
  "${BASE_URL}/api/v1/message/customer-item/${CUSTOMER_ID}/" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"tag_ids": []}')

HTTP_STATUS=$(echo "$RESPONSE" | grep "HTTP_STATUS" | cut -d':' -f2)
BODY=$(echo "$RESPONSE" | sed '/HTTP_STATUS/d')

echo "HTTP Status: $HTTP_STATUS"
echo "Response:"
echo "$BODY" | python3 -m json.tool 2>/dev/null || echo "$BODY"

if [ "$HTTP_STATUS" = "200" ]; then
    echo ""
    echo "✅ SUCCESS! Tags cleared successfully"
else
    echo ""
    echo "❌ FAILED! Status code: $HTTP_STATUS"
fi

echo ""
echo "=========================================="
echo "Test completed"
echo "=========================================="

