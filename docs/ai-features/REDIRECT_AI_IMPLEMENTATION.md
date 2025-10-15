# 🤖 Redirect to AI Implementation Guide

## 📋 خلاصه تغییرات

این تغییرات امکان redirect مکالمه به AI یا Support را فراهم می‌کند:
- **Redirect به AI:** status = `active`, AI enabled
- **Redirect به Support:** status = `support_active`, AI disabled

---

## 🔧 تغییرات اعمال شده

### 1. فایل: `src/workflow/models.py`
- اضافه شدن `('ai', 'AI Assistant')` به `REDIRECT_DESTINATIONS`

### 2. فایل: `src/workflow/services/node_execution_service.py`
- بهبود تابع `_execute_redirect_action` برای تفکیک AI و Support
- اضافه شدن error handling برای Redis cache

---

## 📦 Migration

### دستورات اجرا (روی سرور):

```bash
# 1. Pull کردن کد جدید
cd /path/to/Fiko-Backend
git pull origin main

# 2. Activate کردن virtual environment
source venv/bin/activate  # یا path خودت

# 3. ساخت migration
python manage.py makemigrations workflow

# 4. نمایش migration (برای بررسی)
python manage.py sqlmigrate workflow <migration_number>

# 5. اجرای migration
python manage.py migrate workflow

# 6. Restart کردن سرویس‌ها
# برای Gunicorn/uWSGI:
sudo systemctl restart gunicorn
# یا
sudo supervisorctl restart fiko-backend

# برای Celery:
sudo systemctl restart celery
# یا
sudo supervisorctl restart celery-worker
```

---

## ⚠️ تاثیرات Migration

### ✅ چیزهایی که تغییر نمی‌کنن:
- ❌ **هیچ data موجودی تغییر نمی‌کنه**
- ❌ **هیچ ستون جدیدی اضافه نمیشه**
- ❌ **هیچ index جدیدی ساخته نمیشه**
- ❌ **هیچ foreign key تغییر نمی‌کنه**

### ✅ تنها تغییر:
```python
# Migration فقط choices در model را آپدیت می‌کند:
migrations.AlterField(
    model_name='actionnode',
    name='redirect_destination',
    field=models.CharField(
        choices=[
            ('ai', 'AI Assistant'),  # 🆕 جدید
            ('support', 'Support'),
            ('sales', 'Sales'),
            ('technical', 'Technical'),
            ('billing', 'Billing'),
            ('general', 'General')
        ],
        ...
    ),
)
```

**این migration فقط metadata Django را آپدیت می‌کند، نه schema database!**

### 🔍 چرا ایمنه:
1. **هیچ تغییر در database schema نیست**
2. **رکوردهای قدیمی دست نخورده باقی می‌مانند**
3. **Downtime لازم نیست**
4. **Rollback آسان است**

---

## 🧪 تست در Production

### مرحله 1: بررسی اولیه
```bash
# چک کردن Redis
redis-cli ping
# باید PONG برگردونه

# چک کردن conversation statuses
python manage.py shell
>>> from message.models import Conversation
>>> Conversation.objects.values_list('status', flat=True).distinct()
# باید 'active', 'support_active', 'marketing_active', 'closed' را ببینید
```

### مرحله 2: تست Redirect به AI
1. در Frontend یک workflow بساز
2. یک action node با `redirect_destination='ai'` اضافه کن
3. Workflow را trigger کن
4. چک کن:
   - Status مکالمه باید `active` باشه
   - AI باید جواب بده

### مرحله 3: تست Redirect به Support
1. یک action node با `redirect_destination='support'` بساز
2. Workflow را trigger کن
3. چک کن:
   - Status مکالمه باید `support_active` باشه
   - AI نباید جواب بده

---

## 🚨 خطاهای احتمالی

### خطا: "Redis connection failed"
```python
# خطا در log:
[WARNING] Failed to set AI control cache: ConnectionError

# راه حل:
sudo systemctl status redis
sudo systemctl start redis
```

### خطا: "Migration conflict"
```bash
# خطا:
Conflicting migrations detected

# راه حل:
python manage.py migrate --fake workflow <previous_migration>
python manage.py migrate workflow
```

---

## 🔄 Rollback (اگر مشکلی پیش اومد)

```bash
# 1. برگشت به migration قبلی
python manage.py migrate workflow <previous_migration_number>

# 2. برگشت کد
git revert <commit_hash>
git push

# 3. Restart سرویس‌ها
sudo systemctl restart gunicorn celery
```

---

## 📊 Monitoring

### Log های مهم:

```bash
# بررسی log های workflow
tail -f /var/log/fiko/workflow.log

# جستجو برای redirect logs
grep "Redirect" /var/log/fiko/workflow.log

# جستجو برای AI control
grep "ai_control_" /var/log/fiko/workflow.log
```

### چیزهایی که باید ببینی:
```
[INFO] [Redirect to AI] Conversation abc123: AI enabled, status -> active
[INFO] [Redirect to support] Conversation xyz789: AI disabled, status -> support_active
```

---

## ✅ Checklist نهایی

قبل از Deploy:
- [ ] Code review انجام شده
- [ ] Redis در سرور در دسترس است
- [ ] Backup از database گرفته شده
- [ ] Migration در dev environment تست شده

بعد از Deploy:
- [ ] Migration با موفقیت اجرا شد
- [ ] Redirect به AI کار می‌کند
- [ ] Redirect به Support کار می‌کند
- [ ] AI به درستی فعال/غیرفعال می‌شود
- [ ] Log ها نرمال هستند

---

## 📞 در صورت مشکل

اگر مشکلی پیش اومد:
1. Log ها را چک کن
2. Redis را restart کن
3. در صورت لزوم rollback کن
4. مشکل را با جزئیات گزارش بده

---

تاریخ: 2025-01-04
نسخه: 1.0.0

