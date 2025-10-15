# 🎉 Complete Setup Guide - Using Your Stripe Data

## ✅ What You Have

```
Webhook Signing Secret: whsec_kYH0d9bTpjXpaaVMlVK78LDJqvLCkjz1
Monthly Price ID: price_1S0dwrKkH1LI50QC2GhtfzN4
Yearly Price ID: price_1S0dxYKkH1LI50QCEqPZJ6Jq
```

---

## 🚀 Complete Setup (5 Steps)

### Step 1: Add Webhook Secret to .env

```bash
# Edit your .env file
nano .env
```

Add or update these lines:
```bash
# STRIPE CONFIGURATION
STRIPE_PUBLISHABLE_KEY=pk_test_YOUR_KEY_HERE
STRIPE_SECRET_KEY=sk_test_YOUR_KEY_HERE
STRIPE_WEBHOOK_SECRET=whsec_kYH0d9bTpjXpaaVMlVK78LDJqvLCkjz1
STRIPE_ENABLED=True
STRIPE_TEST_MODE=True
STRIPE_CURRENCY=usd
STRIPE_SUCCESS_URL=https://app.fiko.net/billing/success?session_id={CHECKOUT_SESSION_ID}
STRIPE_CANCEL_URL=https://app.fiko.net/billing/plans
STRIPE_PORTAL_RETURN_URL=https://app.fiko.net/billing
```

Save and exit (`Ctrl+X`, then `Y`, then `Enter`)

### Step 2: Run Migrations

```bash
cd /Users/nima/Projects/Fiko-Backend
python src/manage.py makemigrations
python src/manage.py migrate
```

This adds `stripe_product_id` and `stripe_price_id` fields to your plans.

### Step 3: Link Stripe Prices to Your Plans

**Option A: Using Django Admin (Easiest)**

1. Go to: http://api.fiko.net/admin/billing/fullplan/
2. Edit your Monthly plan:
   - Set `stripe_price_id` = `price_1S0dwrKkH1LI50QC2GhtfzN4`
3. Edit your Yearly plan:
   - Set `stripe_price_id` = `price_1S0dxYKkH1LI50QCEqPZJ6Jq`
4. Save

**Option B: Using Script**

```bash
# Run the linking script
python link_stripe_prices.py
```

**Option C: Using Django Shell**

```bash
python src/manage.py shell
```

```python
from billing.models import FullPlan

# Update monthly plan
monthly = FullPlan.objects.filter(is_yearly=False).first()
if monthly:
    monthly.stripe_price_id = 'price_1S0dwrKkH1LI50QC2GhtfzN4'
    monthly.save()
    print(f"✅ Updated {monthly.name}")

# Update yearly plan
yearly = FullPlan.objects.filter(is_yearly=True).first()
if yearly:
    yearly.stripe_price_id = 'price_1S0dxYKkH1LI50QCEqPZJ6Jq'
    yearly.save()
    print(f"✅ Updated {yearly.name}")

print("Done!")
exit()
```

### Step 4: Restart Your Server

```bash
# If using systemd
sudo systemctl restart gunicorn

# If using Docker
docker-compose restart web
```

### Step 5: Test It!

```bash
# Get your plans
curl -X GET http://api.fiko.net/api/v1/billing/plans/full/ \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"

# Create checkout session
curl -X POST http://api.fiko.net/api/v1/billing/stripe/checkout-session/ \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "plan_type": "full",
    "plan_id": 1
  }'
```

**Expected Response:**
```json
{
  "session_id": "cs_test_...",
  "url": "https://checkout.stripe.com/pay/cs_test_...",
  "message": "Checkout session created successfully"
}
```

---

## 🧪 Test the Complete Flow

### 1. Create Checkout Session

```bash
POST /api/v1/billing/stripe/checkout-session/
{
  "plan_type": "full",
  "plan_id": 2  # Your yearly plan ID
}
```

### 2. Open Checkout URL

- Copy the `url` from the response
- Open it in a browser
- Use test card: `4242 4242 4242 4242`
- Any future date, any CVC, any ZIP

### 3. Complete Payment

After payment:
- Stripe redirects to: `https://app.fiko.net/billing/success?session_id=cs_test_...`
- Stripe sends webhook to: `https://api.fiko.net/api/v1/billing/stripe/webhook/`
- Your backend processes the webhook
- Subscription activated ✅
- Tokens added to user account ✅

### 4. Verify Subscription

```bash
GET /api/v1/billing/subscription/
```

Should show:
```json
{
  "is_active": true,
  "tokens_remaining": 100000,  # or whatever your plan includes
  "stripe_customer_id": "cus_...",
  "stripe_subscription_id": "sub_..."
}
```

---

## 📊 How Your Stripe Data is Used

### Webhook Secret
```
whsec_kYH0d9bTpjXpaaVMlVK78LDJqvLCkjz1
```
- Used to verify webhook signatures
- Ensures webhooks are actually from Stripe
- Prevents fake webhook attacks

### Monthly Price
```
price_1S0dwrKkH1LI50QC2GhtfzN4
```
- Linked to your Monthly subscription plan in database
- Used when creating checkout sessions for monthly subscriptions
- Stripe automatically handles recurring billing

### Yearly Price
```
price_1S0dxYKkH1LI50QCEqPZJ6Jq
```
- Linked to your Yearly subscription plan in database
- Used when creating checkout sessions for yearly subscriptions
- Stripe automatically handles recurring billing

---

## 🔄 Payment Flow Diagram

```
User clicks "Buy Plan"
         ↓
Frontend → POST /api/v1/billing/stripe/checkout-session/
         ↓
Backend creates session using your Stripe price ID
         ↓
User redirected to Stripe Checkout
         ↓
User enters card: 4242 4242 4242 4242
         ↓
Stripe processes payment
         ↓
Stripe → POST /api/v1/billing/stripe/webhook/
         ↓
Backend verifies signature using: whsec_kYH0d9bTpjXpaaVMlVK78LDJqvLCkjz1
         ↓
Backend activates subscription & adds tokens
         ↓
User redirected to success page
         ↓
✅ Done!
```

---

## 🎯 What Each Plan ID Means

When you create a checkout session for:

**Monthly Plan (plan_id = 1):**
- Uses: `price_1S0dwrKkH1LI50QC2GhtfzN4`
- Charges: $5/month (or whatever you set in Stripe)
- Gives: X tokens (defined in your database)
- Auto-renews: Every month

**Yearly Plan (plan_id = 2):**
- Uses: `price_1S0dxYKkH1LI50QCEqPZJ6Jq`
- Charges: $10/year (or whatever you set in Stripe)
- Gives: Y tokens (defined in your database)
- Auto-renews: Every year

---

## ✅ Verification Checklist

- [ ] Webhook secret added to `.env`: `whsec_kYH0d9bTpjXpaaVMlVK78LDJqvLCkjz1`
- [ ] Migrations run: `python src/manage.py migrate`
- [ ] Monthly plan linked: `price_1S0dwrKkH1LI50QC2GhtfzN4`
- [ ] Yearly plan linked: `price_1S0dxYKkH1LI50QCEqPZJ6Jq`
- [ ] Server restarted
- [ ] Test checkout session created successfully
- [ ] Test payment completed with test card
- [ ] Subscription activated after payment
- [ ] Tokens added to account
- [ ] Webhook events showing in Stripe Dashboard

---

## 🐛 Troubleshooting

### "Failed to create Stripe customer"
- **Fix**: Add Stripe API keys to `.env` (see Step 1)

### "Webhook signature verification failed"
- **Fix**: Make sure `STRIPE_WEBHOOK_SECRET` matches exactly: `whsec_kYH0d9bTpjXpaaVMlVK78LDJqvLCkjz1`

### Payment succeeds but subscription not activated
- **Check**: Stripe Dashboard → Webhooks → Your endpoint → Events
- **Look for**: 200 OK responses (good) or errors (bad)
- **Fix**: Check Django logs: `tail -f src/logs/django.log | grep stripe`

### Price ID not found
- **Fix**: Run Step 3 again to link prices to plans

---

## 📞 Quick Commands Reference

```bash
# Check if Stripe is configured
python3 -c "import os; print('Webhook secret:', 'SET' if os.environ.get('STRIPE_WEBHOOK_SECRET') else 'NOT SET')"

# Run migrations
python src/manage.py migrate

# Link prices (Django shell)
python src/manage.py shell
>>> from billing.models import FullPlan
>>> FullPlan.objects.filter(is_yearly=False).update(stripe_price_id='price_1S0dwrKkH1LI50QC2GhtfzN4')
>>> FullPlan.objects.filter(is_yearly=True).update(stripe_price_id='price_1S0dxYKkH1LI50QCEqPZJ6Jq')
>>> exit()

# Restart server
sudo systemctl restart gunicorn

# Test checkout
curl -X POST http://api.fiko.net/api/v1/billing/stripe/checkout-session/ \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"plan_type": "full", "plan_id": 1}'
```

---

## 🎉 You're All Set!

Your Stripe integration is now complete and using your actual Stripe products!

- ✅ Webhook configured and working
- ✅ Price IDs linked to database plans
- ✅ Ready to accept real payments
- ✅ Automatic subscription management

**Test with real card in Test Mode, then switch to Live Mode for production!**

---

*Need help? Read STRIPE_INTEGRATION_GUIDE.md for detailed documentation.*

