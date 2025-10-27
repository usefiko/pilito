import os
from celery import Celery
from django.conf import settings
from kombu import Queue, Exchange


# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.production')

app = Celery('fiko_backend')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django apps.
app.autodiscover_tasks()

# Also discover Instagram media tasks
app.autodiscover_tasks(['message'], related_name='tasks_instagram_media')

# Configure timezone
app.conf.timezone = 'UTC'

# ========================================
# 🚀 Priority Queue Configuration
# ========================================
# تعریف Queue های جداگانه با اولویت
app.conf.task_queues = [
    # Queue با اولویت بالا برای AI Chat (کاربر منتظره!)
    Queue('high_priority', 
          Exchange('high_priority'), 
          routing_key='high.#',
          priority=10,
          queue_arguments={'x-max-priority': 10}),
    
    # Queue عادی برای کارهای معمولی
    Queue('default', 
          Exchange('default'), 
          routing_key='default.#',
          priority=5,
          queue_arguments={'x-max-priority': 10}),
    
    # Queue با اولویت پایین برای Background tasks
    Queue('low_priority', 
          Exchange('low_priority'), 
          routing_key='low.#',
          priority=1,
          queue_arguments={'x-max-priority': 10}),
]

# تنظیم routing: کدوم task به کدوم queue بره
app.conf.task_routes = {
    # ⭐ AI Tasks → High Priority
    'AI_model.tasks.process_ai_response_async': {
        'queue': 'high_priority',
        'routing_key': 'high.ai',
    },
    
    # 🔽 Crawl & Background → Low Priority
    'web_knowledge.tasks.crawl_website_task': {
        'queue': 'low_priority',
        'routing_key': 'low.crawl',
    },
    'web_knowledge.tasks.process_page_content_task': {
        'queue': 'low_priority',
        'routing_key': 'low.crawl',
    },
    'web_knowledge.tasks.recrawl_website_task': {
        'queue': 'low_priority',
        'routing_key': 'low.crawl',
    },
    
    # 📊 Analytics & Cleanup → Low Priority
    'AI_model.tasks.reconcile_knowledge_base_task': {
        'queue': 'low_priority',
        'routing_key': 'low.maintenance',
    },
    'workflow.tasks.process_scheduled_when_nodes': {
        'queue': 'low_priority',
        'routing_key': 'low.workflow',
    },
}

# Rate Limiting: محدود کردن تعداد crawl همزمان
app.conf.task_annotations = {
    'web_knowledge.tasks.crawl_website_task': {
        'rate_limit': '5/m',  # فقط 5 crawl در دقیقه
    },
    'web_knowledge.tasks.process_page_content_task': {
        'rate_limit': '30/m',  # 30 page process در دقیقه
    },
}

# Performance tuning
app.conf.task_acks_late = True  # Task فقط بعد از اتمام acknowledge بشه
app.conf.worker_prefetch_multiplier = 1  # هر worker فقط 1 task بگیره
app.conf.worker_max_tasks_per_child = 50  # بعد از 50 task، worker restart بشه (memory leak جلوگیری)

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