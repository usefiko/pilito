"""
Unified Node ViewSet for complete node management
"""

import logging
from typing import Dict, Any

from rest_framework import viewsets, status, permissions, serializers
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Count, Q
from django.utils import timezone

from workflow.models import (
    Workflow,
    WorkflowNode,
    WhenNode,
    ConditionNode,
    ActionNode,
    NodeConnection,
)
from workflow.serializers import UnifiedNodeSerializer

logger = logging.getLogger(__name__)


class StandardResultPagination(PageNumberPagination):
    page_size = 50
    page_size_query_param = 'page_size'
    max_page_size = 100


class UnifiedNodeViewSet(viewsets.ModelViewSet):
    """
    Unified ViewSet for complete node management (CRUD) with supported node types.
    Waiting node handling is temporarily removed.
    """
    queryset = WorkflowNode.objects.all()
    serializer_class = UnifiedNodeSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultPagination
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['node_type', 'workflow', 'is_active']
    search_fields = ['title', 'description']
    ordering = ['-updated_at']
    
    def get_queryset(self):
        """Filter nodes by user's workflows"""
        queryset = super().get_queryset()
        if hasattr(self.request.user, 'created_workflows'):
            user_workflows = self.request.user.created_workflows.all()
            queryset = queryset.filter(workflow__in=user_workflows)
        return queryset.select_related('workflow').prefetch_related(
            'outgoing_connections', 'incoming_connections'
        )
    
    def perform_create(self, serializer):
        """Create node with proper workflow association"""
        workflow_id = self.request.data.get('workflow')
        if workflow_id:
            try:
                workflow = Workflow.objects.get(id=workflow_id)
                serializer.save(workflow=workflow)
            except Workflow.DoesNotExist:
                raise serializers.ValidationError({'workflow': 'Invalid workflow ID'})
        else:
            raise serializers.ValidationError({'workflow': 'Workflow ID is required'})
    
    def update(self, request, *args, **kwargs):
        """
        Override update to implement partial updates - only modify fields that are sent in the request
        No validation of unrelated fields like key_word, key_value, or tags unless provided
        """
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        
        # For PATCH requests, always use partial=True to only update provided fields
        if request.method == 'PATCH':
            partial = True
        
        # Store the original request data to know which fields were sent
        request_fields = set(request.data.keys())
        
        # Use the UnifiedNodeSerializer which already handles smart partial updates
        # The serializer handles both 'configuration' and legacy 'config' fields
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        
        # The UnifiedNodeSerializer's update method already handles partial updates intelligently
        serializer.save()

        # Force-apply direct updates for simple fields
        direct_updates = {}
        if 'position_x' in request.data:
            direct_updates['position_x'] = request.data.get('position_x')
        if 'position_y' in request.data:
            direct_updates['position_y'] = request.data.get('position_y')
        if 'title' in request.data:
            direct_updates['title'] = request.data.get('title')
        if direct_updates:
            WorkflowNode.objects.filter(id=instance.id).update(**direct_updates)
        
        if getattr(instance, '_prefetched_objects_cache', None):
            # If 'prefetch_related' has been applied to a queryset, we need to
            # forcibly invalidate the prefetch cache on the instance.
            instance._prefetched_objects_cache = {}

        # IMPORTANT: Re-fetch a fresh instance to avoid any stale attribute caching
        # and ensure that base fields like position_x/position_y are reflected correctly
        refreshed = WorkflowNode.objects.get(id=instance.id)
        refreshed_serializer = self.get_serializer(refreshed)
        # Return complete serializer data for both PATCH and PUT requests
        return Response(refreshed_serializer.data)
    
    def partial_update(self, request, *args, **kwargs):
        """Handle PATCH requests with partial updates"""
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)
    
    def destroy(self, request, *args, **kwargs):
        """Delete node and clean up connections"""
        try:
            instance = self.get_object()
            
            # Delete related connections
            NodeConnection.objects.filter(
                Q(source_node=instance) | Q(target_node=instance)
            ).delete()
            
            # Delete the node
            self.perform_destroy(instance)
            
            return Response({
                'message': f'Node "{instance.title}" and its connections have been deleted successfully',
                'deleted_connections': f'All connections involving this node were removed'
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'error': f'Failed to delete node: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['get'])
    def connections(self, request, pk=None):
        """Get all connections for this node"""
        node = self.get_object()
        
        # Get source connections (this node as source)
        source_connections = NodeConnection.objects.filter(source_node=node)
        source_data = [
            {
                'id': conn.id,
                'type': 'outgoing',
                'target_node': {
                    'id': conn.target_node.id,
                    'title': conn.target_node.title,
                    'node_type': conn.target_node.node_type
                },
                'connection_type': conn.connection_type,
                'condition': conn.condition
            }
            for conn in source_connections
        ]
        
        # Get target connections (this node as target)
        target_connections = NodeConnection.objects.filter(target_node=node)
        target_data = [
            {
                'id': conn.id,
                'type': 'incoming',
                'source_node': {
                    'id': conn.source_node.id,
                    'title': conn.source_node.title,
                    'node_type': conn.source_node.node_type
                },
                'connection_type': conn.connection_type,
                'condition': conn.condition
            }
            for conn in target_connections
        ]
        
        return Response({
            'node_id': node.id,
            'node_title': node.title,
            'outgoing_connections': source_data,
            'incoming_connections': target_data,
            'total_connections': len(source_data) + len(target_data)
        })
    
    @action(detail=True, methods=['post'])
    def duplicate(self, request, pk=None):
        """Duplicate a node with all its properties"""
        try:
            original_node = self.get_object()
            
            # Get the specific node instance
            if hasattr(original_node, 'whennode'):
                specific_node = original_node.whennode
            elif hasattr(original_node, 'conditionnode'):
                specific_node = original_node.conditionnode
            elif hasattr(original_node, 'actionnode'):
                specific_node = original_node.actionnode
            else:
                specific_node = original_node
            
            # Create duplicate data
            duplicate_data = {}
            for field in specific_node._meta.fields:
                if field.name not in ['id', 'created_at', 'updated_at']:
                    duplicate_data[field.name] = getattr(specific_node, field.name)
            
            # Modify title to indicate it's a duplicate
            duplicate_data['title'] = f"{duplicate_data['title']} (Copy)"
            
            # Adjust position slightly
            duplicate_data['position_x'] = duplicate_data.get('position_x', 0) + 50
            duplicate_data['position_y'] = duplicate_data.get('position_y', 0) + 50
            
            # Create new node
            serializer = self.get_serializer(data=duplicate_data)
            serializer.is_valid(raise_exception=True)
            duplicated_node = serializer.save()
            
            return Response({
                'message': f'Node "{original_node.title}" duplicated successfully',
                'original_node_id': original_node.id,
                'duplicated_node': serializer.data
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response({
                'error': f'Failed to duplicate node: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        """Activate a node"""
        node = self.get_object()
        node.is_active = True
        node.save()
        
        return Response({
            'message': f'Node "{node.title}" activated successfully',
            'node_id': node.id,
            'is_active': node.is_active
        })
    
    @action(detail=True, methods=['post'])
    def deactivate(self, request, pk=None):
        """Deactivate a node"""
        node = self.get_object()
        node.is_active = False
        node.save()
        
        return Response({
            'message': f'Node "{node.title}" deactivated successfully',
            'node_id': node.id,
            'is_active': node.is_active
        })
    
    @action(detail=False, methods=['get'])
    def types(self, request):
        """Get all available node types with their descriptions"""
        node_types = [
            {
                'value': 'when',
                'label': 'When Node',
                'description': 'Triggers that start the workflow',
                'icon': '▶️',
                'color': '#4CAF50'
            },
            {
                'value': 'condition',
                'label': 'Condition Node', 
                'description': 'Logic conditions to control flow',
                'icon': '❓',
                'color': '#FF9800'
            },
            {
                'value': 'action',
                'label': 'Action Node',
                'description': 'Actions to perform',
                'icon': '⚡',
                'color': '#2196F3'
            }
        ]
        
        return Response(node_types)
    
    @action(detail=False, methods=['get'])
    def by_workflow(self, request):
        """Get all nodes grouped by workflow"""
        workflow_id = request.query_params.get('workflow_id')
        
        if workflow_id:
            try:
                workflow = Workflow.objects.get(id=workflow_id)
                nodes = self.get_queryset().filter(workflow=workflow)
                
                # Group by node type
                grouped_nodes = {
                    'when': [],
                    'condition': [],
                    'action': []
                }
                
                for node in nodes:
                    serializer = self.get_serializer(node)
                    grouped_nodes[node.node_type].append(serializer.data)
                
                return Response({
                    'workflow_id': workflow.id,
                    'workflow_name': workflow.name,
                    'nodes': grouped_nodes,
                    'total_nodes': nodes.count()
                })
                
            except Workflow.DoesNotExist:
                return Response({
                    'error': 'Workflow not found'
                }, status=status.HTTP_404_NOT_FOUND)
        else:
            return Response({
                'error': 'workflow_id parameter is required'
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def test_execution(self, request, pk=None):
        """Test node execution with provided context"""
        node = self.get_object()
        context = request.data.get('context', {})
        
        try:
            # Basic test execution logic based on node type
            if node.node_type == 'when':
                # Test when node trigger logic
                result = {
                    'node_type': 'when',
                    'triggered': True,
                    'message': f'When node "{node.title}" would trigger with provided context'
                }
            elif node.node_type == 'condition':
                # Test condition evaluation
                result = {
                    'node_type': 'condition',
                    'condition_met': True,  # This would use actual condition evaluator
                    'message': f'Condition node "{node.title}" evaluation result'
                }
            elif node.node_type == 'action':
                # Test action execution
                result = {
                    'node_type': 'action',
                    'executed': True,
                    'message': f'Action node "{node.title}" would execute successfully'
                }
            else:
                result = {
                    'error': 'Unknown node type'
                }
            
            result.update({
                'node_id': node.id,
                'node_title': node.title,
                'test_context': context,
                'timestamp': timezone.now().isoformat()
            })
            
            return Response(result)
            
        except Exception as e:
            return Response({
                'error': f'Test execution failed: {str(e)}',
                'node_id': node.id,
                'node_title': node.title
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['delete'])
    def delete_connections(self, request, pk=None):
        """Delete all connections for this node"""
        try:
            node = self.get_object()
            
            # Get all connections involving this node
            from workflow.models import NodeConnection
            connections = NodeConnection.objects.filter(
                Q(source_node=node) | Q(target_node=node)
            )
            
            if not connections.exists():
                return Response({
                    'message': f'No connections found for node "{node.title}"',
                    'deleted_count': 0,
                    'status': 'success'
                }, status=status.HTTP_200_OK)
            
            # Store connection info before deletion
            deleted_connections = []
            for conn in connections:
                deleted_connections.append({
                    'id': str(conn.id),
                    'connection_type': conn.connection_type,
                    'direction': 'outgoing' if conn.source_node == node else 'incoming',
                    'other_node': {
                        'id': str(conn.target_node.id if conn.source_node == node else conn.source_node.id),
                        'title': conn.target_node.title if conn.source_node == node else conn.source_node.title
                    }
                })
            
            # Delete connections
            deleted_count = connections.count()
            connections.delete()
            
            return Response({
                'message': f'Successfully deleted {deleted_count} connections for node "{node.title}"',
                'deleted_count': deleted_count,
                'node_id': node.id,
                'node_title': node.title,
                'deleted_connections': deleted_connections,
                'status': 'success'
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'error': f'Failed to delete connections: {str(e)}',
                'node_id': pk,
                'status': 'error'
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def disconnect_from(self, request, pk=None):
        """Disconnect this node from specific target nodes"""
        try:
            node = self.get_object()
            target_node_ids = request.data.get('target_node_ids', [])
            connection_type = request.data.get('connection_type')  # optional filter
            
            if not target_node_ids:
                return Response({
                    'error': 'target_node_ids is required',
                    'status': 'error'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Build query filters
            filters = {
                'source_node': node,
                'target_node_id__in': target_node_ids
            }
            
            if connection_type:
                filters['connection_type'] = connection_type
            
            # Get connections to delete
            from workflow.models import NodeConnection
            connections = NodeConnection.objects.filter(**filters)
            
            if not connections.exists():
                return Response({
                    'error': 'No connections found matching the criteria',
                    'status': 'error'
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Store connection info
            deleted_connections = []
            for conn in connections:
                deleted_connections.append({
                    'id': str(conn.id),
                    'target_node': {
                        'id': str(conn.target_node.id),
                        'title': conn.target_node.title
                    },
                    'connection_type': conn.connection_type
                })
            
            # Delete connections
            deleted_count = connections.count()
            connections.delete()
            
            return Response({
                'message': f'Successfully disconnected node "{node.title}" from {deleted_count} target nodes',
                'deleted_count': deleted_count,
                'source_node_id': node.id,
                'source_node_title': node.title,
                'deleted_connections': deleted_connections,
                'status': 'success'
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'error': f'Failed to disconnect: {str(e)}',
                'status': 'error'
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def disconnect_incoming(self, request, pk=None):
        """Disconnect all incoming connections to this node"""
        try:
            node = self.get_object()
            
            # Get all incoming connections
            from workflow.models import NodeConnection
            incoming_connections = NodeConnection.objects.filter(target_node=node)
            
            if not incoming_connections.exists():
                return Response({
                    'message': f'No incoming connections found for node "{node.title}"',
                    'deleted_count': 0,
                    'status': 'success'
                }, status=status.HTTP_200_OK)
            
            # Store connection info
            deleted_connections = []
            for conn in incoming_connections:
                deleted_connections.append({
                    'id': str(conn.id),
                    'source_node': {
                        'id': str(conn.source_node.id),
                        'title': conn.source_node.title
                    },
                    'connection_type': conn.connection_type
                })
            
            # Delete incoming connections
            deleted_count = incoming_connections.count()
            incoming_connections.delete()
            
            return Response({
                'message': f'Successfully deleted {deleted_count} incoming connections for node "{node.title}"',
                'deleted_count': deleted_count,
                'target_node_id': node.id,
                'target_node_title': node.title,
                'deleted_connections': deleted_connections,
                'status': 'success'
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'error': f'Failed to delete incoming connections: {str(e)}',
                'status': 'error'
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def disconnect_outgoing(self, request, pk=None):
        """Disconnect all outgoing connections from this node"""
        try:
            node = self.get_object()
            
            # Get all outgoing connections
            from workflow.models import NodeConnection
            outgoing_connections = NodeConnection.objects.filter(source_node=node)
            
            if not outgoing_connections.exists():
                return Response({
                    'message': f'No outgoing connections found for node "{node.title}"',
                    'deleted_count': 0,
                    'status': 'success'
                }, status=status.HTTP_200_OK)
            
            # Store connection info
            deleted_connections = []
            for conn in outgoing_connections:
                deleted_connections.append({
                    'id': str(conn.id),
                    'target_node': {
                        'id': str(conn.target_node.id),
                        'title': conn.target_node.title
                    },
                    'connection_type': conn.connection_type
                })
            
            # Delete outgoing connections
            deleted_count = outgoing_connections.count()
            outgoing_connections.delete()
            
            return Response({
                'message': f'Successfully deleted {deleted_count} outgoing connections for node "{node.title}"',
                'deleted_count': deleted_count,
                'source_node_id': node.id,
                'source_node_title': node.title,
                'deleted_connections': deleted_connections,
                'status': 'success'
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'error': f'Failed to delete outgoing connections: {str(e)}',
                'status': 'error'
            }, status=status.HTTP_400_BAD_REQUEST)
