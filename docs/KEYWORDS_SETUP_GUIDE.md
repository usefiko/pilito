# 🔑 راهنمای نصب Intent Keywords

## روش 1: استفاده از Admin Panel (توصیه می‌شود)

### مراحل:

1. **ورود به Admin Panel:**
   ```
   https://your-domain.com/admin/
   ```

2. **رفتن به بخش Intent Keywords:**
   ```
   AI Model → 🔑 Intent Keywords
   ```

3. **اضافه کردن Keywords:**
   - روی "Add Intent Keyword" کلیک کنید
   - فیلدها را پر کنید:
     - **Intent**: انتخاب کنید (pricing, product, howto, contact, general)
     - **Language**: زبان (fa, en, ar, tr)
     - **Keyword**: کلمه کلیدی
     - **Weight**: وزن (1.0 = عادی، 2.0 = مهم، 0.5 = کم‌اهمیت)
     - **User**: خالی بگذارید (برای global)
     - **Is Active**: ✅ فعال
   - "Save" کنید

---

## روش 2: Import با SQL (سریع‌تر)

### مراحل:

1. **فایل SQL را کپی کنید:**
   ```
   intent_keywords_complete.sql
   ```

2. **به سرور وصل شوید:**
   ```bash
   ssh root@185.164.72.165
   ```

3. **SQL را اجرا کنید:**
   ```bash
   docker exec -i postgres_db psql -U your_db_user -d your_db_name < intent_keywords_complete.sql
   ```

   یا:

   ```bash
   docker exec postgres_db psql -U your_db_user -d your_db_name -f /path/to/intent_keywords_complete.sql
   ```

4. **Cache را پاک کنید:**
   ```bash
   docker exec celery_ai python manage.py shell -c "from django.core.cache import cache; cache.clear()"
   ```

---

## روش 3: استفاده از Django Management Command

### ایجاد Command:

فایل: `src/AI_model/management/commands/populate_intent_keywords.py`

```python
from django.core.management.base import BaseCommand
from AI_model.models import IntentKeyword

class Command(BaseCommand):
    help = 'Populate intent keywords'

    def handle(self, *args, **options):
        keywords = [
            # Pricing - فارسی
            {'intent': 'pricing', 'language': 'fa', 'keyword': 'قیمت', 'weight': 1.5},
            {'intent': 'pricing', 'language': 'fa', 'keyword': 'چنده', 'weight': 1.5},
            # ... (بقیه keywords از فایل SQL)
        ]

        for kw in keywords:
            IntentKeyword.objects.get_or_create(
                intent=kw['intent'],
                language=kw['language'],
                keyword=kw['keyword'],
                user=None,
                defaults={'weight': kw['weight'], 'is_active': True}
            )

        self.stdout.write(self.style.SUCCESS('✅ Keywords populated!'))
```

### اجرا:

```bash
docker exec celery_ai python manage.py populate_intent_keywords
```

---

## بررسی Keywords

### در Admin Panel:

1. به `AI Model → 🔑 Intent Keywords` بروید
2. فیلتر کنید:
   - Intent: contact
   - Language: fa
3. باید ببینید:
   - ادرس ✅
   - ارسال ✅
   - نحوه ارسال ✅
   - ... و بقیه

### با Shell:

```python
from AI_model.models import IntentKeyword

# بررسی تعداد Keywords
print(f"Total: {IntentKeyword.objects.filter(user__isnull=True).count()}")

# بررسی contact keywords
contact_fa = IntentKeyword.objects.filter(
    intent='contact',
    language='fa',
    user__isnull=True
)
print(f"Contact (FA): {contact_fa.count()}")
for kw in contact_fa:
    print(f"  - {kw.keyword} (weight: {kw.weight})")
```

---

## تست

### تست با Query:

```python
from AI_model.services.query_router import QueryRouter
from accounts.models import User

user = User.objects.get(email='y_motahedin@yahoo.com')

# تست 1: آدرس
result = QueryRouter.route_query("ادرس شما کجاست؟", user)
print(f"Intent: {result['intent']}")  # باید 'contact' باشد

# تست 2: ارسال
result = QueryRouter.route_query("نحوه ارسالتون چطوریه؟", user)
print(f"Intent: {result['intent']}")  # باید 'contact' باشد

# تست 3: ارسال دارید
result = QueryRouter.route_query("ارسال دارید؟", user)
print(f"Intent: {result['intent']}")  # باید 'contact' یا 'product' باشد
```

---

## ⚠️ نکات مهم:

1. **Cache:**
   - Keywords در cache ذخیره می‌شوند (1 ساعت)
   - بعد از هر تغییر، cache را پاک کنید:
     ```python
     from django.core.cache import cache
     cache.delete_pattern('intent_keywords:*')
     ```

2. **Weight (وزن):**
   - 2.0 = خیلی مهم (مثل "ادرس"، "ارسال")
   - 1.5 = مهم (مثل "چطور"، "قیمت")
   - 1.0 = عادی
   - 0.5 = کم‌اهمیت (مثل "سلام")

3. **املای غلط:**
   - حتماً املاهای رایج غلط را اضافه کنید
   - مثال: "ادرس" و "آدرس" (هر دو)

4. **User-Specific:**
   - برای keywords خاص یک کاربر:
     - `user` را set کنید
   - برای global keywords:
     - `user` را خالی بگذارید (NULL)

---

## نتیجه

بعد از import کردن این Keywords:

✅ "ادرس شما کجاست؟" → Intent: **contact** (100%)
✅ "نحوه ارسالتون چطوریه؟" → Intent: **contact** (100%)  
✅ "ارسال دارید؟" → Intent: **contact** (100%)
✅ "قیمتش چنده؟" → Intent: **pricing** (100%)
✅ "چی دارین؟" → Intent: **product** (100%)

---

## پشتیبانی

اگر مشکلی بود:
1. Cache را پاک کنید
2. Keywords را در Admin بررسی کنید
3. لاگ‌ها را چک کنید:
   ```bash
   docker logs celery_ai | grep "Intent:"
   ```

