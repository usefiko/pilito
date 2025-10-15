"""
Workflow debugging utilities
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta

from django.utils import timezone
from django.db import models

from workflow.models import (
    Workflow, Trigger, TriggerWorkflowAssociation, WorkflowAction, Action,
    TriggerEventLog, WorkflowExecution, WorkflowActionExecution
)
from workflow.services.trigger_service import TriggerService
from workflow.utils.condition_evaluator import build_context_from_event_log, evaluate_conditions

logger = logging.getLogger(__name__)


class WorkflowDebugger:
    """
    Utility class for debugging workflow execution issues
    """
    
    @staticmethod
    def check_workflow_setup() -> Dict[str, Any]:
        """
        Check if workflows are properly set up for execution
        """
        results = {
            'total_workflows': Workflow.objects.count(),
            'active_workflows': Workflow.objects.filter(status='ACTIVE').count(),
            'total_triggers': Trigger.objects.count(),
            'active_triggers': Trigger.objects.filter(is_active=True).count(),
            'total_actions': Action.objects.count(),
            'active_actions': Action.objects.filter(is_active=True).count(),
            'trigger_workflow_associations': TriggerWorkflowAssociation.objects.filter(is_active=True).count(),
            'workflow_actions': WorkflowAction.objects.count(),
            'issues': [],
            'recommendations': []
        }
        
        # Check for common issues
        if results['active_workflows'] == 0:
            results['issues'].append("No active workflows found")
            results['recommendations'].append("Create workflows and set their status to 'ACTIVE'")
        
        if results['active_triggers'] == 0:
            results['issues'].append("No active triggers found")
            results['recommendations'].append("Create triggers and ensure they are active")
        
        if results['trigger_workflow_associations'] == 0:
            results['issues'].append("No trigger-workflow associations found")
            results['recommendations'].append("Create associations between triggers and workflows")
        
        # Check for workflows without actions
        workflows_without_actions = Workflow.objects.filter(
            status='ACTIVE',
            workflow_actions__isnull=True
        ).count()
        
        if workflows_without_actions > 0:
            results['issues'].append(f"{workflows_without_actions} active workflows have no actions")
            results['recommendations'].append("Add actions to workflows to make them functional")
        
        # Check for workflows without triggers
        workflows_without_triggers = Workflow.objects.filter(
            status='ACTIVE',
            trigger_associations__isnull=True
        ).count()
        
        if workflows_without_triggers > 0:
            results['issues'].append(f"{workflows_without_triggers} active workflows have no trigger associations")
            results['recommendations'].append("Associate triggers with workflows to enable execution")
        
        return results
    
    @staticmethod
    def simulate_trigger_event(event_type: str, event_data: Dict[str, Any], 
                             user_id: Optional[str] = None, conversation_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Simulate a trigger event and see what workflows would execute
        """
        # Create a mock event log
        event_log = TriggerEventLog(
            event_type=event_type,
            event_data=event_data,
            user_id=user_id,
            conversation_id=conversation_id,
            created_at=timezone.now()
        )
        
        # Build context
        context = build_context_from_event_log(event_log)
        
        # Find matching workflows
        trigger_service = TriggerService()
        workflows = trigger_service.process_event_get_workflows(event_log)
        
        return {
            'event_type': event_type,
            'event_data': event_data,
            'context': context,
            'matching_workflows': workflows,
            'workflow_count': len(workflows)
        }
    
    @staticmethod
    def get_recent_execution_stats(hours: int = 24) -> Dict[str, Any]:
        """
        Get statistics about recent workflow executions
        """
        cutoff = timezone.now() - timedelta(hours=hours)
        
        executions = WorkflowExecution.objects.filter(created_at__gte=cutoff)
        
        stats = {
            'total_executions': executions.count(),
            'by_status': {},
            'by_workflow': {},
            'avg_duration': None,
            'failed_executions': [],
            'period_hours': hours
        }
        
        # Status breakdown
        status_counts = executions.values('status').annotate(
            count=models.Count('id')
        ).order_by('-count')
        
        for item in status_counts:
            stats['by_status'][item['status']] = item['count']
        
        # Workflow breakdown
        workflow_counts = executions.values('workflow__name').annotate(
            count=models.Count('id')
        ).order_by('-count')
        
        for item in workflow_counts:
            stats['by_workflow'][item['workflow__name']] = item['count']
        
        # Average duration
        completed_executions = executions.filter(
            status='COMPLETED',
            started_at__isnull=False,
            completed_at__isnull=False
        )
        
        if completed_executions.exists():
            durations = []
            for exec in completed_executions:
                if exec.duration:
                    durations.append(exec.duration.total_seconds())
            
            if durations:
                stats['avg_duration'] = sum(durations) / len(durations)
        
        # Failed executions details
        failed_executions = executions.filter(status='FAILED')
        for exec in failed_executions:
            stats['failed_executions'].append({
                'id': exec.id,
                'workflow': exec.workflow.name,
                'error': exec.error_message,
                'created_at': exec.created_at.isoformat()
            })
        
        return stats
    
    @staticmethod
    def test_workflow_conditions(workflow_id: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Test if a workflow's conditions would pass with given context
        """
        try:
            workflow = Workflow.objects.get(id=workflow_id)
        except Workflow.DoesNotExist:
            return {'error': 'Workflow not found'}
        
        results = {
            'workflow_id': workflow_id,
            'workflow_name': workflow.name,
            'workflow_active': workflow.is_active(),
            'triggers': [],
            'actions': []
        }
        
        # Test triggers associated with this workflow
        associations = workflow.trigger_associations.filter(is_active=True)
        
        for assoc in associations:
            trigger_result = {
                'trigger_name': assoc.trigger.name,
                'trigger_type': assoc.trigger.trigger_type,
                'trigger_active': assoc.trigger.is_active,
                'filters_pass': True,
                'association_conditions_pass': True,
                'priority': assoc.priority
            }
            
            # Test trigger filters
            if assoc.trigger.filters:
                try:
                    trigger_result['filters_pass'] = evaluate_conditions(assoc.trigger.filters, context)
                except Exception as e:
                    trigger_result['filters_pass'] = False
                    trigger_result['filter_error'] = str(e)
            
            # Test association conditions
            if assoc.specific_conditions:
                try:
                    trigger_result['association_conditions_pass'] = evaluate_conditions(
                        assoc.specific_conditions, context
                    )
                except Exception as e:
                    trigger_result['association_conditions_pass'] = False
                    trigger_result['association_error'] = str(e)
            
            results['triggers'].append(trigger_result)
        
        # Test workflow actions
        workflow_actions = workflow.workflow_actions.all().order_by('order')
        
        for workflow_action in workflow_actions:
            action_result = {
                'action_name': workflow_action.action.name,
                'action_type': workflow_action.action.action_type,
                'order': workflow_action.order,
                'is_required': workflow_action.is_required,
                'condition_pass': True
            }
            
            # Test action condition if it exists
            if workflow_action.condition:
                condition_config = {
                    'operator': workflow_action.condition.operator,
                    'conditions': workflow_action.condition.conditions,
                    'use_custom_code': workflow_action.condition.use_custom_code,
                    'custom_code': workflow_action.condition.custom_code
                }
                
                try:
                    action_result['condition_pass'] = evaluate_conditions(condition_config, context)
                except Exception as e:
                    action_result['condition_pass'] = False
                    action_result['condition_error'] = str(e)
            
            results['actions'].append(action_result)
        
        return results
    
    @staticmethod
    def get_workflow_execution_trace(execution_id: int) -> Dict[str, Any]:
        """
        Get detailed trace of a workflow execution
        """
        try:
            execution = WorkflowExecution.objects.get(id=execution_id)
        except WorkflowExecution.DoesNotExist:
            return {'error': 'Execution not found'}
        
        trace = {
            'execution_id': execution_id,
            'workflow_name': execution.workflow.name,
            'status': execution.status,
            'started_at': execution.started_at.isoformat() if execution.started_at else None,
            'completed_at': execution.completed_at.isoformat() if execution.completed_at else None,
            'duration': execution.duration.total_seconds() if execution.duration else None,
            'trigger_data': execution.trigger_data,
            'context_data': execution.context_data,
            'result_data': execution.result_data,
            'error_message': execution.error_message,
            'error_details': execution.error_details,
            'actions': []
        }
        
        # Get action executions
        action_executions = execution.action_executions.all().order_by('workflow_action__order')
        
        for action_exec in action_executions:
            action_trace = {
                'action_name': action_exec.workflow_action.action.name,
                'action_type': action_exec.workflow_action.action.action_type,
                'order': action_exec.workflow_action.order,
                'status': action_exec.status,
                'started_at': action_exec.started_at.isoformat() if action_exec.started_at else None,
                'completed_at': action_exec.completed_at.isoformat() if action_exec.completed_at else None,
                'duration': action_exec.duration.total_seconds() if action_exec.duration else None,
                'input_data': action_exec.input_data,
                'result_data': action_exec.result_data,
                'error_message': action_exec.error_message,
                'error_details': action_exec.error_details,
                'retry_count': action_exec.retry_count
            }
            trace['actions'].append(action_trace)
        
        return trace
    
    @staticmethod
    def find_problematic_workflows() -> Dict[str, Any]:
        """
        Find workflows that might have configuration issues
        """
        problems = {
            'inactive_workflows_with_triggers': [],
            'active_workflows_without_triggers': [],
            'active_workflows_without_actions': [],
            'workflows_with_failed_executions': [],
            'triggers_without_associations': []
        }
        
        # Inactive workflows that have trigger associations
        inactive_with_triggers = Workflow.objects.filter(
            status__in=['DRAFT', 'PAUSED', 'ARCHIVED'],
            trigger_associations__isnull=False
        ).distinct()
        
        for workflow in inactive_with_triggers:
            problems['inactive_workflows_with_triggers'].append({
                'id': str(workflow.id),
                'name': workflow.name,
                'status': workflow.status
            })
        
        # Active workflows without trigger associations
        active_without_triggers = Workflow.objects.filter(
            status='ACTIVE',
            trigger_associations__isnull=True
        )
        
        for workflow in active_without_triggers:
            problems['active_workflows_without_triggers'].append({
                'id': str(workflow.id),
                'name': workflow.name
            })
        
        # Active workflows without actions
        active_without_actions = Workflow.objects.filter(
            status='ACTIVE',
            workflow_actions__isnull=True
        )
        
        for workflow in active_without_actions:
            problems['active_workflows_without_actions'].append({
                'id': str(workflow.id),
                'name': workflow.name
            })
        
        # Workflows with recent failed executions
        cutoff = timezone.now() - timedelta(hours=24)
        failed_executions = WorkflowExecution.objects.filter(
            status='FAILED',
            created_at__gte=cutoff
        ).values('workflow').annotate(
            failure_count=models.Count('id')
        ).order_by('-failure_count')
        
        for item in failed_executions:
            workflow = Workflow.objects.get(id=item['workflow'])
            problems['workflows_with_failed_executions'].append({
                'id': str(workflow.id),
                'name': workflow.name,
                'failure_count': item['failure_count']
            })
        
        # Triggers without workflow associations
        triggers_without_assoc = Trigger.objects.filter(
            is_active=True,
            workflow_associations__isnull=True
        )
        
        for trigger in triggers_without_assoc:
            problems['triggers_without_associations'].append({
                'id': str(trigger.id),
                'name': trigger.name,
                'trigger_type': trigger.trigger_type
            })
        
        return problems
