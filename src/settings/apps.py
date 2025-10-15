from django.apps import AppConfig
import logging

logger = logging.getLogger(__name__)

class SettingsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'settings'
    verbose_name = 'System Settings'
    
    def ready(self):
        """
        Initialize settings app signals when Django starts
        """
        try:
            # Import signals to register them
            from . import signals
            logger.info("✅ Settings app initialized with Intercom ticket sync signals")
        except Exception as e:
            logger.error(f"❌ Error initializing settings signals: {e}")
