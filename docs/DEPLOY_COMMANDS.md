# 🚀 دستورات Deployment برای سرور

## روش 1: استفاده از اسکریپت (پیشنهادی)

```bash
cd /Users/omidataei/Documents/GitHub/pilito2/Untitled
./deploy_to_server.sh
```

## روش 2: دستورات مستقیم (Copy-Paste)

### مرحله 1: اتصال به سرور

```bash
ssh root@185.164.72.165
# Password: 9188945776poST?
```

### مرحله 2: پیدا کردن مسیر پروژه

```bash
# پیدا کردن مسیر پروژه
find /root /var/www /opt -name "manage.py" -type f 2>/dev/null | head -1

# یا اگر می‌دانید مسیر چیست:
cd /root/pilito/src
# یا
cd /var/www/pilito/src
# یا
cd /opt/pilito/src
```

### مرحله 3: Pull کردن کد

```bash
# اگر git repository است:
git pull origin main

# اگر نیست، باید کد را از جای دیگری کپی کنید
```

### مرحله 4: فعال کردن Virtual Environment (اگر وجود دارد)

```bash
source venv/bin/activate
# یا
source ../venv/bin/activate
```

### مرحله 5: اجرای Migrations

```bash
python manage.py migrate --noinput
```

### مرحله 6: Seed کردن Keywords (مهم!)

```bash
python manage.py seed_default_keywords
```

### مرحله 7: بررسی Keywords

```bash
python manage.py test_keywords
```

### مرحله 8: Collect Static Files

```bash
python manage.py collectstatic --noinput
```

### مرحله 9: Restart کردن سرویس‌ها

#### اگر از Docker استفاده می‌کنید:
```bash
docker-compose restart web celery worker
# یا
docker restart $(docker ps | grep pilito | awk '{print $1}')
```

#### اگر از systemd استفاده می‌کنید:
```bash
systemctl restart gunicorn
systemctl restart celery
```

#### اگر از supervisor استفاده می‌کنید:
```bash
supervisorctl restart all
```

### مرحله 10: بررسی لاگ‌ها

```bash
# Docker:
docker logs -f <container_name>

# systemd:
journalctl -u gunicorn -f
journalctl -u celery -f

# یا لاگ‌های Django:
tail -f /var/log/django.log
```

## دستورات یکجا (Copy-Paste)

```bash
# اتصال به سرور و اجرای همه دستورات
ssh root@185.164.72.165 << 'ENDSSH'
cd /root/pilito/src || cd /var/www/pilito/src || cd /opt/pilito/src
git pull origin main
source venv/bin/activate 2>/dev/null || true
python manage.py migrate --noinput
python manage.py seed_default_keywords
python manage.py test_keywords
python manage.py collectstatic --noinput
docker-compose restart web celery worker 2>/dev/null || systemctl restart gunicorn celery 2>/dev/null || supervisorctl restart all 2>/dev/null
echo "✅ Deployment completed!"
ENDSSH
```

## نکات مهم

1. **مسیر پروژه**: باید مسیر دقیق پروژه را پیدا کنید
2. **Virtual Environment**: اگر venv دارید، باید فعال کنید
3. **Keywords**: حتماً `seed_default_keywords` را اجرا کنید
4. **Restart**: بعد از تغییرات، سرویس‌ها را restart کنید

## Troubleshooting

### مشکل: "manage.py not found"
```bash
# پیدا کردن مسیر:
find / -name "manage.py" -type f 2>/dev/null
```

### مشکل: "git pull failed"
```bash
# بررسی وضعیت git:
git status
git remote -v
```

### مشکل: "Keywords not found"
```bash
# بررسی keywords در database:
python manage.py shell
>>> from AI_model.models import IntentKeyword
>>> IntentKeyword.objects.filter(user__isnull=True).count()
```

### مشکل: "Service restart failed"
```bash
# بررسی سرویس‌های فعال:
systemctl list-units --type=service | grep -E "gunicorn|celery"
docker ps
supervisorctl status
```

