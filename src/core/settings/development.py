from .common import *
import sys
DEBUG=True


LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '%(asctime)s %(name)-20s %(levelname)-8s %(message)s'
        },
        'simple': {
            'format': '%(name)-20s %(levelname)-8s %(message)s'
        },
        'minimal': {
            'format': '%(levelname)-8s %(message)s'
        }
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
            'level': 'INFO'  # Only show INFO and above in console
        },
        'file': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose'
        }
    },
    'loggers': {
        # Suppress verbose AWS SDK logs
        'boto3': {
            'level': 'WARNING',
            'handlers': ['console', 'file'],
            'propagate': False
        },
        'botocore': {
            'level': 'WARNING',
            'handlers': ['console', 'file'],
            'propagate': False
        },
        'urllib3': {
            'level': 'WARNING',
            'handlers': ['console', 'file'],
            'propagate': False
        },
        's3transfer': {
            'level': 'WARNING',
            'handlers': ['console', 'file'],
            'propagate': False
        },
        
        # Suppress PostgreSQL collation warnings
        'django.db.backends.postgresql': {
            'level': 'ERROR',
            'handlers': ['console', 'file'],
            'propagate': False
        },
        'django.db.backends.postgresql.base': {
            'level': 'ERROR',
            'handlers': ['console', 'file'],
            'propagate': False
        },
        
        # Reduce Django Channels/Daphne verbosity
        'daphne.ws_protocol': {
            'level': 'WARNING',  # Suppress DEBUG WebSocket protocol messages
            'handlers': ['console', 'file'],
            'propagate': False
        },
        'daphne.http_protocol': {
            'level': 'WARNING',  # Suppress DEBUG HTTP protocol messages
            'handlers': ['console', 'file'],
            'propagate': False
        },
        
        # Your app loggers - reduce verbosity
        'message.consumers': {
            'level': 'INFO',  # Only show INFO and above for WebSocket consumers
            'handlers': ['console', 'file'],
            'propagate': False
        },
        'message.middleware.websocket_auth': {
            'level': 'WARNING',  # Only show warnings and errors for auth
            'handlers': ['console', 'file'],
            'propagate': False
        },
        
        # Keep other message module logs at INFO level
        'message': {
            'level': 'INFO',
            'handlers': ['console', 'file'],
            'propagate': False
        },
        
        # Django root logger - less verbose
        'django': {
            'level': 'INFO',
            'handlers': ['console', 'file'],
            'propagate': False
        },
        
        # Default for everything else - less verbose
        '': {
            'level': 'INFO',  # Changed from DEBUG to INFO
            'handlers': ['console', 'file']
        }
    }
}



# EMAIL CONFIGURATION FOR DEVELOPMENT
# Use console backend for development unless EMAIL_BACKEND is explicitly set
EMAIL_BACKEND = environ.get('EMAIL_BACKEND', 'django.core.mail.backends.console.EmailBackend')

# GOOGLE OAUTH CONFIGURATION FOR DEVELOPMENT
# Override production URLs with development URLs
GOOGLE_OAUTH2_REDIRECT_URI = environ.get("GOOGLE_OAUTH2_REDIRECT_URI", "http://localhost:8000/api/v1/usr/google/callback")
GOOGLE_OAUTH2_FRONTEND_REDIRECT = environ.get("GOOGLE_OAUTH2_FRONTEND_REDIRECT", "http://localhost:3000/auth/success")

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': environ.get("POSTGRES_DB"),
        'USER': environ.get("POSTGRES_USER"),
        'PASSWORD': environ.get("POSTGRES_PASSWORD"),
        'HOST':'db',
        'PORT': 5432
    }
}