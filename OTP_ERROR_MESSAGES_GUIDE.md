# 🎯 OTP Error Messages - Complete Guide

## ✅ **IMPROVED ERROR HANDLING**

All OTP errors now show **clear, specific messages** instead of generic "Failed to send OTP" errors.

---

## 📋 All Error Scenarios

### 1️⃣ Success Response

**Request:**
```bash
curl -X POST http://localhost:8000/api/v1/usr/otp \
  -H "Content-Type: application/json" \
  -d '{"phone_number": "+989123456789"}'
```

**Response: `200 OK`**
```json
{
  "phone_number": "+989123456789",
  "message": "OTP sent successfully",
  "expires_in": 300
}
```

---

### 2️⃣ Rate Limit Error (NEW - CLEAR MESSAGE!)

**Request:** (second request within 5 minutes)
```bash
curl -X POST http://localhost:8000/api/v1/usr/otp \
  -H "Content-Type: application/json" \
  -d '{"phone_number": "+989123456789"}'
```

**Response: `429 TOO MANY REQUESTS`** ⭐ **IMPROVED!**
```json
{
  "detail": "Too many OTP requests. Please wait 4 minute(s) and 30 second(s) before requesting a new OTP."
}
```

**Before (BAD):**
```json
{
  "detail": "Failed to send OTP. Please try again."  // ❌ Not clear!
}
```

**After (GOOD):**
```json
{
  "detail": "Too many OTP requests. Please wait 4 minute(s) and 30 second(s) before requesting a new OTP."  // ✅ Crystal clear!
}
```

---

### 3️⃣ Invalid Phone Number

**Request:**
```bash
curl -X POST http://localhost:8000/api/v1/usr/otp \
  -H "Content-Type: application/json" \
  -d '{"phone_number": "123456"}'
```

**Response: `400 BAD REQUEST`**
```json
{
  "phone_number": [
    "Please provide a valid Iranian phone number starting with +98 or 09"
  ]
}
```

---

### 4️⃣ Missing Phone Number

**Request:**
```bash
curl -X POST http://localhost:8000/api/v1/usr/otp \
  -H "Content-Type: application/json" \
  -d '{}'
```

**Response: `400 BAD REQUEST`**
```json
{
  "phone_number": [
    "This field is required."
  ]
}
```

---

### 5️⃣ SMS Service Not Configured

**Response: `500 INTERNAL SERVER ERROR`**
```json
{
  "detail": "Failed to send OTP. Please try again later."
}
```

*Note: This happens if `KAVENEGAR_API_KEY` is not set*

---

### 6️⃣ Kavenegar Sender Invalid (Error 412)

**Response: `400 BAD REQUEST`**
```json
{
  "detail": "Sender number is invalid. Please contact support."
}
```

*Note: This is handled by verify_lookup fallback now*

---

### 7️⃣ Insufficient Credit

**Response: `400 BAD REQUEST`**
```json
{
  "detail": "Insufficient credit. Please contact support."
}
```

---

## 🎯 HTTP Status Codes

| Code | Meaning | When |
|------|---------|------|
| **200** | Success | OTP sent successfully |
| **400** | Bad Request | Invalid phone, missing fields |
| **429** | Too Many Requests | ⭐ **Rate limit exceeded** |
| **500** | Server Error | SMS service issues, unexpected errors |

---

## 🔄 What Changed?

### ✅ Rate Limit Error Now Shows:

**Before:**
- ❌ Generic message: "Failed to send OTP. Please try again."
- ❌ Status: 500 or 400 (unclear)
- ❌ No countdown information

**After:**
- ✅ Specific message: "Too many OTP requests. Please wait X minute(s) and Y second(s)..."
- ✅ Status: 429 (standard for rate limiting)
- ✅ Clear countdown time

### Implementation Changes:

1. **Moved rate limit check to `validate()` method** - Now caught properly by `is_valid()`
2. **View handles rate limit separately** - Returns 429 status code
3. **Clear error message format** - Shows exact wait time

---

## 🧪 Test Error Messages

### Quick Test Script:
```bash
bash test_otp_error_messages.sh
```

### Manual Testing:

```bash
# Test 1: Success
curl -X POST http://localhost:8000/api/v1/usr/otp \
  -H "Content-Type: application/json" \
  -d '{"phone_number": "+989123456789"}'
# Expected: 200 OK

# Test 2: Rate limit
curl -X POST http://localhost:8000/api/v1/usr/otp \
  -H "Content-Type: application/json" \
  -d '{"phone_number": "+989123456789"}'
# Expected: 429 with clear countdown message

# Test 3: Invalid phone
curl -X POST http://localhost:8000/api/v1/usr/otp \
  -H "Content-Type: application/json" \
  -d '{"phone_number": "123"}'
# Expected: 400 with validation error
```

---

## 📱 Frontend Error Handling

### React Example:

```jsx
async function sendOTP(phoneNumber) {
  try {
    const response = await fetch('/api/v1/usr/otp', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ phone_number: phoneNumber })
    });
    
    const data = await response.json();
    
    if (response.ok) {
      // Success
      alert('OTP sent successfully!');
      return { success: true };
    }
    
    // Handle different error types
    switch (response.status) {
      case 429:
        // Rate limit - show clear message with countdown
        alert(data.detail);  // "Too many OTP requests. Please wait..."
        // Extract time and show countdown
        showRateLimitMessage(data.detail);
        break;
        
      case 400:
        // Validation error
        if (data.phone_number) {
          alert(`Invalid phone: ${data.phone_number[0]}`);
        } else {
          alert(data.detail || 'Invalid request');
        }
        break;
        
      case 500:
        // Server error
        alert('Service temporarily unavailable. Please try again later.');
        break;
        
      default:
        alert('Failed to send OTP. Please try again.');
    }
    
    return { success: false, error: data };
    
  } catch (error) {
    console.error('Network error:', error);
    alert('Network error. Please check your connection.');
    return { success: false, error };
  }
}

function showRateLimitMessage(message) {
  // Extract time from message
  // "Too many OTP requests. Please wait 4 minute(s) and 30 second(s)..."
  const match = message.match(/wait (\d+) minute\(s\) and (\d+) second\(s\)/);
  if (match) {
    const minutes = parseInt(match[1]);
    const seconds = parseInt(match[2]);
    const totalSeconds = minutes * 60 + seconds;
    
    // Start countdown
    startCountdown(totalSeconds);
  }
}
```

### JavaScript/Vanilla Example:

```javascript
async function sendOTP(phone) {
  const response = await fetch('/api/v1/usr/otp', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ phone_number: phone })
  });
  
  const data = await response.json();
  
  if (response.status === 429) {
    // Rate limit error - extract exact wait time
    document.getElementById('error').textContent = data.detail;
    document.getElementById('send-btn').disabled = true;
    
    // Parse time and show countdown
    parseAndShowCountdown(data.detail);
  } else if (!response.ok) {
    // Other errors
    const errorMsg = data.detail || 
                    data.phone_number?.[0] || 
                    'Failed to send OTP';
    document.getElementById('error').textContent = errorMsg;
  } else {
    // Success
    document.getElementById('success').textContent = data.message;
  }
}
```

---

## 🎨 User-Friendly Display

### Error Message Formatting:

**Backend sends:**
```
"Too many OTP requests. Please wait 4 minute(s) and 30 second(s) before requesting a new OTP."
```

**Frontend can display as:**
```
⏱️ Please wait 4:30 before requesting a new code
```

Or with countdown:
```
⏱️ You can request a new code in 4:30
⏱️ You can request a new code in 4:29
⏱️ You can request a new code in 4:28
...
```

---

## 📊 Error Message Summary Table

| Error Type | Status | Message Format | Action |
|------------|--------|----------------|--------|
| **Rate Limited** | 429 | "Too many OTP requests. Wait X min Y sec" | Show countdown |
| **Invalid Phone** | 400 | "Please provide valid Iranian phone number" | Fix phone format |
| **Missing Phone** | 400 | "This field is required" | Add phone number |
| **Service Error** | 500 | "Failed to send OTP. Try again later" | Retry later |
| **Success** | 200 | "OTP sent successfully" | Proceed to verify |

---

## 🔧 Files Modified

| File | Change |
|------|--------|
| `src/accounts/serializers/otp.py` | ✅ Moved rate check to `validate()` |
| `src/accounts/api/otp.py` | ✅ Returns 429 for rate limits |
| | ✅ Clear error message handling |
| `test_otp_error_messages.sh` | ✅ Test script for errors |

---

## ✅ Before & After Comparison

### Scenario: User tries to send OTP twice

**Before:**
```json
// ❌ Unclear, generic error
{
  "detail": "Failed to send OTP. Please try again."
}
```
*User thinks: "What failed? Should I retry? System broken?"*

**After:**
```json
// ✅ Clear, actionable error
{
  "detail": "Too many OTP requests. Please wait 4 minute(s) and 30 second(s) before requesting a new OTP."
}
```
*User thinks: "Oh, I need to wait. I'll check back in 4.5 minutes."*

---

## 💡 Key Improvements

1. ✅ **Specific error messages** - No more generic "Failed to send OTP"
2. ✅ **Proper HTTP status codes** - 429 for rate limiting
3. ✅ **Exact countdown time** - User knows how long to wait
4. ✅ **Better UX** - Clear, actionable messages
5. ✅ **Frontend friendly** - Easy to parse and display

---

## 🚀 Try It Now

```bash
# Run the test script
bash test_otp_error_messages.sh

# Or test manually
curl -X POST http://localhost:8000/api/v1/usr/otp \
  -H "Content-Type: application/json" \
  -d '{"phone_number": "+989123456789"}'

# Try again immediately - you'll see the clear rate limit message!
curl -X POST http://localhost:8000/api/v1/usr/otp \
  -H "Content-Type: application/json" \
  -d '{"phone_number": "+989123456789"}'
```

---

**Error messages are now crystal clear! 🎉**

