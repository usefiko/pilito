# 📖 راهنمای استفاده از Intent Routing

## 📁 فایل‌های موجود:

1. **INTENT_ROUTING_GUIDE.md** → راهنمای کامل برای AI
2. **INTENT_ROUTING_EXAMPLE_OUTPUT.json** → نمونه فرمت خروجی
3. **این فایل** → راهنمای استفاده

---

## 🎯 مراحل کار:

### مرحله 1️⃣: ارسال به AI

فایل `INTENT_ROUTING_GUIDE.md` رو به یکی از این AIها بفرست:

- **ChatGPT (GPT-4)** ✅ توصیه می‌شه
- **Claude (Sonnet/Opus)** ✅ توصیه می‌شه  
- **Gemini 1.5 Pro** ✅ خوب کار می‌کنه

**دستور به AI:**
```
من این راهنما رو بهت می‌دم. لطفاً یک فایل JSON کامل با 5 Intent Routing تولید کن.
خروجی باید دقیقاً مثل INTENT_ROUTING_EXAMPLE_OUTPUT.json باشه.

برای هر Intent:
1. Primary source مناسب انتخاب کن
2. Token budget بهینه تعیین کن
3. Secondary sources منطقی انتخاب کن
4. is_active رو true بذار

اصول مهم:
- Pricing → Primary: products
- Product → Primary: products  
- Howto → Primary: manual
- Contact → Primary: faq
- General → Primary: faq

Token budget ها:
- Primary: 600-800 توکن (بسته به پیچیدگی)
- Secondary: 200-400 توکن
- مجموع کل: کمتر از 1500 توکن
```

---

### مرحله 2️⃣: دریافت و ذخیره

AI یک فایل JSON بهت میده. ذخیره‌ش کن با نام:
```
intent_routing_generated.json
```

---

### مرحله 3️⃣: Import به Django

سه راه داری:

---

#### **راه 1: استفاده از Django Management Command** ⭐ توصیه می‌شه

یک فایل Python بساز:

**فایل: `src/AI_model/management/commands/import_routing.py`**

```python
import json
from django.core.management.base import BaseCommand
from AI_model.models import IntentRouting

class Command(BaseCommand):
    help = 'Import Intent Routing from JSON file'
    
    def add_arguments(self, parser):
        parser.add_argument('json_file', type=str, help='Path to JSON file')
    
    def handle(self, *args, **options):
        json_file = options['json_file']
        
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        total = 0
        for rule in data['routing_rules']:
            obj, created = IntentRouting.objects.update_or_create(
                intent=rule['intent'],
                defaults={
                    'primary_source': rule['primary_source'],
                    'primary_token_budget': rule['primary_token_budget'],
                    'secondary_sources': rule['secondary_sources'],
                    'secondary_token_budget': rule['secondary_token_budget'],
                    'is_active': rule['is_active']
                }
            )
            
            if created:
                total += 1
                self.stdout.write(
                    self.style.SUCCESS(f'✅ Created: {rule["intent"]} → {rule["primary_source"]}')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'🔄 Updated: {rule["intent"]} → {rule["primary_source"]}')
                )
        
        self.stdout.write(
            self.style.SUCCESS(f'\n🎉 Imported {total} new routing rules!')
        )
```

**اجرا:**
```bash
# Local
python src/manage.py import_routing intent_routing_generated.json

# Docker
docker compose exec web python manage.py import_routing /app/intent_routing_generated.json
```

---

#### **راه 2: استفاده از Django Shell** (دستی)

```bash
docker compose exec web python manage.py shell
```

در shell:
```python
import json
from AI_model.models import IntentRouting

# بارگذاری JSON
with open('intent_routing_generated.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Import کردن
for rule in data['routing_rules']:
    obj, created = IntentRouting.objects.update_or_create(
        intent=rule['intent'],
        defaults={
            'primary_source': rule['primary_source'],
            'primary_token_budget': rule['primary_token_budget'],
            'secondary_sources': rule['secondary_sources'],
            'secondary_token_budget': rule['secondary_token_budget'],
            'is_active': rule['is_active']
        }
    )
    
    if created:
        print(f"✅ Created: {rule['intent']}")
    else:
        print(f"🔄 Updated: {rule['intent']}")

print("\n🎉 Import completed!")
```

---

#### **راه 3: استفاده از Django Admin** (یکی یکی)

**برای 5 Intent تنظیم:**

1. برو به: `https://api.fiko.net/admin/AI_model/intentrouting/add/`

---

##### **1. Pricing & Plans:**
```
Intent: Pricing & Plans
Primary source: Products
Primary token budget: 800
Secondary sources: faq,manual    ← کاما بذار بینشون
Secondary token budget: 300
☑️ Is active
```
**Save**

---

##### **2. Product Info:**
```
Intent: Product Info
Primary source: Products
Primary token budget: 800
Secondary sources: website,faq
Secondary token budget: 300
☑️ Is active
```
**Save**

---

##### **3. How-to & Tutorial:**
```
Intent: How-to & Tutorial
Primary source: Manual Prompt
Primary token budget: 800
Secondary sources: website,faq
Secondary token budget: 300
☑️ Is active
```
**Save**

---

##### **4. Contact & Support:**
```
Intent: Contact & Support
Primary source: FAQ
Primary token budget: 600
Secondary sources: manual
Secondary token budget: 200
☑️ Is active
```
**Save**

---

##### **5. General Question:**
```
Intent: General Question
Primary source: FAQ
Primary token budget: 600
Secondary sources: manual,products,website
Secondary token budget: 400
☑️ Is active
```
**Save**

---

### مرحله 4️⃣: تست کردن

بعد از import، تست کن:

```bash
docker compose exec web python manage.py shell
```

```python
from AI_model.services.query_router import QueryRouter

# تست 1: سوال قیمت
result = QueryRouter.route_query("قیمت این محصول چقدره؟")
print(f"Intent: {result['intent']}")
print(f"Primary: {result['primary_source']}")
print(f"Primary Budget: {result['token_budgets']['primary']}")
print(f"Confidence: {result['confidence']}")
# Expected: intent='pricing', primary='products', budget=800

print("\n" + "="*50 + "\n")

# تست 2: سوال محصول
result = QueryRouter.route_query("چه محصولاتی دارید؟")
print(f"Intent: {result['intent']}")
print(f"Primary: {result['primary_source']}")
# Expected: intent='product', primary='products'

print("\n" + "="*50 + "\n")

# تست 3: سوال آموزش
result = QueryRouter.route_query("چطور استفاده کنم؟")
print(f"Intent: {result['intent']}")
print(f"Primary: {result['primary_source']}")
# Expected: intent='howto', primary='manual'

print("\n" + "="*50 + "\n")

# تست 4: سوال تماس
result = QueryRouter.route_query("شماره تماس شما چیه؟")
print(f"Intent: {result['intent']}")
print(f"Primary: {result['primary_source']}")
# Expected: intent='contact', primary='faq'

print("\n" + "="*50 + "\n")

# تست 5: سوال عمومی
result = QueryRouter.route_query("سلام، کمک می‌کنید؟")
print(f"Intent: {result['intent']}")
print(f"Primary: {result['primary_source']}")
# Expected: intent='general', primary='faq'
```

---

### مرحله 5️⃣: بررسی در Admin

برو به: `https://api.fiko.net/admin/AI_model/intentrouting/`

باید **5 رکورد** ببینی:

| Intent | Primary | Primary Budget | Secondary | Secondary Budget | Active |
|--------|---------|----------------|-----------|------------------|--------|
| Pricing & Plans | products | 800 | faq, manual | 300 | ✅ |
| Product Info | products | 800 | website, faq | 300 | ✅ |
| How-to & Tutorial | manual | 800 | website, faq | 300 | ✅ |
| Contact & Support | faq | 600 | manual | 200 | ✅ |
| General Question | faq | 600 | manual, products, website | 400 | ✅ |

---

## ✅ چک‌لیست نهایی:

- [ ] فایل `INTENT_ROUTING_GUIDE.md` رو به AI فرستادی
- [ ] فایل JSON کامل رو دریافت کردی (5 Intent)
- [ ] بررسی کردی که Primary sources درست هستن
- [ ] بررسی کردی که Token budgets منطقی هستن
- [ ] Import کردی به Django
- [ ] تست کردی با 5 سوال نمونه
- [ ] Django Admin رو چک کردی که 5 رکورد اضافه شدن
- [ ] همه رکوردها `is_active = True` هستن

---

## 🎯 نکات مهم:

### ✅ **درست:**
```
Secondary sources: faq,manual    ← بدون فاصله!
Secondary sources: website,faq
```

### ❌ **غلط:**
```
Secondary sources: faq, manual   ← فاصله داره! اشتباهه!
Secondary sources: [faq, manual] ← براکت نباید باشه!
```

---

## 🆘 مشکلات رایج:

### ❌ مشکل: "Intent matching query does not exist"
**راه حل:** مطمئن شو که Intent در choices موجوده:
```python
INTENT_CHOICES = [
    ('pricing', 'Pricing & Plans'),
    ('product', 'Product Info'),
    ('howto', 'How-to & Tutorial'),
    ('contact', 'Contact & Support'),
    ('general', 'General Question'),
]
```

### ❌ مشکل: "Source not in choices"
**راه حل:** Sources باید از این لیست باشن:
- `faq`
- `manual`
- `products`
- `website`

### ❌ مشکل: "Secondary sources parse error"
**راه حل:** 
- باید comma-separated باشه: `faq,manual`
- بدون فاصله!
- بدون براکت!

---

## 📊 آمار بعد از Setup:

وقتی همه چی ست شد، سیستم باید:

- ✅ **5 Intent** شناسایی کنه
- ✅ **Routing** به منابع درست
- ✅ **Token Budget** بهینه
- ✅ **سرعت** 40-50% بهتر
- ✅ **هزینه** 30-40% کمتر
- ✅ **دقت** 20-30% بیشتر

---

**موفق باشی!** 🚀

