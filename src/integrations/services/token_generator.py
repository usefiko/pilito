import secrets
import string


class TokenGenerator:
    """Generate secure tokens for integrations"""
    
    @staticmethod
    def generate_woocommerce_token() -> str:
        """
        Generate WooCommerce-style token
        
        Format: wc_sk_live_{40 random chars}
        Example: wc_sk_live_a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0
        """
        alphabet = string.ascii_lowercase + string.digits
        random_part = ''.join(secrets.choice(alphabet) for _ in range(40))
        return f"wc_sk_live_{random_part}"
    
    @staticmethod
    def generate_shopify_token() -> str:
        """Generate Shopify-style token"""
        alphabet = string.ascii_lowercase + string.digits
        random_part = ''.join(secrets.choice(alphabet) for _ in range(32))
        return f"shpat_{random_part}"
    
    @staticmethod
    def get_token_preview(token: str, show_first: int = 6, show_last: int = 6) -> str:
        """
        Create safe preview of token
        
        Example:
            wc_sk_live_a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0
            -> wc_sk...s9t0
        """
        if len(token) < show_first + show_last + 3:
            return token[:show_first] + '...'
        return token[:show_first] + '...' + token[-show_last:]

