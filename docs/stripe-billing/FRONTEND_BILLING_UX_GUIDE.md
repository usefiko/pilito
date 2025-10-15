# 🎨 Frontend Billing UX Guide - Smart Upgrade/Downgrade

## 📋 Overview

راهنمای طراحی UX حرفه‌ای برای صفحه Billing & Plans با قابلیت Upgrade/Downgrade هوشمند.

---

## 🎯 هدف

ساده‌سازی فرآیند تغییر plan برای کاربران با نمایش **فقط گزینه‌های مرتبط** به جای نمایش همه plan‌ها.

---

## 🌍 استاندارد صنعت (Industry Best Practices)

### ✅ **رویکرد حرفه‌ای (توصیه می‌شه):**

#### **Netflix Model:**
```
Current Plan: Basic
↓
[Upgrade to Standard] [Upgrade to Premium]
```

#### **Spotify Model:**
```
Current Plan: Premium Individual
↓
[Switch to Premium Family] [Switch to Premium Duo]
(نه downgrade، فقط تغییر به plan‌های دیگه)
```

#### **GitHub Model:**
```
Current Plan: Free
↓
[Upgrade to Pro] [Upgrade to Team]

Current Plan: Pro
↓
[Upgrade to Team] [Downgrade to Free]
```

---

## 🎯 پیشنهاد برای Fiko

### **رویکرد 1: Smart Upgrade/Downgrade (توصیه می‌کنم) ✅**

نمایش **فقط یک دکمه** بر اساس plan فعلی:

```
┌─────────────────────────────────────────┐
│ Current Plan: Monthly                   │
│ $15/month • 5000 tokens • 29 days left  │
│                                         │
│ ┌─────────────────────────────────┐    │
│ │  🚀 Upgrade to Yearly           │    │
│ │  $150/year • 100,000 tokens     │    │
│ │  💰 Save $30/year (17% off)     │    │
│ │  ✅ +20 days prorated credit    │    │
│ │                                 │    │
│ │  [Upgrade Now →]                │    │
│ └─────────────────────────────────┘    │
│                                         │
│ [Cancel Subscription]                   │
└─────────────────────────────────────────┘
```

---

### **رویکرد 2: مقایسه دو Plan (محبوب‌تر) ✅✅**

نمایش **Current + Recommended** برای مقایسه:

```
┌──────────────────┬──────────────────────────────┐
│  Current Plan    │  Recommended Plan            │
├──────────────────┼──────────────────────────────┤
│  Monthly         │  Yearly                      │
│  $15/month       │  $150/year                   │
│  5,000 tokens    │  100,000 tokens              │
│                  │  🏷️ Recommended              │
│  ✅ Active       │  💰 Save $30/year            │
│  29 days left    │  ✅ Prorated credit: $14.50  │
│                  │                              │
│  [Manage]        │  [Upgrade Now →]             │
└──────────────────┴──────────────────────────────┘

[Cancel Subscription]
```

---

### **رویکرد 3: همه Plans با Highlight (کمتر توصیه می‌شه) ⚠️**

نمایش همه plans ولی با هایلایت current:

```
┌─────────────────────────────────────────┐
│ Current Plan                            │
├─────────────────────────────────────────┤
│ ○ Monthly - $15/month                   │
│   5000 tokens • ✅ Your current plan    │
│                                         │
│ ○ Yearly - $150/year (Recommended)      │
│   100,000 tokens • 💰 Save $30          │
│   [Upgrade]                             │
└─────────────────────────────────────────┘
```

**مشکل:** کاربر confused میشه - "پس چرا plan فعلیم رو نشون میده؟"

---

## 🎨 طراحی پیشنهادی (Recommended Design)

### **حالت 1: کاربر Monthly داره**

```jsx
<div className="billing-page">
  {/* Current Plan Section */}
  <div className="current-plan-card">
    <div className="plan-header">
      <h3>Your Current Plan</h3>
      <button className="cancel-btn">Cancel Subscription</button>
    </div>
    
    <div className="plan-details">
      <div className="plan-badge">Monthly</div>
      <div className="plan-price">$15 / month</div>
      <div className="plan-tokens">5,000 tokens included</div>
    </div>
    
    <div className="plan-status">
      <ProgressBar value={29} max={30} />
      <p>29 days remaining until renewal</p>
      <p className="renewal-date">Active until 3 Nov 2025</p>
    </div>
  </div>
  
  {/* Upgrade Recommendation */}
  <div className="upgrade-card recommended">
    <div className="badge-recommended">⭐ Recommended</div>
    
    <h3>Upgrade to Yearly Plan</h3>
    <p className="subtitle">Save money with annual billing</p>
    
    <div className="comparison">
      <div className="comparison-item">
        <span className="label">Price</span>
        <span className="value">$150 / year</span>
        <span className="savings">💰 Save $30/year (17% off)</span>
      </div>
      
      <div className="comparison-item">
        <span className="label">Tokens</span>
        <span className="value">100,000 tokens</span>
        <span className="vs">vs. 60,000 tokens/year on monthly</span>
      </div>
      
      <div className="comparison-item">
        <span className="label">Your unused time</span>
        <span className="value">29 days remaining</span>
        <span className="credit">✅ $14.50 prorated credit applied</span>
      </div>
    </div>
    
    <button className="btn-upgrade primary">
      Upgrade to Yearly - Pay $135.50
    </button>
    
    <p className="fine-print">
      Your monthly plan will be cancelled and you'll be charged $135.50 
      (after $14.50 credit for unused days)
    </p>
  </div>
  
  {/* Token Add-ons */}
  <div className="token-addons-section">
    <h3>Need more tokens?</h3>
    <div className="token-cards">
      <TokenCard tokens={5000} price={10} />
      <TokenCard tokens={10000} price={18} />
      <TokenCard tokens={50000} price={80} />
    </div>
  </div>
</div>
```

---

### **حالت 2: کاربر Yearly داره**

```jsx
<div className="billing-page">
  {/* Current Plan Section */}
  <div className="current-plan-card premium">
    <div className="plan-header">
      <h3>Your Current Plan</h3>
      <button className="cancel-btn">Cancel Subscription</button>
    </div>
    
    <div className="plan-details">
      <div className="plan-badge gold">⭐ Yearly Plan</div>
      <div className="plan-price">$150 / year</div>
      <div className="plan-tokens">100,000 tokens included</div>
    </div>
    
    <div className="plan-status">
      <ProgressBar value={335} max={365} />
      <p>335 days remaining until renewal</p>
      <p className="renewal-date">Active until 5 Oct 2026</p>
    </div>
  </div>
  
  {/* Downgrade Option (Less Prominent) */}
  <details className="downgrade-section">
    <summary>Want to switch to Monthly?</summary>
    
    <div className="downgrade-card">
      <h4>Switch to Monthly Plan</h4>
      <p className="warning">
        ⚠️ You'll lose the yearly discount and pay more per month
      </p>
      
      <div className="comparison-table">
        <table>
          <tr>
            <th>Plan</th>
            <th>Price</th>
            <th>Tokens/Month</th>
          </tr>
          <tr className="current">
            <td>Yearly (Current)</td>
            <td>$12.50/month</td>
            <td>8,333 tokens</td>
          </tr>
          <tr>
            <td>Monthly</td>
            <td>$15/month</td>
            <td>5,000 tokens</td>
          </tr>
        </table>
      </div>
      
      <div className="refund-info">
        <h5>What happens to unused time?</h5>
        <p>
          You have 335 days remaining worth $137.67. 
          This will be credited to your account for future purchases.
        </p>
      </div>
      
      <button className="btn-downgrade secondary">
        Switch to Monthly (Keep $137.67 credit)
      </button>
    </div>
  </details>
  
  {/* Token Add-ons */}
  <div className="token-addons-section">
    <h3>Need more tokens?</h3>
    <div className="token-cards">
      <TokenCard tokens={5000} price={10} />
      <TokenCard tokens={10000} price={18} />
      <TokenCard tokens={50000} price={80} />
    </div>
  </div>
</div>
```

---

## 🔧 API Integration

### **1. دریافت اطلاعات Current Plan**

```javascript
// GET /api/v1/billing/subscription/
const response = await fetch('/api/v1/billing/subscription/', {
  headers: {
    'Authorization': `Bearer ${token}`
  }
});

const data = await response.json();

/*
Expected Response:
{
  "subscription": {
    "id": "abc123",
    "full_plan": {
      "id": 1,
      "name": "Monthly Pro",
      "price_en": 15.00,
      "tokens_included": 5000,
      "duration_days": 30,
      "is_yearly": false
    },
    "start_date": "2025-10-05T12:00:00Z",
    "end_date": "2025-11-03T12:00:00Z",
    "tokens_remaining": 4800,
    "is_active": true,
    "status": "active"
  },
  "days_remaining": 29,
  "recommended_upgrade": {
    "plan": {
      "id": 2,
      "name": "Yearly Pro",
      "price_en": 150.00,
      "tokens_included": 100000,
      "duration_days": 365,
      "is_yearly": true
    },
    "savings": {
      "annual_savings": 30.00,
      "percentage": 17,
      "prorated_credit": 14.50,
      "final_price": 135.50
    }
  }
}
*/
```

---

### **2. محاسبه Prorated Credit (Frontend)**

```javascript
function calculateProratedCredit(subscription) {
  const now = new Date();
  const endDate = new Date(subscription.end_date);
  const startDate = new Date(subscription.start_date);
  
  // Calculate days remaining
  const daysRemaining = Math.ceil((endDate - now) / (1000 * 60 * 60 * 24));
  
  // Calculate total days in current plan
  const totalDays = Math.ceil((endDate - startDate) / (1000 * 60 * 60 * 24));
  
  // Calculate daily rate
  const dailyRate = subscription.full_plan.price_en / totalDays;
  
  // Calculate prorated credit
  const proratedCredit = daysRemaining * dailyRate;
  
  return {
    daysRemaining,
    dailyRate: dailyRate.toFixed(2),
    proratedCredit: proratedCredit.toFixed(2)
  };
}

// Usage:
const credit = calculateProratedCredit(subscription);
console.log(`You have ${credit.daysRemaining} days remaining`);
console.log(`Prorated credit: $${credit.proratedCredit}`);
```

---

### **3. درخواست Upgrade/Downgrade**

```javascript
// Upgrade to Yearly
async function upgradePlan(newPlanId) {
  const response = await fetch('/api/v1/billing/stripe/checkout/', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      plan_id: newPlanId,
      plan_type: 'full_plan',
      success_url: window.location.origin + '/billing/success',
      cancel_url: window.location.origin + '/billing'
    })
  });
  
  const data = await response.json();
  
  if (data.url) {
    // Redirect to Stripe Checkout
    window.location.href = data.url;
  }
}

// Usage:
<button onClick={() => upgradePlan(yearlyPlan.id)}>
  Upgrade to Yearly
</button>
```

---

## 📊 UI States

### **State 1: No Subscription (Free/Trial)**

```
┌─────────────────────────────────────────┐
│ 🎉 Choose Your Plan                     │
│                                         │
│ ┌──────────────┐  ┌──────────────────┐ │
│ │   Monthly    │  │   Yearly ⭐      │ │
│ │   $15/mo     │  │   $150/yr        │ │
│ │   5K tokens  │  │   100K tokens    │ │
│ │              │  │   Save $30!      │ │
│ │  [Select]    │  │  [Select]        │ │
│ └──────────────┘  └──────────────────┘ │
└─────────────────────────────────────────┘
```

---

### **State 2: Active Monthly Subscription**

```
┌─────────────────────────────────────────┐
│ Current Plan: Monthly                   │
│ ✅ Active • 29 days left                │
│                                         │
│ ╔═══════════════════════════════════╗  │
│ ║  💡 Upgrade to Yearly & Save!     ║  │
│ ║  • Save $30/year (17% discount)   ║  │
│ ║  • Get $14.50 credit for unused   ║  │
│ ║    days                            ║  │
│ ║  • Pay only $135.50 now           ║  │
│ ║                                    ║  │
│ ║  [Upgrade to Yearly →]            ║  │
│ ╚═══════════════════════════════════╝  │
└─────────────────────────────────────────┘
```

---

### **State 3: Active Yearly Subscription**

```
┌─────────────────────────────────────────┐
│ Current Plan: Yearly ⭐                  │
│ ✅ Active • 335 days left               │
│                                         │
│ 🎉 You're on the best plan!            │
│                                         │
│ [▼ Want to switch to Monthly?]         │
└─────────────────────────────────────────┘
```

---

### **State 4: Expired Subscription**

```
┌─────────────────────────────────────────┐
│ ⚠️ Your subscription has expired        │
│                                         │
│ Previous Plan: Monthly                  │
│ Expired: 5 days ago                     │
│                                         │
│ ┌──────────────┐  ┌──────────────────┐ │
│ │  Renew       │  │  Upgrade to      │ │
│ │  Monthly     │  │  Yearly ⭐       │ │
│ │  $15/mo      │  │  $150/yr         │ │
│ │              │  │  Save $30!       │ │
│ │  [Renew]     │  │  [Upgrade]       │ │
│ └──────────────┘  └──────────────────┘ │
└─────────────────────────────────────────┘
```

---

## 🎯 UX Best Practices

### ✅ **DO:**

1. **نمایش واضح savings:**
   ```
   💰 Save $30/year (17% off)
   ```

2. **نمایش prorated credit:**
   ```
   ✅ You'll get $14.50 credit for your unused 29 days
   ```

3. **نمایش قیمت نهایی:**
   ```
   Total: $135.50 (after $14.50 credit)
   ```

4. **مقایسه واضح:**
   ```
   Monthly: $15/mo × 12 = $180/year
   Yearly:  $150/year (Save $30!)
   ```

5. **Call-to-action واضح:**
   ```
   [Upgrade to Yearly - Pay $135.50 →]
   ```

---

### ❌ **DON'T:**

1. **نمایش همزمان همه plans بدون context**
   - کاربر confused میشه

2. **پنهان کردن هزینه‌ها:**
   - همیشه قیمت نهایی رو نشون بده

3. **استفاده از terminology پیچیده:**
   - ❌ "Prorated adjustment"
   - ✅ "Credit for unused days"

4. **فشار برای upgrade:**
   - ❌ "You're missing out!"
   - ✅ "Save $30 with yearly plan"

5. **نمایش downgrade به عنوان گزینه اصلی:**
   - Downgrade باید کمتر prominent باشه

---

## 📱 Responsive Design

### **Mobile View:**

```
┌─────────────────────┐
│ Current Plan        │
│ Monthly • 29d left  │
│ ─────────────────── │
│                     │
│ ⭐ Upgrade Yearly   │
│ $150/yr             │
│ 💰 Save $30         │
│ ✅ +$14.50 credit   │
│                     │
│ [Upgrade Now]       │
│                     │
│ [Cancel Plan]       │
└─────────────────────┘
```

---

## 🔄 User Flow

### **Upgrade Flow:**

```
1. User sees billing page
   ↓
2. "Upgrade to Yearly" recommendation shown
   ↓
3. User clicks "Upgrade Now"
   ↓
4. Modal/Page shows:
   - Current plan details
   - New plan details
   - Prorated credit calculation
   - Final price
   - Confirmation checkbox
   ↓
5. User confirms → Redirect to Stripe
   ↓
6. Payment successful → Backend applies professional logic
   ↓
7. Redirect back → Show success message
   ↓
8. Updated billing page with new plan
```

---

## 💻 Code Examples

### **React Component Structure:**

```jsx
// BillingPage.jsx
import { useState, useEffect } from 'react';
import CurrentPlanCard from './CurrentPlanCard';
import UpgradeCard from './UpgradeCard';
import TokenAddons from './TokenAddons';

export default function BillingPage() {
  const [subscription, setSubscription] = useState(null);
  const [loading, setLoading] = useState(true);
  
  useEffect(() => {
    fetchSubscription();
  }, []);
  
  const fetchSubscription = async () => {
    const res = await fetch('/api/v1/billing/subscription/');
    const data = await res.json();
    setSubscription(data);
    setLoading(false);
  };
  
  if (loading) return <LoadingSpinner />;
  
  const isMonthly = !subscription.full_plan?.is_yearly;
  const isYearly = subscription.full_plan?.is_yearly;
  
  return (
    <div className="billing-page">
      <CurrentPlanCard subscription={subscription} />
      
      {isMonthly && (
        <UpgradeCard 
          currentPlan={subscription.full_plan}
          recommendedPlan={subscription.recommended_upgrade}
        />
      )}
      
      {isYearly && (
        <DowngradeSection 
          currentPlan={subscription.full_plan}
        />
      )}
      
      <TokenAddons />
    </div>
  );
}
```

---

### **UpgradeCard Component:**

```jsx
// UpgradeCard.jsx
export default function UpgradeCard({ currentPlan, recommendedPlan }) {
  const { plan, savings } = recommendedPlan;
  
  const handleUpgrade = async () => {
    const response = await fetch('/api/v1/billing/stripe/checkout/', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('token')}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        plan_id: plan.id,
        plan_type: 'full_plan',
        success_url: `${window.location.origin}/billing/success`,
        cancel_url: `${window.location.origin}/billing`
      })
    });
    
    const data = await response.json();
    
    if (data.url) {
      window.location.href = data.url;
    }
  };
  
  return (
    <div className="upgrade-card">
      <div className="badge">⭐ Recommended</div>
      
      <h3>Upgrade to {plan.name}</h3>
      
      <div className="savings-highlight">
        <span className="amount">💰 Save ${savings.annual_savings}/year</span>
        <span className="percentage">({savings.percentage}% off)</span>
      </div>
      
      <div className="comparison-grid">
        <div className="comparison-item">
          <span className="label">Price</span>
          <span className="value">${plan.price_en}/year</span>
          <span className="vs">vs. ${currentPlan.price_en * 12}/year</span>
        </div>
        
        <div className="comparison-item">
          <span className="label">Tokens</span>
          <span className="value">{plan.tokens_included.toLocaleString()}</span>
          <span className="vs">vs. {(currentPlan.tokens_included * 12).toLocaleString()}</span>
        </div>
        
        <div className="comparison-item">
          <span className="label">Your unused time</span>
          <span className="credit">✅ ${savings.prorated_credit} credit applied</span>
        </div>
      </div>
      
      <button 
        className="btn-upgrade"
        onClick={handleUpgrade}
      >
        Upgrade Now - Pay ${savings.final_price}
      </button>
      
      <p className="fine-print">
        Your monthly plan will be cancelled and you'll be charged ${savings.final_price} 
        (after ${savings.prorated_credit} credit for unused days)
      </p>
    </div>
  );
}
```

---

## 🎨 CSS Examples

```css
/* Upgrade Card */
.upgrade-card {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border-radius: 12px;
  padding: 24px;
  margin: 24px 0;
  box-shadow: 0 10px 30px rgba(102, 126, 234, 0.3);
}

.upgrade-card .badge {
  display: inline-block;
  background: rgba(255, 255, 255, 0.2);
  padding: 4px 12px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 600;
  margin-bottom: 12px;
}

.savings-highlight {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 24px;
  font-weight: bold;
  margin: 16px 0;
}

.comparison-grid {
  background: rgba(255, 255, 255, 0.1);
  border-radius: 8px;
  padding: 16px;
  margin: 16px 0;
}

.comparison-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 12px 0;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.comparison-item:last-child {
  border-bottom: none;
}

.btn-upgrade {
  width: 100%;
  background: white;
  color: #667eea;
  border: none;
  padding: 16px;
  border-radius: 8px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: transform 0.2s;
}

.btn-upgrade:hover {
  transform: scale(1.02);
}

/* Downgrade Section */
.downgrade-section {
  margin: 24px 0;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  padding: 16px;
}

.downgrade-section summary {
  cursor: pointer;
  font-weight: 600;
  color: #666;
}

.downgrade-card {
  margin-top: 16px;
  padding: 16px;
  background: #f9f9f9;
  border-radius: 8px;
}

.downgrade-card .warning {
  color: #f59e0b;
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 12px 0;
}
```

---

## ✅ Summary

### **توصیه نهایی:**

1. ✅ **برای Monthly → Yearly:** نمایش بزرگ و highlighted
2. ✅ **برای Yearly → Monthly:** نمایش کوچک در `<details>` یا modal
3. ✅ **محاسبه prorated credit** در frontend برای شفافیت
4. ✅ **نمایش savings واضح** برای ترغیب کاربر
5. ✅ **Call-to-action صریح** با قیمت نهایی

---

### **مزایا:**

- 🎯 User-friendly: کاربر confused نمیشه
- 💰 Transparent: همه هزینه‌ها واضحه
- 🚀 Conversion-optimized: افزایش احتمال upgrade
- 📱 Responsive: روی موبایل هم خوب کار می‌کنه
- ✅ Industry-standard: مثل Netflix و Spotify

---

**این راهنما رو به frontend developer بده تا صفحه Billing & Plans رو professional کنه! 🎉**
