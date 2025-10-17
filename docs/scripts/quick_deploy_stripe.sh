#!/bin/bash
# Quick deployment script for Stripe integration

echo "🚀 Deploying Stripe Integration"
echo "================================"
echo ""

# Check if git is clean
if [[ -n $(git status -s) ]]; then
    echo "📝 Changes detected. Committing..."
    
    git add src/billing/migrations/0006_add_stripe_fields.py
    git add src/billing/models.py
    git add src/billing/services/stripe_service.py
    git add src/requirements/base.txt
    
    git commit -m "Add Stripe integration with price ID support

- Added stripe_product_id and stripe_price_id fields to TokenPlan and FullPlan
- Updated Stripe service to use existing price IDs
- Added stripe to requirements
- Migration for new fields"
    
    echo "✅ Changes committed"
else
    echo "✅ Git is clean"
fi

echo ""
echo "📤 Pushing to repository..."
git push origin main

if [ $? -eq 0 ]; then
    echo "✅ Pushed successfully"
else
    echo "❌ Push failed. Please check your git remote."
    exit 1
fi

echo ""
echo "📋 Next steps on your production server:"
echo ""
echo "1. SSH to server:"
echo "   ssh ubuntu@your-server-ip"
echo ""
echo "2. Pull changes:"
echo "   cd /path/to/Fiko-Backend"
echo "   git pull origin main"
echo ""
echo "3. Restart and migrate:"
echo "   docker-compose restart"
echo "   docker-compose exec web python manage.py migrate"
echo ""
echo "4. Link Stripe prices:"
echo "   docker-compose exec web python manage.py shell"
echo "   >>> from billing.models import FullPlan"
echo "   >>> FullPlan.objects.filter(is_yearly=False).update(stripe_price_id='price_1S0dwrKkH1LI50QC2GhtfzN4')"
echo "   >>> FullPlan.objects.filter(is_yearly=True).update(stripe_price_id='price_1S0dxYKkH1LI50QCEqPZJ6Jq')"
echo "   >>> exit()"
echo ""
echo "5. Test checkout:"
echo "   curl -X POST https://api.pilito.com/api/v1/billing/stripe/checkout-session/ \\"
echo "     -H 'Authorization: Bearer TOKEN' \\"
echo "     -H 'Content-Type: application/json' \\"
echo "     -d '{\"plan_type\": \"full\", \"plan_id\": 2}'"
echo ""
echo "✅ Local deployment complete!"
echo ""

