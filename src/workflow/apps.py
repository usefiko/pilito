from django.apps import AppConfig



class WorkflowConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'workflow'
    
    def ready(self):
        """
        Initialize workflow app when Django starts.
        """
        try:
            # Import and connect signals
            from workflow.signals import connect_workflow_signals
            connect_workflow_signals()
            
            # Note: Event type registration moved to management command
            # to avoid database access during app initialization
            
        except Exception as e:
            # Don't fail app startup if workflow initialization fails
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Failed to initialize workflow app: {e}")
            