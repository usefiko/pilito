#!/bin/bash
# Quick setup script for Stripe integration

echo "🚀 Fiko Backend - Stripe Integration Quick Setup"
echo "================================================="
echo ""

# Check if stripe is installed
python -c "import stripe" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "📦 Installing Stripe SDK..."
    pip install stripe
else
    echo "✅ Stripe SDK already installed"
fi

echo ""
echo "📝 Configuration Checklist:"
echo ""
echo "1. Get your Stripe API keys:"
echo "   https://dashboard.stripe.com/apikeys"
echo ""
echo "2. Add environment variables to .env file:"
echo "   See: STRIPE_ENVIRONMENT_VARIABLES.txt"
echo ""
echo "3. Configure Stripe webhook:"
echo "   https://dashboard.stripe.com/webhooks"
echo "   Webhook URL: https://api.pilito.com/billing/stripe/webhook/"
echo ""
echo "4. Test locally with Stripe CLI:"
echo "   brew install stripe/stripe-cli/stripe"
echo "   stripe listen --forward-to localhost:8000/billing/stripe/webhook/"
echo ""
echo "5. Sync plans to Stripe (optional):"
echo "   python src/manage.py sync_stripe_products --dry-run"
echo ""
echo "6. Read the complete guide:"
echo "   STRIPE_INTEGRATION_GUIDE.md"
echo ""

# Offer to create environment file template
read -p "Would you like to create a .env.stripe template file? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    if [ ! -f ".env.stripe" ]; then
        cp STRIPE_ENVIRONMENT_VARIABLES.txt .env.stripe
        echo "✅ Created .env.stripe - Please fill in your Stripe keys"
    else
        echo "⚠️  .env.stripe already exists"
    fi
fi

echo ""
echo "✅ Setup complete! Follow the checklist above to finish configuration."
echo "📚 Read STRIPE_INTEGRATION_GUIDE.md for detailed instructions."
echo ""

