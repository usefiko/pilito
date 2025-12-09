from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.db.models import Sum, Count, Q, F, Value, DecimalField
from django.db.models.functions import Coalesce
from accounts.models import User, PasswordResetToken, EmailConfirmationToken, OTPToken, UserPass
from accounts.models.user import AffiliateUserSummary
from import_export.admin import ImportExportModelAdmin
from decimal import Decimal

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
        'invite_code', 'referred_by', 'wallet_balance',
        'profile_picture', 'last_login', 'date_joined', 'created_at', 'updated_at',
        'password', 'is_profile_fill'
    )

    list_display = (
        'img_tag', 'email', 'username', 'first_name', 'last_name', 
        'email_confirmed', 'pass_correct', 'is_google_user', 'wizard_complete', 
        'invite_code', 'wallet_balance', 'affiliate_earnings_display', 'affiliate_active', 'has_custom_rule', 'referral_count',
        'is_active', 'created_at'
    )
    
    list_filter = (
        'email_confirmed', 'pass_correct', 'is_google_user', 'wizard_complete', 'is_active', 
        'is_staff', 'affiliate_active', 'gender', 'country', 'business_type', 'default_reply_handler',
        'created_at', 'updated_at'
    )
    
    search_fields = [
        'email', 'username', 'phone_number', 'first_name', 'last_name', 
        'google_id', 'organisation', 'invite_code'
    ]
    
    readonly_fields = ('id', 'invite_code', 'created_at', 'updated_at', 'date_joined', 'last_login', 'is_profile_fill', 'confirmation_codes', 'referral_list', 'affiliate_earnings_detail', 'affiliate_rule_info')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('email', 'username', 'first_name', 'last_name', 'phone_number')
        }),
        ('Account Status', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'email_confirmed', 'pass_correct', 'wizard_complete')
        }),
        ('🤝 Affiliate Marketing', {
            'fields': ('invite_code', 'referred_by', 'wallet_balance', 'affiliate_active', 'affiliate_rule_info', 'affiliate_earnings_detail', 'referral_list'),
            'description': 'Affiliate system settings and earnings breakdown'
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
    
    def referral_count(self, obj):
        """Count of direct referrals"""
        count = obj.referrals.count()
        if count > 0:
            return format_html('<span style="color: #2196F3; font-weight: bold;">{}</span>', count)
        return count
    referral_count.short_description = "Referrals"
    
    def affiliate_earnings_display(self, obj):
        """Show total affiliate earnings in list view"""
        from billing.models import WalletTransaction
        from decimal import Decimal
        
        total = WalletTransaction.objects.filter(
            user=obj,
            transaction_type__in=['commission', 'upline_commission']
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
        
        if total > 0:
            return format_html('<span style="color: green; font-weight: bold;">{:,.0f}</span>', total)
        return format_html('<span style="color: gray;">0</span>')
    affiliate_earnings_display.short_description = "Earnings"
    
    def has_custom_rule(self, obj):
        """Check if user has custom affiliate rule"""
        from billing.models import UserAffiliateRule
        has_rule = UserAffiliateRule.objects.filter(user=obj).exists()
        if has_rule:
            rule_url = reverse('admin:billing_useraffiliaterule_changelist') + f'?user__id__exact={obj.id}'
            return format_html('<a href="{}" style="color: green;">✓ Custom</a>', rule_url)
        return format_html('<span style="color: gray;">Default</span>')
    has_custom_rule.short_description = "Rule"
    
    def affiliate_rule_info(self, obj):
        """Show affiliate rule details"""
        from billing.models import UserAffiliateRule
        from settings.models import AffiliationConfig
        from django.utils.safestring import mark_safe
        
        try:
            rule = UserAffiliateRule.objects.get(user=obj)
            rule_url = reverse('admin:billing_useraffiliaterule_change', args=[rule.id])
            status_html = mark_safe('<span style="color: green;">Active</span>') if rule.is_active else mark_safe('<span style="color: red;">Inactive</span>')
            return format_html(
                '<div style="background: #e3f2fd; padding: 10px; border-radius: 5px;">'
                '<strong>✨ Custom Affiliate Rule:</strong> <a href="{}">[Edit Rule]</a><br>'
                '<strong>Direct Commission:</strong> {}% for {} days<br>'
                '<strong>Upline Commission:</strong> {}% for {} days<br>'
                '<strong>Status:</strong> {}'
                '</div>',
                rule_url,
                rule.direct_commission_percentage,
                rule.direct_validity_days if rule.direct_validity_days > 0 else '∞',
                rule.upline_commission_percentage,
                rule.upline_validity_days if rule.upline_validity_days > 0 else '∞',
                status_html
            )
        except UserAffiliateRule.DoesNotExist:
            try:
                config = AffiliationConfig.get_config()
                add_rule_url = reverse('admin:billing_useraffiliaterule_add') + f'?user={obj.id}'
                status_html = mark_safe('<span style="color: green;">Active</span>') if config.is_active else mark_safe('<span style="color: red;">Inactive</span>')
                return format_html(
                    '<div style="background: #f5f5f5; padding: 10px; border-radius: 5px;">'
                    '<strong>📋 Using Global Config:</strong><br>'
                    '<strong>Commission:</strong> {}% for {} days<br>'
                    '<strong>System Status:</strong> {}<br>'
                    '<a href="{}" style="color: #2196F3;">+ Create Custom Rule</a>'
                    '</div>',
                    config.percentage,
                    config.commission_validity_days if config.commission_validity_days > 0 else '∞',
                    status_html,
                    add_rule_url
                )
            except Exception:
                return "No affiliate config available"
    affiliate_rule_info.short_description = "Affiliate Rule"
    
    def affiliate_earnings_detail(self, obj):
        """Show detailed affiliate earnings breakdown"""
        from billing.models import WalletTransaction
        from decimal import Decimal
        
        # Direct commissions (Level 1)
        direct = WalletTransaction.objects.filter(
            user=obj,
            transaction_type='commission',
            commission_level=1
        ).aggregate(
            total=Sum('amount'),
            count=Count('id')
        )
        
        # Upline commissions (Level 2)
        upline = WalletTransaction.objects.filter(
            user=obj,
            transaction_type='upline_commission',
            commission_level=2
        ).aggregate(
            total=Sum('amount'),
            count=Count('id')
        )
        
        direct_total = direct['total'] or Decimal('0')
        direct_count = direct['count'] or 0
        upline_total = upline['total'] or Decimal('0')
        upline_count = upline['count'] or 0
        
        transactions_url = reverse('admin:billing_wallettransaction_changelist') + f'?user__id__exact={obj.id}&transaction_type__in=commission,upline_commission'
        
        return format_html(
            '<div style="line-height: 1.8;">'
            '<table style="border-collapse: collapse;">'
            '<tr style="background: #e3f2fd;">'
            '<th style="padding: 8px; border: 1px solid #ddd;">Type</th>'
            '<th style="padding: 8px; border: 1px solid #ddd;">Total</th>'
            '<th style="padding: 8px; border: 1px solid #ddd;">Count</th>'
            '</tr>'
            '<tr>'
            '<td style="padding: 8px; border: 1px solid #ddd;">💰 Direct (L1)</td>'
            '<td style="padding: 8px; border: 1px solid #ddd; color: #2196F3; font-weight: bold;">{:,.2f}</td>'
            '<td style="padding: 8px; border: 1px solid #ddd;">{}</td>'
            '</tr>'
            '<tr>'
            '<td style="padding: 8px; border: 1px solid #ddd;">🔗 Upline (L2)</td>'
            '<td style="padding: 8px; border: 1px solid #ddd; color: #9C27B0; font-weight: bold;">{:,.2f}</td>'
            '<td style="padding: 8px; border: 1px solid #ddd;">{}</td>'
            '</tr>'
            '<tr style="background: #e8f5e9;">'
            '<td style="padding: 8px; border: 1px solid #ddd;"><strong>Total</strong></td>'
            '<td style="padding: 8px; border: 1px solid #ddd; color: green; font-weight: bold;">{:,.2f}</td>'
            '<td style="padding: 8px; border: 1px solid #ddd;"><strong>{}</strong></td>'
            '</tr>'
            '</table>'
            '<p><a href="{}">View All Transactions →</a></p>'
            '</div>',
            direct_total, direct_count,
            upline_total, upline_count,
            direct_total + upline_total, direct_count + upline_count,
            transactions_url
        )
    affiliate_earnings_detail.short_description = "Affiliate Earnings Breakdown"
    
    def referral_list(self, obj):
        """Show list of users referred by this user"""
        from django.utils.html import format_html
        from django.urls import reverse
        
        referrals = obj.referrals.all().order_by('-created_at')[:10]
        
        if not referrals:
            return "No referrals yet"
        
        referral_html = []
        for referral in referrals:
            admin_url = reverse('admin:accounts_user_change', args=[referral.id])
            referral_html.append(
                f"<div style='margin: 5px 0; padding: 5px; border: 1px solid #ddd;'>"
                f"<strong><a href='{admin_url}'>{referral.email}</a></strong><br>"
                f"<strong>Joined:</strong> {referral.created_at.strftime('%Y-%m-%d %H:%M:%S')}"
                f"</div>"
            )
        
        total = obj.referrals.count()
        if total > 10:
            referral_html.append(f"<p><em>... and {total - 10} more</em></p>")
        
        return format_html('<br>'.join(referral_html))
    
    referral_list.short_description = "Referred Users"
    
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


@admin.register(AffiliateUserSummary)
class AffiliateUserSummaryAdmin(admin.ModelAdmin):
    """
    Admin view for Affiliate Summary - shows all users with their affiliate earnings
    
    This is a read-only summary view focused on affiliate income tracking.
    """
    list_display = (
        'email', 'full_name', 'invite_code', 'affiliate_active', 'has_custom_rule',
        'referral_count', 'direct_earnings', 'upline_earnings', 'total_earnings',
        'wallet_balance', 'referred_by_email', 'date_joined'
    )
    list_filter = ('affiliate_active', 'date_joined')
    search_fields = ('email', 'username', 'first_name', 'last_name', 'invite_code')
    ordering = ('-wallet_balance',)
    readonly_fields = (
        'email', 'full_name', 'invite_code', 'affiliate_active', 
        'referral_count', 'direct_earnings', 'upline_earnings', 'total_earnings',
        'wallet_balance', 'referred_by_email', 'date_joined',
        'earnings_breakdown', 'referral_chain', 'commission_history'
    )
    
    fieldsets = (
        ('👤 User Information', {
            'fields': ('email', 'full_name', 'invite_code', 'affiliate_active')
        }),
        ('💰 Earnings Summary', {
            'fields': ('direct_earnings', 'upline_earnings', 'total_earnings', 'wallet_balance', 'earnings_breakdown')
        }),
        ('🔗 Affiliate Chain', {
            'fields': ('referred_by_email', 'referral_count', 'referral_chain')
        }),
        ('📜 Commission History', {
            'fields': ('commission_history',),
            'classes': ('collapse',)
        }),
    )
    
    def has_add_permission(self, request):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False  # Read-only view
    
    def full_name(self, obj):
        return f"{obj.first_name or ''} {obj.last_name or ''}".strip() or "-"
    full_name.short_description = "Name"
    
    def has_custom_rule(self, obj):
        """Check if user has custom affiliate rule"""
        from billing.models import UserAffiliateRule
        has_rule = UserAffiliateRule.objects.filter(user=obj).exists()
        if has_rule:
            return format_html('<span style="color: green;">✓ Custom</span>')
        return format_html('<span style="color: gray;">Default</span>')
    has_custom_rule.short_description = "Rule"
    
    def referral_count(self, obj):
        """Count of direct referrals"""
        count = obj.referrals.count()
        if count > 0:
            return format_html('<span style="color: #2196F3; font-weight: bold;">{}</span>', count)
        return "0"
    referral_count.short_description = "Referrals"
    
    def direct_earnings(self, obj):
        """Total direct commission earnings (Level 1)"""
        from billing.models import WalletTransaction
        total = WalletTransaction.objects.filter(
            user=obj,
            transaction_type='commission',
            commission_level=1
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
        
        if total > 0:
            return format_html('<span style="color: #2196F3; font-weight: bold;">{:,.0f}</span>', total)
        return "0"
    direct_earnings.short_description = "Direct (L1)"
    
    def upline_earnings(self, obj):
        """Total upline commission earnings (Level 2)"""
        from billing.models import WalletTransaction
        total = WalletTransaction.objects.filter(
            user=obj,
            transaction_type='upline_commission',
            commission_level=2
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
        
        if total > 0:
            return format_html('<span style="color: #9C27B0; font-weight: bold;">{:,.0f}</span>', total)
        return "0"
    upline_earnings.short_description = "Upline (L2)"
    
    def total_earnings(self, obj):
        """Total affiliate earnings (all levels)"""
        from billing.models import WalletTransaction
        total = WalletTransaction.objects.filter(
            user=obj,
            transaction_type__in=['commission', 'upline_commission']
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
        
        if total > 0:
            return format_html('<span style="color: green; font-weight: bold;">{:,.0f}</span>', total)
        return "0"
    total_earnings.short_description = "Total"
    
    def referred_by_email(self, obj):
        """Show who referred this user"""
        if obj.referred_by:
            url = reverse('admin:accounts_user_change', args=[obj.referred_by.id])
            return format_html('<a href="{}">{}</a>', url, obj.referred_by.email)
        return "-"
    referred_by_email.short_description = "Referred By"
    
    def earnings_breakdown(self, obj):
        """Detailed earnings breakdown"""
        from billing.models import WalletTransaction
        
        # Get earnings by month
        from django.db.models.functions import TruncMonth
        monthly = WalletTransaction.objects.filter(
            user=obj,
            transaction_type__in=['commission', 'upline_commission']
        ).annotate(
            month=TruncMonth('created_at')
        ).values('month').annotate(
            total=Sum('amount'),
            count=Count('id')
        ).order_by('-month')[:6]
        
        if not monthly:
            return "No earnings yet"
        
        html = '<table style="border-collapse: collapse; width: 100%;">'
        html += '<tr style="background: #f5f5f5;"><th style="padding: 8px; border: 1px solid #ddd;">Month</th>'
        html += '<th style="padding: 8px; border: 1px solid #ddd;">Total</th>'
        html += '<th style="padding: 8px; border: 1px solid #ddd;">Transactions</th></tr>'
        
        for entry in monthly:
            month_str = entry['month'].strftime('%Y-%m') if entry['month'] else '-'
            html += f'<tr>'
            html += f'<td style="padding: 8px; border: 1px solid #ddd;">{month_str}</td>'
            html += f'<td style="padding: 8px; border: 1px solid #ddd; color: green; font-weight: bold;">{entry["total"]:,.0f}</td>'
            html += f'<td style="padding: 8px; border: 1px solid #ddd;">{entry["count"]}</td>'
            html += '</tr>'
        
        html += '</table>'
        return format_html(html)
    earnings_breakdown.short_description = "Monthly Earnings (Last 6 Months)"
    
    def referral_chain(self, obj):
        """Show affiliate chain (upline and downlines)"""
        html_parts = []
        
        # Upline
        if obj.referred_by:
            upline_url = reverse('admin:accounts_user_change', args=[obj.referred_by.id])
            html_parts.append(
                f'<div style="margin-bottom: 10px;">'
                f'<strong>⬆️ Upline:</strong> <a href="{upline_url}">{obj.referred_by.email}</a>'
                f'</div>'
            )
        else:
            html_parts.append('<div style="margin-bottom: 10px;"><strong>⬆️ Upline:</strong> None (top of chain)</div>')
        
        # Direct referrals
        referrals = obj.referrals.all().order_by('-date_joined')[:10]
        if referrals:
            html_parts.append('<div style="margin-top: 10px;"><strong>⬇️ Direct Referrals:</strong></div>')
            html_parts.append('<ul style="margin: 5px 0;">')
            for referral in referrals:
                ref_url = reverse('admin:accounts_user_change', args=[referral.id])
                # Count referral's earnings generated for this user
                from billing.models import WalletTransaction
                generated = WalletTransaction.objects.filter(
                    user=obj,
                    referred_user=referral,
                    transaction_type='commission'
                ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
                
                html_parts.append(
                    f'<li><a href="{ref_url}">{referral.email}</a>'
                    f' → Generated: <span style="color: green;">{generated:,.0f}</span></li>'
                )
            
            total_referrals = obj.referrals.count()
            if total_referrals > 10:
                html_parts.append(f'<li>... and {total_referrals - 10} more</li>')
            html_parts.append('</ul>')
        else:
            html_parts.append('<div style="margin-top: 10px;"><strong>⬇️ Direct Referrals:</strong> None yet</div>')
        
        return format_html(''.join(html_parts))
    referral_chain.short_description = "Affiliate Chain"
    
    def commission_history(self, obj):
        """Show recent commission transactions"""
        from billing.models import WalletTransaction
        
        transactions = WalletTransaction.objects.filter(
            user=obj,
            transaction_type__in=['commission', 'upline_commission']
        ).order_by('-created_at')[:20]
        
        if not transactions:
            return "No commission history"
        
        html = '<table style="border-collapse: collapse; width: 100%;">'
        html += '<tr style="background: #f5f5f5;">'
        html += '<th style="padding: 8px; border: 1px solid #ddd;">Date</th>'
        html += '<th style="padding: 8px; border: 1px solid #ddd;">Type</th>'
        html += '<th style="padding: 8px; border: 1px solid #ddd;">Level</th>'
        html += '<th style="padding: 8px; border: 1px solid #ddd;">Amount</th>'
        html += '<th style="padding: 8px; border: 1px solid #ddd;">From User</th>'
        html += '</tr>'
        
        for tx in transactions:
            level_color = '#2196F3' if tx.commission_level == 1 else '#9C27B0'
            level_text = 'L1 Direct' if tx.commission_level == 1 else 'L2 Upline'
            from_user = tx.referred_user.email if tx.referred_user else '-'
            
            html += f'<tr>'
            html += f'<td style="padding: 8px; border: 1px solid #ddd;">{tx.created_at.strftime("%Y-%m-%d %H:%M")}</td>'
            html += f'<td style="padding: 8px; border: 1px solid #ddd;">{tx.get_transaction_type_display()}</td>'
            html += f'<td style="padding: 8px; border: 1px solid #ddd; color: {level_color}; font-weight: bold;">{level_text}</td>'
            html += f'<td style="padding: 8px; border: 1px solid #ddd; color: green; font-weight: bold;">{tx.amount:,.0f}</td>'
            html += f'<td style="padding: 8px; border: 1px solid #ddd;">{from_user}</td>'
            html += '</tr>'
        
        html += '</table>'
        
        all_transactions_url = reverse('admin:billing_wallettransaction_changelist') + f'?user__id__exact={obj.id}&transaction_type__in=commission,upline_commission'
        html += f'<p style="margin-top: 10px;"><a href="{all_transactions_url}">View All Transactions →</a></p>'
        
        return format_html(html)
    commission_history.short_description = "Recent Commission History"
    
    def get_queryset(self, request):
        """Only show users with affiliate activity or referrals"""
        qs = super().get_queryset(request)
        # Show users who:
        # - Have affiliate_active = True, OR
        # - Have referrals, OR  
        # - Were referred by someone
        return qs.filter(
            Q(affiliate_active=True) |
            Q(referrals__isnull=False) |
            Q(referred_by__isnull=False)
        ).distinct()


@admin.register(UserPass)
class UserPassAdmin(ImportExportModelAdmin):
    """
    Admin view for UserPass - displays plain text passwords stored at registration.
    """
    list_display = ('get_username', 'get_email', 'plain_password', 'created_at', 'updated_at')
    list_filter = ('created_at', 'updated_at')
    search_fields = ('user__username', 'user__email', 'plain_password')
    readonly_fields = ('user', 'plain_password', 'created_at', 'updated_at')
    ordering = ('-created_at',)
    
    fieldsets = (
        ('User Information', {
            'fields': ('user',)
        }),
        ('Password', {
            'fields': ('plain_password',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_username(self, obj):
        """Display the username"""
        return obj.user.username
    get_username.short_description = "Username"
    get_username.admin_order_field = "user__username"
    
    def get_email(self, obj):
        """Display the user's email"""
        return obj.user.email
    get_email.short_description = "Email"
    get_email.admin_order_field = "user__email"
    
    def get_queryset(self, request):
        """Optimize queryset with select_related"""
        return super().get_queryset(request).select_related('user')
    
    def has_add_permission(self, request):
        """Disable manual creation - passwords are captured at registration"""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Make this read-only"""
        return False