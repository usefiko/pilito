# Wizard Complete - Backend Integration Guide

## 🎯 خلاصه تغییرات

API قبلی حفظ شده و **backward compatible** هست، با این تفاوت که حالا **validation هوشمند** داره!

---

## 📊 مقایسه قبل و بعد

### ⏮️ قبل (کد قدیمی)
```python
# فقط یک flag setter ساده بود
def patch(self, request):
    user.wizard_complete = True
    user.save()
    return {"wizard_complete": True}
```

**مشکل:**
- ✗ هیچ بررسی نمی‌کرد
- ✗ حتی اگه چیزی پر نبود تیک می‌زد
- ✗ کاربر می‌تونست بدون تکمیل کردن ویزارد رو complete کنه

### ⏭️ بعد (کد جدید)
```python
def patch(self, request):
    # بررسی همه شرایط
    is_complete, missing_fields, details = check_requirements(user)
    
    if is_complete:
        user.wizard_complete = True
        return {"success": True, "wizard_complete": True, ...}
    else:
        return {"success": False, "missing_fields": [...], ...}
```

**مزایا:**
- ✅ بررسی هوشمند همه فیلدها
- ✅ لیست دقیق موارد کم شده
- ✅ فقط با شرایط کامل تیک می‌زنه
- ✅ Backward compatible با کد قبلی

---

## 🔄 Backward Compatibility

### فرانت قدیمی (بدون تغییر کار می‌کنه)
```javascript
// کد قبلی فرانت
fetch('/api/v1/accounts/wizard-complete', {
  method: 'PATCH',
  headers: { Authorization: `Bearer ${token}` }
})
.then(res => res.json())
.then(data => {
  if (data.wizard_complete) {
    // ✅ همین فیلد همچنان وجود داره
    console.log('Wizard completed!');
  }
});
```

**نتیجه:**
- اگه همه شرایط OK باشه → `wizard_complete: true` ✅
- اگه چیزی کم باشه → Error 400 با جزئیات ❌

---

## 🆕 فرانت جدید (استفاده از قابلیت‌های جدید)

### 1️⃣ بررسی وضعیت قبل از تکمیل
```javascript
// ابتدا وضعیت رو چک کن
const status = await fetch('/api/v1/accounts/wizard-complete', {
  method: 'GET',
  headers: { Authorization: `Bearer ${token}` }
}).then(r => r.json());

// نمایش به کاربر
if (status.can_complete) {
  // همه چیز OK - دکمه رو فعال کن
  enableCompleteButton();
} else {
  // چیزی کم هست - لیست بده
  showMissingFields(status.missing_fields);
}
```

### 2️⃣ تکمیل با handling خطا
```javascript
try {
  const result = await fetch('/api/v1/accounts/wizard-complete', {
    method: 'PATCH',
    headers: { Authorization: `Bearer ${token}` }
  }).then(r => r.json());

  if (result.success) {
    // موفق ✅
    alert('ویزارد تکمیل شد!');
    window.location = '/dashboard';
  }
} catch (error) {
  // خطا در درخواست
  if (error.response?.data?.missing_fields) {
    // نمایش موارد کم شده
    showMissingFieldsAlert(error.response.data.missing_fields);
  }
}
```

---

## 🔍 شرایط لازم برای تکمیل ویزارد

کاربر باید **همه** موارد زیر را کامل کرده باشه:

| # | فیلد | جدول | بررسی |
|---|------|------|-------|
| 1 | نام | `User.first_name` | نباید null یا خالی باشه |
| 2 | نام خانوادگی | `User.last_name` | نباید null یا خالی باشه |
| 3 | شماره تماس | `User.phone_number` | نباید null یا خالی باشه |
| 4 | نوع بیزنس | `User.business_type` | نباید null یا خالی باشه |
| 5 | منوال پرامپت | `AIPrompts.manual_prompt` | نباید null یا خالی باشه |
| 6 | کانال متصل | `InstagramChannel` یا `TelegramChannel` | حداقل یکی `is_connect=True` باشه |

---

## 📡 API Reference

### GET `/api/v1/accounts/wizard-complete`

**بررسی وضعیت فعلی ویزارد**

**Response (همه چیز OK):**
```json
{
  "wizard_complete": false,
  "can_complete": true,
  "missing_fields": [],
  "details": {
    "first_name": true,
    "last_name": true,
    "phone_number": true,
    "business_type": true,
    "manual_prompt": true,
    "channel_connected": true,
    "instagram_connected": true,
    "telegram_connected": false
  }
}
```

**Response (چیزی کم هست):**
```json
{
  "wizard_complete": false,
  "can_complete": false,
  "missing_fields": ["manual_prompt", "business_type"],
  "details": {
    "first_name": true,
    "last_name": true,
    "phone_number": true,
    "business_type": false,
    "manual_prompt": false,
    "channel_connected": true,
    "instagram_connected": false,
    "telegram_connected": true
  }
}
```

---

### PATCH `/api/v1/accounts/wizard-complete`

**تکمیل ویزارد (فقط اگه همه شرایط OK باشه)**

**Request:**
```http
PATCH /api/v1/accounts/wizard-complete
Authorization: Bearer <token>
```

**Response (موفق - 200):**
```json
{
  "success": true,
  "message": "Wizard completed successfully",
  "wizard_complete": true,
  "details": {
    "first_name": true,
    "last_name": true,
    "phone_number": true,
    "business_type": true,
    "manual_prompt": true,
    "channel_connected": true,
    "instagram_connected": true,
    "telegram_connected": false
  }
}
```

**Response (ناموفق - 400):**
```json
{
  "success": false,
  "message": "Cannot complete wizard. Missing required fields.",
  "missing_fields": ["manual_prompt", "business_type"],
  "wizard_complete": false,
  "details": {
    "first_name": true,
    "last_name": true,
    "phone_number": true,
    "business_type": false,
    "manual_prompt": false,
    "channel_connected": true,
    "instagram_connected": false,
    "telegram_connected": true
  }
}
```

---

## 🎨 نمایش در Admin Panel

در Admin Panel، فیلد `wizard_complete` به صورت Boolean نمایش داده می‌شه:

```python
# در src/accounts/admin.py
class UserAdmin(admin.ModelAdmin):
    list_display = [
        'email', 'first_name', 'last_name', 
        'wizard_complete',  # ← این فیلد
        'is_active'
    ]
    
    list_filter = ['wizard_complete', 'is_active']
```

**نمایش:**
- ✅ تیک سبز: `wizard_complete = True`
- ❌ ضربدر قرمز: `wizard_complete = False`

---

## 🧪 تست با Curl

### 1. دریافت وضعیت
```bash
curl -X GET http://localhost:8000/api/v1/accounts/wizard-complete \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### 2. تکمیل ویزارد
```bash
curl -X PATCH http://localhost:8000/api/v1/accounts/wizard-complete \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

---

## 🧪 تست با Python

```python
import requests

# تنظیمات
BASE_URL = "http://localhost:8000"
EMAIL = "omidlog@gmail.com"
PASSWORD = "your_password"

# 1. لاگین و دریافت توکن
login_response = requests.post(
    f"{BASE_URL}/api/v1/accounts/login",
    json={"email": EMAIL, "password": PASSWORD}
)
token = login_response.json()['access']

headers = {"Authorization": f"Bearer {token}"}

# 2. بررسی وضعیت ویزارد
status = requests.get(
    f"{BASE_URL}/api/v1/accounts/wizard-complete",
    headers=headers
).json()

print("وضعیت فعلی:", status)
print("می‌تونه تکمیل کنه؟", status['can_complete'])
print("موارد کم شده:", status['missing_fields'])

# 3. تلاش برای تکمیل
if status['can_complete']:
    result = requests.patch(
        f"{BASE_URL}/api/v1/accounts/wizard-complete",
        headers=headers
    ).json()
    print("نتیجه:", result)
else:
    print("⚠️ نمی‌تونه تکمیل کنه! اول این موارد رو کامل کن:")
    for field in status['missing_fields']:
        print(f"  - {field}")
```

---

## 🔧 Troubleshooting

### مشکل 1: همه چیز پر شده ولی هنوز `can_complete = false`

**راه‌حل:**
```python
# چک کنید که manual_prompt فقط فاصله نباشه
ai_prompts = AIPrompts.objects.get(user=user)
print(f"Manual Prompt: '{ai_prompts.manual_prompt}'")
print(f"Is Empty: {not ai_prompts.manual_prompt.strip()}")

# چک کنید business_type
print(f"Business Type: '{user.business_type}'")
print(f"Is None: {user.business_type is None}")
```

### مشکل 2: کانال connect هست ولی در details نشون نمی‌ده

**راه‌حل:**
```python
# چک کنید فیلد is_connect
instagram = InstagramChannel.objects.filter(user=user)
print(f"Instagram Channels: {instagram.count()}")
for ch in instagram:
    print(f"  - {ch.username}: is_connect={ch.is_connect}")

telegram = TelegramChannel.objects.filter(user=user)
print(f"Telegram Channels: {telegram.count()}")
for ch in telegram:
    print(f"  - {ch.bot_username}: is_connect={ch.is_connect}")
```

### مشکل 3: بعد از PATCH موفق، Admin Panel هنوز قرمزه

**راه‌حل:**
- صفحه Admin Panel رو refresh کنید (F5)
- یا logout/login کنید

---

## ✅ خلاصه برای تیم فرانت

### نیازی به تغییر ندارید! 🎉

کد قبلی شما همچنان کار می‌کنه:

```javascript
// همین کد قبلی شما
fetch('/api/v1/accounts/wizard-complete', { method: 'PATCH' })
```

**ولی الان:**
- ✅ اگه همه چیز OK باشه → موفق
- ❌ اگه چیزی کم باشه → خطا 400 با لیست موارد کم شده

### اگه می‌خواید از قابلیت‌های جدید استفاده کنید:

```javascript
// 1. ابتدا وضعیت رو بگیر
const { can_complete, missing_fields } = await getWizardStatus();

// 2. اگه می‌تونه complete کنه
if (can_complete) {
  await completeWizard();
} else {
  showMissingFields(missing_fields);
}
```

**مستندات کامل:** `/docs/WIZARD_COMPLETE_FRONTEND_GUIDE.md`

---

## 📞 پشتیبانی

اگه مشکلی داشتید:
1. لاگ‌های backend رو چک کنید
2. Response API رو بررسی کنید
3. فیلدهای کاربر رو در database چک کنید
4. با تیم backend تماس بگیرید

---

## 🎯 نتیجه‌گیری

این تغییرات باعث می‌شه:
- ✅ **Admin Panel**: می‌تونه ببینه wizard کامل شده یا نه
- ✅ **Validation**: فقط با شرایط کامل تیک می‌خوره
- ✅ **Backward Compatible**: کد قبلی فرانت کار می‌کنه
- ✅ **Smart**: جزئیات کامل و لیست موارد کم شده رو می‌ده
- ✅ **Frontend Friendly**: می‌تونه چک‌لیست درست کنه

**همه چیز آماده است! 🚀**

