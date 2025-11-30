from django.db import models
from django.conf import settings
from django.utils import timezone
from accounts.models import User
from .utils import days_left_from_now, enforce_account_deactivation_for_user


class TokenPlan(models.Model):
    """
    Token-based plans (no time duration)
    """
    name = models.CharField(max_length=100)
    price = models.IntegerField(default=0, help_text="Price of the plan")
    tokens_included = models.IntegerField()
    is_recurring = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True, help_text="Whether this plan is available for purchase")
    description = models.TextField(null=True, blank=True)
    stripe_product_id = models.CharField(max_length=255, null=True, blank=True, help_text='Stripe Product ID')
    stripe_price_id = models.CharField(max_length=255, null=True, blank=True, help_text='Stripe Price ID')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} - ${self.price} ({self.tokens_included} tokens)"

    class Meta:
        ordering = ['price']


class FullPlan(models.Model):
    """
    Complete plan with tokens and time duration
    """
    name = models.CharField(max_length=100)
    tokens_included = models.IntegerField()
    duration_days = models.IntegerField(help_text="Duration of the plan in days")
    is_recommended = models.BooleanField(default=False)
    is_yearly = models.BooleanField(default=False)
    price = models.IntegerField(default=0, help_text="Price of the plan")
    is_active = models.BooleanField(default=True)
    description = models.TextField(null=True, blank=True)
    stripe_product_id = models.CharField(max_length=255, null=True, blank=True, help_text='Stripe Product ID')
    stripe_price_id = models.CharField(max_length=255, null=True, blank=True, help_text='Stripe Price ID')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} - {self.duration_days}d / {self.tokens_included} tokens"

    class Meta:
        ordering = ['is_yearly', 'price']


class Subscription(models.Model):
    """
    User's active subscription with remaining tokens and status
    """
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='subscription')
    token_plan = models.ForeignKey(TokenPlan, on_delete=models.CASCADE, null=True, blank=True)
    full_plan = models.ForeignKey(FullPlan, on_delete=models.CASCADE, null=True, blank=True)
    # Queued plans (activated after current plan expires)
    queued_full_plan = models.ForeignKey(
        FullPlan, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='queued_subscriptions',
        help_text="Full plan scheduled to activate at end_date of current plan"
    )
    queued_token_plan = models.ForeignKey(
        TokenPlan,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='queued_subscriptions',
        help_text="Token plan scheduled to activate at end_date of current plan"
    )
    queued_tokens_amount = models.IntegerField(
        null=True,
        blank=True,
        help_text="Number of tokens to be added when queued plan activates"
    )
    start_date = models.DateTimeField(default=timezone.now)
    end_date = models.DateTimeField(null=True, blank=True)
    tokens_remaining = models.IntegerField()
    is_active = models.BooleanField(default=True)
    status = models.CharField(max_length=32, default='active', choices=[
        ('trialing', 'Trialing'),
        ('active', 'Active'),
        ('past_due', 'Past Due'),
        ('canceled', 'Canceled'),
        ('unpaid', 'Unpaid'),
        ('incomplete', 'Incomplete'),
        ('incomplete_expired', 'Incomplete Expired'),
    ])
    trial_end = models.DateTimeField(null=True, blank=True)
    stripe_customer_id = models.CharField(max_length=255, null=True, blank=True)
    stripe_subscription_id = models.CharField(max_length=255, null=True, blank=True)
    cancel_at_period_end = models.BooleanField(
        default=False,
        help_text="If true, subscription will be canceled at the end of current period"
    )
    canceled_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Timestamp when subscription was canceled"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        plan_name = self.token_plan.name if self.token_plan else (self.full_plan.name if self.full_plan else 'No Plan')
        return f"{self.user.email} - {plan_name} ({self.tokens_remaining} tokens left)"

    def save(self, *args, **kwargs):
        # Token-only plans do not imply a duration; end_date should be explicitly set if needed
        super().save(*args, **kwargs)

    def is_subscription_active(self):
        """
        Check if subscription is truly active based on all conditions.
        
        IMPORTANT: This method ONLY checks status - it does NOT enforce deactivation.
        Use deactivate_subscription() method to explicitly deactivate with proper logging.
        """
        is_active = True
        if not self.is_active:
            is_active = False
        if self.tokens_remaining is None or self.tokens_remaining <= 0:
            is_active = False
        if self.end_date and timezone.now() > self.end_date:
            is_active = False

        # REMOVED: Automatic enforcement of deactivation side-effects
        # This was causing unexpected chat conversions to manual mode
        # Use deactivate_subscription() method for controlled deactivation
        return is_active
    
    def deactivate_subscription(self, reason='unspecified', skip_enforcement=False):
        """
        Explicitly deactivate subscription with proper logging and enforcement.
        
        Args:
            reason: Why the subscription is being deactivated (for logging)
            skip_enforcement: If True, only mark inactive without enforcing workflow/chat changes
        
        Returns:
            bool: True if deactivation was performed
        """
        import logging
        logger = logging.getLogger(__name__)
        
        if not self.is_active:
            logger.info(f"Subscription {self.id} for user {self.user.username} already inactive")
            return False
        
        logger.warning(
            f"Deactivating subscription {self.id} for user {self.user.username}. "
            f"Reason: {reason}. Tokens remaining: {self.tokens_remaining}, "
            f"End date: {self.end_date}"
        )
        
        self.is_active = False
        self.save(update_fields=['is_active', 'updated_at'])
        
        if not skip_enforcement:
            try:
                enforce_account_deactivation_for_user(self.user)
                logger.info(f"Enforced account deactivation for user {self.user.username}")
            except Exception as e:
                logger.error(f"Error enforcing deactivation for user {self.user.username}: {e}")
        
        return True

    def days_remaining(self):
        """
        Calculate days remaining in subscription
        Returns 0 if expired, None if unlimited
        """
        if not self.end_date:
            return None  # Unlimited
        days_left = days_left_from_now(self.end_date)
        return max(0, days_left)  # Return 0 if negative (expired)

    class Meta:
        ordering = ['-created_at']


class Payment(models.Model):
    """
    Payment records for subscription purchases
    """
    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
        ('cancelled', 'Cancelled'),
    ]

    PAYMENT_METHOD_CHOICES = [
        ('credit_card', 'Credit Card'),
        ('paypal', 'PayPal'),
        ('stripe', 'Stripe'),
        ('bank_transfer', 'Bank Transfer'),
        ('other', 'Other'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='payments')
    subscription = models.ForeignKey(Subscription, on_delete=models.CASCADE, null=True, blank=True, related_name='payments')
    token_plan = models.ForeignKey(TokenPlan, on_delete=models.CASCADE, null=True, blank=True)
    full_plan = models.ForeignKey(FullPlan, on_delete=models.CASCADE, null=True, blank=True)
    amount = models.IntegerField(default=0, help_text="Amount in Toman")
    payment_date = models.DateTimeField(default=timezone.now)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, default='credit_card')
    status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')
    transaction_id = models.CharField(max_length=255, null=True, blank=True)
    payment_gateway_response = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Legacy fields for backward compatibility
    ref_id = models.CharField(max_length=256, null=True, blank=True)
    authority = models.CharField(max_length=256, null=True, blank=True)

    def __str__(self):
        return f"{self.user.email} - ${self.amount} ({self.status})"

    class Meta:
        ordering = ['-created_at']


class TokenUsage(models.Model):
    """
    Track token consumption for analytics and billing
    """
    subscription = models.ForeignKey(Subscription, on_delete=models.CASCADE, related_name='token_usages')
    used_tokens = models.IntegerField()
    usage_date = models.DateTimeField(default=timezone.now)
    description = models.CharField(max_length=255, null=True, blank=True, help_text="Description of what the tokens were used for")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.subscription.user.email} - {self.used_tokens} tokens on {self.usage_date.date()}"

    class Meta:
        ordering = ['-usage_date']


# Legacy model for backward compatibility - can be removed if not used
class Purchases(models.Model):
    name = models.CharField(max_length=1000, null=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    price = models.IntegerField()
    created_at = models.DateField(auto_now_add=True)
    paid = models.BooleanField(default=False)
    description = models.CharField(max_length=256, null=True, blank=True)
    ref_id = models.CharField(max_length=256, null=True, blank=True)
    authority = models.CharField(max_length=256, null=True, blank=True)

    def __str__(self):
        return str(self.user) +'-'+ str(self.price)

    class Meta:
        verbose_name_plural = "Legacy Purchases"


class WalletTransaction(models.Model):
    """
    Track wallet transactions for affiliate commissions and other wallet operations
    """
    TRANSACTION_TYPE_CHOICES = [
        ('commission', 'Affiliate Commission'),
        ('payment', 'Payment'),
        ('refund', 'Refund'),
        ('withdrawal', 'Withdrawal'),
        ('adjustment', 'Manual Adjustment'),
    ]
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='wallet_transactions',
        help_text="User whose wallet is affected"
    )
    transaction_type = models.CharField(
        max_length=20,
        choices=TRANSACTION_TYPE_CHOICES,
        default='commission'
    )
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Transaction amount (positive for credit, negative for debit)"
    )
    balance_after = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Wallet balance after this transaction"
    )
    description = models.TextField(
        help_text="Description of the transaction"
    )
    
    # Reference fields for traceability
    related_payment = models.ForeignKey(
        Payment,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='wallet_transactions',
        help_text="Related payment if this is a commission"
    )
    referred_user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='generated_commissions',
        help_text="User who made the payment that generated this commission"
    )
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_wallet_transactions',
        help_text="Admin user who created manual adjustments"
    )
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "💰 Wallet Transaction"
        verbose_name_plural = "💰 Wallet Transactions"
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['related_payment']),
        ]
    
    def __str__(self):
        return f"{self.user.email} - {self.get_transaction_type_display()} - {self.amount}"