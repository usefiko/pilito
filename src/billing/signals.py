"""
Signals for billing app
Handles affiliate commission payouts when payments are completed

Multi-Level Affiliate System:
- Level 1 (Direct): When a referred user makes a payment, their referrer earns commission
- Level 2 (Upline): When a referrer earns commission, their referrer (upline) earns a percentage of that commission

Each user can have custom commission rules via UserAffiliateRule model.
Falls back to global AffiliationConfig if no custom rule exists.
"""
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import transaction
from decimal import Decimal
import logging

from billing.models import Payment, WalletTransaction, UserAffiliateRule
from settings.models import AffiliationConfig

logger = logging.getLogger(__name__)


def get_affiliate_settings(user):
    """
    Get affiliate settings for a user.
    Returns custom UserAffiliateRule if exists, otherwise falls back to global config.
    
    Returns tuple: (direct_percentage, direct_validity_days, upline_percentage, upline_validity_days, is_custom_rule)
    """
    # Try to get custom rule first
    custom_rule = UserAffiliateRule.get_user_rule(user)
    
    if custom_rule:
        return (
            custom_rule.direct_commission_percentage,
            custom_rule.direct_validity_days,
            custom_rule.upline_commission_percentage,
            custom_rule.upline_validity_days,
            True,
            custom_rule
        )
    
    # Fall back to global config
    try:
        global_config = AffiliationConfig.get_config()
        return (
            global_config.percentage,
            global_config.commission_validity_days,
            Decimal('0.00'),  # No upline commission in global config
            0,
            False,
            global_config
        )
    except Exception:
        return None


def is_within_validity_period(registration_date, payment_date, validity_days):
    """Check if payment is within validity period"""
    from django.utils import timezone
    from datetime import timedelta
    
    if validity_days == 0:
        return True  # Unlimited
    
    if payment_date is None:
        payment_date = timezone.now()
    
    if timezone.is_naive(registration_date):
        registration_date = timezone.make_aware(registration_date)
    if timezone.is_naive(payment_date):
        payment_date = timezone.make_aware(payment_date)
    
    validity_deadline = registration_date + timedelta(days=validity_days)
    return payment_date <= validity_deadline


def process_upline_commission(direct_commission_transaction, referrer):
    """
    Process upline commission (Level 2) when a referrer earns direct commission.
    
    Args:
        direct_commission_transaction: The WalletTransaction for the direct commission
        referrer: The user who earned the direct commission
    
    Returns:
        WalletTransaction or None
    """
    # Check if referrer has an upline (was referred by someone)
    if not referrer.referred_by:
        logger.debug(f"Referrer {referrer.email} has no upline, skipping upline commission")
        return None
    
    upline = referrer.referred_by
    
    # Check if upline has affiliate active
    if not upline.affiliate_active:
        logger.debug(f"Upline {upline.email} has affiliate disabled, skipping upline commission")
        return None
    
    # Get upline's affiliate settings
    settings = get_affiliate_settings(upline)
    if not settings:
        logger.debug(f"No affiliate settings found for upline {upline.email}")
        return None
    
    (direct_pct, direct_days, upline_pct, upline_days, is_custom, config) = settings
    
    # Check if upline commission is enabled (percentage > 0)
    if upline_pct <= 0:
        logger.debug(f"Upline {upline.email} has no upline commission percentage configured")
        return None
    
    # Check if within upline validity period (from when referrer joined)
    if not is_within_validity_period(referrer.date_joined, None, upline_days):
        logger.debug(f"Upline commission for {upline.email} is outside validity period")
        return None
    
    # Check for idempotency - don't pay twice for the same source commission
    if WalletTransaction.objects.filter(
        source_commission=direct_commission_transaction,
        transaction_type='upline_commission'
    ).exists():
        logger.debug(f"Upline commission already paid for transaction {direct_commission_transaction.id}")
        return None
    
    # Calculate upline commission
    upline_commission_amount = (
        direct_commission_transaction.amount * upline_pct / Decimal('100')
    ).quantize(Decimal('0.01'))
    
    if upline_commission_amount <= 0:
        logger.debug(f"Upline commission amount is zero or negative")
        return None
    
    # Update upline's wallet balance
    upline.wallet_balance += upline_commission_amount
    upline.save(update_fields=['wallet_balance', 'updated_at'])
    
    # Create upline commission transaction
    upline_transaction = WalletTransaction.objects.create(
        user=upline,
        transaction_type='upline_commission',
        amount=upline_commission_amount,
        balance_after=upline.wallet_balance,
        description=(
            f"Upline commission ({upline_pct}%) from {referrer.email}'s affiliate earning of {direct_commission_transaction.amount}"
        ),
        commission_level=2,
        commission_percentage=upline_pct,
        source_amount=direct_commission_transaction.amount,
        related_payment=direct_commission_transaction.related_payment,
        referred_user=referrer,  # The referrer whose commission triggered this
        source_commission=direct_commission_transaction
    )
    
    logger.info(
        f"Upline commission paid: {upline.email} earned {upline_commission_amount} "
        f"({upline_pct}% of {direct_commission_transaction.amount}) from {referrer.email}'s commission"
    )
    
    return upline_transaction


@receiver(post_save, sender=Payment)
def process_affiliate_commission(sender, instance, created, **kwargs):
    """
    Process affiliate commission when a payment is completed.
    
    This signal:
    1. Checks if payment is newly completed
    2. Verifies user has a referrer with affiliate active
    3. Gets referrer's custom affiliate rule (or global config as fallback)
    4. Calculates direct commission based on referrer's settings
    5. Adds commission to referrer's wallet
    6. Creates wallet transaction record
    7. Processes upline commission if applicable (multi-level)
    8. Is idempotent (won't pay twice for same payment)
    
    Args:
        instance: Payment object that was saved
        created: Boolean indicating if this is a new payment
    """
    # Only process completed payments
    if instance.status != 'completed':
        return
    
    # Check if direct commission already paid (idempotent check)
    if WalletTransaction.objects.filter(
        related_payment=instance,
        transaction_type='commission',
        commission_level=1
    ).exists():
        logger.debug(f"Direct commission already paid for payment {instance.id}")
        return  # Already paid, don't pay again
    
    # Get the user who made the payment
    paying_user = instance.user
    
    # Check if user was referred by someone
    if not paying_user.referred_by:
        logger.debug(f"User {paying_user.email} has no referrer, skipping commission")
        return  # No referrer, nothing to do
    
    referrer = paying_user.referred_by
    
    # Check if referrer has affiliate system active
    if not referrer.affiliate_active:
        logger.debug(f"Referrer {referrer.email} has affiliate disabled, skipping commission")
        return  # Referrer doesn't have affiliate enabled
    
    # Get affiliate settings for the referrer
    settings = get_affiliate_settings(referrer)
    if not settings:
        logger.debug(f"No affiliate settings found, skipping commission")
        return
    
    (direct_pct, direct_days, upline_pct, upline_days, is_custom, config) = settings
    
    # Check if affiliate system is globally active (only if using global config)
    if not is_custom:
        try:
            global_config = AffiliationConfig.get_config()
            if not global_config.is_active:
                logger.debug("Global affiliate system is disabled")
                return
        except Exception:
            return
    
    # Check if payment is within the commission validity period
    payment_date = instance.payment_date if hasattr(instance, 'payment_date') and instance.payment_date else None
    if not is_within_validity_period(paying_user.date_joined, payment_date, direct_days):
        logger.debug(
            f"Payment for {paying_user.email} is outside validity period "
            f"({direct_days} days from registration)"
        )
        return  # Payment is outside the validity period
    
    # Calculate direct commission
    commission_amount = (
        Decimal(str(instance.amount)) * direct_pct / Decimal('100')
    ).quantize(Decimal('0.01'))
    
    if commission_amount <= 0:
        logger.debug("Commission amount is zero or negative")
        return
    
    # Use atomic transaction to ensure consistency
    with transaction.atomic():
        # Update referrer's wallet balance
        referrer.wallet_balance += commission_amount
        referrer.save(update_fields=['wallet_balance', 'updated_at'])
        
        # Create wallet transaction record for direct commission
        direct_transaction = WalletTransaction.objects.create(
            user=referrer,
            transaction_type='commission',
            amount=commission_amount,
            balance_after=referrer.wallet_balance,
            description=(
                f"Affiliate commission ({direct_pct}%) from {paying_user.email}'s payment of {instance.amount}"
            ),
            commission_level=1,
            commission_percentage=direct_pct,
            source_amount=Decimal(str(instance.amount)),
            related_payment=instance,
            referred_user=paying_user
        )
        
        rule_type = "custom rule" if is_custom else "global config"
        logger.info(
            f"Direct commission paid: {referrer.email} earned {commission_amount} "
            f"({direct_pct}% of {instance.amount}) from {paying_user.email}'s payment "
            f"using {rule_type}"
        )
        
        # Process upline commission (Level 2) if applicable
        upline_transaction = process_upline_commission(direct_transaction, referrer)
        
        if upline_transaction:
            logger.info(
                f"Multi-level commission chain: Payment → {referrer.email} (L1) → "
                f"{referrer.referred_by.email} (L2)"
            )
