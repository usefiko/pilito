# 📱 Instagram Button Template (CTA Buttons) - Implementation Complete

## ✅ تمام تغییرات با موفقیت اعمال شد!

### 📋 خلاصه پیاده‌سازی (طبق نظرات Review)

همه نکاتی که در review ذکر شد، رعایت شده است:

#### ✅ نکات مثبت حفظ شد:
- استفاده از `buttons` به‌عنوان JSONField در Message
- Pattern مشخص `[[CTA:Title|URL]]`
- Validation فقط `http://` و `https://`
- Limit دکمه‌ها به 3 تا
- Truncate title به 20 کاراکتر
- CTA فقط روی پیام AI (نه customer)
- Coupling تمیز در زنجیره pass کردن buttons

#### ✅ نکات اصلاحی پیاده‌سازی شد:
1. **محل فایل**: `src/message/utils/cta_utils.py` (نه AI_model) ✅
2. **Import safety**: استفاده از `.get()` برای `ai_response['response']` ✅
3. **فاصله‌های اضافی**: `re.sub(r'\s{2,}', ' ', clean_text).strip()` ✅
4. **محدودیت text**: اگر > 400 chars → fallback به text معمولی ✅
5. **Empty content guard**: چک خالی بودن content بعد از CTA extraction ✅
6. **Logging کامل**: برای extraction، Button Template، و fallback ✅

---

## 📁 فایل‌های تغییر یافته (5 فایل)

### 1. `src/message/models.py`
```python
# اضافه شده در خط 130:
buttons = models.JSONField(
    null=True,
    blank=True,
    help_text="CTA buttons for this message (Instagram/WhatsApp Button Template). Max 3 buttons."
)
```

### 2. `src/message/utils/cta_utils.py` (فایل جدید)
- تابع `extract_cta_from_text()`: استخراج CTA از متن
- تابع `_is_valid_url()`: امنیت و validation URL
- Pattern: `[[CTA:Title|URL]]`
- حذف فاصله‌های اضافی
- Logging کامل

### 3. `src/message/services/instagram_service.py`
```python
# تغییرات:
def send_message(self, recipient_id, message_text, buttons=None):
    # اگر buttons داره و text <= 400 chars → Button Template
    # وگرنه → text معمولی
    
def send_message_to_customer(self, customer, message_text, buttons=None):
    # پاس دادن buttons به send_message
```

### 4. `src/AI_model/services/gemini_service.py` - `create_ai_message`
```python
# تغییرات:
from message.utils.cta_utils import extract_cta_from_text

original_content = ai_response.get('response') or ''  # ✅ با .get()
clean_content, buttons = extract_cta_from_text(original_content)

# Guard برای empty content
if not clean_content or not clean_content.strip():
    clean_content = original_content
    buttons = None

ai_message = Message.objects.create(
    content=clean_content,  # بدون CTA tokens
    buttons=buttons,  # لیست دکمه‌ها یا None
    # ...
)
```

### 5. `src/AI_model/services/gemini_service.py` - `_send_instagram_response`
```python
# تغییرات:
buttons = getattr(ai_message, 'buttons', None)

result = instagram_service.send_message_to_customer(
    customer,
    ai_message.content,
    buttons=buttons  # ✅ پاس دادن buttons
)

if buttons:
    logger.info(f"📌 Sent with {len(buttons)} CTA button(s)")
```

---

## 🚀 Deployment Steps

### مرحله 1: Migration (روی سرور)
```bash
cd /root/manual_pilito/pilito
git pull

# Migration
python manage.py makemigrations message
python manage.py migrate

# Restart services
docker compose restart web celery_worker
```

### مرحله 2: Test دستی با Shell (قبل از AI)

```python
# در Django shell (روی سرور):
python manage.py shell

from message.models import Message, Conversation, Customer
from message.services.instagram_service import InstagramService

# پیدا کردن یک conversation از Instagram
conv = Conversation.objects.filter(source='instagram').first()
customer = conv.customer

# ساختن دکمه fake
test_buttons = [
    {'type': 'web_url', 'title': 'سایت فیکو', 'url': 'https://fiko.ai'},
    {'type': 'web_url', 'title': 'قیمت‌ها', 'url': 'https://fiko.ai/pricing'}
]

# ارسال
service = InstagramService.get_service_for_conversation(conv)
result = service.send_message_to_customer(
    customer,
    "این یک تست Button Template است 👇",
    buttons=test_buttons
)

print(result)
# انتظار: {'success': True, ...}
```

**چک کنید**: آیا دکمه‌ها در Instagram ظاهر شدند؟

---

### مرحله 3: Test با AI

1. برو به **Admin Panel** → **Manual Prompt**
2. اضافه کن:

```
درباره فیکو:
فیکو یک پلتفرم هوشمند مدیریت گفت‌وگو است.

برای اطلاعات بیشتر [[CTA:سایت ما|https://fiko.ai]] ببینید.
```

3. یک پیام Instagram بفرست: **"درباره فیکو بگو"**
4. انتظار:
   - متن: "فیکو یک پلتفرم... برای اطلاعات بیشتر ببینید"
   - یک دکمه: "سایت ما"

---

### مرحله 4: Monitoring و Logs

```bash
# بررسی لاگ‌های CTA extraction:
docker compose logs -f web | grep -E "CTA|Button Template"

# لاگ‌های مورد انتظار:
# ✅ Extracted 2 CTA button(s) from text
# 📤 Sending Button Template with 2 button(s) to...
# ✅ AI response sent to Instagram successfully
# 📌 Sent with 2 CTA button(s)
```

---

## 🧪 Test Cases

### ✅ Case 1: یک CTA
```
Input (Manual Prompt): 
"برای سفارش [[CTA:سایت|https://fiko.ai]] مراجعه کنید."

Expected:
- Text: "برای سفارش مراجعه کنید."
- Buttons: [{"type": "web_url", "title": "سایت", "url": "https://fiko.ai"}]
```

### ✅ Case 2: چند CTA
```
Input:
"برای اطلاعات:
[[CTA:سایت|https://fiko.ai]]
[[CTA:قیمت|https://fiko.ai/pricing]]
[[CTA:تماس|https://fiko.ai/contact]]"

Expected:
- Text: "برای اطلاعات:"
- Buttons: 3 دکمه (max limit)
```

### ✅ Case 3: بدون CTA
```
Input: "سلام! چطور می‌تونم کمکتون کنم؟"

Expected:
- Text: همان متن
- Buttons: None (پیام text معمولی)
```

### ✅ Case 4: Text بلند (> 400 chars)
```
Input: متن خیلی طولانی + [[CTA:...]]

Expected:
- Fallback به text معمولی (بدون Button Template)
- Log: "Text too long (XXX chars) for Button Template, falling back to plain text"
```

### ✅ Case 5: URL نامعتبر
```
Input: [[CTA:Test|ftp://invalid.com]]

Expected:
- URL رد می‌شود
- Log: "⚠️ URL must start with http:// or https://"
- فقط متن ارسال می‌شود
```

---

## ⚠️ نکات مهم (Troubleshooting)

### اگر دکمه نیامد:

1. **چک کنید لاگ‌ها**:
   ```bash
   docker compose logs --tail 100 web | grep -E "CTA|Button"
   ```

2. **Payload را چک کنید**:
   - آیا `template_type: button` صحیح است؟
   - آیا `buttons` یک array با max 3 element است؟
   - آیا `text` خالی نیست؟

3. **Instagram API Response**:
   - Error code 400 → payload format مشکل دارد
   - Error code 190 → Token expired

4. **محدودیت‌های Instagram**:
   - حداکثر 3 دکمه
   - عنوان دکمه حداکثر 20 کاراکتر
   - فقط `web_url` و `postback`

### اگر AI پاسخ نداد:

1. Migration اجرا شد؟
2. CTA token صحیح است؟ `[[CTA:Title|URL]]`
3. URL با `https://` شروع می‌شود؟

---

## 📊 Architecture Summary

```
User Message (Instagram)
    ↓
AI generates response with [[CTA:...]]
    ↓
create_ai_message()
    ├─ extract_cta_from_text()
    │   ├─ Parse CTA tokens
    │   ├─ Validate URLs
    │   └─ Return (clean_text, buttons)
    ↓
Message.objects.create(
    content=clean_text,  # بدون tokens
    buttons=buttons       # لیست دکمه‌ها
)
    ↓
_send_instagram_response()
    ├─ buttons = getattr(ai_message, 'buttons')
    └─ instagram_service.send_message_to_customer(..., buttons=buttons)
        ↓
send_message()
    ├─ if buttons and len(text) <= 400:
    │   └─ Button Template payload
    └─ else:
        └─ Plain text payload
            ↓
Instagram API
    ↓
User sees message with button(s)! 🎉
```

---

## 🎯 Multi-Channel Roadmap (آینده)

این معماری برای کانال‌های دیگر هم آماده است:

### WhatsApp:
```python
# Interactive Message (Button)
payload = {
    'type': 'interactive',
    'interactive': {
        'type': 'button',
        'body': {'text': message_text},
        'action': {
            'buttons': [
                {'type': 'reply', 'reply': {'id': '1', 'title': title}}
            ]
        }
    }
}
```

### Telegram:
```python
# Inline Keyboard
reply_markup = {
    'inline_keyboard': [
        [{'text': title, 'url': url}]
    ]
}
```

### Web Chat:
```javascript
// React Component
<ChatMessage>
  <p>{message.content}</p>
  {message.buttons && (
    <div className="cta-buttons">
      {message.buttons.map(btn => (
        <a href={btn.url}>{btn.title}</a>
      ))}
    </div>
  )}
</ChatMessage>
```

---

## ✅ Checklist نهایی

- [x] فیلد `buttons` به Message اضافه شد
- [x] Migration آماده است
- [x] `cta_utils.py` در `message/utils` ساخته شد
- [x] `InstagramService.send_message` از Button Template پشتیبانی می‌کند
- [x] `create_ai_message` CTA را extract می‌کند
- [x] `_send_instagram_response` buttons را pass می‌دهد
- [x] Validation و security (فقط http/https)
- [x] Logging کامل
- [x] Guard برای text طولانی (>400 chars)
- [x] حذف فاصله‌های اضافی
- [x] Empty content guard
- [ ] Migration روی سرور (بعد از git pull)
- [ ] Test دستی با shell
- [ ] Test با AI و Manual Prompt
- [ ] Monitor logs

---

## 📝 یادداشت برای UX (مرحله بعد)

برای کاربران نهایی (non-technical):
- UI فرم برای ساختن دکمه‌ها:
  - متن پیام
  - عنوان دکمه
  - URL دکمه
- پشت‌صحنه تبدیل به `[[CTA:...]]`
- Preview قبل از ارسال

---

**🎉 پیاده‌سازی کامل شد! آماده برای deployment و test است.**

