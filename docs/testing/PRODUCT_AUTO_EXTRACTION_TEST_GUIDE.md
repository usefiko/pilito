# 🧪 راهنمای تست Product Auto-Extraction

## ⚡ قابلیت جدید: Auto-ON!

✅ **پیش‌فرض:** `auto_extract_products = True`  
🤖 **هوشمند:** Pre-filter تشخیص میده صفحه محصول داره یا نه  
💰 **کم‌هزینه:** فقط صفحات با confidence >= 0.4 به AI میرن

---

## 📋 مرحله ۱: Push کردن کد

```bash
# از دایرکتوری اصلی پروژه
cd /Users/omidataei/Documents/GitHub/Fiko-Backend

# بررسی تغییرات
git status

# Add تغییرات
git add src/web_knowledge/models.py
git add src/web_knowledge/services/product_extractor.py
git add src/web_knowledge/tasks.py
git add src/web_knowledge/serializers.py

# Commit
git commit -m "feat: AI-powered product auto-extraction with Gemini 1.5 Pro

- Enhanced Product model: pricing, discounts, features, stock, images
- Added auto_extract_products toggle to WebsiteSource
- Created ProductExtractor service with Gemini 1.5 Pro (high accuracy)
- Hybrid extraction: rule-based pre-filter + AI extraction
- Integrated with crawl system (optional, non-breaking)
- Updated serializers to expose new fields
- Source tracking: links products to pages/websites"

# Push
git push origin main
```

---

## 🖥️ مرحله ۲: روی سرور (SSH)

### ۲.۱ اتصال و Pull

```bash
# SSH به سرور
ssh ubuntu@your-server-ip

# رفتن به پروژه
cd ~/fiko-backend

# Pull
git pull origin main
```

### ۲.۲ ایجاد و اجرای Migration

```bash
# ساخت migration
docker compose exec django_app python src/manage.py makemigrations web_knowledge

# باید این رو ببینید:
# Migrations for 'web_knowledge':
#   web_knowledge/migrations/0XXX_enhance_product_model.py
#     - Add field auto_extract_products to websitesource
#     - Add field short_description to product
#     - Add field long_description to product
#     - ... (20+ fields)

# اجرای migration
docker compose exec django_app python src/manage.py migrate web_knowledge

# باید ببینید:
# Running migrations:
#   Applying web_knowledge.0XXX_enhance_product_model... OK
```

### ۲.۳ Restart سرویس‌ها

```bash
# Restart
docker compose restart django_app celery_worker

# چک کردن که بالا اومدن
docker compose ps

# باید django_app و celery_worker هر دو "Up" باشن
```

---

## ✅ مرحله ۳: تست اولیه (بررسی Migration)

```bash
# وارد Django shell شوید
docker compose exec django_app python src/manage.py shell
```

**در shell این دستورات رو بزنید:**

```python
# 1. چک کردن فیلدهای جدید Product
from web_knowledge.models import Product

# لیست همه فیلدها
fields = [f.name for f in Product._meta.fields]
print("Product fields:", fields)

# باید این فیلدها رو ببینید:
# 'short_description', 'long_description', 'original_price', 
# 'discount_percentage', 'currency', 'features', 'brand', 
# 'category', 'in_stock', 'main_image', 'source_website',
# 'source_page', 'extraction_method', etc.

# 2. چک کردن WebsiteSource toggle
from web_knowledge.models import WebsiteSource

website = WebsiteSource.objects.first()
if website:
    print(f"Website: {website.name}")
    print(f"Auto-extract enabled: {website.auto_extract_products}")
    # باید False باشه (پیش‌فرض)

# 3. چک کردن ProductExtractor
from web_knowledge.services.product_extractor import ProductExtractor

if website:
    extractor = ProductExtractor(website.user)
    print(f"Extractor initialized: {extractor.gemini_model is not None}")
    # باید True باشه

# بیرون اومدن
exit()
```

**✅ اگر همه چی OK بود، ادامه بدید!**

---

## 🧪 مرحله ۴: تست واقعی (دو روش)

### روش ۱: تست با یک صفحه موجود (سریع)

```bash
# وارد shell شوید
docker compose exec django_app python src/manage.py shell
```

```python
from web_knowledge.models import WebsitePage, Product
from web_knowledge.services.product_extractor import ProductExtractor

# پیدا کردن یک صفحه که احتمالاً محصول داره
page = WebsitePage.objects.filter(
    word_count__gte=200  # صفحات با محتوای کافی
).first()

if page:
    print(f"Testing with page: {page.url}")
    print(f"Title: {page.title}")
    
    # تست extraction
    extractor = ProductExtractor(page.website.user)
    
    # Pre-filter test
    should_extract, confidence = extractor.should_extract_from_page(page)
    print(f"\nPre-filter result:")
    print(f"  Should extract: {should_extract}")
    print(f"  Confidence: {confidence:.2f}")
    
    if should_extract:
        # اگر confidence بالا بود، AI extraction
        print("\n🤖 Running AI extraction...")
        products = extractor.extract_and_save(page)
        
        print(f"\n✅ Extracted {len(products)} products:")
        for p in products:
            print(f"\n  📦 {p.title}")
            print(f"     Price: {p.get_display_price()}")
            print(f"     Type: {p.product_type}")
            print(f"     Features: {p.features[:2] if p.features else []}")
            print(f"     Confidence: {p.extraction_confidence}")
    else:
        print("⏩ Page doesn't look like a product page")
else:
    print("❌ No pages found")

exit()
```

---

### روش ۲: فعال کردن برای یک Website و Crawl جدید

```bash
docker compose exec django_app python src/manage.py shell
```

```python
from web_knowledge.models import WebsiteSource
from accounts.models import User

# انتخاب یک user
user = User.objects.first()  # یا get(email='your@email.com')

# ساخت یک website تست با محصولات
# (مثال: یک سایت فروشگاهی یا سایت خودتون)
website = WebsiteSource.objects.create(
    user=user,
    name="Test Shop - Product Extraction",
    url="https://example-shop.com",  # سایتی که محصول داره
    description="Testing auto product extraction",
    max_pages=5,  # فقط 5 صفحه برای تست
    crawl_depth=2,
    auto_extract_products=True  # ✅ فعال!
)

print(f"✅ Created website: {website.name}")
print(f"   Auto-extract: {website.auto_extract_products}")

# شروع crawl
from web_knowledge.tasks import crawl_website_task

task = crawl_website_task.delay(str(website.id))
print(f"🚀 Crawl started! Task ID: {task.id}")

exit()
```

**چک کردن نتایج:**

```bash
# مشاهده logs در real-time
docker compose logs -f --tail=100 django_app celery_worker

# دنبال این پیام‌ها بگردید:
# "🔍 Starting product auto-extraction"
# "Pre-filter: ... → Extract: True"
# "✅ Gemini 1.5 Pro extracted X products"
# "✅ Saved product: ..."
```

---

## 📊 مرحله ۵: بررسی نتایج

### ۵.۱ از Django Shell

```bash
docker compose exec django_app python src/manage.py shell
```

```python
from web_knowledge.models import Product

# همه محصولات auto-extracted
auto_products = Product.objects.filter(extraction_method='ai_auto')
print(f"Found {auto_products.count()} auto-extracted products\n")

# نمایش جزئیات
for p in auto_products[:5]:
    print(f"{'='*60}")
    print(f"📦 {p.title}")
    print(f"   Type: {p.product_type}")
    print(f"   Price: {p.get_display_price()}")
    print(f"   Currency: {p.currency}")
    
    if p.has_discount:
        print(f"   Discount: {p.discount_info}")
    
    if p.features:
        print(f"   Features: {p.features[:3]}")
    
    if p.brand:
        print(f"   Brand: {p.brand}")
    
    print(f"   In Stock: {p.in_stock}")
    print(f"   Source: {p.source_page.url if p.source_page else 'N/A'}")
    print(f"   Confidence: {p.extraction_confidence:.2f}")
    print(f"   Tags: {p.tags}")

exit()
```

### ۵.۲ از Django Admin

```
1. برو به: https://api.fiko.net/admin/web_knowledge/product/
2. فیلتر کن: extraction_method = 'AI Auto-extracted'
3. چک کن:
   ✅ محصولات auto-extracted رو می‌بینی
   ✅ قیمت‌ها درست هستن
   ✅ تخفیف‌ها (اگه هست) نمایش داده میشن
   ✅ source_page لینک شده
   ✅ features و tags پر شدن
```

### ۵.۳ از API

```bash
# لیست محصولات
curl -H "Authorization: Bearer YOUR_TOKEN" \
  https://api.fiko.net/api/v1/web-knowledge/products/ | jq .

# باید فیلدهای جدید رو ببینید:
# - short_description
# - original_price, discount_percentage
# - currency, billing_period
# - features, brand, category
# - extraction_method, extraction_confidence
# - source_website, source_page
```

---

## 🎯 چیزهایی که باید چک کنید

### ✅ Checklist تست:

- [ ] Migration بدون خطا اجرا شد
- [ ] Django و Celery restart شدن
- [ ] ProductExtractor initialize میشه
- [ ] Pre-filter کار می‌کنه (confidence محاسبه میشه)
- [ ] Gemini 1.5 Pro extraction کار می‌کنه
- [ ] محصولات در database ذخیره میشن
- [ ] فیلدهای جدید (price, features, etc.) پر میشن
- [ ] source_page به درستی لینک میشه
- [ ] API فیلدهای جدید رو برمی‌گردونه
- [ ] Admin panel محصولات رو نشون میده
- [ ] اگه auto_extract_products=False باشه، extract نمیکنه

---

## 🐛 عیب‌یابی (Troubleshooting)

### مشکل ۱: Migration خطا میده

```bash
# چک کردن وضعیت migrations
docker compose exec django_app python src/manage.py showmigrations web_knowledge

# اگه conflict بود:
docker compose exec django_app python src/manage.py migrate web_knowledge --fake-initial
```

### مشکل ۲: "Gemini not available"

```bash
# چک کردن API key
docker compose exec django_app python src/manage.py shell

from settings.models import GeneralSettings
settings = GeneralSettings.get_settings()
print(f"Gemini API key configured: {bool(settings.gemini_api_key)}")
exit()
```

### مشکل ۳: هیچ محصولی extract نمیشه

```python
# در shell:
from web_knowledge.models import WebsitePage

# چک کردن محتوای صفحه
page = WebsitePage.objects.first()
print(f"Content preview: {page.cleaned_content[:500]}")
print(f"Word count: {page.word_count}")

# چک کردن pre-filter
from web_knowledge.services.product_extractor import ProductExtractor
extractor = ProductExtractor(page.website.user)
should, conf = extractor.should_extract_from_page(page)
print(f"Should extract: {should}, Confidence: {conf}")
```

### مشکل ۴: Logs نشون نمیده

```bash
# افزایش سطح logging
docker compose exec django_app python src/manage.py shell

import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('web_knowledge')
logger.setLevel(logging.DEBUG)
```

---

## 💰 هزینه تخمینی

```
Gemini 1.5 Pro:
- Pre-filter: رایگان (rule-based)
- AI extraction: ~$0.00125 per request
- فقط صفحاتی که confidence >= 0.4 دارن پردازش میشن

مثال:
- 100 صفحه crawl → ~40 صفحه candidate → $0.05
- بسیار کم! 😊
```

---

## 📝 نکات مهم

1. **غیرفعال به صورت پیش‌فرض:**
   - `auto_extract_products = False`
   - باید دستی فعال کنید

2. **Pre-filter هوشمند:**
   - فقط صفحاتی که شبیه محصول هستند پردازش میشن
   - صرفه‌جویی در هزینه AI

3. **Non-breaking:**
   - اگه خطا بخوره، فقط product extraction fail میشه
   - Q&A و crawl ادامه پیدا می‌کنن

4. **Source tracking:**
   - هر محصول به صفحه و website منبع لینک میشه
   - می‌تونید ببینید از کجا extract شده

---

## 🎉 موفقیت!

اگه همه تست‌ها OK بود:

✅ سیستم آماده production است!
✅ می‌تونید برای websiteهای واقعی فعالش کنید
✅ محصولات خودکار استخراج و ذخیره میشن
✅ AI می‌تونه از این محصولات برای پاسخ‌دهی استفاده کنه

---

**نویسنده:** AI Assistant  
**تاریخ:** October 2025  
**نسخه:** 1.0

