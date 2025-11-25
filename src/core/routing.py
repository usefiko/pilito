from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator
from message.routing import websocket_urlpatterns
from message.middleware.websocket_auth import WebSocketAuthMiddleware, WebSocketSecurityMiddleware

# Simplified version for easier development
application = ProtocolTypeRouter({
    'websocket': URLRouter(websocket_urlpatterns)
})

# Version with basic auth (optional)
# application = ProtocolTypeRouter({
#     'websocket': WebSocketAuthMiddleware(
#         URLRouter(websocket_urlpatterns)
#     )
# })

# Full security version (use in production)
# application = ProtocolTypeRouter({
#     'websocket': AllowedHostsOriginValidator(
#         WebSocketSecurityMiddleware(
#             WebSocketAuthMiddleware(
#                 URLRouter(websocket_urlpatterns)
#             )
#         )
#     ),
# }) 