"""
API Views for Workflow Management
"""

import logging
from typing import Dict, Any

from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from rest_framework.pagination import PageNumberPagination
from django_filters.rest_framework import DjangoFilterBackend
from django.db import models
from django.db.models import Count, Q, Avg
from django.utils import timezone

from workflow.models import (
    EventType,
    Trigger,
    Condition,
    Action,
    ActionTemplate,
    Workflow,
    TriggerWorkflowAssociation,
    WorkflowAction,
    WorkflowExecution,
    WorkflowActionExecution,
    TriggerEventLog,
    ActionLog,
    # New node-based models
    WorkflowNode,
    WhenNode,
    ConditionNode,
    ActionNode,
    WaitingNode,
    NodeConnection,
    UserResponse
)
from workflow.serializers import (
    EventTypeSerializer,
    TriggerSerializer,
    ConditionSerializer,
    ActionSerializer,
    ActionTemplateSerializer,
    WorkflowListSerializer,
    WorkflowDetailSerializer,
    TriggerWorkflowAssociationSerializer,
    WorkflowActionSerializer,
    WorkflowExecutionSerializer,
    WorkflowActionExecutionSerializer,
    TriggerEventLogSerializer,
    ActionLogSerializer,
    TriggerTestSerializer,
    WorkflowExecuteSerializer,
    ProcessEventSerializer,
    # New node-based serializers
    WorkflowNodeSerializer,
    WhenNodeSerializer,
    ConditionNodeSerializer,
    ActionNodeSerializer,
    WaitingNodeSerializer,
    NodeConnectionSerializer,
    UserResponseSerializer,
    NodeBasedWorkflowSerializer,
    WorkflowDetailWithNodesSerializer,
    CreateNodeSerializer,
    CreateConnectionSerializer,
    WorkflowExecuteWithNodesSerializer,
    UnifiedNodeSerializer,
    WorkflowExportSerializer,
    WorkflowImportSerializer
)
from workflow.services.trigger_service import TriggerService
from workflow.services.workflow_execution_service import WorkflowExecutionService
from workflow.tasks import process_event

# Import BusinessPrompt from settings app
from settings.models import BusinessPrompt

logger = logging.getLogger(__name__)


class StandardResultPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


class EventTypeViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for EventType management (read-only)
    """
    queryset = EventType.objects.all()
    serializer_class = EventTypeSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultPagination
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['category', 'is_active']
    search_fields = ['name', 'code', 'description']
    ordering = ['category', 'name']


class TriggerViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Trigger management
    """
    queryset = Trigger.objects.all()
    serializer_class = TriggerSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultPagination
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['trigger_type', 'is_active']
    search_fields = ['name', 'description']
    ordering = ['-created_at']
    
    @action(detail=False, methods=['post'])
    def process_event(self, request):
        """
        Process an event and trigger workflows
        
        POST /api/workflow/triggers/process_event/
        {
            "event_type": "MESSAGE_RECEIVED",
            "data": {"message_id": "123", "content": "Hello"},
            "user_id": "user123",
            "conversation_id": "conv123"
        }
        """
        serializer = ProcessEventSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            # Create event log
            event_log = TriggerService.create_event_log(
                event_type=serializer.validated_data['event_type'],
                event_data=serializer.validated_data['data'],
                user_id=serializer.validated_data.get('user_id'),
                conversation_id=serializer.validated_data.get('conversation_id')
            )
            
            # Queue event processing
            process_event.delay(str(event_log.id))
            
            return Response({
                'success': True,
                'event_log_id': str(event_log.id),
                'message': 'Event queued for processing'
            }, status=status.HTTP_201_CREATED)
        
        except Exception as e:
            logger.error(f"Error processing event: {e}")
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['get'])
    def workflows(self, request, pk=None):
        """Get workflows associated with this trigger"""
        trigger = self.get_object()
        associations = trigger.workflow_associations.filter(is_active=True)
        serializer = TriggerWorkflowAssociationSerializer(associations, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def test(self, request, pk=None):
        """Test trigger with provided context"""
        trigger = self.get_object()
        serializer = TriggerTestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            from workflow.utils.condition_evaluator import evaluate_conditions
            
            context = serializer.validated_data['context']
            filters_match = True
            
            if trigger.filters:
                filters_match = evaluate_conditions(trigger.filters, context)
            
            return Response({
                'trigger_id': str(trigger.id),
                'trigger_name': trigger.name,
                'filters_match': filters_match,
                'test_context': context
            })
        
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        """Activate trigger"""
        trigger = self.get_object()
        trigger.is_active = True
        trigger.save()
        return Response({'message': 'Trigger activated'})
    
    @action(detail=True, methods=['post'])
    def deactivate(self, request, pk=None):
        """Deactivate trigger"""
        trigger = self.get_object()
        trigger.is_active = False
        trigger.save()
        return Response({'message': 'Trigger deactivated'})


class ConditionViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Condition management
    """
    queryset = Condition.objects.all()
    serializer_class = ConditionSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultPagination
    search_fields = ['name', 'description']
    ordering = ['name']


class ActionViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Action management
    """
    queryset = Action.objects.all()
    serializer_class = ActionSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultPagination
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['action_type', 'is_active']
    search_fields = ['name', 'description']
    ordering = ['order', 'name']
    
    @action(detail=False, methods=['get'])
    def action_types(self, request):
        """Get available action types"""
        return Response([
            {'value': choice[0], 'label': choice[1]}
            for choice in Action.ACTION_TYPE_CHOICES
        ])
    
    @action(detail=True, methods=['post'])
    def test(self, request, pk=None):
        """Test action with provided context"""
        action = self.get_object()
        serializer = TriggerTestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            execution_service = WorkflowExecutionService()
            result = execution_service._execute_action(action, serializer.validated_data['context'])
            
            return Response({
                'action_id': str(action.id),
                'action_name': action.name,
                'action_type': action.action_type,
                'test_result': result
            })
        
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def parameter_templates(self, request):
        """Get parameter templates for action types"""
        action_type = request.query_params.get('action_type')
        
        templates = {
            'send_message': {
                'message': 'Hello {{user.first_name}}!',
                'channel': 'auto'
            },
            'send_email': {
                'subject': 'Welcome {{user.first_name}}!',
                'body': 'Thank you for joining us.',
                'recipient': '{{user.email}}',
                'is_html': False
            },
            'add_tag': {
                'tag_name': 'interested'
            },
            'remove_tag': {
                'tag_name': 'unsubscribed'
            },
            'webhook': {
                'url': 'https://api.example.com/webhook',
                'method': 'POST',
                'headers': {'Content-Type': 'application/json'},
                'payload': {'user_id': '{{user.id}}', 'event': '{{event.type}}'}
            },
            'wait': {
                'duration': 5,
                'unit': 'minutes'
            },
            'set_conversation_status': {
                'status': 'closed'
            },
            'update_user': {
                'updates': {
                    'description': 'Updated by workflow'
                }
            },
            'add_note': {
                'note': 'User completed workflow action'
            },
            'custom_code': {
                'code': '# Set result dict with your logic\nresult["custom_field"] = "value"'
            },
            'control_ai_response': {
                'action': 'disable',  # disable, enable, custom_prompt, reset_context
                'custom_prompt': 'You are a specialized assistant for {{user.first_name}}. Be extra helpful and professional.'
            },
            'update_ai_context': {
                'context_data': {
                    'customer_tier': 'premium',
                    'last_purchase': '{{user.last_purchase}}',
                    'preferred_language': 'English'
                }
            }
        }
        
        if action_type and action_type in templates:
            return Response(templates[action_type])
        
        return Response(templates)


class ActionTemplateViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for ActionTemplate management (read-only)
    """
    queryset = ActionTemplate.objects.all()
    serializer_class = ActionTemplateSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultPagination
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['action_type', 'category', 'is_featured']
    search_fields = ['name', 'description']
    ordering = ['-is_featured', 'category', 'name']


class WorkflowViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Workflow management
    """
    queryset = Workflow.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultPagination
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['status', 'created_by']
    search_fields = ['name', 'description']
    ordering = ['-updated_at']
    
    def get_queryset(self):
        """Limit workflows to those created by the current user (admins see all)."""
        queryset = super().get_queryset()
        user = getattr(self.request, 'user', None)
        if not user:
            return queryset.none()
        if getattr(user, 'is_superuser', False) or getattr(user, 'is_staff', False):
            return queryset
        return queryset.filter(created_by=user)
    
    def get_serializer_class(self):
        if self.action == 'list':
            return WorkflowListSerializer
        return WorkflowDetailSerializer
    
    def update(self, request, *args, **kwargs):
        """
        Override update to implement partial updates - only modify fields that are sent in the request
        Ignores fields like key_word, key_value, and tags unless explicitly provided
        """
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        
        # For PATCH requests, always use partial=True to only update provided fields
        if request.method == 'PATCH':
            partial = True
        
        # Store the original request data to know which fields were sent
        request_fields = set(request.data.keys())
        
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        
        # Only update the fields that were actually provided in the request
        validated_data = serializer.validated_data
        
        # Update only the provided fields
        for field_name, field_value in validated_data.items():
            if hasattr(instance, field_name):
                setattr(instance, field_name, field_value)
        
        instance.save()
        
        if getattr(instance, '_prefetched_objects_cache', None):
            # If 'prefetch_related' has been applied to a queryset, we need to
            # forcibly invalidate the prefetch cache on the instance.
            instance._prefetched_objects_cache = {}

        # Return complete serializer data for both PATCH and PUT requests
        return Response(serializer.data)
    
    def partial_update(self, request, *args, **kwargs):
        """Handle PATCH requests with partial updates"""
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)
    
    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        """Activate workflow"""
        workflow = self.get_object()
        workflow.status = 'ACTIVE'
        workflow.save()
        return Response({'message': 'Workflow activated'})
    
    @action(detail=True, methods=['post'])
    def pause(self, request, pk=None):
        """Pause workflow"""
        workflow = self.get_object()
        workflow.status = 'PAUSED'
        workflow.save()
        return Response({'message': 'Workflow paused'})
    
    @action(detail=True, methods=['post'])
    def archive(self, request, pk=None):
        """Archive workflow"""
        workflow = self.get_object()
        workflow.status = 'ARCHIVED'
        workflow.save()
        return Response({'message': 'Workflow archived'})
    
    @action(detail=True, methods=['post'])
    def reset(self, request, pk=None):
        """Reset workflow to draft"""
        workflow = self.get_object()
        workflow.status = 'DRAFT'
        workflow.save()
        return Response({'message': 'Workflow reset to draft'})
    
    @action(detail=True, methods=['get'])
    def export(self, request, pk=None):
        """Export workflow as JSON including all related objects"""
        workflow = self.get_object()
        serializer = WorkflowExportSerializer(workflow)
        
        # Create filename with workflow name and timestamp
        from django.utils import timezone
        timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{workflow.name.replace(' ', '_')}_{timestamp}.json"
        
        # Return JSON response with appropriate headers for download
        response = Response(serializer.data)
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        response['Content-Type'] = 'application/json'
        return response
    
    @action(detail=False, methods=['post'])
    def import_workflow(self, request):
        """Import workflow from JSON data"""
        serializer = WorkflowImportSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        
        try:
            workflow = serializer.save()
            response_serializer = WorkflowDetailSerializer(workflow)
            return Response({
                'message': 'Workflow imported successfully',
                'workflow': response_serializer.data
            }, status=status.HTTP_201_CREATED)
        except Exception as e:
            logger.error(f"Error importing workflow: {str(e)}")
            return Response({
                'error': 'Failed to import workflow',
                'details': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def add_trigger(self, request, pk=None):
        """Add trigger to workflow"""
        workflow = self.get_object()
        trigger_id = request.data.get('trigger_id')
        priority = request.data.get('priority', 100)
        specific_conditions = request.data.get('specific_conditions', {})
        
        if not trigger_id:
            return Response({'error': 'trigger_id is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            trigger = Trigger.objects.get(id=trigger_id)
            association, created = TriggerWorkflowAssociation.objects.get_or_create(
                trigger=trigger,
                workflow=workflow,
                defaults={
                    'priority': priority,
                    'specific_conditions': specific_conditions
                }
            )
            
            if not created:
                association.priority = priority
                association.specific_conditions = specific_conditions
                association.save()
            
            serializer = TriggerWorkflowAssociationSerializer(association)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        except Trigger.DoesNotExist:
            return Response({'error': 'Trigger not found'}, status=status.HTTP_404_NOT_FOUND)
    
    @action(detail=True, methods=['post'])
    def remove_trigger(self, request, pk=None):
        """Remove trigger from workflow"""
        workflow = self.get_object()
        trigger_id = request.data.get('trigger_id')
        
        if not trigger_id:
            return Response({'error': 'trigger_id is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            association = TriggerWorkflowAssociation.objects.get(
                trigger_id=trigger_id,
                workflow=workflow
            )
            association.delete()
            return Response({'message': 'Trigger removed from workflow'})
        
        except TriggerWorkflowAssociation.DoesNotExist:
            return Response({'error': 'Association not found'}, status=status.HTTP_404_NOT_FOUND)
    
    @action(detail=True, methods=['get'])
    def triggers(self, request, pk=None):
        """Get triggers for workflow"""
        workflow = self.get_object()
        associations = workflow.trigger_associations.filter(is_active=True)
        serializer = TriggerWorkflowAssociationSerializer(associations, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def actions(self, request, pk=None):
        """Get actions for workflow"""
        workflow = self.get_object()
        actions = workflow.workflow_actions.all().order_by('order')
        serializer = WorkflowActionSerializer(actions, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def executions(self, request, pk=None):
        """Get executions for workflow"""
        workflow = self.get_object()
        executions = workflow.executions.all().order_by('-created_at')
        
        # Apply pagination
        page = self.paginate_queryset(executions)
        if page is not None:
            serializer = WorkflowExecutionSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = WorkflowExecutionSerializer(executions, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def events(self, request, pk=None):
        """Get trigger events for workflow"""
        workflow = self.get_object()
        
        # Get events that could trigger this workflow
        trigger_types = workflow.trigger_associations.values_list('trigger__trigger_type', flat=True)
        events = TriggerEventLog.objects.filter(event_type__in=trigger_types).order_by('-created_at')
        
        # Apply pagination
        page = self.paginate_queryset(events)
        if page is not None:
            serializer = TriggerEventLogSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = TriggerEventLogSerializer(events, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def execute(self, request, pk=None):
        """Manually execute workflow"""
        workflow = self.get_object()
        serializer = WorkflowExecuteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            execution_service = WorkflowExecutionService()
            execution = execution_service.execute_workflow(workflow, serializer.validated_data['context'])
            
            return Response({
                'execution_id': execution.id,
                'status': execution.status,
                'message': 'Workflow execution started'
            }, status=status.HTTP_201_CREATED)
        
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Get workflow statistics"""
        try:
            stats = {
                'total_workflows': Workflow.objects.count(),
                'active_workflows': Workflow.objects.filter(status='ACTIVE').count(),
                'draft_workflows': Workflow.objects.filter(status='DRAFT').count(),
                'paused_workflows': Workflow.objects.filter(status='PAUSED').count(),
                'total_executions': WorkflowExecution.objects.count(),
                'recent_executions': WorkflowExecution.objects.filter(
                    created_at__gte=timezone.now().date()
                ).count(),
                'successful_executions': WorkflowExecution.objects.filter(status='COMPLETED').count(),
                'failed_executions': WorkflowExecution.objects.filter(status='FAILED').count(),
            }
            
            return Response(stats)
        
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


class WorkflowExecutionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for WorkflowExecution management (read-only)
    """
    queryset = WorkflowExecution.objects.all()
    serializer_class = WorkflowExecutionSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultPagination
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['status', 'workflow']
    ordering = ['-created_at']
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Cancel a running execution"""
        execution = self.get_object()
        
        if execution.status not in ['PENDING', 'RUNNING', 'WAITING']:
            return Response({
                'error': 'Can only cancel pending, running, or waiting executions'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        execution.status = 'FAILED'
        execution.error_message = 'Cancelled by user'
        execution.completed_at = timezone.now()
        execution.save()
        
        # Cancel pending action executions
        execution.action_executions.filter(status__in=['PENDING', 'WAITING']).update(
            status='FAILED',
            error_message='Cancelled by user',
            completed_at=timezone.now()
        )
        
        return Response({'message': 'Execution cancelled'})


class WorkflowActionExecutionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for WorkflowActionExecution management (read-only)
    """
    queryset = WorkflowActionExecution.objects.all()
    serializer_class = WorkflowActionExecutionSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultPagination
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['status', 'workflow_execution']
    ordering = ['workflow_execution', 'workflow_action__order']


class TriggerEventLogViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for TriggerEventLog management (read-only)
    """
    queryset = TriggerEventLog.objects.all()
    serializer_class = TriggerEventLogSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultPagination
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['event_type', 'user_id', 'conversation_id']
    ordering = ['-created_at']


class ActionLogViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for ActionLog management (read-only)
    """
    queryset = ActionLog.objects.all()
    serializer_class = ActionLogSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultPagination
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['action', 'success']
    ordering = ['-executed_at']


# Business Types API

class BusinessTypesAPIView(APIView):
    """
    API to return list of BusinessPrompt names
    """
    permission_classes = [permissions.IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Get list of business prompt names",
        responses={
            200: openapi.Response(
                description="List of business prompt names",
                examples={
                    "application/json": [
                        {"name": "Restaurant"},
                        {"name": "E-commerce"},
                        {"name": "Healthcare"},
                        {"name": "Education"}
                    ]
                }
            )
        }
    )
    def get(self, request):
        """Get list of all BusinessPrompt names"""
        try:
            business_prompts = BusinessPrompt.objects.all().values_list('name', flat=True)
            # Convert to list of dictionaries with 'name' field
            result = [{'name': name} for name in business_prompts]
            return Response(result, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Error getting business types: {str(e)}")
            return Response(
                {'error': 'Failed to get business types'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# New Node-Based Workflow ViewSets

class WorkflowNodeViewSet(viewsets.ModelViewSet):
    """
    ViewSet for WorkflowNode management
    """
    queryset = WorkflowNode.objects.all()
    serializer_class = WorkflowNodeSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultPagination
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['workflow', 'node_type', 'is_active']
    search_fields = ['title']
    ordering = ['workflow', 'node_type', 'created_at']


class WhenNodeViewSet(viewsets.ModelViewSet):
    """
    ViewSet for WhenNode management
    """
    queryset = WhenNode.objects.all()
    serializer_class = WhenNodeSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultPagination
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['workflow', 'when_type', 'is_active']
    search_fields = ['title']
    ordering = ['workflow', 'created_at']
    
    @action(detail=False, methods=['get'])
    def when_types(self, request):
        """Get available when types"""
        return Response([
            {'value': choice[0], 'label': choice[1]}
            for choice in WhenNode.WHEN_TYPE_CHOICES
        ])


class ConditionNodeViewSet(viewsets.ModelViewSet):
    """
    ViewSet for ConditionNode management
    """
    queryset = ConditionNode.objects.all()
    serializer_class = ConditionNodeSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultPagination
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['workflow', 'combination_operator', 'is_active']
    search_fields = ['title']
    ordering = ['workflow', 'created_at']
    
    @action(detail=True, methods=['post'])
    def test(self, request, pk=None):
        """Test condition node with provided context"""
        condition_node = self.get_object()
        serializer = TriggerTestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            from workflow.utils.condition_evaluator import evaluate_condition_group
            
            context = serializer.validated_data['context']
            result = evaluate_condition_group(
                condition_node.conditions, 
                condition_node.combination_operator, 
                context
            )
            
            return Response({
                'condition_node_id': str(condition_node.id),
                'condition_node_title': condition_node.title,
                'conditions_match': result,
                'test_context': context
            })
        
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def condition_types(self, request):
        """Get available condition types"""
        return Response([
            {'value': choice[0], 'label': choice[1]}
            for choice in ConditionNode.CONDITION_TYPE_CHOICES
        ])
    
    @action(detail=False, methods=['get'])
    def message_operators(self, request):
        """Get available message operators"""
        return Response([
            {'value': choice[0], 'label': choice[1]}
            for choice in ConditionNode.MESSAGE_OPERATOR_CHOICES
        ])
    
    @action(detail=False, methods=['get'])
    def combination_operators(self, request):
        """Get available combination operators"""
        return Response([
            {'value': choice[0], 'label': choice[1]}
            for choice in ConditionNode.OPERATOR_CHOICES
        ])


class ActionNodeViewSet(viewsets.ModelViewSet):
    """
    ViewSet for ActionNode management
    """
    queryset = ActionNode.objects.all()
    serializer_class = ActionNodeSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultPagination
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['workflow', 'action_type', 'is_active']
    search_fields = ['title', 'message_content']
    ordering = ['workflow', 'created_at']
    
    @action(detail=False, methods=['get'])
    def action_types(self, request):
        """Get available action types"""
        return Response([
            {'value': choice[0], 'label': choice[1]}
            for choice in ActionNode.ACTION_TYPE_CHOICES
        ])
    
    @action(detail=False, methods=['get'])
    def redirect_destinations(self, request):
        """Get available redirect destinations"""
        return Response([
            {'value': choice[0], 'label': choice[1]}
            for choice in ActionNode.REDIRECT_DESTINATIONS
        ])
    
    @action(detail=False, methods=['get'])
    def delay_units(self, request):
        """Get available delay units"""
        delay_units = [
            ('seconds', 'Seconds'),
            ('minutes', 'Minutes'),
            ('hours', 'Hours'),
            ('days', 'Days')
        ]
        return Response([
            {'value': choice[0], 'label': choice[1]}
            for choice in delay_units
        ])
    
    @action(detail=False, methods=['get'])
    def webhook_methods(self, request):
        """Get available webhook methods"""
        webhook_methods = [
            ('GET', 'GET'),
            ('POST', 'POST'),
            ('PUT', 'PUT'),
            ('DELETE', 'DELETE')
        ]
        return Response([
            {'value': choice[0], 'label': choice[1]}
            for choice in webhook_methods
        ])


class WaitingNodeViewSet(viewsets.ModelViewSet):
    """
    ViewSet for WaitingNode management with complete CRUD operations
    """
    serializer_class = WaitingNodeSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultPagination
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['workflow', 'storage_type', 'is_active']
    ordering = ['workflow', 'position', 'created_at']
    
    def get_queryset(self):
        """Filter waiting nodes by user's workflows"""
        queryset = WaitingNode.objects.all()
        if hasattr(self.request.user, 'created_workflows'):
            user_workflows = self.request.user.created_workflows.all()
            queryset = queryset.filter(workflow__in=user_workflows)
        return queryset.select_related('workflow').prefetch_related('responses')
    
    @swagger_auto_schema(
        operation_description="List all waiting nodes for user's workflows",
        responses={200: WaitingNodeSerializer(many=True)}
    )
    def list(self, request, *args, **kwargs):
        """List waiting nodes with filtering"""
        logger.info(f"🕐 [WaitingNodeAPI] Listing WaitingNodes for user {request.user.username}")
        response = super().list(request, *args, **kwargs)
        if response.status_code == status.HTTP_200_OK:
            count = len(response.data.get('results', response.data) if isinstance(response.data, dict) else response.data)
            logger.info(f"🕐 [WaitingNodeAPI] ✅ Listed {count} waiting nodes")
        return response
    
    @swagger_auto_schema(
        operation_description="Get waiting node details",
        responses={
            200: WaitingNodeSerializer,
            404: 'Not found'
        }
    )
    def retrieve(self, request, *args, **kwargs):
        """Get specific waiting node"""
        instance = self.get_object()
        logger.info(f"🕐 [WaitingNodeAPI] Retrieving WaitingNode {instance.id} ('{instance.title}') for user {request.user.username}")
        response = super().retrieve(request, *args, **kwargs)
        if response.status_code == status.HTTP_200_OK:
            logger.info(f"🕐 [WaitingNodeAPI] ✅ Retrieved waiting node {instance.id}")
        return response
    
    @swagger_auto_schema(
        operation_description="Create a new waiting node",
        request_body=WaitingNodeSerializer,
        responses={
            201: WaitingNodeSerializer,
            400: 'Bad request'
        }
    )
    def create(self, request, *args, **kwargs):
        """Create new waiting node"""
        try:
            logger.info(f"🕐 [WaitingNodeAPI] Creating new WaitingNode by user {request.user.username}")
            logger.info(f"🕐 [WaitingNodeAPI] Request data: {request.data}")
            
            # Validate that workflow belongs to user
            workflow_id = request.data.get('workflow')
            if workflow_id:
                logger.info(f"🕐 [WaitingNodeAPI] Validating workflow ownership: {workflow_id}")
                try:
                    workflow = Workflow.objects.get(id=workflow_id, created_by=request.user)
                    logger.info(f"🕐 [WaitingNodeAPI] ✅ Workflow validation passed: {workflow.title}")
                except Workflow.DoesNotExist:
                    logger.warning(f"🕐 [WaitingNodeAPI] ❌ Workflow not found or access denied: {workflow_id}")
                    return Response(
                        {'workflow': ['Workflow not found or access denied']},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            else:
                logger.warning(f"🕐 [WaitingNodeAPI] ❌ No workflow_id provided in request")
            
            response = super().create(request, *args, **kwargs)
            
            # Log creation
            if response.status_code == status.HTTP_201_CREATED:
                created_node_id = response.data.get('id', 'unknown')
                logger.info(f"🕐 [WaitingNodeAPI] ✅ Created waiting node {created_node_id} by user {request.user.username}")
            else:
                logger.warning(f"🕐 [WaitingNodeAPI] ❌ Create failed with status {response.status_code}")
            
            return response
            
        except Exception as e:
            logger.error(f"Error creating waiting node: {e}")
            return Response(
                {'error': 'Failed to create waiting node'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @swagger_auto_schema(
        operation_description="Update waiting node",
        request_body=WaitingNodeSerializer,
        responses={
            200: WaitingNodeSerializer,
            400: 'Bad request',
            404: 'Not found'
        }
    )
    def update(self, request, *args, **kwargs):
        """Update waiting node"""
        try:
            instance = self.get_object()
            logger.info(f"🕐 [WaitingNodeAPI] Updating WaitingNode {instance.id} by user {request.user.username}")
            logger.info(f"🕐 [WaitingNodeAPI] Current node: '{instance.title}' (storage_type: {instance.storage_type})")
            logger.info(f"🕐 [WaitingNodeAPI] Update data: {request.data}")
            
            # Handle skip_keywords to exit_keywords mapping for frontend compatibility
            if 'skip_keywords' in request.data:
                skip_keywords = request.data.get('skip_keywords', [])
                exit_keywords = request.data.get('exit_keywords', [])
                
                if skip_keywords:
                    # Create a mutable copy of request.data
                    updated_data = request.data.copy()
                    
                    if not exit_keywords:
                        # Only skip_keywords provided, use them as exit_keywords
                        updated_data['exit_keywords'] = skip_keywords
                        logger.info(f"🕐 [WaitingNodeAPI] Mapped skip_keywords to exit_keywords: {skip_keywords}")
                    else:
                        # Both provided, merge them
                        combined_keywords = list(set(skip_keywords + exit_keywords))
                        updated_data['exit_keywords'] = combined_keywords
                        logger.info(f"🕐 [WaitingNodeAPI] Merged skip_keywords + exit_keywords: {combined_keywords}")
                    
                    # Update request.data with the modified data
                    request._full_data = updated_data
            
            # Validate workflow ownership if changing workflow
            workflow_id = request.data.get('workflow')
            if workflow_id and str(workflow_id) != str(instance.workflow.id):
                logger.info(f"🕐 [WaitingNodeAPI] Validating new workflow ownership: {workflow_id}")
                try:
                    new_workflow = Workflow.objects.get(id=workflow_id, created_by=request.user)
                    logger.info(f"🕐 [WaitingNodeAPI] ✅ New workflow validation passed: {new_workflow.title}")
                except Workflow.DoesNotExist:
                    logger.warning(f"🕐 [WaitingNodeAPI] ❌ New workflow not found or access denied: {workflow_id}")
                    return Response(
                        {'workflow': ['Workflow not found or access denied']},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            
            response = super().update(request, *args, **kwargs)
            
            if response.status_code == status.HTTP_200_OK:
                logger.info(f"🕐 [WaitingNodeAPI] ✅ Updated waiting node {instance.id} by user {request.user.username}")
            else:
                logger.warning(f"🕐 [WaitingNodeAPI] ❌ Update failed with status {response.status_code}")
            
            return response
            
        except Exception as e:
            logger.error(f"Error updating waiting node: {e}")
            return Response(
                {'error': 'Failed to update waiting node'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @swagger_auto_schema(
        operation_description="Partially update waiting node",
        request_body=WaitingNodeSerializer,
        responses={
            200: WaitingNodeSerializer,
            400: 'Bad request',
            404: 'Not found'
        }
    )
    def partial_update(self, request, *args, **kwargs):
        """Partially update waiting node (PATCH)"""
        logger.info(f"🕐 [WaitingNodeAPI] Partial update (PATCH) for WaitingNode by user {request.user.username}")
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_description="Delete waiting node",
        responses={
            204: 'Deleted successfully',
            404: 'Not found',
            400: 'Cannot delete - has dependencies'
        }
    )
    def destroy(self, request, *args, **kwargs):
        """Delete waiting node with dependency checks"""
        try:
            instance = self.get_object()
            logger.info(f"🕐 [WaitingNodeAPI] Attempting to delete WaitingNode {instance.id} ('{instance.title}') by user {request.user.username}")
            
            # Check for active executions
            active_executions = WorkflowExecution.objects.filter(
                workflow=instance.workflow,
                status__in=['RUNNING', 'WAITING'],
                context_data__waiting_node_id=str(instance.id)
            ).exists()
            
            if active_executions:
                logger.warning(f"🕐 [WaitingNodeAPI] ❌ Cannot delete - has active executions: {instance.id}")
                return Response(
                    {'error': 'Cannot delete waiting node - it has active executions'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Check for user responses
            response_count = instance.responses.count()
            logger.info(f"🕐 [WaitingNodeAPI] Node has {response_count} user responses")
            
            node_title = instance.title
            workflow_name = instance.workflow.name
            
            response = super().destroy(request, *args, **kwargs)
            
            if response.status_code == status.HTTP_204_NO_CONTENT:
                logger.info(f"🕐 [WaitingNodeAPI] ✅ Deleted waiting node '{node_title}' from workflow '{workflow_name}' by user {request.user.username} (had {response_count} responses)")
            else:
                logger.warning(f"🕐 [WaitingNodeAPI] ❌ Delete failed with status {response.status_code}")
            
            return response
            
        except Exception as e:
            logger.error(f"Error deleting waiting node: {e}")
            return Response(
                {'error': 'Failed to delete waiting node'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['get'])
    @swagger_auto_schema(
        operation_description="Get user responses for this waiting node",
        responses={200: UserResponseSerializer(many=True)}
    )
    def responses(self, request, pk=None):
        """Get all user responses for this waiting node"""
        try:
            waiting_node = self.get_object()
            responses = waiting_node.responses.all().order_by('-created_at')
            
            # Apply pagination
            page = self.paginate_queryset(responses)
            if page is not None:
                serializer = UserResponseSerializer(page, many=True)
                return self.get_paginated_response(serializer.data)
            
            serializer = UserResponseSerializer(responses, many=True)
            return Response(serializer.data)
            
        except Exception as e:
            logger.error(f"Error getting waiting node responses: {e}")
            return Response(
                {'error': 'Failed to get responses'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['get'])
    @swagger_auto_schema(
        operation_description="Get statistics for this waiting node",
        responses={200: 'Statistics data'}
    )
    def statistics(self, request, pk=None):
        """Get statistics for waiting node responses"""
        try:
            waiting_node = self.get_object()
            responses = waiting_node.responses.all()
            
            stats = {
                'total_responses': responses.count(),
                'valid_responses': responses.filter(is_valid=True).count(),
                'invalid_responses': responses.filter(is_valid=False).count(),
                'processed_responses': responses.filter(processed_at__isnull=False).count(),
                'pending_responses': responses.filter(processed_at__isnull=True).count(),
                'average_error_count': responses.aggregate(
                    avg_errors=models.Avg('error_count')
                )['avg_errors'] or 0,
            }
            
            # Response time analysis (if processed_at exists)
            processed = responses.filter(processed_at__isnull=False)
            if processed.exists():
                response_times = []
                for resp in processed:
                    if resp.processed_at and resp.created_at:
                        delta = resp.processed_at - resp.created_at
                        response_times.append(delta.total_seconds())
                
                if response_times:
                    stats['average_response_time_seconds'] = sum(response_times) / len(response_times)
                    stats['min_response_time_seconds'] = min(response_times)
                    stats['max_response_time_seconds'] = max(response_times)
            
            return Response(stats)
            
        except Exception as e:
            logger.error(f"Error getting waiting node statistics: {e}")
            return Response(
                {'error': 'Failed to get statistics'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    @swagger_auto_schema(
        operation_description="Get storage type choices",
        responses={200: 'Storage type choices'}
    )
    def storage_types(self, request):
        """Get available storage type choices"""
        storage_types = [
            {'value': choice[0], 'label': choice[1]}
            for choice in WaitingNode.STORAGE_TYPE_CHOICES
        ]
        return Response(storage_types)
    
    @action(detail=False, methods=['get'])
    @swagger_auto_schema(
        operation_description="Get time unit choices",
        responses={200: 'Time unit choices'}
    )
    def time_units(self, request):
        """Get available time unit choices"""
        time_units = [
            {'value': choice[0], 'label': choice[1]}
            for choice in WaitingNode.TIME_UNIT_CHOICES
        ]
        return Response(time_units)


class NodeConnectionViewSet(viewsets.ModelViewSet):
    """
    ViewSet for NodeConnection management with enhanced delete operations
    """
    queryset = NodeConnection.objects.all()
    serializer_class = NodeConnectionSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultPagination
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['workflow', 'source_node', 'target_node', 'connection_type']
    ordering = ['workflow', 'created_at']
    
    def get_queryset(self):
        """Filter connections by user's workflows"""
        queryset = super().get_queryset()
        if hasattr(self.request.user, 'created_workflows'):
            user_workflows = self.request.user.created_workflows.all()
            queryset = queryset.filter(workflow__in=user_workflows)
        return queryset.select_related('source_node', 'target_node', 'workflow')
    
    def destroy(self, request, *args, **kwargs):
        """Enhanced delete with detailed response"""
        try:
            instance = self.get_object()
            
            # Store connection info for response
            connection_info = {
                'id': str(instance.id),
                'source_node': {
                    'id': str(instance.source_node.id),
                    'title': instance.source_node.title
                },
                'target_node': {
                    'id': str(instance.target_node.id),
                    'title': instance.target_node.title
                },
                'connection_type': instance.connection_type,
                'workflow': {
                    'id': str(instance.workflow.id),
                    'name': instance.workflow.name
                }
            }
            
            # Delete the connection
            self.perform_destroy(instance)
            
            return Response({
                'message': f'Connection deleted successfully',
                'deleted_connection': connection_info,
                'status': 'success'
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'error': f'Failed to delete connection: {str(e)}',
                'status': 'error'
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'])
    def bulk_delete(self, request):
        """Delete multiple connections at once"""
        try:
            connection_ids = request.data.get('connection_ids', [])
            
            if not connection_ids:
                return Response({
                    'error': 'No connection IDs provided',
                    'status': 'error'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Get connections that belong to user's workflows
            connections = self.get_queryset().filter(id__in=connection_ids)
            
            if not connections.exists():
                return Response({
                    'error': 'No valid connections found for deletion',
                    'status': 'error'
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Store connection info for response
            deleted_connections = []
            for connection in connections:
                deleted_connections.append({
                    'id': str(connection.id),
                    'source_node_title': connection.source_node.title,
                    'target_node_title': connection.target_node.title,
                    'connection_type': connection.connection_type
                })
            
            # Bulk delete
            deleted_count = connections.count()
            connections.delete()
            
            return Response({
                'message': f'Successfully deleted {deleted_count} connections',
                'deleted_count': deleted_count,
                'deleted_connections': deleted_connections,
                'status': 'success'
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'error': f'Bulk delete failed: {str(e)}',
                'status': 'error'
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['delete'])
    def delete_by_nodes(self, request):
        """Delete connections between specific nodes"""
        try:
            source_node_id = request.query_params.get('source_node')
            target_node_id = request.query_params.get('target_node')
            connection_type = request.query_params.get('connection_type')
            
            if not source_node_id or not target_node_id:
                return Response({
                    'error': 'Both source_node and target_node parameters are required',
                    'status': 'error'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Build filter conditions
            filters = {
                'source_node_id': source_node_id,
                'target_node_id': target_node_id
            }
            
            if connection_type:
                filters['connection_type'] = connection_type
            
            # Get connections to delete
            connections = self.get_queryset().filter(**filters)
            
            if not connections.exists():
                return Response({
                    'error': 'No connections found matching the criteria',
                    'status': 'error'
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Store connection info
            deleted_connections = []
            for connection in connections:
                deleted_connections.append({
                    'id': str(connection.id),
                    'connection_type': connection.connection_type,
                    'condition': connection.condition
                })
            
            # Delete connections
            deleted_count = connections.count()
            connections.delete()
            
            return Response({
                'message': f'Successfully deleted {deleted_count} connections between nodes',
                'deleted_count': deleted_count,
                'source_node_id': source_node_id,
                'target_node_id': target_node_id,
                'deleted_connections': deleted_connections,
                'status': 'success'
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'error': f'Delete by nodes failed: {str(e)}',
                'status': 'error'
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['delete'])
    def delete_by_workflow(self, request):
        """Delete all connections for a specific workflow"""
        try:
            workflow_id = request.query_params.get('workflow_id')
            
            if not workflow_id:
                return Response({
                    'error': 'workflow_id parameter is required',
                    'status': 'error'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Get connections for the workflow
            connections = self.get_queryset().filter(workflow_id=workflow_id)
            
            if not connections.exists():
                return Response({
                    'message': 'No connections found for this workflow',
                    'deleted_count': 0,
                    'status': 'success'
                }, status=status.HTTP_200_OK)
            
            # Count and delete
            deleted_count = connections.count()
            workflow_name = connections.first().workflow.name
            connections.delete()
            
            return Response({
                'message': f'Successfully deleted all {deleted_count} connections for workflow "{workflow_name}"',
                'deleted_count': deleted_count,
                'workflow_id': workflow_id,
                'workflow_name': workflow_name,
                'status': 'success'
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'error': f'Delete by workflow failed: {str(e)}',
                'status': 'error'
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['delete'])
    def delete_orphaned(self, request):
        """Delete connections that reference non-existent nodes"""
        try:
            # Find connections with missing source or target nodes
            from django.db.models import Q
            
            orphaned_connections = self.get_queryset().filter(
                Q(source_node__isnull=True) | 
                Q(target_node__isnull=True) |
                Q(source_node__is_active=False) |
                Q(target_node__is_active=False)
            )
            
            if not orphaned_connections.exists():
                return Response({
                    'message': 'No orphaned connections found',
                    'deleted_count': 0,
                    'status': 'success'
                }, status=status.HTTP_200_OK)
            
            deleted_count = orphaned_connections.count()
            orphaned_connections.delete()
            
            return Response({
                'message': f'Successfully deleted {deleted_count} orphaned connections',
                'deleted_count': deleted_count,
                'status': 'success'
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'error': f'Delete orphaned connections failed: {str(e)}',
                'status': 'error'
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def connection_types(self, request):
        """Get available connection types"""
        return Response([
            {'value': choice[0], 'label': choice[1]}
            for choice in NodeConnection.CONNECTION_TYPE_CHOICES
        ])
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Get connection statistics"""
        try:
            queryset = self.get_queryset()
            
            stats = {
                'total_connections': queryset.count(),
                'by_type': {},
                'by_workflow': {},
                'recent_connections': queryset.order_by('-created_at')[:5].values(
                    'id', 'source_node__title', 'target_node__title', 
                    'connection_type', 'created_at'
                )
            }
            
            # Count by connection type
            for choice in NodeConnection.CONNECTION_TYPE_CHOICES:
                conn_type = choice[0]
                count = queryset.filter(connection_type=conn_type).count()
                stats['by_type'][conn_type] = {
                    'count': count,
                    'label': choice[1]
                }
            
            # Count by workflow (top 10)
            workflow_counts = queryset.values('workflow__id', 'workflow__name').annotate(
                count=Count('id')
            ).order_by('-count')[:10]
            
            for wf in workflow_counts:
                stats['by_workflow'][wf['workflow__id']] = {
                    'name': wf['workflow__name'],
                    'count': wf['count']
                }
            
            return Response(stats)
            
        except Exception as e:
            return Response({
                'error': f'Failed to get statistics: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)


class UserResponseViewSet(viewsets.ReadOnlyModelViewSet):
    """UserResponse endpoints temporarily removed; URL kept for compatibility."""
    queryset = UserResponse.objects.none()
    serializer_class = UserResponseSerializer
    permission_classes = [permissions.IsAuthenticated]

    def list(self, request, *args, **kwargs):
        return Response({'detail': 'UserResponse endpoints are disabled'}, status=status.HTTP_501_NOT_IMPLEMENTED)

    def retrieve(self, request, *args, **kwargs):
        return Response({'detail': 'UserResponse endpoints are disabled'}, status=status.HTTP_501_NOT_IMPLEMENTED)


class NodeBasedWorkflowViewSet(viewsets.ModelViewSet):
    """
    Enhanced WorkflowViewSet with node-based structure support
    """
    queryset = Workflow.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultPagination
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['status', 'created_by']
    search_fields = ['name', 'description']
    ordering = ['-updated_at']
    
    def get_serializer_class(self):
        if self.action == 'list':
            return NodeBasedWorkflowSerializer
        return WorkflowDetailWithNodesSerializer
    
    def get_queryset(self):
        """Limit workflows to those created by the current user (admins see all)."""
        queryset = super().get_queryset()
        user = getattr(self.request, 'user', None)
        if not user:
            return queryset.none()
        if getattr(user, 'is_superuser', False) or getattr(user, 'is_staff', False):
            return queryset
        return queryset.filter(created_by=user)
    
    @action(detail=True, methods=['get'])
    def nodes(self, request, pk=None):
        """Get all nodes for workflow"""
        workflow = self.get_object()
        nodes = workflow.nodes.filter(is_active=True).order_by('node_type', 'created_at')
        serializer = WorkflowNodeSerializer(nodes, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def create_node(self, request, pk=None):
        """Create a new node for workflow"""
        workflow = self.get_object()
        
        # Log incoming data for debugging
        logger.info(f"Creating node for workflow {workflow.id} with data: {request.data}")
        
        serializer = CreateNodeSerializer(data=request.data)
        if not serializer.is_valid():
            logger.error(f"CreateNodeSerializer validation errors: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        serializer.is_valid(raise_exception=True)
        
        try:
            data = serializer.validated_data
            node_type = data['node_type']
            
            # Create the appropriate node type
            if node_type == 'when':
                node = WhenNode.objects.create(
                    workflow=workflow,
                    title=data['title'],
                    position_x=data['position_x'],
                    position_y=data['position_y'],
                    configuration=data['configuration'],
                    when_type=data.get('when_type', 'receive_message'),
                    keywords=data.get('keywords', []),
                    tags=data.get('tags', []),
                    channels=data.get('channels', []),
                    schedule_frequency=data.get('schedule_frequency'),
                    schedule_start_date=data.get('schedule_start_date'),
                    schedule_time=data.get('schedule_time'),
                )
                response_serializer = WhenNodeSerializer(node)
            
            elif node_type == 'condition':
                node = ConditionNode.objects.create(
                    workflow=workflow,
                    title=data['title'],
                    position_x=data['position_x'],
                    position_y=data['position_y'],
                    configuration=data['configuration'],
                    combination_operator=data.get('combination_operator', 'or'),
                    conditions=data.get('conditions', []),
                )
                response_serializer = ConditionNodeSerializer(node)
            
            elif node_type == 'action':
                node = ActionNode.objects.create(
                    workflow=workflow,
                    title=data['title'],
                    position_x=data['position_x'],
                    position_y=data['position_y'],
                    configuration=data['configuration'],
                    action_type=data.get('action_type', 'send_message'),
                    message_content=data.get('message_content', ''),
                    key_values=data.get('key_values', []),
                    delay_amount=data.get('delay_amount', 0),
                    delay_unit=data.get('delay_unit', 'minutes'),
                    redirect_destination=data.get('redirect_destination', ''),
                    tag_name=data.get('tag_name', ''),
                    webhook_url=data.get('webhook_url', ''),
                    webhook_method=data.get('webhook_method', 'POST'),
                    webhook_headers=data.get('webhook_headers', {}),
                    webhook_payload=data.get('webhook_payload', {}),
                    custom_code=data.get('custom_code', ''),
                )
                response_serializer = ActionNodeSerializer(node)
            
            elif node_type == 'waiting':
                # Handle skip_keywords to exit_keywords mapping for frontend compatibility
                exit_keywords = data.get('exit_keywords', [])
                skip_keywords = data.get('skip_keywords', [])
                if skip_keywords:
                    if not exit_keywords:
                        exit_keywords = skip_keywords
                    else:
                        # Merge both lists if both are provided
                        exit_keywords = list(set(exit_keywords + skip_keywords))
                
                node = WaitingNode.objects.create(
                    workflow=workflow,
                    title=data['title'],
                    position_x=data['position_x'],
                    position_y=data['position_y'],
                    configuration=data['configuration'],
                    storage_type=data.get('storage_type', 'text'),
                    customer_message=data.get('customer_message', ''),
                    key_values=data.get('key_values', []),
                    error_message=data.get('error_message', ''),
                    choice_options=data.get('choice_options', []),
                    allowed_errors=data.get('allowed_errors', 3),
                    exit_keywords=exit_keywords,
                    response_time_limit_enabled=data.get('response_time_limit_enabled', True),
                    response_timeout_amount=data.get('response_timeout_amount', 30),
                    response_timeout_unit=data.get('response_timeout_unit', 'minutes'),
                )
                response_serializer = WaitingNodeSerializer(node)

            else:
                return Response({'error': 'Invalid node type'}, status=status.HTTP_400_BAD_REQUEST)
            
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['get'])
    def connections(self, request, pk=None):
        """Get all connections for workflow"""
        workflow = self.get_object()
        connections = workflow.connections.order_by('created_at')
        serializer = NodeConnectionSerializer(connections, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def create_connection(self, request, pk=None):
        """Create a new connection between nodes"""
        workflow = self.get_object()
        serializer = CreateConnectionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            data = serializer.validated_data
            
            # Verify nodes belong to this workflow
            source_node = WorkflowNode.objects.get(
                id=data['source_node_id'], 
                workflow=workflow
            )
            target_node = WorkflowNode.objects.get(
                id=data['target_node_id'], 
                workflow=workflow
            )
            
            connection = NodeConnection.objects.create(
                workflow=workflow,
                source_node=source_node,
                target_node=target_node,
                connection_type=data.get('connection_type', 'success'),
                condition=data.get('condition', {}),
            )
            
            response_serializer = NodeConnectionSerializer(connection)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        
        except WorkflowNode.DoesNotExist:
            return Response({'error': 'Node not found or does not belong to this workflow'}, 
                          status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def execute_with_nodes(self, request, pk=None):
        """Execute workflow using node-based structure"""
        workflow = self.get_object()
        serializer = WorkflowExecuteWithNodesSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            # This would integrate with the enhanced execution service
            # For now, we'll use the existing execution logic
            from workflow.services.workflow_execution_service import WorkflowExecutionService
            
            execution_service = WorkflowExecutionService()
            execution = execution_service.execute_workflow(workflow, serializer.validated_data['context'])
            
            return Response({
                'execution_id': execution.id,
                'status': execution.status,
                'message': 'Node-based workflow execution started'
            }, status=status.HTTP_201_CREATED)
        
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
