from .common import *
DEBUG=True

# Production Logging Configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'production': {
            'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
        },
        'json': {
            'format': '{"time": "%(asctime)s", "level": "%(levelname)s", "logger": "%(name)s", "message": "%(message)s"}'
        }
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'production',
            'level': 'WARNING'  # Only warnings and errors in production console
        },
        'file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'formatter': 'production',
            'filename': '/var/log/fiko/app.log',
            'maxBytes': 10485760,  # 10MB
            'backupCount': 5
        }
    },
    'loggers': {
        # Suppress verbose third-party logs
        'boto3': {'level': 'ERROR', 'handlers': ['console', 'file'], 'propagate': False},
        'botocore': {'level': 'ERROR', 'handlers': ['console', 'file'], 'propagate': False},
        'urllib3': {'level': 'ERROR', 'handlers': ['console', 'file'], 'propagate': False},
        's3transfer': {'level': 'ERROR', 'handlers': ['console', 'file'], 'propagate': False},
        
        # Suppress PostgreSQL collation warnings
        'django.db.backends.postgresql': {'level': 'ERROR', 'handlers': ['console', 'file'], 'propagate': False},
        'django.db.backends.postgresql.base': {'level': 'ERROR', 'handlers': ['console', 'file'], 'propagate': False},
        'django.db.backends': {'level': 'ERROR', 'handlers': ['console', 'file'], 'propagate': False},
        'psycopg': {'level': 'ERROR', 'handlers': ['console', 'file'], 'propagate': False},
        'asyncio': {'level': 'ERROR', 'handlers': ['console', 'file'], 'propagate': False},
        'daphne.server': {'level': 'ERROR', 'handlers': ['console', 'file'], 'propagate': False},
        'daphne.access': {'level': 'ERROR', 'handlers': ['console', 'file'], 'propagate': False},
        
        # Suppress Daphne/Channels verbose logs
        'daphne.ws_protocol': {'level': 'ERROR', 'handlers': ['console', 'file'], 'propagate': False},
        'daphne.http_protocol': {'level': 'ERROR', 'handlers': ['console', 'file'], 'propagate': False},
        
        # App loggers - production levels
        'message.consumers': {'level': 'WARNING', 'handlers': ['console', 'file'], 'propagate': False},
        'message.middleware.websocket_auth': {'level': 'ERROR', 'handlers': ['console', 'file'], 'propagate': False},
        'message': {'level': 'INFO', 'handlers': ['console', 'file'], 'propagate': False},
        
        # Django logs
        'django': {'level': 'WARNING', 'handlers': ['console', 'file'], 'propagate': False},
        'django.request': {'level': 'ERROR', 'handlers': ['console', 'file'], 'propagate': False},
        'django.security': {'level': 'WARNING', 'handlers': ['console', 'file'], 'propagate': False},
        
        # Root logger
        '': {'level': 'WARNING', 'handlers': ['console', 'file']}
    }
}
try:
    import sentry_sdk
    from sentry_sdk.integrations.django import DjangoIntegration
    SENTRY_AVAILABLE = True
except ImportError:
    SENTRY_AVAILABLE = False
    print("⚠️  Sentry SDK not available - error monitoring disabled")


# PRODUCTION ALLOWED HOSTS - مهم برای WebSocket
ALLOWED_HOSTS = [
    'api.pilito.com',
    'pilito.com',
    'app.pilito.com',
    'localhost',
    '127.0.0.1',
    '0.0.0.0',
    '185.164.72.165',
    # Docker internal network hostnames for monitoring
    'web',
    'django_app',
    'prometheus',
    'grafana',
    'celery_worker',
    'celery_beat',
    'redis_exporter',
    'postgres_exporter',
]

# Override CORS settings from common.py
CORS_ORIGIN_ALLOW_ALL = False  # امنیت بیشتر در production
CORS_ALLOW_CREDENTIALS = True

# WebSocket CORS Settings - حل مشکل 403
CORS_ALLOWED_ORIGINS = [
    "https://app.pilito.net",
    "https://pilito.net",
    "https://api.pilito.net",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://0.0.0.0:8000",
    "http://localhost:5173",
    "http://185.164.72.165:8000",
    "http://185.164.72.165:5173",
    "http://185.164.72.165:5173",
    # Google OAuth domains
    "https://accounts.google.com",
    "https://oauth2.googleapis.com",
]

# CSRF settings برای WebSocket
CSRF_TRUSTED_ORIGINS = [
    'https://app.pilito.net',
    'https://api.pilito.net',
    'https://pilito.net',
    'http://localhost:8000',
    'http://localhost:3000',
    'http://127.0.0.1:8000',
    'http://127.0.0.1:3000',
    "http://0.0.0.0:8000",
    "http://localhost:5173",
    "http://185.164.72.165:8000",
    "http://185.164.72.165:5173",
    "http://185.164.72.165:5173",
    # Google OAuth domains
    'https://accounts.google.com',
    'https://oauth2.googleapis.com',
]

# WebSocket Origin Validation
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [environ.get("REDIS_URL", "redis://redis:6379")],
            # تنظیمات اضافی برای production
            "capacity": 1500,
            "expiry": 60,
        },
    },
}

# Security Headers for WebSocket
SECURE_WEBSOCKET_ORIGIN_ALLOWED = True
WEBSOCKET_ACCEPT_ALL_ORIGINS = False  # امنیت بیشتر

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': environ.get("POSTGRES_DB"),
        'USER': environ.get("POSTGRES_USER"),
        'PASSWORD': environ.get("POSTGRES_PASSWORD"),
        'HOST':'db',
        'PORT': 5432,
        'OPTIONS': {
            'options': '-c client_min_messages=error'
        }
    }
}


# Configure Sentry if available
if SENTRY_AVAILABLE:
    sentry_sdk.init(
        dsn="https://7b512e5f879f41dcbaeb25d4c8b3900b@o1070704.ingest.sentry.io/6066938",
        integrations=[DjangoIntegration()],
        traces_sample_rate=1.0,
        send_default_pii=True
    )
    print("✅ Sentry error monitoring enabled")

# Logging Configuration برای Debug کردن WebSocket
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': '/app/logs/django.log',
        },
        'console': {
            'level': 'WARNING',
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        # Suppress verbose AWS SDK logs
        'boto3': {
            'handlers': ['file', 'console'],
            'level': 'WARNING',
            'propagate': False,
        },
        'botocore': {
            'handlers': ['file', 'console'],
            'level': 'WARNING',
            'propagate': False,
        },
        'urllib3': {
            'handlers': ['file', 'console'],
            'level': 'WARNING',
            'propagate': False,
        },
        's3transfer': {
            'handlers': ['file', 'console'],
            'level': 'WARNING',
            'propagate': False,
        },
        # Suppress Daphne/Channels access chatter
        'daphne.access': {
            'handlers': ['file', 'console'],
            'level': 'ERROR',
            'propagate': False,
        },
        'daphne.server': {
            'handlers': ['file', 'console'],
            'level': 'ERROR',
            'propagate': False,
        },
        'daphne.ws_protocol': {
            'handlers': ['file', 'console'],
            'level': 'ERROR',
            'propagate': False,
        },
        'daphne.http_protocol': {
            'handlers': ['file', 'console'],
            'level': 'ERROR',
            'propagate': False,
        },
        'twisted': {
            'handlers': ['file', 'console'],
            'level': 'ERROR',
            'propagate': False,
        },
        # Application specific loggers
        'message.consumers': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': True,
        },
        'message.middleware': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': True,
        },
        # Suppress noisy JWT cache warnings in production
        'accounts.functions.jwt': {
            'handlers': ['file', 'console'],
            'level': 'ERROR',
            'propagate': False,
        },
        'channels': {
            'handlers': ['file', 'console'],
            'level': 'WARNING',
            'propagate': True,
        },
        'django': {
            'handlers': ['file', 'console'],
            'level': 'WARNING',
            'propagate': True,
        },
    },
}

