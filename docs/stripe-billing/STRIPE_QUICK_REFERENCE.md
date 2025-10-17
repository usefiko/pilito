# ⚡ Stripe Integration - Quick Reference Card

## 🎯 Essential Commands

```bash
# 1. Run quick setup
./stripe_quick_setup.sh

# 2. Sync plans to Stripe
python src/manage.py sync_stripe_products --dry-run
python src/manage.py sync_stripe_products

# 3. Test webhooks locally
stripe listen --forward-to localhost:8000/billing/stripe/webhook/

# 4. Check subscription status
python src/manage.py check_subscription_status --dry-run
```

## 📡 API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/billing/stripe/checkout-session/` | POST | Create checkout session |
| `/billing/stripe/customer-portal/` | POST | Open customer portal |
| `/billing/stripe/webhook/` | POST | Receive Stripe webhooks |
| `/billing/plans/` | GET | List all plans |
| `/billing/plans/token/` | GET | List token plans |
| `/billing/plans/full/` | GET | List subscription plans |

## 💳 Test Cards

| Card | Result |
|------|--------|
| `4242 4242 4242 4242` | ✅ Success |
| `4000 0025 0000 3155` | 🔒 3D Secure |
| `4000 0000 0000 9995` | ❌ Declined |

## 🔑 Environment Variables (Required)

```bash
STRIPE_PUBLISHABLE_KEY=pk_test_...
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
STRIPE_ENABLED=True
STRIPE_TEST_MODE=True
```

## 📱 Frontend Code Example

```javascript
// Create checkout session
const response = await fetch('/api/billing/stripe/checkout-session/', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${token}`,
  },
  body: JSON.stringify({
    plan_type: 'full',  // or 'token'
    plan_id: 1,
  }),
});

const { url } = await response.json();
window.location.href = url;  // Redirect to Stripe
```

## 🔗 Important Links

- **Get API Keys**: https://dashboard.stripe.com/apikeys
- **Configure Webhooks**: https://dashboard.stripe.com/webhooks
- **View Payments**: https://dashboard.stripe.com/payments
- **Stripe Docs**: https://stripe.com/docs

## 🪝 Webhook Configuration

1. Go to: https://dashboard.stripe.com/webhooks
2. Add endpoint: `https://api.pilito.com/billing/stripe/webhook/`
3. Select events:
   - ✅ checkout.session.completed
   - ✅ customer.subscription.created
   - ✅ customer.subscription.updated
   - ✅ customer.subscription.deleted
   - ✅ invoice.paid
   - ✅ invoice.payment_failed
4. Copy webhook secret → Add to `.env` as `STRIPE_WEBHOOK_SECRET`

## 🚀 Quick Start (3 Steps)

### 1. Install & Configure
```bash
pip install stripe
# Add Stripe keys to .env
```

### 2. Test Locally
```bash
# Terminal 1
python src/manage.py runserver

# Terminal 2
stripe listen --forward-to localhost:8000/billing/stripe/webhook/
```

### 3. Test Purchase
```bash
curl -X POST http://localhost:8000/billing/stripe/checkout-session/ \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"plan_type": "full", "plan_id": 1}'
```

## 🐛 Troubleshooting

| Issue | Solution |
|-------|----------|
| "Stripe is not enabled" | Set `STRIPE_ENABLED=True` |
| Webhook not working | Check webhook URL and secret |
| Payment succeeds but no subscription | Check webhook logs |
| Customer Portal error | Verify `stripe_customer_id` exists |

## 📊 Monitoring

```bash
# Check Django logs
tail -f src/logs/django.log | grep -i stripe

# Check subscriptions
python src/manage.py check_subscription_status

# View payments in Stripe Dashboard
open https://dashboard.stripe.com/payments
```

## 📚 Documentation Files

- **📘 STRIPE_INTEGRATION_GUIDE.md** - Complete guide
- **📄 STRIPE_INTEGRATION_SUMMARY.md** - Summary
- **⚡ STRIPE_QUICK_REFERENCE.md** - This file
- **🔧 STRIPE_ENVIRONMENT_VARIABLES.txt** - Env vars

## ✅ Implementation Checklist

- [x] Backend integration complete
- [ ] Environment variables configured
- [ ] Webhook configured in Stripe
- [ ] Test payment successful
- [ ] Frontend integration complete
- [ ] Production keys configured
- [ ] Production webhook configured
- [ ] Monitoring set up

---

**Need help?** Read `STRIPE_INTEGRATION_GUIDE.md` for detailed instructions.

