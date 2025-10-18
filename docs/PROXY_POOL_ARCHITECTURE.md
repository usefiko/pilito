# 🏗️ معماری Proxy Pool با Auto-Failover و Cost Optimization

## 📋 فهرست

1. [نمای کلی](#نمای-کلی)
2. [استراتژی Cost-First](#استراتژی-cost-first)
3. [معماری سیستم](#معماری-سیستم)
4. [مدل‌های دیتابیس](#مدلهای-دیتابیس)
5. [لایه سرویس](#لایه-سرویس)
6. [Health Check و Monitoring](#health-check-و-monitoring)
7. [Alert System](#alert-system)
8. [راهنمای پیاده‌سازی](#راهنمای-پیادهسازی)
9. [تنظیمات پروکسی](#تنظیمات-پروکسی)
10. [API Endpoints](#api-endpoints)

---

## نمای کلی

سیستم Proxy Pool یک لایه مدیریت هوشمند پروکسی است که:

- ✅ **همیشه ارزان‌ترین پروکسی رو اول امتحان می‌کنه**
- ✅ در صورت fail شدن، خودکار به پروکسی بعدی switch می‌کنه
- ✅ Health check مداوم و real-time monitoring
- ✅ Alert فوری به ادمین در صورت مشکل
- ✅ آماری کامل از performance و uptime هر پروکسی
- ✅ بدون نیاز به تغییر کد موجود (backward compatible)

---

## استراتژی Cost-First

### اولویت‌بندی بر اساس هزینه:

```
Priority 1 (کم‌ترین هزینه) → VPS خارجی ($5/ماه)
    ↓ fail
Priority 2 → Datacenter IP #1 ($5/ماه)
    ↓ fail
Priority 3 → Datacenter IP #2 ($5/ماه)
    ↓ fail
Priority 4 → Datacenter IP #3 ($5/ماه)
    ↓ fail
Priority 5 (بیشترین هزینه) → Residential IP (~$10/GB)
```

### محاسبه Cost:

```python
# هر پروکسی یک فیلد cost_per_gb دارد
# سیستم بر اساس کمترین cost مرتب می‌کنه

VPS: cost_per_gb = 0 (نامحدود) → Priority = 10
Datacenter: cost_per_gb = 0 (نامحدود) → Priority = 20-40
Residential: cost_per_gb = 10 ($/GB) → Priority = 100
```

### نکته مهم:

اگه یک پروکسی 3 بار پشت سر هم fail کنه، status اش میشه `down` و دیگه استفاده نمیشه تا health check بعدی اونو `healthy` کنه.

---

## معماری سیستم

```
┌──────────────────────────────────────────────────────────┐
│                    Django Application                     │
│                                                           │
│  ┌────────────────────────────────────────────────────┐  │
│  │            ProxyPoolManager Service                │  │
│  │                                                    │  │
│  │  • get_active_proxy() ← استفاده در کد موجود      │  │
│  │  • health_check_all() ← Celery Task (هر 1 دقیقه) │  │
│  │  • make_request_with_failover()                   │  │
│  │  • _send_alert() ← ارسال notification به ادمین   │  │
│  └────────────────────────────────────────────────────┘  │
│                           ↓                               │
│  ┌────────────────────────────────────────────────────┐  │
│  │              ProxyServer Model (Database)          │  │
│  │                                                    │  │
│  │  Fields:                                           │  │
│  │  - name: نام پروکسی                               │  │
│  │  - proxy_type: vps | datacenter | residential     │  │
│  │  - http_proxy, https_proxy                        │  │
│  │  - cost_per_gb: هزینه به ازای هر GB (0=نامحدود)  │  │
│  │  - priority: اولویت استفاده (auto-calculated)    │  │
│  │  - status: healthy | degraded | down | blocked    │  │
│  │  - last_check, last_success                       │  │
│  │  - failure_count, response_time_ms                │  │
│  │  - total_requests, failed_requests                │  │
│  └────────────────────────────────────────────────────┘  │
│                           ↓                               │
│  ┌────────────────────────────────────────────────────┐  │
│  │              Celery Beat (Scheduler)               │  │
│  │                                                    │  │
│  │  check_proxy_health: هر 1 دقیقه                   │  │
│  │  - بررسی سلامت همه پروکسی‌ها                     │  │
│  │  - update کردن status                             │  │
│  │  - ارسال alert در صورت down شدن                  │  │
│  └────────────────────────────────────────────────────┘  │
│                           ↓                               │
│  ┌────────────────────────────────────────────────────┐  │
│  │            Alert System (Telegram Bot)             │  │
│  │                                                    │  │
│  │  Alerts:                                           │  │
│  │  - 🚨 پروکسی X down شد                            │  │
│  │  - ⚠️ پروکسی X کند شده (>2 sec)                  │  │
│  │  - ❌ همه پروکسی‌ها fail شدند!                   │  │
│  │  - 💰 هزینه residential از حد گذشت               │  │
│  └────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────┘
                           ↓
        ┌──────────────────────────────────────┐
        │     External APIs (Telegram/Insta)    │
        └──────────────────────────────────────┘
```

---

## مدل‌های دیتابیس

### 1. مدل `ProxyServer`

```python
# فایل: core/models.py

class ProxyServer(models.Model):
    """
    مدل اصلی برای مدیریت پروکسی‌ها
    """
    
    # انواع پروکسی
    TYPE_CHOICES = [
        ('vps', 'VPS خارجی (ارزان‌ترین)'),
        ('datacenter', 'Datacenter IP'),
        ('residential', 'Residential IP (گران‌ترین)'),
    ]
    
    # وضعیت‌های ممکن
    STATUS_CHOICES = [
        ('healthy', '✅ سالم'),
        ('degraded', '⚠️ کند (>2 sec)'),
        ('down', '❌ از کار افتاده'),
        ('blocked', '🚫 Block شده توسط API'),
    ]
    
    # ──────────────────────────────────────────
    # اطلاعات اصلی
    # ──────────────────────────────────────────
    name = models.CharField(max_length=100, unique=True)
    proxy_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    http_proxy = models.CharField(max_length=255)
    https_proxy = models.CharField(max_length=255)
    
    # ──────────────────────────────────────────
    # Cost & Priority
    # ──────────────────────────────────────────
    cost_per_gb = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=0,
        help_text="هزینه به ازای هر GB (0 = نامحدود)"
    )
    
    priority = models.IntegerField(
        default=100,
        help_text="کمتر = اولویت بالاتر (auto-calculated based on cost)"
    )
    
    # ──────────────────────────────────────────
    # Health & Status
    # ──────────────────────────────────────────
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='healthy'
    )
    
    last_check = models.DateTimeField(null=True, blank=True)
    last_success = models.DateTimeField(null=True, blank=True)
    
    failure_count = models.IntegerField(
        default=0,
        help_text="تعداد failهای متوالی (>= 3 = down)"
    )
    
    response_time_ms = models.IntegerField(
        null=True, 
        blank=True,
        help_text="میانگین زمان پاسخ (میلی‌ثانیه)"
    )
    
    # ──────────────────────────────────────────
    # Statistics
    # ──────────────────────────────────────────
    total_requests = models.IntegerField(default=0)
    failed_requests = models.IntegerField(default=0)
    
    # برای residential: تخمین traffic مصرف شده
    estimated_traffic_mb = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text="تخمین traffic مصرف شده (MB)"
    )
    
    # ──────────────────────────────────────────
    # Settings
    # ──────────────────────────────────────────
    is_active = models.BooleanField(
        default=True,
        help_text="فعال/غیرفعال کردن دستی"
    )
    
    max_failures_before_down = models.IntegerField(
        default=3,
        help_text="تعداد fail های مجاز قبل از down شدن"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # ──────────────────────────────────────────
    # Meta
    # ──────────────────────────────────────────
    class Meta:
        ordering = ['priority', 'cost_per_gb', 'name']
        verbose_name = "پروکسی سرور"
        verbose_name_plural = "پروکسی سرورها"
        indexes = [
            models.Index(fields=['status', 'priority']),
            models.Index(fields=['is_active', 'status']),
        ]
    
    def __str__(self):
        cost_str = f"${self.cost_per_gb}/GB" if self.cost_per_gb > 0 else "نامحدود"
        return f"{self.name} ({self.get_status_display()}) - {cost_str}"
    
    # ──────────────────────────────────────────
    # Properties
    # ──────────────────────────────────────────
    @property
    def uptime_percentage(self):
        """محاسبه uptime به درصد"""
        if self.total_requests == 0:
            return 100.0
        success = self.total_requests - self.failed_requests
        return (success / self.total_requests) * 100
    
    @property
    def estimated_cost_usd(self):
        """تخمین هزینه مصرف شده (USD)"""
        if self.cost_per_gb == 0:
            return 0
        traffic_gb = self.estimated_traffic_mb / 1024
        return float(self.cost_per_gb) * traffic_gb
    
    @property
    def is_healthy(self):
        """آیا پروکسی سالم است؟"""
        return self.status == 'healthy' and self.is_active
    
    # ──────────────────────────────────────────
    # Methods
    # ──────────────────────────────────────────
    def mark_failure(self, error_type='connection'):
        """ثبت یک failure"""
        self.failure_count += 1
        self.failed_requests += 1
        
        # بررسی threshold
        if self.failure_count >= self.max_failures_before_down:
            self.status = 'down'
        
        self.save()
    
    def mark_success(self, response_time_ms=None):
        """ثبت یک success"""
        self.failure_count = 0  # Reset
        self.status = 'healthy'
        self.last_success = timezone.now()
        self.total_requests += 1
        
        if response_time_ms:
            self.response_time_ms = response_time_ms
            
            # اگر خیلی کند شد
            if response_time_ms > 2000:
                self.status = 'degraded'
        
        self.save()
    
    def mark_blocked(self):
        """ثبت block شدن توسط API"""
        self.status = 'blocked'
        self.save()
    
    def save(self, *args, **kwargs):
        """Auto-calculate priority based on cost"""
        # Priority = cost_per_gb * 10
        # VPS (0) → 0
        # Datacenter (0) → 10-40 (manual)
        # Residential (10) → 100
        
        if self.cost_per_gb == 0 and self.proxy_type == 'vps':
            self.priority = 10
        elif self.cost_per_gb == 0 and self.proxy_type == 'datacenter':
            # Keep manual priority (20-40 range)
            if not self.priority or self.priority < 20 or self.priority > 40:
                self.priority = 20
        else:
            self.priority = int(self.cost_per_gb * 10)
        
        super().save(*args, **kwargs)
```

### 2. مدل `ProxyUsageLog` (اختیاری - برای audit)

```python
class ProxyUsageLog(models.Model):
    """
    لاگ استفاده از پروکسی‌ها (برای analytics و billing)
    """
    proxy = models.ForeignKey(ProxyServer, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    api_endpoint = models.CharField(max_length=255)
    success = models.BooleanField()
    response_time_ms = models.IntegerField(null=True)
    estimated_size_kb = models.IntegerField(default=5)
    
    error_message = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['proxy', '-timestamp']),
        ]
```

---

## لایه سرویس

### فایل: `core/services/proxy_manager.py`

```python
"""
ProxyPoolManager Service
------------------------
مدیریت pool پروکسی‌ها با استراتژی Cost-First
"""

import requests
import logging
import time
from typing import Dict, Optional, Tuple, List
from django.utils import timezone
from django.core.cache import cache
from core.models import ProxyServer

logger = logging.getLogger(__name__)


class ProxyPoolManager:
    """
    مدیریت هوشمند پروکسی‌ها
    
    استراتژی:
    1. همیشه ارزان‌ترین پروکسی سالم رو امتحان کن
    2. اگه fail شد، به بعدی برو
    3. health check مداوم
    4. alert به ادمین
    """
    
    # URLs for health check
    TEST_URLS = [
        'https://api.telegram.org/botTEST/getMe',
        'https://www.google.com',
    ]
    
    CACHE_KEY_PREFIX = 'proxy_pool'
    CACHE_TIMEOUT = 60  # 1 minute
    
    # ──────────────────────────────────────────
    # Public Methods
    # ──────────────────────────────────────────
    
    @classmethod
    def get_active_proxy(cls) -> Dict[str, str]:
        """
        برگرداندن پروکسی فعال (ارزان‌ترین سالم)
        
        Returns:
            dict: {"http": "...", "https": "..."}
            dict: {} اگه هیچ پروکسی سالمی نبود
        
        Example:
            proxies = ProxyPoolManager.get_active_proxy()
            response = requests.get(url, proxies=proxies)
        """
        # بررسی cache
        cache_key = f"{cls.CACHE_KEY_PREFIX}:active"
        cached = cache.get(cache_key)
        if cached:
            return cached
        
        # پیدا کردن ارزان‌ترین پروکسی سالم
        proxy = cls._find_best_proxy()
        
        if not proxy:
            logger.error("❌ هیچ پروکسی سالمی موجود نیست!")
            cls._send_critical_alert("🚨 CRITICAL: همه پروکسی‌ها down هستند!")
            return {}
        
        # ساخت config
        config = cls._build_proxy_config(proxy)
        
        # Cache کردن
        cache.set(cache_key, config, cls.CACHE_TIMEOUT)
        
        logger.info(
            f"🔒 Using proxy: {proxy.name} "
            f"(${proxy.cost_per_gb}/GB, Priority: {proxy.priority})"
        )
        
        return config
    
    @classmethod
    def make_request_with_failover(
        cls,
        method: str,
        url: str,
        max_retries: int = None,
        **kwargs
    ) -> requests.Response:
        """
        درخواست با failover خودکار
        
        در صورت fail، به پروکسی بعدی switch می‌کنه
        
        Args:
            method: 'GET', 'POST', etc.
            url: آدرس API
            max_retries: حداکثر تعداد retry (None = همه پروکسی‌ها)
            **kwargs: سایر پارامترهای requests
        
        Returns:
            Response object
        
        Raises:
            Exception: اگه همه پروکسی‌ها fail کردن
        
        Example:
            response = ProxyPoolManager.make_request_with_failover(
                'POST',
                'https://api.telegram.org/botXXX/sendMessage',
                json={'chat_id': 123, 'text': 'hello'}
            )
        """
        proxies = cls._get_proxy_list()
        
        if max_retries:
            proxies = proxies[:max_retries]
        
        last_error = None
        
        for proxy in proxies:
            try:
                config = cls._build_proxy_config(proxy)
                kwargs['proxies'] = config
                kwargs.setdefault('timeout', 10)
                
                logger.info(f"🔄 Trying: {proxy.name} (${proxy.cost_per_gb}/GB)")
                
                start_time = time.time()
                response = requests.request(method, url, **kwargs)
                response_time = int((time.time() - start_time) * 1000)
                
                # Success!
                proxy.mark_success(response_time)
                cls._invalidate_cache()
                
                # تخمین traffic (برای residential)
                if proxy.cost_per_gb > 0:
                    cls._estimate_traffic(proxy, response)
                
                logger.info(
                    f"✅ Success with {proxy.name} ({response_time}ms)"
                )
                
                return response
                
            except requests.exceptions.ProxyError as e:
                logger.warning(f"⚠️ {proxy.name} proxy error: {e}")
                proxy.mark_failure('proxy_error')
                last_error = e
                
            except requests.exceptions.Timeout as e:
                logger.warning(f"⏱️ {proxy.name} timeout: {e}")
                proxy.mark_failure('timeout')
                last_error = e
                
            except requests.exceptions.ConnectionError as e:
                logger.warning(f"🔌 {proxy.name} connection error: {e}")
                proxy.mark_failure('connection_error')
                last_error = e
                
            except Exception as e:
                logger.error(f"❌ {proxy.name} unexpected error: {e}")
                proxy.mark_failure('unknown')
                last_error = e
        
        # همه fail شدند
        cls._send_critical_alert(
            f"🚨 همه پروکسی‌ها fail شدند!\n"
            f"URL: {url}\n"
            f"Error: {last_error}"
        )
        
        raise last_error or Exception("No working proxy found")
    
    @classmethod
    def health_check_all(cls):
        """
        بررسی سلامت همه پروکسی‌های فعال
        
        این method توسط Celery Beat هر 1 دقیقه صدا زده میشه
        """
        logger.info("🏥 Starting health check for all proxies...")
        
        proxies = ProxyServer.objects.filter(is_active=True)
        
        results = {
            'total': proxies.count(),
            'healthy': 0,
            'degraded': 0,
            'down': 0,
            'blocked': 0,
        }
        
        for proxy in proxies:
            old_status = proxy.status
            
            is_healthy, response_time = cls._check_proxy_health(proxy)
            
            proxy.last_check = timezone.now()
            proxy.response_time_ms = response_time
            
            if is_healthy:
                proxy.mark_success(response_time)
                logger.info(
                    f"✅ {proxy.name}: OK ({response_time}ms)"
                )
            else:
                proxy.mark_failure('health_check')
                logger.warning(f"❌ {proxy.name}: FAILED")
            
            # ارسال alert اگه status تغییر کرد
            if old_status != proxy.status:
                cls._send_status_change_alert(proxy, old_status, proxy.status)
            
            # آمار
            results[proxy.status] += 1
        
        # پاک کردن cache
        cls._invalidate_cache()
        
        logger.info(
            f"🏥 Health check completed: "
            f"{results['healthy']} healthy, "
            f"{results['degraded']} degraded, "
            f"{results['down']} down, "
            f"{results['blocked']} blocked"
        )
        
        return results
    
    # ──────────────────────────────────────────
    # Private Methods
    # ──────────────────────────────────────────
    
    @classmethod
    def _find_best_proxy(cls) -> Optional[ProxyServer]:
        """
        پیدا کردن بهترین پروکسی (ارزان‌ترین سالم)
        """
        return ProxyServer.objects.filter(
            is_active=True,
            status__in=['healthy', 'degraded']
        ).order_by('priority', 'cost_per_gb', 'failure_count').first()
    
    @classmethod
    def _get_proxy_list(cls) -> List[ProxyServer]:
        """
        لیست پروکسی‌های سالم به ترتیب priority
        """
        return list(
            ProxyServer.objects.filter(
                is_active=True,
                status__in=['healthy', 'degraded']
            ).order_by('priority', 'cost_per_gb')
        )
    
    @classmethod
    def _build_proxy_config(cls, proxy: ProxyServer) -> Dict[str, str]:
        """
        ساخت dictionary config برای requests
        """
        # Fix uppercase issue
        http_proxy = proxy.http_proxy
        https_proxy = proxy.https_proxy
        
        if http_proxy.startswith(('HTTP://', 'HTTPS://')):
            http_proxy = http_proxy.lower()
        
        if https_proxy.startswith(('HTTP://', 'HTTPS://')):
            https_proxy = https_proxy.lower()
        
        return {
            'http': http_proxy,
            'https': https_proxy,
        }
    
    @classmethod
    def _check_proxy_health(cls, proxy: ProxyServer) -> Tuple[bool, Optional[int]]:
        """
        بررسی سلامت یک پروکسی
        
        Returns:
            (is_healthy, response_time_ms)
        """
        config = cls._build_proxy_config(proxy)
        
        for test_url in cls.TEST_URLS:
            try:
                start = time.time()
                response = requests.get(
                    test_url,
                    proxies=config,
                    timeout=10
                )
                response_time = int((time.time() - start) * 1000)
                
                # اگه response بگیریم = کار می‌کنه
                if response.status_code in [200, 401, 404]:
                    return True, response_time
                    
            except Exception as e:
                logger.debug(
                    f"Health check failed for {proxy.name} "
                    f"on {test_url}: {e}"
                )
                continue
        
        return False, None
    
    @classmethod
    def _estimate_traffic(cls, proxy: ProxyServer, response: requests.Response):
        """
        تخمین traffic مصرف شده (برای residential proxies)
        """
        if proxy.cost_per_gb == 0:
            return  # نامحدود
        
        # تخمین rough: headers + body
        size_bytes = len(response.content) + 1024  # +1KB for headers
        size_mb = size_bytes / (1024 * 1024)
        
        proxy.estimated_traffic_mb += Decimal(size_mb)
        proxy.save(update_fields=['estimated_traffic_mb'])
        
        # اگه از threshold عبور کرد
        threshold_gb = 5  # 5GB warning
        if proxy.estimated_traffic_mb / 1024 > threshold_gb:
            cls._send_cost_alert(proxy)
    
    @classmethod
    def _invalidate_cache(cls):
        """پاک کردن cache"""
        cache.delete(f"{cls.CACHE_KEY_PREFIX}:active")
    
    @classmethod
    def _send_status_change_alert(cls, proxy, old_status, new_status):
        """ارسال alert برای تغییر status"""
        emoji_map = {
            'healthy': '✅',
            'degraded': '⚠️',
            'down': '❌',
            'blocked': '🚫',
        }
        
        message = (
            f"{emoji_map.get(new_status, '❓')} پروکسی {proxy.name}\n"
            f"Status changed: {old_status} → {new_status}\n"
            f"Type: {proxy.get_proxy_type_display()}\n"
            f"Cost: ${proxy.cost_per_gb}/GB\n"
            f"Uptime: {proxy.uptime_percentage:.1f}%"
        )
        
        from core.tasks import send_admin_alert
        send_admin_alert.delay(message)
    
    @classmethod
    def _send_critical_alert(cls, message: str):
        """ارسال alert بحرانی"""
        from core.tasks import send_admin_alert
        send_admin_alert.delay(f"🚨 CRITICAL:\n{message}", priority='high')
    
    @classmethod
    def _send_cost_alert(cls, proxy: ProxyServer):
        """ارسال alert برای هزینه بالا"""
        message = (
            f"💰 هزینه پروکسی {proxy.name} بالا رفته!\n"
            f"Traffic: {proxy.estimated_traffic_mb / 1024:.2f} GB\n"
            f"Cost: ${proxy.estimated_cost_usd:.2f}\n"
            f"لطفاً بررسی کنید."
        )
        
        from core.tasks import send_admin_alert
        send_admin_alert.delay(message)
```

---

## Health Check و Monitoring

### Celery Task: `core/tasks.py`

```python
from celery import shared_task
from core.services.proxy_manager import ProxyPoolManager
import requests
import logging

logger = logging.getLogger(__name__)


@shared_task
def check_proxy_health():
    """
    بررسی سلامت همه پروکسی‌ها
    
    این task هر 1 دقیقه توسط Celery Beat اجرا میشه
    """
    try:
        results = ProxyPoolManager.health_check_all()
        logger.info(f"Health check completed: {results}")
        return results
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise


@shared_task
def send_admin_alert(message: str, priority: str = 'normal'):
    """
    ارسال alert به تلگرام ادمین
    
    Args:
        message: متن پیام
        priority: 'high' | 'normal' | 'low'
    """
    from django.conf import settings
    
    # تنظیمات bot ادمین
    BOT_TOKEN = settings.ADMIN_TELEGRAM_BOT_TOKEN
    CHAT_ID = settings.ADMIN_TELEGRAM_CHAT_ID
    
    if not BOT_TOKEN or not CHAT_ID:
        logger.warning("Admin bot not configured")
        return
    
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    
    # emoji بر اساس priority
    emoji = {
        'high': '🚨',
        'normal': '📢',
        'low': 'ℹ️',
    }.get(priority, '📢')
    
    data = {
        'chat_id': CHAT_ID,
        'text': f"{emoji} {message}",
        'parse_mode': 'HTML',
        'disable_notification': priority == 'low',
    }
    
    try:
        # ارسال بدون پروکسی (مطمئن شو برسه!)
        response = requests.post(url, json=data, timeout=10)
        
        if response.status_code == 200:
            logger.info(f"Admin alert sent: {message[:50]}")
        else:
            logger.error(f"Failed to send alert: {response.text}")
            
    except Exception as e:
        logger.error(f"Error sending admin alert: {e}")
        # می‌تونی به Sentry بفرستی
        import sentry_sdk
        sentry_sdk.capture_exception(e)
```

### Celery Beat Configuration: `settings/common.py`

```python
from celery.schedules import crontab

CELERY_BEAT_SCHEDULE = {
    # ... سایر taskها ...
    
    # ─────────────────────────────────────────
    # Proxy Pool Health Check
    # ─────────────────────────────────────────
    'check-proxy-health': {
        'task': 'core.tasks.check_proxy_health',
        'schedule': crontab(minute='*/1'),  # هر 1 دقیقه
        'options': {
            'queue': 'default',
            'expires': 50,  # expire بعد از 50 ثانیه
        }
    },
    
    # ─────────────────────────────────────────
    # Cost Report (اختیاری - هر روز)
    # ─────────────────────────────────────────
    'daily-proxy-cost-report': {
        'task': 'core.tasks.send_daily_cost_report',
        'schedule': crontab(hour=9, minute=0),  # هر روز 9 صبح
        'options': {
            'queue': 'default',
        }
    },
}
```

---

## Alert System

### انواع Alert ها:

#### 1. Status Change Alert
```
⚠️ پروکسی Datacenter-1
Status changed: healthy → degraded
Type: Datacenter IP
Cost: $0/GB
Uptime: 98.5%
```

#### 2. Down Alert
```
❌ پروکسی VPS-Main
Status changed: healthy → down
Type: VPS خارجی
Cost: $0/GB
Uptime: 95.2%

⚡ Auto-switched to: Datacenter-1
```

#### 3. Critical Alert
```
🚨 CRITICAL:
همه پروکسی‌ها down هستند!

لطفاً فوراً بررسی کنید.
```

#### 4. Cost Alert
```
💰 هزینه پروکسی Residential-1 بالا رفته!
Traffic: 5.2 GB
Cost: $52.00
لطفاً بررسی کنید.
```

#### 5. Daily Report (اختیاری)
```
📊 گزارش روزانه پروکسی‌ها

✅ Healthy: 4
⚠️ Degraded: 1
❌ Down: 0

💰 هزینه امروز: $2.50
📊 Total Traffic: 250 MB

Top Performer: VPS-Main (100% uptime)
```

---

## راهنمای پیاده‌سازی

### مرحله 1: Migration

```bash
# ساخت migration برای model جدید
python manage.py makemigrations core

# اجرا
python manage.py migrate
```

### مرحله 2: Admin Panel

```python
# core/admin.py

from django.contrib import admin
from django.utils.html import format_html
from .models import ProxyServer

@admin.register(ProxyServer)
class ProxyServerAdmin(admin.ModelAdmin):
    list_display = [
        'name',
        'proxy_type_badge',
        'status_badge',
        'priority',
        'cost_badge',
        'uptime_badge',
        'response_time_badge',
        'last_check',
    ]
    
    list_filter = ['proxy_type', 'status', 'is_active']
    search_fields = ['name', 'http_proxy']
    
    readonly_fields = [
        'failure_count',
        'last_check',
        'last_success',
        'total_requests',
        'failed_requests',
        'estimated_traffic_mb',
        'uptime_percentage',
        'estimated_cost_usd',
    ]
    
    fieldsets = [
        ('اطلاعات اصلی', {
            'fields': ['name', 'proxy_type', 'http_proxy', 'https_proxy']
        }),
        ('Cost & Priority', {
            'fields': ['cost_per_gb', 'priority']
        }),
        ('Health & Status', {
            'fields': [
                'status',
                'is_active',
                'max_failures_before_down',
                'failure_count',
                'response_time_ms',
                'last_check',
                'last_success',
            ]
        }),
        ('Statistics', {
            'fields': [
                'total_requests',
                'failed_requests',
                'uptime_percentage',
                'estimated_traffic_mb',
                'estimated_cost_usd',
            ],
            'classes': ['collapse'],
        }),
    ]
    
    def proxy_type_badge(self, obj):
        colors = {
            'vps': '#28a745',
            'datacenter': '#007bff',
            'residential': '#ffc107',
        }
        return format_html(
            '<span style="background:{}; color:white; padding:3px 10px; '
            'border-radius:3px;">{}</span>',
            colors.get(obj.proxy_type, '#6c757d'),
            obj.get_proxy_type_display()
        )
    proxy_type_badge.short_description = 'نوع'
    
    def status_badge(self, obj):
        colors = {
            'healthy': '#28a745',
            'degraded': '#ffc107',
            'down': '#dc3545',
            'blocked': '#6c757d',
        }
        return format_html(
            '<span style="background:{}; color:white; padding:3px 10px; '
            'border-radius:3px;">{}</span>',
            colors.get(obj.status, '#6c757d'),
            obj.get_status_display()
        )
    status_badge.short_description = 'وضعیت'
    
    def cost_badge(self, obj):
        if obj.cost_per_gb == 0:
            return format_html(
                '<span style="color:#28a745;font-weight:bold;">نامحدود</span>'
            )
        return format_html(
            '<span style="color:#ffc107;font-weight:bold;">${}/GB</span>',
            obj.cost_per_gb
        )
    cost_badge.short_description = 'هزینه'
    
    def uptime_badge(self, obj):
        uptime = obj.uptime_percentage
        color = '#28a745' if uptime >= 95 else '#ffc107' if uptime >= 80 else '#dc3545'
        return format_html(
            '<span style="color:{};font-weight:bold;">{:.1f}%</span>',
            color, uptime
        )
    uptime_badge.short_description = 'Uptime'
    
    def response_time_badge(self, obj):
        if not obj.response_time_ms:
            return '-'
        
        rt = obj.response_time_ms
        color = '#28a745' if rt < 500 else '#ffc107' if rt < 2000 else '#dc3545'
        return format_html(
            '<span style="color:{};font-weight:bold;">{} ms</span>',
            color, rt
        )
    response_time_badge.short_description = 'Response Time'
    
    actions = ['mark_as_healthy', 'mark_as_down', 'reset_stats']
    
    def mark_as_healthy(self, request, queryset):
        for proxy in queryset:
            proxy.status = 'healthy'
            proxy.failure_count = 0
            proxy.save()
        self.message_user(request, f"{queryset.count()} پروکسی healthy شد")
    mark_as_healthy.short_description = "Mark as Healthy"
    
    def mark_as_down(self, request, queryset):
        queryset.update(status='down')
        self.message_user(request, f"{queryset.count()} پروکسی down شد")
    mark_as_down.short_description = "Mark as Down"
    
    def reset_stats(self, request, queryset):
        queryset.update(
            total_requests=0,
            failed_requests=0,
            estimated_traffic_mb=0,
        )
        self.message_user(request, f"آمار {queryset.count()} پروکسی reset شد")
    reset_stats.short_description = "Reset Statistics"
```

### مرحله 3: تغییر کد موجود

```python
# هیچ تغییری لازم نیست!
# فقط مطمئن شو که get_active_proxy() رو از core.utils import می‌کنی

# مثال - کد قبلی:
from core.utils import get_active_proxy

response = requests.get(url, proxies=get_active_proxy())

# همین! هیچ تغییری لازم نیست ✅
```

### مرحله 4: تست

```python
# تست manual در Django shell

python manage.py shell

>>> from core.services.proxy_manager import ProxyPoolManager

# تست get_active_proxy
>>> config = ProxyPoolManager.get_active_proxy()
>>> print(config)
{'http': 'http://...', 'https': 'http://...'}

# تست با درخواست واقعی
>>> response = ProxyPoolManager.make_request_with_failover(
...     'GET',
...     'https://api.telegram.org/botTEST/getMe'
... )
>>> print(response.status_code)
404  # انتظار داریم (توکن fake)

# تست health check
>>> results = ProxyPoolManager.health_check_all()
>>> print(results)
{'total': 5, 'healthy': 4, 'degraded': 1, 'down': 0, 'blocked': 0}
```

---

## تنظیمات پروکسی

### نمونه Configuration در Admin:

```python
# 1. VPS خارجی (Primary - ارزان‌ترین)
Name: VPS-Germany-Main
Type: VPS خارجی
HTTP Proxy: http://YOUR_VPS_IP:3128
HTTPS Proxy: http://YOUR_VPS_IP:3128
Cost per GB: 0 (نامحدود)
Priority: 10 (auto)
Max Failures: 3

# 2. Datacenter IP #1 (Backup)
Name: Datacenter-iProyal-1
Type: Datacenter IP
HTTP Proxy: http://user:pass@ip1:port
HTTPS Proxy: http://user:pass@ip1:port
Cost per GB: 0 (نامحدود)
Priority: 20 (manual)
Max Failures: 3

# 3. Datacenter IP #2 (Backup)
Name: Datacenter-iProyal-2
Type: Datacenter IP
HTTP Proxy: http://user:pass@ip2:port
HTTPS Proxy: http://user:pass@ip2:port
Cost per GB: 0 (نامحدود)
Priority: 30 (manual)
Max Failures: 3

# 4. Datacenter IP #3 (Backup)
Name: Datacenter-iProyal-3
Type: Datacenter IP
HTTP Proxy: http://user:pass@ip3:port
HTTPS Proxy: http://user:pass@ip3:port
Cost per GB: 0 (نامحدود)
Priority: 40 (manual)
Max Failures: 3

# 5. Residential IP (Last Resort - گران‌ترین)
Name: Residential-Smartproxy
Type: Residential IP
HTTP Proxy: http://user:pass@residential.com:port
HTTPS Proxy: http://user:pass@residential.com:port
Cost per GB: 12 ($/GB)
Priority: 120 (auto)
Max Failures: 2
```

### ترتیب استفاده:

```
Request → Check Cache → VPS (Priority 10)
               ↓ fail
          Datacenter-1 (Priority 20)
               ↓ fail
          Datacenter-2 (Priority 30)
               ↓ fail
          Datacenter-3 (Priority 40)
               ↓ fail
          Residential (Priority 120)
               ↓ fail
          ERROR + Alert!
```

---

## API Endpoints

### 1. Proxy Status API

```python
# core/api/proxy_status.py

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from core.models import ProxyServer
from django.utils import timezone
from datetime import timedelta

@api_view(['GET'])
@permission_classes([IsAdminUser])
def proxy_status_api(request):
    """
    GET /api/v1/proxy/status
    
    نمایش وضعیت تمام پروکسی‌ها
    """
    proxies = ProxyServer.objects.filter(is_active=True)
    
    # آمار کلی
    total = proxies.count()
    healthy = proxies.filter(status='healthy').count()
    degraded = proxies.filter(status='degraded').count()
    down = proxies.filter(status='down').count()
    blocked = proxies.filter(status='blocked').count()
    
    # محاسبه هزینه کل
    total_cost = sum(p.estimated_cost_usd for p in proxies)
    
    # جزئیات هر پروکسی
    proxy_details = []
    for p in proxies:
        proxy_details.append({
            'id': p.id,
            'name': p.name,
            'type': p.proxy_type,
            'status': p.status,
            'priority': p.priority,
            'cost_per_gb': float(p.cost_per_gb),
            'estimated_cost': round(p.estimated_cost_usd, 2),
            'uptime': round(p.uptime_percentage, 2),
            'response_time_ms': p.response_time_ms,
            'total_requests': p.total_requests,
            'failed_requests': p.failed_requests,
            'last_check': p.last_check.isoformat() if p.last_check else None,
            'last_success': p.last_success.isoformat() if p.last_success else None,
        })
    
    return Response({
        'summary': {
            'total': total,
            'healthy': healthy,
            'degraded': degraded,
            'down': down,
            'blocked': blocked,
            'total_cost_usd': round(total_cost, 2),
        },
        'proxies': proxy_details,
        'timestamp': timezone.now().isoformat(),
    })


@api_view(['POST'])
@permission_classes([IsAdminUser])
def manual_health_check_api(request):
    """
    POST /api/v1/proxy/health-check
    
    اجرای manual health check
    """
    from core.services.proxy_manager import ProxyPoolManager
    
    results = ProxyPoolManager.health_check_all()
    
    return Response({
        'message': 'Health check completed',
        'results': results,
    })
```

### 2. URLs

```python
# core/urls.py

from django.urls import path
from core.api import proxy_status_api, manual_health_check_api

urlpatterns = [
    # ...
    path('api/v1/proxy/status/', proxy_status_api),
    path('api/v1/proxy/health-check/', manual_health_check_api),
]
```

---

## Environment Variables

```bash
# .env

# ─────────────────────────────────────────
# Admin Telegram Bot (برای alerts)
# ─────────────────────────────────────────
ADMIN_TELEGRAM_BOT_TOKEN=your_admin_bot_token
ADMIN_TELEGRAM_CHAT_ID=your_admin_chat_id

# ─────────────────────────────────────────
# Proxy Pool Settings
# ─────────────────────────────────────────
PROXY_HEALTH_CHECK_INTERVAL=60  # seconds
PROXY_MAX_FAILURES=3
PROXY_CACHE_TIMEOUT=60  # seconds
```

---

## نکات مهم

### ✅ Backward Compatibility

کد قدیمی بدون هیچ تغییری کار می‌کنه:

```python
# قبل
from core.utils import get_active_proxy
response = requests.get(url, proxies=get_active_proxy())

# بعد - همون کد!
from core.utils import get_active_proxy
response = requests.get(url, proxies=get_active_proxy())
```

### ✅ Cost Optimization

سیستم **همیشه ارزان‌ترین** پروکسی سالم رو انتخاب می‌کنه:

1. VPS (رایگان) → اول
2. Datacenter (رایگان) → دوم
3. Residential (حجمی) → آخر

### ✅ Monitoring

- Health check خودکار هر 1 دقیقه
- Alert فوری در صورت down شدن
- Dashboard برای نمایش وضعیت
- آمار کامل performance

### ✅ Reliability

- Auto-failover در کسری از ثانیه
- حداقل 5 پروکسی موازی
- همیشه یک backup آماده

---

## خلاصه

### چرا این معماری؟

1. **Cost-Effective**: همیشه ارزان‌ترین رو استفاده می‌کنه
2. **Reliable**: Auto-failover فوری
3. **Scalable**: راحت پروکسی اضافه می‌کنی
4. **Monitored**: همیشه می‌دونی چه خبره
5. **Backward Compatible**: کد قدیمی کار می‌کنه

### هزینه تقریبی:

```
VPS خارجی: $5/ماه
3x Datacenter: $15/ماه (backup)
1x Residential: $30/ماه (emergency only)
───────────────────────────
Total: ~$50/ماه

با uptime 99.9%+ ✅
```

---

**تاریخ:** 2025-10-18  
**نسخه:** 1.0  
**وضعیت:** Ready for Implementation

