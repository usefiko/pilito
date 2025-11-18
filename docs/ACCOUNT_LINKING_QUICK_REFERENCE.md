# Account Linking - Quick Reference

## 📋 New API Endpoints

### Add Email to Phone-Based Account
```
POST /api/accounts/link/email          # Send verification code
POST /api/accounts/link/email/verify   # Verify code and link email
```

### Add Phone to Email-Based Account
```
POST /api/accounts/link/phone          # Send OTP
POST /api/accounts/link/phone/verify   # Verify OTP and link phone
```

---

## 🔥 Quick Examples

### Example 1: Phone User Adding Email

```bash
# Step 1: Send verification code
curl -X POST http://localhost:8000/api/accounts/link/email \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"email": "newuser@example.com"}'

# Response:
# {
#   "email": "newuser@example.com",
#   "message": "Verification code sent to your email",
#   "expires_in": 900
# }

# Step 2: Verify the code from email
curl -X POST http://localhost:8000/api/accounts/link/email/verify \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"code": "123456"}'

# Response:
# {
#   "message": "Email linked successfully!",
#   "email": "newuser@example.com",
#   "email_confirmed": true
# }
```

### Example 2: Email User Adding Phone

```bash
# Step 1: Send OTP
curl -X POST http://localhost:8000/api/accounts/link/phone \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"phone_number": "+989123456789"}'

# Response:
# {
#   "phone_number": "+989123456789",
#   "message": "OTP sent successfully",
#   "expires_in": 300
# }

# Step 2: Verify OTP from SMS
curl -X POST http://localhost:8000/api/accounts/link/phone/verify \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"phone_number": "+989123456789", "code": "123456"}'

# Response:
# {
#   "message": "Phone number linked successfully!",
#   "phone_number": "+989123456789"
# }
```

---

## ⚙️ Configuration

### Required Django Settings

Make sure these settings are configured in your `settings.py`:

```python
# Email Configuration (for email verification)
EMAIL_HOST = 'your-smtp-host'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'your-email@example.com'
EMAIL_HOST_PASSWORD = 'your-password'
DEFAULT_FROM_EMAIL = 'Pilito <noreply@pilito.com>'

# Kavenegar SMS Configuration (for phone OTP)
KAVENEGAR_API_KEY = 'your-kavenegar-api-key'
KAVENEGAR_SENDER = 'your-sender-number'

# OTP Settings (optional - these are defaults)
OTP_EXPIRY_TIME = 300  # 5 minutes in seconds
OTP_RESEND_WAIT_TIME = 300  # 5 minutes in seconds
OTP_MAX_ATTEMPTS = 3  # Maximum verification attempts
```

---

## 🎯 User Flow Diagrams

### Phone User → Add Email

```
User (logged in with phone)
    ↓
Provides email address
    ↓
System sends 6-digit code to email
    ↓
User receives email with code
    ↓
User submits code
    ↓
✅ Email linked and verified
```

### Email User → Add Phone

```
User (logged in with email)
    ↓
Provides phone number
    ↓
System sends 6-digit OTP via SMS
    ↓
User receives SMS with OTP
    ↓
User submits OTP
    ↓
✅ Phone linked to account
```

---

## 🔐 Security Checks

The API automatically handles:

- ✅ Prevents linking email/phone used by another account
- ✅ Prevents re-linking already verified credentials
- ✅ Rate limiting (2 min for email, 5 min for phone)
- ✅ Code expiration (15 min for email, 5 min for phone)
- ✅ Attempt limiting (max 3 attempts for OTP)
- ✅ Authentication required for all endpoints

---

## 🐛 Troubleshooting

### Email not sending?
- Check `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`
- Check server logs: `python manage.py runserver` or check Django logs
- Try sending test email: `python manage.py test_email`

### SMS not sending?
- Check `KAVENEGAR_API_KEY` and `KAVENEGAR_SENDER`
- Verify Kavenegar account has sufficient credit
- Check if template `otp-verify` exists in Kavenegar panel
- Check server logs for detailed Kavenegar errors

### Rate limit errors?
- Wait the specified time before retrying
- Check if multiple requests are being sent accidentally
- Verify rate limit settings in Django settings

### "Already linked to another account" error?
- Email/phone is already registered with a different user
- User needs to use a different email/phone number
- Or login to the other account if they own it

---

## 📊 Database Changes

### User Model Fields Used:
- `email` - Email address (CharField, unique)
- `email_confirmed` - Boolean flag for verified email
- `phone_number` - Phone number (CharField, unique, nullable)

### Token Models:
- `EmailConfirmationToken` - Stores email verification codes
- `OTPToken` - Stores phone OTP codes

No new migrations required - using existing models! ✅

---

## 🧪 Testing Checklist

- [ ] Phone user can request email verification code
- [ ] Email code is delivered successfully
- [ ] Invalid email code shows proper error
- [ ] Expired email code shows proper error
- [ ] Valid email code links email successfully
- [ ] Email user can request phone OTP
- [ ] Phone OTP is delivered via SMS
- [ ] Invalid OTP shows proper error with remaining attempts
- [ ] Expired OTP shows proper error
- [ ] Valid OTP links phone successfully
- [ ] Cannot link email already used by another account
- [ ] Cannot link phone already used by another account
- [ ] Rate limiting works correctly
- [ ] Swagger docs display all endpoints correctly

---

## 📱 Frontend Integration

### Example JavaScript/TypeScript

```typescript
// Add email to phone-based account
async function addEmail(email: string, accessToken: string) {
  const response = await fetch('/api/accounts/link/email', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${accessToken}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ email })
  });
  return response.json();
}

async function verifyEmailCode(code: string, accessToken: string) {
  const response = await fetch('/api/accounts/link/email/verify', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${accessToken}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ code })
  });
  return response.json();
}

// Add phone to email-based account
async function addPhone(phoneNumber: string, accessToken: string) {
  const response = await fetch('/api/accounts/link/phone', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${accessToken}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ phone_number: phoneNumber })
  });
  return response.json();
}

async function verifyPhoneOTP(phoneNumber: string, code: string, accessToken: string) {
  const response = await fetch('/api/accounts/link/phone/verify', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${accessToken}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ phone_number: phoneNumber, code })
  });
  return response.json();
}
```

---

## 🎉 Summary

✅ **4 new endpoints** added for account linking  
✅ **All authenticated** - requires login  
✅ **Fully documented** with Swagger/OpenAPI  
✅ **Production-ready** with rate limiting and security  
✅ **Reuses existing** OTP and email utilities  
✅ **Zero new migrations** - uses existing models  

**Ready to use!** 🚀

