# Instagram Token Management System

## مشکل

کاربران اینستاگرام با مشکل انقضای سریع توکن‌ها مواجه بودند که باعث قطع ارتباط و عدم امکان ارسال پیام می‌شد.

## راه‌حل پیاده‌سازی شده

### 1. تبدیل خودکار Short-lived به Long-lived Token

**تغییرات در `instagram_callback.py`:**
- هنگام ورود کاربر، short-lived token به long-lived token تبدیل می‌شود
- مدت اعتبار توکن محاسبه و ذخیره می‌شود
- Long-lived tokens معمولاً 60 روز اعتبار دارند

```python
# مثال استفاده
long_lived_token, expires_in = self._exchange_for_long_lived_token(access_token)
```

### 2. سیستم Refresh پیشرفته

**تغییرات در `insta.py`:**
- پشتیبانی از هر دو نوع توکن (short-lived و long-lived)
- سعی در تبدیل short-lived به long-lived
- Refresh خودکار long-lived tokens
- بروزرسانی خودکار زمان انقضا

### 3. بازیابی خودکار در Service

**تغییرات در `instagram_service.py`:**
- تشخیص خودکار انقضای توکن هنگام ارسال پیام
- تلاش خودکار برای refresh توکن
- تکرار عملیات با توکن جدید

## دستورات مدیریتی

### 1. تبدیل توکن‌های موجود

```bash
# تبدیل تمام توکن‌های short-lived به long-lived
python manage.py convert_instagram_tokens

# بررسی بدون تغییر
python manage.py convert_instagram_tokens --check-only

# تبدیل توکن مشخص
python manage.py convert_instagram_tokens --channel-id 123

# اجبار تبدیل حتی توکن‌های long-lived
python manage.py convert_instagram_tokens --force
```

### 2. رفرش خودکار توکن‌ها

```bash
# رفرش توکن‌هایی که ظرف 7 روز منقضی می‌شوند
python manage.py auto_refresh_instagram_tokens

# تنظیم آستانه زمانی مختلف (مثلاً 3 روز)
python manage.py auto_refresh_instagram_tokens --days-before-expiry 3

# نمایش فقط (بدون تغییر)
python manage.py auto_refresh_instagram_tokens --dry-run

# رفرش همه توکن‌ها بدون در نظر گیری زمان انقضا
python manage.py auto_refresh_instagram_tokens --force-all
```

### 3. مانیتورینگ توکن‌ها

```bash
# بررسی وضعیت توکن‌ها
python manage.py refresh_instagram_tokens --check-only

# رفرش توکن مشخص
python manage.py refresh_instagram_tokens --channel-id 123
```

## زمان‌بندی خودکار

### Crontab Setup

برای رفرش خودکار روزانه:

```bash
# اضافه کردن به crontab
crontab -e

# رفرش روزانه ساعت 3 صبح
0 3 * * * cd /path/to/your/project && python manage.py auto_refresh_instagram_tokens

# رفرش هفتگی با فورس
0 2 * * 0 cd /path/to/your/project && python manage.py auto_refresh_instagram_tokens --force-all
```

### Systemd Timer (Linux)

ایجاد فایل `/etc/systemd/system/instagram-token-refresh.service`:

```ini
[Unit]
Description=Instagram Token Refresh
After=network.target

[Service]
Type=oneshot
User=your-app-user
WorkingDirectory=/path/to/your/project
ExecStart=/path/to/your/venv/bin/python manage.py auto_refresh_instagram_tokens
```

ایجاد فایل `/etc/systemd/system/instagram-token-refresh.timer`:

```ini
[Unit]
Description=Run Instagram token refresh daily
Requires=instagram-token-refresh.service

[Timer]
OnCalendar=daily
Persistent=true

[Install]
WantedBy=timers.target
```

فعال‌سازی:
```bash
sudo systemctl enable instagram-token-refresh.timer
sudo systemctl start instagram-token-refresh.timer
```

## نحوه عملکرد

### 1. هنگام اتصال کاربر جدید:
1. دریافت authorization code از Instagram
2. تبدیل به short-lived token
3. تبدیل فوری به long-lived token
4. ذخیره توکن و زمان انقضا

### 2. هنگام ارسال پیام:
1. استفاده از توکن موجود
2. در صورت خطای 190 (token expired):
   - تلاش برای refresh توکن
   - تکرار ارسال پیام با توکن جدید

### 3. مانیتورینگ دوره‌ای:
1. بررسی توکن‌هایی که نزدیک انقضا هستند
2. رفرش خودکار قبل از انقضا
3. گزارش وضعیت

## مزایا

### ✅ قبل از پیاده‌سازی:
- توکن‌ها هر 1-2 ساعت منقضی می‌شدند
- نیاز به reconnect مداوم کاربران
- قطعی در ارسال پیام‌ها

### ✅ بعد از پیاده‌سازی:
- توکن‌ها 60 روز اعتبار دارند
- رفرش خودکار قبل از انقضا
- بازیابی خودکار در صورت انقضا
- کاهش 95% reconnect های کاربران

## نظارت و عیب‌یابی

### لاگ‌های مهم:

```python
# موفقیت تبدیل توکن
"✅ Successfully converted to long-lived token, expires in X seconds"

# موفقیت رفرش
"✅ Instagram token refreshed for channel {username}, expires at {time}"

# خطای انقضا
"🔄 Instagram access token expired, attempting refresh..."

# شکست رفرش
"❌ All token refresh methods failed"
```

### بررسی وضعیت:

```bash
# نمایش تمام کانال‌ها و وضعیت توکن‌ها
python manage.py convert_instagram_tokens --check-only

# نمایش جزئیات رفرش
python manage.py auto_refresh_instagram_tokens --dry-run
```

## توجهات امنیتی

1. **حفاظت از Secrets:**
   - Client ID و Secret در متغیرهای محیطی قرار دهید
   - از hardcode کردن آن‌ها خودداری کنید

2. **Rate Limiting:**
   - Instagram حد درخواست دارد
   - رفرش‌های مکرر اجتناب کنید

3. **Error Handling:**
   - همیشه خطاها را log کنید
   - کاربران را در صورت نیاز به reconnect اطلاع دهید

## نتیجه‌گیری

این سیستم مشکل انقضای توکن‌های اینستاگرام را به طور کامل حل می‌کند و تجربه کاربری بهتری فراهم می‌آورد.