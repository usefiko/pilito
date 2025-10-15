#!/bin/bash
# Script to help add Stripe configuration to .env file

echo "🔧 Stripe Configuration Helper"
echo "================================"
echo ""

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "❌ .env file not found!"
    echo "Creating .env file..."
    touch .env
fi

echo "📝 Current .env file location: $(pwd)/.env"
echo ""

# Check if Stripe is already configured
if grep -q "STRIPE_SECRET_KEY" .env; then
    echo "⚠️  Stripe configuration already exists in .env"
    echo ""
    read -p "Do you want to overwrite it? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Cancelled."
        exit 0
    fi
    # Remove old Stripe config
    sed -i.bak '/STRIPE_/d' .env
fi

echo "🔑 Please enter your Stripe keys from:"
echo "   https://dashboard.stripe.com/test/apikeys"
echo ""

# Get Publishable Key
read -p "Enter STRIPE_PUBLISHABLE_KEY (pk_test_...): " pub_key
if [ -z "$pub_key" ]; then
    echo "❌ Publishable key cannot be empty!"
    exit 1
fi

# Get Secret Key
read -p "Enter STRIPE_SECRET_KEY (sk_test_...): " secret_key
if [ -z "$secret_key" ]; then
    echo "❌ Secret key cannot be empty!"
    exit 1
fi

# Get Webhook Secret (optional for now)
echo ""
echo "ℹ️  Webhook secret is optional for now (configure later)"
read -p "Enter STRIPE_WEBHOOK_SECRET (optional, press Enter to skip): " webhook_secret

# Add to .env
echo "" >> .env
echo "# =====================================" >> .env
echo "# STRIPE CONFIGURATION" >> .env
echo "# =====================================" >> .env
echo "STRIPE_PUBLISHABLE_KEY=$pub_key" >> .env
echo "STRIPE_SECRET_KEY=$secret_key" >> .env

if [ ! -z "$webhook_secret" ]; then
    echo "STRIPE_WEBHOOK_SECRET=$webhook_secret" >> .env
else
    echo "STRIPE_WEBHOOK_SECRET=" >> .env
fi

echo "STRIPE_ENABLED=True" >> .env
echo "STRIPE_TEST_MODE=True" >> .env
echo "STRIPE_CURRENCY=usd" >> .env
echo "STRIPE_SUCCESS_URL=https://app.fiko.net/billing/success?session_id={CHECKOUT_SESSION_ID}" >> .env
echo "STRIPE_CANCEL_URL=https://app.fiko.net/billing/plans" >> .env
echo "STRIPE_PORTAL_RETURN_URL=https://app.fiko.net/billing" >> .env

echo ""
echo "✅ Stripe configuration added to .env!"
echo ""
echo "📋 Next steps:"
echo "1. Restart your server"
echo "2. Test the API again"
echo "3. Configure webhook (see STRIPE_WEBHOOK_SETUP.md)"
echo ""
echo "🔄 To restart server:"
echo "   sudo systemctl restart gunicorn"
echo "   # or"
echo "   docker-compose restart web"
echo ""

