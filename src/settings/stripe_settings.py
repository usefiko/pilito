"""
Stripe Configuration Settings
Add these to your environment variables or settings file
"""
import os
from django.conf import settings

# Stripe API Keys
STRIPE_PUBLISHABLE_KEY = os.environ.get('STRIPE_PUBLISHABLE_KEY', '')
STRIPE_SECRET_KEY = os.environ.get('STRIPE_SECRET_KEY', '')
STRIPE_WEBHOOK_SECRET = os.environ.get('STRIPE_WEBHOOK_SECRET', '')

# Stripe Configuration
STRIPE_CURRENCY = getattr(settings, 'STRIPE_CURRENCY', 'usd')
STRIPE_API_VERSION = '2023-10-16'

# Success/Cancel URLs for Checkout (configure based on your frontend)
STRIPE_SUCCESS_URL = os.environ.get('STRIPE_SUCCESS_URL', 'http://localhost:3000/billing/success?session_id={CHECKOUT_SESSION_ID}')
STRIPE_CANCEL_URL = os.environ.get('STRIPE_CANCEL_URL', 'http://localhost:3000/billing/plans')

# Stripe Customer Portal URL (where users return after managing subscription)
STRIPE_PORTAL_RETURN_URL = os.environ.get('STRIPE_PORTAL_RETURN_URL', 'http://localhost:3000/billing')

# Enable/Disable Stripe Features
STRIPE_ENABLED = os.environ.get('STRIPE_ENABLED', 'True').lower() == 'true'
STRIPE_TEST_MODE = os.environ.get('STRIPE_TEST_MODE', 'True').lower() == 'true'

# Stripe Product Configuration
# Set to True to automatically sync plans to Stripe
STRIPE_AUTO_SYNC_PRODUCTS = os.environ.get('STRIPE_AUTO_SYNC_PRODUCTS', 'False').lower() == 'true'

# Validation
def validate_stripe_settings():
    """Validate that required Stripe settings are configured"""
    if not STRIPE_ENABLED:
        return True, "Stripe is disabled"
    
    if not STRIPE_SECRET_KEY:
        return False, "STRIPE_SECRET_KEY is not configured"
    
    if not STRIPE_PUBLISHABLE_KEY:
        return False, "STRIPE_PUBLISHABLE_KEY is not configured"
    
    return True, "Stripe is properly configured"

