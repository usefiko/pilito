from pathlib import Path
from dotenv import load_dotenv
import os
from os import environ


load_dotenv()
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = environ.get("SECRET_KEY")

# SECURITY WARNING: don't run with debug turned on in production!
ALLOWED_HOSTS=['*']
"""
ALLOWED_HOSTS = [
    'api.fiko.net',
    'fiko.net',
    'app.fiko.net',
    'localhost',
    '127.0.0.1',
    '0.0.0.0',
    '18.119.134.7',
]
"""

# APP CONFIGURATION
DJANGO_APPS = (
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.admin",
    "django.contrib.admindocs",
    "django.contrib.sites",
)
THIRD_PARTY_APPS = (
    "rest_framework",
    "django_filters",
    "corsheaders",
    "gunicorn",
    "whitenoise",
    "import_export",
    "drf_yasg",
    "storages",
    "channels",
    "django_celery_beat",
)
# Apps specific for this project go here.
LOCAL_APPS = (
    "accounts",
    "settings",
    "billing",
    "message",
    "academy",
    "AI_model",
    "workflow",
    "web_knowledge",
    "workflow_template",
    "monitoring",
)
INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS
# END APP CONFIGURATION


MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'monitoring.middleware.PrometheusMetricsMiddleware',
    'monitoring.middleware.DatabaseMetricsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'core.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        "DIRS": [
            BASE_DIR / "templates/",
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'core.wsgi.application'
ASGI_APPLICATION = 'core.asgi.application'

# CHANNELS CONFIGURATION
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [environ.get("REDIS_URL", "redis://redis:6379")],
            # Optimize Redis channel layer for better performance
            "capacity": 1500,  # Default is 100
            "expiry": 60,      # Default is 60
            "group_expiry": 86400,  # 24 hours, default is 86400
            # Connection pool settings
            "symmetric_encryption_keys": [environ.get("DJANGO_SECRET_KEY", "fallback-key")[:32].ljust(32, 'x')],
        },
    },
}
# END CHANNELS CONFIGURATION


# CACHING CONFIGURATION
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": environ.get("REDIS_URL", "redis://redis:6379"),
        "TIMEOUT": 300,  # 5 minutes default timeout
    }
}


# Password validation
# https://docs.djangoproject.com/en/3.2/ref/settings/#auth-password-validators
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_L10N = True
USE_TZ = True

SITE_ID = 1


# --- S3 storages ---
AWS_ACCESS_KEY_ID = environ.get("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = environ.get("AWS_SECRET_ACCESS_KEY")
AWS_STORAGE_BUCKET_NAME = environ.get("AWS_STORAGE_BUCKET_NAME")
AWS_S3_REGION_NAME = environ.get("AWS_S3_REGION_NAME")
AWS_S3_CUSTOM_DOMAIN = f'{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com'
AWS_S3_FILE_OVERWRITE = False
AWS_DEFAULT_ACL = 'public-read'
AWS_S3_SIGNATURE_VERSION = "s3v4"

# Additional S3 settings to fix Access Denied issues
AWS_S3_OBJECT_PARAMETERS = {
    'CacheControl': 'max-age=86400',
}
AWS_QUERYSTRING_AUTH = False
AWS_S3_VERIFY = True
AWS_S3_USE_SSL = True

# Force django-storages to use the new ACL format
AWS_S3_OBJECT_ACL = 'public-read'

# Optimize S3 performance
AWS_PRELOAD_METADATA = False  # Disable preloading to avoid 404 errors
AWS_IS_GZIPPED = True  # Enable gzip compression

STATICFILES_STORAGE = 'core.settings.storage_backends.StaticStorage'
# Use MediaStoragePresigned if ACL issues persist
# DEFAULT_FILE_STORAGE = 'core.settings.storage_backends.MediaStorage'
# Uncomment the line below and comment the line above if you want to use pre-signed URLs instead
# DEFAULT_FILE_STORAGE = 'core.settings.storage_backends.MediaStoragePresigned'  # Commented out as STORAGES is used instead


# Django 4.2+ STORAGES setting (replaces DEFAULT_FILE_STORAGE)
STORAGES = {
    "default": {
        "BACKEND": "core.settings.storage_backends.MediaStoragePresigned",
    },
    "staticfiles": {
        "BACKEND": "core.settings.storage_backends.StaticStorage",
    },
}

STATIC_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/static/'
MEDIA_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/media/'

STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
# Ensure project-level static assets (like email images) are collected
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]
MEDIA_ROOT = 'media'

# Default primary key field type
# https://docs.djangoproject.com/en/3.2/ref/settings/#default-auto-field


DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# AUTH USER MODEL CONFIGURATION
AUTH_USER_MODEL = "accounts.User"
# END AUTH USER MODEL CONFIGURATION

APPEND_SLASH = False

# OTP CONFIGURATION
OTP_CODE_LENGTH = int(os.getenv("OTP_CODE_LENGTH", default="4"))
OTP_TTL = int(os.getenv("OTP_TTL", default="120"))
# END OTP CONFIGURATION

# JWT SETIINGS
JWT_SECRET = "jango-insecure-_#2hxi#d@7!6bg((p@tmy-)#y3i_ad=n!pm4@_h2c60+1m9gty"
ACCESS_TTL = int(os.getenv("ACCESS_TTL", default="7"))  # days
REFRESH_TTL = int(os.getenv("REFRESH_TTL", default="15"))  # days
# END JWT SETTINGS


# REST FRAMEWORK CONFIGURATION
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": ("accounts.backends.jwt_auth.JWTAuthentication",),
    'DEFAULT_FILTER_BACKENDS': ['django_filters.rest_framework.DjangoFilterBackend'],
    "DEFAULT_THROTTLE_RATES": {"otp": os.getenv("OTP_THROTTLE_RATE", default="10/min"), },
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 10,
}
# END REST FRAMEWORK CONFIGURATION


# ZARRINPAL CONFIGURATION
ZARRINPAL_URL="https://api.zarinpal.com/pg/"
ZARRINPAL_MERCHANT_ID = "38541d6c-9eb6-45f9-830e-7248be500437"
ZP_API_REQUEST = "https://www.zarinpal.com/pg/rest/WebGate/PaymentRequest.json"
ZP_API_VERIFY = "https://www.zarinpal.com/pg/rest/WebGate/PaymentVerification.json"
ZP_API_STARTPAY = "https://www.zarinpal.com/pg/StartPay/"
ZARIN_CALL_BACK = 'https://api.fiko.app/api/v1/billing/payment-verify/'
# END ZARRINPAL CONFIGURATION


# CORSHEADERS CONFIGURATION
CORS_ORIGIN_ALLOW_ALL = True
CORS_ALLOW_CREDENTIALS = True

# WebSocket CORS Settings - حل مشکل 403
CORS_ALLOWED_ORIGINS = [
    "https://app.fiko.net",
    "https://fiko.net",
    "https://api.fiko.net",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://0.0.0.0:8000",
    "http://localhost:5173",
    "http://172.27.192.1:5173",
    "http://192.168.1.6:5173",
    # Google OAuth domains
    'https://accounts.google.com',
    'https://oauth2.googleapis.com',
]

CSRF_TRUSTED_ORIGINS = [
    'http://localhost:8000',
    'http://localhost:3000',
    'https://app.fiko.net',
    'https://api.fiko.net',
    'https://fiko.net',
    'http://127.0.0.1:8000',
    'http://127.0.0.1:3000',
    "http://0.0.0.0:8000",
    "http://localhost:5173",
    "http://172.27.192.1:5173",
    "http://192.168.1.6:5173",
    # Google OAuth domains
    'https://accounts.google.com',
    'https://oauth2.googleapis.com',
]
# END CORSHEADERS CONFIGURATION


# GOOGLE OAUTH CONFIGURATION
GOOGLE_OAUTH2_CLIENT_ID = "474127607425-nspfkpns0k5r5nou0fmbvtatj2fak6rd.apps.googleusercontent.com"
GOOGLE_OAUTH2_CLIENT_SECRET = "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"
GOOGLE_OAUTH2_REDIRECT_URI = environ.get("GOOGLE_OAUTH2_REDIRECT_URI", "https://api.fiko.net/api/v1/usr/google/callback")
# Frontend redirect URL after successful authentication
GOOGLE_OAUTH2_FRONTEND_REDIRECT = environ.get("GOOGLE_OAUTH2_FRONTEND_REDIRECT", "https://app.fiko.net/auth/success")
# END GOOGLE OAUTH CONFIGURATION


# INTERCOM CONFIGURATION
INTERCOM_APP_ID = "fciihyj0"
INTERCOM_API_SECRET = "CRHagBsgI6q7xrjCOeG9EDk7yjqLANYFyHGjHahBm08"
INTERCOM_SESSION_DURATION = int(environ.get("INTERCOM_SESSION_DURATION", default="604800000"))  # 7 days in milliseconds

# Intercom REST API Integration (for syncing users, conversations, etc.)
INTERCOM_ACCESS_TOKEN = environ.get('INTERCOM_ACCESS_TOKEN', '')
INTERCOM_CLIENT_ID = environ.get('INTERCOM_CLIENT_ID', '')
INTERCOM_CLIENT_SECRET = environ.get('INTERCOM_CLIENT_SECRET', '')
INTERCOM_WEBHOOK_SECRET = environ.get('INTERCOM_WEBHOOK_SECRET', '')
INTERCOM_ADMIN_ID = environ.get('INTERCOM_ADMIN_ID', '')  # Admin ID for ticket replies
INTERCOM_API_BASE_URL = 'https://api.intercom.io'
INTERCOM_API_VERSION = '2.14'  # Intercom API version (latest)
# Note: Ticket Type IDs are now managed via IntercomTicketType model in Admin Panel
# END INTERCOM CONFIGURATION

# ============================================================================
# BASE URL CONFIGURATION (for generating absolute URLs)
# ============================================================================
BASE_URL = environ.get('BASE_URL', 'https://api.fiko.net')


# STRIPE PAYMENT CONFIGURATION
STRIPE_PUBLISHABLE_KEY = environ.get('STRIPE_PUBLISHABLE_KEY', '')
STRIPE_SECRET_KEY = environ.get('STRIPE_SECRET_KEY', '')
STRIPE_WEBHOOK_SECRET = environ.get('STRIPE_WEBHOOK_SECRET', '')
STRIPE_ENABLED = environ.get('STRIPE_ENABLED', 'True').lower() == 'true'
STRIPE_TEST_MODE = environ.get('STRIPE_TEST_MODE', 'True').lower() == 'true'
STRIPE_CURRENCY = environ.get('STRIPE_CURRENCY', 'usd')
STRIPE_API_VERSION = '2023-10-16'
STRIPE_SUCCESS_URL = environ.get('STRIPE_SUCCESS_URL', 'https://app.fiko.net/dashboard/profile?payment=success&session_id={CHECKOUT_SESSION_ID}#billing')
STRIPE_CANCEL_URL = environ.get('STRIPE_CANCEL_URL', 'https://app.fiko.net/dashboard/profile?payment=cancelled#billing')
STRIPE_PORTAL_RETURN_URL = environ.get('STRIPE_PORTAL_RETURN_URL', 'https://app.fiko.net/dashboard/profile#billing')
# END STRIPE PAYMENT CONFIGURATION


# EMAIL CONFIGURATION
# Use environment variables for email backend selection
EMAIL_BACKEND = environ.get('EMAIL_BACKEND', 'django.core.mail.backends.smtp.EmailBackend')

# AWS SES SMTP Configuration
EMAIL_HOST = environ.get('EMAIL_HOST', 'email-smtp.us-east-2.amazonaws.com')
EMAIL_PORT = int(environ.get('EMAIL_PORT', '587'))
EMAIL_USE_TLS = environ.get('EMAIL_USE_TLS', 'True').lower() == 'true'
EMAIL_USE_SSL = environ.get('EMAIL_USE_SSL', 'False').lower() == 'true'
EMAIL_HOST_USER = environ.get('EMAIL_HOST_USER', 'AKIARTLO5HLCKHLZ7KWR')
EMAIL_HOST_PASSWORD = environ.get('EMAIL_HOST_PASSWORD', 'BLrFuGxymqJxlgcGdrWLJXFfX4+pMc33Dqi43J/av31h')
EMAIL_TIMEOUT = int(environ.get('EMAIL_TIMEOUT', '30'))

DEFAULT_FROM_EMAIL = environ.get('DEFAULT_FROM_EMAIL', 'noreply@fiko.net')
# Email sender display name configuration
DEFAULT_FROM_EMAIL_DISPLAY = 'Fiko <noreply@fiko.net>'
# END EMAIL CONFIGURATION


# FILE UPLOAD CONFIGURATION
# Maximum size in bytes for a single file upload (500MB)
FILE_UPLOAD_MAX_MEMORY_SIZE = 524288000  # 500MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 524288000  # 500MB
# Maximum number of fields that can be uploaded (for forms with many fields)
DATA_UPLOAD_MAX_NUMBER_FIELDS = 10000
# END FILE UPLOAD CONFIGURATION


# CELERY CONFIGURATION
# Redis connection for Celery
CELERY_BROKER_URL = environ.get("REDIS_URL", "redis://redis:6379")
CELERY_RESULT_BACKEND = environ.get("REDIS_URL", "redis://redis:6379")

# Accept messages in JSON format only (security)
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'

# Task time limit (30 minutes)
CELERY_TASK_TIME_LIMIT = 30 * 60
CELERY_TASK_SOFT_TIME_LIMIT = 25 * 60

# Task routing
CELERY_TASK_ROUTES = {
    'message.tasks.auto_refresh_instagram_tokens': {'queue': 'instagram_tokens'},
    'message.tasks.refresh_single_instagram_token': {'queue': 'instagram_tokens'},
    # AI tasks (updated to match actual task names)
    'AI_model.tasks.process_ai_response_async': {'queue': 'ai_tasks'},
    'AI_model.tasks.cleanup_old_usage_data': {'queue': 'ai_tasks'},
    'AI_model.tasks.generate_usage_analytics': {'queue': 'ai_tasks'},
    'AI_model.tasks.sync_conversation_ai_status': {'queue': 'ai_tasks'},
    'AI_model.tasks.test_ai_configuration': {'queue': 'ai_tasks'},
    # Workflow tasks
    'workflow.tasks.process_event': {'queue': 'workflow_tasks'},
    'workflow.tasks.execute_workflow_action': {'queue': 'workflow_tasks'},
    'workflow.tasks.execute_scheduled_workflow': {'queue': 'workflow_tasks'},
    'workflow.tasks.process_scheduled_triggers': {'queue': 'workflow_tasks'},
    'workflow.tasks.process_scheduled_when_nodes': {'queue': 'workflow_tasks'},
    'workflow.tasks.retry_failed_actions': {'queue': 'workflow_tasks'},
    'workflow.tasks.cleanup_old_executions': {'queue': 'workflow_tasks'},
}

# Timezone
CELERY_TIMEZONE = TIME_ZONE

# Task discovery
CELERY_IMPORTS = [
    'message.tasks',
    'AI_model.tasks',
    'web_knowledge.tasks',
    'workflow.tasks',
]

# Celery Beat (Periodic Tasks) Configuration
CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers:DatabaseScheduler'

# Periodic task schedule
from celery.schedules import crontab
CELERY_BEAT_SCHEDULE = {
    'auto-refresh-instagram-tokens': {
        'task': 'message.tasks.auto_refresh_instagram_tokens',
        'schedule': crontab(hour=3, minute=0),  # Every day at 3:00 AM
        'kwargs': {'days_before_expiry': 7},  # Refresh tokens expiring within 7 days
        'options': {
            'queue': 'instagram_tokens',
            'routing_key': 'instagram_tokens',
        }
    },
    'emergency-refresh-instagram-tokens': {
        'task': 'message.tasks.auto_refresh_instagram_tokens',
        'schedule': crontab(hour='*/6'),  # Every 6 hours
        'kwargs': {'days_before_expiry': 1},  # Emergency refresh for tokens expiring within 1 day
        'options': {
            'queue': 'instagram_tokens',
            'routing_key': 'instagram_tokens',
        }
    },
    # Billing Tasks
    'activate-queued-plans': {
        'task': 'billing.activate_queued_plans',
        'schedule': crontab(hour=4, minute=0),  # Every day at 4:00 AM
        'options': {
            'queue': 'default',
        }
    },
    # AI Model Tasks (updated names)
    'cleanup-old-usage-data': {
        'task': 'AI_model.tasks.cleanup_old_usage_data',
        'schedule': crontab(hour=2, minute=0),  # Every day at 2:00 AM
        'options': {
            'queue': 'ai_tasks',
        }
    },
    'generate-usage-analytics': {
        'task': 'AI_model.tasks.generate_usage_analytics',
        'schedule': crontab(hour=1, minute=0),  # Every day at 1:00 AM
        'options': {
            'queue': 'ai_tasks',
        }
    },
    'sync-conversation-ai-status': {
        'task': 'AI_model.tasks.sync_conversation_ai_status',
        'schedule': crontab(minute='*/30'),  # Every 30 minutes
        'options': {
            'queue': 'ai_tasks',
        }
    },
    'test-ai-configuration': {
        'task': 'AI_model.tasks.test_ai_configuration',
        'schedule': crontab(hour='*/12'),  # Every 12 hours
        'options': {
            'queue': 'ai_tasks',
        }
    },
    # Workflow Tasks
    'process-scheduled-triggers': {
        'task': 'workflow.tasks.process_scheduled_triggers',
        'schedule': crontab(minute='*/5'),  # Every 5 minutes
        'options': {
            'queue': 'workflow_tasks',
        }
    },
    'retry-failed-workflow-actions': {
        'task': 'workflow.tasks.retry_failed_actions',
        'schedule': crontab(minute='*/15'),  # Every 15 minutes
        'options': {
            'queue': 'workflow_tasks',
        }
    },
    'cleanup-old-workflow-executions': {
        'task': 'workflow.tasks.cleanup_old_executions',
        'schedule': crontab(hour=4, minute=0),  # Every day at 4:00 AM
        'kwargs': {'days': 30},  # Keep 30 days of data
        'options': {
            'queue': 'workflow_tasks',
        }
    },
    # New: run scheduled When nodes every minute
    'process-scheduled-when-nodes': {
        'task': 'workflow.tasks.process_scheduled_when_nodes',
        'schedule': crontab(minute='*'),
        'options': {
            'queue': 'workflow_tasks',
        }
    },
}

STRIPE_WEBHOOK_SECRET = environ.get("STRIPE_WEBHOOK_SECRET")


# Worker configuration
CELERY_WORKER_CONCURRENCY = 2
CELERY_WORKER_MAX_TASKS_PER_CHILD = 50

# Monitoring
CELERY_SEND_TASK_EVENTS = True
CELERY_TASK_SEND_SENT_EVENT = True
# END CELERY CONFIGURATION

# ============================================================================
# RAPIDAPI CONFIGURATION (Instagram Profile Scraper)
# ============================================================================
RAPIDAPI_KEY = environ.get("RAPIDAPI_KEY", "")
INSTAGRAM_PROFILE_CACHE_TTL = 30 * 24 * 60 * 60  # 30 days

