import uuid
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from django.db import models, transaction
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator

logger = logging.getLogger(__name__)


class EventType(models.Model):
    """
    Defines types of events that can trigger workflows
    """
    CATEGORY_CHOICES = [
        ('user', 'User'),
        ('conversation', 'Conversation'),
        ('message', 'Message'),
        ('system', 'System'),
        ('custom', 'Custom'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200, help_text="Human-readable name")
    code = models.CharField(max_length=100, unique=True, help_text="Unique code for this event type")
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='custom')
    description = models.TextField(blank=True, help_text="Description of when this event is triggered")
    available_fields = models.JSONField(
        default=dict,
        help_text="JSON schema of fields available in event data"
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Event Type"
        verbose_name_plural = "Event Types"
        ordering = ['category', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.code})"


class Trigger(models.Model):
    """
    Defines what events trigger workflows and under what conditions
    """
    TRIGGER_TYPE_CHOICES = [
        ('MESSAGE_RECEIVED', 'Receive Message'),
        ('MESSAGE_SENT', 'Message Sent'),
        ('CONVERSATION_CREATED', 'Conversation Created'),
        ('CONVERSATION_CLOSED', 'Conversation Closed'),
        ('USER_CREATED', 'New Customer'),
        ('USER_UPDATED', 'User Updated'),
        ('TAG_ADDED', 'Add Tag'),
        ('TAG_REMOVED', 'Tag Removed'),
        ('FORM_SUBMITTED', 'Form Submitted'),
        ('SCHEDULED', 'Scheduled'),
        ('WEBHOOK', 'Webhook'),
        ('MANUAL', 'Manual'),
        ('CUSTOM', 'Custom'),
    ]
    
    SCHEDULE_TYPE_CHOICES = [
        ('ONCE', 'Once'),
        ('DAILY', 'Daily'),
        ('WEEKLY', 'Weekly'),
        ('MONTHLY', 'Monthly'),
        ('YEARLY', 'Yearly'),
        ('CUSTOM', 'Custom'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    trigger_type = models.CharField(max_length=30, choices=TRIGGER_TYPE_CHOICES)
    configuration = models.JSONField(
        default=dict,
        help_text="Trigger-specific configuration (e.g., schedule details, webhook settings)"
    )
    filters = models.JSONField(
        default=dict,
        help_text="Conditions that must be met for this trigger to fire"
    )
    schedule_type = models.CharField(
        max_length=20, 
        choices=SCHEDULE_TYPE_CHOICES, 
        null=True, 
        blank=True,
        help_text="For scheduled triggers only"
    )
    next_execution = models.DateTimeField(
        null=True, 
        blank=True,
        help_text="When this trigger should next execute (for scheduled triggers)"
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Trigger"
        verbose_name_plural = "Triggers"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} ({self.trigger_type})"


class Condition(models.Model):
    """
    Defines logical conditions that can be evaluated against event data
    """
    OPERATOR_CHOICES = [
        ('and', 'AND'),
        ('or', 'OR'),
    ]
    
    CONDITION_TYPE_CHOICES = [
        ('message', 'Message Condition'),
        ('ai', 'AI Condition'),
        ('user', 'User Condition'),
        ('tag', 'Tag Condition'),
        ('time', 'Time Condition'),
        ('custom', 'Custom Condition'),
    ]
    
    MESSAGE_OPERATOR_CHOICES = [
        ('equals', 'Equals To'),
        ('not_equals', 'Not Equal'),
        ('starts_with', 'Start With'),
        ('ends_with', 'End With'),
        ('contains', 'Contains'),
        ('not_contains', 'Not Contains'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    operator = models.CharField(max_length=5, choices=OPERATOR_CHOICES, default='and')
    conditions = models.JSONField(
        default=list,
        help_text="Array of condition rules in JSON format"
    )
    use_custom_code = models.BooleanField(default=False)
    custom_code = models.TextField(
        blank=True,
        help_text="Custom Python code for complex conditions (executed in sandbox)"
    )
    # AI condition fields
    ai_prompt = models.TextField(
        blank=True,
        help_text="AI prompt for AI-based condition evaluation"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Condition"
        verbose_name_plural = "Conditions"
        ordering = ['name']
    
    def __str__(self):
        return self.name


class Action(models.Model):
    """
    Defines actions that can be executed as part of workflows
    """
    ACTION_TYPE_CHOICES = [
        ('send_message', 'Send Message'),
        ('update_user', 'Update User'),
        ('add_tag', 'Add Tag'),
        ('remove_tag', 'Remove Tag'),
        ('send_email', 'Send Email'),
        ('add_note', 'Add Note'),
        ('webhook', 'Webhook'),
        ('delay', 'Delay'),
        ('redirect_conversation', 'Redirect Conversation'),
        ('transfer_to_human', 'Transfer to Human'),
        ('custom_code', 'Custom Code'),
        ('set_conversation_status', 'Set Conversation Status'),
        ('control_ai_response', 'Control AI Response'),
        ('update_ai_context', 'Update AI Context'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    action_type = models.CharField(max_length=30, choices=ACTION_TYPE_CHOICES)
    configuration = models.JSONField(
        default=dict,
        help_text="Action-specific configuration (templates, settings, etc.)"
    )
    is_active = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0, help_text="Order of execution within workflow")
    delay = models.PositiveIntegerField(
        default=0,
        help_text="Delay in seconds before executing this action"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Action"
        verbose_name_plural = "Actions"
        ordering = ['order', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.action_type})"


class ActionTemplate(models.Model):
    """
    Pre-defined action templates for common use cases
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    action_type = models.CharField(max_length=30, choices=Action.ACTION_TYPE_CHOICES)
    configuration = models.JSONField(
        default=dict,
        help_text="Template configuration with placeholders"
    )
    use_custom_code = models.BooleanField(default=False)
    custom_code = models.TextField(blank=True)
    category = models.CharField(max_length=100, blank=True)
    is_featured = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Action Template"
        verbose_name_plural = "Action Templates"
        ordering = ['-is_featured', 'category', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.action_type})"


class Workflow(models.Model):
    """
    Main workflow definition combining triggers, conditions, and actions
    """
    STATUS_CHOICES = [
        ('DRAFT', 'Draft'),
        ('ACTIVE', 'Active'),
        ('PAUSED', 'Paused'),
        ('ARCHIVED', 'Archived'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='DRAFT')
    ui_settings = models.JSONField(
        default=dict,
        help_text="UI layout and visual settings for workflow editor"
    )
    edges = models.JSONField(
        default=list,
        help_text="Visual connections between workflow elements"
    )
    max_executions = models.PositiveIntegerField(
        default=0,
        help_text="Maximum executions per user (0 = unlimited)"
    )
    delay_between_executions = models.PositiveIntegerField(
        default=0,
        help_text="Minimum seconds between executions for same user"
    )
    start_date = models.DateTimeField(null=True, blank=True)
    end_date = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(
        get_user_model(),
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_workflows'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Workflow"
        verbose_name_plural = "Workflows"
        ordering = ['-updated_at']
    
    def __str__(self):
        return f"{self.name} ({self.status})"
    
    def is_active(self) -> bool:
        """Check if workflow is currently active and within date range"""
        if self.status != 'ACTIVE':
            return False
        
        now = timezone.now()
        if self.start_date and now < self.start_date:
            return False
        if self.end_date and now > self.end_date:
            return False
        
        return True
    
    def export_to_dict(self) -> Dict[str, Any]:
        """
        Export workflow and all related objects to a dictionary.
        This includes nodes, connections, triggers, actions, conditions, etc.
        """
        workflow_data = {
            'workflow': {
                'name': self.name,
                'description': self.description,
                'status': 'DRAFT',  # Always import as draft
                'ui_settings': self.ui_settings,
                'edges': self.edges,
                'max_executions': self.max_executions,
                'delay_between_executions': self.delay_between_executions,
                'start_date': self.start_date.isoformat() if self.start_date else None,
                'end_date': self.end_date.isoformat() if self.end_date else None,
            },
            'nodes': [],
            'connections': [],
            'triggers': [],
            'actions': [],
            'conditions': [],
            'trigger_associations': [],
            'workflow_actions': [],
            'export_metadata': {
                'exported_at': timezone.now().isoformat(),
                'original_workflow_id': str(self.id),
                'version': '1.0'
            }
        }
        
        # Export workflow nodes
        for node in self.nodes.all():
            node_data = {
                'id': str(node.id),
                'node_type': node.node_type,
                'title': node.title,
                'position_x': node.position_x,
                'position_y': node.position_y,
                'configuration': node.configuration,
                'is_active': node.is_active,
            }
            
            # Add specific node type data
            if hasattr(node, 'whennode'):
                when_node = node.whennode
                node_data.update({
                    'when_type': when_node.when_type,
                    'keywords': when_node.keywords,
                    'tags': when_node.tags,
                    'channels': when_node.channels,
                    'schedule_frequency': when_node.schedule_frequency,
                    'schedule_start_date': when_node.schedule_start_date.isoformat() if when_node.schedule_start_date else None,
                    'schedule_time': when_node.schedule_time.isoformat() if when_node.schedule_time else None,
                })
            elif hasattr(node, 'conditionnode'):
                condition_node = node.conditionnode
                node_data.update({
                    'combination_operator': condition_node.combination_operator,
                    'conditions': condition_node.conditions,
                })
            elif hasattr(node, 'actionnode'):
                action_node = node.actionnode
                node_data.update({
                    'action_type': action_node.action_type,
                    'message_content': action_node.message_content,
                    'delay_amount': action_node.delay_amount,
                    'delay_unit': action_node.delay_unit,
                    'redirect_destination': action_node.redirect_destination,
                    'tag_name': action_node.tag_name,
                    'webhook_url': action_node.webhook_url,
                    'webhook_method': action_node.webhook_method,
                    'webhook_headers': action_node.webhook_headers,
                    'webhook_payload': action_node.webhook_payload,
                    'custom_code': action_node.custom_code,
                    'ai_control_action': action_node.ai_control_action,
                    'ai_custom_prompt': action_node.ai_custom_prompt,
                    'ai_context_data': action_node.ai_context_data,
                })
            elif hasattr(node, 'waitingnode'):
                waiting_node = node.waitingnode
                node_data.update({
                    'storage_type': waiting_node.storage_type,
                    'customer_message': waiting_node.customer_message,
                    'error_message': waiting_node.error_message,
                    'choice_options': waiting_node.choice_options,
                    'allowed_errors': waiting_node.allowed_errors,
                    'exit_keywords': waiting_node.exit_keywords,
                    'response_time_limit_enabled': waiting_node.response_time_limit_enabled,
                    'response_timeout_amount': waiting_node.response_timeout_amount,
                    'response_timeout_unit': waiting_node.response_timeout_unit,
                    'response_timeout': waiting_node.response_timeout,
                })
            
            workflow_data['nodes'].append(node_data)
        
        # Export node connections
        for connection in self.connections.all():
            connection_data = {
                'id': str(connection.id),
                'source_node_id': str(connection.source_node.id),
                'target_node_id': str(connection.target_node.id),
                'connection_type': connection.connection_type,
                'condition': connection.condition,
            }
            workflow_data['connections'].append(connection_data)
        
        # Export legacy triggers
        for trigger_assoc in self.trigger_associations.all():
            trigger = trigger_assoc.trigger
            trigger_data = {
                'id': str(trigger.id),
                'name': trigger.name,
                'description': trigger.description,
                'trigger_type': trigger.trigger_type,
                'configuration': trigger.configuration,
                'filters': trigger.filters,
                'schedule_type': trigger.schedule_type,
                'is_active': trigger.is_active,
            }
            workflow_data['triggers'].append(trigger_data)
            
            # Export trigger association
            assoc_data = {
                'trigger_id': str(trigger.id),
                'specific_conditions': trigger_assoc.specific_conditions,
                'priority': trigger_assoc.priority,
                'is_active': trigger_assoc.is_active,
            }
            workflow_data['trigger_associations'].append(assoc_data)
        
        # Export legacy actions
        for workflow_action in self.workflow_actions.all():
            action = workflow_action.action
            action_data = {
                'id': str(action.id),
                'name': action.name,
                'description': action.description,
                'action_type': action.action_type,
                'configuration': action.configuration,
                'is_active': action.is_active,
                'order': action.order,
                'delay': action.delay,
            }
            workflow_data['actions'].append(action_data)
            
            # Export workflow action association
            workflow_action_data = {
                'action_id': str(action.id),
                'order': workflow_action.order,
                'is_required': workflow_action.is_required,
                'add_result_to_context': workflow_action.add_result_to_context,
                'condition_id': str(workflow_action.condition.id) if workflow_action.condition else None,
            }
            workflow_data['workflow_actions'].append(workflow_action_data)
        
        # Export legacy conditions
        condition_ids = set()
        for workflow_action in self.workflow_actions.all():
            if workflow_action.condition:
                condition_ids.add(workflow_action.condition.id)
        
        for condition_id in condition_ids:
            try:
                condition = Condition.objects.get(id=condition_id)
                condition_data = {
                    'id': str(condition.id),
                    'name': condition.name,
                    'description': condition.description,
                    'operator': condition.operator,
                    'conditions': condition.conditions,
                    'use_custom_code': condition.use_custom_code,
                    'custom_code': condition.custom_code,
                    'ai_prompt': condition.ai_prompt,
                }
                workflow_data['conditions'].append(condition_data)
            except Condition.DoesNotExist:
                continue
        
        return workflow_data
    
    @classmethod
    def import_from_dict(cls, data: Dict[str, Any], created_by=None) -> 'Workflow':
        """
        Import workflow from exported dictionary data.
        Creates new objects with new primary keys while maintaining relationships.
        """
        with transaction.atomic():
            # Create new workflow
            workflow_data = data.get('workflow', {})
            
            # Handle date fields - convert empty strings to None
            start_date = workflow_data.get('start_date')
            end_date = workflow_data.get('end_date')
            
            # Convert empty strings to None for date fields
            if start_date == '':
                start_date = None
            if end_date == '':
                end_date = None
            
            workflow = cls.objects.create(
                name=workflow_data.get('name', 'Imported Workflow'),
                description=workflow_data.get('description', ''),
                status=workflow_data.get('status', 'DRAFT'),
                ui_settings=workflow_data.get('ui_settings', {}),
                edges=workflow_data.get('edges', []),
                max_executions=workflow_data.get('max_executions', 0),
                delay_between_executions=workflow_data.get('delay_between_executions', 0),
                start_date=start_date,
                end_date=end_date,
                created_by=created_by
            )
            
            # Map old IDs to new objects for relationship maintenance
            node_id_mapping = {}
            trigger_id_mapping = {}
            action_id_mapping = {}
            condition_id_mapping = {}
            
            # Import conditions first (as they may be referenced by workflow actions)
            for condition_data in data.get('conditions', []):
                old_id = condition_data.pop('id')
                condition = Condition.objects.create(**condition_data)
                condition_id_mapping[old_id] = condition
            
            # Import triggers
            for trigger_data in data.get('triggers', []):
                old_id = trigger_data.pop('id')
                trigger = Trigger.objects.create(**trigger_data)
                trigger_id_mapping[old_id] = trigger
            
            # Import actions
            for action_data in data.get('actions', []):
                old_id = action_data.pop('id')
                action = Action.objects.create(**action_data)
                action_id_mapping[old_id] = action
            
            # Import workflow nodes
            for node_data in data.get('nodes', []):
                old_id = node_data.pop('id')
                node_type = node_data.pop('node_type')
                
                # Create base workflow node
                base_node_data = {
                    'workflow': workflow,
                    'node_type': node_type,
                    'title': node_data.get('title', ''),
                    'position_x': node_data.get('position_x', 0),
                    'position_y': node_data.get('position_y', 0),
                    'configuration': node_data.get('configuration', {}),
                    'is_active': node_data.get('is_active', True),
                }
                
                # Create specific node type
                if node_type == 'when':
                    # Handle date/time fields - convert empty strings to None
                    schedule_start_date = node_data.get('schedule_start_date')
                    schedule_time = node_data.get('schedule_time')
                    if schedule_start_date == '':
                        schedule_start_date = None
                    if schedule_time == '':
                        schedule_time = None
                    
                    node = WhenNode.objects.create(
                        **base_node_data,
                        when_type=node_data.get('when_type', 'receive_message'),
                        keywords=node_data.get('keywords', []),
                        tags=node_data.get('tags', []),
                        channels=node_data.get('channels', []),
                        schedule_frequency=node_data.get('schedule_frequency'),
                        schedule_start_date=schedule_start_date,
                        schedule_time=schedule_time,
                    )
                elif node_type == 'condition':
                    node = ConditionNode.objects.create(
                        **base_node_data,
                        combination_operator=node_data.get('combination_operator', 'or'),
                        conditions=node_data.get('conditions', []),
                    )
                elif node_type == 'action':
                    node = ActionNode.objects.create(
                        **base_node_data,
                        action_type=node_data.get('action_type', 'send_message'),
                        message_content=node_data.get('message_content', ''),
                        delay_amount=node_data.get('delay_amount', 0),
                        delay_unit=node_data.get('delay_unit', 'minutes'),
                        redirect_destination=node_data.get('redirect_destination', ''),
                        tag_name=node_data.get('tag_name', ''),
                        webhook_url=node_data.get('webhook_url', ''),
                        webhook_method=node_data.get('webhook_method', 'POST'),
                        webhook_headers=node_data.get('webhook_headers', {}),
                        webhook_payload=node_data.get('webhook_payload', {}),
                        custom_code=node_data.get('custom_code', ''),
                        ai_control_action=node_data.get('ai_control_action', ''),
                        ai_custom_prompt=node_data.get('ai_custom_prompt', ''),
                        ai_context_data=node_data.get('ai_context_data', {}),
                    )
                elif node_type == 'waiting':
                    node = WaitingNode.objects.create(
                        **base_node_data,
                        storage_type=node_data.get('storage_type', 'text'),
                        customer_message=node_data.get('customer_message', ''),
                        error_message=node_data.get('error_message', ''),
                        choice_options=node_data.get('choice_options', []),
                        allowed_errors=node_data.get('allowed_errors', 3),
                        exit_keywords=node_data.get('exit_keywords', []),
                        response_time_limit_enabled=node_data.get('response_time_limit_enabled', True),
                        response_timeout_amount=node_data.get('response_timeout_amount', 30),
                        response_timeout_unit=node_data.get('response_timeout_unit', 'minutes'),
                        response_timeout=node_data.get('response_timeout', 3600),
                    )
                else:
                    # Fallback to base WorkflowNode
                    node = WorkflowNode.objects.create(**base_node_data)
                
                node_id_mapping[old_id] = node
            
            # Import node connections
            for connection_data in data.get('connections', []):
                source_node_id = connection_data.get('source_node_id')
                target_node_id = connection_data.get('target_node_id')
                
                if source_node_id in node_id_mapping and target_node_id in node_id_mapping:
                    NodeConnection.objects.create(
                        workflow=workflow,
                        source_node=node_id_mapping[source_node_id],
                        target_node=node_id_mapping[target_node_id],
                        connection_type=connection_data.get('connection_type', 'success'),
                        condition=connection_data.get('condition', {}),
                    )
            
            # Import trigger associations
            for trigger_assoc_data in data.get('trigger_associations', []):
                trigger_id = trigger_assoc_data.get('trigger_id')
                if trigger_id in trigger_id_mapping:
                    TriggerWorkflowAssociation.objects.create(
                        trigger=trigger_id_mapping[trigger_id],
                        workflow=workflow,
                        specific_conditions=trigger_assoc_data.get('specific_conditions', {}),
                        priority=trigger_assoc_data.get('priority', 100),
                        is_active=trigger_assoc_data.get('is_active', True),
                    )
            
            # Import workflow actions
            for workflow_action_data in data.get('workflow_actions', []):
                action_id = workflow_action_data.get('action_id')
                condition_id = workflow_action_data.get('condition_id')
                
                if action_id in action_id_mapping:
                    condition = condition_id_mapping.get(condition_id) if condition_id else None
                    WorkflowAction.objects.create(
                        workflow=workflow,
                        action=action_id_mapping[action_id],
                        order=workflow_action_data.get('order', 0),
                        is_required=workflow_action_data.get('is_required', True),
                        add_result_to_context=workflow_action_data.get('add_result_to_context', False),
                        condition=condition,
                    )
            
            return workflow


class TriggerWorkflowAssociation(models.Model):
    """
    Associates triggers with workflows with specific conditions and priority
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    trigger = models.ForeignKey(Trigger, on_delete=models.CASCADE, related_name='workflow_associations')
    workflow = models.ForeignKey(Workflow, on_delete=models.CASCADE, related_name='trigger_associations')
    specific_conditions = models.JSONField(
        default=dict,
        help_text="Additional conditions specific to this trigger-workflow association"
    )
    priority = models.PositiveIntegerField(
        default=100,
        help_text="Execution priority (lower numbers execute first)"
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('trigger', 'workflow')
        verbose_name = "Trigger-Workflow Association"
        verbose_name_plural = "Trigger-Workflow Associations"
        ordering = ['priority', '-created_at']
    
    def __str__(self):
        return f"{self.trigger.name} → {self.workflow.name} (Priority: {self.priority})"


class WorkflowAction(models.Model):
    """
    Associates actions with workflows in a specific order with conditions
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workflow = models.ForeignKey(Workflow, on_delete=models.CASCADE, related_name='workflow_actions')
    action = models.ForeignKey(Action, on_delete=models.CASCADE, related_name='workflow_associations')
    order = models.PositiveIntegerField(help_text="Execution order within workflow")
    is_required = models.BooleanField(
        default=True,
        help_text="Whether workflow should fail if this action fails"
    )
    add_result_to_context = models.BooleanField(
        default=False,
        help_text="Whether to add action result to workflow context for later actions"
    )
    condition = models.ForeignKey(
        Condition,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Optional condition that must be true for this action to execute"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('workflow', 'action')
        verbose_name = "Workflow Action"
        verbose_name_plural = "Workflow Actions"
        ordering = ['workflow', 'order']
    
    def __str__(self):
        return f"{self.workflow.name} - {self.action.name} (Order: {self.order})"


class WorkflowExecution(models.Model):
    """
    Tracks individual workflow executions
    """
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('RUNNING', 'Running'),
        ('COMPLETED', 'Completed'),
        ('FAILED', 'Failed'),
        ('TIMED_OUT', 'Timed Out'),
        ('WAITING', 'Waiting'),
    ]
    
    id = models.AutoField(primary_key=True)
    workflow = models.ForeignKey(Workflow, on_delete=models.CASCADE, related_name='executions')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    user = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        help_text="User ID (Customer ID) this execution is for"
    )
    conversation = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        help_text="Conversation ID this execution is related to"
    )
    trigger_data = models.JSONField(
        default=dict,
        help_text="Original trigger data that started this execution"
    )
    context_data = models.JSONField(
        default=dict,
        help_text="Runtime context data available to actions"
    )
    result_data = models.JSONField(
        default=dict,
        help_text="Final execution results"
    )
    error_message = models.TextField(blank=True)
    error_details = models.JSONField(default=dict)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Workflow Execution"
        verbose_name_plural = "Workflow Executions"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['workflow', 'status']),
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['conversation', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.workflow.name} execution #{self.id} ({self.status})"
    
    @property
    def duration(self) -> Optional[timedelta]:
        """Calculate execution duration"""
        if self.started_at and self.completed_at:
            return self.completed_at - self.started_at
        return None


class WorkflowActionExecution(models.Model):
    """
    Tracks individual action executions within a workflow
    """
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('RUNNING', 'Running'),
        ('COMPLETED', 'Completed'),
        ('FAILED', 'Failed'),
        ('SKIPPED', 'Skipped'),
        ('WAITING', 'Waiting'),
    ]
    
    id = models.AutoField(primary_key=True)
    workflow_execution = models.ForeignKey(
        WorkflowExecution,
        on_delete=models.CASCADE,
        related_name='action_executions'
    )
    workflow_action = models.ForeignKey(
        WorkflowAction,
        on_delete=models.CASCADE,
        related_name='executions'
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    queued_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    input_data = models.JSONField(default=dict)
    result_data = models.JSONField(default=dict)
    error_message = models.TextField(blank=True)
    error_details = models.JSONField(default=dict)
    retry_count = models.PositiveIntegerField(default=0)
    max_retries = models.PositiveIntegerField(default=3)
    next_retry_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = "Workflow Action Execution"
        verbose_name_plural = "Workflow Action Executions"
        ordering = ['workflow_execution', 'workflow_action__order']
        indexes = [
            models.Index(fields=['workflow_execution', 'status']),
            models.Index(fields=['status', 'next_retry_at']),
        ]
    
    def __str__(self):
        return f"Execution #{self.workflow_execution.id} - {self.workflow_action.action.name} ({self.status})"
    
    @property
    def duration(self) -> Optional[timedelta]:
        """Calculate action execution duration"""
        if self.started_at and self.completed_at:
            return self.completed_at - self.started_at
        return None


class TriggerEventLog(models.Model):
    """
    Logs all trigger events for auditing and debugging
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event_type = models.CharField(max_length=100)
    event_data = models.JSONField(default=dict)
    user_id = models.CharField(max_length=100, null=True, blank=True)
    conversation_id = models.CharField(max_length=100, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Trigger Event Log"
        verbose_name_plural = "Trigger Event Logs"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['event_type', 'created_at']),
            models.Index(fields=['user_id', 'created_at']),
            models.Index(fields=['conversation_id', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.event_type} - {self.created_at.strftime('%Y-%m-%d %H:%M:%S')}"


class ActionLog(models.Model):
    """
    Detailed logs for action executions
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    action = models.ForeignKey(Action, on_delete=models.CASCADE, related_name='logs')
    executed_at = models.DateTimeField(auto_now_add=True)
    duration = models.FloatField(help_text="Execution duration in seconds")
    context = models.JSONField(default=dict)
    result = models.JSONField(default=dict)
    success = models.BooleanField(default=True)
    error_message = models.TextField(blank=True)
    
    class Meta:
        verbose_name = "Action Log"
        verbose_name_plural = "Action Logs"
        ordering = ['-executed_at']
        indexes = [
            models.Index(fields=['action', 'executed_at']),
            models.Index(fields=['success', 'executed_at']),
        ]
    
    def __str__(self):
        status = "SUCCESS" if self.success else "FAILED"
        return f"{self.action.name} - {status} - {self.executed_at.strftime('%Y-%m-%d %H:%M:%S')}"


# New Node-Based Workflow Models

class WorkflowNode(models.Model):
    """
    Base model for workflow nodes (When, Condition, Action, Waiting)
    """
    NODE_TYPE_CHOICES = [
        ('when', 'When'),
        ('condition', 'Condition'),
        ('action', 'Action'),
        ('waiting', 'Waiting'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workflow = models.ForeignKey(Workflow, on_delete=models.CASCADE, related_name='nodes')
    node_type = models.CharField(max_length=20, choices=NODE_TYPE_CHOICES)
    title = models.CharField(max_length=200, help_text="Node title")
    position_x = models.FloatField(default=0, help_text="X position in visual editor")
    position_y = models.FloatField(default=0, help_text="Y position in visual editor")
    configuration = models.JSONField(default=dict, help_text="Node-specific configuration")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Workflow Node"
        verbose_name_plural = "Workflow Nodes"
        ordering = ['workflow', 'node_type', 'created_at']
        indexes = [
            models.Index(fields=['workflow', 'node_type']),
            models.Index(fields=['workflow', 'is_active']),
        ]
    
    def __str__(self):
        return f"{self.workflow.name} - {self.get_node_type_display()}: {self.title}"


class WhenNode(WorkflowNode):
    """
    When node - defines workflow triggers (start points)
    """
    WHEN_TYPE_CHOICES = [
        ('receive_message', 'Receive Message'),
        ('add_tag', 'Add Tag'),
        ('new_customer', 'New Customer'),
        ('scheduled', 'Scheduled'),
    ]
    
    SCHEDULE_FREQUENCY_CHOICES = [
        ('once', 'Once'),
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('yearly', 'Yearly'),
    ]
    
    when_type = models.CharField(max_length=30, choices=WHEN_TYPE_CHOICES)
    keywords = models.JSONField(default=list, blank=True, help_text="Keywords for message triggers")
    tags = models.JSONField(default=list, blank=True, help_text="Tags for tag triggers - filters customers by these tags")
    channels = models.JSONField(default=list, blank=True, help_text="Channels to monitor (instagram, telegram, all)")
    
    # Scheduling fields
    schedule_frequency = models.CharField(
        max_length=20, 
        choices=SCHEDULE_FREQUENCY_CHOICES, 
        null=True, 
        blank=True
    )
    schedule_start_date = models.DateField(null=True, blank=True)
    schedule_time = models.TimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = "When Node"
        verbose_name_plural = "When Nodes"
    
    def save(self, *args, **kwargs):
        self.node_type = 'when'
        # Ensure JSONField lists are never None
        if self.keywords is None:
            self.keywords = []
        if self.tags is None:
            self.tags = []
        if self.channels is None:
            self.channels = []
        super().save(*args, **kwargs)


class ConditionNode(WorkflowNode):
    """
    Condition node - defines logical conditions to check
    """
    OPERATOR_CHOICES = [
        ('and', 'AND'),
        ('or', 'OR'),
    ]
    
    CONDITION_TYPE_CHOICES = [
        ('ai', 'AI Condition'),
        ('message', 'Message Condition'),
    ]
    
    MESSAGE_OPERATOR_CHOICES = [
        ('equals_to', 'Equals to (=)'),
        ('not_equal', 'Not equal (≠)'),
        ('start_with', 'Start with'),
        ('end_with', 'End with'),
        ('contains', 'Contains'),
    ]
    
    # ترکیب شرط‌ها (AND/OR)
    combination_operator = models.CharField(
        max_length=5, 
        choices=OPERATOR_CHOICES, 
        default='or',
        help_text="How to combine multiple conditions (AND/OR)"
    )
    
    # لیست شرط‌ها - هر شرط شامل type, prompt/operator/value
    conditions = models.JSONField(
        default=list, 
        help_text="List of conditions - each with type, and specific fields based on type"
    )
    
    class Meta:
        verbose_name = "Condition Node"
        verbose_name_plural = "Condition Nodes"
    
    def save(self, *args, **kwargs):
        self.node_type = 'condition'
        super().save(*args, **kwargs)


class ActionNode(WorkflowNode):
    """
    Action node - defines actions to execute
    """
    ACTION_TYPE_CHOICES = [
        ('send_message', 'Send Message'),
        ('delay', 'Delay'),
        ('redirect_conversation', 'Redirect Conversation'),
        ('add_tag', 'Add Tag'),
        ('remove_tag', 'Remove Tag'),
        ('transfer_to_human', 'Transfer to Human'),
        ('send_email', 'Send Email'),
        ('webhook', 'Webhook'),
        ('custom_code', 'Custom Code'),
        ('control_ai_response', 'Control AI Response'),
        ('update_ai_context', 'Update AI Context'),
    ]
    
    REDIRECT_DESTINATIONS = [
        ('ai', 'AI Assistant'),
        ('support', 'Support'),
        ('sales', 'Sales'),
        ('technical', 'Technical'),
        ('billing', 'Billing'),
        ('general', 'General'),
    ]
    
    action_type = models.CharField(max_length=30, choices=ACTION_TYPE_CHOICES)
    message_content = models.TextField(blank=True, help_text="Message content for send_message action")
    delay_amount = models.PositiveIntegerField(default=0, help_text="Delay amount")
    delay_unit = models.CharField(
        max_length=10, 
        choices=[('seconds', 'Seconds'), ('minutes', 'Minutes'), ('hours', 'Hours'), ('days', 'Days')],
        default='minutes'
    )
    redirect_destination = models.CharField(
        max_length=20, 
        choices=REDIRECT_DESTINATIONS, 
        blank=True,
        help_text="Destination for conversation redirect"
    )
    tag_name = models.CharField(max_length=100, blank=True, help_text="Tag name for add/remove tag actions")
    webhook_url = models.URLField(blank=True, help_text="Webhook URL")
    webhook_method = models.CharField(
        max_length=10, 
        choices=[('GET', 'GET'), ('POST', 'POST'), ('PUT', 'PUT'), ('DELETE', 'DELETE')],
        default='POST'
    )
    webhook_headers = models.JSONField(default=dict, help_text="Webhook headers")
    webhook_payload = models.JSONField(default=dict, help_text="Webhook payload")
    custom_code = models.TextField(blank=True, help_text="Custom code to execute")
    
    # AI Control fields
    ai_control_action = models.CharField(
        max_length=20, 
        choices=[
            ('disable', 'Disable AI'),
            ('enable', 'Enable AI'),
            ('custom_prompt', 'Set Custom Prompt'),
            ('reset_context', 'Reset AI Context')
        ],
        blank=True,
        help_text="AI control action type"
    )
    ai_custom_prompt = models.TextField(blank=True, help_text="Custom AI prompt for this conversation")
    ai_context_data = models.JSONField(default=dict, help_text="Additional context data for AI")
    
    class Meta:
        verbose_name = "Action Node"
        verbose_name_plural = "Action Nodes"
    
    def save(self, *args, **kwargs):
        self.node_type = 'action'
        super().save(*args, **kwargs)


class WaitingNode(WorkflowNode):
    """
    Waiting node - waits for user response
    """
    ANSWER_TYPE_CHOICES = [
        ('text', 'Text'),
        ('number', 'Number'),
        ('email', 'Email'),
        ('phone', 'Phone'),
        ('date', 'Date'),
        ('choice', 'Choice Answer'),
    ]
    
    STORAGE_TYPE_CHOICES = [
        ('text', 'Text'),
        ('email', 'Email'),
        ('phone', 'Phone'),
    ]
    
    TIME_UNIT_CHOICES = [
        ('seconds', 'Seconds'),
        ('minutes', 'Minutes'),
        ('hours', 'Hours'),
        ('days', 'Days'),
    ]
    
    # answer_type = models.CharField(max_length=20, choices=ANSWER_TYPE_CHOICES)
    storage_type = models.CharField(max_length=20, choices=STORAGE_TYPE_CHOICES, default='text')
    # storage_field = models.CharField(max_length=100, blank=True, help_text="Field name to store answer")
    customer_message = models.TextField(help_text="Message sent to customer requesting response")
    error_message = models.TextField(
        blank=True,
        default="",
        help_text="Custom error message to send when validation fails. If empty, default error messages will be used."
    )
    choice_options = models.JSONField(default=list, help_text="Options for choice answer type")
    allowed_errors = models.PositiveIntegerField(default=3, help_text="Number of allowed user errors")
    exit_keywords = models.JSONField(default=list, help_text="Keywords that exit this step unsuccessfully")
    
    # Response time limit with toggle
    response_time_limit_enabled = models.BooleanField(default=True, help_text="Enable response time limit")
    response_timeout_amount = models.PositiveIntegerField(
        default=30, 
        help_text="Response timeout amount"
    )
    response_timeout_unit = models.CharField(
        max_length=10,
        choices=TIME_UNIT_CHOICES,
        default='minutes',
        help_text="Response timeout unit"
    )
    
    # Legacy field for backward compatibility
    response_timeout = models.PositiveIntegerField(
        default=3600, 
        help_text="Response timeout in seconds (legacy field)"
    )
    
    class Meta:
        verbose_name = "Waiting Node"
        verbose_name_plural = "Waiting Nodes"
    
    def save(self, *args, **kwargs):
        self.node_type = 'waiting'
        super().save(*args, **kwargs)



class NodeConnection(models.Model):
    """
    Defines connections between workflow nodes
    """
    CONNECTION_TYPE_CHOICES = [
        ('success', 'Success'),
        ('failure', 'Failure'),
        ('timeout', 'Timeout'),
        ('skip', 'Skip'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workflow = models.ForeignKey(Workflow, on_delete=models.CASCADE, related_name='connections')
    source_node = models.ForeignKey(WorkflowNode, on_delete=models.CASCADE, related_name='outgoing_connections')
    target_node = models.ForeignKey(WorkflowNode, on_delete=models.CASCADE, related_name='incoming_connections')
    connection_type = models.CharField(max_length=20, choices=CONNECTION_TYPE_CHOICES, default='success')
    condition = models.JSONField(default=dict, help_text="Optional condition for this connection")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Node Connection"
        verbose_name_plural = "Node Connections"
        unique_together = ('source_node', 'target_node', 'connection_type')
        indexes = [
            models.Index(fields=['workflow', 'source_node']),
            models.Index(fields=['workflow', 'target_node']),
        ]
    
    def __str__(self):
        return f"{self.source_node.title} → {self.target_node.title} ({self.connection_type})"



class UserResponse(models.Model):
    """
    Stores user responses to waiting nodes
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    waiting_node = models.ForeignKey(WaitingNode, on_delete=models.CASCADE, related_name='responses')
    workflow_execution = models.ForeignKey(WorkflowExecution, on_delete=models.CASCADE, related_name='user_responses')
    user_id = models.CharField(max_length=100, help_text="Customer ID")
    conversation_id = models.CharField(max_length=100, help_text="Conversation ID")
    response_value = models.TextField(help_text="User's response")
    is_valid = models.BooleanField(default=True)
    error_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = "User Response"
        verbose_name_plural = "User Responses"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user_id', 'created_at']),
            models.Index(fields=['conversation_id', 'created_at']),
            models.Index(fields=['waiting_node', 'workflow_execution']),
        ]
    
    def __str__(self):
        return f"Response to {self.waiting_node.title} from {self.user_id}"