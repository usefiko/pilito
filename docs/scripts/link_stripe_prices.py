#!/usr/bin/env python
"""
Script to link your Stripe price IDs to your database plans
Run this after running migrations
"""
import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from billing.models import FullPlan

def link_stripe_prices():
    """Link Stripe price IDs to database plans"""
    
    print("🔗 Linking Stripe Prices to Database Plans")
    print("=" * 50)
    
    # Your Stripe price IDs
    STRIPE_PRICES = {
        'monthly': 'price_1S0dwrKkH1LI50QC2GhtfzN4',
        'yearly': 'price_1S0dxYKkH1LI50QCEqPZJ6Jq',
    }
    
    # Find your plans
    try:
        # Find monthly plan (adjust query based on your plan names)
        monthly_plan = FullPlan.objects.filter(
            is_yearly=False,
            is_active=True
        ).first()
        
        if monthly_plan:
            monthly_plan.stripe_price_id = STRIPE_PRICES['monthly']
            monthly_plan.save()
            print(f"✅ Linked Monthly Plan: {monthly_plan.name}")
            print(f"   Price ID: {STRIPE_PRICES['monthly']}")
        else:
            print("⚠️  No monthly plan found. Create one in Django admin.")
        
        # Find yearly plan
        yearly_plan = FullPlan.objects.filter(
            is_yearly=True,
            is_active=True
        ).first()
        
        if yearly_plan:
            yearly_plan.stripe_price_id = STRIPE_PRICES['yearly']
            yearly_plan.save()
            print(f"✅ Linked Yearly Plan: {yearly_plan.name}")
            print(f"   Price ID: {STRIPE_PRICES['yearly']}")
        else:
            print("⚠️  No yearly plan found. Create one in Django admin.")
        
        print("\n✅ Done! Plans are now linked to Stripe prices.")
        print("\n📋 Next steps:")
        print("1. Test checkout session creation")
        print("2. Verify prices match in Stripe Dashboard")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    
    return True

if __name__ == '__main__':
    success = link_stripe_prices()
    sys.exit(0 if success else 1)

