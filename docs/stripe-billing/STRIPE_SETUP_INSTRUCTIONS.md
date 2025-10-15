# 🔧 Fix "Failed to create Stripe customer" Error

## ❌ Problem
Your Stripe API keys are not configured in the environment variables.

## ✅ Solution (3 Minutes)

### Step 1: Get Your Stripe API Keys

1. **Go to Stripe Dashboard**:
   - **Test Mode**: https://dashboard.stripe.com/test/apikeys
   - **Live Mode**: https://dashboard.stripe.com/apikeys (for production)

2. **Copy Your Keys**:
   ```
   Publishable key: pk_test_51ABC...xyz
   Secret key: sk_test_51ABC...xyz (click "Reveal" button)
   ```

### Step 2: Add Keys to .env File

Open your `.env` file:
```bash
nano .env
```

Add these lines at the end:
```bash
# ===================================
# STRIPE CONFIGURATION
# ===================================

# Get from: https://dashboard.stripe.com/test/apikeys
STRIPE_PUBLISHABLE_KEY=pk_test_YOUR_KEY_HERE
STRIPE_SECRET_KEY=sk_test_YOUR_KEY_HERE

# Get after configuring webhook (see STRIPE_WEBHOOK_SETUP.md)
STRIPE_WEBHOOK_SECRET=whsec_YOUR_WEBHOOK_SECRET

# Configuration
STRIPE_ENABLED=True
STRIPE_TEST_MODE=True
STRIPE_CURRENCY=usd

# Frontend URLs (adjust to match your frontend)
STRIPE_SUCCESS_URL=https://app.fiko.net/billing/success?session_id={CHECKOUT_SESSION_ID}
STRIPE_CANCEL_URL=https://app.fiko.net/billing/plans
STRIPE_PORTAL_RETURN_URL=https://app.fiko.net/billing
```

**Save and exit**: Press `Ctrl+X`, then `Y`, then `Enter`

### Step 3: Restart Your Server

```bash
# If using systemd/gunicorn
sudo systemctl restart gunicorn

# If using Docker
docker-compose restart web

# If running development server
# Kill the process and restart:
python src/manage.py runserver
```

### Step 4: Test Again

Try your API request again:

```bash
POST /api/v1/billing/stripe/checkout-session/
{
    "plan_type": "full",
    "plan_id": 2
}
```

Should now return:
```json
{
    "session_id": "cs_test_...",
    "url": "https://checkout.stripe.com/pay/cs_test_...",
    "message": "Checkout session created successfully"
}
```

---

## 🎯 Quick Copy-Paste Template

Replace `YOUR_KEY_HERE` with actual keys from Stripe Dashboard:

```bash
# Copy this to your .env file
STRIPE_PUBLISHABLE_KEY=pk_test_YOUR_KEY_HERE
STRIPE_SECRET_KEY=sk_test_YOUR_KEY_HERE
STRIPE_WEBHOOK_SECRET=whsec_YOUR_WEBHOOK_SECRET
STRIPE_ENABLED=True
STRIPE_TEST_MODE=True
STRIPE_CURRENCY=usd
STRIPE_SUCCESS_URL=https://app.fiko.net/billing/success?session_id={CHECKOUT_SESSION_ID}
STRIPE_CANCEL_URL=https://app.fiko.net/billing/plans
STRIPE_PORTAL_RETURN_URL=https://app.fiko.net/billing
```

---

## 🔍 Verify Configuration

After adding keys and restarting, check if Stripe is configured:

```bash
python3 -c "import os; from dotenv import load_dotenv; load_dotenv(); print('✅ STRIPE_SECRET_KEY:', 'CONFIGURED' if os.getenv('STRIPE_SECRET_KEY') else '❌ NOT SET')"
```

Expected output:
```
✅ STRIPE_SECRET_KEY: CONFIGURED
```

---

## 📝 Complete Setup Order

1. ✅ **Install Stripe SDK** (Done!)
2. ⏳ **Get API Keys** (https://dashboard.stripe.com/test/apikeys)
3. ⏳ **Add to .env** (see above)
4. ⏳ **Restart server**
5. ⏳ **Configure webhook** (see STRIPE_WEBHOOK_SETUP.md)
6. ⏳ **Test checkout session**

---

## 🆘 Still Getting Errors?

### Error: "STRIPE_SECRET_KEY is not configured"
- Make sure you added the keys to `.env`
- Make sure you restarted the server
- Check there are no typos in variable names

### Error: "Invalid API Key"
- Make sure you're using **Test mode** keys (pk_test_ and sk_test_)
- Copy the keys again from Stripe Dashboard
- Make sure there are no extra spaces

### Error: "Stripe is not enabled"
- Add `STRIPE_ENABLED=True` to `.env`
- Restart server

---

## 🎉 Next Steps

Once this works:
1. Configure webhooks (STRIPE_WEBHOOK_SETUP.md)
2. Test with test card: 4242 4242 4242 4242
3. Integrate with your frontend
4. Switch to Live mode for production

---

**Need Help?** 
- Read: STRIPE_INTEGRATION_GUIDE.md
- Check: STRIPE_WEBHOOK_SETUP.md

