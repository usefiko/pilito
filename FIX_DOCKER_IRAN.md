# 🔧 راه‌حل مشکل Docker در سرور ایران

## ❌ مشکل
```
pull access denied for prom/prometheus, repository does not exist or may require 'docker login': denied: 403 Forbidden
```

**دلیل:** Docker Hub دسترسی از IP های ایرانی رو block کرده.

---

## ⚠️ هشدار مهم

**این اسکریپت فقط برای سرورهای داخل ایران است!**

- ✅ اگر VPS شما در ایران هست → این اسکریپت رو اجرا کنید
- ❌ اگر VPS شما خارج از ایران هست → نیازی به این اسکریپت نیست (ممکنه سرعت کم بشه)

---

## ✅ راه‌حل‌های موجود

### 🎯 راه‌حل 1: استفاده از Registry Mirror ایرانی (توصیه می‌شود)

#### قدم 1: SSH به VPS
```bash
ssh root@185.164.72.165
```

#### قدم 2: دانلود و اجرای اسکریپت
```bash
cd /root/pilito

# دانلود اسکریپت (اگر با git pull اومده باشه)
chmod +x fix_docker_registry.sh
sudo ./fix_docker_registry.sh
```

یا اگر فایل وجود نداره، دستی بسازش:
```bash
nano fix_docker_registry.sh
```

#### قدم 3: تست
```bash
# تست pull کردن یک image
docker pull hello-world:latest

# اگر موفق شد
docker rmi hello-world:latest
```

#### قدم 4: Deploy مجدد
```bash
cd /root/pilito

# پاک کردن containerهای قبلی
docker-compose down

# Build و Start مجدد
docker-compose build --pull
docker-compose up -d
```

---

### 🎯 راه‌حل 2: استفاده از Shecan DNS (اگر راه‌حل 1 کار نکرد)

```bash
# تغییر DNS به Shecan
sudo nano /etc/resolv.conf
```

اضافه کردن این خطوط:
```
nameserver 178.22.122.100
nameserver 185.51.200.2
```

بعد:
```bash
sudo systemctl restart docker
```

---

### 🎯 راه‌حل 3: استفاده از چند Mirror با Fallback

اسکریپت `fix_docker_registry.sh` این قابلیت رو داره که چند mirror رو تست می‌کنه:

```json
{
  "registry-mirrors": [
    "https://docker.iranrepo.ir",      // Mirror اصلی ایران
    "https://registry.docker.ir",       // Mirror پشتیبان ایران  
    "https://dockerhub.ir",             // Mirror سوم ایران
    "https://mirror.gcr.io"             // Mirror بین‌المللی (fallback)
  ]
}
```

**مزیت:** اگه یکی از mirrorها down بود، خودکار به بقیه متصل میشه! 🎯

---

## 🧠 نکات مهم (برای آینده)

### ⚡ بهبودهای احتمالی:

1. **Healthcheck قبل از استفاده:**
   - اسکریپت الان قبل از configure، mirrorها رو تست می‌کنه
   - اگه همه down بودن، به mirror بین‌المللی fallback می‌کنه

2. **Monitoring Mirrors:**
   ```bash
   # بررسی وضعیت mirrorها
   curl -I https://docker.iranrepo.ir
   curl -I https://registry.docker.ir
   ```

3. **لاگ کردن:**
   - تمام تغییرات backup می‌شن
   - فایل قدیمی: `/etc/docker/daemon.json.backup.YYYYMMDD_HHMMSS`

---

## 📝 بعد از Fix

وقتی مشکل حل شد، دوباره push کن:

```bash
# در local machine
cd /Users/omidataei/Documents/GitHub/pilito2/Untitled

# Add تغییرات
git add src/message/consumers.py
git add BACKEND_WEBSOCKET_CHANGES_SUMMARY.md
git add WEBSOCKET_RECONNECT_GUIDE.md
git add fix_docker_registry.sh
git add FIX_DOCKER_IRAN.md

git commit -m "✨ Fix WebSocket reconnect + Docker registry fix

- Add connection_established message to all consumers
- Improve JWT token validation
- Add authentication_error handling
- Add Docker registry mirror configuration for Iranian VPS
- Add healthcheck for registry mirrors
- Add international fallback mirror
"

git push origin main
```

---

## 🔍 بررسی وضعیت

در VPS بعد از fix:

```bash
# بررسی Docker daemon.json
cat /etc/docker/daemon.json

# بررسی Docker info
docker info | grep -A 5 "Registry Mirrors"

# تست pull
docker pull nginx:alpine

# بررسی containerها
docker-compose ps

# بررسی لاگ‌ها
docker-compose logs -f --tail=50
```

---

## ⚠️ اگر همچنان کار نکرد

### گزینه A: بررسی Firewall و Network

```bash
# بررسی اتصال به mirrorها
curl -v https://docker.iranrepo.ir
curl -v https://registry.docker.ir

# بررسی DNS
nslookup docker.iranrepo.ir
```

### گزینه B: استفاده از VPN در VPS

```bash
# نصب و راه‌اندازی VPN client در VPS
# (نیاز به VPN subscription دارد)
```

### گزینه C: Pre-pull Images در GitHub Actions

می‌تونیم images رو در GitHub Actions (که IP آمریکایی داره) pull کنیم و به VPS بفرستیم.

---

## 💡 توصیه نهایی

**بهترین ترکیب:**
1. ✅ Registry Mirrors (راه‌حل 1)
2. ✅ Shecan DNS (راه‌حل 2)
3. ✅ Healthcheck و Fallback (در اسکریپت اضافه شده)

این ترکیب 95% مشکلات Docker در ایران رو حل می‌کنه! 🎉

---

## 🎯 چک‌لیست قبل از Deploy

- [ ] اسکریپت در مسیر root پروژه قرار داره
- [ ] اسکریپت executable هست (`chmod +x`)
- [ ] در VPS اجرا شده و Docker restart شده
- [ ] تست pull موفقیت‌آمیز بوده
- [ ] `docker info` نشون میده mirrorها configure شدن
- [ ] آماده push و deploy مجدد

---

## 📞 نیاز به کمک؟

اگر همچنان مشکل دارید:
1. لاگ کامل Docker رو بفرستید: `sudo journalctl -xeu docker`
2. خروجی `docker info` رو بفرستید
3. خروجی `cat /etc/docker/daemon.json` رو بفرستید
4. تست کنید: `curl -I https://docker.iranrepo.ir`
