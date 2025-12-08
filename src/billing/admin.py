from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from django.db.models import Sum, Count, Q
from django.urls import reverse
from import_export.admin import ImportExportModelAdmin
from import_export import resources
from .models import TokenPlan, FullPlan, Subscription, Payment, TokenUsage, Purchases, WalletTransaction, BillingInformation, Withdraw, UserAffiliateRule


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
    list_display = ('user_email', 'plan_name', 'actual_tokens_remaining', 'tokens_consumed', 'is_active', 'subscription_status', 'cancellation_status', 'days_left', 'start_date', 'end_date')
    list_filter = ('is_active', 'status', 'cancel_at_period_end', 'token_plan', 'full_plan', 'start_date', 'end_date')
    search_fields = ('user__email', 'user__first_name', 'user__last_name', 'token_plan__name', 'full_plan__name', 'stripe_subscription_id')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at', 'subscription_status_display', 'canceled_at', 'actual_tokens_remaining', 'tokens_consumed')
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

    def actual_tokens_remaining(self, obj):
        """Show ACCURATE remaining tokens based on actual AI usage"""
        try:
            from billing.utils import get_accurate_tokens_remaining
            original, consumed, remaining = get_accurate_tokens_remaining(obj.user)
            
            if remaining <= 0:
                return format_html('<span style="color: red; font-weight: bold;">0 ❌</span>')
            elif remaining < 1000:
                return format_html('<span style="color: orange;">{}</span>', remaining)
            else:
                return format_html('<span style="color: green;">{}</span>', remaining)
        except Exception as e:
            return format_html('<span style="color: gray;">Error: {}</span>', str(e)[:30])
    actual_tokens_remaining.short_description = 'Actual Remaining'
    
    def tokens_consumed(self, obj):
        """Show total tokens consumed since subscription started"""
        try:
            from billing.utils import get_accurate_tokens_remaining
            original, consumed, remaining = get_accurate_tokens_remaining(obj.user)
            return format_html('{} / {}', consumed, original)
        except Exception:
            return '-'
    tokens_consumed.short_description = 'Consumed/Total'

    def subscription_status_display(self, obj):
        """Detailed status display for subscription detail page"""
        try:
            from billing.utils import get_accurate_tokens_remaining
            original, consumed, remaining = get_accurate_tokens_remaining(obj.user)
        except Exception:
            original, consumed, remaining = 0, 0, 0
        
        status = "Active" if obj.is_subscription_active() else "Inactive"
        days = obj.days_remaining()
        
        status_info = f"Status: {status}\n"
        status_info += f"Original Tokens: {original}\n"
        status_info += f"Consumed Tokens: {consumed}\n"
        status_info += f"Actual Remaining: {remaining}\n"
        status_info += f"DB tokens_remaining (stale): {obj.tokens_remaining}\n"
        
        if days is not None:
            status_info += f"Days Remaining: {days}"
        else:
            status_info += "Duration: Unlimited"
            
        return status_info
    subscription_status_display.short_description = 'Subscription Status (Detailed)'


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
    
    Shows all wallet transactions including affiliate commissions with multi-level support
    """
    list_display = (
        'id', 'user_email', 'transaction_type', 'commission_level_display',
        'amount_display', 'commission_percentage', 'source_amount',
        'balance_after', 'referred_user_email', 'created_at'
    )
    list_filter = ('transaction_type', 'commission_level', 'created_at')
    search_fields = (
        'user__email', 'user__username', 
        'referred_user__email', 'description'
    )
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'balance_after', 'commission_level', 'commission_percentage', 'source_amount', 'source_commission')
    raw_id_fields = ('user', 'related_payment', 'referred_user', 'created_by', 'source_commission')
    
    fieldsets = (
        ('Transaction Information', {
            'fields': ('user', 'transaction_type', 'amount', 'balance_after', 'description')
        }),
        ('Commission Details', {
            'fields': ('commission_level', 'commission_percentage', 'source_amount', 'source_commission'),
            'classes': ('collapse',),
            'description': 'Commission-specific information for affiliate transactions'
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
    
    def commission_level_display(self, obj):
        """Display commission level with visual indicator"""
        if obj.commission_level == 1:
            return format_html('<span style="color: #2196F3; font-weight: bold;">L1 Direct</span>')
        elif obj.commission_level == 2:
            return format_html('<span style="color: #9C27B0; font-weight: bold;">L2 Upline</span>')
        return "-"
    commission_level_display.short_description = 'Level'
    commission_level_display.admin_order_field = 'commission_level'
    
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


@admin.register(BillingInformation)
class BillingInformationAdmin(ImportExportModelAdmin):
    """
    Admin interface for Billing Information
    
    View and manage user banking information for withdrawals
    """
    list_display = ('user_email', 'full_name', 'sheba_number', 'bank_name', 'created_at')
    search_fields = ('user__email', 'user__username', 'first_name', 'last_name', 'sheba_number', 'bank_name')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at')
    raw_id_fields = ('user',)
    
    fieldsets = (
        ('User Information', {
            'fields': ('user',)
        }),
        ('Banking Details', {
            'fields': ('first_name', 'last_name', 'sheba_number', 'bank_name')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'User Email'
    user_email.admin_order_field = 'user__email'
    
    def full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}"
    full_name.short_description = 'Name'


@admin.register(Withdraw)
class WithdrawAdmin(ImportExportModelAdmin):
    """
    Admin interface for Withdrawal Requests
    
    Manage user withdrawal requests with status updates
    """
    list_display = (
        'id', 'user_email', 'amount_display', 'status_display', 
        'date', 'processed_date', 'processed_by_email'
    )
    list_filter = ('status', 'date', 'processed_date')
    search_fields = (
        'user__email', 'user__username', 
        'processed_by__email', 'admin_notes'
    )
    ordering = ('-created_at',)
    readonly_fields = ('date', 'created_at', 'updated_at', 'wallet_transaction', 'user_wallet_balance')
    raw_id_fields = ('user', 'processed_by', 'wallet_transaction')
    
    fieldsets = (
        ('Request Information', {
            'fields': ('user', 'amount', 'date', 'user_wallet_balance')
        }),
        ('Status Management', {
            'fields': ('status', 'processed_date', 'processed_by', 'admin_notes'),
            'description': 'Update status to "paid" to mark as completed. Status changes are tracked.'
        }),
        ('Transaction Link', {
            'fields': ('wallet_transaction',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['mark_as_paid', 'mark_as_processing', 'mark_as_rejected']
    
    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'User Email'
    user_email.admin_order_field = 'user__email'
    
    def amount_display(self, obj):
        """Display amount with formatting"""
        return format_html('<strong>{:,.0f} Tomans</strong>', obj.amount)
    amount_display.short_description = 'Amount'
    amount_display.admin_order_field = 'amount'
    
    def status_display(self, obj):
        """Display status with color coding"""
        status_colors = {
            'pending': 'orange',
            'processing': 'blue',
            'paid': 'green',
            'rejected': 'red',
            'cancelled': 'gray'
        }
        color = status_colors.get(obj.status, 'black')
        return format_html(
            '<span style="color: {}; font-weight: bold;">● {}</span>', 
            color, 
            obj.get_status_display()
        )
    status_display.short_description = 'Status'
    status_display.admin_order_field = 'status'
    
    def processed_by_email(self, obj):
        """Show who processed this withdrawal"""
        if obj.processed_by:
            return obj.processed_by.email
        return "-"
    processed_by_email.short_description = 'Processed By'
    processed_by_email.admin_order_field = 'processed_by__email'
    
    def user_wallet_balance(self, obj):
        """Show current wallet balance of the user"""
        return format_html('{:,.2f} Tomans', obj.user.wallet_balance)
    user_wallet_balance.short_description = 'Current Wallet Balance'
    
    def save_model(self, request, obj, form, change):
        """Override save to track who processed the withdrawal"""
        if change:
            # Check if status changed to paid
            original_obj = Withdraw.objects.get(pk=obj.pk)
            if original_obj.status != 'paid' and obj.status == 'paid':
                obj.processed_date = timezone.now()
                obj.processed_by = request.user
        
        super().save_model(request, obj, form, change)
    
    # Admin Actions
    def mark_as_paid(self, request, queryset):
        """Mark selected withdrawals as paid"""
        updated = 0
        for withdraw in queryset:
            if withdraw.status != 'paid':
                withdraw.status = 'paid'
                withdraw.processed_date = timezone.now()
                withdraw.processed_by = request.user
                withdraw.save()
                updated += 1
        
        self.message_user(
            request,
            f'{updated} withdrawal(s) marked as paid successfully.'
        )
    mark_as_paid.short_description = 'Mark selected as Paid'
    
    def mark_as_processing(self, request, queryset):
        """Mark selected withdrawals as processing"""
        updated = queryset.update(status='processing')
        self.message_user(
            request,
            f'{updated} withdrawal(s) marked as processing.'
        )
    mark_as_processing.short_description = 'Mark selected as Processing'
    
    def mark_as_rejected(self, request, queryset):
        """Mark selected withdrawals as rejected"""
        updated = 0
        for withdraw in queryset:
            if withdraw.status == 'pending':
                # Refund the amount back to wallet
                withdraw.user.wallet_balance += withdraw.amount
                withdraw.user.save(update_fields=['wallet_balance', 'updated_at'])
                
                # Create refund transaction
                WalletTransaction.objects.create(
                    user=withdraw.user,
                    transaction_type='refund',
                    amount=withdraw.amount,
                    balance_after=withdraw.user.wallet_balance,
                    description=f"Refund for rejected withdrawal request #{withdraw.id}",
                    created_by=request.user
                )
                
                withdraw.status = 'rejected'
                withdraw.processed_date = timezone.now()
                withdraw.processed_by = request.user
                withdraw.save()
                updated += 1
        
        self.message_user(
            request,
            f'{updated} withdrawal(s) rejected and refunded.'
        )
    mark_as_rejected.short_description = 'Reject selected (with refund)'


@admin.register(UserAffiliateRule)
class UserAffiliateRuleAdmin(ImportExportModelAdmin):
    """
    Admin interface for User Affiliate Rules
    
    Configure per-user affiliate commission settings including multi-level support.
    
    Example Scenario:
    - Nima: Direct 20% for 365 days (earns from his referrals' payments)
    - Mohammad referred Nima: Upline 10% for 365 days (earns from Nima's affiliate income)
    """
    list_display = (
        'user_email', 'direct_commission_display', 'direct_validity_display',
        'upline_commission_display', 'upline_validity_display', 
        'is_active', 'total_earnings', 'referral_count', 'created_at'
    )
    list_filter = ('is_active', 'created_at', 'updated_at')
    search_fields = ('user__email', 'user__username', 'user__first_name', 'user__last_name', 'notes')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at', 'total_earnings', 'referral_count', 'affiliate_chain', 'example_calculation')
    raw_id_fields = ('user', 'created_by')
    autocomplete_fields = ['user']
    
    fieldsets = (
        ('👤 User', {
            'fields': ('user',),
            'description': 'Select the user to configure affiliate rules for'
        }),
        ('💰 Direct Commission (Level 1)', {
            'fields': ('direct_commission_percentage', 'direct_validity_days'),
            'description': '''
                <p><strong>Direct Commission:</strong> What this user earns from their direct referrals' payments.</p>
                <ul>
                    <li><strong>Percentage:</strong> e.g., 20% means user earns 20% of each payment their referrals make</li>
                    <li><strong>Validity:</strong> How many days after referral registration the commission applies (0 = forever)</li>
                </ul>
            '''
        }),
        ('🔗 Upline Commission (Level 2 - Multi-Level)', {
            'fields': ('upline_commission_percentage', 'upline_validity_days'),
            'description': '''
                <p><strong>Upline Commission:</strong> What this user earns from their referrals' affiliate earnings.</p>
                <ul>
                    <li><strong>Example:</strong> If Mohammad has 10% upline commission and Nima (referred by Mohammad) earns 1,000 from affiliates, Mohammad gets 100</li>
                    <li><strong>Validity:</strong> How many days from when the referral joined (0 = forever)</li>
                </ul>
            '''
        }),
        ('⚙️ Status', {
            'fields': ('is_active', 'notes', 'created_by'),
        }),
        ('📊 Statistics', {
            'fields': ('total_earnings', 'referral_count', 'affiliate_chain', 'example_calculation'),
            'classes': ('collapse',),
            'description': 'View affiliate statistics and earnings'
        }),
        ('📅 Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def user_email(self, obj):
        url = reverse('admin:accounts_user_change', args=[obj.user.id])
        return format_html('<a href="{}">{}</a>', url, obj.user.email)
    user_email.short_description = 'User'
    user_email.admin_order_field = 'user__email'
    
    def direct_commission_display(self, obj):
        """Display direct commission with color"""
        if obj.direct_commission_percentage > 0:
            return format_html(
                '<span style="color: #2196F3; font-weight: bold;">{}%</span>',
                obj.direct_commission_percentage
            )
        return format_html('<span style="color: gray;">0%</span>')
    direct_commission_display.short_description = 'Direct %'
    direct_commission_display.admin_order_field = 'direct_commission_percentage'
    
    def direct_validity_display(self, obj):
        """Display direct validity period"""
        if obj.direct_validity_days == 0:
            return "∞ Forever"
        return f"{obj.direct_validity_days} days"
    direct_validity_display.short_description = 'Direct Validity'
    
    def upline_commission_display(self, obj):
        """Display upline commission with color"""
        if obj.upline_commission_percentage > 0:
            return format_html(
                '<span style="color: #9C27B0; font-weight: bold;">{}%</span>',
                obj.upline_commission_percentage
            )
        return format_html('<span style="color: gray;">0%</span>')
    upline_commission_display.short_description = 'Upline %'
    upline_commission_display.admin_order_field = 'upline_commission_percentage'
    
    def upline_validity_display(self, obj):
        """Display upline validity period"""
        if obj.upline_validity_days == 0:
            return "∞ Forever"
        return f"{obj.upline_validity_days} days"
    upline_validity_display.short_description = 'Upline Validity'
    
    def total_earnings(self, obj):
        """Calculate total affiliate earnings for this user"""
        from decimal import Decimal
        
        # Direct commissions (Level 1)
        direct = WalletTransaction.objects.filter(
            user=obj.user,
            transaction_type='commission',
            commission_level=1
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
        
        # Upline commissions (Level 2)
        upline = WalletTransaction.objects.filter(
            user=obj.user,
            transaction_type='upline_commission',
            commission_level=2
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
        
        return format_html(
            '<div style="line-height: 1.6;">'
            '<strong>Direct (L1):</strong> <span style="color: #2196F3;">{:,.2f}</span><br>'
            '<strong>Upline (L2):</strong> <span style="color: #9C27B0;">{:,.2f}</span><br>'
            '<strong>Total:</strong> <span style="color: green; font-weight: bold;">{:,.2f}</span>'
            '</div>',
            direct, upline, direct + upline
        )
    total_earnings.short_description = 'Total Earnings'
    
    def referral_count(self, obj):
        """Count of direct referrals"""
        count = obj.user.referrals.count()
        if count > 0:
            url = reverse('admin:accounts_user_changelist') + f'?referred_by__id__exact={obj.user.id}'
            return format_html('<a href="{}">{} referrals</a>', url, count)
        return "0 referrals"
    referral_count.short_description = 'Referrals'
    
    def affiliate_chain(self, obj):
        """Show the affiliate chain (upline and downlines)"""
        html_parts = []
        
        # Upline
        if obj.user.referred_by:
            upline = obj.user.referred_by
            upline_url = reverse('admin:accounts_user_change', args=[upline.id])
            html_parts.append(
                f'<div style="margin-bottom: 10px;">'
                f'<strong>⬆️ Upline (Referrer):</strong> <a href="{upline_url}">{upline.email}</a>'
                f'</div>'
            )
        else:
            html_parts.append('<div style="margin-bottom: 10px;"><strong>⬆️ Upline:</strong> None (top of chain)</div>')
        
        # Downlines (referrals)
        referrals = obj.user.referrals.all()[:10]
        if referrals:
            html_parts.append('<div><strong>⬇️ Downlines (Referrals):</strong></div><ul>')
            for referral in referrals:
                ref_url = reverse('admin:accounts_user_change', args=[referral.id])
                # Check if referral has custom rule
                has_rule = UserAffiliateRule.objects.filter(user=referral).exists()
                rule_badge = ' <span style="color: green;">✓ Has Rule</span>' if has_rule else ''
                html_parts.append(f'<li><a href="{ref_url}">{referral.email}</a>{rule_badge}</li>')
            if obj.user.referrals.count() > 10:
                html_parts.append(f'<li>... and {obj.user.referrals.count() - 10} more</li>')
            html_parts.append('</ul>')
        else:
            html_parts.append('<div><strong>⬇️ Downlines:</strong> No referrals yet</div>')
        
        return format_html(''.join(html_parts))
    affiliate_chain.short_description = 'Affiliate Chain'
    
    def example_calculation(self, obj):
        """Show example commission calculations"""
        from decimal import Decimal
        
        payment_amounts = [100000, 500000, 1000000]
        
        html = '<table style="border-collapse: collapse; margin-top: 10px;">'
        html += '<tr style="background: #f5f5f5;">'
        html += '<th style="padding: 8px; border: 1px solid #ddd;">Payment Amount</th>'
        html += f'<th style="padding: 8px; border: 1px solid #ddd;">Direct ({obj.direct_commission_percentage}%)</th>'
        html += f'<th style="padding: 8px; border: 1px solid #ddd;">Upline from 10K ({obj.upline_commission_percentage}%)</th>'
        html += '</tr>'
        
        for amount in payment_amounts:
            direct = obj.calculate_direct_commission(amount)
            # Example: if user's referral earned 10,000 commission
            upline = obj.calculate_upline_commission(10000)
            html += f'<tr>'
            html += f'<td style="padding: 8px; border: 1px solid #ddd;">{amount:,}</td>'
            html += f'<td style="padding: 8px; border: 1px solid #ddd; color: #2196F3;">{direct:,.2f}</td>'
            html += f'<td style="padding: 8px; border: 1px solid #ddd; color: #9C27B0;">{upline:,.2f}</td>'
            html += '</tr>'
        
        html += '</table>'
        html += '<p style="margin-top: 10px; color: #666; font-size: 12px;">'
        html += '<em>Note: Upline column shows what user earns if their referral earns 10,000 commission</em>'
        html += '</p>'
        
        return format_html(html)
    example_calculation.short_description = 'Example Calculations'
    
    def save_model(self, request, obj, form, change):
        """Track who created/modified the rule"""
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'created_by')
