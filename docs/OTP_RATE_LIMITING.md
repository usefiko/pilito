# OTP Rate Limiting

## 🔒 Overview

The OTP system now enforces strict rate limiting to prevent abuse:
- **Users can request OTP only once every 5 minutes per phone number**
- Clear error messages show exact wait time remaining
- Configurable via environment variables

---

## ⚙️ Configuration

### Default Settings

In `src/core/settings/common.py`:
```python
OTP_RESEND_WAIT_TIME = 300  # 5 minutes (in seconds)
OTP_EXPIRY_TIME = 300       # 5 minutes (in seconds)
OTP_MAX_ATTEMPTS = 3         # Maximum verification attempts
```

### Environment Variables

You can customize these in your `.env` file:

```bash
# Time to wait before requesting new OTP (in seconds)
OTP_RESEND_WAIT_TIME=300  # 5 minutes (default)

# How long OTP code is valid (in seconds)
OTP_EXPIRY_TIME=300       # 5 minutes (default)

# Maximum attempts to verify OTP
OTP_MAX_ATTEMPTS=3        # 3 attempts (default)
```

---

## 🚦 How It Works

### First Request (✅ Success)
```bash
curl -X POST http://localhost:8000/api/v1/usr/otp \
  -H "Content-Type: application/json" \
  -d '{"phone_number": "+989123456789"}'
```

**Response:**
```json
{
  "phone_number": "+989123456789",
  "message": "OTP sent successfully",
  "expires_in": 300
}
```

### Second Request within 5 minutes (❌ Blocked)
```bash
# Try again immediately
curl -X POST http://localhost:8000/api/v1/usr/otp \
  -H "Content-Type: application/json" \
  -d '{"phone_number": "+989123456789"}'
```

**Response:**
```json
{
  "detail": "Please wait 4 minute(s) and 30 second(s) before requesting a new OTP.",
  "retry_after": 270
}
```

### After 5 minutes (✅ Allowed)
```bash
# Wait 5 minutes, then try again
curl -X POST http://localhost:8000/api/v1/usr/otp \
  -H "Content-Type: application/json" \
  -d '{"phone_number": "+989123456789"}'
```

**Response:**
```json
{
  "phone_number": "+989123456789",
  "message": "OTP sent successfully",
  "expires_in": 300
}
```

---

## 📊 Rate Limiting Rules

| Rule | Description | Default |
|------|-------------|---------|
| **Per Phone** | 1 OTP per phone number | 5 minutes |
| **Per IP** | 5 requests per minute (any phone) | 5 req/min |
| **Verification Attempts** | Max attempts to verify OTP | 3 attempts |
| **OTP Validity** | How long OTP is valid | 5 minutes |

---

## 🎯 Frontend Integration

### JavaScript Example

```javascript
async function sendOTP(phoneNumber) {
  try {
    const response = await fetch('/api/v1/usr/otp', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ phone_number: phoneNumber })
    });
    
    const data = await response.json();
    
    if (response.ok) {
      console.log('OTP sent successfully!');
      console.log(`Valid for ${data.expires_in} seconds`);
      return { success: true, data };
    } else {
      // Handle rate limit error
      if (data.retry_after) {
        const minutes = Math.floor(data.retry_after / 60);
        const seconds = data.retry_after % 60;
        console.error(`Rate limited. Wait ${minutes}m ${seconds}s`);
        
        // Show countdown to user
        showCountdown(data.retry_after);
      }
      return { success: false, error: data.detail };
    }
  } catch (error) {
    console.error('Network error:', error);
    return { success: false, error: 'Network error' };
  }
}

// Optional: Show countdown timer
function showCountdown(seconds) {
  const interval = setInterval(() => {
    seconds--;
    const minutes = Math.floor(seconds / 60);
    const secs = seconds % 60;
    
    document.getElementById('countdown').textContent = 
      `Please wait ${minutes}:${secs.toString().padStart(2, '0')}`;
    
    if (seconds <= 0) {
      clearInterval(interval);
      document.getElementById('countdown').textContent = 
        'You can request a new OTP now';
    }
  }, 1000);
}
```

### React Example

```jsx
import { useState, useEffect } from 'react';

function OTPForm() {
  const [phoneNumber, setPhoneNumber] = useState('');
  const [countdown, setCountdown] = useState(0);
  const [message, setMessage] = useState('');
  
  // Countdown timer effect
  useEffect(() => {
    if (countdown > 0) {
      const timer = setTimeout(() => setCountdown(countdown - 1), 1000);
      return () => clearTimeout(timer);
    }
  }, [countdown]);
  
  const handleSendOTP = async () => {
    try {
      const response = await fetch('/api/v1/usr/otp', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ phone_number: phoneNumber })
      });
      
      const data = await response.json();
      
      if (response.ok) {
        setMessage('OTP sent successfully!');
        setCountdown(data.expires_in);
      } else {
        setMessage(data.detail);
        if (data.retry_after) {
          setCountdown(data.retry_after);
        }
      }
    } catch (error) {
      setMessage('Failed to send OTP. Please try again.');
    }
  };
  
  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };
  
  return (
    <div>
      <input
        type="tel"
        value={phoneNumber}
        onChange={(e) => setPhoneNumber(e.target.value)}
        placeholder="+989123456789"
      />
      <button
        onClick={handleSendOTP}
        disabled={countdown > 0}
      >
        {countdown > 0 ? `Wait ${formatTime(countdown)}` : 'Send OTP'}
      </button>
      {message && <p>{message}</p>}
    </div>
  );
}
```

---

## 🔧 Customization Examples

### 1. Shorter Wait Time (2 minutes)
```bash
# .env
OTP_RESEND_WAIT_TIME=120  # 2 minutes
```

### 2. Longer Wait Time (10 minutes)
```bash
# .env
OTP_RESEND_WAIT_TIME=600  # 10 minutes
```

### 3. Development Mode (30 seconds)
```bash
# .env.development
OTP_RESEND_WAIT_TIME=30  # 30 seconds for testing
```

---

## 🧪 Testing Rate Limiting

### Test Script

```bash
#!/bin/bash
# test_rate_limit.sh

PHONE="+989123456789"

echo "Test 1: First request (should succeed)"
curl -X POST http://localhost:8000/api/v1/usr/otp \
  -H "Content-Type: application/json" \
  -d "{\"phone_number\": \"$PHONE\"}"

echo -e "\n\nTest 2: Immediate second request (should fail)"
curl -X POST http://localhost:8000/api/v1/usr/otp \
  -H "Content-Type: application/json" \
  -d "{\"phone_number\": \"$PHONE\"}"

echo -e "\n\nTest 3: After 5 minutes (should succeed)"
echo "Wait 5 minutes, then run:"
echo "curl -X POST http://localhost:8000/api/v1/usr/otp \\"
echo "  -H \"Content-Type: application/json\" \\"
echo "  -d '{\"phone_number\": \"$PHONE\"}'"
```

### Manual Test

```bash
# Terminal 1: Send first OTP
curl -X POST http://localhost:8000/api/v1/usr/otp \
  -H "Content-Type: application/json" \
  -d '{"phone_number": "+989123456789"}'

# Expected: Success ✅

# Terminal 2: Try immediately again
curl -X POST http://localhost:8000/api/v1/usr/otp \
  -H "Content-Type: application/json" \
  -d '{"phone_number": "+989123456789"}'

# Expected: Rate limit error with countdown ❌
```

---

## 📋 Error Response Format

### Rate Limit Error
```json
{
  "detail": "Please wait 4 minute(s) and 30 second(s) before requesting a new OTP.",
  "retry_after": 270
}
```

**Fields:**
- `detail`: Human-readable error message
- `retry_after`: Seconds to wait before retry (useful for countdown timers)

---

## 🔒 Security Benefits

1. **Prevents Spam:** Users can't flood phone numbers with OTPs
2. **Cost Control:** Limits SMS costs from abuse
3. **Better UX:** Clear wait times instead of confusing errors
4. **API Protection:** Reduces load on SMS service
5. **Abuse Prevention:** Makes automated attacks impractical

---

## 📊 Monitoring

### Check Recent OTP Requests

```python
# Django shell
from accounts.models import OTPToken
from django.utils import timezone
from datetime import timedelta

# OTPs sent in last hour
recent = OTPToken.objects.filter(
    created_at__gte=timezone.now() - timedelta(hours=1)
)
print(f"OTPs sent in last hour: {recent.count()}")

# Top phone numbers
from django.db.models import Count
top_phones = OTPToken.objects.values('phone_number').annotate(
    count=Count('id')
).order_by('-count')[:10]
print("Top 10 phone numbers:")
for phone in top_phones:
    print(f"  {phone['phone_number']}: {phone['count']} requests")
```

### Admin Panel

View all OTP requests:
👉 http://localhost:8000/admin/accounts/otptoken/

---

## 💡 Best Practices

1. **Show Countdown:** Display remaining wait time to users
2. **Disable Button:** Disable "Send OTP" button during countdown
3. **Clear Messages:** Show exact wait time in error messages
4. **Store Timestamp:** Save last OTP request time in frontend
5. **Handle Errors:** Properly catch and display rate limit errors

---

## 🆘 Troubleshooting

### Issue: Users complaining they can't get OTP

**Check:**
1. How much time since last request?
2. Is `OTP_RESEND_WAIT_TIME` too long?
3. Are there old OTP records blocking?

**Solution:**
```python
# Clear old OTPs for a phone number
from accounts.models import OTPToken
OTPToken.objects.filter(phone_number='+989123456789').delete()
```

### Issue: Rate limit too strict for development

**Solution:**
```bash
# .env.development
OTP_RESEND_WAIT_TIME=30  # 30 seconds instead of 5 minutes
```

---

## 📚 Related Documentation

- [OTP Quick Start](./OTP_QUICK_START.md)
- [OTP Authentication](./OTP_AUTHENTICATION.md)
- [OTP Troubleshooting](./OTP_TROUBLESHOOTING.md)

---

**Last Updated:** November 1, 2025

