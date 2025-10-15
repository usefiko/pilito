from django.apps import AppConfig


class MonitoringConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'monitoring'
    verbose_name = 'Monitoring & Metrics'

    def ready(self):
        """Initialize metrics when Django starts"""
        from . import metrics  # noqa

