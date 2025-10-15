# 🎯 Persona & Tone Layer - RapidAPI Deployment Guide

## ✅ تکمیل شد!

سیستم Persona & Tone Adaptation با استفاده از **RapidAPI** برای fetch کردن biography از Instagram پیاده‌سازی شد.

---

## 🔑 پیش‌نیازها

### 1. دریافت RapidAPI Key

1. برو به: https://rapidapi.com/
2. ثبت‌نام کن (اگه نکردی)
3. برو به: https://rapidapi.com/bestapiever365/api/instagram-looter2
4. Subscribe کن (Free plan: 500 requests/month)
5. Copy کن `X-RapidAPI-Key` رو

---

## 📦 فایل‌های تغییر یافته

### 1. **فایل جدید:**
- `src/message/services/instagram_profile_scraper.py` → سرویس fetch کردن bio

### 2. **فایل‌های اصلاح شده:**
- `src/message/insta.py` → استفاده از RapidAPI برای bio
- `src/core/settings/common.py` → اضافه شدن `RAPIDAPI_KEY`

### 3. **فایل‌های قبلی (بدون تغییر):**
- `src/AI_model/services/persona_extractor.py` → کار میکنه ✅
- `src/message/models.py` → `bio` & `persona_data` fields ✅
- `src/AI_model/services/gemini_service.py` → persona adaptation ✅
- `src/AI_model/services/token_budget_controller.py` → budget management ✅

---

## 🚀 مراحل Deploy

### مرحله 1: اضافه کردن API Key

```bash
# در سرور Production
cd ~/fiko-backend

# ویرایش .env
nano .env

# اضافه کردن:
RAPIDAPI_KEY=your-rapidapi-key-here

# Save: Ctrl+X, Y, Enter
```

### مرحله 2: Migration (قبلا انجام شده ✅)

```bash
# این مراحل قبلا انجام شدن، نیازی نیست دوباره بزنی
docker-compose exec web python manage.py migrate message
```

### مرحله 3: Restart Services

```bash
# Restart web & celery
docker-compose restart web
docker-compose restart celery_worker
docker-compose restart celery_beat

# چک status
docker-compose ps
```

---

## 🧪 تست

### تست 1: Django Shell

```bash
docker-compose exec web python manage.py shell
```

**در Shell:**

```python
# تست 1: RapidAPI Service
from message.services.instagram_profile_scraper import InstagramProfileScraper

profile = InstagramProfileScraper.get_profile("ataei.ca")
print(f"Bio: {profile.get('biography')}")
print(f"Status: {profile.get('fetch_status')}")

# تست 2: Persona Extraction
from AI_model.services.persona_extractor import PersonaExtractor

bio = "استراتژیست برندینگ و مارکتینگ"
persona = PersonaExtractor.extract_persona(bio, "test_user")
print(f"Tone: {persona.get('tone_preference')}")
print(f"Interests: {persona.get('interests')}")

# تست 3: Customer Fields
from message.models import Customer

c = Customer.objects.filter(source='instagram').first()
if c:
    print(f"Bio: {c.bio}")
    print(f"Persona: {c.persona_data}")

exit()
```

### تست 2: End-to-End

```bash
# مانیتورینگ لاگ‌ها
docker-compose logs -f web | grep -E "Persona|biography|✨|🎨"
```

**بعد یک پیام از Instagram بفرست** و باید این لاگ‌ها رو ببینی:

```
✅ Fetched Instagram profile: @username (verified: True, followers: 74333)
✨ Persona extracted for customer 123 (@username): tone=friendly, interests=3
🎨 Persona adaptation enabled: friendly tone
📊 Token budget: 1450/1500 tokens (persona: 45, ...)
```

---

## ⚠️ عیب‌یابی

### Error 1: `no_api_key`

```bash
# لاگ:
⚠️ RapidAPI key not configured

# راه حل:
# چک کن .env داره RAPIDAPI_KEY
cat .env | grep RAPIDAPI_KEY

# اگه نداره، اضافه کن و restart کن
```

### Error 2: `rate_limited`

```bash
# لاگ:
⚠️ Rate limited by RapidAPI

# راه حل:
# Free plan: 500 requests/month
# Cache: 30 روز (یعنی هر customer فقط 1 بار)
# اگه تموم شد، Upgrade کن plan رو
```

### Error 3: `not_found`

```bash
# لاگ:
Profile not found for @username

# دلیل:
# Username اشتباهه یا account delete شده
# این OK هست، سیستم ادامه میده بدون persona
```

---

## 💰 هزینه‌ها

### RapidAPI Pricing

| Plan | Requests/Month | قیمت |
|------|---------------|------|
| Free | 500 | $0 |
| Basic | 10,000 | ~$10/month |
| Pro | 100,000 | ~$50/month |

### محاسبه استفاده:

```
- فرض: 100 new customer/day
- Cache: 30 روز
- Request/month: 100 × 30 = 3,000 requests
- Plan needed: Basic ($10/month)
```

---

## 🎯 ویژگی‌ها

### ✅ چی کار میکنه:

1. **Auto Biography Fetch:**
   - وقتی customer جدید پیام میده
   - از RapidAPI bio رو میگیره
   - Cache میکنه برای 30 روز

2. **Persona Extraction:**
   - از bio، interests رو extract میکنه
   - Tone preference تشخیص میده (friendly/formal/neutral)
   - Profession شناسایی میکنه

3. **Tone Adaptation:**
   - در AI responses، tone رو تغییر میده
   - Interests رو mention میکنه (وقتی relevant هست)
   - Token budget رو مدیریت میکنه (50 tokens)

### ❌ چی کار نمیکنه:

- ❌ Instagram Graph API (bio field نداره)
- ❌ Web Scraping (block میشه)
- ❌ Selenium (خیلی کنده)

---

## 📊 Architecture

```
Instagram Webhook
    ↓
Check: created or no persona?
    ↓
RapidAPI Fetch (with cache)
    ↓
PersonaExtractor.extract()
    ↓
Save: bio & persona_data
    ↓
AI Response (with persona adaptation)
    ↓
TokenBudgetController (50 tokens for persona)
```

---

## 🔒 Legal & Ethical

### ✅ قانونی چون:
- از **third-party API** معتبر استفاده میکنه
- فقط **public data** میگیره
- **Cache** میکنه (30 روز)
- **Rate limiting** داره
- **Graceful failure** (اگه نیومد، ادامه میده)

### ✅ Best Practices:
- فقط برای **new customers** (1 بار)
- **Opt-in** (فقط Instagram Business accounts)
- **Respects privacy** (no private data)

---

## 🎉 وضعیت فعلی

| Component | Status |
|-----------|--------|
| Migration | ✅ Done |
| PersonaExtractor | ✅ Working |
| RapidAPI Service | ✅ Implemented |
| Instagram Webhook | ✅ Integrated |
| Token Budget | ✅ Updated |
| Gemini Service | ✅ Updated |
| Cache System | ✅ 30 days |
| Error Handling | ✅ Graceful |

---

## 📝 Next Steps (Optional)

### 1. Admin Panel UI (اگه خواستی):
```python
# در admin.py:
# افزودن فیلد bio (editable)
# دکمه "Refresh Biography"
# نمایش persona_data (read-only)
```

### 2. Manual Bio Input (اگه API down بود):
```python
# فیلد bio در customer profile
# Admin می‌تونه دستی پر کنه
```

### 3. Analytics:
```python
# تعداد persona extractions موفق
# API usage tracking
# Success rate
```

---

## 💡 Tips

1. **Monitor API Usage:**
   ```bash
   # در RapidAPI Dashboard ببین
   # چقدر request زدی
   ```

2. **Cache Hit Rate:**
   ```python
   # لاگ‌ها رو ببین:
   # "📦 Using cached Instagram profile"
   ```

3. **Cost Optimization:**
   - Cache: 30 روز خوبه
   - اگه بیشتر بخوای: 90 روز
   - کمتر: 7 روز

---

## 🚨 مهم!

- **API Key** رو **commit نکن** به Git!
- فقط در `.env` ذخیره کن
- در production از **environment variables** استفاده کن

---

**🎉 تمام! سیستم آماده production هست!**

برای سوالات بیشتر، check کن:
- `PERSONA_TONE_IMPLEMENTATION_GUIDE.md`
- `AI_RESPONSE_ALGORITHM_ARCHITECTURE.md`

