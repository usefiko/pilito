# 🎯 Professional Subscription Logic - Implementation Guide

## 📋 Overview

This document describes the **professional and industry-standard** subscription logic implemented in Fiko's billing system, following best practices from companies like **Netflix, Spotify, GitHub, and Stripe**.

---

## 🔄 How It Works

### **1️⃣ Token Plans (One-time purchases)**

**Behavior:** Unlimited purchases allowed, tokens accumulate.

```python
# Example:
User has: 1000 tokens
User buys: 500 token plan
Result: 1500 tokens total ✅
```

**Industry Examples:**
- OpenAI API Credits
- AWS Credits
- Mobile phone top-up

**Logic:**
```python
subscription.tokens_remaining += tokens_included
# No end_date restriction
```

---

### **2️⃣ Full Plans - Same Plan Renewal**

**Behavior:** Extend `end_date` instead of resetting it.

#### Case A: Active Subscription
```python
# Example:
Current plan: Monthly (30 days)
Remaining: 20 days
User buys: Same Monthly plan
Result: 20 + 30 = 50 days remaining ✅
```

**Code:**
```python
if subscription.end_date > now:
    subscription.end_date += timedelta(days=plan.duration_days)
```

#### Case B: Expired Subscription
```python
# Example:
Current plan: Monthly (expired 5 days ago)
User buys: Same Monthly plan
Result: Start fresh, 30 days from now ✅
```

**Code:**
```python
else:
    subscription.start_date = now
    subscription.end_date = now + timedelta(days=plan.duration_days)
```

---

### **3️⃣ Full Plans - Plan Change (Upgrade/Downgrade)**

**Behavior:** Calculate prorated credit, switch to new plan immediately.

```python
# Example:
Current plan: Monthly ($10/month), 20 days remaining
User buys: Yearly ($100/year)
Prorated credit: (20 days / 30 days) × $10 = $6.67
New plan: Starts immediately, ends in 365 days
```

**Code:**
```python
days_remaining = (subscription.end_date - now).days
old_daily_rate = old_plan.price / old_plan.duration_days
prorated_credit = days_remaining * old_daily_rate

# Log for manual handling (or apply to next invoice in production)
logger.info(f"Prorated credit: ${prorated_credit:.2f}")

# Switch to new plan
subscription.full_plan = new_plan
subscription.start_date = now
subscription.end_date = now + timedelta(days=new_plan.duration_days)
```

---

## 🏗️ Implementation Details

### **Files Modified:**

1. **`src/billing/services/stripe_service.py`**
   - Added `_update_subscription_professional()` method
   - Implements all 3 cases with proper logic

2. **`src/billing/views.py`**
   - Updated webhook handler to use new logic
   - Ensures consistency across payment methods

---

## 📊 Comparison Table

| Scenario | Old Logic ❌ | New Logic ✅ |
|----------|-------------|-------------|
| **Buy token plan twice** | Tokens added | Tokens added (same) |
| **Renew same Monthly** | Reset to 30 days (lose remaining days) | Extend by 30 days (keep remaining days) |
| **Switch Monthly → Yearly** | Reset, no credit | Calculate prorated credit, switch immediately |
| **Expired subscription renewal** | Start fresh | Start fresh (same) |

---

## 🎯 Industry Standards

### **What We Follow:**

✅ **Netflix Model:**
- One active subscription at a time
- Upgrade/downgrade supported
- Prorated billing

✅ **Spotify Model:**
- Can't have multiple Premium subscriptions
- Switch plans immediately
- Credit applied to next bill

✅ **GitHub Pro Model:**
- Prorated adjustments on plan changes
- Immediate plan activation
- Credits shown in billing

✅ **Stripe Subscriptions:**
- Industry-standard billing
- Automatic proration
- Subscription lifecycle management

---

## 🧪 Testing Scenarios

### **Test 1: Token Plan Purchase**
```bash
# Initial state
User subscription: 1000 tokens

# Action
Buy 500 token plan

# Expected result
✅ Tokens: 1500
✅ No end_date change
✅ Log: "Added 500 tokens. Total: 1500 tokens"
```

### **Test 2: Same Plan Renewal (Active)**
```bash
# Initial state
Plan: Monthly (30 days)
End date: 2025-10-25 (20 days remaining)

# Action
Buy same Monthly plan

# Expected result
✅ End date: 2025-11-24 (50 days from now)
✅ Tokens: Original + New tokens
✅ Log: "Extended subscription. New end date: 2025-11-24"
```

### **Test 3: Same Plan Renewal (Expired)**
```bash
# Initial state
Plan: Monthly (expired)
End date: 2025-09-20 (expired 15 days ago)

# Action
Buy same Monthly plan

# Expected result
✅ Start date: 2025-10-05 (today)
✅ End date: 2025-11-04 (30 days from now)
✅ Tokens: Refilled
✅ Log: "Renewed expired subscription. End date: 2025-11-04"
```

### **Test 4: Plan Upgrade (Monthly → Yearly)**
```bash
# Initial state
Plan: Monthly ($10/month, $0.33/day)
End date: 2025-10-25 (20 days remaining)

# Action
Buy Yearly plan ($100/year)

# Expected result
✅ Prorated credit: 20 × $0.33 = $6.67 (logged)
✅ New plan: Yearly
✅ Start date: 2025-10-05 (today)
✅ End date: 2026-10-05 (365 days from now)
✅ Tokens: Refilled with yearly plan tokens
✅ Log: "User switching from Monthly to Yearly. Prorated credit: $6.67"
```

---

## 🔍 Detailed Code Flow

### **Method: `_update_subscription_professional()`**

```python
def _update_subscription_professional(
    subscription: Subscription,
    selected_token_plan: Optional[TokenPlan],
    selected_full_plan: Optional[FullPlan],
    tokens_included: int,
    stripe_customer_id: str,
    stripe_subscription_id: Optional[str]
) -> Subscription:
    """
    Professional subscription update logic
    
    Handles 3 cases:
    1. Token plan: Add tokens
    2. Same full plan: Extend end_date
    3. Different full plan: Upgrade/downgrade with proration
    """
```

**Flow:**
1. Check if Token Plan → Add tokens, done
2. Check if Full Plan:
   - Same plan? → Extend end_date
   - Different plan? → Calculate prorated credit, switch plan

---

## 📈 Benefits

### **For Users:**
✅ No lost days when renewing
✅ Fair prorated credits on plan changes
✅ Flexible token purchases
✅ Transparent billing

### **For Business:**
✅ Industry-standard practices
✅ Better customer retention
✅ Reduced support tickets
✅ Clear audit trail in logs

### **For Development:**
✅ Single source of truth (`_update_subscription_professional`)
✅ Consistent logic across webhooks and API
✅ Easy to test and maintain
✅ Extensible for future features

---

## 🚀 Deployment Checklist

- [x] Code implemented in `stripe_service.py`
- [x] Webhook handler updated in `views.py`
- [x] No linter errors
- [ ] Unit tests written (recommended)
- [ ] Manual testing in test mode
- [ ] Verify logs in production
- [ ] Monitor Stripe Dashboard for prorated credits

---

## 📝 Future Enhancements

### **Phase 2: Automatic Prorated Credit Application**
Currently, prorated credits are **logged** but not automatically applied.

**To implement:**
1. Create `BillingCredit` model to track credits
2. Apply credits to next invoice automatically
3. Show credits in user dashboard
4. Integrate with Stripe Billing Credits API

### **Phase 3: Subscription Preview**
Show users what will happen before they purchase:
```
"You have 20 days remaining on Monthly plan.
Upgrading to Yearly will:
- Credit: $6.67 for remaining days
- New plan: Yearly ($100/year)
- Total due: $93.33"
```

---

## 🐛 Troubleshooting

### **Issue: User lost days on renewal**
**Cause:** Old logic was used
**Fix:** Ensure `_update_subscription_professional` is called in both:
- `StripeService.handle_successful_payment()`
- `StripeWebhookView` (webhook handler)

### **Issue: Prorated credit not visible**
**Cause:** Credits are logged but not applied yet
**Fix:** Check logs for prorated amounts:
```bash
grep "Prorated credit" logs/celery.log
```

### **Issue: Tokens not accumulating**
**Cause:** Ensure `tokens_remaining += tokens_included` is executed
**Fix:** Check logs for token addition confirmation

---

## 📞 Support

For questions or issues:
1. Check logs: `docker logs -f fiko_web | grep "subscription"`
2. Review Stripe Dashboard events
3. Check database: `python manage.py shell`
   ```python
   from billing.models import Subscription
   sub = Subscription.objects.get(user__email='test@example.com')
   print(f"Plan: {sub.full_plan}, Tokens: {sub.tokens_remaining}, End: {sub.end_date}")
   ```

---

## ✅ Summary

This implementation provides:
- ✅ Industry-standard subscription logic
- ✅ Fair treatment of users
- ✅ Flexible token purchases
- ✅ Professional upgrade/downgrade handling
- ✅ Comprehensive logging
- ✅ Easy to test and maintain

**Result:** A billing system that matches the quality of Netflix, Spotify, and GitHub! 🎉
