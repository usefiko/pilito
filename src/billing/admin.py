from django.contrib import admin
from django.utils.html import format_html
from import_export.admin import ImportExportModelAdmin
from .models import TokenPlan, FullPlan, Subscription, Payment, TokenUsage, Purchases, WalletTransaction


@admin.register(TokenPlan)
class TokenPlanAdmin(ImportExportModelAdmin):
    list_display = ('name', 'price', 'tokens_included', 'is_recurring', 'is_active', 'created_at')
    list_filter = ('is_recurring', 'is_active', 'created_at')
    search_fields = ('name', 'description')
    ordering = ('price',)
    readonly_fields = ('created_at', 'updated_at')


@admin.register(FullPlan)
class FullPlanAdmin(ImportExportModelAdmin):
    list_display = ('name', 'tokens_included', 'duration_days', 'is_yearly', 'is_recommended', 'price', 'is_active', 'created_at')
    list_filter = ('is_yearly', 'is_recommended', 'is_active', 'created_at')
    search_fields = ('name', 'description')
    ordering = ('is_yearly', 'price')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(Subscription)
class SubscriptionAdmin(ImportExportModelAdmin):
    list_display = ('user_email', 'plan_name', 'tokens_remaining', 'is_active', 'subscription_status', 'cancellation_status', 'days_left', 'start_date', 'end_date')
    list_filter = ('is_active', 'status', 'cancel_at_period_end', 'token_plan', 'full_plan', 'start_date', 'end_date')
    search_fields = ('user__email', 'user__first_name', 'user__last_name', 'token_plan__name', 'full_plan__name', 'stripe_subscription_id')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at', 'subscription_status_display', 'canceled_at')
    raw_id_fields = ('user', 'token_plan', 'full_plan')
    
    fieldsets = (
        ('User & Plan', {
            'fields': ('user', 'token_plan', 'full_plan')
        }),
        ('Status', {
            'fields': ('is_active', 'status', 'tokens_remaining')
        }),
        ('Duration', {
            'fields': ('start_date', 'end_date', 'trial_end')
        }),
        ('Cancellation', {
            'fields': ('cancel_at_period_end', 'canceled_at'),
            'classes': ('collapse',)
        }),
        ('Stripe', {
            'fields': ('stripe_customer_id', 'stripe_subscription_id'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'User Email'

    def plan_name(self, obj):
        if obj.token_plan:
            return obj.token_plan.name
        if obj.full_plan:
            return obj.full_plan.name
        return "-"
    plan_name.short_description = 'Plan'

    def subscription_status(self, obj):
        if obj.is_subscription_active():
            return format_html('<span style="color: green;">●</span> Active')
        else:
            return format_html('<span style="color: red;">●</span> Inactive')
    subscription_status.short_description = 'Status'
    
    def cancellation_status(self, obj):
        if obj.cancel_at_period_end:
            return format_html('<span style="color: orange;">⚠️ Cancels at period end</span>')
        elif obj.status == 'canceled':
            return format_html('<span style="color: red;">❌ Canceled</span>')
        else:
            return format_html('<span style="color: green;">✓ Active</span>')
    cancellation_status.short_description = 'Cancellation'

    def days_left(self, obj):
        days = obj.days_remaining()
        if days is None:
            return "Unlimited"
        elif days > 0:
            return f"{days} days"
        else:
            return "Expired"
    days_left.short_description = 'Days Remaining'

    def subscription_status_display(self, obj):
        status = "Active" if obj.is_subscription_active() else "Inactive"
        days = obj.days_remaining()
        tokens = obj.tokens_remaining
        
        status_info = f"Status: {status}\n"
        status_info += f"Tokens Remaining: {tokens}\n"
        
        if days is not None:
            status_info += f"Days Remaining: {days}"
        else:
            status_info += "Duration: Unlimited"
            
        return status_info
    subscription_status_display.short_description = 'Subscription Status'


@admin.register(Payment)
class PaymentAdmin(ImportExportModelAdmin):
    list_display = ('user_email', 'plan_name', 'amount', 'status', 'payment_method', 'payment_date', 'transaction_id')
    list_filter = ('status', 'payment_method', 'payment_date', 'token_plan', 'full_plan')
    search_fields = ('user__email', 'transaction_id', 'token_plan__name', 'full_plan__name', 'ref_id', 'authority')
    ordering = ('-payment_date',)
    readonly_fields = ('created_at', 'updated_at')
    raw_id_fields = ('user', 'subscription', 'token_plan', 'full_plan')

    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'User Email'

    def plan_name(self, obj):
        if obj.token_plan:
            return obj.token_plan.name
        if obj.full_plan:
            return obj.full_plan.name
        return "-"
    plan_name.short_description = 'Plan'


@admin.register(TokenUsage)
class TokenUsageAdmin(ImportExportModelAdmin):
    list_display = ('user_email', 'plan_name', 'tokens_display', 'description_preview', 'usage_date', 'id')
    list_filter = ('usage_date', 'subscription__token_plan', 'subscription__full_plan')
    search_fields = ('subscription__user__email', 'description', 'subscription__token_plan__name', 'subscription__full_plan__name')
    ordering = ('-usage_date',)
    readonly_fields = ('created_at', 'usage_date')
    raw_id_fields = ('subscription',)
    
    fieldsets = (
        ('Usage Info', {
            'fields': ('subscription', 'used_tokens', 'description')
        }),
        ('Timestamps', {
            'fields': ('usage_date', 'created_at'),
            'classes': ('collapse',)
        }),
    )

    def user_email(self, obj):
        return obj.subscription.user.email
    user_email.short_description = 'User Email'

    def plan_name(self, obj):
        if obj.subscription.token_plan:
            return obj.subscription.token_plan.name
        if obj.subscription.full_plan:
            return obj.subscription.full_plan.name
        return "-"
    plan_name.short_description = 'Plan'
    
    def tokens_display(self, obj):
        """Display tokens with formatting"""
        return f"🎯 {obj.used_tokens:,}"
    tokens_display.short_description = 'Tokens Used'
    
    def description_preview(self, obj):
        """Show shortened description"""
        if len(obj.description) > 40:
            return obj.description[:40] + '...'
        return obj.description
    description_preview.short_description = 'Description'


# Legacy admin (keep for backward compatibility)
class PurchasesAdmin(ImportExportModelAdmin):
    list_display = ('user', 'price', 'created_at', 'paid')
    list_filter = ("created_at", "user", "paid")
    
admin.site.register(Purchases, PurchasesAdmin)


@admin.register(WalletTransaction)
class WalletTransactionAdmin(ImportExportModelAdmin):
    """
    Admin interface for Wallet Transactions
    
    Shows all wallet transactions including affiliate commissions
    """
    list_display = (
        'id', 'user_email', 'transaction_type', 'amount_display', 
        'balance_after', 'referred_user_email', 'created_at'
    )
    list_filter = ('transaction_type', 'created_at')
    search_fields = (
        'user__email', 'user__username', 
        'referred_user__email', 'description'
    )
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'balance_after')
    raw_id_fields = ('user', 'related_payment', 'referred_user', 'created_by')
    
    fieldsets = (
        ('Transaction Information', {
            'fields': ('user', 'transaction_type', 'amount', 'balance_after', 'description')
        }),
        ('Related Information', {
            'fields': ('related_payment', 'referred_user', 'created_by'),
            'classes': ('collapse',)
        }),
        ('Timestamp', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'User'
    user_email.admin_order_field = 'user__email'
    
    def amount_display(self, obj):
        """Display amount with color coding"""
        if obj.amount >= 0:
            return format_html('<span style="color: green;">+{:,.2f}</span>', obj.amount)
        return format_html('<span style="color: red;">{:,.2f}</span>', obj.amount)
    amount_display.short_description = 'Amount'
    amount_display.admin_order_field = 'amount'
    
    def referred_user_email(self, obj):
        """Show which user generated this commission"""
        if obj.referred_user:
            return obj.referred_user.email
        return "-"
    referred_user_email.short_description = 'From User'
    referred_user_email.admin_order_field = 'referred_user__email'
    
    def has_add_permission(self, request):
        # Transactions are created automatically by signals
        return False
