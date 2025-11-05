# Billing & Subscription System

A comprehensive Django-based subscription and payment management system with token usage tracking.

## 🏗️ System Architecture

### Core Models

```
TokenPlan → Subscription ← User
                    ↓
                  Payment
                    ↓
                TokenUsage
```

- **TokenPlan**: Defines available token bundles
- **Subscription**: User's active subscription with token balance
- **Payment**: Payment records and transaction history
- **TokenUsage**: Tracks API/service consumption

## 🚀 Quick Start

### 1. Run Migrations

```bash
cd src/
python manage.py migrate billing
```

### 2. Create Subscription Plans

Use Django Admin or create programmatically:

```python
from billing.models import TokenPlan

# Create basic plan
basic_plan = TokenPlan.objects.create(
    name="Basic Plan",
    price=15,
    tokens_included=1000,
    duration_days=30,
    is_recurring=True,
    description="Perfect for small teams"
)

# Create pro plan
pro_plan = TokenPlan.objects.create(
    name="Pro Plan", 
    price=40,
    tokens_included=5000,
    duration_days=30,
    is_recurring=True,
    description="For power users"
)
```

### 3. Test API Endpoints

```bash
# Get available plans
curl -X GET "http://localhost:8000/api/v1/billing/plans/" \
  -H "Authorization: Bearer <token>"

# Purchase a plan
curl -X POST "http://localhost:8000/api/v1/billing/purchase/" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"plan_id": 1, "payment_method": "credit_card"}'

# Check subscription
curl -X GET "http://localhost:8000/api/v1/billing/subscription/" \
  -H "Authorization: Bearer <token>"
```

## 📊 Features

### ✅ Subscription Management
- Multiple subscription plans with different pricing tiers
- Automatic subscription renewal handling
- Token-based usage tracking
- Expiration date management

### ✅ Payment Processing
- Multiple payment method support
- Transaction history tracking
- Payment status management
- Gateway integration ready

### ✅ Token System
- Token consumption tracking
- Usage analytics and reporting
- Automatic deduction on API calls
- Usage history with descriptions

### ✅ Admin Interface
- Rich Django admin interfaces
- Visual status indicators
- Comprehensive filtering and search
- Export capabilities

### ✅ API Integration
- RESTful API endpoints
- JWT authentication
- Comprehensive error handling
- Legacy API compatibility

## 🔧 Configuration

### Settings

Add to your Django settings:

```python
INSTALLED_APPS = [
    # ... other apps
    'billing',
]

# Optional: Configure payment gateways
STRIPE_PUBLIC_KEY = 'pk_test_...'
STRIPE_SECRET_KEY = 'sk_test_...'
```

### URL Configuration

In your main `urls.py`:

```python
urlpatterns = [
    # ... other patterns
    path('api/v1/billing/', include('billing.urls')),
]
```

## 💼 Business Logic

### Purchase Flow

1. User selects a subscription plan
2. Payment record created with "pending" status
3. Payment gateway processes payment
4. On success: Payment status → "completed"
5. Subscription created/renewed with tokens
6. User can consume tokens via API

### Token Consumption

1. API call requests token consumption
2. System checks subscription status
3. Validates sufficient token balance
4. Deducts tokens and creates usage record
5. Returns updated token balance

### Subscription Status

A subscription is active when:
- `is_active = True`
- `tokens_remaining > 0`
- `current_date <= end_date` (if plan has duration)

## 🎯 Usage Examples

### Django Views Integration

```python
from billing.models import Subscription
from rest_framework.decorators import api_view

@api_view(['POST'])
def ai_process_message(request):
    try:
        subscription = request.user.subscription
        if not subscription.is_subscription_active():
            return Response({'error': 'No active subscription'}, 
                          status=400)
        
        if subscription.tokens_remaining < 10:
            return Response({'error': 'Insufficient tokens'}, 
                          status=400)
        
        # Process the AI request
        result = process_ai_message(request.data['message'])
        
        # Deduct tokens
        subscription.tokens_remaining -= 10
        subscription.save()
        
        # Track usage
        TokenUsage.objects.create(
            subscription=subscription,
            used_tokens=10,
            description="AI message processing"
        )
        
        return Response(result)
        
    except Subscription.DoesNotExist:
        return Response({'error': 'No subscription found'}, 
                      status=404)
```

### Frontend Integration

```javascript
// Get user's subscription status
const getSubscription = async () => {
  const response = await fetch('/api/v1/billing/subscription/', {
    headers: {
      'Authorization': `Bearer ${token}`
    }
  });
  return response.json();
};

// Purchase a plan
const purchasePlan = async (planId) => {
  const response = await fetch('/api/v1/billing/purchase/', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      plan_id: planId,
      payment_method: 'credit_card'
    })
  });
  return response.json();
};

// Consume tokens
const consumeTokens = async (tokens, description) => {
  const response = await fetch('/api/v1/billing/tokens/consume/', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      tokens: tokens,
      description: description
    })
  });
  return response.json();
};
```

## 🔌 Payment Gateway Integration

### Stripe Example

```python
# views.py
import stripe
from django.conf import settings

stripe.api_key = settings.STRIPE_SECRET_KEY

class StripePaymentView(APIView):
    def post(self, request):
        try:
            # Create Stripe payment intent
            intent = stripe.PaymentIntent.create(
                amount=plan.price * 100,  # Convert to cents
                currency='usd',
                metadata={
                    'user_id': request.user.id,
                    'plan_id': plan.id
                }
            )
            
            # Create pending payment
            payment = Payment.objects.create(
                user=request.user,
                plan=plan,
                amount=plan.price,
                payment_method='stripe',
                status='pending',
                transaction_id=intent.id
            )
            
            return Response({
                'client_secret': intent.client_secret,
                'payment_id': payment.id
            })
            
        except Exception as e:
            return Response({'error': str(e)}, status=400)
```

### PayPal Example

```python
# PayPal SDK integration
import paypalrestsdk

class PayPalPaymentView(APIView):
    def post(self, request):
        payment = paypalrestsdk.Payment({
            "intent": "sale",
            "payer": {"payment_method": "paypal"},
            "transactions": [{
                "amount": {
                    "total": str(plan.price),
                    "currency": "USD"
                },
                "description": f"Subscription: {plan.name}"
            }],
            "redirect_urls": {
                "return_url": "http://localhost:8000/payment/execute",
                "cancel_url": "http://localhost:8000/payment/cancel"
            }
        })
        
        if payment.create():
            # Store payment record
            Payment.objects.create(
                user=request.user,
                plan=plan,
                amount=plan.price,
                payment_method='paypal',
                status='pending',
                transaction_id=payment.id
            )
            
            return Response({'approval_url': payment.links[1].href})
        else:
            return Response({'error': payment.error}, status=400)
```

## 📈 Analytics & Reporting

### Usage Analytics

```python
from django.db.models import Sum, Count
from django.utils import timezone
from datetime import timedelta

# Get usage statistics
def get_usage_stats(user):
    subscription = user.subscription
    now = timezone.now()
    
    # Today's usage
    today_usage = subscription.token_usages.filter(
        usage_date__date=now.date()
    ).aggregate(total=Sum('used_tokens'))['total'] or 0
    
    # This month's usage
    month_start = now.replace(day=1, hour=0, minute=0, second=0)
    month_usage = subscription.token_usages.filter(
        usage_date__gte=month_start
    ).aggregate(total=Sum('used_tokens'))['total'] or 0
    
    # Usage by day (last 30 days)
    thirty_days_ago = now - timedelta(days=30)
    daily_usage = subscription.token_usages.filter(
        usage_date__gte=thirty_days_ago
    ).values('usage_date__date').annotate(
        total_tokens=Sum('used_tokens')
    ).order_by('usage_date__date')
    
    return {
        'today': today_usage,
        'this_month': month_usage,
        'daily_breakdown': list(daily_usage)
    }
```

### Revenue Analytics

```python
def get_revenue_stats():
    from django.db.models import Sum, Count
    
    # Total revenue
    total_revenue = Payment.objects.filter(
        status='completed'
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    # Revenue by plan
    revenue_by_plan = Payment.objects.filter(
        status='completed'
    ).values('plan__name').annotate(
        total_revenue=Sum('amount'),
        total_sales=Count('id')
    ).order_by('-total_revenue')
    
    # Monthly revenue
    monthly_revenue = Payment.objects.filter(
        status='completed'
    ).extra({
        'month': "DATE_FORMAT(payment_date, '%Y-%m')"
    }).values('month').annotate(
        total=Sum('amount')
    ).order_by('month')
    
    return {
        'total_revenue': total_revenue,
        'revenue_by_plan': list(revenue_by_plan),
        'monthly_revenue': list(monthly_revenue)
    }
```

## 🛠️ Troubleshooting

### Common Issues

1. **Migration Errors**
   ```bash
   python manage.py migrate billing --fake-initial
   ```

2. **Import Errors**
   - Ensure `billing` is in `INSTALLED_APPS`
   - Check circular import issues

3. **Token Balance Issues**
   ```python
   # Reset user tokens
   subscription = user.subscription
   subscription.tokens_remaining = subscription.plan.tokens_included
   subscription.save()
   ```

4. **Subscription Status Issues**
   ```python
   # Refresh subscription status
   subscription.refresh_from_db()
   if not subscription.is_subscription_active():
       subscription.is_active = False
       subscription.save()
   ```

## 📚 Related Documentation

- [API Documentation](./API_DOCUMENTATION.md) - Complete API reference
- [Django Admin Guide](../docs/admin-guide.md) - Admin interface usage
- [Payment Integration](../docs/payment-integration.md) - Payment gateway setup
- [Testing Guide](../docs/testing.md) - Testing the billing system

## 🤝 Contributing

1. Follow Django best practices
2. Add tests for new features
3. Update documentation
4. Ensure backward compatibility with legacy models

## 📝 License

This billing system is part of the Fiko Backend project.
