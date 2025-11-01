#!/bin/bash
# Test OTP error messages

echo "======================================================================"
echo "Testing OTP Error Messages"
echo "======================================================================"

PHONE="+989123456789"
API_URL="http://localhost:8000/api/v1/usr/otp"

echo -e "\n📋 Test 1: First OTP request (should succeed)"
echo "----------------------------------------------------------------------"
curl -X POST "$API_URL" \
  -H "Content-Type: application/json" \
  -d "{\"phone_number\": \"$PHONE\"}" \
  -w "\nHTTP Status: %{http_code}\n" \
  -s | jq '.'

echo -e "\n⏱️  Test 2: Immediate second request (should show clear rate limit error)"
echo "----------------------------------------------------------------------"
echo "Expected: 429 Too Many Requests with clear message"
curl -X POST "$API_URL" \
  -H "Content-Type: application/json" \
  -d "{\"phone_number\": \"$PHONE\"}" \
  -w "\nHTTP Status: %{http_code}\n" \
  -s | jq '.'

echo -e "\n📱 Test 3: Invalid phone number (should show validation error)"
echo "----------------------------------------------------------------------"
curl -X POST "$API_URL" \
  -H "Content-Type: application/json" \
  -d '{"phone_number": "123456"}' \
  -w "\nHTTP Status: %{http_code}\n" \
  -s | jq '.'

echo -e "\n======================================================================"
echo "✅ Test Complete!"
echo "======================================================================"
echo ""
echo "Expected Results:"
echo "  Test 1: HTTP 200 - OTP sent successfully"
echo "  Test 2: HTTP 429 - Clear rate limit message with countdown"
echo "  Test 3: HTTP 400 - Invalid phone number format"
echo ""

