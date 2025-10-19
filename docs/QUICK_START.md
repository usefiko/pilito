# 🚀 Billing API Quick Start Guide

Get up and running with the billing and subscription APIs in 5 minutes!

## 📋 Prerequisites

- Django project running with the billing app installed
- User authentication working (JWT tokens)
- Database migrations applied

## ⚡ Quick Setup

### 1. Apply Migrations

```bash
cd src/
python manage.py migrate billing
```

### 2. Create Subscription Plans

**Option A: Django Admin (Recommended for beginners)**
1. Go to `/admin/billing/subscriptionplan/`
2. Click "Add Subscription Plan"
3. Create plans like:

| Name | Price | Tokens | Duration (days) | Recurring |
|------|-------|--------|-----------------|-----------|
| 1M Tokens | $10 | 1,000,000 | null | No |
| 5M Tokens | $40 | 5,000,000 | null | No |
| Monthly Basic | $15 | 1,000,000 | 30 | Yes |

**Option B: Django Shell**
```python
python manage.py shell

from billing.models import TokenPlan

# Create sample plans
plans = [
    TokenPlan.objects.create(
        name="1M Tokens",
        price_en=10.00,
        price_tr=10.00,
        price_ar=10.00,
        tokens_included=1000000,
        description="Perfect for small teams"
    ),
    TokenPlan.objects.create(
        name="5M Tokens", 
        price_en=40.00,
        price_tr=40.00,
        price_ar=40.00,
        tokens_included=5000000,
        description="For power users"
    )
]
```

### 3. Get Your JWT Token

**Login via API:**
```bash
curl -X POST "http://localhost:8000/api/v1/accounts/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "your@email.com",
    "password": "yourpassword"
  }'
```

**Response:**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

Save the `access_token` - you'll need it for all API calls.

## 🧪 Test the APIs

### Step 1: List Available Plans

```bash
curl -X GET "http://localhost:8000/api/v1/billing/plans/" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

**Expected Response:**
```json
[
  {
    "id": 1,
    "name": "1M Tokens",
    "price": "10.00",
    "tokens_included": 1000000,
    "duration_days": null,
    "is_recurring": false,
    "is_active": true,
    "description": "Perfect for small teams"
  }
]
```

### Step 2: Purchase a Plan

```bash
curl -X POST "http://localhost:8000/api/v1/billing/purchase/" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "plan_id": 1,
    "payment_method": "credit_card"
  }'
```

**Expected Response:**
```json
{
  "message": "Plan purchased successfully",
  "payment_id": 1,
  "subscription": {
    "id": 1,
    "tokens_remaining": 1000000,
    "is_active": true,
    "is_subscription_active": true,
    "plan_details": {
      "name": "1M Tokens",
      "price": "10.00"
    }
  }
}
```

### Step 3: Check Your Subscription

```bash
curl -X GET "http://localhost:8000/api/v1/billing/subscription/" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

**Expected Response:**
```json
{
  "id": 1,
  "tokens_remaining": 1000000,
  "is_active": true,
  "is_subscription_active": true,
  "days_remaining": null,
  "plan_details": {
    "name": "1M Tokens",
    "price": "10.00",
    "tokens_included": 1000000
  }
}
```

### Step 4: Consume Some Tokens

```bash
curl -X POST "http://localhost:8000/api/v1/billing/tokens/consume/" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "tokens": 1000,
    "description": "AI message processing"
  }'
```

**Expected Response:**
```json
{
  "message": "Tokens consumed successfully",
  "tokens_consumed": 1000,
  "tokens_remaining": 999000,
  "subscription_active": true
}
```

### Step 5: Check Updated Account Overview

```bash
curl -X GET "http://localhost:8000/api/v1/accounts/overview/" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

**Expected Response:**
```json
{
  "id": 1,
  "subscription_remaining": "Unlimited",
  "token_usage_remaining": 999000,
  "free_trial": false,
  "free_trial_days_left": "0 days left"
}
```

## 🎯 Common Use Cases

### Use Case 1: Frontend Integration

```javascript
class BillingService {
    constructor(apiUrl, token) {
        this.apiUrl = apiUrl;
        this.token = token;
    }

    async getPlans() {
        const response = await fetch(`${this.apiUrl}/api/v1/billing/plans/`, {
            headers: { 'Authorization': `Bearer ${this.token}` }
        });
        return response.json();
    }

    async purchasePlan(planId) {
        const response = await fetch(`${this.apiUrl}/api/v1/billing/purchase/`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${this.token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ plan_id: planId })
        });
        return response.json();
    }

    async checkSubscription() {
        const response = await fetch(`${this.apiUrl}/api/v1/billing/subscription/`, {
            headers: { 'Authorization': `Bearer ${this.token}` }
        });
        return response.json();
    }
}

// Usage
const billing = new BillingService('http://localhost:8000', 'your_token');
const plans = await billing.getPlans();
console.log('Available plans:', plans);
```

### Use Case 2: Backend Service Integration

```python
from billing.models import Subscription
from rest_framework.decorators import api_view
from rest_framework.response import Response

@api_view(['POST'])
def process_ai_request(request):
    """Example: Integrate token consumption with AI processing"""
    
    # Check subscription
    try:
        subscription = request.user.subscription
        if not subscription.is_subscription_active():
            return Response({
                'error': 'Please upgrade your subscription to continue'
            }, status=402)  # Payment Required
        
        # Check token balance
        tokens_needed = 100  # This AI request costs 100 tokens
        if subscription.tokens_remaining < tokens_needed:
            return Response({
                'error': f'Insufficient tokens. Need {tokens_needed}, have {subscription.tokens_remaining}'
            }, status=402)
        
        # Process the AI request
        ai_result = your_ai_processing_function(request.data['message'])
        
        # Deduct tokens
        subscription.tokens_remaining -= tokens_needed
        subscription.save()
        
        # Track usage
        from billing.models import TokenUsage
        TokenUsage.objects.create(
            subscription=subscription,
            used_tokens=tokens_needed,
            description='AI message processing'
        )
        
        return Response({
            'result': ai_result,
            'tokens_remaining': subscription.tokens_remaining
        })
        
    except Subscription.DoesNotExist:
        return Response({
            'error': 'No subscription found. Please purchase a plan.'
        }, status=402)
```

### Use Case 3: Check Before Action

```python
def check_user_can_perform_action(user, tokens_required=50):
    """Helper function to check if user can perform token-consuming action"""
    try:
        subscription = user.subscription
        return {
            'can_perform': (
                subscription.is_subscription_active() and 
                subscription.tokens_remaining >= tokens_required
            ),
            'tokens_remaining': subscription.tokens_remaining,
            'tokens_required': tokens_required
        }
    except Subscription.DoesNotExist:
        return {
            'can_perform': False,
            'tokens_remaining': 0,
            'tokens_required': tokens_required,
            'error': 'No subscription found'
        }

# Usage in views
@api_view(['POST'])
def some_expensive_operation(request):
    check = check_user_can_perform_action(request.user, tokens_required=200)
    
    if not check['can_perform']:
        return Response({
            'error': 'Cannot perform operation',
            'details': check
        }, status=402)
    
    # Proceed with operation...
```

## 📊 Monitoring & Analytics

### Get Billing Overview

```bash
curl -X GET "http://localhost:8000/api/v1/billing/overview/" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### Get Token Usage History

```bash
curl -X GET "http://localhost:8000/api/v1/billing/tokens/usage/" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### Get Payment History

```bash
curl -X GET "http://localhost:8000/api/v1/billing/payments/" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

## 🛠️ Troubleshooting

### Issue: "No subscription found"
**Solution:** User needs to purchase a plan first
```bash
# Check if user has any subscription
curl -X GET "http://localhost:8000/api/v1/billing/subscription/" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### Issue: "Insufficient tokens"
**Solutions:** 
1. Purchase more tokens
2. Check current balance
3. Verify subscription is active

### Issue: "Authentication failed"
**Solution:** Check your JWT token
```bash
# Get a fresh token
curl -X POST "http://localhost:8000/api/v1/accounts/login" \
  -H "Content-Type: application/json" \
  -d '{"email": "your@email.com", "password": "yourpassword"}'
```

### Issue: Plans not showing
**Solution:** Create plans in Django admin or via shell
```python
python manage.py shell
from billing.models import TokenPlan
TokenPlan.objects.create(name="Test", price_en=10, price_tr=10, price_ar=10, tokens_included=1000)
```

## 🎉 Next Steps

1. **Integrate with Payment Gateway** - Connect Stripe, PayPal, etc.
2. **Add Frontend** - Build subscription management UI
3. **Set up Webhooks** - Handle payment confirmations
4. **Add Analytics** - Track usage patterns
5. **Implement Notifications** - Email users about low tokens, expiration

## 📚 More Resources

- [Complete API Documentation](./API_DOCUMENTATION.md)
- [Full Implementation Guide](./README.md)
- [Code Examples](./examples.py)
- Django Admin: `http://localhost:8000/admin/billing/`

## 💡 Pro Tips

1. **Always check subscription status** before consuming tokens
2. **Use the overview endpoint** for dashboard data
3. **Implement proper error handling** for payment failures
4. **Monitor token usage patterns** to optimize pricing
5. **Test with different plan types** (recurring vs one-time)

---

**Need help?** Check the documentation or create an issue in the project repository.
