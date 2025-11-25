from django.contrib import admin
from .models import ProxySetting



@admin.register(ProxySetting)
class ProxySettingAdmin(admin.ModelAdmin):
    list_display = ('name', 'http_proxy', 'https_proxy', 'is_active', 'updated_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'http_proxy', 'https_proxy')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('🔧 اطلاعات پروکسی اصلی', {
            'fields': ('name', 'http_proxy', 'https_proxy', 'is_active')
        }),
        ('🔄 پروکسی پشتیبان (اختیاری)', {
            'fields': ('fallback_http_proxy', 'fallback_https_proxy'),
            'classes': ('collapse',)
        }),
        ('📅 تاریخچه', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['activate_proxy', 'deactivate_proxy']
    
    def activate_proxy(self, request, queryset):
        """فعال کردن پروکسی انتخاب شده"""
        if queryset.count() > 1:
            self.message_user(
                request, 
                "⚠️ فقط می‌تونید یک پروکسی رو فعال کنید", 
                level='warning'
            )
            return
        
        # فعال کردن پروکسی انتخاب شده
        proxy = queryset.first()
        proxy.is_active = True
        proxy.save()  # save method خودش بقیه رو غیرفعال می‌کنه
        
        self.message_user(request, f"✅ پروکسی '{proxy.name}' فعال شد")
    activate_proxy.short_description = "✅ فعال کردن پروکسی"
    
    def deactivate_proxy(self, request, queryset):
        """غیرفعال کردن پروکسی‌های انتخاب شده"""
        count = queryset.update(is_active=False)
        self.message_user(
            request, 
            f"❌ {count} پروکسی غیرفعال شد (درخواست‌ها بدون پروکسی ارسال می‌شن)"
        )
    deactivate_proxy.short_description = "❌ غیرفعال کردن پروکسی"

