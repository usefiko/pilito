"""
Billing API Usage Examples

This file contains practical examples of how to use the billing and subscription APIs
in your Django application and with external clients.
"""

import requests
import json
from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from .models import TokenPlan, Subscription, Payment, TokenUsage

User = get_user_model()


# ============================================================================
# Django ORM Examples (Server-side usage)
# ============================================================================

class BillingExamples:
    """
    Server-side examples using Django ORM
    """
    
    @staticmethod
    def create_sample_plans():
        """Create sample subscription plans"""
        plans = [
            {
                'name': '1M Tokens',
                'price': 10.00,
                'tokens_included': 1000000,
                'duration_days': None,  # Lifetime
                'is_recurring': False,
                'description': 'Perfect for small teams and individual creators'
            },
            {
                'name': '3M Tokens', 
                'price': 20.00,
                'tokens_included': 3000000,
                'duration_days': None,
                'is_recurring': False,
                'description': 'Designed for growing businesses'
            },
            {
                'name': '5M Tokens',
                'price': 40.00,
                'tokens_included': 5000000,
                'duration_days': None,
                'is_recurring': False,
                'description': 'For power users and large teams'
            },
            {
                'name': '10M Tokens',
                'price': 100.00,
                'tokens_included': 10000000,
                'duration_days': None,
                'is_recurring': False,
                'description': 'Enterprise solution for organizations'
            },
            {
                'name': 'Basic Monthly',
                'price': 15.00,
                'tokens_included': 1000000,
                'duration_days': 30,
                'is_recurring': True,
                'description': 'Monthly subscription with 1M tokens'
            }
        ]
        
        created_plans = []
        for plan_data in plans:
            plan, created = TokenPlan.objects.get_or_create(
                name=plan_data['name'],
                defaults=plan_data
            )
            created_plans.append(plan)
            print(f"{'Created' if created else 'Found'} plan: {plan.name}")
        
        return created_plans
    
    @staticmethod
    def purchase_plan_for_user(user, plan_id, payment_method='credit_card'):
        """
        Purchase a plan for a user (server-side)
        """
        try:
            plan = TokenPlan.objects.get(id=plan_id, is_active=True)
        except TokenPlan.DoesNotExist:
            return {'error': 'Plan not found'}
        
        # Create payment record
        payment = Payment.objects.create(
            user=user,
            plan=plan,
            amount=plan.price,
            payment_method=payment_method,
            status='completed',  # Simulated successful payment
            transaction_id=f'sim_{user.id}_{plan.id}'
        )
        
        # Create or update subscription
        subscription, created = Subscription.objects.get_or_create(
            user=user,
            defaults={
                'plan': plan,
                'tokens_remaining': plan.tokens_included,
                'is_active': True
            }
        )
        
        if not created:
            # Add tokens to existing subscription
            subscription.tokens_remaining += plan.tokens_included
            subscription.plan = plan
            subscription.is_active = True
            subscription.save()
        
        # Link payment to subscription
        payment.subscription = subscription
        payment.save()
        
        return {
            'success': True,
            'payment_id': payment.id,
            'subscription_id': subscription.id,
            'tokens_added': plan.tokens_included,
            'total_tokens': subscription.tokens_remaining
        }
    
    @staticmethod
    def consume_tokens(user, tokens, description='API usage'):
        """
        Consume tokens from user's subscription
        """
        try:
            subscription = user.subscription
        except Subscription.DoesNotExist:
            return {'error': 'No subscription found'}
        
        if not subscription.is_subscription_active():
            return {'error': 'Subscription is not active'}
        
        if subscription.tokens_remaining < tokens:
            return {
                'error': f'Insufficient tokens. Available: {subscription.tokens_remaining}, Requested: {tokens}'
            }
        
        # Deduct tokens
        subscription.tokens_remaining -= tokens
        subscription.save()
        
        # Create usage record
        usage = TokenUsage.objects.create(
            subscription=subscription,
            used_tokens=tokens,
            description=description
        )
        
        return {
            'success': True,
            'tokens_consumed': tokens,
            'tokens_remaining': subscription.tokens_remaining,
            'usage_id': usage.id,
            'subscription_active': subscription.is_subscription_active()
        }
    
    @staticmethod
    def get_user_billing_summary(user):
        """
        Get comprehensive billing summary for a user
        """
        try:
            subscription = user.subscription
            
            # Calculate usage statistics
            from django.db.models import Sum
            from django.utils import timezone
            
            now = timezone.now()
            today_usage = subscription.token_usages.filter(
                usage_date__date=now.date()
            ).aggregate(total=Sum('used_tokens'))['total'] or 0
            
            month_start = now.replace(day=1, hour=0, minute=0, second=0)
            month_usage = subscription.token_usages.filter(
                usage_date__gte=month_start
            ).aggregate(total=Sum('used_tokens'))['total'] or 0
            
            total_payments = user.payments.filter(status='completed').count()
            total_spent = user.payments.filter(status='completed').aggregate(
                total=Sum('amount')
            )['total'] or 0
            
            return {
                'user_email': user.email,
                'subscription': {
                    'plan_name': subscription.plan.name,
                    'tokens_remaining': subscription.tokens_remaining,
                    'is_active': subscription.is_subscription_active(),
                    'days_remaining': subscription.days_remaining(),
                    'start_date': subscription.start_date,
                    'end_date': subscription.end_date
                },
                'usage': {
                    'today': today_usage,
                    'this_month': month_usage
                },
                'payments': {
                    'total_payments': total_payments,
                    'total_spent': float(total_spent)
                }
            }
            
        except Subscription.DoesNotExist:
            return {
                'user_email': user.email,
                'subscription': None,
                'usage': {'today': 0, 'this_month': 0},
                'payments': {'total_payments': 0, 'total_spent': 0}
            }


# ============================================================================
# HTTP API Examples (Client-side usage)
# ============================================================================

class BillingAPIClient:
    """
    Client-side examples using HTTP requests
    """
    
    def __init__(self, base_url='http://localhost:8000', token=None):
        self.base_url = base_url
        self.token = token
        self.session = requests.Session()
        if token:
            self.session.headers.update({'Authorization': f'Bearer {token}'})
    
    def get_plans(self):
        """Get available subscription plans"""
        response = self.session.get(f'{self.base_url}/api/v1/billing/plans/')
        return response.json()
    
    def purchase_plan(self, plan_id, payment_method='credit_card', transaction_id=None):
        """Purchase a subscription plan"""
        data = {
            'plan_id': plan_id,
            'payment_method': payment_method
        }
        if transaction_id:
            data['transaction_id'] = transaction_id
        
        response = self.session.post(
            f'{self.base_url}/api/v1/billing/purchase/',
            json=data
        )
        return response.json()
    
    def get_subscription(self):
        """Get current subscription details"""
        response = self.session.get(f'{self.base_url}/api/v1/billing/subscription/')
        return response.json()
    
    def consume_tokens(self, tokens, description=''):
        """Consume tokens from subscription"""
        data = {
            'tokens': tokens,
            'description': description
        }
        response = self.session.post(
            f'{self.base_url}/api/v1/billing/tokens/consume/',
            json=data
        )
        return response.json()
    
    def get_payment_history(self):
        """Get payment history"""
        response = self.session.get(f'{self.base_url}/api/v1/billing/payments/')
        return response.json()
    
    def get_token_usage_history(self):
        """Get token usage history"""
        response = self.session.get(f'{self.base_url}/api/v1/billing/tokens/usage/')
        return response.json()
    
    def get_billing_overview(self):
        """Get comprehensive billing overview"""
        response = self.session.get(f'{self.base_url}/api/v1/billing/overview/')
        return response.json()


# ============================================================================
# JavaScript/Frontend Examples
# ============================================================================

javascript_examples = """
// JavaScript/Frontend Examples

class BillingAPI {
    constructor(baseUrl = 'http://localhost:8000', token = null) {
        this.baseUrl = baseUrl;
        this.token = token;
    }

    async request(endpoint, options = {}) {
        const url = `${this.baseUrl}${endpoint}`;
        const headers = {
            'Content-Type': 'application/json',
            ...options.headers
        };
        
        if (this.token) {
            headers['Authorization'] = `Bearer ${this.token}`;
        }

        const response = await fetch(url, {
            ...options,
            headers
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        return response.json();
    }

    // Get available plans
    async getPlans() {
        return this.request('/api/v1/billing/plans/');
    }

    // Purchase a plan
    async purchasePlan(planId, paymentMethod = 'credit_card', transactionId = null) {
        const data = {
            plan_id: planId,
            payment_method: paymentMethod
        };
        
        if (transactionId) {
            data.transaction_id = transactionId;
        }

        return this.request('/api/v1/billing/purchase/', {
            method: 'POST',
            body: JSON.stringify(data)
        });
    }

    // Get current subscription
    async getSubscription() {
        return this.request('/api/v1/billing/subscription/');
    }

    // Consume tokens
    async consumeTokens(tokens, description = '') {
        return this.request('/api/v1/billing/tokens/consume/', {
            method: 'POST',
            body: JSON.stringify({
                tokens: tokens,
                description: description
            })
        });
    }

    // Get billing overview
    async getBillingOverview() {
        return this.request('/api/v1/billing/overview/');
    }
}

// Usage example:
const billing = new BillingAPI('http://localhost:8000', 'your_jwt_token_here');

// Get plans and display
billing.getPlans().then(plans => {
    console.log('Available plans:', plans);
    plans.forEach(plan => {
        console.log(`${plan.name}: $${plan.price} for ${plan.tokens_included} tokens`);
    });
});

// Purchase a plan
billing.purchasePlan(1, 'credit_card').then(result => {
    console.log('Purchase result:', result);
}).catch(error => {
    console.error('Purchase failed:', error);
});

// Check subscription status
billing.getSubscription().then(subscription => {
    console.log(`Tokens remaining: ${subscription.tokens_remaining}`);
    console.log(`Days remaining: ${subscription.days_remaining}`);
}).catch(error => {
    console.log('No active subscription');
});

// Consume tokens for AI processing
async function processAIRequest(message) {
    try {
        // First check if we have enough tokens
        const subscription = await billing.getSubscription();
        
        if (subscription.tokens_remaining < 50) {
            throw new Error('Insufficient tokens');
        }

        // Process the AI request (your AI logic here)
        const aiResult = await processAIMessage(message);

        // Deduct tokens
        await billing.consumeTokens(50, 'AI message processing');

        return aiResult;
    } catch (error) {
        console.error('AI processing failed:', error);
        throw error;
    }
}
"""


# ============================================================================
# Django Test Examples
# ============================================================================

class BillingAPITestCase(TestCase):
    """
    Test cases demonstrating API usage
    """
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.client = APIClient()
        
        # Create JWT token
        refresh = RefreshToken.for_user(self.user)
        self.token = str(refresh.access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')
        
        # Create test plan
        self.plan = TokenPlan.objects.create(
            name='Test Plan',
            price_en=10.00,
            price_tr=10.00,
            price_ar=10.00,
            tokens_included=1000,
            is_recurring=False
        )
    
    def test_get_plans(self):
        """Test getting available plans"""
        response = self.client.get('/api/v1/billing/plans/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], 'Test Plan')
    
    def test_purchase_plan(self):
        """Test purchasing a plan"""
        data = {
            'plan_id': self.plan.id,
            'payment_method': 'credit_card'
        }
        response = self.client.post('/api/v1/billing/purchase/', data)
        self.assertEqual(response.status_code, 201)
        self.assertIn('subscription', response.data)
        
        # Verify subscription was created
        subscription = Subscription.objects.get(user=self.user)
        self.assertEqual(subscription.tokens_remaining, 1000)
        self.assertTrue(subscription.is_active)
    
    def test_consume_tokens(self):
        """Test consuming tokens"""
        # First create a subscription
        subscription = Subscription.objects.create(
            user=self.user,
            plan=self.plan,
            tokens_remaining=1000,
            is_active=True
        )
        
        data = {
            'tokens': 100,
            'description': 'Test consumption'
        }
        response = self.client.post('/api/v1/billing/tokens/consume/', data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['tokens_remaining'], 900)
        
        # Verify token usage was recorded
        usage = TokenUsage.objects.get(subscription=subscription)
        self.assertEqual(usage.used_tokens, 100)
        self.assertEqual(usage.description, 'Test consumption')
    
    def test_billing_overview(self):
        """Test billing overview endpoint"""
        # Create subscription and some usage
        subscription = Subscription.objects.create(
            user=self.user,
            plan=self.plan,
            tokens_remaining=800,
            is_active=True
        )
        
        TokenUsage.objects.create(
            subscription=subscription,
            used_tokens=100,
            description='Test usage'
        )
        
        response = self.client.get('/api/v1/billing/overview/')
        self.assertEqual(response.status_code, 200)
        self.assertIn('current_subscription', response.data)
        self.assertEqual(response.data['current_subscription']['tokens_remaining'], 800)


# ============================================================================
# Example Usage Script
# ============================================================================

def run_examples():
    """
    Run example scenarios
    """
    print("=== Billing System Examples ===\n")
    
    # 1. Create sample plans
    print("1. Creating sample plans...")
    plans = BillingExamples.create_sample_plans()
    print(f"Created {len(plans)} plans\n")
    
    # 2. Create a test user
    print("2. Creating test user...")
    user, created = User.objects.get_or_create(
        email='example@test.com',
        defaults={'username': 'example_user'}
    )
    print(f"{'Created' if created else 'Found'} user: {user.email}\n")
    
    # 3. Purchase a plan
    print("3. Purchasing a plan...")
    purchase_result = BillingExamples.purchase_plan_for_user(user, plans[0].id)
    print(f"Purchase result: {purchase_result}\n")
    
    # 4. Consume some tokens
    print("4. Consuming tokens...")
    consumption_result = BillingExamples.consume_tokens(user, 500, 'Example AI processing')
    print(f"Consumption result: {consumption_result}\n")
    
    # 5. Get billing summary
    print("5. Getting billing summary...")
    summary = BillingExamples.get_user_billing_summary(user)
    print(f"Billing summary: {json.dumps(summary, indent=2, default=str)}\n")
    
    print("=== Examples completed ===")


if __name__ == '__main__':
    # This would be run in Django shell or management command
    # python manage.py shell
    # >>> exec(open('billing/examples.py').read())
    # >>> run_examples()
    pass
