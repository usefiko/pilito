# 📖 راهنمای استفاده از Intent Keywords

## 📁 فایل‌های موجود:

1. **INTENT_KEYWORDS_GUIDE.md** → راهنمای کامل برای AI
2. **INTENT_KEYWORDS_EXAMPLE_OUTPUT.json** → نمونه فرمت خروجی
3. **این فایل** → راهنمای استفاده

---

## 🎯 مراحل کار:

### مرحله 1️⃣: ارسال به AI

فایل `INTENT_KEYWORDS_GUIDE.md` رو به یکی از این AIها بفرست:

- **ChatGPT (GPT-4)** ✅ توصیه می‌شه
- **Claude (Sonnet/Opus)** ✅ توصیه می‌شه  
- **Gemini 1.5 Pro** ✅ خوب کار می‌کنه

**دستور به AI:**
```
من این راهنما رو بهت می‌دم. لطفاً یک فایل JSON کامل با 250-300 کلمه کلیدی 
برای 5 Intent تولید کن. خروجی باید دقیقاً مثل INTENT_KEYWORDS_EXAMPLE_OUTPUT.json باشه.

تمرکز اصلی رو بذار روی:
1. فارسی (اولویت اول) - حداقل 20 کلمه برای هر Intent
2. انگلیسی (اولویت دوم) - حداقل 15 کلمه برای هر Intent
3. عربی و ترکی (اختیاری) - 10-12 کلمه برای هر Intent

کلمات باید:
- طبیعی و کاربردی باشن
- املای متفاوت رو شامل بشن (مثلاً "میخوام" و "می‌خوام")
- عامیانه هم داشته باشن
- وزن‌دهی منطقی داشته باشن
```

---

### مرحله 2️⃣: دریافت و ذخیره

AI یک فایل JSON بهت میده. ذخیره‌ش کن با نام:
```
intent_keywords_generated.json
```

---

### مرحله 3️⃣: Import به Django

دو راه داری:

#### **راه 1: استفاده از Django Management Command** (ساده‌تر)

یک فایل Python بساز:

**فایل: `src/AI_model/management/commands/import_keywords.py`**

```python
import json
from django.core.management.base import BaseCommand
from AI_model.models import IntentKeyword

class Command(BaseCommand):
    help = 'Import Intent Keywords from JSON file'
    
    def add_arguments(self, parser):
        parser.add_argument('json_file', type=str, help='Path to JSON file')
    
    def handle(self, *args, **options):
        json_file = options['json_file']
        
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        total = 0
        for intent_name, intent_data in data['intents'].items():
            for kw in intent_data['keywords']:
                obj, created = IntentKeyword.objects.get_or_create(
                    intent=kw['intent'],
                    language=kw['language'],
                    keyword=kw['keyword'],
                    user=None,  # Global
                    defaults={
                        'weight': kw['weight'],
                        'is_active': kw['is_active']
                    }
                )
                if created:
                    total += 1
                    self.stdout.write(
                        self.style.SUCCESS(f'✅ Added: {kw["language"]} - {kw["keyword"]}')
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING(f'⚠️ Exists: {kw["language"]} - {kw["keyword"]}')
                    )
        
        self.stdout.write(
            self.style.SUCCESS(f'\n🎉 Imported {total} new keywords!')
        )
```

**اجرا:**
```bash
# Local
python src/manage.py import_keywords intent_keywords_generated.json

# Docker
docker compose exec web python manage.py import_keywords /app/intent_keywords_generated.json
```

---

#### **راه 2: استفاده از Django Shell** (دستی)

```bash
docker compose exec web python manage.py shell
```

در shell:
```python
import json
from AI_model.models import IntentKeyword

# بارگذاری JSON
with open('intent_keywords_generated.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Import کردن
total = 0
for intent_name, intent_data in data['intents'].items():
    for kw in intent_data['keywords']:
        obj, created = IntentKeyword.objects.get_or_create(
            intent=kw['intent'],
            language=kw['language'],
            keyword=kw['keyword'],
            user=None,
            defaults={
                'weight': kw['weight'],
                'is_active': kw['is_active']
            }
        )
        if created:
            total += 1
            print(f"✅ Added: {kw['keyword']}")

print(f"\n🎉 Total imported: {total} keywords")
```

---

#### **راه 3: استفاده از Django Admin** (یکی یکی)

اگه تعداد کم باشه:

1. برو به Django Admin: `https://your-domain.com/admin/`
2. بخش **AI Model** → **Intent Keywords**
3. کلیک روی **Add Intent Keyword**
4. پر کن:
   - Intent: انتخاب کن (pricing, product, howto, contact, general)
   - Language: انتخاب کن (fa, en, ar, tr)
   - Keyword: بنویس
   - Weight: عدد بین 0.5 تا 3.0
   - User: خالی بذار (برای Global)
   - Is active: ✅

---

### مرحله 4️⃣: تست کردن

بعد از import، تست کن که کار می‌کنه:

```bash
docker compose exec web python manage.py shell
```

```python
from AI_model.services.query_router import QueryRouter

# تست 1: سوال قیمت
result = QueryRouter.route_query("قیمت این محصول چقدره؟")
print(result)
# باید نشون بده: intent='pricing', confidence > 0.7

# تست 2: سوال محصول
result = QueryRouter.route_query("چه محصولاتی دارید؟")
print(result)
# باید نشون بده: intent='product', confidence > 0.7

# تست 3: سوال آموزش
result = QueryRouter.route_query("چطور استفاده کنم؟")
print(result)
# باید نشون بده: intent='howto', confidence > 0.7
```

---

## ✅ چک‌لیست نهایی:

- [ ] فایل `INTENT_KEYWORDS_GUIDE.md` رو به AI فرستادی
- [ ] فایل JSON کامل رو دریافت کردی (250-300 کلمه)
- [ ] بررسی کردی که فارسی کافی داره (حداقل 100 کلمه فارسی)
- [ ] Import کردی به Django
- [ ] تست کردی با چند سوال نمونه
- [ ] Django Admin رو چک کردی که Keywords اضافه شدن

---

## 🆘 مشکلات رایج:

### ❌ مشکل: "IntentKeyword matching query does not exist"
**راه حل:** اطمینان حاصل کن که Intent در choices موجوده:
```python
# src/AI_model/models.py
INTENT_CHOICES = [
    ('pricing', 'Pricing & Plans'),
    ('product', 'Product Info'),
    ('howto', 'How-to & Tutorial'),
    ('contact', 'Contact & Support'),
    ('general', 'General Question'),
]
```

### ❌ مشکل: "duplicate key value violates unique constraint"
**راه حل:** این keyword قبلاً اضافه شده. می‌تونی:
1. نادیده بگیری (skip)
2. یا update کنی

### ❌ مشکل: "UnicodeDecodeError"
**راه حل:** فایل رو با UTF-8 بخون:
```python
with open('file.json', 'r', encoding='utf-8') as f:
```

---

## 📞 پشتیبانی:

اگه مشکلی داشتی:
1. Log های Django رو چک کن
2. بررسی کن که فرمت JSON درسته
3. مطمئن شو که database connection سالمه

---

**موفق باشی!** 🚀

