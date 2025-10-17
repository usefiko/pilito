# 🎉 Stripe Integration Guide for Fiko Backend

## 📋 Table of Contents

1. [Overview](#overview)
2. [Setup & Configuration](#setup--configuration)
3. [API Endpoints](#api-endpoints)
4. [Frontend Integration](#frontend-integration)
5. [Webhook Configuration](#webhook-configuration)
6. [Testing](#testing)
7. [Production Deployment](#production-deployment)

---

## 🎯 Overview

This guide provides complete instructions for integrating Stripe payment processing into your Fiko Backend application. The integration supports:

- ✅ **Token Package Purchases** - One-time or recurring token purchases
- ✅ **Full Plan Subscriptions** - Monthly or yearly subscription plans with tokens
- ✅ **Stripe Checkout** - Secure, hosted payment pages
- ✅ **Customer Portal** - Self-service subscription management
- ✅ **Webhook Events** - Automatic subscription and payment status updates
- ✅ **Multi-currency Support** - Configurable currencies (USD, EUR, etc.)

---

## ⚙️ Setup & Configuration

### 1. Install Stripe SDK

```bash
pip install stripe
```

Or add to your `requirements/base.txt`:
```
stripe>=5.0.0
```

### 2. Get Your Stripe Keys

1. Go to [https://dashboard.stripe.com/apikeys](https://dashboard.stripe.com/apikeys)
2. Copy your **Publishable key** and **Secret key**
3. For testing, use the **Test mode** keys (starting with `pk_test_` and `sk_test_`)

### 3. Configure Environment Variables

Add these to your `.env` file or environment:

```bash
# Stripe API Keys
STRIPE_PUBLISHABLE_KEY=pk_test_your_key_here
STRIPE_SECRET_KEY=sk_test_your_key_here
STRIPE_WEBHOOK_SECRET=whsec_your_webhook_secret_here

# Configuration
STRIPE_ENABLED=True
STRIPE_TEST_MODE=True
STRIPE_CURRENCY=usd

# Frontend URLs (adjust to match your frontend)
STRIPE_SUCCESS_URL=http://localhost:3000/billing/success?session_id={CHECKOUT_SESSION_ID}
STRIPE_CANCEL_URL=http://localhost:3000/billing/plans
STRIPE_PORTAL_RETURN_URL=http://localhost:3000/billing
```

### 4. Update Django Settings

The Stripe settings are automatically loaded from `settings/stripe_settings.py`. Make sure it's imported in your main settings file.

Add to your `core/settings/__init__.py` or `core/settings/base.py`:

```python
from settings import stripe_settings
```

---

## 📡 API Endpoints

### 1. Create Checkout Session

**Endpoint**: `POST /billing/stripe/checkout-session/`

**Purpose**: Create a Stripe Checkout session for purchasing a plan.

**Request**:
```json
{
  "plan_type": "full",
  "plan_id": 1,
  "success_url": "https://yoursite.com/success",  // optional
  "cancel_url": "https://yoursite.com/cancel"     // optional
}
```

**Response**:
```json
{
  "session_id": "cs_test_a1b2c3...",
  "url": "https://checkout.stripe.com/pay/cs_test_a1b2c3...",
  "message": "Checkout session created successfully"
}
```

**cURL Example**:
```bash
curl -X POST http://localhost:8000/billing/stripe/checkout-session/ \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "plan_type": "full",
    "plan_id": 1
  }'
```

### 2. Create Customer Portal Session

**Endpoint**: `POST /billing/stripe/customer-portal/`

**Purpose**: Create a Stripe Customer Portal session for managing subscription.

**Request**:
```json
{
  "return_url": "https://yoursite.com/billing"  // optional
}
```

**Response**:
```json
{
  "url": "https://billing.stripe.com/session/...",
  "message": "Portal session created successfully"
}
```

**cURL Example**:
```bash
curl -X POST http://localhost:8000/billing/stripe/customer-portal/ \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{}'
```

### 3. Webhook Endpoint

**Endpoint**: `POST /billing/stripe/webhook/`

**Purpose**: Receive webhook events from Stripe (configured in Stripe Dashboard).

This endpoint is called automatically by Stripe and should not be called manually.

---

## 💻 Frontend Integration

### React/Next.js Example

#### 1. Install Stripe.js

```bash
npm install @stripe/stripe-js
```

#### 2. Purchase Flow Component

```javascript
import { loadStripe } from '@stripe/stripe-js';

const stripePromise = loadStripe('pk_test_your_publishable_key');

function PlanPurchase({ planType, planId }) {
  const handlePurchase = async () => {
    try {
      // Call your backend to create checkout session
      const response = await fetch('/api/billing/stripe/checkout-session/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${yourJwtToken}`,
        },
        body: JSON.stringify({
          plan_type: planType,  // 'token' or 'full'
          plan_id: planId,
        }),
      });

      const { url } = await response.json();

      // Redirect to Stripe Checkout
      window.location.href = url;
    } catch (error) {
      console.error('Error creating checkout session:', error);
    }
  };

  return (
    <button onClick={handlePurchase}>
      Purchase Plan
    </button>
  );
}
```

#### 3. Customer Portal Component

```javascript
function ManageSubscription() {
  const handleManageSubscription = async () => {
    try {
      const response = await fetch('/api/billing/stripe/customer-portal/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${yourJwtToken}`,
        },
        body: JSON.stringify({}),
      });

      const { url } = await response.json();

      // Redirect to Stripe Customer Portal
      window.location.href = url;
    } catch (error) {
      console.error('Error creating portal session:', error);
    }
  };

  return (
    <button onClick={handleManageSubscription}>
      Manage Subscription
    </button>
  );
}
```

#### 4. Success Page

```javascript
// pages/billing/success.js
import { useEffect } from 'react';
import { useRouter } from 'next/router';

export default function Success() {
  const router = useRouter();
  const { session_id } = router.query;

  useEffect(() => {
    if (session_id) {
      // Optionally verify the session on your backend
      // Then show success message and redirect
      setTimeout(() => {
        router.push('/billing');
      }, 3000);
    }
  }, [session_id]);

  return (
    <div>
      <h1>✅ Payment Successful!</h1>
      <p>Your subscription has been activated.</p>
      <p>Session ID: {session_id}</p>
    </div>
  );
}
```

---

## 🔗 Webhook Configuration

### 1. Set Up Webhook in Stripe Dashboard

1. Go to [https://dashboard.stripe.com/webhooks](https://dashboard.stripe.com/webhooks)
2. Click **+ Add endpoint**
3. Enter your webhook URL:
   ```
   https://api.pilito.com/billing/stripe/webhook/
   ```
4. Select events to listen to:
   - ✅ `checkout.session.completed`
   - ✅ `customer.subscription.created`
   - ✅ `customer.subscription.updated`
   - ✅ `customer.subscription.deleted`
   - ✅ `invoice.paid`
   - ✅ `invoice.payment_failed`
   - ✅ `payment_intent.succeeded`
   - ✅ `payment_intent.payment_failed`

5. Click **Add endpoint**
6. Copy the **Signing secret** (starts with `whsec_...`)
7. Add it to your environment variables as `STRIPE_WEBHOOK_SECRET`

### 2. Test Webhook Locally

Use Stripe CLI to forward webhooks to your local development server:

```bash
# Install Stripe CLI
brew install stripe/stripe-cli/stripe

# Login
stripe login

# Forward webhooks to local server
stripe listen --forward-to localhost:8000/billing/stripe/webhook/
```

This will give you a webhook signing secret for testing. Add it to your `.env`:
```bash
STRIPE_WEBHOOK_SECRET=whsec_test_...
```

---

## 🧪 Testing

### 1. Test Cards

Use these test card numbers in Stripe Checkout (Test Mode):

| Card Number | Description |
|-------------|-------------|
| `4242 4242 4242 4242` | Successful payment |
| `4000 0025 0000 3155` | Requires authentication (3D Secure) |
| `4000 0000 0000 9995` | Payment declined |

- Use any future expiration date (e.g., `12/34`)
- Use any 3-digit CVC (e.g., `123`)
- Use any ZIP code (e.g., `12345`)

### 2. Test Subscription Purchase

```bash
# 1. Get available plans
curl -X GET http://localhost:8000/billing/plans/full/ \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"

# 2. Create checkout session
curl -X POST http://localhost:8000/billing/stripe/checkout-session/ \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "plan_type": "full",
    "plan_id": 1
  }'

# 3. Open the returned URL in browser and complete payment with test card
```

### 3. Test Webhook Events

```bash
# Trigger test webhook events
stripe trigger checkout.session.completed
stripe trigger customer.subscription.updated
stripe trigger invoice.paid
```

### 4. Check Logs

Monitor your Django logs to see webhook events being processed:

```bash
tail -f src/logs/django.log | grep -i stripe
```

---

## 🚀 Production Deployment

### 1. Switch to Live Mode

1. Get your **Live** API keys from [Stripe Dashboard](https://dashboard.stripe.com/apikeys)
2. Update environment variables:
   ```bash
   STRIPE_PUBLISHABLE_KEY=pk_live_your_key_here
   STRIPE_SECRET_KEY=sk_live_your_key_here
   STRIPE_TEST_MODE=False
   ```

### 2. Update Frontend URLs

Update your environment variables with production URLs:
```bash
STRIPE_SUCCESS_URL=https://app.pilito.com/billing/success?session_id={CHECKOUT_SESSION_ID}
STRIPE_CANCEL_URL=https://app.pilito.com/billing/plans
STRIPE_PORTAL_RETURN_URL=https://app.pilito.com/billing
```

### 3. Configure Production Webhook

1. Go to [Stripe Dashboard - Webhooks](https://dashboard.stripe.com/webhooks) (Live mode)
2. Add your production webhook URL:
   ```
   https://api.pilito.com/billing/stripe/webhook/
   ```
3. Select the same events as before
4. Copy the signing secret and add to production environment:
   ```bash
   STRIPE_WEBHOOK_SECRET=whsec_live_...
   ```

### 4. Sync Plans to Stripe (Optional)

Run the management command to create Stripe products for your plans:

```bash
python manage.py sync_stripe_products --plan-type all
```

This will:
- Create Stripe Products for each plan
- Create Stripe Prices for each product
- Link them to your billing plans

### 5. Test in Production

Use a real credit card to test the complete flow in production (use small amounts):
1. Purchase a plan
2. Verify subscription activation
3. Check Customer Portal works
4. Verify webhook events are received

---

## 📊 Monitoring & Maintenance

### 1. Monitor Stripe Dashboard

Regularly check:
- [Payments](https://dashboard.stripe.com/payments)
- [Subscriptions](https://dashboard.stripe.com/subscriptions)
- [Customers](https://dashboard.stripe.com/customers)
- [Webhooks](https://dashboard.stripe.com/webhooks) (check for failed deliveries)

### 2. Check Subscription Status

Use the management command to review subscriptions:

```bash
python manage.py check_subscription_status --dry-run
```

### 3. Handle Failed Payments

Monitor for failed payment webhooks and follow up with customers. You can set up email notifications in Stripe Dashboard.

### 4. Regular Health Checks

```bash
# Check for subscriptions with payment issues
python manage.py check_subscription_status

# View payment history
curl -X GET http://localhost:8000/billing/payments/ \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

---

## 🔒 Security Best Practices

1. **Always verify webhook signatures** - The webhook secret is configured and verification is enabled
2. **Use HTTPS in production** - Stripe requires HTTPS for webhooks
3. **Keep API keys secret** - Never commit keys to version control
4. **Rotate keys periodically** - Generate new keys every 6-12 months
5. **Monitor for suspicious activity** - Check Stripe Dashboard regularly
6. **Enable Stripe Radar** - Helps prevent fraud automatically

---

## 🆘 Troubleshooting

### Issue: Webhook not receiving events

**Solution**:
1. Check webhook URL is correct in Stripe Dashboard
2. Verify `STRIPE_WEBHOOK_SECRET` is configured
3. Check server logs for webhook errors
4. Use Stripe CLI to test locally: `stripe listen --forward-to localhost:8000/billing/stripe/webhook/`

### Issue: Payment succeeds but subscription not activated

**Solution**:
1. Check webhook logs in Stripe Dashboard
2. Verify webhook handler is processing `checkout.session.completed` event
3. Check Django logs for errors during webhook processing
4. Manually trigger the event: `stripe trigger checkout.session.completed`

### Issue: Customer Portal not working

**Solution**:
1. Verify user has a `stripe_customer_id` in their subscription
2. Check Stripe Customer Portal is enabled in [Dashboard Settings](https://dashboard.stripe.com/settings/billing/portal)
3. Verify return URL is properly configured

### Issue: "Stripe is not enabled" error

**Solution**:
1. Check `STRIPE_ENABLED=True` in environment variables
2. Verify `STRIPE_SECRET_KEY` is configured
3. Restart Django server after changing environment variables

---

## 📚 Additional Resources

- [Stripe Documentation](https://stripe.com/docs)
- [Stripe API Reference](https://stripe.com/docs/api)
- [Stripe Testing Guide](https://stripe.com/docs/testing)
- [Stripe Webhook Events](https://stripe.com/docs/api/events)
- [Stripe Checkout](https://stripe.com/docs/payments/checkout)
- [Stripe Customer Portal](https://stripe.com/docs/billing/subscriptions/integrating-customer-portal)

---

## 🎉 You're Done!

Your Stripe integration is now complete! Users can:
- ✅ Purchase token packages
- ✅ Subscribe to monthly/yearly plans
- ✅ Manage their subscriptions via Customer Portal
- ✅ Receive automatic token updates
- ✅ Get subscription status updates in real-time

**Need help?** Check the troubleshooting section or contact your development team.

