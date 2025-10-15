from django.apps import AppConfig


class AiModelConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'AI_model'
    verbose_name = '🤖 AI Model'
    
    def ready(self):
        """
        Initialize the AI model app when Django starts
        """
        try:
            # Import signals module to register all @receiver decorators
            import AI_model.signals
            
            # Also connect legacy signals
            from AI_model.signals import connect_ai_signals
            connect_ai_signals()
            
            import logging
            logger = logging.getLogger(__name__)
            logger.info("AI Model app initialized successfully (with auto-chunking signals)")
            
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error initializing AI Model app: {str(e)}")