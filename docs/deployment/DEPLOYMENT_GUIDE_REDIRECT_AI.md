# 🚀 راهنمای کامل Deploy - Redirect to AI Feature

## 📌 خلاصه تغییرات

این feature امکان redirect مکالمات به AI یا Support را فراهم می‌کند:

✅ **تغییرات اعمال شده:**
1. اضافه شدن `('ai', 'AI Assistant')` به `REDIRECT_DESTINATIONS`
2. بهبود لاجیک `_execute_redirect_action` با error handling کامل
3. اضافه شدن logging جامع برای debug

---

## 🎯 چگونه کار می‌کند؟

### Redirect به AI (`destination='ai'`):
```
Workflow Action → redirect_destination='ai'
↓
1. Status = 'active'
2. Cache: ai_enabled = True
3. AI شروع به پاسخ‌دهی می‌کند
```

### Redirect به Support (`destination='support'`, 'sales', etc):
```
Workflow Action → redirect_destination='support'
↓
1. Status = 'support_active'
2. Cache: ai_enabled = False
3. AI متوقف می‌شود، support دستی فعال
```

---

## 📦 مراحل Deploy در Production

### مرحله 1: Backup (قبل از هر کاری!)

```bash
# 1. Backup از Database
cd /path/to/Fiko-Backend
sudo -u postgres pg_dump fiko_db > /backup/fiko_db_$(date +%Y%m%d_%H%M%S).sql

# 2. Backup از Redis (اختیاری ولی توصیه میشه)
redis-cli --rdb /backup/redis_$(date +%Y%m%d_%H%M%S).rdb

# 3. تایید backup
ls -lh /backup/
```

### مرحله 2: Pull کردن کد جدید

```bash
cd /path/to/Fiko-Backend

# چک کردن وضعیت فعلی
git status
git log --oneline -5

# Pull
git pull origin main

# یا اگه از branch دیگه‌ای کار می‌کنی:
git fetch origin
git checkout feature/redirect-to-ai
git pull origin feature/redirect-to-ai
```

### مرحله 3: چک کردن تغییرات

```bash
# دیدن فایل‌های تغییر یافته
git diff HEAD~1 HEAD --name-only

# باید این 2 فایل را ببینی:
# src/workflow/models.py
# src/workflow/services/node_execution_service.py

# دیدن تغییرات دقیق
git diff HEAD~1 HEAD src/workflow/models.py | grep -A 5 "REDIRECT_DESTINATIONS"
```

### مرحله 4: Virtual Environment

```bash
# Activate کردن venv
source venv/bin/activate

# یا اگه مسیر دیگه‌ای داری:
source /path/to/venv/bin/activate

# تایید Python version
python --version  # باید Python 3.8+ باشه

# آپدیت dependencies (اگه لازم باشه)
pip install -r src/requirements/production.txt
```

### مرحله 5: Migration (مهم‌ترین قسمت!)

```bash
# 1. چک کردن وضعیت migrations
python manage.py showmigrations workflow

# 2. ساخت migration جدید
python manage.py makemigrations workflow

# خروجی باید چیزی شبیه این باشه:
# Migrations for 'workflow':
#   workflow/migrations/0XXX_alter_actionnode_redirect_destination.py
#     - Alter field redirect_destination on actionnode

# 3. دیدن SQL که اجرا میشه (اختیاری ولی خیلی مفیده)
python manage.py sqlmigrate workflow 0XXX

# باید چیزی شبیه این ببینی (یا حتی هیچی!):
# -- این migration فقط Django metadata رو آپدیت می‌کنه
# -- هیچ تغییر واقعی در database نداره

# 4. تست dry-run (امن‌ترین روش)
python manage.py migrate workflow --plan

# 5. اجرای واقعی migration
python manage.py migrate workflow

# خروجی موفقیت‌آمیز:
# Running migrations:
#   Applying workflow.0XXX_alter_actionnode_redirect_destination... OK
```

---

## ⚠️ اگه Migration خطا داد

### خطای احتمالی 1: "No changes detected"

```bash
# علت: Migration قبلاً اجرا شده یا تغییری وجود نداره
# راه حل:
python manage.py migrate workflow --fake-initial
# یا
python manage.py showmigrations workflow
# اگه آخرین migration چک خورده، مشکلی نیست
```

### خطای احتمالی 2: "Conflicting migrations"

```bash
# راه حل:
python manage.py migrate workflow <previous_migration_number>
python manage.py makemigrations workflow --merge
python manage.py migrate workflow
```

### خطای احتمالی 3: Database connection failed

```bash
# چک کردن database
python manage.py dbshell
# اگه connect نشد:
sudo systemctl status postgresql
sudo systemctl start postgresql
```

---

## 🔄 Restart Services

### برای Systemd (معمولی):

```bash
# Restart Gunicorn/uWSGI
sudo systemctl restart gunicorn
# یا
sudo systemctl restart uwsgi

# Restart Celery Worker
sudo systemctl restart celery-worker

# Restart Celery Beat (اگه داری)
sudo systemctl restart celery-beat

# چک کردن status
sudo systemctl status gunicorn celery-worker

# دیدن لاگ‌های اخیر
sudo journalctl -u gunicorn -n 50 --no-pager
sudo journalctl -u celery-worker -n 50 --no-pager
```

### برای Supervisor:

```bash
# Restart همه
sudo supervisorctl restart all

# یا جداگانه
sudo supervisorctl restart fiko-backend
sudo supervisorctl restart celery-worker
sudo supervisorctl restart celery-beat

# چک کردن وضعیت
sudo supervisorctl status
```

### برای Docker (اگه استفاده می‌کنی):

```bash
# Rebuild و restart
docker-compose build backend
docker-compose up -d backend celery

# چک logs
docker-compose logs -f --tail=50 backend
```

---

## 🧪 تست در Production

### تست 1: API Endpoint

```bash
# چک کردن redirect destinations
curl -X GET "https://api.pilito.com/api/workflow/action-nodes/redirect_destinations/" \
     -H "Authorization: Bearer YOUR_TOKEN"

# باید 'ai' رو در لیست ببینی:
# [
#   {"value": "ai", "label": "AI Assistant"},
#   {"value": "support", "label": "Support"},
#   ...
# ]
```

### تست 2: Workflow در Dashboard

1. **ورود به Admin Panel:**
   - برو به `https://your-domain.com/admin/`
   - لاگین کن

2. **ساخت Workflow تست:**
   - یک workflow جدید بساز
   - یک Action Node اضافه کن
   - Type: `redirect_conversation`
   - Destination: `ai` انتخاب کن
   - Save

3. **تست Redirect به AI:**
   ```
   - یک پیام از customer بفرست
   - Workflow trigger بشه
   - چک کن: Conversation status = 'active'
   - چک کن: AI جواب می‌ده؟
   ```

4. **تست Redirect به Support:**
   ```
   - Destination رو به 'support' تغییر بده
   - دوباره trigger کن
   - چک کن: Conversation status = 'support_active'
   - چک کن: AI جواب نمی‌ده
   ```

### تست 3: Redis Cache

```bash
# Connect به Redis
redis-cli

# چک کردن key های AI control
KEYS ai_control_*

# دیدن یک key خاص
GET ai_control_abc123

# باید چیزی شبیه این ببینی:
# {"ai_enabled": true}  یا  {"ai_enabled": false}

# خروج
EXIT
```

### تست 4: Logs

```bash
# دیدن لاگ‌های Redirect
tail -f /var/log/fiko/workflow.log | grep -i redirect

# باید چیزهایی شبیه این ببینی:
# [INFO] [Redirect to AI] Conversation abc123: will enable AI, set status to 'active'
# [INFO] ✓ Conversation abc123 status updated: support_active -> active
# [INFO] ✓ AI control cache set: conversation=abc123, ai_enabled=True
# [INFO] ✅ [Redirect Complete] Conversation abc123 redirected to 'ai': status support_active->active, AI=enabled
```

---

## 📊 Monitoring بعد از Deploy

### دستورات مفید:

```bash
# تعداد conversation های active
python manage.py shell << EOF
from message.models import Conversation
print("Active:", Conversation.objects.filter(status='active').count())
print("Support Active:", Conversation.objects.filter(status='support_active').count())
EOF

# چک کردن Redis memory usage
redis-cli INFO memory | grep human

# چک کردن Celery tasks
celery -A core inspect active

# چک کردن error rate
grep -i error /var/log/fiko/workflow.log | tail -20
```

### Metrics مهم:

- تعداد redirect به AI در ساعت
- تعداد redirect به Support در ساعت
- Error rate (باید < 1% باشه)
- Redis hit rate (باید > 95% باشه)

---

## 🚨 Rollback (اگه مشکل جدی پیش اومد)

### مرحله 1: Rollback Git

```bash
cd /path/to/Fiko-Backend

# پیدا کردن commit قبلی
git log --oneline -10

# Rollback
git revert HEAD
# یا
git reset --hard <previous_commit_hash>

# Push (اگه نیازه)
git push origin main
```

### مرحله 2: Rollback Migration

```bash
# برگشت به migration قبلی
python manage.py migrate workflow <previous_migration_number>

# مثال:
python manage.py migrate workflow 0015
```

### مرحله 3: Restart Services

```bash
sudo systemctl restart gunicorn celery-worker
```

### مرحله 4: Restore Backup (در بدترین حالت)

```bash
# Restore database
sudo -u postgres psql fiko_db < /backup/fiko_db_TIMESTAMP.sql

# Restart Redis
sudo systemctl restart redis
```

---

## ✅ Checklist نهایی

قبل از Deploy:
- [x] Backup از database گرفته شد
- [x] Code review شد
- [x] در dev environment تست شد
- [x] Migration بررسی شد
- [x] Redis در دسترس است

حین Deploy:
- [ ] Git pull موفق بود
- [ ] Migration بدون خطا اجرا شد
- [ ] Services restart شدند
- [ ] API endpoint پاسخ می‌دهد

بعد از Deploy:
- [ ] Redirect به AI کار می‌کند
- [ ] Redirect به Support کار می‌کند
- [ ] Logs نرمال هستند
- [ ] AI به درستی فعال/غیرفعال می‌شود
- [ ] هیچ error غیرمعمولی در logs نیست

---

## 📞 در صورت مشکل

### Log Files مهم:

```
/var/log/fiko/workflow.log     # لاگ‌های workflow
/var/log/fiko/django.log       # لاگ‌های کلی Django
/var/log/fiko/celery.log       # لاگ‌های Celery
/var/log/redis/redis.log       # لاگ‌های Redis
/var/log/nginx/error.log       # لاگ‌های Nginx
```

### دستورات Debug:

```bash
# چک کردن وضعیت کلی سیستم
sudo systemctl status gunicorn celery-worker redis nginx

# دیدن CPU و Memory usage
htop
# یا
top

# دیدن disk usage
df -h

# چک کردن Redis
redis-cli ping
redis-cli INFO stats
```

---

## 📚 مستندات مرتبط

- [REDIRECT_AI_IMPLEMENTATION.md](./REDIRECT_AI_IMPLEMENTATION.md) - جزئیات تکنیکال
- [WORKFLOW_DOCUMENTATION.md](./docs/WORKFLOW_DOCUMENTATION.md) - راهنمای کلی workflow
- Django Migration Docs: https://docs.djangoproject.com/en/stable/topics/migrations/

---

## 🎉 پس از Deploy موفق

- تیم را مطلع کن که feature جدید deploy شد
- در Frontend می‌تونید option "AI Assistant" رو در redirect destinations اضافه کنید
- مانیتور کنید که همه چیز درست کار می‌کنه

---

**نسخه:** 1.0.0  
**تاریخ:** 2025-01-04  
**وضعیت:** ✅ آماده Deploy

---

## ❓ سوالات متداول

### Q: Migration چقدر طول می‌کشه؟
**A:** کمتر از 1 ثانیه. این migration فقط Django metadata رو آپدیت می‌کنه، هیچ تغییر واقعی در database نداره.

### Q: Downtime لازم داره؟
**A:** خیر! می‌تونی بدون downtime deploy کنی.

### Q: رکوردهای قدیمی مشکل پیدا نمی‌کنن؟
**A:** نه، رکوردهای قدیمی با `redirect_destination` های قبلی (support, sales, ...) همون‌طور کار می‌کنن.

### Q: اگه Redis down باشه چی میشه؟
**A:** Status conversation هنوز تغییر می‌کنه، فقط AI control cache set نمیشه و یک warning لاگ میشه. سیستم خراب نمیشه.

### Q: چطوری می‌فهمم کار کرد؟
**A:** Log ها رو چک کن. باید پیام‌های "✅ [Redirect Complete]" رو ببینی با جزئیات کامل.

