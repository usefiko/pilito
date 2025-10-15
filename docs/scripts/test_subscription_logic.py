"""
Test script for Professional Subscription Logic
Run this in Django shell to verify the new subscription logic

Usage:
    python manage.py shell < test_subscription_logic.py
"""

from django.utils import timezone
from datetime import timedelta
from billing.models import Subscription, TokenPlan, FullPlan
from billing.services.stripe_service import StripeService
from accounts.models import User

print("=" * 80)
print("🧪 TESTING PROFESSIONAL SUBSCRIPTION LOGIC")
print("=" * 80)

# Create or get test user
test_email = "subscription_test@example.com"
user, created = User.objects.get_or_create(
    email=test_email,
    defaults={'username': 'subscription_test'}
)
print(f"\n✅ Test user: {user.email} (ID: {user.id})")

# Clean up existing subscription for clean test
Subscription.objects.filter(user=user).delete()
print("🧹 Cleaned up existing subscriptions")

# Create test plans
token_plan_500, _ = TokenPlan.objects.get_or_create(
    name="500 Tokens",
    defaults={
        'price_en': 10.00,
        'price_tr': 10.00,
        'price_ar': 10.00,
        'tokens_included': 500,
        'is_recurring': False,
        'is_active': True
    }
)

monthly_plan, _ = FullPlan.objects.get_or_create(
    name="Monthly Pro",
    defaults={
        'price_en': 30.00,
        'price_tr': 30.00,
        'price_ar': 30.00,
        'tokens_included': 10000,
        'duration_days': 30,
        'is_yearly': False,
        'is_active': True
    }
)

yearly_plan, _ = FullPlan.objects.get_or_create(
    name="Yearly Pro",
    defaults={
        'price_en': 300.00,
        'price_tr': 300.00,
        'price_ar': 300.00,
        'tokens_included': 150000,
        'duration_days': 365,
        'is_yearly': True,
        'is_active': True
    }
)

print(f"\n✅ Test plans created:")
print(f"   - {token_plan_500.name}: {token_plan_500.tokens_included} tokens")
print(f"   - {monthly_plan.name}: {monthly_plan.tokens_included} tokens, {monthly_plan.duration_days} days")
print(f"   - {yearly_plan.name}: {yearly_plan.tokens_included} tokens, {yearly_plan.duration_days} days")

print("\n" + "=" * 80)
print("TEST 1: Token Plan Purchase (Should accumulate)")
print("=" * 80)

# Create initial subscription with tokens
subscription = Subscription.objects.create(
    user=user,
    token_plan=token_plan_500,
    tokens_remaining=1000,
    is_active=True
)
print(f"Initial state: {subscription.tokens_remaining} tokens")

# Buy more tokens
subscription = StripeService._update_subscription_professional(
    subscription=subscription,
    selected_token_plan=token_plan_500,
    selected_full_plan=None,
    tokens_included=500,
    stripe_customer_id="cus_test_123",
    stripe_subscription_id=None
)
print(f"✅ After buying 500 tokens: {subscription.tokens_remaining} tokens")
assert subscription.tokens_remaining == 1500, "Tokens should accumulate to 1500"

print("\n" + "=" * 80)
print("TEST 2: Same Plan Renewal (Active - Should extend end_date)")
print("=" * 80)

# Reset subscription to monthly plan with 20 days remaining
now = timezone.now()
subscription.full_plan = monthly_plan
subscription.token_plan = None
subscription.start_date = now - timedelta(days=10)
subscription.end_date = now + timedelta(days=20)
subscription.tokens_remaining = 5000
subscription.save()

print(f"Initial state:")
print(f"   Plan: {subscription.full_plan.name}")
print(f"   End date: {subscription.end_date.date()} (20 days remaining)")
print(f"   Tokens: {subscription.tokens_remaining}")

# Renew same plan
old_end_date = subscription.end_date
subscription = StripeService._update_subscription_professional(
    subscription=subscription,
    selected_token_plan=None,
    selected_full_plan=monthly_plan,
    tokens_included=monthly_plan.tokens_included,
    stripe_customer_id="cus_test_123",
    stripe_subscription_id="sub_test_123"
)

days_extended = (subscription.end_date - old_end_date).days
print(f"✅ After renewal:")
print(f"   End date: {subscription.end_date.date()} (extended by {days_extended} days)")
print(f"   Tokens: {subscription.tokens_remaining}")
assert days_extended == 30, f"Should extend by 30 days, got {days_extended}"
assert subscription.tokens_remaining == 5000 + 10000, "Tokens should be 15000"

print("\n" + "=" * 80)
print("TEST 3: Same Plan Renewal (Expired - Should start fresh)")
print("=" * 80)

# Set subscription as expired
subscription.end_date = now - timedelta(days=5)
subscription.tokens_remaining = 100
subscription.save()

print(f"Initial state:")
print(f"   Plan: {subscription.full_plan.name}")
print(f"   End date: {subscription.end_date.date()} (expired 5 days ago)")
print(f"   Tokens: {subscription.tokens_remaining}")

# Renew expired subscription
subscription = StripeService._update_subscription_professional(
    subscription=subscription,
    selected_token_plan=None,
    selected_full_plan=monthly_plan,
    tokens_included=monthly_plan.tokens_included,
    stripe_customer_id="cus_test_123",
    stripe_subscription_id="sub_test_456"
)

days_from_now = (subscription.end_date - now).days
print(f"✅ After renewal:")
print(f"   Start date: {subscription.start_date.date()}")
print(f"   End date: {subscription.end_date.date()} ({days_from_now} days from now)")
print(f"   Tokens: {subscription.tokens_remaining}")
assert days_from_now >= 29 and days_from_now <= 30, f"Should be ~30 days from now, got {days_from_now}"

print("\n" + "=" * 80)
print("TEST 4: Plan Upgrade (Monthly → Yearly with prorated credit)")
print("=" * 80)

# Set subscription to monthly with 20 days remaining
subscription.full_plan = monthly_plan
subscription.start_date = now - timedelta(days=10)
subscription.end_date = now + timedelta(days=20)
subscription.tokens_remaining = 5000
subscription.save()

print(f"Initial state:")
print(f"   Plan: {subscription.full_plan.name}")
print(f"   End date: {subscription.end_date.date()} (20 days remaining)")
print(f"   Tokens: {subscription.tokens_remaining}")

# Calculate expected prorated credit
days_remaining = 20
daily_rate = float(monthly_plan.price_en) / monthly_plan.duration_days
expected_credit = days_remaining * daily_rate
print(f"   Expected prorated credit: ${expected_credit:.2f}")

# Upgrade to yearly
subscription = StripeService._update_subscription_professional(
    subscription=subscription,
    selected_token_plan=None,
    selected_full_plan=yearly_plan,
    tokens_included=yearly_plan.tokens_included,
    stripe_customer_id="cus_test_123",
    stripe_subscription_id="sub_test_789"
)

days_from_now = (subscription.end_date - now).days
print(f"✅ After upgrade:")
print(f"   Plan: {subscription.full_plan.name}")
print(f"   End date: {subscription.end_date.date()} ({days_from_now} days from now)")
print(f"   Tokens: {subscription.tokens_remaining}")
assert subscription.full_plan.id == yearly_plan.id, "Should be yearly plan"
assert days_from_now >= 364 and days_from_now <= 365, f"Should be ~365 days from now, got {days_from_now}"
assert subscription.tokens_remaining == 5000 + 150000, "Tokens should be 155000"
print(f"   💰 Check logs above for prorated credit calculation")

print("\n" + "=" * 80)
print("✅ ALL TESTS PASSED!")
print("=" * 80)

# Clean up
print(f"\n🧹 Cleaning up test data...")
subscription.delete()
# Note: Don't delete test plans as they might be used elsewhere

print(f"✅ Test completed successfully!")
print(f"\n💡 To review logs, check for lines containing:")
print(f"   - 'Added X tokens'")
print(f"   - 'Extended subscription'")
print(f"   - 'Renewed expired subscription'")
print(f"   - 'User switching from'")
print(f"   - 'Prorated credit'")
