"""
URL Configuration for Workflow API
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from workflow.api.views import (
    EventTypeViewSet,
    TriggerViewSet,
    ConditionViewSet,
    ActionViewSet,
    ActionTemplateViewSet,
    WorkflowViewSet,
    WorkflowExecutionViewSet,
    WorkflowActionExecutionViewSet,
    TriggerEventLogViewSet,
    ActionLogViewSet,
    # New node-based views
    WorkflowNodeViewSet,
    WhenNodeViewSet,
    ConditionNodeViewSet,
    ActionNodeViewSet,
    WaitingNodeViewSet,
    NodeConnectionViewSet,
    UserResponseViewSet,
    NodeBasedWorkflowViewSet,
    # Business Types API
    BusinessTypesAPIView
)
from workflow.api.unified_views import UnifiedNodeViewSet

# Create router and register viewsets
router = DefaultRouter()
router.register(r'event-types', EventTypeViewSet, basename='eventtype')
router.register(r'triggers', TriggerViewSet, basename='trigger')
router.register(r'conditions', ConditionViewSet, basename='condition')
router.register(r'actions', ActionViewSet, basename='action')
router.register(r'action-templates', ActionTemplateViewSet, basename='actiontemplate')
router.register(r'workflows', WorkflowViewSet, basename='workflow')
router.register(r'workflow-executions', WorkflowExecutionViewSet, basename='workflowexecution')
router.register(r'workflow-action-executions', WorkflowActionExecutionViewSet, basename='workflowactionexecution')
router.register(r'trigger-event-logs', TriggerEventLogViewSet, basename='triggereventlog')
router.register(r'action-logs', ActionLogViewSet, basename='actionlog')

# New node-based workflow endpoints
router.register(r'workflow-nodes', WorkflowNodeViewSet, basename='workflownode')
router.register(r'when-nodes', WhenNodeViewSet, basename='whennode')
router.register(r'condition-nodes', ConditionNodeViewSet, basename='conditionnode')
router.register(r'action-nodes', ActionNodeViewSet, basename='actionnode')
router.register(r'waiting-nodes', WaitingNodeViewSet, basename='waitingnode')
router.register(r'node-connections', NodeConnectionViewSet, basename='nodeconnection')
router.register(r'user-responses', UserResponseViewSet, basename='userresponse')
router.register(r'node-workflows', NodeBasedWorkflowViewSet, basename='nodeworkflow')

# Unified node management endpoint
router.register(r'nodes', UnifiedNodeViewSet, basename='unifiednode')

# URL patterns
urlpatterns = [
    path('', include(router.urls)),
    # Business Types API - specific URL pattern as requested
    path('business_types/', BusinessTypesAPIView.as_view(), name='business_types'),
]
