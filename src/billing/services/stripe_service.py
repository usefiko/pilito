"""
Stripe Service Layer
Handles all Stripe API interactions
"""
import logging
import stripe
from decimal import Decimal
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from typing import Optional, Dict, Any, Tuple

from billing.models import TokenPlan, FullPlan, Subscription, Payment

logger = logging.getLogger(__name__)

# Initialize Stripe with settings from Django conf
if hasattr(settings, 'STRIPE_SECRET_KEY') and settings.STRIPE_SECRET_KEY:
    stripe.api_key = settings.STRIPE_SECRET_KEY
    stripe.api_version = getattr(settings, 'STRIPE_API_VERSION', '2023-10-16')


class StripeService:
    """Service class for Stripe operations"""
    
    @staticmethod
    def _update_subscription_professional(
        subscription: Subscription,
        selected_token_plan: Optional[TokenPlan],
        selected_full_plan: Optional[FullPlan],
        tokens_included: int,
        stripe_customer_id: str,
        stripe_subscription_id: Optional[str]
    ) -> Subscription:
        """
        Professional subscription update logic following Fiko business rules:
        
        1. Token Plans: Always add tokens (no expiration - tokens never burn)
        2. Full Plans (Same Plan): Extend end_date (renewal - tokens accumulate)
        3. Full Plans (Different Plan - Active): 
           - New subscription starts from END of old period (keeps paid days)
           - Old Full Plan tokens are BURNED
           - Token Plan tokens are preserved (they don't expire)
        4. Full Plans (Different Plan - Expired/First): 
           - New subscription starts now
           - Tokens accumulate (preserves Token Plan tokens)
        
        Args:
            subscription: Existing subscription object
            selected_token_plan: Token plan if purchased (or None)
            selected_full_plan: Full plan if purchased (or None)
            tokens_included: Number of tokens to add
            stripe_customer_id: Stripe customer ID
            stripe_subscription_id: Stripe subscription ID (for recurring plans)
            
        Returns:
            Updated subscription object
        """
        now = timezone.now()
        
        # Update Stripe IDs
        subscription.stripe_customer_id = stripe_customer_id
        subscription.is_active = True
        
        # ===== CASE 1: Token Plan Purchase (One-time purchase) =====
        if selected_token_plan:
            subscription.token_plan = selected_token_plan
            subscription.tokens_remaining += tokens_included
            # Token plans don't have end_date unless explicitly set
            logger.info(
                f"✅ Added {tokens_included} tokens to user {subscription.user.id}. "
                f"Total: {subscription.tokens_remaining} tokens"
            )
        
        # ===== CASE 2: Full Plan Purchase (Subscription with duration) =====
        elif selected_full_plan:
            old_plan = subscription.full_plan
            
            # ===== CASE 2A: Same plan renewal (extend end_date) =====
            if old_plan and old_plan.id == selected_full_plan.id:
                # Extend existing subscription
                if subscription.end_date and subscription.end_date > now:
                    # Active subscription: extend from current end_date
                    subscription.end_date += timedelta(days=selected_full_plan.duration_days)
                    logger.info(
                        f"✅ Extended subscription for user {subscription.user.id}. "
                        f"New end date: {subscription.end_date.date()}"
                    )
                else:
                    # Expired subscription: start fresh from now
                    subscription.start_date = now
                    subscription.end_date = now + timedelta(days=selected_full_plan.duration_days)
                    logger.info(
                        f"✅ Renewed expired subscription for user {subscription.user.id}. "
                        f"End date: {subscription.end_date.date()}"
                    )
                
                # Add tokens
                subscription.tokens_remaining += tokens_included
            
            # ===== CASE 2B: Different plan (upgrade/downgrade) =====
            else:
                old_tokens = subscription.tokens_remaining
                
                # INDUSTRY STANDARD POLICY:
                # UPGRADE (higher price): Immediate switch + Accumulate tokens + Cancel old Stripe sub
                # DOWNGRADE (lower price): Scheduled switch + Queue plan + Cancel at period end
                # Token Plan tokens: NEVER burned (they have no expiration)
                
                if old_plan and subscription.end_date and subscription.end_date > now:
                    # ===== ACTIVE SUBSCRIPTION - DETECT UPGRADE OR DOWNGRADE =====
                    days_remaining = (subscription.end_date - now).days
                    
                    # Detect upgrade vs downgrade based on price
                    # Use price_en as reference (can also check other currencies)
                    old_price = float(old_plan.price_en) if hasattr(old_plan, 'price_en') else 0
                    new_price = float(selected_full_plan.price_en) if hasattr(selected_full_plan, 'price_en') else 0
                    
                    is_upgrade = new_price > old_price
                    is_downgrade = new_price < old_price
                    
                    if is_upgrade:
                        # ===== UPGRADE: IMMEDIATE SWITCH =====
                        logger.info(
                            f"⬆️ UPGRADE detected: User {subscription.user.id} upgrading from {old_plan.name} (${old_price}) "
                            f"to {selected_full_plan.name} (${new_price}). Applying immediate upgrade with token accumulation."
                        )
                        
                        # 1. Cancel old Stripe subscription (with prorated credit)
                        if subscription.stripe_subscription_id:
                            try:
                                stripe.Subscription.delete(
                                    subscription.stripe_subscription_id,
                                    prorate=True
                                )
                                logger.info(f"✅ Cancelled old Stripe subscription {subscription.stripe_subscription_id} with prorated credit")
                            except Exception as stripe_error:
                                logger.error(f"⚠️ Failed to cancel old Stripe subscription: {stripe_error}")
                        
                        # 2. Update to new plan immediately
                        subscription.full_plan = selected_full_plan
                        subscription.start_date = now
                        subscription.end_date = now + timedelta(days=selected_full_plan.duration_days)
                        
                        # 3. ACCUMULATE tokens (old + new)
                        subscription.tokens_remaining += tokens_included
                        
                        logger.info(
                            f"✅ Upgrade completed immediately. "
                            f"New plan: {selected_full_plan.name}, "
                            f"End date: {subscription.end_date.date()}, "
                            f"Tokens: {old_tokens} + {tokens_included} = {subscription.tokens_remaining}"
                        )
                    
                    elif is_downgrade:
                        # ===== DOWNGRADE: SCHEDULED SWITCH =====
                        logger.info(
                            f"⬇️ DOWNGRADE detected: User {subscription.user.id} downgrading from {old_plan.name} (${old_price}) "
                            f"to {selected_full_plan.name} (${new_price}). Scheduling downgrade at period end."
                        )
                        
                        # 1. Schedule Stripe cancellation at period end
                        if subscription.stripe_subscription_id:
                            try:
                                stripe.Subscription.modify(
                                    subscription.stripe_subscription_id,
                                    cancel_at_period_end=True
                                )
                                logger.info(f"✅ Scheduled Stripe subscription cancellation at period end")
                            except Exception as stripe_error:
                                logger.error(f"⚠️ Failed to schedule Stripe cancellation: {stripe_error}")
                        
                        # 2. Queue the new plan (will activate at end_date)
                        subscription.queued_full_plan = selected_full_plan
                        subscription.queued_tokens_amount = tokens_included
                        # DO NOT change current plan, start_date, end_date, or tokens_remaining
                        # Keep current subscription active until end_date
                        
                        logger.info(
                            f"✅ Downgrade queued successfully. "
                            f"Current plan ({old_plan.name}) remains active until: {subscription.end_date.date()}. "
                            f"New plan ({selected_full_plan.name}) will activate with {tokens_included} tokens on: {subscription.end_date.date()}. "
                            f"Current tokens ({old_tokens}) remain usable until then. "
                            f"Remaining days: {days_remaining}"
                        )
                    
                    else:
                        # Same price (edge case - treat as upgrade)
                        logger.warning(
                            f"⚠️ Same price plan change: {old_plan.name} → {selected_full_plan.name}. "
                            f"Treating as immediate switch."
                        )
                        subscription.full_plan = selected_full_plan
                        subscription.start_date = now
                        subscription.end_date = now + timedelta(days=selected_full_plan.duration_days)
                        subscription.tokens_remaining += tokens_included
                else:
                    # ===== EXPIRED OR FIRST PURCHASE - ADD TOKENS =====
                    # Note: Token Plan tokens are preserved (they don't expire)
                    # Only Full Plan tokens are replaced for fresh/expired subscriptions
                    
                    logger.info(
                        f"🆕 User {subscription.user.id} starting {selected_full_plan.name}. "
                        f"Current tokens: {old_tokens} (may include Token Plan tokens which will be preserved)"
                    )
                    
                    subscription.full_plan = selected_full_plan
                    subscription.start_date = now
                    subscription.end_date = now + timedelta(days=selected_full_plan.duration_days)
                    subscription.tokens_remaining += tokens_included  # ✅ ADD tokens (preserves Token Plan tokens)
                    
                    logger.info(
                        f"✅ New subscription started. "
                        f"Ends: {subscription.end_date.date()}. "
                        f"Tokens: {old_tokens} + {tokens_included} = {subscription.tokens_remaining}"
                    )
            
            # Update Stripe subscription ID for recurring plans
            if stripe_subscription_id:
                subscription.stripe_subscription_id = stripe_subscription_id
        
        subscription.save()
        return subscription
    
    @staticmethod
    def get_or_create_customer(user) -> Optional[str]:
        """
        Get or create a Stripe customer for a user
        
        Args:
            user: Django User instance
            
        Returns:
            str: Stripe customer ID
        """
        try:
            # Check if user already has a Stripe customer ID
            subscription = getattr(user, 'subscription', None)
            if subscription and subscription.stripe_customer_id:
                # Verify customer still exists in Stripe
                try:
                    stripe.Customer.retrieve(subscription.stripe_customer_id)
                    return subscription.stripe_customer_id
                except stripe.InvalidRequestError:
                    logger.warning(f"Stripe customer {subscription.stripe_customer_id} not found, creating new one")
            
            # Create new Stripe customer
            customer = stripe.Customer.create(
                email=user.email,
                name=user.get_full_name() or user.username,
                metadata={
                    'user_id': str(user.id),
                    'username': user.username,
                }
            )
            
            # Store customer ID in subscription
            subscription, _ = Subscription.objects.get_or_create(
                user=user,
                defaults={
                    'tokens_remaining': 0,
                    'is_active': False
                }
            )
            subscription.stripe_customer_id = customer.id
            subscription.save(update_fields=['stripe_customer_id'])
            
            logger.info(f"Created Stripe customer {customer.id} for user {user.username}")
            return customer.id
            
        except Exception as e:
            logger.error(f"Error creating Stripe customer for user {user.username}: {e}")
            return None
    
    @staticmethod
    def create_checkout_session(
        user,
        plan_type: str,  # 'token' or 'full'
        plan_id: int,
        success_url: Optional[str] = None,
        cancel_url: Optional[str] = None
    ) -> Tuple[Optional[str], Optional[str]]:
        """
        Create a Stripe Checkout Session for a plan purchase
        
        Args:
            user: Django User instance
            plan_type: 'token' or 'full'
            plan_id: ID of the plan
            success_url: URL to redirect after successful payment
            cancel_url: URL to redirect if payment is cancelled
            
        Returns:
            Tuple[session_id, checkout_url]
        """
        try:
            # Get or create Stripe customer
            customer_id = StripeService.get_or_create_customer(user)
            if not customer_id:
                return None, "Failed to create Stripe customer"
            
            # Get plan details
            if plan_type == 'token':
                plan = TokenPlan.objects.get(id=plan_id, is_active=True)
                is_recurring = plan.is_recurring
            elif plan_type == 'full':
                plan = FullPlan.objects.get(id=plan_id, is_active=True)
                is_recurring = True  # Full plans are always recurring
            else:
                return None, "Invalid plan type"
            
            # Validate: prevent purchasing same active plan
            if plan_type == 'full':
                try:
                    existing_sub = Subscription.objects.get(user=user, is_active=True)
                    
                    # If user has same active plan, prevent purchase
                    if existing_sub.full_plan and existing_sub.full_plan.id == plan.id:
                        # Check if subscription is not scheduled for cancellation
                        if not existing_sub.cancel_at_period_end:
                            return None, "You already have this plan active. To change plans, please cancel your current subscription first."
                    
                    # If user has different plan, that's OK (upgrade/downgrade)
                    
                except Subscription.DoesNotExist:
                    pass  # No existing subscription, OK to proceed
            
            # Determine currency based on user preference or default
            # You can customize this based on user's country/language
            price_field = 'price_en'  # Default to English pricing
            currency = getattr(settings, 'STRIPE_CURRENCY', 'usd')
            
            amount = getattr(plan, price_field)
            
            # Create or get Stripe price
            if is_recurring and plan_type == 'full':
                # Create recurring subscription
                mode = 'subscription'
                interval = 'year' if plan.is_yearly else 'month'
                
                # Check if plan already has a Stripe price ID
                if hasattr(plan, 'stripe_price_id') and plan.stripe_price_id:
                    # Use existing Stripe price
                    logger.info(f"Using existing Stripe price {plan.stripe_price_id} for plan {plan.id}")
                    line_items = [{
                        'price': plan.stripe_price_id,
                        'quantity': 1,
                    }]
                else:
                    # Create new Stripe product and price
                    logger.info(f"Creating new Stripe price for plan {plan.id}")
                    product = stripe.Product.create(
                        name=plan.name,
                        description=plan.description or f"{plan.tokens_included} tokens",
                        metadata={
                            'plan_type': plan_type,
                            'plan_id': str(plan.id),
                            'tokens_included': str(plan.tokens_included),
                        }
                    )
                    
                    price = stripe.Price.create(
                        product=product.id,
                        unit_amount=int(amount * 100),  # Convert to cents
                        currency=currency,
                        recurring={
                            'interval': interval,
                            'interval_count': 1
                        },
                        metadata={
                            'plan_type': plan_type,
                            'plan_id': str(plan.id),
                        }
                    )
                    
                    # Store Stripe IDs in plan
                    plan.stripe_product_id = product.id
                    plan.stripe_price_id = price.id
                    plan.save(update_fields=['stripe_product_id', 'stripe_price_id'])
                    logger.info(f"Stored Stripe IDs for plan {plan.id}: product={product.id}, price={price.id}")
                    
                    line_items = [{
                        'price': price.id,
                        'quantity': 1,
                    }]
            else:
                # One-time payment (token plans)
                mode = 'payment'
                
                # Check if token plan has a Stripe price ID
                if hasattr(plan, 'stripe_price_id') and plan.stripe_price_id:
                    # Use existing Stripe price
                    line_items = [{
                        'price': plan.stripe_price_id,
                        'quantity': 1,
                    }]
                else:
                    # Create price dynamically
                    line_items = [{
                        'price_data': {
                            'currency': currency,
                            'product_data': {
                                'name': plan.name,
                                'description': f"{plan.tokens_included} tokens",
                                'metadata': {
                                    'plan_type': plan_type,
                                    'plan_id': str(plan.id),
                                }
                            },
                            'unit_amount': int(amount * 100),  # Convert to cents
                        },
                        'quantity': 1,
                    }]
            
            # Set URLs with payment details
            if not success_url:
                # Build success URL with payment details
                # Note: Stripe replaces {CHECKOUT_SESSION_ID} automatically
                success_url = (
                    f"http://app.fiko.net/dashboard/payment/success?"
                    f"status=success&"
                    f"transaction_id={{CHECKOUT_SESSION_ID}}&"
                    f"amount={amount}&"
                    f"plan_name={plan.name}"
                )
            
            if not cancel_url:
                # Build cancel/failure URL
                cancel_url = (
                    f"http://app.fiko.net/dashboard/payment/failure?"
                    f"status=cancelled&"
                    f"error_code=USER_CANCELLED&"
                    f"error_message=Payment was cancelled by user"
                )
            
            # Create checkout session
            session = stripe.checkout.Session.create(
                customer=customer_id,
                payment_method_types=['card'],
                line_items=line_items,
                mode=mode,
                success_url=success_url,
                cancel_url=cancel_url,
                metadata={
                    'user_id': str(user.id),
                    'plan_type': plan_type,
                    'plan_id': str(plan.id),
                    'tokens_included': str(plan.tokens_included),
                },
                allow_promotion_codes=True,
            )
            
            # Create pending payment record
            Payment.objects.create(
                user=user,
                token_plan=plan if plan_type == 'token' else None,
                full_plan=plan if plan_type == 'full' else None,
                amount=amount,
                payment_method='stripe',
                status='pending',
                transaction_id=session.id,
                payment_gateway_response={'session_id': session.id}
            )
            
            logger.info(f"Created Stripe checkout session {session.id} for user {user.username}")
            return session.id, session.url
            
        except TokenPlan.DoesNotExist:
            return None, "Token plan not found"
        except FullPlan.DoesNotExist:
            return None, "Full plan not found"
        except Exception as e:
            logger.error(f"Error creating Stripe checkout session: {e}")
            return None, str(e)
    
    @staticmethod
    def create_customer_portal_session(
        user,
        return_url: Optional[str] = None
    ) -> Optional[str]:
        """
        Create a Stripe Customer Portal session for subscription management
        
        Args:
            user: Django User instance
            return_url: URL to return to after portal session
            
        Returns:
            str: Portal session URL
        """
        try:
            customer_id = StripeService.get_or_create_customer(user)
            if not customer_id:
                return None
            
            return_url = return_url or getattr(settings, 'STRIPE_PORTAL_RETURN_URL', 'https://app.fiko.net/dashboard/profile#billing')
            
            portal_session = stripe.billing_portal.Session.create(
                customer=customer_id,
                return_url=return_url,
            )
            
            logger.info(f"Created Stripe portal session for user {user.username}")
            return portal_session.url
            
        except Exception as e:
            logger.error(f"Error creating Stripe portal session: {e}")
            return None
    
    @staticmethod
    def handle_successful_payment(session_id: str) -> bool:
        """
        Handle successful payment from Stripe
        
        Args:
            session_id: Stripe checkout session ID
            
        Returns:
            bool: Success status
        """
        try:
            # Retrieve session from Stripe
            session = stripe.checkout.Session.retrieve(
                session_id,
                expand=['line_items', 'subscription']
            )
            
            # Get metadata
            user_id = session.metadata.get('user_id')
            plan_type = session.metadata.get('plan_type')
            plan_id = session.metadata.get('plan_id')
            tokens_included = int(session.metadata.get('tokens_included', 0))
            
            if not all([user_id, plan_type, plan_id]):
                logger.error(f"Missing metadata in session {session_id}")
                return False
            
            # Get user
            from django.contrib.auth import get_user_model
            User = get_user_model()
            user = User.objects.get(id=user_id)
            
            # Get plan
            if plan_type == 'token':
                plan = TokenPlan.objects.get(id=plan_id)
                selected_token_plan = plan
                selected_full_plan = None
            else:
                plan = FullPlan.objects.get(id=plan_id)
                selected_token_plan = None
                selected_full_plan = plan
            
            # Update payment record
            payment = Payment.objects.filter(
                transaction_id=session_id,
                user=user
            ).first()
            
            if payment:
                payment.status = 'completed'
                payment.payment_gateway_response = {
                    'session_id': session_id,
                    'payment_intent': session.payment_intent,
                    'customer': session.customer,
                    'subscription': session.subscription.id if (hasattr(session, 'subscription') and session.subscription) else None
                }
                payment.save()
            
            # Create or update subscription
            subscription, created = Subscription.objects.get_or_create(
                user=user,
                defaults={
                    'token_plan': selected_token_plan,
                    'full_plan': selected_full_plan,
                    'tokens_remaining': tokens_included,
                    'start_date': timezone.now(),
                    'is_active': True,
                    'stripe_customer_id': session.customer,
                    'stripe_subscription_id': session.subscription.id if (hasattr(session, 'subscription') and session.subscription) else None
                }
            )
            
            if not created:
                # Update existing subscription using professional logic
                subscription = StripeService._update_subscription_professional(
                    subscription=subscription,
                    selected_token_plan=selected_token_plan,
                    selected_full_plan=selected_full_plan,
                    tokens_included=tokens_included,
                    stripe_customer_id=session.customer,
                    stripe_subscription_id=session.subscription.id if (hasattr(session, 'subscription') and session.subscription) else None
                )
            
            # Link payment to subscription
            if payment:
                payment.subscription = subscription
                payment.save()
            
            logger.info(f"Successfully processed payment {session_id} for user {user.username}")
            return True
            
        except Exception as e:
            logger.error(f"Error handling successful payment for session {session_id}: {e}")
            return False
    
    @staticmethod
    def cancel_subscription(user) -> Tuple[bool, str]:
        """
        Cancel user's Stripe subscription
        
        Args:
            user: Django User instance
            
        Returns:
            Tuple[success, message]
        """
        try:
            subscription = user.subscription
            if not subscription.stripe_subscription_id:
                return False, "No Stripe subscription found"
            
            # Cancel subscription in Stripe
            stripe.Subscription.modify(
                subscription.stripe_subscription_id,
                cancel_at_period_end=True
            )
            
            logger.info(f"Cancelled Stripe subscription {subscription.stripe_subscription_id} for user {user.username}")
            return True, "Subscription will be cancelled at the end of the billing period"
            
        except Exception as e:
            logger.error(f"Error cancelling subscription: {e}")
            return False, str(e)

