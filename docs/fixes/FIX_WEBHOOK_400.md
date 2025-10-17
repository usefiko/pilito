# 🔧 Fix Stripe Webhook 400 Error

## Problem
Getting 400 error when Stripe sends webhook to `/api/v1/billing/stripe/webhook/`

## Root Cause
Most likely: **`STRIPE_WEBHOOK_SECRET` not configured in production environment**

---

## ✅ Solution (3 Steps)

### Step 1: Add STRIPE_WEBHOOK_SECRET to Production

**On your production server:**

```bash
# SSH to server
ssh ubuntu@your-server-ip

# Go to project directory
cd /path/to/Fiko-Backend

# Edit .env file
nano .env
```

Add this line (or update if exists):
```bash
STRIPE_WEBHOOK_SECRET=whsec_kYH0d9bTpjXpaaVMlVK78LDJqvLCkjz1
```

Save: `Ctrl+X`, then `Y`, then `Enter`

### Step 2: Restart Docker

```bash
docker-compose restart
```

### Step 3: Verify It's Set

```bash
docker-compose exec web python -c "import os; from dotenv import load_dotenv; load_dotenv(); print('STRIPE_WEBHOOK_SECRET:', 'CONFIGURED' if os.environ.get('STRIPE_WEBHOOK_SECRET') else 'NOT SET')"
```

**Expected output:**
```
STRIPE_WEBHOOK_SECRET: CONFIGURED
```

---

## 🧪 Test the Fix

### Method 1: Test from Stripe Dashboard

1. Go to: https://dashboard.stripe.com/test/webhooks
2. Click on your webhook endpoint
3. Click **"Send test webhook"**
4. Choose: `checkout.session.completed`
5. Click **"Send test webhook"**

**Expected Response:** Status 200 ✅

### Method 2: Check Server Logs

```bash
# Watch logs in real-time
docker-compose logs -f web

# Or check recent logs
docker-compose logs --tail=50 web | grep -i stripe
```

Now the logs will show **exactly** what's wrong:
- `"Stripe SDK not installed"` → Install stripe: `pip install stripe`
- `"Webhook secret not configured"` → Add to `.env`
- `"Invalid signature"` → Wrong webhook secret
- `"Invalid payload"` → Check request format

---

## 🔍 Common Issues & Solutions

### Issue 1: "Webhook secret not configured"

**Solution:**
```bash
# Add to .env
STRIPE_WEBHOOK_SECRET=whsec_kYH0d9bTpjXpaaVMlVK78LDJqvLCkjz1

# Restart
docker-compose restart
```

### Issue 2: "Invalid signature"

**Causes:**
- Wrong webhook secret
- Using Test secret with Live webhooks (or vice versa)
- Webhook secret from different endpoint

**Solution:**
```bash
# Get the correct secret from Stripe Dashboard
# https://dashboard.stripe.com/test/webhooks
# Click your endpoint → Reveal signing secret

# Update .env with correct secret
STRIPE_WEBHOOK_SECRET=whsec_the_correct_secret_here

# Restart
docker-compose restart
```

### Issue 3: "Stripe SDK not installed"

**Solution:**
```bash
# In your Dockerfile or manually in container
docker-compose exec web pip install stripe

# Better: Add to requirements/base.txt (already done)
# Then rebuild:
docker-compose build
docker-compose up -d
```

---

## 📋 Complete Environment Variables Checklist

Your `.env` should have:

```bash
# Stripe API Keys
STRIPE_PUBLISHABLE_KEY=pk_test_...
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_kYH0d9bTpjXpaaVMlVK78LDJqvLCkjz1  # ← This one!

# Stripe Configuration
STRIPE_ENABLED=True
STRIPE_TEST_MODE=True
STRIPE_CURRENCY=usd

# Frontend URLs
STRIPE_SUCCESS_URL=https://app.pilito.com/billing/success?session_id={CHECKOUT_SESSION_ID}
STRIPE_CANCEL_URL=https://app.pilito.com/billing/plans
STRIPE_PORTAL_RETURN_URL=https://app.pilito.com/billing
```

---

## 🎯 Verification Steps

After fixing, verify:

1. **Environment variable set:**
   ```bash
   docker-compose exec web python -c "import os; print(os.environ.get('STRIPE_WEBHOOK_SECRET', 'NOT SET')[:20] + '...')"
   ```
   Should show: `whsec_kYH0d9bTpjXp...`

2. **Webhook responds with 200:**
   - Send test webhook from Stripe Dashboard
   - Check response is 200 OK

3. **Events are processed:**
   ```bash
   docker-compose logs web | grep "Successfully processed checkout session"
   ```

---

## 🚨 If Still Getting 400

### Check Settings Loading

The webhook uses `settings.STRIPE_WEBHOOK_SECRET`, so check it's loading:

```bash
docker-compose exec web python manage.py shell
```

```python
from django.conf import settings

# Check if it's loaded
print("STRIPE_WEBHOOK_SECRET:", hasattr(settings, 'STRIPE_WEBHOOK_SECRET'))
print("Value:", getattr(settings, 'STRIPE_WEBHOOK_SECRET', 'NOT SET')[:20] + '...')

# Also check from stripe_settings module
from settings import stripe_settings
print("stripe_settings.STRIPE_WEBHOOK_SECRET:", stripe_settings.STRIPE_WEBHOOK_SECRET[:20] + '...')

exit()
```

If these show different values or NOT SET, the issue is with settings loading.

### Ensure Settings Module Loads Environment

Check that your settings file loads environment variables:

```python
# In your settings/__init__.py or settings/base.py
import os
from dotenv import load_dotenv

load_dotenv()  # This loads .env file

STRIPE_WEBHOOK_SECRET = os.environ.get('STRIPE_WEBHOOK_SECRET', '')
```

---

## 📝 Quick Fix Commands

```bash
# Complete fix in one go:

# 1. Add to .env
echo "STRIPE_WEBHOOK_SECRET=whsec_kYH0d9bTpjXpaaVMlVK78LDJqvLCkjz1" >> .env

# 2. Restart
docker-compose restart

# 3. Test
curl -X POST https://api.pilito.com/api/v1/billing/stripe/webhook/ \
  -H "Content-Type: application/json" \
  -d '{}'

# Should now return proper error message instead of just "400"
```

---

## ✅ Success Criteria

You'll know it's fixed when:

1. ✅ Test webhook from Stripe Dashboard returns **200 OK**
2. ✅ Logs show `"Successfully processed checkout session"`
3. ✅ No `"Webhook secret not configured"` errors in logs
4. ✅ Actual payment webhooks are processed correctly

---

## 🆘 Still Not Working?

Deploy the updated code with better error messages:

```bash
# On local machine
cd /Users/nima/Projects/Fiko-Backend
git add src/billing/views.py
git commit -m "Improve webhook error logging"
git push origin main

# On production server
git pull origin main
docker-compose restart

# Now try webhook again - you'll see exact error in response
```

---

**TL;DR**: Add `STRIPE_WEBHOOK_SECRET=whsec_kYH0d9bTpjXpaaVMlVK78LDJqvLCkjz1` to your `.env` file and restart Docker!

