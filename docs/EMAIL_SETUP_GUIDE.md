# 📧 Email Configuration Setup Guide

## Current Status: ✅ WORKING (Console Backend)

The email confirmation system is currently working with console backend (emails print to console/logs instead of sending). To enable actual email sending, follow the solutions below.

## 🔧 SMTP Authentication Issue: "535 Authentication Credentials Invalid"

### **Root Cause:**
The AWS SES SMTP credentials are invalid or the sender email domain is not verified.

---

## **Solution 1: Verify AWS SES Setup (Recommended)**

### Step 1: Check AWS SES Console
1. Go to AWS SES Console → `us-east-1` region
2. **Verify Identities:**
   - Domain: `fiko.net` should be verified ✅
   - Email: `noreply@fiko.net` or `support@fiko.net` should be verified ✅
3. **Check Sandbox Mode:**
   - If in sandbox, you can only send to verified emails
   - Request production access if needed

### Step 2: Verify SMTP Credentials
1. Go to AWS SES → Account Dashboard → SMTP Settings
2. Create new SMTP credentials if needed
3. Update the credentials in settings:

```python
# In src/core/settings/common.py
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'email-smtp.us-east-1.amazonaws.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'YOUR_NEW_SMTP_USERNAME'
EMAIL_HOST_PASSWORD = 'YOUR_NEW_SMTP_PASSWORD'
DEFAULT_FROM_EMAIL = 'noreply@fiko.net'  # Must be verified
```

---

## **Solution 2: Alternative SMTP Settings**

Try these alternative configurations:

### Option A: Use SSL instead of TLS
```python
EMAIL_HOST = 'email-smtp.us-east-1.amazonaws.com'
EMAIL_PORT = 465
EMAIL_USE_TLS = False
EMAIL_USE_SSL = True
```

### Option B: Try Different Region
```python
# Try US West
EMAIL_HOST = 'email-smtp.us-west-2.amazonaws.com'
# Or EU West
EMAIL_HOST = 'email-smtp.eu-west-1.amazonaws.com'
```

---

## **Solution 3: Environment Variables (Security)**

Move credentials to environment variables:

### Step 1: Add to .env file
```bash
SMTP_USERNAME=AKIARTLO5HLCKHLZ7KWR
SMTP_PASSWORD=BLrFuGxymqJxlgcGdrWLJXFfX4+pMc33Dqi43J/av31h
SMTP_FROM_EMAIL=noreply@fiko.net
```

### Step 2: Update settings
```python
EMAIL_HOST_USER = environ.get('SMTP_USERNAME')
EMAIL_HOST_PASSWORD = environ.get('SMTP_PASSWORD')
DEFAULT_FROM_EMAIL = environ.get('SMTP_FROM_EMAIL', 'noreply@fiko.net')
```

---

## **Solution 4: Third-Party Email Services**

### Option A: SendGrid
```python
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.sendgrid.net'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'apikey'
EMAIL_HOST_PASSWORD = 'your_sendgrid_api_key'
```

### Option B: Mailgun
```python
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.mailgun.org'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'your_mailgun_username'
EMAIL_HOST_PASSWORD = 'your_mailgun_password'
```

---

## **Quick Test Commands**

### Test Current Setup:
```bash
cd /Users/nima/Projects/Fiko-Backend && source venv/bin/activate && cd src
python -c "
import django, os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.development')
django.setup()
from django.core.mail import send_mail
result = send_mail('Test', 'Test message', 'noreply@fiko.net', ['test@example.com'])
print(f'Result: {result}')
"
```

### Test Registration API:
```bash
curl -X POST "http://localhost:8000/api/v1/accounts/register" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser123",
    "email": "test@example.com",
    "password": "SecurePassword123!"
  }'
```

---

## **Current Configuration**

### ✅ Working (Console Backend):
- Emails print to console/server logs
- Perfect for development and testing
- Email confirmation codes are still generated
- All API endpoints work normally

### 🔧 To Enable Real Emails:
1. Fix AWS SES credentials/verification
2. Uncomment SMTP settings in `common.py`
3. Comment out console backend line

---

## **Email Flow Status**

| Component | Status | Notes |
|-----------|--------|-------|
| User Model | ✅ Working | `email_confirmed` field added |
| Email Token Model | ✅ Working | 6-digit codes, 15min expiry |
| Registration API | ✅ Working | Auto-sends confirmation |
| Confirmation API | ✅ Working | Validates codes |
| Resend API | ✅ Working | Sends new codes |
| Status API | ✅ Working | Check confirmation status |
| Email Template | ✅ Working | HTML + plain text |
| SMTP Delivery | ⚠️ Console Only | Fix credentials for real emails |

---

## **Next Steps**

1. **For Development:** Keep console backend, test all functionality
2. **For Production:** Fix AWS SES credentials and verify domain
3. **Alternative:** Use SendGrid/Mailgun for simpler setup

The system is fully functional - only email delivery needs SMTP fix!
