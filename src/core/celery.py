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

# ========================================
# 🚀 Priority Queue Configuration
# ⚠️ این تنظیمات باید بعد از config_from_object باشن
# چون اون settings از common.py رو override میکنه
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
    'web_knowledge.tasks.crawl_manual_urls_task': {
        'queue': 'low_priority',
        'routing_key': 'low.crawl',
    },
    
    # 📦 Auto-Chunking Tasks → Default Priority (balanced)
    'ai_model.chunk_webpage': {
        'queue': 'default',
        'routing_key': 'default.chunk',
    },
    'ai_model.chunk_qapair': {
        'queue': 'default',
        'routing_key': 'default.chunk',
    },
    'ai_model.chunk_product': {
        'queue': 'default',
        'routing_key': 'default.chunk',
    },
    'ai_model.chunk_manual_prompt': {
        'queue': 'default',
        'routing_key': 'default.chunk',
    },
    'ai_model.delete_chunks_for_source': {
        'queue': 'default',
        'routing_key': 'default.chunk',
    },
    
    # 📸 Media Processing → High Priority (user waiting!)
    'message.tasks_instagram_media.process_instagram_image': {
        'queue': 'high_priority',
        'routing_key': 'high.media',
    },
    'message.tasks_instagram_media.process_instagram_voice': {
        'queue': 'high_priority',
        'routing_key': 'high.media',
    },
    'message.tasks.process_telegram_image': {
        'queue': 'high_priority',
        'routing_key': 'high.media',
    },
    'message.tasks.process_telegram_voice': {
        'queue': 'high_priority',
        'routing_key': 'high.media',
    },
    
    # 💬 Message Sync Tasks → Default Priority
    'message.sync_conversation_to_intercom': {
        'queue': 'default',
        'routing_key': 'default.sync',
    },
    'message.sync_message_to_intercom': {
        'queue': 'default',
        'routing_key': 'default.sync',
    },
    
    # 🔄 Instagram Token Refresh → Low Priority (scheduled background task)
    'message.tasks.auto_refresh_instagram_tokens': {
        'queue': 'low_priority',
        'routing_key': 'low.maintenance',
    },
    'message.tasks.refresh_single_instagram_token': {
        'queue': 'low_priority',
        'routing_key': 'low.maintenance',
    },
    
    # ⚡ Workflow Tasks → Default Priority (user triggered)
    'workflow.tasks.process_event': {
        'queue': 'default',
        'routing_key': 'default.workflow',
    },
    'workflow.tasks.execute_workflow_action': {
        'queue': 'default',
        'routing_key': 'default.workflow',
    },
    'workflow.tasks.waiting_node_timeout': {
        'queue': 'default',
        'routing_key': 'default.workflow',
    },
    'workflow.tasks.resume_node_workflow_after_delay': {
        'queue': 'default',
        'routing_key': 'default.workflow',
    },
    
    # 📊 Scheduled Workflow Tasks → Low Priority
    'workflow.tasks.process_scheduled_triggers': {
        'queue': 'low_priority',
        'routing_key': 'low.workflow',
    },
    'workflow.tasks.execute_scheduled_workflow': {
        'queue': 'low_priority',
        'routing_key': 'low.workflow',
    },
    'workflow.tasks.process_scheduled_when_nodes': {
        'queue': 'low_priority',
        'routing_key': 'low.workflow',
    },
    'workflow.tasks.retry_failed_actions': {
        'queue': 'low_priority',
        'routing_key': 'low.workflow',
    },
    'workflow.tasks.cleanup_old_executions': {
        'queue': 'low_priority',
        'routing_key': 'low.workflow',
    },
    
    # 💰 Billing Tasks → Low Priority
    'billing.activate_queued_plans': {
        'queue': 'low_priority',
        'routing_key': 'low.billing',
    },
    'billing.expire_free_trial_subscriptions': {
        'queue': 'low_priority',
        'routing_key': 'low.billing',
    },
    
    # 📝 Web Knowledge Tasks → Default Priority (user-triggered)
    'web_knowledge.tasks.generate_prompt_async_task': {
        'queue': 'default',
        'routing_key': 'default.prompt',
    },
    
    # 📊 AI Analytics & Maintenance → Low Priority
    'AI_model.tasks.cleanup_old_usage_data': {
        'queue': 'low_priority',
        'routing_key': 'low.maintenance',
    },
    'AI_model.tasks.generate_usage_analytics': {
        'queue': 'low_priority',
        'routing_key': 'low.maintenance',
    },
    'AI_model.tasks.test_ai_configuration': {
        'queue': 'low_priority',
        'routing_key': 'low.maintenance',
    },
    'AI_model.tasks.ensure_global_config': {
        'queue': 'low_priority',
        'routing_key': 'low.maintenance',
    },
    'AI_model.tasks.reconcile_knowledge_base_task': {
        'queue': 'low_priority',
        'routing_key': 'low.maintenance',
    },
    'ai_model.reconcile_knowledge': {
        'queue': 'low_priority',
        'routing_key': 'low.maintenance',
    },
    
    # 🔌 Integration Tasks → Default Priority (WooCommerce, Shopify, WordPress)
    'integrations.tasks.process_woocommerce_product': {
        'queue': 'default',
        'routing_key': 'default.integration',
    },
    'integrations.tasks.process_wordpress_content': {
        'queue': 'default',
        'routing_key': 'default.integration',
    },
}

# Rate Limiting: محدود کردن تعداد crawl همزمان
app.conf.task_annotations = {
    'web_knowledge.tasks.crawl_website_task': {
        'rate_limit': '5/m',  # فقط 5 crawl در دقیقه
    },
    'web_knowledge.tasks.process_page_content_task': {
        'rate_limit': '100/m',  # 100 page process در دقیقه (افزایش یافته)
    },
}

# Performance tuning
app.conf.task_acks_late = True  # Task فقط بعد از اتمام acknowledge بشه
app.conf.worker_prefetch_multiplier = 1  # هر worker فقط 1 task بگیره
app.conf.worker_max_tasks_per_child = 50  # بعد از 50 task، worker restart بشه (memory leak جلوگیری)

# Configure timezone
app.conf.timezone = 'UTC'

# Load task modules from all registered Django apps
app.autodiscover_tasks()

# Also discover Instagram media tasks
app.autodiscover_tasks(['message'], related_name='tasks_instagram_media')

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