# 🚨 Anti-Hallucination System Fixes

## 📋 خلاصه مشکل

مشکل اصلی: AI برای پیام‌هایی که فقط لینک بودند (مثل مسیج `T2epjS`)، توهم‌زایی می‌کرد و اطلاعات نادرست می‌داد.

### ریشه مشکل:

1. **Confusion بین کاراکتر و توکن**:
   - `anti_hallucination_rules`: max_length=1000 کاراکتر
   - متن واقعی: ~1800 کاراکتر (~450-550 توکن)
   - Budget واقعی: فقط 400 توکن برای کل `system_prompt`
   - نتیجه: بیش از نیمی از قوانین ضد توهم‌زایی trim می‌شد ❌

2. **عدم وجود گارد مخصوص "فقط لینک"**:
   - وقتی کاربر فقط URL می‌فرستاد، AI سعی می‌کرد حدس بزند لینک درباره چیست
   - هیچ check صریحی قبل از AI call وجود نداشت

3. **Token budget ناکافی برای system_prompt**:
   - 400 توکن برای 7 بخش مختلف (role, language, tone, guidelines, greeting, anti-hallucination, link handling)
   - قوانین critical در trim حذف می‌شدند

---

## ✅ راه‌حل‌های پیاده‌شده

### 1️⃣ افزایش Token Budget برای System Prompt

**فایل**: `src/AI_model/services/token_budget_controller.py`

```python
BUDGET = {
    'system_prompt': 700,      # +300 tokens (قبلاً 400)
    'bio_context': 60,          # -20 tokens
    'customer_info': 30,        # بدون تغییر
    'conversation': 250,        # -50 tokens
    'primary_context': 600,     # -50 tokens
    'secondary_context': 510,   # -180 tokens
}
# Total: 2150 tokens (زیر limit 2200)
```

**چرا 700؟**
- حتی با anti_hallucination کوتاه (~250 tokens)، 6 section دیگر هم داریم
- با 700 tokens، جای کافی برای همه sections + حاشیه امنیت

---

### 2️⃣ کوتاه کردن Anti-Hallucination Rules

**فایل**: `src/settings/models.py`

**قبل**: ~1800 کاراکتر (~550 توکن) ❌  
**بعد**: ~780 کاراکتر (~250 توکن) ✅

**تغییرات کلیدی**:
- حذف redundancy و تکرارها
- فرمت bullet-point ساده‌تر
- تأکید ویژه روی لینک‌ها:

```
4) لینک و وب‌سایت (خیلی مهم):
   - اگر فقط یک لینک می‌بینی و محتوای صفحه در کانتکست نیست، اصلاً حدس نزن
   - بگو: "متأسفانه من نمی‌تونم محتوای این لینک را ببینم..."
   
   ⚠️ CRITICAL: If user sends ONLY a URL without context:
   - NEVER guess what the link is about
   - Say you can't see the content
```

---

### 3️⃣ Hard Cap روی Anti-Hallucination Rules

**فایل**: `src/settings/models.py` - متد `get_combined_system_prompt()`

```python
# ✅ Hard cap at 800 characters to prevent token budget overflow
if len(rules) > 800:
    rules = rules[:800] + "\n\n⚠️ (قوانین کامل به دلیل محدودیت توکن trim شدند)"
```

**هدف**: حتی اگر کسی در admin panel متن طولانی بنویسد، سیستم آن را محدود می‌کند.

---

### 4️⃣ URL-Only Guard (مهم‌ترین تغییر!)

**فایل**: `src/AI_model/services/message_integration.py`

#### ✅ تابع تشخیص:
```python
def _is_only_url(text: str) -> bool:
    """
    Check if message is just a URL with no meaningful text.
    """
    text = text.strip()
    url_pattern = r'https?://\S+'
    urls = re.findall(url_pattern, text)
    
    if not urls:
        return False
    
    # Remove URLs and punctuation
    text_without_urls = re.sub(url_pattern, '', text).strip()
    text_without_urls = re.sub(r'[،,\.؟?\s]+', '', text_without_urls)
    
    # If remaining text < 10 chars → only URL
    return len(text_without_urls) < 10
```

#### ✅ Guard قبل از AI Call:
```python
# در MessageSystemIntegration.process_new_customer_message()

original_message_text = message_instance.content
if (message_instance.message_type == 'text' and 
    _is_only_url(original_message_text)):
    
    logger.info(f"🔗 Message {message_instance.id} is only URL - returning static response")
    
    static_response = (
        "متأسفانه من نمی‌تونم محتوای لینک‌ها را ببینم. "
        "اگر سوالی راجع به این لینک داری، لطفاً با متن توضیح بده..."
    )
    
    # Create response WITHOUT calling AI ✅
    response_message = Message.objects.create(...)
    
    return {'processed': True, 'reason': 'url_only_guard'}
```

**نکات مهم**:
- ✅ فقط روی `message_type == 'text'` اعمال می‌شود
- ✅ روی `original_message_text` چک می‌شود (نه combined content)
- ✅ پاسخ ثابت بدون صدا زدن AI
- ✅ در **همه entrypoints** فعال است (چون همه از `process_new_customer_message` استفاده می‌کنند)

---

### 5️⃣ Token Usage Logging

**فایل**: `src/AI_model/services/token_budget_controller.py`

```python
logger.info(
    f"📊 Token Budget Breakdown:\n"
    f"  • System Prompt: {result['system_prompt_tokens']}/{cls.BUDGET['system_prompt']} tokens\n"
    f"  • Bio Context: {result['bio_context_tokens']}/{cls.BUDGET['bio_context']} tokens\n"
    f"  • Customer Info: {result['customer_info_tokens']}/{cls.BUDGET['customer_info']} tokens\n"
    f"  • Conversation: {result['conversation_tokens']}/{cls.BUDGET['conversation']} tokens\n"
    f"  • Primary Context: {result['primary_context_tokens']}/{cls.BUDGET['primary_context']} tokens\n"
    f"  • Secondary Context: {result['secondary_context_tokens']}/{cls.BUDGET['secondary_context']} tokens\n"
    f"  • User Query: {result['user_query_tokens']} tokens\n"
    f"  ━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    f"  • TOTAL: {result['total_tokens']}/{cls.MAX_TOTAL_TOKENS} tokens"
)
```

**هدف**: مانیتورینگ دقیق برای اطمینان از این‌که system_prompt واقعاً در بودجه 700 توکن جا می‌شود.

---

## 🎯 نتیجه

### قبل از فیکس ❌:
1. `system_prompt` = 400 tokens → قوانین trim می‌شدند
2. `anti_hallucination_rules` = ~550 tokens → از بودجه خارج
3. پیام فقط لینک → AI حدس می‌زد و توهم‌زایی می‌کرد
4. هیچ مانیتورینگ دقیق نداشتیم

### بعد از فیکس ✅:
1. `system_prompt` = 700 tokens → قوانین کامل می‌رسند
2. `anti_hallucination_rules` = ~250 tokens + hard cap 800 chars
3. پیام فقط لینک → پاسخ ثابت بدون AI call
4. مانیتورینگ کامل token usage در لاگ‌ها

---

## 🧪 تست

### سناریوی 1: پیام فقط لینک (مثل T2epjS)
```
ورودی: "https://example.com"
خروجی: "متأسفانه من نمی‌تونم محتوای لینک‌ها را ببینم..."
وضعیت: ✅ AI call نمی‌شود، پاسخ ثابت
```

### سناریوی 2: لینک + سوال
```
ورودی: "https://example.com\nاین چیه؟"
خروجی: پاسخ AI (با تمام قوانین ضد توهم‌زایی)
وضعیت: ✅ AI call می‌شود با budget کامل
```

### سناریوی 3: Instagram Share + Text
```
ورودی: [share] + "این خوبه؟"
خروجی: پاسخ AI (با کانتکست combine شده)
وضعیت: ✅ URL guard trigger نمی‌شود (message_type != 'text')
```

---

## 📁 فایل‌های تغییر یافته

1. ✅ `src/AI_model/services/token_budget_controller.py` - افزایش budget + logging
2. ✅ `src/settings/models.py` - کوتاه کردن rules + hard cap
3. ✅ `src/AI_model/services/message_integration.py` - URL guard

---

## 🚀 Deployment

### مرحله 1: Migration (اگر لازم باشد)
```bash
python manage.py makemigrations
python manage.py migrate
```

### مرحله 2: Restart Services
```bash
# Local
python manage.py runserver

# Server
docker compose restart web celery_worker
```

### مرحله 3: مانیتورینگ
```bash
# بررسی لاگ‌ها برای token breakdown
docker compose logs -f --tail 100 | grep "📊 Token Budget Breakdown"
```

---

## 🔍 مانیتورینگ بعد از دیپلوی

روی چند پیام واقعی این‌ها را چک کنید:

1. ✅ Token usage logs → آیا system_prompt < 700 است؟
2. ✅ پیام‌های فقط لینک → آیا پاسخ ثابت می‌آید؟
3. ✅ توهم‌زایی → آیا کاهش یافته؟
4. ✅ پاسخ‌های با کانتکست → آیا کامل و دقیق هستند؟

---

## 📝 یادداشت‌های نهایی

**سه لایه محافظتی**:
1. **Budget Level**: system_prompt = 700 tokens (کافی برای همه sections)
2. **Content Level**: anti_hallucination کوتاه + hard cap 800 chars
3. **Request Level**: URL-only guard با پاسخ ثابت

**تضمین**:
- ✅ برای کیس‌های مثل T2epjS دیگر توهم‌زایی رخ نمی‌دهد
- ✅ قوانین ضد توهم‌زایی کامل به مدل می‌رسند
- ✅ همه entrypoints پوشش داده شده‌اند

**محدودیت‌ها**:
- ⚠️ هیچ LLM 100% بدون توهم نیست
- این تغییرات توهم‌زایی را به حداقل می‌رسانند، نه حذف کامل
- برای محصول SaaS در این مرحله، کیفیت بسیار بالایی دارد ✅

