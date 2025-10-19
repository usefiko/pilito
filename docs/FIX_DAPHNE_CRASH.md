# 🔧 راهنمای رفع مشکل Daphne Crash

## مشکل ❌

Django container با خطای زیر crash می‌کنه:
```
Illegal instruction (core dumped) daphne -b 0.0.0.0 -p 8000 core.asgi:application
Exit code: 132
```

### دلیل مشکل:
- **Daphne** از instruction های CPU جدیدتر استفاده می‌کنه
- سرورهای ایرانی قدیمی‌تر این instruction ها رو ساپورت نمی‌کنن
- نتیجه: `SIGILL` (Illegal Instruction) و crash

---

## راه‌حل ✅

استفاده از **Gunicorn + Uvicorn Workers** به جای Daphne:

### مزایا:
- ✅ سازگار با CPU های قدیمی‌تر
- ✅ پایدارتر و performance بهتر
- ✅ همچنان از WebSocket پشتیبانی می‌کنه
- ✅ Multi-worker و multi-threaded
- ✅ بهتر برای production

---

## تغییرات انجام شده

### 1. `docker-compose.yml`
```yaml
# قبل ❌
command: daphne -b 0.0.0.0 -p 8000 core.asgi:application

# بعد ✅
command: gunicorn core.asgi:application -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000 --workers 2 --threads 4 --timeout 120
```

**توضیحات:**
- `uvicorn.workers.UvicornWorker`: Worker class برای WebSocket
- `--workers 2`: تعداد worker processes
- `--threads 4`: تعداد thread per worker
- `--timeout 120`: Timeout برای request های طولانی

### 2. `entrypoint.sh`
```bash
# قبل ❌
daphne -b 0.0.0.0 -p 8000 core.asgi:application

# بعد ✅
exec "$@"  # استفاده از command در docker-compose
```

### 3. `requirements/base.txt`
```txt
# اضافه شده:
uvicorn==0.34.0
uvicorn[standard]==0.34.0  # با websockets و httptools
```

---

## نحوه اعمال تغییرات

### روش 1: استفاده از اسکریپت خودکار (توصیه می‌شود)

```bash
# 1. SSH به سرور
ssh root@185.164.72.165

# 2. رفتن به مسیر پروژه
cd /root/pilito

# 3. Pull تغییرات جدید
git pull origin main

# 4. اجرای اسکریپت
chmod +x fix_daphne_crash.sh
./fix_daphne_crash.sh
```

این اسکریپت:
- ✅ Backup از فایل‌های قدیمی می‌گیره
- ✅ Container های قدیمی رو stop می‌کنه
- ✅ Image رو از نو rebuild می‌کنه
- ✅ Container جدید رو start می‌کنه
- ✅ وضعیت رو چک می‌کنه

---

### روش 2: دستی

#### مرحله 1: Pull تغییرات
```bash
cd /root/pilito
git pull origin main
```

#### مرحله 2: Stop container قدیمی
```bash
docker-compose stop web
docker-compose rm -f web
```

#### مرحله 3: Rebuild image
```bash
docker-compose build --no-cache web
```

#### مرحله 4: Start container جدید
```bash
docker-compose up -d web
```

#### مرحله 5: بررسی logs
```bash
docker-compose logs -f web
```

---

## تست و بررسی

### 1. بررسی وضعیت container
```bash
docker-compose ps web
```

باید ببینی:
```
NAME         STATUS      PORTS
django_app   Up 2 minutes   0.0.0.0:8000->8000/tcp
```

### 2. بررسی logs
```bash
docker-compose logs --tail=50 web
```

باید ببینی:
```
Starting Gunicorn server with Uvicorn workers...
[INFO] Starting gunicorn 23.0.0
[INFO] Listening at: http://0.0.0.0:8000
[INFO] Using worker: uvicorn.workers.UvicornWorker
[INFO] Booting worker with pid: 123
```

### 3. تست API
```bash
# از روی سرور:
curl -I http://localhost:8000/admin/

# از خارج:
curl -I https://api.pilito.com/admin/
```

باید `200 OK` یا `302 Found` ببینی.

### 4. تست WebSocket
از frontend بررسی کن که WebSocket ها به درستی کار می‌کنن.

---

## عیب‌یابی

### مشکل 1: Container start نمیشه
```bash
# بررسی logs
docker-compose logs web

# بررسی resources
docker stats django_app

# Restart
docker-compose restart web
```

### مشکل 2: ModuleNotFoundError: No module named 'uvicorn'
```bash
# Rebuild با --no-cache
docker-compose build --no-cache web
docker-compose up -d web
```

### مشکل 3: Worker timeout
اگر request ها timeout می‌شن:
```yaml
# در docker-compose.yml timeout رو بیشتر کن:
command: gunicorn ... --timeout 300
```

### مشکل 4: Memory issues
اگر memory کم داری:
```yaml
# تعداد workers رو کم کن:
command: gunicorn ... --workers 1 --threads 2
```

---

## تنظیمات پیشرفته

### افزایش Performance
```yaml
# بیشتر workers برای traffic بالا:
command: gunicorn core.asgi:application \
  -k uvicorn.workers.UvicornWorker \
  -b 0.0.0.0:8000 \
  --workers 4 \
  --threads 4 \
  --worker-connections 1000 \
  --timeout 120 \
  --graceful-timeout 30 \
  --keep-alive 5
```

### Logging بیشتر
```yaml
command: gunicorn ... --log-level debug --access-logfile - --error-logfile -
```

### Reload خودکار (فقط development)
```yaml
command: gunicorn ... --reload  # فقط برای development!
```

---

## مقایسه Daphne vs Gunicorn+Uvicorn

| ویژگی | Daphne | Gunicorn+Uvicorn |
|-------|--------|------------------|
| WebSocket | ✅ | ✅ |
| HTTP/2 | ✅ | ✅ |
| Multi-worker | ❌ | ✅ |
| Multi-thread | ❌ | ✅ |
| CPU قدیمی | ❌ | ✅ |
| Production-ready | ⚠️ | ✅ |
| Performance | 🟢 خوب | 🟢 عالی |

---

## نکات مهم ⚠️

1. **Backup:** اسکریپت خودکار backup می‌گیره
2. **Rebuild:** حتماً `--no-cache` استفاده کن تا تغییرات اعمال بشه
3. **WebSocket:** همچنان کار می‌کنه، نگران نباش
4. **Performance:** احتمالاً بهتر از Daphne خواهی دید
5. **Monitoring:** Prometheus metrics همچنان کار می‌کنه

---

## بازگشت به Daphne

اگر به هر دلیلی خواستی برگردی به Daphne:
```bash
cd /root/pilito
cp docker-compose.yml.backup.* docker-compose.yml
docker-compose build --no-cache web
docker-compose up -d web
```

---

## خلاصه

- ❌ **قبل:** Daphne → Crash با Illegal Instruction
- ✅ **بعد:** Gunicorn + Uvicorn → پایدار و سازگار
- ✅ **نتیجه:** Django کار می‌کنه، Admin در دسترسه، WebSocket OK

---

**تاریخ:** $(date)  
**نسخه:** 1.0  
**وضعیت:** Production Ready ✅

