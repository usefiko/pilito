# OTP Troubleshooting Guide

## Error: "Failed to send OTP. Please try again."

This guide helps you diagnose and fix OTP sending issues with Kavenegar.

---

## 🔍 Quick Diagnostic

### Step 1: Check Configuration

```bash
cd /Users/nima/Projects/pilito
source venv/bin/activate
python check_otp_config.py
```

This will show you:
- ✅ Whether Kavenegar API key is set
- ✅ Current OTP settings
- ✅ Package installation status
- ✅ Database connectivity

### Step 2: Test Kavenegar Integration

```bash
python test_kavenegar.py
```

This script will:
- Test different Kavenegar API calling methods
- Show detailed error messages
- Help identify the exact issue

---

## 🛠️ Common Issues and Solutions

### Issue 1: API Key Not Set

**Symptom:**
```json
{
  "detail": "SMS service is not configured. Please contact support."
}
```

**Solution:**
1. Create/edit `.env` file in project root:
   ```bash
   KAVENEGAR_API_KEY=your_actual_api_key_here
   KAVENEGAR_SENDER=10008663
   ```

2. Get your API key from: https://panel.kavenegar.com/client/setting/account
3. Restart Django server

---

### Issue 2: Invalid API Key

**Symptom:**
```json
{
  "detail": "Failed to send OTP: API key is invalid"
}
```

**Solution:**
1. Verify API key in Kavenegar panel
2. Check for extra spaces or characters in `.env`
3. Ensure key is active and not expired

---

### Issue 3: Insufficient Credits

**Symptom:**
```json
{
  "detail": "Failed to send OTP: Insufficient credit"
}
```

**Solution:**
1. Login to Kavenegar panel
2. Check credit balance
3. Recharge your account

---

### Issue 4: Invalid Phone Number Format

**Symptom:**
```json
{
  "phone_number": ["Please provide a valid Iranian phone number"]
}
```

**Solution:**
Accepted formats:
- `+989123456789` ✅
- `09123456789` ✅
- `989123456789` ✅

Not accepted:
- `9123456789` ❌
- `+1234567890` (non-Iranian) ❌

---

### Issue 5: Kavenegar Library Not Installed

**Symptom:**
```
ModuleNotFoundError: No module named 'kavenegar'
```

**Solution:**
```bash
cd /Users/nima/Projects/pilito
source venv/bin/activate
pip install kavenegar==1.1.2
```

---

### Issue 6: Rate Limiting

**Symptom:**
```json
{
  "phone_number": ["Too many OTP requests. Please try again in 2 minutes."]
}
```

**Solution:**
- Wait 2 minutes before requesting new OTP
- This is a security feature to prevent abuse
- Limit: 3 OTPs per phone number per 2 minutes

---

### Issue 7: Kavenegar API Error Codes

| Code | Meaning | Solution |
|------|---------|----------|
| 200 | Success | ✅ No action needed |
| 400 | Invalid parameters | Check phone number format |
| 401 | Invalid API key | Verify API key |
| 402 | Insufficient credit | Recharge account |
| 403 | Access denied | Check account status |
| 404 | Not found | Check sender number |
| 405 | Method not allowed | Contact support |
| 406 | Invalid sender | Verify sender number |
| 409 | Duplicate request | Wait before retry |
| 411 | Invalid receptor | Check phone number |
| 413 | Message too long | Shorten message |
| 414 | Invalid sender format | Check sender number |
| 415 | Invalid message | Check message content |
| 416 | Invalid date | Check scheduled time |
| 417 | Line not active | Check sender line status |
| 418 | Blacklisted number | Contact support |
| 422 | Data validation error | Check all parameters |
| 501 | Server error | Try again later |

---

## 🧪 Manual Testing

### Test 1: Check API Connection

```bash
curl -X POST https://api.kavenegar.com/v1/YOUR_API_KEY/sms/send.json \
  -d "receptor=09123456789" \
  -d "message=Test" \
  -d "sender=10008663"
```

Replace `YOUR_API_KEY` with your actual key.

### Test 2: Test Django API

```bash
# Send OTP
curl -X POST http://localhost:8000/api/v1/usr/otp \
  -H "Content-Type: application/json" \
  -d '{"phone_number": "+989123456789"}'

# Check response - you'll get the OTP code or error
```

### Test 3: Check OTP in Admin

1. Go to: http://localhost:8000/admin/accounts/otptoken/
2. Login with admin credentials
3. View the latest OTP codes
4. Check if codes are being generated

---

## 🔧 Advanced Debugging

### Enable Detailed Error Messages

The error handling has been improved to show actual error messages instead of generic ones.

**Before:**
```json
{
  "detail": "Failed to send OTP. Please try again."
}
```

**After (with improved logging):**
```json
{
  "detail": "Failed to send OTP: Invalid API key (401)"
}
```

### Check Django Logs

```bash
# If using Docker
docker logs -f pilito_backend

# If running locally
cd src
python manage.py runserver
# Errors will appear in console
```

### Python Shell Testing

```bash
cd src
python manage.py shell
```

Then:
```python
from kavenegar import KavenegarAPI
from django.conf import settings

api = KavenegarAPI(settings.KAVENEGAR_API_KEY)

# Test SMS send
params = {
    'sender': settings.KAVENEGAR_SENDER,
    'receptor': '09123456789',
    'message': 'تست'
}

response = api.sms_send(params)
print(response)
```

---

## 📋 Pre-Production Checklist

Before deploying to production:

- [ ] Valid Kavenegar API key set in production `.env`
- [ ] Sufficient credit in Kavenegar account
- [ ] Sender number is active and approved
- [ ] Test OTP sending with real phone number
- [ ] Verify SMS delivery
- [ ] Check OTP expiry time (default: 5 minutes)
- [ ] Configure rate limiting appropriately
- [ ] Set up monitoring/alerting for failed OTPs
- [ ] Enable HTTPS (set `secure=True` in cookies)

---

## 🆘 Still Having Issues?

### 1. Run Full Diagnostic
```bash
python check_otp_config.py
python test_kavenegar.py
```

### 2. Check Environment Variables
```bash
cd /Users/nima/Projects/pilito
cat .env | grep KAVENEGAR
```

### 3. Verify Kavenegar Account
- Login to: https://panel.kavenegar.com/
- Check API key
- Check credit balance
- Check sender number status

### 4. Contact Kavenegar Support
- Website: https://kavenegar.com/
- Support: https://kavenegar.com/support
- Documentation: https://kavenegar.com/rest.html

### 5. Check Application Logs
```bash
# View recent errors
tail -f src/logs/django.log

# Or check Docker logs
docker logs pilito_backend --tail=100
```

---

## 📚 Related Documentation

- [OTP Quick Start Guide](./OTP_QUICK_START.md)
- [OTP Authentication Guide](./OTP_AUTHENTICATION.md)
- [Kavenegar REST API](https://kavenegar.com/rest.html)
- [Kavenegar Python Library](https://github.com/kavenegar/kavenegar-python)

---

## 💡 Tips

1. **Development Testing**: During development, check OTP codes in admin panel instead of waiting for SMS
2. **Use Test Credit**: Kavenegar provides test credits for development
3. **Monitor Usage**: Keep track of SMS usage to avoid running out of credit
4. **Error Logging**: Always check logs when debugging issues
5. **Rate Limiting**: Respect rate limits to avoid account suspension

---

**Last Updated:** November 1, 2025

