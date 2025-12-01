"""
Signals for billing app
Handles affiliate commission payouts when payments are completed
"""
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import transaction
from decimal import Decimal
from billing.models import Payment, WalletTransaction
from settings.models import AffiliationConfig


@receiver(post_save, sender=Payment)
def process_affiliate_commission(sender, instance, created, **kwargs):
    """
    Process affiliate commission when a payment is completed.
    
    This signal:
    1. Checks if payment is newly completed
    2. Verifies user has a referrer with affiliate active
    3. Calculates commission based on AffiliationConfig
    4. Adds commission to referrer's wallet
    5. Creates wallet transaction record
    6. Is idempotent (won't pay twice for same payment)
    
    Args:
        instance: Payment object that was saved
        created: Boolean indicating if this is a new payment
    """
    # Only process completed payments
    if instance.status != 'completed':
        return
    
    # Check if commission already paid (idempotent check)
    if WalletTransaction.objects.filter(
        related_payment=instance,
        transaction_type='commission'
    ).exists():
        return  # Already paid, don't pay again
    
    # Get the user who made the payment
    paying_user = instance.user
    
    # Check if user was referred by someone
    if not paying_user.referred_by:
        return  # No referrer, nothing to do
    
    referrer = paying_user.referred_by
    
    # Check if referrer has affiliate system active
    if not referrer.affiliate_active:
        return  # Referrer doesn't have affiliate enabled
    
    # Get affiliation config
    try:
        affiliation_config = AffiliationConfig.get_config()
    except Exception:
        return  # No config found
    
    # Check if affiliate system is globally active
    if not affiliation_config.is_active:
        return

    # Check if payment is within the commission validity period
    # (Only pay commission for payments made within X days of registration)
    if not affiliation_config.is_within_validity_period(
        user_registration_date=paying_user.date_joined,
        payment_date=instance.payment_date if hasattr(instance, 'payment_date') and instance.payment_date else None
    ):
        return  # Payment is outside the validity period
    
    # Calculate commission
    commission_amount = affiliation_config.calculate_commission(instance.amount)
    
    # Use atomic transaction to ensure consistency
    with transaction.atomic():
        # Update referrer's wallet balance
        referrer.wallet_balance += commission_amount
        referrer.save(update_fields=['wallet_balance', 'updated_at'])
        
        # Create wallet transaction record
        WalletTransaction.objects.create(
            user=referrer,
            transaction_type='commission',
            amount=commission_amount,
            balance_after=referrer.wallet_balance,
            description=f"Affiliate commission ({affiliation_config.percentage}%) from {paying_user.email}'s payment of {instance.amount}",
            related_payment=instance,
            referred_user=paying_user
        )
