from django.apps import AppConfig


class WebKnowledgeConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'web_knowledge'
    verbose_name = 'Web Knowledge'
    
    def ready(self):
        """Initialize app when Django starts"""
        # Import signals to connect them
        import web_knowledge.signals  # noqa