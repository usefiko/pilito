# 🪝 Stripe Webhook Setup Guide

## Quick Answer: How to Get STRIPE_WEBHOOK_SECRET

There are **two ways** to get your webhook secret:

---

## 🚀 Method 1: For Development (Local Testing)

Use Stripe CLI to test webhooks on your local machine:

### Step 1: Install Stripe CLI

**macOS:**
```bash
brew install stripe/stripe-cli/stripe
```

**Linux:**
```bash
# Download and install
wget https://github.com/stripe/stripe-cli/releases/download/v1.19.0/stripe_1.19.0_linux_x86_64.tar.gz
tar -xvf stripe_1.19.0_linux_x86_64.tar.gz
sudo mv stripe /usr/local/bin/
```

**Windows:**
Download from: https://github.com/stripe/stripe-cli/releases

### Step 2: Login to Stripe CLI

```bash
stripe login
```

This will open your browser to authenticate.

### Step 3: Forward Webhooks to Your Local Server

```bash
stripe listen --forward-to localhost:8000/billing/stripe/webhook/
```

**Output:**
```
> Ready! Your webhook signing secret is whsec_1234567890abcdef... (^C to quit)
```

### Step 4: Copy the Webhook Secret

Copy the `whsec_...` secret from the output and add to your `.env`:

```bash
STRIPE_WEBHOOK_SECRET=whsec_1234567890abcdef...
```

✅ **Done!** Now webhooks will be forwarded to your local server for testing.

### Test It

In another terminal, trigger a test event:
```bash
stripe trigger checkout.session.completed
```

---

## 🌐 Method 2: For Production (Live Server)

Configure webhooks directly in Stripe Dashboard:

### Step 1: Go to Stripe Dashboard

**Test Mode:**
https://dashboard.stripe.com/test/webhooks

**Live Mode:**
https://dashboard.stripe.com/webhooks

### Step 2: Add Endpoint

1. Click **"+ Add endpoint"** button

2. Enter your webhook URL:
   ```
   https://api.pilito.com/billing/stripe/webhook/
   ```
   
   **Important**: Must be HTTPS in production!

3. **Select events to listen to**:
   
   Click **"Select events"** button and choose:
   
   ✅ **Checkout Events:**
   - `checkout.session.completed`
   - `checkout.session.async_payment_succeeded`
   - `checkout.session.async_payment_failed`
   
   ✅ **Subscription Events:**
   - `customer.subscription.created`
   - `customer.subscription.updated`
   - `customer.subscription.deleted`
   - `customer.subscription.trial_will_end`
   
   ✅ **Invoice Events:**
   - `invoice.paid`
   - `invoice.payment_failed`
   - `invoice.upcoming`
   
   ✅ **Payment Intent Events:**
   - `payment_intent.succeeded`
   - `payment_intent.payment_failed`
   
   **Or** select **"receive all events"** (easier but more events)

4. Click **"Add endpoint"**

### Step 3: Get Your Webhook Secret

After creating the endpoint:

1. You'll see your new webhook endpoint in the list
2. Click on it to open details
3. Under **"Signing secret"**, click **"Reveal"**
4. Copy the secret (starts with `whsec_...`)

**Screenshot Location:**
```
Dashboard → Webhooks → [Your Endpoint] → Signing secret
```

### Step 4: Add to Environment Variables

**For Production Server:**
```bash
# SSH into your production server
ssh user@api.pilito.com

# Edit your environment file
nano /path/to/your/.env

# Add the webhook secret
STRIPE_WEBHOOK_SECRET=whsec_your_production_secret_here

# Restart your Django application
sudo systemctl restart gunicorn
# or
docker-compose restart web
```

---

## 🧪 Testing Your Webhook

### Method 1: Use Stripe CLI (Recommended)

```bash
# Trigger test events
stripe trigger checkout.session.completed
stripe trigger customer.subscription.updated
stripe trigger invoice.paid
```

### Method 2: Make a Test Purchase

1. Create a checkout session:
   ```bash
   curl -X POST http://api.pilito.com/api/v1/billing/stripe/checkout-session/ \
     -H "Authorization: Bearer YOUR_JWT_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"plan_type": "full", "plan_id": 1}'
   ```

2. Open the returned URL in browser

3. Use test card: `4242 4242 4242 4242`

4. Complete payment

5. Check your server logs:
   ```bash
   tail -f /path/to/logs/django.log | grep -i stripe
   ```

### Method 3: Check Webhook Events in Dashboard

Go to: https://dashboard.stripe.com/webhooks

- Click on your endpoint
- View **"Events"** tab
- See delivered events and their status (✅ success or ❌ failed)

---

## 🔍 Verify Webhook is Working

### Check 1: Webhook Status in Stripe Dashboard

1. Go to https://dashboard.stripe.com/webhooks
2. Click on your endpoint
3. Check **"Events"** tab
4. You should see events with status codes:
   - **200** = ✅ Success
   - **4xx** = ❌ Client error (check your code)
   - **5xx** = ❌ Server error (check your logs)

### Check 2: Check Django Logs

```bash
# Look for Stripe webhook logs
tail -f src/logs/django.log | grep -i stripe

# Expected output:
# INFO: Received Stripe webhook: checkout.session.completed
# INFO: Successfully processed checkout session cs_test_...
```

### Check 3: Test Subscription Activation

After a successful test payment:

```bash
# Check if subscription was created
curl -X GET http://api.pilito.com/api/v1/billing/subscription/ \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"

# Should show active subscription with tokens
```

---

## 🚨 Troubleshooting

### Issue 1: "No signature found in headers"

**Cause:** Webhook secret not configured or incorrect

**Solution:**
```bash
# Make sure STRIPE_WEBHOOK_SECRET is set
echo $STRIPE_WEBHOOK_SECRET

# If empty, add to .env:
STRIPE_WEBHOOK_SECRET=whsec_...

# Restart Django
```

### Issue 2: "Webhook signature verification failed"

**Cause:** Using wrong webhook secret (Test vs Live)

**Solution:**
- In **Test Mode**: Use webhook secret from Stripe CLI or Test Dashboard
- In **Live Mode**: Use webhook secret from Live Dashboard
- Make sure `STRIPE_TEST_MODE` matches your environment

### Issue 3: Webhooks timing out (status code 504)

**Cause:** Webhook handler taking too long (>30 seconds)

**Solution:**
- Move heavy processing to background tasks (Celery)
- Return 200 response quickly
- Process event asynchronously

### Issue 4: Receiving same event multiple times

**Cause:** Not responding quickly enough, Stripe retries

**Solution:**
- Implement idempotency (we already do this!)
- Check if event was already processed
- Return 200 even if already processed

### Issue 5: Local webhooks not working

**Cause:** Stripe CLI not forwarding or server not running

**Solution:**
```bash
# Make sure Django is running
python src/manage.py runserver

# In another terminal, forward webhooks
stripe listen --forward-to localhost:8000/billing/stripe/webhook/

# Test
stripe trigger checkout.session.completed
```

---

## 📋 Complete Setup Checklist

### Development Setup:
- [ ] Install Stripe SDK: `pip install stripe`
- [ ] Install Stripe CLI: `brew install stripe/stripe-cli/stripe`
- [ ] Login: `stripe login`
- [ ] Forward webhooks: `stripe listen --forward-to localhost:8000/billing/stripe/webhook/`
- [ ] Copy webhook secret to `.env`
- [ ] Test: `stripe trigger checkout.session.completed`

### Production Setup:
- [ ] Go to Stripe Dashboard → Webhooks
- [ ] Add endpoint: `https://api.pilito.com/billing/stripe/webhook/`
- [ ] Select events (or "receive all events")
- [ ] Copy signing secret
- [ ] Add to production `.env`: `STRIPE_WEBHOOK_SECRET=whsec_...`
- [ ] Restart Django application
- [ ] Test with real purchase (use test card in test mode)
- [ ] Verify events in Dashboard → Webhooks → [Your endpoint] → Events

---

## 🔐 Security Notes

1. **Never commit webhook secrets** to version control
2. **Always verify signatures** in production (we do this automatically)
3. **Use HTTPS** for production webhooks (Stripe requires it)
4. **Different secrets for Test vs Live** mode
5. **Rotate secrets** if compromised

---

## 📚 Quick Reference

### Get Webhook Secret (Development):
```bash
stripe listen --forward-to localhost:8000/billing/stripe/webhook/
# Copy the whsec_... from output
```

### Get Webhook Secret (Production):
```
1. Go to: https://dashboard.stripe.com/webhooks
2. Click your endpoint
3. Click "Reveal" under "Signing secret"
4. Copy the whsec_... secret
```

### Add to .env:
```bash
STRIPE_WEBHOOK_SECRET=whsec_your_secret_here
```

### Test Webhook:
```bash
stripe trigger checkout.session.completed
```

### Check Logs:
```bash
tail -f src/logs/django.log | grep -i stripe
```

---

## 🎉 You're Done!

Your webhook is now configured! When a payment is completed:

1. Stripe sends webhook to your server
2. Your server verifies the signature
3. Subscription is activated
4. Tokens are added to user account
5. User is redirected to success page

✅ **All automatic!**

---

## 📞 Need More Help?

- **Stripe Webhook Docs**: https://stripe.com/docs/webhooks
- **Stripe CLI Docs**: https://stripe.com/docs/stripe-cli
- **Testing Guide**: https://stripe.com/docs/testing
- **Dashboard**: https://dashboard.stripe.com/webhooks

---

*Last Updated: October 2, 2025*

