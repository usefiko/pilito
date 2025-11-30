from django.urls import path
from message.api import FullUserConversationsAPIView,UserConversationsAPIView,ConversationItemAPIView,TagsAPIView,\
    CustomersListAPIView,CustomerItemAPIView,UserMessagesAPIView,SupportAnswerAPIView,ActivateAllUserConversationsAPIView,DisableAllUserConversationsAPIView
from message.api.customer import CustomerBulkDeleteAPIView, CustomerBulkExportAPIView
from message.api.customer_tags import CustomerTagsAPIView, CustomerSingleTagAPIView
from message.api.tag import TagItemAPIView, TagBulkDeleteAPIView
from message.api.instagram_callback import (
    InstagramAuthURLAPIView,
    InstagramAuthURLWizardAPIView,
    InstagramCallbackAPIView, 
    InstagramDeauthorizeAPIView, 
    InstagramDataDeletionAPIView, 
    InstagramDeletionStatusAPIView
)
from message.api.send_message import SendMessageAPIView, ConversationStatusAPIView
from message.api.message import submit_message_feedback
from message.telegram_bot import telegram_webhook,TelegramWebhook
from message.insta import InstaWebhook, InstaChannelDebugAPIView, InstaChannelUpdatePageIdAPIView, InstaChannelAutoFixIDsAPIView
from message.api.intercom_webhook import IntercomWebhookView



urlpatterns = [
    # Tag Management APIs
    path("tags", TagsAPIView.as_view(), name="tags"),
    path("tags/<int:tag_id>/", TagItemAPIView.as_view(), name="tag-item"),
    path("tags/bulk-delete/", TagBulkDeleteAPIView.as_view(), name="tags-bulk-delete"),
    
    # Message APIs
    path("user-conversation", UserConversationsAPIView.as_view(), name="user-conversation"),
    path("user-conversation-full", FullUserConversationsAPIView.as_view(), name="user-conversation-full"),
    path("conversation-item/<str:id>/", ConversationItemAPIView.as_view(), name="conversation-item"),
    path("conversations/activate-all/", ActivateAllUserConversationsAPIView.as_view(), name="activate-all-conversations"),
    path("conversations/disable-all/", DisableAllUserConversationsAPIView.as_view(), name="disable-all-conversations"),
    path("customers", CustomersListAPIView.as_view(), name="customers"),
    path("customer-item/<int:id>/", CustomerItemAPIView.as_view(), name="customer-item"),
    path("customers/bulk-delete/", CustomerBulkDeleteAPIView.as_view(), name="customers-bulk-delete"),
    path("customers/bulk-export/", CustomerBulkExportAPIView.as_view(), name="customers-bulk-export"),
    
    # Customer Tags Management
    path("customer/<int:customer_id>/tags/", CustomerTagsAPIView.as_view(), name="customer-tags"),
    path("customer/<int:customer_id>/tags/<int:tag_id>/", CustomerSingleTagAPIView.as_view(), name="customer-single-tag"),
    
    path("user-messages", UserMessagesAPIView.as_view(), name="user-messages"),
    path("support-answer/<str:id>/", SupportAnswerAPIView.as_view(), name="support-answer"),
    
    # Response Quality Feedback (Phase 1 - Feature 2)
    path("message/<str:message_id>/feedback/", submit_message_feedback, name="submit-message-feedback"),
    
    # New WebSocket-integrated APIs
    path("conversation/<str:conversation_id>/send-message/", SendMessageAPIView.as_view(), name="send-message"),
    path("conversation/<str:conversation_id>/status/", ConversationStatusAPIView.as_view(), name="conversation-status"),
    
    # Webhook URLs
    path("webhook/<str:bot_name>/", TelegramWebhook.as_view(), name="webhook"),
    path("insta-webhook/", InstaWebhook.as_view(), name="insta-webhook"),
    path("intercom-webhook/", IntercomWebhookView.as_view(), name="intercom-webhook"),
    
    # Instagram Connection APIs
    path("instagram-auth-url/", InstagramAuthURLAPIView.as_view(), name="instagram-auth-url"),
    path("instagram-auth-url-wizard/", InstagramAuthURLWizardAPIView.as_view(), name="instagram-auth-url-wizard"),
    path("instagram-callback/", InstagramCallbackAPIView.as_view(), name="instagram-callback"),
    
    # Instagram Data Management (required by Instagram)
    path("instagram/deauthorize/", InstagramDeauthorizeAPIView.as_view(), name="instagram-deauthorize"),
    path("instagram/data-deletion/", InstagramDataDeletionAPIView.as_view(), name="instagram-data-deletion"),
    path("instagram/deletion-status/<str:confirmation_code>/", InstagramDeletionStatusAPIView.as_view(), name="instagram-deletion-status"),
    
    # Debug endpoints
    path("instagram-channels-debug/", InstaChannelDebugAPIView.as_view(), name="instagram-channels-debug"),
    path("instagram-update-page-id/", InstaChannelUpdatePageIdAPIView.as_view(), name="instagram-update-page-id"),
    path("instagram-auto-fix-ids/", InstaChannelAutoFixIDsAPIView.as_view(), name="instagram-auto-fix-ids"),
]
