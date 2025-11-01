# ✅ OTP Rate Limiting - IMPLEMENTED

## 🎯 Problem Solved

**Issue:** Users could request OTP multiple times without limit

**Solution:** Now users can only request OTP **once every 5 minutes** per phone number

---

## 🔒 What Changed

### Before:
```json
// User could spam OTP requests
Request 1 ✅ → OTP sent
Request 2 ✅ → OTP sent  
Request 3 ✅ → OTP sent
... (unlimited)
```

### After:
```json
// Strict 5-minute wait between requests
Request 1 ✅ → OTP sent
Request 2 ❌ → "Please wait 4 minute(s) and 58 second(s)..."
... wait 5 minutes ...
Request 3 ✅ → OTP sent
```

---

## 📋 Implementation Details

### 1. Rate Limiting Logic (`serializers/otp.py`)

```python
# Check most recent OTP for phone number
last_otp = OTPToken.objects.filter(
    phone_number=phone_number
).order_by('-created_at').first()

# If exists and within wait time
if last_otp:
    time_since = now - last_otp.created_at
    if time_since < 5 minutes:
        # Block and show exact wait time
        raise ValidationError({
            'detail': 'Please wait X minutes and Y seconds...',
            'retry_after': remaining_seconds
        })
```

### 2. Configuration (`settings/common.py`)

```python
OTP_RESEND_WAIT_TIME = 300  # 5 minutes (configurable)
```

### 3. API Response

**Blocked Request:**
```json
{
  "detail": "Please wait 4 minute(s) and 30 second(s) before requesting a new OTP.",
  "retry_after": 270
}
```

**Success:**
```json
{
  "phone_number": "+989123456789",
  "message": "OTP sent successfully",
  "expires_in": 300
}
```

---

## 🧪 Testing

### Test 1: Via API
```bash
# First request - should succeed
curl -X POST http://localhost:8000/api/v1/usr/otp \
  -H "Content-Type: application/json" \
  -d '{"phone_number": "+989123456789"}'

# Immediate second request - should fail
curl -X POST http://localhost:8000/api/v1/usr/otp \
  -H "Content-Type: application/json" \
  -d '{"phone_number": "+989123456789"}'
```

### Test 2: Run Test Script
```bash
python test_otp_rate_limit.py
```

Expected output:
```
✅ First OTP: Allowed
✅ Immediate retry: Blocked (must wait 5 minutes)
✅ After 5 minutes: Allowed
```

---

## 🎨 Frontend Example

```javascript
async function sendOTP(phone) {
  const response = await fetch('/api/v1/usr/otp', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ phone_number: phone })
  });
  
  const data = await response.json();
  
  if (!response.ok) {
    // Show countdown timer with remaining time
    if (data.retry_after) {
      startCountdown(data.retry_after);
    }
    alert(data.detail);
  }
}

function startCountdown(seconds) {
  const interval = setInterval(() => {
    seconds--;
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    
    document.getElementById('btn').textContent = 
      `Wait ${mins}:${secs.toString().padStart(2, '0')}`;
    
    if (seconds <= 0) {
      clearInterval(interval);
      document.getElementById('btn').textContent = 'Send OTP';
      document.getElementById('btn').disabled = false;
    }
  }, 1000);
}
```

---

## ⚙️ Configuration

### Change Wait Time

**2 minutes:**
```bash
# .env
OTP_RESEND_WAIT_TIME=120
```

**10 minutes:**
```bash
# .env
OTP_RESEND_WAIT_TIME=600
```

**30 seconds (development only):**
```bash
# .env.development
OTP_RESEND_WAIT_TIME=30
```

---

## 🔒 Security Benefits

| Benefit | Description |
|---------|-------------|
| **Anti-Spam** | Prevents flooding phone numbers |
| **Cost Control** | Limits SMS costs |
| **Better UX** | Clear wait times |
| **API Protection** | Reduces load |
| **Abuse Prevention** | Makes attacks impractical |

---

## 📊 Files Modified

| File | Changes |
|------|---------|
| `src/accounts/serializers/otp.py` | ✅ Added rate limiting check |
| `src/accounts/api/otp.py` | ✅ Updated API docs |
| `src/core/settings/common.py` | ✅ Added `OTP_RESEND_WAIT_TIME` |
| `docs/OTP_RATE_LIMITING.md` | ✅ Complete documentation |
| `test_otp_rate_limit.py` | ✅ Test script |

---

## ✅ Features

- [x] **5-minute wait** between OTP requests
- [x] **Exact countdown** shown to user
- [x] **Configurable** via environment variables
- [x] **Clear error messages** with remaining time
- [x] **API documentation** updated
- [x] **Test script** provided
- [x] **Frontend examples** included

---

## 📚 Documentation

- **Complete Guide:** `docs/OTP_RATE_LIMITING.md`
- **API Docs:** `/api/v1/usr/otp` endpoint
- **Test Script:** `test_otp_rate_limit.py`

---

## 🚀 Try It Now

```bash
# Test the rate limiting
curl -X POST http://localhost:8000/api/v1/usr/otp \
  -H "Content-Type: application/json" \
  -d '{"phone_number": "+989123456789"}'

# Try again immediately (should be blocked)
curl -X POST http://localhost:8000/api/v1/usr/otp \
  -H "Content-Type: application/json" \
  -d '{"phone_number": "+989123456789"}'
```

**Second request will return:**
```json
{
  "detail": "Please wait 4 minute(s) and 59 second(s) before requesting a new OTP.",
  "retry_after": 299
}
```

---

## 💡 Key Points

1. ✅ **One OTP per 5 minutes** per phone number
2. ✅ **Exact countdown** in error message
3. ✅ **`retry_after` field** for countdown timers
4. ✅ **Configurable** wait time
5. ✅ **Production ready**

---

**Problem solved! Users can now only request OTP once every 5 minutes.** 🎉

