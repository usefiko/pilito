# 🔑 Migration: Keywords از Code به Database

## چرا این تغییر؟

قبلاً keywords در دو جا بودند:
1. **DEFAULT_KEYWORDS** (هاردکد در `query_router.py`)
2. **IntentKeyword Model** (در database و admin panel)

این باعث می‌شد:
- ❌ Duplicate logic
- ❌ مدیریت سخت (باید دو جا تغییر می‌دادید)
- ❌ Inconsistency

## راه حل جدید

✅ **همه keywords فقط در database هستند**
- مدیریت از admin panel
- بدون duplicate
- Consistency کامل

## مراحل Migration

### 1️⃣ Seed کردن Default Keywords

```bash
cd src
python manage.py seed_default_keywords
```

این command:
- همه keywords از `DEFAULT_KEYWORDS` را به database منتقل می‌کند
- فقط keywords جدید را اضافه می‌کند (duplicate نمی‌سازد)
- Cache را clear می‌کند

### 2️⃣ بررسی نتایج

```bash
python manage.py test_keywords
```

این command بررسی می‌کند:
- آیا keywords از database درست خوانده می‌شوند؟
- آیا user-specific keywords کار می‌کنند؟

### 3️⃣ مدیریت از Admin Panel

بعد از seed کردن:
- همه keywords در admin panel قابل مشاهده و ویرایش هستند
- می‌توانید keywords جدید اضافه کنید
- می‌توانید keywords موجود را ویرایش یا حذف کنید
- می‌توانید user-specific keywords اضافه کنید

## اولویت Keywords

1. **User-specific keywords** (بالاترین اولویت)
   - اگر user داشته باشد، keywords مخصوص آن user استفاده می‌شود
   - در admin panel می‌توانید برای هر user keywords خاص تعریف کنید

2. **Global keywords** (از database)
   - Keywords عمومی که برای همه کاربران استفاده می‌شود
   - در admin panel با `user=None` تعریف می‌شوند

3. **Default keywords** (فقط fallback)
   - فقط اگر database خالی باشد استفاده می‌شود
   - در production نباید اتفاق بیفتد
   - Warning در لاگ نمایش داده می‌شود

## تغییرات در Code

### قبل:
```python
# Keywords از database + defaults merge می‌شدند
if db_keywords:
    # Merge با defaults
    for intent in DEFAULT_KEYWORDS:
        if lang not in db_keywords[intent]:
            db_keywords[intent][lang] = DEFAULT_KEYWORDS[intent][lang]
```

### بعد:
```python
# فقط از database استفاده می‌شود
if db_keywords:
    # فقط database keywords (بدون merge)
    for intent in intents_to_check:
        if lang not in db_keywords[intent]:
            db_keywords[intent][lang] = []  # Empty, not default
```

## مزایا

✅ **مدیریت متمرکز**: همه keywords در admin panel
✅ **بدون Duplicate**: فقط یک منبع حقیقت
✅ **User-specific**: می‌توانید برای هر user keywords خاص تعریف کنید
✅ **Consistency**: همه keywords از یک جا می‌آیند
✅ **Audit Trail**: می‌توانید ببینید چه کسی چه keyword را اضافه/ویرایش کرده

## نکات مهم

1. **اولین بار**: حتماً `seed_default_keywords` را اجرا کنید
2. **Cache**: بعد از تغییر keywords در admin، cache به صورت خودکار clear می‌شود
3. **Fallback**: Default keywords فقط برای backward compatibility هستند
4. **Production**: در production باید همه keywords در database باشند

## Troubleshooting

### مشکل: "No keywords found in database"
**راه حل**: 
```bash
python manage.py seed_default_keywords
```

### مشکل: Keywords تغییر نمی‌کنند
**راه حل**: 
- Cache را clear کنید
- یا صبر کنید (cache 1 ساعت expire می‌شود)

### مشکل: User-specific keywords کار نمی‌کنند
**راه حل**: 
- مطمئن شوید که `user` field در IntentKeyword درست set شده
- مطمئن شوید که `is_active=True`

## مثال استفاده

### اضافه کردن Keyword جدید:
1. به admin panel بروید: `/admin/AI_model/intentkeyword/`
2. روی "Add Intent Keyword" کلیک کنید
3. Intent, Language, Keyword را انتخاب کنید
4. Weight را تنظیم کنید (0.1-3.0)
5. User را خالی بگذارید برای global، یا user خاص انتخاب کنید
6. Save کنید

### اضافه کردن User-specific Keyword:
1. همان مراحل بالا
2. در فیلد "User" کاربر مورد نظر را انتخاب کنید
3. این keyword فقط برای آن user استفاده می‌شود

## خلاصه

- ✅ همه keywords در database
- ✅ مدیریت از admin panel
- ✅ User-specific keywords پشتیبانی می‌شود
- ✅ Default keywords فقط fallback (برای backward compatibility)

