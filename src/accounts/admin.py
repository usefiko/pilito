from django.contrib import admin
from accounts.models import User, PasswordResetToken, EmailConfirmationToken, OTPToken
from import_export.admin import ImportExportModelAdmin

admin.site.site_header = "Fiko Admin Panel"
admin.site.site_title = "Fiko"
admin.site.index_title = "Fiko Dashboard"

class UserAdmin(ImportExportModelAdmin):
    # Complete field list including all new fields
    field_list = (
        'id', 'email', 'username', 'first_name', 'last_name', 'phone_number',
        'is_active', 'is_staff', 'is_superuser', 'email_confirmed',
        'age', 'gender', 'address', 'organisation', 'description', 
        'state', 'zip_code', 'country', 'language', 'time_zone', 'currency',
        'business_type', 'default_reply_handler', 'wizard_complete',
        'google_id', 'is_google_user', 'google_avatar_url',
        'profile_picture', 'last_login', 'date_joined', 'created_at', 'updated_at',
        'password', 'is_profile_fill'
    )

    list_display = (
        'img_tag', 'email', 'username', 'first_name', 'last_name', 
        'email_confirmed', 'is_google_user', 'wizard_complete', 
        'is_active', 'created_at'
    )
    
    list_filter = (
        'email_confirmed', 'is_google_user', 'wizard_complete', 'is_active', 
        'is_staff', 'gender', 'country', 'business_type', 'default_reply_handler',
        'created_at', 'updated_at'
    )
    
    search_fields = [
        'email', 'username', 'phone_number', 'first_name', 'last_name', 
        'google_id', 'organisation'
    ]
    
    readonly_fields = ('id', 'created_at', 'updated_at', 'date_joined', 'last_login', 'is_profile_fill', 'confirmation_codes')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('email', 'username', 'first_name', 'last_name', 'phone_number')
        }),
        ('Account Status', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'email_confirmed', 'wizard_complete')
        }),
        ('Google OAuth', {
            'fields': ('is_google_user', 'google_id', 'google_avatar_url'),
            'classes': ('collapse',)
        }),
        ('Personal Details', {
            'fields': ('age', 'gender', 'profile_picture', 'description'),
            'classes': ('collapse',)
        }),
        ('Location & Business', {
            'fields': ('address', 'organisation', 'state', 'zip_code', 'country', 'business_type'),
            'classes': ('collapse',)
        }),
        ('Preferences', {
            'fields': ('language', 'time_zone', 'currency', 'default_reply_handler'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'date_joined', 'last_login'),
            'classes': ('collapse',)
        }),
        ('Email Confirmation Codes', {
            'fields': ('confirmation_codes',),
            'classes': ('collapse',)
        }),
        ('Advanced', {
            'fields': ('password',),
            'classes': ('collapse',)
        })
    )
    
    def confirmation_codes(self, obj):
        """Show email confirmation codes for this user"""
        from django.utils.html import format_html
        tokens = EmailConfirmationToken.objects.filter(user=obj).order_by('-created_at')[:5]
        
        if not tokens:
            return "No confirmation codes"
        
        codes_html = []
        for token in tokens:
            status = "✅ Valid" if token.is_valid() else "❌ Invalid/Expired/Used"
            codes_html.append(
                f"<div style='margin: 5px 0; padding: 5px; border: 1px solid #ddd;'>"
                f"<strong>Code:</strong> {token.code}<br>"
                f"<strong>Status:</strong> {status}<br>"
                f"<strong>Created:</strong> {token.created_at.strftime('%Y-%m-%d %H:%M:%S')}<br>"
                f"<strong>Expires:</strong> {token.expires_at.strftime('%Y-%m-%d %H:%M:%S')}<br>"
                f"<strong>Used:</strong> {'Yes' if token.is_used else 'No'}"
                f"</div>"
            )
        
        return format_html('<br>'.join(codes_html))
    
    confirmation_codes.short_description = "Recent Email Confirmation Codes"
admin.site.register(User, UserAdmin)

class PasswordResetTokenAdmin(ImportExportModelAdmin):
    list_display = ("user", "token", "created_at", "expires_at", "is_used")
    list_filter = ("is_used", "created_at", "expires_at")
    search_fields = ["user__email", "user__username", "token"]
    readonly_fields = ("token", "created_at")
admin.site.register(PasswordResetToken, PasswordResetTokenAdmin)

class EmailConfirmationTokenAdmin(ImportExportModelAdmin):
    list_display = ("user", "code", "created_at", "expires_at", "is_used", "is_valid_status")
    list_filter = ("is_used", "created_at", "expires_at")
    search_fields = ["user__email", "user__username", "code"]
    readonly_fields = ("code", "created_at", "expires_at", "is_valid_status")
    
    fieldsets = (
        ('Email Confirmation', {
            'fields': ('user', 'code', 'is_used')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'expires_at', 'is_valid_status'),
            'classes': ('collapse',)
        })
    )
    
    def is_valid_status(self, obj):
        """Show if the token is currently valid"""
        return obj.is_valid()
    is_valid_status.boolean = True
    is_valid_status.short_description = "Valid"
    
    def get_queryset(self, request):
        """Optimize queryset with select_related"""
        return super().get_queryset(request).select_related('user')

admin.site.register(EmailConfirmationToken, EmailConfirmationTokenAdmin)

class OTPTokenAdmin(ImportExportModelAdmin):
    list_display = ("phone_number", "code", "created_at", "expires_at", "is_used", "attempts", "is_valid_status")
    list_filter = ("is_used", "created_at", "expires_at")
    search_fields = ["phone_number", "code"]
    readonly_fields = ("code", "created_at", "expires_at", "is_valid_status")
    ordering = ["-created_at"]
    
    fieldsets = (
        ('OTP Details', {
            'fields': ('phone_number', 'code', 'is_used', 'attempts')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'expires_at', 'is_valid_status'),
            'classes': ('collapse',)
        })
    )
    
    def is_valid_status(self, obj):
        """Show if the OTP is currently valid"""
        return obj.is_valid()
    is_valid_status.boolean = True
    is_valid_status.short_description = "Valid"

admin.site.register(OTPToken, OTPTokenAdmin)