from django.urls import path, include
from rest_framework.routers import DefaultRouter
from integrations import views

# Router for viewsets
router = DefaultRouter()
router.register(r'tokens', views.IntegrationTokenViewSet, basename='integration-token')
router.register(r'woocommerce/events', views.WooCommerceEventLogViewSet, basename='woocommerce-event')
router.register(r'wordpress-content', views.WordPressContentViewSet, basename='wordpress-content')

urlpatterns = [
    # WooCommerce webhook endpoints
    path('woocommerce/webhook/', views.WooCommerceWebhookView.as_view(), name='woocommerce-webhook'),
    path('woocommerce/health/', views.WooCommerceHealthCheckView.as_view(), name='woocommerce-health'),
    
    # WordPress content webhook endpoints (استاندارد با Plugin)
    path('wordpress-content/webhook/', views.WordPressContentWebhookView.as_view(), name='wordpress-content-webhook'),
    path('wordpress-content/health/', views.WordPressContentHealthCheckView.as_view(), name='wordpress-content-health'),
    
    # Admin endpoints (via router)
    path('', include(router.urls)),
]

