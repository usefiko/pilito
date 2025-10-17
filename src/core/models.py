from django.db import models


class ProxySetting(models.Model):
    """
    مدل برای مدیریت تنظیمات پروکسی برای اتصال به APIهای فیلتر شده (Instagram و Telegram)
    """
    name = models.CharField(
        max_length=50, 
        unique=True, 
        help_text="نام پروکسی (مثلاً: Main Proxy)"
    )
    http_proxy = models.CharField(
        max_length=255, 
        help_text="آدرس پروکسی HTTP به فرمت: http://user:pass@ip:port"
    )
    https_proxy = models.CharField(
        max_length=255, 
        help_text="آدرس پروکسی HTTPS به فرمت: http://user:pass@ip:port"
    )
    fallback_http_proxy = models.CharField(
        max_length=255, 
        blank=True, 
        null=True, 
        help_text="پروکسی پشتیبان HTTP (اختیاری)"
    )
    fallback_https_proxy = models.CharField(
        max_length=255, 
        blank=True, 
        null=True, 
        help_text="پروکسی پشتیبان HTTPS (اختیاری)"
    )
    is_active = models.BooleanField(
        default=True, 
        help_text="فقط یک پروکسی باید فعال باشد"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "تنظیمات پروکسی"
        verbose_name_plural = "تنظیمات پروکسی‌ها"
        ordering = ['-is_active', '-updated_at']

    def __str__(self):
        status = "✅ فعال" if self.is_active else "❌ غیرفعال"
        return f"{self.name} ({status})"

    def save(self, *args, **kwargs):
        """
        اگر این پروکسی فعال شود، بقیه پروکسی‌ها رو غیرفعال می‌کنه
        """
        if self.is_active:
            ProxySetting.objects.filter(is_active=True).exclude(pk=self.pk).update(is_active=False)
        super().save(*args, **kwargs)

