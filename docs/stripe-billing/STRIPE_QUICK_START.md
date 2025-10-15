# ⚡ Stripe Quick Start - Use Your Data

## 🎯 Your Stripe Data

```
Webhook Secret: whsec_kYH0d9bTpjXpaaVMlVK78LDJqvLCkjz1
Monthly Price:  price_1S0dwrKkH1LI50QC2GhtfzN4  
Yearly Price:   price_1S0dxYKkH1LI50QCEqPZJ6Jq
```

---

## 🚀 Quick Setup (3 Commands)

### 1. Add Webhook Secret
```bash
echo 'STRIPE_WEBHOOK_SECRET=whsec_kYH0d9bTpjXpaaVMlVK78LDJqvLCkjz1' >> .env
```

### 2. Run Migrations
```bash
python src/manage.py migrate
```

### 3. Link Prices
```bash
python src/manage.py shell <<EOF
from billing.models import FullPlan
FullPlan.objects.filter(is_yearly=False).update(stripe_price_id='price_1S0dwrKkH1LI50QC2GhtfzN4')
FullPlan.objects.filter(is_yearly=True).update(stripe_price_id='price_1S0dxYKkH1LI50QCEqPZJ6Jq')
print('✅ Prices linked!')
EOF
```

### 4. Restart Server
```bash
sudo systemctl restart gunicorn
```

**Done!** 🎉

---

## 🧪 Test It

```bash
curl -X POST https://api.fiko.net/api/v1/billing/stripe/checkout-session/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"plan_type": "full", "plan_id": 2}'
```

Expected: Checkout URL returned ✅

---

## 📚 Need More Info?

- **Complete Guide**: SETUP_COMPLETE_GUIDE.md
- **Webhook Setup**: STRIPE_WEBHOOK_SETUP.md  
- **Full Docs**: STRIPE_INTEGRATION_GUIDE.md

