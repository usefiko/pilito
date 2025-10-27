"""
Feature Flags for AI Model Services
Allows gradual rollout and easy rollback
"""
import logging
from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)


class FeatureFlags:
    """
    Feature flags for AI services
    
    Usage:
        if FeatureFlags.is_enabled('production_rag'):
            use_production_rag()
        else:
            use_context_retriever()
    """
    
    # Default values (can be overridden in settings or cache)
    DEFAULTS = {
        # Production RAG
        'production_rag': False,  # ✅ Start disabled (safe rollout)
        'cross_encoder_reranking': False,
        
        # User-based rollout (% of users)
        'production_rag_rollout_percentage': 0,  # 0-100
        
        # Model selection
        'rerank_model': 'base',  # 'base' or 'large'
        
        # Performance tuning
        'dense_top_k': 20,
        'sparse_top_k': 15,
        'rerank_top_k': 8,
        
        # Debugging
        'production_rag_debug': False,
    }
    
    @classmethod
    def is_enabled(cls, flag_name: str) -> bool:
        """
        Check if a feature flag is enabled
        
        Priority:
        1. Cache (Django admin can set)
        2. Settings (environment variable)
        3. Default value
        
        Args:
            flag_name: Name of the feature flag
        
        Returns:
            bool: True if enabled
        """
        # Check cache first (fastest, allows runtime changes)
        cache_key = f'feature_flag:{flag_name}'
        cached_value = cache.get(cache_key)
        
        if cached_value is not None:
            return bool(cached_value)
        
        # Check Django settings
        settings_key = f'FEATURE_FLAG_{flag_name.upper()}'
        if hasattr(settings, settings_key):
            return bool(getattr(settings, settings_key))
        
        # Fall back to default
        return cls.DEFAULTS.get(flag_name, False)
    
    @classmethod
    def get_value(cls, flag_name: str, default=None):
        """
        Get value of a feature flag
        
        Args:
            flag_name: Name of the feature flag
            default: Default value if not found
        
        Returns:
            Value of the flag
        """
        # Check cache
        cache_key = f'feature_flag:{flag_name}'
        cached_value = cache.get(cache_key)
        
        if cached_value is not None:
            return cached_value
        
        # Check settings
        settings_key = f'FEATURE_FLAG_{flag_name.upper()}'
        if hasattr(settings, settings_key):
            return getattr(settings, settings_key)
        
        # Fall back to default
        if default is not None:
            return default
        
        return cls.DEFAULTS.get(flag_name)
    
    @classmethod
    def set_flag(cls, flag_name: str, value, ttl: int = 3600):
        """
        Set a feature flag (in cache)
        
        Args:
            flag_name: Name of the flag
            value: Value to set
            ttl: Time to live in seconds (default: 1 hour)
        """
        cache_key = f'feature_flag:{flag_name}'
        cache.set(cache_key, value, ttl)
        logger.info(f"🚩 Feature flag set: {flag_name} = {value}")
    
    @classmethod
    def is_enabled_for_user(cls, flag_name: str, user) -> bool:
        """
        Check if feature is enabled for specific user
        Supports percentage-based rollout
        
        Args:
            flag_name: Name of the feature
            user: User instance
        
        Returns:
            bool: True if enabled for this user
        """
        # Check if globally enabled
        if cls.is_enabled(flag_name):
            return True
        
        # Check percentage rollout
        rollout_key = f'{flag_name}_rollout_percentage'
        rollout_percentage = cls.get_value(rollout_key, 0)
        
        if rollout_percentage <= 0:
            return False
        
        if rollout_percentage >= 100:
            return True
        
        # Hash user ID to determine if in rollout
        if not user or not hasattr(user, 'id'):
            return False
        
        user_hash = hash(str(user.id))
        return (user_hash % 100) < rollout_percentage
    
    @classmethod
    def get_all_flags(cls) -> dict:
        """Get all feature flags with current values"""
        flags = {}
        
        for flag_name in cls.DEFAULTS.keys():
            flags[flag_name] = {
                'enabled': cls.is_enabled(flag_name),
                'value': cls.get_value(flag_name),
                'default': cls.DEFAULTS[flag_name]
            }
        
        return flags


# Convenience functions
def use_production_rag(user=None) -> bool:
    """Check if ProductionRAG should be used"""
    if user:
        return FeatureFlags.is_enabled_for_user('production_rag', user)
    return FeatureFlags.is_enabled('production_rag')


def get_rerank_model() -> str:
    """Get reranking model to use"""
    return FeatureFlags.get_value('rerank_model', 'base')

