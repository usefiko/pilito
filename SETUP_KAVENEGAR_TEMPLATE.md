# 🎯 Setup Kavenegar Verify Template (Recommended Solution)

## ✅ Why Use Verify/Lookup?

**Kavenegar Verify** is BETTER than regular SMS for OTP because:
- ✅ **No sender number required** (solves Error 412!)
- ✅ Pre-approved templates (faster delivery)
- ✅ Better delivery rates
- ✅ Lower cost per SMS
- ✅ Designed specifically for OTP/verification codes

---

## 📋 Setup Steps (5 minutes)

### Step 1: Login to Kavenegar Panel

👉 Go to: https://panel.kavenegar.com/

### Step 2: Create Verification Template

1. **Go to Verification section:**
   👉 https://panel.kavenegar.com/client/verification/add
   
   Or click: **خدمات** (Services) → **ارسال قالب** (Send Template)

2. **Click "افزودن قالب جدید" (Add New Template)**

3. **Fill in the template details:**

   **Template Name:** `verify`
   
   **Template Text (متن قالب):**
   ```
   کد تایید شما: %token%
   
   این کد تا 5 دقیقه اعتبار دارد.
   ```
   
   **Translation:** "Your verification code: %token%\n\nThis code is valid for 5 minutes."
   
   **Template Type:** OTP / Verification Code

4. **Click "ثبت قالب" (Register Template)**

5. **Wait for approval** (usually instant, max 1 hour)

### Step 3: Test Your Template

Once approved, test it:

```bash
curl -X POST http://localhost:8000/api/v1/usr/otp \
  -H "Content-Type: application/json" \
  -d '{"phone_number": "+989123456789"}'
```

---

## 🎨 Template Variables

You can use these placeholders in your template:

| Variable | Description | Example |
|----------|-------------|---------|
| `%token%` | The OTP code | 123456 |
| `%token2%` | Second token (optional) | - |
| `%token3%` | Third token (optional) | - |

**Example Template:**
```
سلام!

کد تایید شما: %token%

این کد تا 5 دقیقه معتبر است.
از افشای این کد خودداری کنید.

پیلیتو
```

---

## 🔄 How It Works Now

### New Flow (with Verify):

1. **User requests OTP**
2. **Backend tries `verify_lookup` first** ✅ (No sender needed!)
3. **If verify fails** → Falls back to regular SMS
4. **User receives OTP via SMS**

### Code Changes:

```python
# Primary method: verify_lookup (no sender required)
response = api.verify_lookup({
    'receptor': recipient,
    'token': otp_code,
    'template': 'verify'
})

# Fallback: regular sms_send (requires sender)
# Only used if verify_lookup fails
```

---

## 🚀 Testing

### Method 1: Via API
```bash
curl -X POST http://localhost:8000/api/v1/usr/otp \
  -H "Content-Type: application/json" \
  -d '{"phone_number": "+989123456789"}'
```

### Method 2: Check Logs
```bash
docker logs -f pilito_backend
```

You should see:
```
Attempting to send OTP via Kavenegar Verify:
  Receptor: 989123456789
  Template: verify
  Token: 123456
OTP sent successfully via Verify service
```

### Method 3: Admin Panel
Check if OTP was created:
👉 http://localhost:8000/admin/accounts/otptoken/

---

## ⚠️ If Template Not Found

If you see:
```
Verify lookup failed: Template 'verify' not found
Falling back to regular SMS send...
```

**Then:**
1. Check template is created and approved in Kavenegar panel
2. Verify template name is exactly `verify` (lowercase)
3. Wait a few minutes for Kavenegar to sync

**Temporary Fix:**
The code will automatically fallback to regular SMS (which needs correct sender number)

---

## 🎯 Multiple Templates (Optional)

You can create different templates for different purposes:

### Template: `verify` (OTP)
```
کد تایید شما: %token%
```

### Template: `login` (Login OTP)
```
کد ورود به حساب کاربری: %token%
```

### Template: `reset` (Password Reset)
```
کد بازیابی رمز عبور: %token%
```

Then in your code:
```python
# Use different templates
api.verify_lookup({
    'receptor': phone,
    'token': code,
    'template': 'login'  # or 'reset', etc.
})
```

---

## 📊 Benefits Comparison

| Feature | Regular SMS | Verify/Lookup |
|---------|------------|---------------|
| **Sender Required** | ✅ Yes (412 error risk) | ❌ No |
| **Cost** | Normal | Lower |
| **Delivery Speed** | Normal | Faster |
| **Setup** | Easy | Need template |
| **Approval** | Instant | 1 hour max |
| **Best For** | General SMS | OTP/Verification |

---

## 🆘 Troubleshooting

### Issue: "Template not found"

**Solution:**
1. Go to: https://panel.kavenegar.com/client/verification/list
2. Check template status is "تایید شده" (Approved)
3. Verify template name matches exactly

### Issue: Still getting 412 error

**Solution:**
- Template might not be approved yet
- Wait for approval, code will use fallback SMS
- Or fix sender number as before

### Issue: Template rejected

**Possible reasons:**
- Template text violates policies
- Missing required information
- Contact Kavenegar support

---

## ✅ Success Checklist

- [ ] Created template named "verify" in Kavenegar panel
- [ ] Template includes `%token%` placeholder
- [ ] Template is approved (تایید شده)
- [ ] Code updated to use `verify_lookup`
- [ ] Tested with real phone number
- [ ] Received SMS successfully
- [ ] Verified OTP works end-to-end

---

## 💡 Pro Tips

1. **Keep templates simple** - Avoid complex text
2. **Test thoroughly** - Try with multiple numbers
3. **Monitor usage** - Check Kavenegar dashboard
4. **Multiple templates** - Create for different use cases
5. **Fallback ready** - Code automatically falls back to SMS

---

## 📚 Resources

- **Kavenegar Verify Docs:** https://kavenegar.com/rest.html#verification
- **Template Management:** https://panel.kavenegar.com/client/verification/list
- **Create Template:** https://panel.kavenegar.com/client/verification/add
- **Support:** https://kavenegar.com/support

---

**Now your OTP system uses the BEST method (Verify/Lookup) and automatically falls back to SMS if needed!** 🎉

