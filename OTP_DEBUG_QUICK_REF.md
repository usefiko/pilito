# OTP Debug Quick Reference 🚀

## ⚡ Quick Fix Steps

### 1️⃣ Check Configuration (30 seconds)
```bash
cd /Users/nima/Projects/pilito
source venv/bin/activate
python check_otp_config.py
```

### 2️⃣ Test Kavenegar (2 minutes)
```bash
python test_kavenegar.py
```
Enter a test phone number when prompted.

### 3️⃣ Most Common Issue - API Key Not Set

**Check if API key is set:**
```bash
cat .env | grep KAVENEGAR_API_KEY
```

**If not set, add to `.env` file:**
```bash
KAVENEGAR_API_KEY=your_actual_api_key_here
KAVENEGAR_SENDER=10008663
```

**Get your API key:**
👉 https://panel.kavenegar.com/client/setting/account

---

## 🔥 Quick Fixes

| Issue | Fix |
|-------|-----|
| "Failed to send OTP" | Run `python check_otp_config.py` |
| "SMS service not configured" | Add `KAVENEGAR_API_KEY` to `.env` |
| "Invalid API key" | Verify key at https://panel.kavenegar.com/ |
| "Insufficient credit" | Recharge at https://panel.kavenegar.com/ |
| "Too many requests" | Wait 2 minutes |

---

## 📁 New Files Added

1. **`check_otp_config.py`** - Quick diagnostic tool
2. **`test_kavenegar.py`** - Full integration test
3. **`docs/OTP_TROUBLESHOOTING.md`** - Complete troubleshooting guide

---

## 🎯 What Changed

### Improved Error Messages
**Before:**
```json
{"detail": "Failed to send OTP. Please try again."}
```

**After:**
```json
{"detail": "Failed to send OTP: Invalid API key (401)"}
```

Now you'll see the **actual error** from Kavenegar!

---

## 🧪 Test API

```bash
# Terminal 1: Start server
cd src
python manage.py runserver

# Terminal 2: Test OTP
curl -X POST http://localhost:8000/api/v1/usr/otp \
  -H "Content-Type: application/json" \
  -d '{"phone_number": "+989123456789"}'
```

---

## 📝 Check Admin Panel

http://localhost:8000/admin/accounts/otptoken/

You can see all OTP codes here during development!

---

## 🆘 Need Help?

**Full Documentation:**
- `docs/OTP_TROUBLESHOOTING.md` - Complete troubleshooting guide
- `docs/OTP_QUICK_START.md` - Getting started guide
- `docs/OTP_AUTHENTICATION.md` - Full API documentation

**Kavenegar Resources:**
- Panel: https://panel.kavenegar.com/
- Docs: https://kavenegar.com/rest.html
- Support: https://kavenegar.com/support

---

**Quick Tip:** The improved error logging will now show you exactly what's wrong! 🎉

