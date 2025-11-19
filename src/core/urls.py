from django.contrib import admin
from django.urls import path,include
from core import views
from django.conf.urls.static import static
from core.settings import STATIC_ROOT, STATIC_URL, MEDIA_URL, MEDIA_ROOT
from billing.views import StripeWebhookView
from drf_yasg.views import get_schema_view
from drf_yasg.generators import OpenAPISchemaGenerator
from rest_framework.permissions import AllowAny
from drf_yasg import openapi
from core.swagger_inspectors import MultipleFileFieldInspector


class CustomOpenAPISchemaGenerator(OpenAPISchemaGenerator):
    """Custom schema generator that includes our custom field inspectors."""
    
    def get_field_inspectors(self):
        """Prepend our custom inspector to the list of field inspectors."""
        inspectors = super().get_field_inspectors()
        return [MultipleFileFieldInspector] + inspectors


schema_view = get_schema_view(
    openapi.Info(
        title="Pilito APIs",
        default_version='v1',
        description="Pilito API documentation",
        terms_of_service="https://www.google.com/policies/terms/",
        contact=openapi.Contact(email="contact@pilito.com"),
        license=openapi.License(name="Pilito License"),
    ),
    public=True,
    permission_classes=(AllowAny,),
    generator_class=CustomOpenAPISchemaGenerator,
)

urlpatterns = [
    path('docs/', schema_view.with_ui('swagger',cache_timeout=0),name='schema-swagger-ui'),
    path('admin/', admin.site.urls),
    path('', views.index, name='home'),
    path('health/', views.health_check, name='health-check'),
    path('api/v1/usr/', include(('accounts.urls', 'accounts'), namespace='accounts')),
    path('api/v1/settings/', include(('settings.urls', 'accounts'), namespace='settings')),
    path('api/v1/billing/', include(('billing.urls', 'accounts'), namespace='billing')),
    path('api/v1/message/', include(('message.urls', 'message'), namespace='message')),
    path('api/v1/academy/', include(('academy.urls', 'academy'), namespace='academy')),
    path('api/v1/ai/', include(('AI_model.urls', 'AI_model'), namespace='ai')),
    path('api/v1/workflow/', include(('workflow.urls', 'workflow'), namespace='workflow')),
    path('api/v1/web-knowledge/', include(('web_knowledge.urls', 'web_knowledge'), namespace='web_knowledge')),
    path('api/v1/workflow-templates/', include(('workflow_template.urls', 'workflow_template'), namespace='workflow_template')),
    # Integrations (WooCommerce, Shopify, etc.)
    path('api/integrations/', include(('integrations.urls', 'integrations'), namespace='integrations')),
    path('api/v1/integrations/', include(('integrations.urls', 'integrations'), namespace='integrations-v1')),
    # Monitoring and metrics
    path('api/v1/metrics', include(('monitoring.urls', 'monitoring'), namespace='monitoring')),
    # Root-level Stripe webhook for external integrations expecting /stripe/webhook
    path('stripe/webhook', StripeWebhookView.as_view(), name='root-stripe-webhook'),
]
urlpatterns += static(MEDIA_URL, document_root=MEDIA_ROOT)
urlpatterns += static(STATIC_URL, document_root=STATIC_ROOT)
