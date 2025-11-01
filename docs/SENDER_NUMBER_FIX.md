# 🔧 Fix: Invalid Sender Number (Error 412)

## ❌ Current Error

```
APIException[412] ارسال کننده نامعتبر است
Translation: "Sender is invalid"
```

**Problem:** The sender number `10008663` is not activated or assigned to your Kavenegar account.

---

## ✅ Solution: Find Your Correct Sender Number

### Step 1: Login to Kavenegar Panel

👉 **Go to:** https://panel.kavenegar.com/

### Step 2: Find Your Sender Number

1. **Click on "خطوط ارسالی" (Sender Lines)** in the menu
   - Or go directly to: https://panel.kavenegar.com/client/sms/line

2. **You will see your assigned sender numbers:**
   
   Examples:
   - `10008663` (Public shared line)
   - `20005006666` (Public line)
   - `2000xxxx` (Private line)
   - `10004346` (Another public line)
   
3. **Copy the ACTIVE sender number** (shown in green/active status)

### Step 3: Update Your `.env` File

```bash
# In /Users/nima/Projects/pilito/.env
KAVENEGAR_API_KEY=your_api_key_here
KAVENEGAR_SENDER=YOUR_ACTUAL_SENDER_NUMBER  # ← Update this!
```

**Example:**
```bash
KAVENEGAR_SENDER=20005006666
```

### Step 4: Restart Django Server

```bash
# If using Docker
cd /Users/nima/Projects/pilito
docker-compose restart backend

# If running locally
# Press Ctrl+C to stop, then:
cd /Users/nima/Projects/pilito/src
python manage.py runserver
```

### Step 5: Test Again

```bash
curl -X POST http://localhost:8000/api/v1/usr/otp \
  -H "Content-Type: application/json" \
  -d '{"phone_number": "+989123456789"}'
```

---

## 🔍 Check Your Account Info

Run this script to see your account details:

```bash
cd /Users/nima/Projects/pilito
source venv/bin/activate
python check_kavenegar_account.py
```

---

## 📱 Common Kavenegar Sender Number Types

| Type | Format | Example | Description |
|------|--------|---------|-------------|
| **Public Shared** | 1000xxxx | 10008663 | Shared with other users |
| **Public** | 2000xxxxxxx | 20005006666 | Your public line |
| **Private** | 2000xxxx | 20001234 | Private dedicated line |
| **Custom** | Text | PILITO | Custom brand name (if purchased) |

---

## 🆘 Still Not Working?

### Option 1: Use Kavenegar's Lookup/Verify Service

Instead of regular SMS, you can use Kavenegar's Verify service which has pre-approved templates:

```python
# In serializers/otp.py, replace sms_send with verify lookup
response = api.verify_lookup({
    'receptor': recipient,
    'token': otp_token.code,
    'template': 'verify'  # You need to create this template in Kavenegar panel
})
```

### Option 2: Contact Kavenegar Support

- 📧 Support: https://kavenegar.com/support
- 📞 Tell them: "I need an active sender line for OTP messages"
- 📝 They will assign you a proper sender number

### Option 3: Check Your Account Status

1. Go to: https://panel.kavenegar.com/client/setting/account
2. Verify:
   - ✅ Account is active
   - ✅ You have credit
   - ✅ No restrictions on account

---

## 💡 Quick Checklist

- [ ] Logged into Kavenegar panel
- [ ] Found active sender number from "خطوط ارسالی"
- [ ] Updated `.env` with correct sender number
- [ ] Restarted Django server
- [ ] Tested OTP API again

---

## 🎯 Expected Result After Fix

**Before (Error):**
```json
{
  "detail": "Sender number is invalid. Please contact support."
}
```

**After (Success):**
```json
{
  "phone_number": "+989123456789",
  "message": "OTP sent successfully",
  "expires_in": 300
}
```

---

**Need help? The error is now clear - just get your correct sender number from the Kavenegar panel!** 🚀

