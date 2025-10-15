# 🎨 Subscription UX Guide - Frontend Implementation

## 📦 Backend Changes Deployed

### 1. **Prevent Duplicate Plan Purchase**
Users can no longer buy the same plan twice. The checkout will fail with an error message.

### 2. **Cancellation Status Exposed**
Backend now sends cancellation info to frontend via API.

---

## 🔌 API Changes

### **GET /api/v1/billing/subscription/**

**New Fields:**
```json
{
  "id": 123,
  "full_plan_details": {
    "id": 2,
    "name": "month",
    "is_yearly": false
  },
  "is_active": true,
  "status": "active",
  "cancel_at_period_end": true,  // ✨ NEW
  "canceled_at": "2025-10-05T11:57:49Z",  // ✨ NEW
  "end_date": "2025-12-04",
  "days_remaining": 60
}
```

**cancel_at_period_end:**
- `true` → Subscription will end at `end_date` (user clicked cancel)
- `false` → Subscription will auto-renew

**canceled_at:**
- `null` → Not canceled
- `"2025-10-05T11:57:49Z"` → Canceled on this date

---

### **GET /api/v1/billing/payments/?page=1**

**New Field:**
```json
{
  "results": [
    {
      "id": 97,
      "plan_name": "month",
      "amount": "15.00",
      "status": "completed",
      "is_subscription_canceled": true,  // ✨ NEW
      "created_at": "2025-10-05T11:56:29Z"
    }
  ]
}
```

---

### **POST /api/v1/billing/stripe/checkout-session/**

**New Error Response:**
```json
{
  "error": "You already have this plan active. To change plans, please cancel your current subscription first."
}
```

**When does this happen?**
- User has **Monthly plan** → Tries to buy **Monthly plan** again
- User has **Yearly plan** → Tries to buy **Yearly plan** again

**When is it allowed?**
- User has **Monthly plan** → Tries to buy **Yearly plan** ✅ (upgrade)
- User has **Yearly plan** → Tries to buy **Monthly plan** ✅ (downgrade)
- User **canceled** Monthly → Tries to buy **Monthly plan** ✅ (re-subscribe)

---

## 🎨 Frontend UX Recommendations

### **1. Show Cancellation Warning**

**Where:** Billing & Plans page, above subscription details

```tsx
// Example React Component
function SubscriptionStatus({ subscription }) {
  if (!subscription.cancel_at_period_end) {
    return null; // No warning needed
  }

  return (
    <div className="bg-orange-50 border border-orange-200 rounded-lg p-4 mb-4">
      <div className="flex items-start">
        <svg className="h-5 w-5 text-orange-400 mt-0.5" /* warning icon */>
        <div className="ml-3">
          <h3 className="text-sm font-medium text-orange-800">
            Subscription Scheduled for Cancellation
          </h3>
          <div className="mt-2 text-sm text-orange-700">
            <p>
              Your plan will remain active until{' '}
              <strong>{formatDate(subscription.end_date)}</strong>.
              After that, you'll be switched to the Free Trial plan.
            </p>
          </div>
          <div className="mt-4">
            <button
              onClick={handleReactivate}
              className="text-sm font-medium text-orange-800 hover:text-orange-900"
            >
              Reactivate subscription →
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
```

---

### **2. Update Plan Purchase Buttons**

**Where:** Plan cards / pricing table

```tsx
function PlanCard({ plan, currentSubscription }) {
  // Check if user already has this exact plan (and it's not canceled)
  const hasThisPlan = 
    currentSubscription?.full_plan_details?.id === plan.id &&
    currentSubscription?.is_active &&
    !currentSubscription?.cancel_at_period_end;

  // Check if user can upgrade/downgrade
  const canUpgrade = 
    currentSubscription?.full_plan_details?.is_yearly === false && 
    plan.is_yearly === true;
  
  const canDowngrade = 
    currentSubscription?.full_plan_details?.is_yearly === true && 
    plan.is_yearly === false;

  return (
    <div className="plan-card">
      <h3>{plan.name}</h3>
      <p>${plan.price_en}/{plan.is_yearly ? 'year' : 'month'}</p>
      
      {hasThisPlan ? (
        <button disabled className="btn-disabled">
          Current Plan
        </button>
      ) : canUpgrade ? (
        <button onClick={() => purchasePlan(plan.id)} className="btn-primary">
          Upgrade to Yearly
        </button>
      ) : canDowngrade ? (
        <button onClick={() => purchasePlan(plan.id)} className="btn-secondary">
          Switch to Monthly
        </button>
      ) : (
        <button onClick={() => purchasePlan(plan.id)} className="btn-primary">
          Select Plan
        </button>
      )}
    </div>
  );
}
```

---

### **3. Handle Checkout Error**

**Where:** Checkout flow

```tsx
async function handlePurchase(planId) {
  try {
    const response = await fetch('/api/v1/billing/stripe/checkout-session/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        plan_type: 'full',
        plan_id: planId,
      }),
    });

    const data = await response.json();

    if (!response.ok) {
      // Show error to user
      showToast('error', data.error);
      
      // If error is "already have this plan", show reactivation option
      if (data.error.includes('already have this plan')) {
        showReactivationModal();
      }
      return;
    }

    // Redirect to Stripe checkout
    window.location.href = data.url;
  } catch (error) {
    showToast('error', 'Something went wrong. Please try again.');
  }
}
```

---

### **4. Show Cancellation in Billing History**

**Where:** Payment history table

```tsx
function PaymentHistoryTable({ payments }) {
  return (
    <table>
      <thead>
        <tr>
          <th>Plan</th>
          <th>Amount</th>
          <th>Date</th>
          <th>Status</th>
        </tr>
      </thead>
      <tbody>
        {payments.map(payment => (
          <tr key={payment.id}>
            <td>{payment.plan_name}</td>
            <td>${payment.amount}</td>
            <td>{formatDate(payment.created_at)}</td>
            <td>
              <span className={`badge badge-${payment.status}`}>
                {payment.status}
              </span>
              {payment.is_subscription_canceled && (
                <span className="ml-2 text-xs text-orange-600">
                  (Canceled)
                </span>
              )}
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
```

---

### **5. Reactivation Flow**

**Option A: Via Stripe Portal** (Recommended)
```tsx
function handleReactivate() {
  // Open Stripe Customer Portal
  window.location.href = '/api/v1/billing/stripe/customer-portal/';
  
  // User can click "Renew subscription" in Stripe portal
}
```

**Option B: New Purchase** (If canceled)
```tsx
function handleReactivate() {
  // Only works if subscription is canceled
  if (subscription.cancel_at_period_end) {
    // User needs to go through regular checkout flow
    // Backend will allow re-purchase of same plan
    window.location.href = '/billing/plans';
  }
}
```

---

## 🧪 Testing Checklist

### **Scenario 1: Prevent Duplicate Purchase**
1. ✅ Buy Monthly plan
2. ✅ Try to buy Monthly again → Should show error
3. ✅ Try to buy Yearly → Should work (upgrade)

### **Scenario 2: Cancellation Warning**
1. ✅ Buy Monthly plan
2. ✅ Cancel from Stripe portal
3. ✅ Return to dashboard → Should show orange warning
4. ✅ Check `/api/v1/billing/subscription/` → `cancel_at_period_end: true`

### **Scenario 3: Billing History**
1. ✅ Buy Monthly plan
2. ✅ Cancel subscription
3. ✅ Check billing history → Payment should show "(Canceled)" badge

### **Scenario 4: Reactivation**
1. ✅ Cancel subscription
2. ✅ Click "Reactivate" → Opens Stripe portal
3. ✅ Click "Renew subscription" in Stripe
4. ✅ Return to dashboard → Warning should disappear

### **Scenario 5: Re-Purchase After Cancel**
1. ✅ Cancel Monthly plan
2. ✅ Wait or manually deactivate
3. ✅ Try to buy Monthly again → Should work

---

## 📊 UX Improvements Summary

| Before | After |
|--------|-------|
| User can buy same plan multiple times | ❌ Prevented with error message |
| No indication of cancellation | ✅ Orange warning banner |
| Billing history doesn't show cancel | ✅ "(Canceled)" badge shown |
| Button always says "Buy Plan" | ✅ Smart buttons: "Current Plan", "Upgrade", "Switch" |

---

## 🔗 Related APIs

- **Get Subscription:** `GET /api/v1/billing/subscription/`
- **Get Payments:** `GET /api/v1/billing/payments/`
- **Create Checkout:** `POST /api/v1/billing/stripe/checkout-session/`
- **Customer Portal:** `POST /api/v1/billing/stripe/customer-portal/`

---

## 🆘 Support

If users encounter the "already have this plan" error:
1. Check if they want to upgrade (yearly) instead
2. If not, guide them to cancel current subscription first
3. Or let them wait until current period ends

---

**Last Updated:** October 5, 2025
**Backend Version:** 3f743e3
