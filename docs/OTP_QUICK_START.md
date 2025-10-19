# OTP Authentication - Quick Start Guide

## 🚀 Quick Setup (5 minutes)

### 1. Environment Setup
Add to your `.env` file:
```bash
KAVENEGAR_API_KEY=your_kavenegar_api_key
KAVENEGAR_SENDER=10008663
```

### 2. Install & Migrate
```bash
pip install kavenegar==1.1.2
cd src
python manage.py migrate accounts
```

### 3. Test It!

**Send OTP:**
```bash
curl -X POST http://localhost:8000/api/v1/usr/otp \
  -H "Content-Type: application/json" \
  -d '{"phone_number": "+989123456789"}'
```

**Check OTP Code:**
- Admin Panel: http://localhost:8000/admin/accounts/otptoken/

**Verify OTP:**
```bash
curl -X POST http://localhost:8000/api/v1/usr/otp/verify \
  -H "Content-Type: application/json" \
  -d '{"phone_number": "+989123456789", "code": "YOUR_CODE"}'
```

## 📍 API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/v1/usr/otp` | POST | Send OTP code |
| `/api/v1/usr/otp/verify` | POST | Verify OTP & login |

## ⚙️ Configuration Options

```python
# In your .env file
OTP_EXPIRY_TIME=300      # 5 minutes (in seconds)
OTP_MAX_ATTEMPTS=3       # Maximum verification attempts
```

## 🔒 Security Features

- ✅ Rate limiting (5 req/min per IP)
- ✅ Phone rate limiting (3 OTP/2min per phone)
- ✅ Auto-expiration (5 minutes)
- ✅ Limited attempts (3 tries)
- ✅ Single-use tokens
- ✅ JWT token generation

## 📱 Frontend Integration

```javascript
// Send OTP
const sendOTP = async (phone) => {
  const res = await fetch('/api/v1/usr/otp', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ phone_number: phone })
  });
  return res.json();
};

// Verify OTP
const verifyOTP = async (phone, code) => {
  const res = await fetch('/api/v1/usr/otp/verify', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ phone_number: phone, code })
  });
  const data = await res.json();
  
  // Save tokens
  localStorage.setItem('access_token', data.access_token);
  localStorage.setItem('refresh_token', data.refresh_token);
  
  return data;
};
```

## 🐛 Common Issues

| Issue | Solution |
|-------|----------|
| "SMS service is not configured" | Set `KAVENEGAR_API_KEY` in `.env` |
| "Too many OTP requests" | Wait 2 minutes |
| "Invalid OTP code" | Check code is recent & not expired |
| "Failed to send OTP" | Check API key & Kavenegar credit |

## 📊 Admin Panel

View & manage OTP tokens at:
```
http://localhost:8000/admin/accounts/otptoken/
```

Features:
- View all OTP codes
- Check expiration status
- Track verification attempts
- Monitor usage patterns

## 🎯 Production Checklist

Before going live:
- [ ] Set production `KAVENEGAR_API_KEY`
- [ ] Update `KAVENEGAR_SENDER` number
- [ ] Enable HTTPS (set `secure=True` in cookies)
- [ ] Monitor Kavenegar credit
- [ ] Test with real phone numbers
- [ ] Set up error monitoring

## 📚 Full Documentation

See `OTP_AUTHENTICATION.md` for complete details.

## 💡 Example User Flow

1. User enters phone number (+989123456789)
2. Click "Send Code" button
3. System sends 6-digit code via SMS
4. User receives SMS: "کد تایید شما: 123456"
5. User enters code
6. System verifies & logs in user
7. User redirected to dashboard

## ⏱️ Default Settings

| Setting | Default | Description |
|---------|---------|-------------|
| Code Length | 6 digits | OTP code length |
| Expiry Time | 5 minutes | How long code is valid |
| Max Attempts | 3 | Verification attempts |
| Rate Limit | 5/min | Requests per minute |
| Phone Limit | 3/2min | OTPs per phone per 2 min |

## 🔗 Related Files

- Model: `src/accounts/models/user.py` (OTPToken)
- Serializers: `src/accounts/serializers/otp.py`
- Views: `src/accounts/api/otp.py`
- URLs: `src/accounts/urls.py`
- Admin: `src/accounts/admin.py`
- Settings: `src/core/settings/common.py`

---

**Need Help?** Check the full documentation in `OTP_AUTHENTICATION.md`

