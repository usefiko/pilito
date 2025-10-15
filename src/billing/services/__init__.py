"""
Billing Services
"""
from .stripe_service import StripeService

# Use direct file import to avoid package/module name conflict
# (billing.services.py exists alongside billing.services/ directory)
def consume_tokens_for_user(*args, **kwargs):
    """Proxy function to avoid circular import at module level"""
    import importlib.util
    import os
    import billing
    
    # Get path to billing/services.py (the file, not this package)
    billing_path = os.path.dirname(billing.__file__)
    services_file = os.path.join(billing_path, 'services.py')
    
    # Load module directly from file
    spec = importlib.util.spec_from_file_location("_billing_services_module", services_file)
    services_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(services_module)
    
    return services_module.consume_tokens_for_user(*args, **kwargs)

__all__ = ['StripeService', 'consume_tokens_for_user']
