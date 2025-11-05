"""
API Examples for Frontend Integration
Add these to your billing/views.py for frontend consumption
"""

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.utils import timezone
from datetime import timedelta
from billing.models import Subscription, FullPlan
import logging

logger = logging.getLogger(__name__)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_subscription_with_recommendations(request):
    """
    Get user's current subscription with smart upgrade/downgrade recommendations
    
    Returns:
        - Current subscription details
        - Days remaining
        - Recommended plan (upgrade if monthly, downgrade option if yearly)
        - Prorated credit calculation
        - Savings calculation
        
    Frontend Usage:
        GET /api/v1/billing/subscription-details/
        
    Response Example:
        {
          "has_subscription": true,
          "subscription": {
            "id": "abc123",
            "full_plan": {
              "id": 1,
              "name": "Monthly Pro",
              "price": 15.00,
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
          "is_expired": false,
          "recommendation": {
            "type": "upgrade",
            "plan": {
              "id": 2,
              "name": "Yearly Pro",
              "price": 150.00,
              "tokens_included": 100000,
              "duration_days": 365,
              "is_yearly": true
            },
            "savings": {
              "annual_savings": 30.00,
              "percentage": 17,
              "prorated_credit": 14.50,
              "final_price": 135.50
            },
            "comparison": {
              "current_annual_cost": 180.00,
              "new_annual_cost": 150.00,
              "current_tokens_per_year": 60000,
              "new_tokens_per_year": 100000
            }
          }
        }
    """
    try:
        # Get user's subscription
        subscription = Subscription.objects.filter(
            user=request.user,
            is_active=True
        ).select_related('full_plan', 'token_plan').first()
        
        if not subscription:
            # No subscription - show all plans
            monthly_plans = FullPlan.objects.filter(is_yearly=False, is_active=True)
            yearly_plans = FullPlan.objects.filter(is_yearly=True, is_active=True)
            
            return Response({
                'has_subscription': False,
                'available_plans': {
                    'monthly': [
                        {
                            'id': p.id,
                            'name': p.name,
                            'price': p.price,
                            'tokens_included': p.tokens_included,
                            'duration_days': p.duration_days
                        } for p in monthly_plans
                    ],
                    'yearly': [
                        {
                            'id': p.id,
                            'name': p.name,
                            'price': p.price,
                            'tokens_included': p.tokens_included,
                            'duration_days': p.duration_days,
                            'is_recommended': True
                        } for p in yearly_plans
                    ]
                }
            })
        
        # Calculate days remaining
        now = timezone.now()
        days_remaining = 0
        is_expired = False
        
        if subscription.end_date:
            days_remaining = (subscription.end_date - now).days
            is_expired = days_remaining < 0
            days_remaining = max(0, days_remaining)
        
        # Build base response
        response_data = {
            'has_subscription': True,
            'subscription': {
                'id': str(subscription.id),
                'full_plan': None,
                'token_plan': None,
                'start_date': subscription.start_date.isoformat(),
                'end_date': subscription.end_date.isoformat() if subscription.end_date else None,
                'tokens_remaining': subscription.tokens_remaining,
                'is_active': subscription.is_active,
                'status': subscription.status
            },
            'days_remaining': days_remaining,
            'is_expired': is_expired
        }
        
        # Add plan details
        if subscription.full_plan:
            response_data['subscription']['full_plan'] = {
                'id': subscription.full_plan.id,
                'name': subscription.full_plan.name,
                'price': subscription.full_plan.price,
                'tokens_included': subscription.full_plan.tokens_included,
                'duration_days': subscription.full_plan.duration_days,
                'is_yearly': subscription.full_plan.is_yearly
            }
        elif subscription.token_plan:
            response_data['subscription']['token_plan'] = {
                'id': subscription.token_plan.id,
                'name': subscription.token_plan.name,
                'price': subscription.token_plan.price,
                'tokens_included': subscription.token_plan.tokens_included
            }
        
        # Generate recommendation
        recommendation = None
        
        if subscription.full_plan:
            current_plan = subscription.full_plan
            
            # Monthly user → Recommend Yearly upgrade
            if not current_plan.is_yearly:
                yearly_plan = FullPlan.objects.filter(
                    is_yearly=True,
                    is_active=True
                ).first()
                
                if yearly_plan:
                    # Calculate savings
                    annual_cost_monthly = current_plan.price * 12
                    annual_cost_yearly = yearly_plan.price
                    annual_savings = annual_cost_monthly - annual_cost_yearly
                    percentage_savings = (annual_savings / annual_cost_monthly) * 100
                    
                    # Calculate prorated credit for unused days
                    prorated_credit = 0
                    if not is_expired and days_remaining > 0:
                        daily_rate = current_plan.price / current_plan.duration_days
                        prorated_credit = daily_rate * days_remaining
                    
                    final_price = annual_cost_yearly - prorated_credit
                    
                    recommendation = {
                        'type': 'upgrade',
                        'plan': {
                            'id': yearly_plan.id,
                            'name': yearly_plan.name,
                            'price': yearly_plan.price,
                            'tokens_included': yearly_plan.tokens_included,
                            'duration_days': yearly_plan.duration_days,
                            'is_yearly': True
                        },
                        'savings': {
                            'annual_savings': round(annual_savings, 2),
                            'percentage': round(percentage_savings, 0),
                            'prorated_credit': round(prorated_credit, 2),
                            'final_price': round(final_price, 2)
                        },
                        'comparison': {
                            'current_annual_cost': round(annual_cost_monthly, 2),
                            'new_annual_cost': round(annual_cost_yearly, 2),
                            'current_tokens_per_year': current_plan.tokens_included * 12,
                            'new_tokens_per_year': yearly_plan.tokens_included
                        }
                    }
            
            # Yearly user → Show downgrade option (less prominent)
            else:
                monthly_plan = FullPlan.objects.filter(
                    is_yearly=False,
                    is_active=True
                ).first()
                
                if monthly_plan:
                    # Calculate what they'd lose
                    annual_cost_monthly = monthly_plan.price * 12
                    annual_cost_yearly = current_plan.price
                    annual_increase = annual_cost_monthly - annual_cost_yearly
                    
                    # Calculate refund for unused days
                    prorated_refund = 0
                    if not is_expired and days_remaining > 0:
                        daily_rate = current_plan.price / current_plan.duration_days
                        prorated_refund = daily_rate * days_remaining
                    
                    recommendation = {
                        'type': 'downgrade',
                        'plan': {
                            'id': monthly_plan.id,
                            'name': monthly_plan.name,
                            'price': monthly_plan.price,
                            'tokens_included': monthly_plan.tokens_included,
                            'duration_days': monthly_plan.duration_days,
                            'is_yearly': False
                        },
                        'warning': {
                            'annual_increase': round(annual_increase, 2),
                            'percentage_increase': round((annual_increase / annual_cost_yearly) * 100, 0),
                            'prorated_refund': round(prorated_refund, 2),
                            'refund_will_be_credited': True
                        },
                        'comparison': {
                            'current_annual_cost': round(annual_cost_yearly, 2),
                            'new_annual_cost': round(annual_cost_monthly, 2),
                            'current_monthly_effective': round(annual_cost_yearly / 12, 2),
                            'new_monthly_cost': monthly_plan.price,
                            'current_tokens_per_year': current_plan.tokens_included,
                            'new_tokens_per_year': monthly_plan.tokens_included * 12
                        }
                    }
        
        if recommendation:
            response_data['recommendation'] = recommendation
        
        return Response(response_data)
        
    except Exception as e:
        logger.error(f"Error getting subscription recommendations: {str(e)}")
        return Response(
            {'error': 'Failed to get subscription details'},
            status=500
        )


# Add this to urls.py:
"""
from billing.api_examples import get_subscription_with_recommendations

urlpatterns = [
    # ... existing patterns ...
    path('subscription-details/', get_subscription_with_recommendations, name='subscription-details'),
]
"""
