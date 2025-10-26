from django.urls import re_path
from . import consumers
from accounts.consumers import WizardStatusConsumer

websocket_urlpatterns = [
    re_path(r'^ws/chat/(?P<conversation_id>\w+)/$', consumers.ChatConsumer.as_asgi()),
    re_path(r'^ws/conversations/$', consumers.ConversationListConsumer.as_asgi()),
    re_path(r'^ws/customers/$', consumers.CustomerListConsumer.as_asgi()),
    re_path(r'^ws/wizard-status/$', WizardStatusConsumer.as_asgi()),
]
