# 🎯 Your Stripe Configuration Data

## ✅ What You Have

### 1. Webhook Configuration
```
Endpoint ID: we_1SE7GfKkH1LI50QCXtiii36a
Endpoint URL: https://api.fiko.net/api/v1/billing/stripe/webhook/
Signing Secret: whsec_kYH0d9bTpjXpaaVMlVK78LDJqvLCkjz1
```

### 2. Product Prices
```
Monthly Subscription: price_1S0dwrKkH1LI50QC2GhtfzN4
Yearly Subscription: price_1S0dxYKkH1LI50QCEqPZJ6Jq
```

---

## 🚀 How to Use This Data

### Step 1: Add Webhook Secret to .env

Edit your `.env` file and add:

```bash
# Add this webhook secret
STRIPE_WEBHOOK_SECRET=whsec_kYH0d9bTpjXpaaVMlVK78LDJqvLCkjz1
```

Full configuration should be:
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

### Step 2: Restart Your Server

```bash
sudo systemctl restart gunicorn
# or
docker-compose restart web
```

---

## 💡 Option A: Use Existing Stripe Prices (Recommended)

Since you already have Stripe products with prices, you can use them directly:

### Update Your Database Plans to Match Stripe

You need to store the Stripe price IDs in your database. Let me create a migration for you:


