from django.urls import path, include

app_name = 'workflow'

urlpatterns = [
    path('api/', include('workflow.api.urls')),
]
