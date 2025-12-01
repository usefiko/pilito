import os
from django.core.asgi import get_asgi_application
from django.conf import settings

# Configure Django settings before importing any Django modules
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

# Initialize Django ASGI application early to ensure Django is set up
django_asgi_app = get_asgi_application()

# Now import Channels and routing modules after Django is configured
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator, OriginValidator
from message.routing import websocket_urlpatterns
from message.middleware.websocket_auth import WebSocketAuthMiddleware, WebSocketSecurityMiddleware

class ProductionOriginValidator:
    """
    Custom origin validator for production environment
    """
    def __init__(self, application, allowed_origins=None):
        self.application = application
        self.allowed_origins = allowed_origins or []
    
    async def __call__(self, scope, receive, send):
        if scope["type"] == "websocket":
            headers = dict(scope["headers"])
            origin = headers.get(b"origin")
            
            if origin:
                origin_str = origin.decode("latin1")
                # در production, بررسی دقیق‌تر Origin
                if not any(allowed in origin_str for allowed in self.allowed_origins):
                    await send({"type": "websocket.close", "code": 4403})
                    return
        
        return await self.application(scope, receive, send)


# Production allowed origins
PRODUCTION_ALLOWED_ORIGINS = [
    # Pilito Production domains
    "https://app.pilito.com",
    "https://pilito.com",
    "https://api.pilito.com",
    "wss://api.pilito.com",
    "ws://api.pilito.com",
    # Development
    "http://localhost:3000",
    "http://localhost:5173",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:5173",
    "ws://localhost:8000",
    "wss://localhost:8000",
    # Server IP access
    "http://46.249.98.162",
    "http://46.249.98.162:8000",
    "ws://46.249.98.162:8000",
]

# Choose middleware stack based on environment
if getattr(settings, 'DEBUG', False):
    # Development: Relaxed authentication
    websocket_application = WebSocketAuthMiddleware(
        URLRouter(websocket_urlpatterns)
    )
else:
    # Production: Full security
    websocket_application = AllowedHostsOriginValidator(
        ProductionOriginValidator(
            WebSocketSecurityMiddleware(
                WebSocketAuthMiddleware(
                    URLRouter(websocket_urlpatterns)
                )
            ),
            allowed_origins=PRODUCTION_ALLOWED_ORIGINS
        )
    )

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": websocket_application,
})
