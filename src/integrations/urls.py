from django.urls import path, include
from rest_framework.routers import DefaultRouter
from integrations import views

# Router for viewsets
router = DefaultRouter()
router.register(r'tokens', views.IntegrationTokenViewSet, basename='integration-token')
router.register(r'woocommerce/events', views.WooCommerceEventLogViewSet, basename='woocommerce-event')

urlpatterns = [
    # Webhook endpoints (public - authenticated via IntegrationToken)
    path('woocommerce/webhook/', views.WooCommerceWebhookView.as_view(), name='woocommerce-webhook'),
    path('woocommerce/health/', views.WooCommerceHealthCheckView.as_view(), name='woocommerce-health'),
    
    # Admin endpoints (via router)
    path('', include(router.urls)),
]

