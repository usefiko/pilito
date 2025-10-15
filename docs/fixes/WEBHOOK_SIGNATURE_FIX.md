# 🔧 Fix Webhook Signature Error

## Problem
```
stripe._error.SignatureVerificationError: Unable to extract timestamp and signatures from header
```

This means Stripe is not sending the signature header, or you're testing without proper signature.

---

## 🎯 Root Cause

The error happens when:
1. **Testing manually** (curl/Postman) without Stripe signature header
2. **Stripe can't reach your webhook** (firewall/network issue)
3. **Webhook secret is wrong** for the endpoint

---

## ✅ Solutions

### Solution 1: Don't Test Manually (Recommended)

**Webhooks can ONLY be tested with:**
- ✅ Real Stripe events (after real checkout)
- ✅ Stripe Dashboard "Send test webhook"
- ✅ Stripe CLI

**Don't test with:**
- ❌ curl
- ❌ Postman
- ❌ Any manual POST request

Because these don't include the required Stripe signature!

---

### Solution 2: Temporarily Disable Signature Verification (For Testing Only)

**⚠️ WARNING: Only for testing! Never in production!**

Add this environment variable:
```bash
STRIPE_WEBHOOK_TESTING=True
```

Then update the webhook code to skip verification in test mode (not recommended).

---

### Solution 3: Use Stripe CLI for Local Testing

```bash
# Install Stripe CLI
brew install stripe/stripe-cli/stripe

# Login
stripe login

# Forward webhooks to your server
stripe listen --forward-to https://api.fiko.net/api/v1/billing/stripe/webhook/

# In another terminal, trigger test event
stripe trigger checkout.session.completed
```

---

## 🧪 Proper Testing Methods

### Method 1: Stripe Dashboard (Easiest)

1. Go to: https://dashboard.stripe.com/test/webhooks
2. Click on your webhook endpoint
3. Click **"Send test webhook"**
4. Select event type: `checkout.session.completed`
5. Click **"Send test webhook"**

✅ This includes proper signature!

### Method 2: Real Checkout Flow

1. Create checkout session via API
2. Complete payment with test card: `4242 4242 4242 4242`
3. Stripe automatically sends webhook
4. Your endpoint processes it

✅ Real production-like test!

### Method 3: Stripe CLI

```bash
# Trigger specific event
stripe trigger checkout.session.completed

# Or listen and forward
stripe listen --forward-to https://api.fiko.net/api/v1/billing/stripe/webhook/
```

✅ Includes proper signature!

---

## 🔍 Debug: Check What Stripe Receives

### Check Stripe Dashboard

1. Go to: https://dashboard.stripe.com/test/webhooks
2. Click your webhook endpoint
3. Check **"Attempts"** or **"Events"** tab
4. Look for:
   - ✅ 200 OK = Success
   - ❌ 400/500 = Error
   - ⏱️ Timeout = Server unreachable

### Check Your Logs

```bash
docker-compose logs -f web | grep -i webhook
```

Look for:
- `"Invalid webhook signature"` = Wrong secret or no signature
- `"Webhook secret not configured"` = Add to .env
- `"Successfully processed"` = Working!

---

## 🚨 Common Mistakes

### ❌ Testing with curl
```bash
# DON'T DO THIS - will always fail!
curl -X POST https://api.fiko.net/api/v1/billing/stripe/webhook/ \
  -d '{"type": "checkout.session.completed"}'
```
**Why it fails**: No Stripe signature header

### ✅ Correct Way
```bash
# Use Stripe Dashboard "Send test webhook"
# OR use Stripe CLI
stripe trigger checkout.session.completed
```

---

## 📋 Verification Checklist

- [ ] STRIPE_WEBHOOK_SECRET is set in .env
- [ ] Webhook endpoint is publicly accessible (not localhost)
- [ ] Testing using Stripe Dashboard or Stripe CLI
- [ ] NOT testing with curl/Postman
- [ ] Webhook shows in Stripe Dashboard
- [ ] Events tab shows successful deliveries

---

## 🎯 Expected Behavior

### When Working Correctly:

**Request from Stripe includes:**
```
POST /api/v1/billing/stripe/webhook/
Stripe-Signature: t=1234567890,v1=abc123...
Content-Type: application/json

{
  "type": "checkout.session.completed",
  "data": { ... }
}
```

**Your server responds:**
```
HTTP 200 OK
```

**Logs show:**
```
INFO: Received Stripe webhook: checkout.session.completed
INFO: Successfully processed checkout session cs_test_...
```

---

## 🔧 If You Must Test Locally

Use ngrok + Stripe CLI:

```bash
# Terminal 1: Start ngrok
ngrok http 8000

# Copy the https URL (e.g., https://abc123.ngrok.io)

# Terminal 2: Update Stripe webhook URL
# Go to Stripe Dashboard → Webhooks
# Update URL to: https://abc123.ngrok.io/api/v1/billing/stripe/webhook/

# Terminal 3: Run your server
docker-compose up

# Terminal 4: Trigger event
stripe trigger checkout.session.completed
```

---

## ✅ Production Setup

1. **Webhook URL**: `https://api.fiko.net/api/v1/billing/stripe/webhook/`
2. **Must be HTTPS** (Stripe requires it)
3. **Must be publicly accessible** (not localhost)
4. **Must respond within 30 seconds**
5. **Configure in Stripe Dashboard**: https://dashboard.stripe.com/webhooks

---

## 🎉 Summary

**The Issue**: You (or something) is testing the webhook without Stripe's signature header.

**The Fix**: 
1. ✅ Use Stripe Dashboard "Send test webhook"
2. ✅ OR use Stripe CLI
3. ✅ OR wait for real Stripe events
4. ❌ DON'T test with curl/Postman

**Your webhook is working correctly** - it's just rejecting invalid requests (which is good for security!)

---

## 📞 Quick Test

```bash
# From Stripe Dashboard → Webhooks → Your endpoint
# Click "Send test webhook"
# Select: checkout.session.completed
# Click "Send test webhook"

# Check response: Should be 200 OK ✅
```

That's it! Your webhook is secure and working as expected.

