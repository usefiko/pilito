import os
from celery import Celery
from django.conf import settings


# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.production')

app = Celery('fiko_backend')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django apps.
app.autodiscover_tasks()

# Configure timezone
app.conf.timezone = 'UTC'

# Periodic tasks schedule (Celery Beat)
app.conf.beat_schedule = {
    'reconcile-knowledge-base-nightly': {
        'task': 'AI_model.tasks.reconcile_knowledge_base_task',
        'schedule': 60 * 60 * 24,  # Every 24 hours
        'options': {
            'expires': 60 * 60 * 2,  # Expire after 2 hours if not picked up
        },
    },
}

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')