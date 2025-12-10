"""
Serializers for Workflow API
"""

from rest_framework import serializers
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


class EventTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = EventType
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'updated_at')


class TriggerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Trigger
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'updated_at')


class ConditionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Condition
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'updated_at')


class ActionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Action
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'updated_at')


class ActionTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ActionTemplate
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'updated_at')


class WorkflowSerializer(serializers.ModelSerializer):
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    
    class Meta:
        model = Workflow
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'updated_at', 'created_by')
    
    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)


class TriggerWorkflowAssociationSerializer(serializers.ModelSerializer):
    trigger_name = serializers.CharField(source='trigger.name', read_only=True)
    workflow_name = serializers.CharField(source='workflow.name', read_only=True)
    
    class Meta:
        model = TriggerWorkflowAssociation
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'updated_at')


class WorkflowActionSerializer(serializers.ModelSerializer):
    action_name = serializers.CharField(source='action.name', read_only=True)
    action_type = serializers.CharField(source='action.action_type', read_only=True)
    condition_name = serializers.CharField(source='condition.name', read_only=True)
    
    class Meta:
        model = WorkflowAction
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'updated_at')


class WorkflowExecutionSerializer(serializers.ModelSerializer):
    workflow_name = serializers.CharField(source='workflow.name', read_only=True)
    duration = serializers.SerializerMethodField()
    
    class Meta:
        model = WorkflowExecution
        fields = '__all__'
        read_only_fields = ('id', 'created_at')
    
    def get_duration(self, obj):
        if obj.duration:
            return obj.duration.total_seconds()
        return None


class WorkflowActionExecutionSerializer(serializers.ModelSerializer):
    action_name = serializers.CharField(source='workflow_action.action.name', read_only=True)
    action_type = serializers.CharField(source='workflow_action.action.action_type', read_only=True)
    duration = serializers.SerializerMethodField()
    
    class Meta:
        model = WorkflowActionExecution
        fields = '__all__'
        read_only_fields = ('id', 'queued_at')
    
    def get_duration(self, obj):
        if obj.duration:
            return obj.duration.total_seconds()
        return None


class TriggerEventLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = TriggerEventLog
        fields = '__all__'
        read_only_fields = ('id', 'created_at')


class ActionLogSerializer(serializers.ModelSerializer):
    action_name = serializers.CharField(source='action.name', read_only=True)
    action_type = serializers.CharField(source='action.action_type', read_only=True)
    
    class Meta:
        model = ActionLog
        fields = '__all__'
        read_only_fields = ('id', 'executed_at')


# Specialized serializers for API endpoints

class WorkflowListSerializer(serializers.ModelSerializer):
    """Simplified serializer for workflow list view"""
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    actions_count = serializers.SerializerMethodField()
    triggers_count = serializers.SerializerMethodField()
    executions_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Workflow
        fields = [
            'id', 'name', 'description', 'status', 'created_by_username',
            'start_date', 'end_date', 'created_at', 'updated_at',
            'actions_count', 'triggers_count', 'executions_count'
        ]
    
    def get_actions_count(self, obj):
        return obj.workflow_actions.count()
    
    def get_triggers_count(self, obj):
        return obj.trigger_associations.count()
    
    def get_executions_count(self, obj):
        return obj.executions.count()


class WorkflowDetailSerializer(WorkflowSerializer):
    """Detailed serializer for workflow detail view with complete node and connection data"""
    actions = WorkflowActionSerializer(source='workflow_actions', many=True, read_only=True)
    triggers = TriggerWorkflowAssociationSerializer(source='trigger_associations', many=True, read_only=True)
    recent_executions = serializers.SerializerMethodField()
    
    # Add node and connection data
    nodes = serializers.SerializerMethodField()
    connections = serializers.SerializerMethodField()
    node_summary = serializers.SerializerMethodField()
    
    class Meta(WorkflowSerializer.Meta):
        pass
    
    def get_recent_executions(self, obj):
        recent = obj.executions.order_by('-created_at')[:5]
        return WorkflowExecutionSerializer(recent, many=True).data
    
    def get_nodes(self, obj):
        """Get all nodes for this workflow"""
        nodes_data = []
        
        # Get all node types
        when_nodes = obj.nodes.filter(node_type='when').select_related('workflow')
        condition_nodes = obj.nodes.filter(node_type='condition').select_related('workflow')
        action_nodes = obj.nodes.filter(node_type='action').select_related('workflow')
        waiting_nodes = obj.nodes.filter(node_type='waiting').select_related('workflow')
        
        # Serialize each type with appropriate serializer
        for when_node in when_nodes:
            when_instance = WhenNode.objects.get(id=when_node.id)
            nodes_data.append(WhenNodeSerializer(when_instance).data)
            
        for condition_node in condition_nodes:
            condition_instance = ConditionNode.objects.get(id=condition_node.id)
            nodes_data.append(ConditionNodeSerializer(condition_instance).data)
            
        for action_node in action_nodes:
            action_instance = ActionNode.objects.get(id=action_node.id)
            nodes_data.append(ActionNodeSerializer(action_instance).data)
            
        for waiting_node in waiting_nodes:
            waiting_instance = WaitingNode.objects.get(id=waiting_node.id)
            nodes_data.append(WaitingNodeSerializer(waiting_instance).data)
        
        return nodes_data
    
    def get_connections(self, obj):
        """Get all connections for this workflow"""
        connections = NodeConnection.objects.filter(
            source_node__workflow=obj
        ).select_related('source_node', 'target_node')
        return NodeConnectionSerializer(connections, many=True).data
    
    def get_node_summary(self, obj):
        """Get summary count of each node type"""
        nodes = obj.nodes.filter(is_active=True)
        return {
            'total_nodes': nodes.count(),
            'when_nodes': nodes.filter(node_type='when').count(),
            'condition_nodes': nodes.filter(node_type='condition').count(),
            'action_nodes': nodes.filter(node_type='action').count(),
            'waiting_nodes': nodes.filter(node_type='waiting').count(),
            'total_connections': NodeConnection.objects.filter(source_node__workflow=obj).count()
        }


class TriggerTestSerializer(serializers.Serializer):
    """Serializer for testing triggers"""
    context = serializers.JSONField()


class WorkflowExecuteSerializer(serializers.Serializer):
    """Serializer for manual workflow execution"""
    context = serializers.JSONField()


class ProcessEventSerializer(serializers.Serializer):
    """Serializer for processing events"""
    event_type = serializers.CharField(max_length=100)
    data = serializers.JSONField()
    user_id = serializers.CharField(max_length=100, required=False, allow_null=True)
    conversation_id = serializers.CharField(max_length=100, required=False, allow_null=True)


# New Node-Based Workflow Serializers

class WorkflowNodeSerializer(serializers.ModelSerializer):
    """Base serializer for workflow nodes"""
    node_type_display = serializers.CharField(source='get_node_type_display', read_only=True)
    
    class Meta:
        model = WorkflowNode
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'updated_at')


class WhenNodeSerializer(serializers.ModelSerializer):
    """Serializer for When nodes"""
    node_type_display = serializers.CharField(source='get_node_type_display', read_only=True)
    when_type_display = serializers.CharField(source='get_when_type_display', read_only=True)
    
    class Meta:
        model = WhenNode
        fields = '__all__'
        read_only_fields = ('id', 'node_type', 'created_at', 'updated_at')


class ConditionNodeSerializer(serializers.ModelSerializer):
    """Serializer for Condition nodes"""
    node_type_display = serializers.CharField(source='get_node_type_display', read_only=True)
    combination_operator_display = serializers.CharField(source='get_combination_operator_display', read_only=True)
    
    class Meta:
        model = ConditionNode
        fields = '__all__'
        read_only_fields = ('id', 'node_type', 'created_at', 'updated_at')


class ActionNodeSerializer(serializers.ModelSerializer):
    """Serializer for Action nodes"""
    node_type_display = serializers.CharField(source='get_node_type_display', read_only=True)
    action_type_display = serializers.CharField(source='get_action_type_display', read_only=True)
    
    class Meta:
        model = ActionNode
        fields = '__all__'
        read_only_fields = ('id', 'node_type', 'created_at', 'updated_at')

    def to_representation(self, instance):
        """Add configuration object for Instagram actions for frontend compatibility"""
        data = super().to_representation(instance)
        
        # Add 'configuration' object for Instagram actions
        if instance.action_type == 'instagram_comment_dm_reply':
            data['configuration'] = {
                'dm_mode': instance.instagram_dm_mode or 'STATIC',
                'dm_text_template': instance.instagram_dm_text_template or '',
                'product_id': str(instance.instagram_product_id) if instance.instagram_product_id else None,
                'public_reply_enabled': instance.instagram_public_reply_enabled,
                'public_reply_template': instance.instagram_public_reply_text or '',
            }
        
        # Ensure key_values is always a list
        if 'key_values' not in data or data['key_values'] is None:
            data['key_values'] = []
        
        return data


class WaitingNodeSerializer(serializers.ModelSerializer):
    """Serializer for Waiting nodes"""
    node_type_display = serializers.CharField(source='get_node_type_display', read_only=True)
    storage_type_display = serializers.CharField(source='get_storage_type_display', read_only=True)
    response_timeout_unit_display = serializers.CharField(source='get_response_timeout_unit_display', read_only=True)
    
    # Frontend compatibility: allow skip_keywords as alias for exit_keywords
    skip_keywords = serializers.ListField(
        child=serializers.CharField(), 
        source='exit_keywords', 
        required=False,
        help_text="Frontend alias for exit_keywords"
    )
    
    class Meta:
        model = WaitingNode
        fields = '__all__'
        read_only_fields = ('id', 'node_type', 'created_at', 'updated_at')
    
    def to_representation(self, instance):
        """Ensure key_values is always a list"""
        data = super().to_representation(instance)
        
        # Ensure key_values is always a list
        if 'key_values' not in data or data['key_values'] is None:
            data['key_values'] = []
        
        return data
    
    def validate(self, data):
        """Handle skip_keywords to exit_keywords mapping for frontend compatibility"""
        # Handle skip_keywords mapping if provided separately (e.g., in request data before source mapping)
        request_data = getattr(self, 'initial_data', {})
        if 'skip_keywords' in request_data and 'exit_keywords' not in data:
            # This handles cases where skip_keywords is sent but exit_keywords is not yet in validated_data
            skip_keywords = request_data.get('skip_keywords', [])
            if skip_keywords:
                data['exit_keywords'] = skip_keywords
        
        return data
    
    def update(self, instance, validated_data):
        """Handle skip_keywords to exit_keywords mapping during updates"""
        # Check for skip_keywords in initial_data to handle field mapping
        request_data = getattr(self, 'initial_data', {})
        
        if 'skip_keywords' in request_data:
            skip_keywords = request_data.get('skip_keywords', [])
            existing_exit_keywords = validated_data.get('exit_keywords', instance.exit_keywords or [])
            
            # If both skip_keywords and exit_keywords are provided, merge them
            if 'exit_keywords' in request_data:
                explicit_exit_keywords = request_data.get('exit_keywords', [])
                combined_keywords = list(set(skip_keywords + explicit_exit_keywords))
                validated_data['exit_keywords'] = combined_keywords
            else:
                # Only skip_keywords provided, use them as exit_keywords
                validated_data['exit_keywords'] = skip_keywords
        
        return super().update(instance, validated_data)


class NodeConnectionSerializer(serializers.ModelSerializer):
    """Serializer for node connections"""
    source_node_title = serializers.CharField(source='source_node.title', read_only=True)
    target_node_title = serializers.CharField(source='target_node.title', read_only=True)
    connection_type_display = serializers.CharField(source='get_connection_type_display', read_only=True)
    
    class Meta:
        model = NodeConnection
        fields = '__all__'
        read_only_fields = ('id', 'created_at')


class UserResponseSerializer(serializers.ModelSerializer):
    """Serializer for user responses"""
    waiting_node_title = serializers.CharField(source='waiting_node.title', read_only=True)
    workflow_name = serializers.CharField(source='workflow_execution.workflow.name', read_only=True)
    
    class Meta:
        model = UserResponse
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'processed_at')


class NodeBasedWorkflowSerializer(serializers.ModelSerializer):
    """Enhanced workflow serializer with node-based structure"""
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    nodes = WorkflowNodeSerializer(many=True, read_only=True)
    connections = NodeConnectionSerializer(many=True, read_only=True)
    nodes_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Workflow
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'updated_at', 'created_by')
    
    def get_nodes_count(self, obj):
        return obj.nodes.count()
    
    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)


class WorkflowDetailWithNodesSerializer(NodeBasedWorkflowSerializer):
    """Detailed workflow serializer with all nodes and connections"""
    when_nodes = WhenNodeSerializer(source='nodes.whennode_set', many=True, read_only=True)
    condition_nodes = ConditionNodeSerializer(source='nodes.conditionnode_set', many=True, read_only=True)
    action_nodes = ActionNodeSerializer(source='nodes.actionnode_set', many=True, read_only=True)
    waiting_nodes = WaitingNodeSerializer(source='nodes.waitingnode_set', many=True, read_only=True)
    recent_executions = serializers.SerializerMethodField()
    
    def get_recent_executions(self, obj):
        recent = obj.executions.order_by('-created_at')[:5]
        return WorkflowExecutionSerializer(recent, many=True).data


class CreateNodeSerializer(serializers.Serializer):
    """Serializer for creating workflow nodes"""
    node_type = serializers.ChoiceField(choices=WorkflowNode.NODE_TYPE_CHOICES)
    title = serializers.CharField(max_length=200)
    position_x = serializers.FloatField(default=0)
    position_y = serializers.FloatField(default=0)
    configuration = serializers.JSONField(default=dict)
    
    # When node fields
    when_type = serializers.ChoiceField(choices=WhenNode.WHEN_TYPE_CHOICES, required=False)
    keywords = serializers.ListField(child=serializers.CharField(), required=False, default=list)
    tags = serializers.ListField(child=serializers.CharField(), required=False, default=list)
    channels = serializers.ListField(child=serializers.CharField(), required=False, default=list)
    schedule_frequency = serializers.ChoiceField(choices=WhenNode.SCHEDULE_FREQUENCY_CHOICES, required=False)
    schedule_start_date = serializers.DateField(required=False)
    schedule_time = serializers.TimeField(required=False)
    
    # Condition node fields
    combination_operator = serializers.ChoiceField(choices=ConditionNode.OPERATOR_CHOICES, required=False, default='or')
    conditions = serializers.ListField(child=serializers.JSONField(), required=False, default=list)
    
    # Action node fields
    action_type = serializers.ChoiceField(choices=ActionNode.ACTION_TYPE_CHOICES, required=False)
    message_content = serializers.CharField(required=False, allow_blank=True)
    key_values = serializers.ListField(required=False, default=list, help_text="Key-value pairs for CTA buttons")
    delay_amount = serializers.IntegerField(required=False, default=0)
    delay_unit = serializers.CharField(required=False, default='minutes')
    redirect_destination = serializers.ChoiceField(choices=ActionNode.REDIRECT_DESTINATIONS, required=False)
    tag_name = serializers.CharField(required=False, allow_blank=True)
    webhook_url = serializers.URLField(required=False, allow_blank=True)
    webhook_method = serializers.CharField(required=False, default='POST')
    webhook_headers = serializers.JSONField(required=False, default=dict)
    webhook_payload = serializers.JSONField(required=False, default=dict)
    custom_code = serializers.CharField(required=False, allow_blank=True)
    
    # Waiting node fields
    storage_type = serializers.ChoiceField(choices=WaitingNode.STORAGE_TYPE_CHOICES, required=False, default='text')
    customer_message = serializers.CharField(required=False, allow_blank=True)
    error_message = serializers.CharField(required=False, allow_blank=True, default='')
    choice_options = serializers.ListField(child=serializers.CharField(), required=False, default=list)
    allowed_errors = serializers.IntegerField(required=False, default=3)
    exit_keywords = serializers.ListField(child=serializers.CharField(), required=False, default=list)
    skip_keywords = serializers.ListField(child=serializers.CharField(), required=False, default=list, help_text="Frontend alias for exit_keywords")
    
    # Response time limit fields
    response_time_limit_enabled = serializers.BooleanField(required=False, default=True)
    response_timeout_amount = serializers.IntegerField(required=False, default=30)
    response_timeout_unit = serializers.ChoiceField(choices=WaitingNode.TIME_UNIT_CHOICES, required=False, default='minutes')
    
    # Legacy field for backward compatibility
    response_timeout = serializers.IntegerField(required=False, default=3600)
    
    def validate(self, data):
        """Validate node creation data based on node type"""
        node_type = data.get('node_type')
        
        # Set default values for required fields if not provided
        if node_type == 'waiting':
            if not data.get('customer_message'):
                data['customer_message'] = 'Please enter your response:'
            
            # Handle skip_keywords to exit_keywords mapping for frontend compatibility
            if 'skip_keywords' in data and data['skip_keywords']:
                if not data.get('exit_keywords'):
                    data['exit_keywords'] = data['skip_keywords']
                else:
                    # Merge both lists if both are provided
                    combined_keywords = list(set(data['exit_keywords'] + data['skip_keywords']))
                    data['exit_keywords'] = combined_keywords
        
        elif node_type == 'action':
            action_type = data.get('action_type', 'send_message')
            if action_type == 'send_message' and not data.get('message_content'):
                data['message_content'] = 'Default message'
        
        # Ensure key_values is always a list if provided
        if 'key_values' in data and data['key_values'] is None:
            data['key_values'] = []
        
        return data


class CreateConnectionSerializer(serializers.Serializer):
    """Serializer for creating node connections"""
    source_node_id = serializers.UUIDField()
    target_node_id = serializers.UUIDField()
    connection_type = serializers.ChoiceField(choices=NodeConnection.CONNECTION_TYPE_CHOICES, default='success')
    condition = serializers.JSONField(default=dict)


class WorkflowExecuteWithNodesSerializer(serializers.Serializer):
    """Serializer for executing node-based workflows"""
    context = serializers.JSONField()
    start_node_id = serializers.UUIDField(required=False, help_text="Optional specific node to start from")


class UnifiedNodeSerializer(serializers.ModelSerializer):
    """Unified serializer for all node types with complete CRUD support"""
    node_type = serializers.CharField()
    
    # Common fields for all nodes
    workflow_name = serializers.CharField(source='workflow.name', read_only=True)
    
    # When Node specific fields
    when_type = serializers.CharField(required=False, allow_blank=True)
    when_type_display = serializers.CharField(source='get_when_type_display', read_only=True)
    keywords = serializers.ListField(child=serializers.CharField(), required=False, default=list)
    tags = serializers.ListField(child=serializers.CharField(), required=False, default=list)
    channels = serializers.ListField(child=serializers.CharField(), required=False, default=list)
    customer_tags = serializers.ListField(child=serializers.CharField(), required=False, default=list)
    schedule_frequency = serializers.CharField(required=False, allow_blank=True)
    schedule_time = serializers.TimeField(required=False, allow_null=True)
    # Model field is schedule_start_date; accept both for backward compatibility
    schedule_start_date = serializers.DateField(required=False, allow_null=True)
    schedule_date = serializers.DateField(required=False, allow_null=True, write_only=True)
    # Instagram Comment specific filters
    instagram_post_url = serializers.URLField(required=False, allow_blank=True, allow_null=True)
    instagram_media_type = serializers.CharField(required=False, allow_blank=True, default='all')
    comment_keywords = serializers.ListField(child=serializers.CharField(), required=False, default=list)
    
    # Condition Node specific fields
    combination_operator = serializers.CharField(required=False, allow_blank=True)
    combination_operator_display = serializers.CharField(source='get_combination_operator_display', read_only=True)
    conditions = serializers.JSONField(required=False, default=list)
    
    # Action Node specific fields
    action_type = serializers.CharField(required=False, allow_blank=True)
    action_type_display = serializers.CharField(source='get_action_type_display', read_only=True)
    message_content = serializers.CharField(required=False, allow_blank=True)
    
    # Key-value pairs for CTA buttons (used in both Action and Waiting nodes)
    key_values = serializers.JSONField(required=False, default=list)
    
    redirect_destination = serializers.CharField(required=False, allow_blank=True)
    delay_amount = serializers.IntegerField(required=False, allow_null=True)
    delay_unit = serializers.CharField(required=False, allow_blank=True)
    tag_name = serializers.CharField(required=False, allow_blank=True)
    tag_names = serializers.ListField(child=serializers.CharField(), required=False, default=list)
    webhook_url = serializers.URLField(required=False, allow_blank=True)
    webhook_method = serializers.CharField(required=False, allow_blank=True)
    webhook_headers = serializers.JSONField(required=False, default=dict)
    webhook_payload = serializers.JSONField(required=False, default=dict)
    email_to = serializers.EmailField(required=False, allow_blank=True)
    email_subject = serializers.CharField(required=False, allow_blank=True)
    email_body = serializers.CharField(required=False, allow_blank=True)
    custom_code = serializers.CharField(required=False, allow_blank=True)
    
    # Instagram Comment → DM + Reply fields
    instagram_dm_mode = serializers.CharField(required=False, allow_blank=True, default='STATIC')
    instagram_dm_text_template = serializers.CharField(required=False, allow_blank=True)
    instagram_product_id = serializers.UUIDField(required=False, allow_null=True)
    instagram_public_reply_enabled = serializers.BooleanField(required=False, default=False)
    instagram_public_reply_text = serializers.CharField(required=False, allow_blank=True)
    # Configuration field for frontend (write-only on input, added to output in to_representation)
    configuration = serializers.JSONField(required=False, write_only=True, default=dict)
    # Legacy config field for backwards compatibility (write-only, handled in to_internal_value)
    config = serializers.JSONField(required=False, write_only=True, default=dict)
    
    # Waiting Node specific fields
    storage_type = serializers.CharField(required=False, allow_blank=True)
    storage_type_display = serializers.CharField(source='get_storage_type_display', read_only=True)
    customer_message = serializers.CharField(required=False, allow_blank=True)
    error_message = serializers.CharField(required=False, allow_blank=True, default='')
    choice_options = serializers.JSONField(required=False, default=list)
    allowed_errors = serializers.IntegerField(required=False, default=3)
    exit_keywords = serializers.JSONField(required=False, default=list)
    response_time_limit_enabled = serializers.BooleanField(required=False, default=True)
    response_timeout_amount = serializers.IntegerField(required=False, default=30)
    response_timeout_unit = serializers.CharField(required=False, default='minutes')
    response_timeout_unit_display = serializers.CharField(source='get_response_timeout_unit_display', read_only=True)
    
    # Connection information
    connections_as_source = serializers.SerializerMethodField(read_only=True)
    connections_as_target = serializers.SerializerMethodField(read_only=True)
    
    class Meta:
        model = WorkflowNode
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'updated_at')
    
    def get_connections_as_source(self, obj):
        """Get connections where this node is the source"""
        connections = NodeConnection.objects.filter(source_node=obj)
        return [
            {
                'id': conn.id,
                'target_node': conn.target_node.id,
                'target_node_title': conn.target_node.title,
                'connection_type': conn.connection_type,
                'condition': conn.condition
            }
            for conn in connections
        ]
    
    def get_connections_as_target(self, obj):
        """Get connections where this node is the target"""
        connections = NodeConnection.objects.filter(target_node=obj)
        return [
            {
                'id': conn.id,
                'source_node': conn.source_node.id,
                'source_node_title': conn.source_node.title,
                'connection_type': conn.connection_type,
                'condition': conn.condition
            }
            for conn in connections
        ]
    
    def validate(self, data):
        """Validate data based on node type - skip validation for partial updates and specific fields"""
        # Skip validation during partial updates unless node_type is changing
        if hasattr(self, 'partial') and self.partial and 'node_type' not in data:
            # For PATCH requests, completely skip validation for these fields
            excluded_fields = ['key_word', 'key_value', 'tags', 'position_x', 'position_y', 'keywords', 'channels', 'customer_tags']
            
            # Remove excluded fields from validation data copy
            validation_data = {k: v for k, v in data.items() if k not in excluded_fields}
            
            # If only excluded fields are being updated, skip all validation
            if not validation_data:
                return data
            
            # Only validate non-excluded fields if they exist
            return data
            
        node_type = data.get('node_type')
        
        # If this is a partial update without node_type, get it from the instance
        if not node_type and hasattr(self, 'instance') and self.instance:
            node_type = self.instance.node_type
        
        if not node_type:
            raise serializers.ValidationError({'node_type': 'This field is required'})
        
        # For partial updates, only validate fields that are being updated
        if hasattr(self, 'partial') and self.partial:
            self._validate_partial_update(data, node_type)
        else:
            # Full validation for create/complete update
            if node_type == 'when':
                self._validate_when_node(data)
            elif node_type == 'condition':
                self._validate_condition_node(data)
            elif node_type == 'action':
                self._validate_action_node(data)
            elif node_type == 'waiting':
                self._validate_waiting_node(data)
            else:
                raise serializers.ValidationError({'node_type': f'Invalid node type: {node_type}'})
        
        return data
    
    def _validate_partial_update(self, data, node_type):
        """Validate only the fields being updated in a partial update"""
        if node_type == 'when':
            self._validate_when_node_partial(data)
        elif node_type == 'condition':
            self._validate_condition_node_partial(data)
        elif node_type == 'action':
            self._validate_action_node_partial(data)
        elif node_type == 'waiting':
            self._validate_waiting_node_partial(data)
    
    def _validate_when_node_partial(self, data):
        """Validate When Node fields only if they are being updated"""
        # Only validate scheduled fields if they are being updated
        if 'when_type' in data and data['when_type'] == 'scheduled':
            if 'schedule_frequency' in data and not data.get('schedule_frequency'):
                raise serializers.ValidationError({'schedule_frequency': 'Schedule frequency is required for scheduled when nodes'})
    
    def _validate_condition_node_partial(self, data):
        """Validate Condition Node fields only if they are being updated"""
        # Only validate conditions if they are being updated
        if 'conditions' in data:
            conditions = data.get('conditions', [])
            if not conditions:
                raise serializers.ValidationError({'conditions': 'At least one condition is required for Condition nodes'})
            
            # Validate each condition
            for i, condition in enumerate(conditions):
                if not isinstance(condition, dict):
                    raise serializers.ValidationError({'conditions': f'Condition {i+1} must be a dictionary'})
                
                condition_type = condition.get('type')
                if condition_type not in ['ai', 'message']:
                    raise serializers.ValidationError({'conditions': f'Condition {i+1} type must be "ai" or "message"'})
                
                if condition_type == 'ai' and not condition.get('prompt'):
                    raise serializers.ValidationError({'conditions': f'AI condition {i+1} must have a prompt'})
                
                if condition_type == 'message':
                    if not condition.get('operator'):
                        raise serializers.ValidationError({'conditions': f'Message condition {i+1} must have an operator'})
                    if not condition.get('value'):
                        raise serializers.ValidationError({'conditions': f'Message condition {i+1} must have a value'})
        
        # Only validate combination operator if it's being updated
        if 'combination_operator' in data:
            combination_operator = data.get('combination_operator')
            if combination_operator not in ['and', 'or']:
                raise serializers.ValidationError({'combination_operator': 'Combination operator must be "and" or "or"'})
    
    def _validate_action_node_partial(self, data):
        """Validate Action Node fields only if they are being updated"""
        # Only validate action type specific fields if action_type is being updated
        action_type = data.get('action_type')
        
        if action_type == 'send_message' and 'message_content' in data and not data.get('message_content'):
            raise serializers.ValidationError({'message_content': 'Message content is required for send_message actions'})
        
        if action_type == 'delay':
            if 'delay_amount' in data and not data.get('delay_amount'):
                raise serializers.ValidationError({'delay_amount': 'Delay amount is required for delay actions'})
            if 'delay_unit' in data and not data.get('delay_unit'):
                raise serializers.ValidationError({'delay_unit': 'Delay unit is required for delay actions'})
        
        if action_type == 'webhook':
            if 'webhook_url' in data and not data.get('webhook_url'):
                raise serializers.ValidationError({'webhook_url': 'Webhook URL is required for webhook actions'})
            if 'webhook_method' in data and not data.get('webhook_method'):
                raise serializers.ValidationError({'webhook_method': 'Webhook method is required for webhook actions'})
        
        if action_type == 'send_email':
            if 'email_to' in data and not data.get('email_to'):
                raise serializers.ValidationError({'email_to': 'Email to is required for send_email actions'})
            if 'email_subject' in data and not data.get('email_subject'):
                raise serializers.ValidationError({'email_subject': 'Email subject is required for send_email actions'})
    
    def _validate_waiting_node_partial(self, data):
        """Validate Waiting Node fields only if they are being updated"""
        # Validate choice options field format only if provided
        if 'choice_options' in data:
            choice_options = data.get('choice_options', [])
            if not isinstance(choice_options, list):
                raise serializers.ValidationError({'choice_options': 'Choice options must be a list'})
        
        # Validate storage configuration when storage_type is being updated
        if 'storage_type' in data:
            storage_type = data.get('storage_type')
            if storage_type and storage_type not in ['text', 'email', 'phone']:
                raise serializers.ValidationError({'storage_type': 'Invalid storage type'})
    
    def _validate_when_node(self, data):
        """Validate When Node specific fields"""
        when_type = data.get('when_type')
        if not when_type:
            raise serializers.ValidationError({'when_type': 'When type is required for When nodes'})
        
        # Validate scheduled when type
        if when_type == 'scheduled':
            if not data.get('schedule_frequency'):
                raise serializers.ValidationError({'schedule_frequency': 'Schedule frequency is required for scheduled when nodes'})
    
    def _validate_condition_node(self, data):
        """Validate Condition Node specific fields"""
        conditions = data.get('conditions', [])
        if not conditions:
            raise serializers.ValidationError({'conditions': 'At least one condition is required for Condition nodes'})
        
        combination_operator = data.get('combination_operator', 'and')
        if combination_operator not in ['and', 'or']:
            raise serializers.ValidationError({'combination_operator': 'Combination operator must be "and" or "or"'})
        
        # Validate each condition
        for i, condition in enumerate(conditions):
            if not isinstance(condition, dict):
                raise serializers.ValidationError({'conditions': f'Condition {i+1} must be a dictionary'})
            
            condition_type = condition.get('type')
            if condition_type not in ['ai', 'message']:
                raise serializers.ValidationError({'conditions': f'Condition {i+1} type must be "ai" or "message"'})
            
            if condition_type == 'ai' and not condition.get('prompt'):
                raise serializers.ValidationError({'conditions': f'AI condition {i+1} must have a prompt'})
            
            if condition_type == 'message':
                if not condition.get('operator'):
                    raise serializers.ValidationError({'conditions': f'Message condition {i+1} must have an operator'})
                if not condition.get('value'):
                    raise serializers.ValidationError({'conditions': f'Message condition {i+1} must have a value'})
    
    def _validate_action_node(self, data):
        """Validate Action Node specific fields"""
        action_type = data.get('action_type')
        if not action_type:
            raise serializers.ValidationError({'action_type': 'Action type is required for Action nodes'})
        
        # Validate specific action types
        if action_type == 'send_message' and not data.get('message_content'):
            raise serializers.ValidationError({'message_content': 'Message content is required for send_message actions'})
        
        if action_type == 'delay':
            if not data.get('delay_amount'):
                raise serializers.ValidationError({'delay_amount': 'Delay amount is required for delay actions'})
            if not data.get('delay_unit'):
                raise serializers.ValidationError({'delay_unit': 'Delay unit is required for delay actions'})
        
        if action_type == 'webhook':
            if not data.get('webhook_url'):
                raise serializers.ValidationError({'webhook_url': 'Webhook URL is required for webhook actions'})
            if not data.get('webhook_method'):
                raise serializers.ValidationError({'webhook_method': 'Webhook method is required for webhook actions'})
        
        if action_type == 'send_email':
            if not data.get('email_to'):
                raise serializers.ValidationError({'email_to': 'Email to is required for send_email actions'})
            if not data.get('email_subject'):
                raise serializers.ValidationError({'email_subject': 'Email subject is required for send_email actions'})
    
    def _validate_waiting_node(self, data):
        """Validate Waiting Node specific fields"""
        if not data.get('customer_message'):
            raise serializers.ValidationError({'customer_message': 'Customer message is required for Waiting nodes'})
        
        # Validate choice options field format if provided
        if 'choice_options' in data:
            choice_options = data.get('choice_options', [])
            if not isinstance(choice_options, list):
                raise serializers.ValidationError({'choice_options': 'Choice options must be a list'})
        
        # Validate storage configuration
        storage_type = data.get('storage_type')
        if storage_type and storage_type not in ['text', 'email', 'phone']:
            raise serializers.ValidationError({'storage_type': 'Invalid storage type'})
        
        # Validate time limit fields - only required when response_time_limit_enabled is True
        response_time_limit_enabled = data.get('response_time_limit_enabled', False)
        if response_time_limit_enabled:
            if not data.get('response_timeout_amount'):
                raise serializers.ValidationError({'response_timeout_amount': 'Timeout amount is required when time limit is enabled'})
            if not data.get('response_timeout_unit'):
                raise serializers.ValidationError({'response_timeout_unit': 'Timeout unit is required when time limit is enabled'})
            
            # Validate timeout amount is positive
            timeout_amount = data.get('response_timeout_amount')
            if timeout_amount and timeout_amount <= 0:
                raise serializers.ValidationError({'response_timeout_amount': 'Timeout amount must be greater than 0'})

    def create(self, validated_data):
        """Create appropriate node type based on node_type"""
        node_type = validated_data.pop('node_type')
        
        if node_type == 'when':
            return WhenNode.objects.create(**validated_data)
        elif node_type == 'condition':
            return ConditionNode.objects.create(**validated_data)
        elif node_type == 'action':
            return ActionNode.objects.create(**validated_data)
        elif node_type == 'waiting':
            return WaitingNode.objects.create(**validated_data)
        else:
            raise serializers.ValidationError(f"Invalid node_type: {node_type}")
    
    def update(self, instance, validated_data):
        """Smart update that accepts any field and applies changes intelligently"""
        # Remove node_type from validated_data as it shouldn't be changed
        validated_data.pop('node_type', None)
        
        # Get the specific node instance based on type
        specific_instance = None
        if hasattr(instance, 'whennode'):
            specific_instance = instance.whennode
        elif hasattr(instance, 'conditionnode'):
            specific_instance = instance.conditionnode
        elif hasattr(instance, 'actionnode'):
            specific_instance = instance.actionnode
        elif hasattr(instance, 'waitingnode'):
            specific_instance = instance.waitingnode
        
        # Update base WorkflowNode fields (including direct position updates)
        base_fields = ['title', 'description', 'position_x', 'position_y', 'is_active', 'workflow']
        for field in base_fields:
            if field in validated_data:
                setattr(instance, field, validated_data[field])
        
        # Smart position handling (only for advanced position operations)
        # Skip if direct position_x/position_y are being updated to avoid conflicts
        if not ('position_x' in validated_data or 'position_y' in validated_data):
            self._handle_position_updates(instance, validated_data)
        
        # Smart update for type-specific fields
        if specific_instance:
            self._smart_update_specific_fields(specific_instance, validated_data)
        
        # Save both instances
        instance.save()
        if specific_instance:
            specific_instance.save()
        
        return instance
    
    def _handle_position_updates(self, instance, validated_data):
        """Smart position handling with additional position features"""
        # Handle position object format: {"position": {"x": 100, "y": 200}}
        if 'position' in validated_data:
            position_data = validated_data['position']
            if isinstance(position_data, dict):
                if 'x' in position_data:
                    instance.position_x = position_data['x']
                if 'y' in position_data:
                    instance.position_y = position_data['y']
        
        # Handle relative position updates: {"move_by": {"x": 50, "y": -30}}
        if 'move_by' in validated_data:
            move_data = validated_data['move_by']
            if isinstance(move_data, dict):
                if 'x' in move_data and instance.position_x is not None:
                    instance.position_x += move_data['x']
                if 'y' in move_data and instance.position_y is not None:
                    instance.position_y += move_data['y']
        
        # Handle position alignment: {"align_to": {"x": 500}} or {"align_to": {"y": 300}}
        if 'align_to' in validated_data:
            align_data = validated_data['align_to']
            if isinstance(align_data, dict):
                if 'x' in align_data:
                    instance.position_x = align_data['x']
                if 'y' in align_data:
                    instance.position_y = align_data['y']
        
        # Handle grid snapping: {"snap_to_grid": True, "grid_size": 25}
        if validated_data.get('snap_to_grid', False):
            grid_size = validated_data.get('grid_size', 20)  # Default grid size 20px
            if instance.position_x is not None:
                instance.position_x = round(instance.position_x / grid_size) * grid_size
            if instance.position_y is not None:
                instance.position_y = round(instance.position_y / grid_size) * grid_size
        
        # Handle position bounds checking
        if 'enforce_bounds' in validated_data:
            bounds = validated_data['enforce_bounds']
            if isinstance(bounds, dict):
                min_x = bounds.get('min_x', 0)
                max_x = bounds.get('max_x', 2000)
                min_y = bounds.get('min_y', 0)
                max_y = bounds.get('max_y', 2000)
                
                if instance.position_x is not None:
                    instance.position_x = max(min_x, min(max_x, instance.position_x))
                if instance.position_y is not None:
                    instance.position_y = max(min_y, min(max_y, instance.position_y))
    
    def _smart_update_specific_fields(self, specific_instance, validated_data):
        """Smart update for node-specific fields with intelligent merging"""
        node_type = specific_instance.__class__.__name__.lower().replace('node', '')
        
        if node_type == 'when':
            self._update_when_node_fields(specific_instance, validated_data)
        elif node_type == 'condition':
            self._update_condition_node_fields(specific_instance, validated_data)
        elif node_type == 'action':
            self._update_action_node_fields(specific_instance, validated_data)
        elif node_type == 'waiting':
            self._update_waiting_node_fields(specific_instance, validated_data)
    
    def _update_when_node_fields(self, instance, validated_data):
        """Smart update for When Node fields"""
        # Direct field updates
        # Accept both schedule_date (alias) and schedule_start_date (model field)
        direct_fields = ['when_type', 'schedule_frequency', 'schedule_start_date', 'schedule_time', 
                        'instagram_post_url', 'instagram_media_type']
        for field in direct_fields:
            if field in validated_data:
                setattr(instance, field, validated_data[field])
        # Map schedule_date -> schedule_start_date if provided
        if 'schedule_date' in validated_data and 'schedule_start_date' not in validated_data:
            instance.schedule_start_date = validated_data['schedule_date']
        
        # Smart array field updates (replace-by-default on PATCH; merge only with explicit flag)
        if 'keywords' in validated_data:
            new_keywords = validated_data['keywords']
            if isinstance(new_keywords, list):
                if getattr(self, 'partial', False) and not validated_data.get('merge_keywords', False):
                    # Replace entirely during PATCH unless merge explicitly requested
                    instance.keywords = new_keywords
                elif validated_data.get('replace_keywords', False):
                    instance.keywords = new_keywords
                else:
                    # Merge with existing keywords (avoid duplicates)
                    existing_keywords = instance.keywords or []
                    merged_keywords = list(set(existing_keywords + new_keywords))
                    instance.keywords = merged_keywords
        
        # Handle comment_keywords (Instagram filter)
        if 'comment_keywords' in validated_data:
            new_keywords = validated_data['comment_keywords']
            if isinstance(new_keywords, list):
                if getattr(self, 'partial', False):
                    # Replace entirely during PATCH
                    instance.comment_keywords = new_keywords
                else:
                    # Merge with existing
                    existing = instance.comment_keywords or []
                    instance.comment_keywords = list(set(existing + new_keywords))
        
        # Handle tags list (When node tag triggers)
        if 'tags' in validated_data:
            new_tags = validated_data['tags']
            if isinstance(new_tags, list):
                if getattr(self, 'partial', False) and not validated_data.get('merge_tags', False):
                    instance.tags = new_tags
                elif validated_data.get('replace_tags', False):
                    instance.tags = new_tags
                else:
                    existing_tags = instance.tags or []
                    merged_tags = list(set(existing_tags + new_tags))
                    instance.tags = merged_tags
        
        if 'channels' in validated_data:
            new_channels = validated_data['channels']
            if isinstance(new_channels, list):
                if getattr(self, 'partial', False) and not validated_data.get('merge_channels', False):
                    instance.channels = new_channels
                elif validated_data.get('replace_channels', False):
                    instance.channels = new_channels
                else:
                    # Merge with existing channels (avoid duplicates)
                    existing_channels = instance.channels or []
                    merged_channels = list(set(existing_channels + new_channels))
                    instance.channels = merged_channels
        
        if 'customer_tags' in validated_data:
            new_tags = validated_data['customer_tags']
            if isinstance(new_tags, list):
                if getattr(self, 'partial', False) and not validated_data.get('merge_customer_tags', False):
                    instance.customer_tags = new_tags
                elif validated_data.get('replace_customer_tags', False):
                    instance.customer_tags = new_tags
                else:
                    # Merge with existing tags (avoid duplicates)
                    existing_tags = instance.customer_tags or []
                    merged_tags = list(set(existing_tags + new_tags))
                    instance.customer_tags = merged_tags
        
        # Special handling for replacing arrays (if needed)
        if 'replace_keywords' in validated_data:
            instance.keywords = validated_data.get('keywords', [])
        if 'replace_tags' in validated_data:
            instance.tags = validated_data.get('tags', [])
        if 'replace_channels' in validated_data:
            instance.channels = validated_data.get('channels', [])
        if 'replace_customer_tags' in validated_data:
            instance.customer_tags = validated_data.get('customer_tags', [])
    
    def _update_condition_node_fields(self, instance, validated_data):
        """Smart update for Condition Node fields"""
        # Direct field updates
        if 'combination_operator' in validated_data:
            instance.combination_operator = validated_data['combination_operator']
        
        # Smart conditions update (replace-by-default on PATCH)
        if 'conditions' in validated_data:
            new_conditions = validated_data['conditions']
            if isinstance(new_conditions, list):
                if (getattr(self, 'partial', False) and not validated_data.get('merge_conditions', False)) or validated_data.get('replace_conditions', False):
                    instance.conditions = new_conditions
                else:
                    # Merge conditions (avoid exact duplicates)
                    existing_conditions = instance.conditions or []
                    for new_condition in new_conditions:
                        # Check if this condition already exists
                        condition_exists = any(
                            existing.get('type') == new_condition.get('type') and
                            existing.get('prompt') == new_condition.get('prompt') and
                            existing.get('operator') == new_condition.get('operator') and
                            existing.get('value') == new_condition.get('value')
                            for existing in existing_conditions
                        )
                        if not condition_exists:
                            existing_conditions.append(new_condition)
                    instance.conditions = existing_conditions
    
    def _update_action_node_fields(self, instance, validated_data):
        """Smart update for Action Node fields"""
        import logging
        logger = logging.getLogger(__name__)
        
        # Handle 'configuration' (and legacy 'config') object from frontend
        # This is now handled in to_internal_value, but keep as fallback
        config_data = None
        if 'configuration' in validated_data:
            config_data = validated_data['configuration']
            logger.info(f"[Serializer] Found configuration in validated_data: {config_data}")
        elif 'config' in validated_data:
            config_data = validated_data['config']
            logger.info(f"[Serializer] Found legacy config in validated_data: {config_data}")
        
        if config_data and isinstance(config_data, dict):
            # Map configuration fields to ActionNode fields
            field_mapping = {
                'dm_mode': 'instagram_dm_mode',
                'dm_text_template': 'instagram_dm_text_template',
                'product_id': 'instagram_product_id',
                'public_reply_enabled': 'instagram_public_reply_enabled',
                'public_reply_template': 'instagram_public_reply_text',
            }
            for config_key, model_field in field_mapping.items():
                if config_key in config_data:
                    validated_data[model_field] = config_data[config_key]
                    logger.info(f"[Serializer] Mapped {config_key}={config_data[config_key]} to {model_field}")
        
        # Direct field updates
        action_fields = [
            'action_type', 'message_content', 'key_values', 'delay_amount', 'delay_unit',
            'redirect_destination', 'tag_name', 'webhook_url', 'webhook_method',
            'webhook_headers', 'webhook_payload', 'email_to', 'email_subject',
            'email_body', 'custom_code',
            # Instagram Comment → DM + Reply fields
            'instagram_dm_mode', 'instagram_dm_text_template', 'instagram_product_id',
            'instagram_public_reply_enabled', 'instagram_public_reply_text'
        ]
        
        for field in action_fields:
            if field in validated_data:
                old_value = getattr(instance, field, None)
                new_value = validated_data[field]
                setattr(instance, field, new_value)
                if field.startswith('instagram_') or field == 'key_values':
                    logger.info(f"[Serializer] Updated {field}: {old_value} -> {new_value}")
        
        # Smart handling for JSON fields
        if 'webhook_headers' in validated_data:
            new_headers = validated_data['webhook_headers']
            if isinstance(new_headers, dict):
                if validated_data.get('replace_webhook_headers', False):
                    instance.webhook_headers = new_headers
                else:
                    # Merge headers
                    existing_headers = instance.webhook_headers or {}
                    existing_headers.update(new_headers)
                    instance.webhook_headers = existing_headers
        
        if 'webhook_payload' in validated_data:
            new_payload = validated_data['webhook_payload']
            if isinstance(new_payload, dict):
                if validated_data.get('replace_webhook_payload', False):
                    instance.webhook_payload = new_payload
                else:
                    # Merge payload
                    existing_payload = instance.webhook_payload or {}
                    existing_payload.update(new_payload)
                    instance.webhook_payload = existing_payload
    
    def _update_waiting_node_fields(self, instance, validated_data):
        """Smart update for Waiting Node fields"""
        # Handle skip_keywords to exit_keywords mapping for frontend compatibility
        request_data = getattr(self, 'initial_data', {})
        if 'skip_keywords' in request_data:
            skip_keywords = request_data.get('skip_keywords', [])
            if skip_keywords:
                # If both skip_keywords and exit_keywords provided, merge them
                if 'exit_keywords' in request_data:
                    explicit_exit_keywords = request_data.get('exit_keywords', [])
                    combined_keywords = list(set(skip_keywords + explicit_exit_keywords))
                    validated_data['exit_keywords'] = combined_keywords
                else:
                    # Only skip_keywords provided, use them as exit_keywords
                    validated_data['exit_keywords'] = skip_keywords
        
        # Direct field updates
        waiting_fields = [
            'storage_type', 'customer_message', 'key_values', 'error_message',
            'allowed_errors', 'response_time_limit_enabled', 'response_timeout_amount',
            'response_timeout_unit', 'response_timeout'
        ]
        
        for field in waiting_fields:
            if field in validated_data:
                setattr(instance, field, validated_data[field])
        
        # Smart array field updates
        if 'choice_options' in validated_data:
            new_options = validated_data['choice_options']
            if isinstance(new_options, list):
                if (getattr(self, 'partial', False) and not validated_data.get('merge_choice_options', False)) or validated_data.get('replace_choice_options', False):
                    instance.choice_options = new_options
                else:
                    # Merge options (avoid duplicates)
                    existing_options = instance.choice_options or []
                    merged_options = existing_options.copy()
                    for option in new_options:
                        if option not in merged_options:
                            merged_options.append(option)
                    instance.choice_options = merged_options
        
        if 'exit_keywords' in validated_data:
            new_keywords = validated_data['exit_keywords']
            if isinstance(new_keywords, list):
                if (getattr(self, 'partial', False) and not validated_data.get('merge_exit_keywords', False)) or validated_data.get('replace_exit_keywords', False):
                    instance.exit_keywords = new_keywords
                else:
                    # Merge keywords (avoid duplicates)
                    existing_keywords = instance.exit_keywords or []
                    merged_keywords = list(set(existing_keywords + new_keywords))
                    instance.exit_keywords = merged_keywords
    
    def to_representation(self, instance):
        """Custom representation based on actual node type"""
        data = super().to_representation(instance)
        
        # Get the actual node instance with specific type
        # Query from DB directly to avoid cache issues
        if hasattr(instance, 'whennode'):
            specific_instance = WhenNode.objects.get(id=instance.whennode.id)
            data.update(WhenNodeSerializer(specific_instance).data)
        elif hasattr(instance, 'conditionnode'):
            specific_instance = ConditionNode.objects.get(id=instance.conditionnode.id)
            data.update(ConditionNodeSerializer(specific_instance).data)
        elif hasattr(instance, 'actionnode'):
            specific_instance = ActionNode.objects.get(id=instance.actionnode.id)
            data.update(ActionNodeSerializer(specific_instance).data)
            
            # Add 'configuration' object for frontend compatibility (Instagram actions)
            if specific_instance.action_type == 'instagram_comment_dm_reply':
                data['configuration'] = {
                    'dm_mode': specific_instance.instagram_dm_mode or 'STATIC',
                    'dm_text_template': specific_instance.instagram_dm_text_template or '',
                    'product_id': str(specific_instance.instagram_product_id) if specific_instance.instagram_product_id else None,
                    'public_reply_enabled': specific_instance.instagram_public_reply_enabled,
                    'public_reply_template': specific_instance.instagram_public_reply_text or '',
                }
        elif hasattr(instance, 'waitingnode'):
            specific_instance = WaitingNode.objects.get(id=instance.waitingnode.id)
            data.update(WaitingNodeSerializer(specific_instance).data)
        
        return data
    
    def to_internal_value(self, data):
        """Handle 'configuration' (and legacy 'config') object before validation"""
        import logging
        logger = logging.getLogger(__name__)
        
        # Make a copy to avoid modifying the original data
        data = data.copy() if hasattr(data, 'copy') else dict(data)
        
        logger.info(f"[to_internal_value] Original data keys: {list(data.keys())}")
        
        # Handle 'configuration' object from frontend (primary name)
        # Also support legacy 'config' for backwards compatibility
        config_data = None
        if 'configuration' in data and isinstance(data['configuration'], dict):
            config_data = data['configuration']
            logger.info(f"[to_internal_value] Found configuration: {config_data}")
        elif 'config' in data and isinstance(data['config'], dict):
            config_data = data['config']
            logger.info(f"[to_internal_value] Found legacy config: {config_data}")
        
        if config_data:
            field_mapping = {
                'dm_mode': 'instagram_dm_mode',
                'dm_text_template': 'instagram_dm_text_template',
                'product_id': 'instagram_product_id',
                'public_reply_enabled': 'instagram_public_reply_enabled',
                'public_reply_template': 'instagram_public_reply_text',
            }
            for config_key, model_field in field_mapping.items():
                if config_key in config_data:
                    data[model_field] = config_data[config_key]
                    logger.info(f"[to_internal_value] Mapped {config_key}={config_data[config_key]} to data.{model_field}")
        
        logger.info(f"[to_internal_value] Final data keys: {list(data.keys())}")
        return super().to_internal_value(data)


# Export/Import Serializers

class WorkflowExportSerializer(serializers.Serializer):
    """
    Serializer for workflow export - returns JSON representation of workflow and all related objects
    """
    def to_representation(self, instance):
        return instance.export_to_dict()


class WorkflowImportSerializer(serializers.Serializer):
    """
    Serializer for workflow import - accepts JSON data and creates new workflow
    """
    name = serializers.CharField(max_length=200, required=False, help_text="Override workflow name")
    workflow_data = serializers.JSONField(help_text="Exported workflow JSON data")
    
    def validate_workflow_data(self, value):
        """Validate the structure of imported workflow data"""
        required_keys = ['workflow', 'export_metadata']
        for key in required_keys:
            if key not in value:
                raise serializers.ValidationError(f"Missing required key: {key}")
        
        # Validate workflow data structure
        workflow_data = value.get('workflow', {})
        if not isinstance(workflow_data, dict):
            raise serializers.ValidationError("Invalid workflow data structure")
        
        return value
    
    def create(self, validated_data):
        workflow_data = validated_data['workflow_data']
        name_override = validated_data.get('name')
        
        # Override name if provided
        if name_override:
            workflow_data['workflow']['name'] = name_override
        
        # Create workflow from imported data
        created_by = self.context.get('request').user if self.context.get('request') else None
        workflow = Workflow.import_from_dict(workflow_data, created_by=created_by)
        
        return workflow
