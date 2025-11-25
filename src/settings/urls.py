from django.urls import path
from settings.views import (
    PricesAPIView, DefaultReplyHandlerAPIView,
    AIPromptsAPIView, AIPromptsManualPromptAPIView,
    LatestUpToProAPIView, AIBehaviorSettingsView, AIBehaviorSettingsResetView
)
from settings.channels_view import ConnectTeleAPIView,DisConnectTeleAPIView,TeleBotAPIView
from message.insta import InstaChannelAPIView
from settings.support_views import (
    SupportTicketListCreateAPIView,
    SupportTicketDetailAPIView,
    SupportTicketCloseAPIView,
    SupportMessageListCreateAPIView,
    SupportStaffTicketListAPIView,
    SupportStatsAPIView
)
from settings.api.intercom_webhooks import intercom_webhook_handler


urlpatterns = [
    # channels
    path("tele-bot", TeleBotAPIView.as_view(), name="tele-bot"),
    path("connect-tele-bot", ConnectTeleAPIView.as_view(), name="connect-tele-bot"),
    path("dis-tele/<str:bot_name>/", DisConnectTeleAPIView.as_view(), name="dis-tele"),
    path("insta", InstaChannelAPIView.as_view(), name="insta"),
    # AI & Prompts
    path("reply-handler", DefaultReplyHandlerAPIView.as_view(), name="reply-handler"),
    path("ai-prompts/", AIPromptsAPIView.as_view(), name="ai-prompts"),
    path("ai-prompts/manual-prompt/", AIPromptsManualPromptAPIView.as_view(), name="ai-prompts-manual"),
    # AI Behavior Settings (NEW)
    path("ai-behavior/me/", AIBehaviorSettingsView.as_view(), name="ai-behavior-settings"),
    path("ai-behavior/reset/", AIBehaviorSettingsResetView.as_view(), name="ai-behavior-reset"),
    #path("ai", PricesAPIView.as_view(), name="ai"),
    # prices
    path("prices", PricesAPIView.as_view(), name="prices"),
    # UpToPro
    path("uptopro/latest/", LatestUpToProAPIView.as_view(), name="uptopro-latest"),
    # Support System
    path("support/tickets/", SupportTicketListCreateAPIView.as_view(), name="support-tickets"),
    path("support/tickets/<int:pk>/", SupportTicketDetailAPIView.as_view(), name="support-ticket-detail"),
    path("support/tickets/<int:pk>/close/", SupportTicketCloseAPIView.as_view(), name="support-ticket-close"),
    path("support/tickets/<int:ticket_id>/messages/", SupportMessageListCreateAPIView.as_view(), name="support-messages"),
    path("support/admin/tickets/", SupportStaffTicketListAPIView.as_view(), name="support-admin-tickets"),
    path("support/stats/", SupportStatsAPIView.as_view(), name="support-stats"),
    # Intercom Webhooks (for two-way sync)
    path("webhooks/intercom/", intercom_webhook_handler, name="intercom-webhook"),
]
