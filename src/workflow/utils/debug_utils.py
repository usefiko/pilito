"""
Workflow System Debug Utilities

Provides debugging and monitoring tools for the workflow system.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from django.utils import timezone
from django.db.models import Count, Q

from workflow.models import (
    TriggerEventLog, 
    WorkflowExecution, 
    WorkflowActionExecution,
    Trigger,
    Workflow,
    TriggerWorkflowAssociation
)

logger = logging.getLogger(__name__)


class WorkflowDebugger:
    """Debug utilities for workflow system"""
    
    @staticmethod
    def get_system_stats(hours: int = 24) -> Dict[str, Any]:
        """Get workflow system statistics for the last N hours"""
        cutoff_time = timezone.now() - timedelta(hours=hours)
        
        stats = {
            'period_hours': hours,
            'cutoff_time': cutoff_time.isoformat(),
            'timestamp': timezone.now().isoformat(),
        }
        
        # Event statistics
        event_stats = TriggerEventLog.objects.filter(
            created_at__gte=cutoff_time
        ).values('event_type').annotate(count=Count('id')).order_by('-count')
        
        stats['events'] = {
            'total': TriggerEventLog.objects.filter(created_at__gte=cutoff_time).count(),
            'by_type': list(event_stats)
        }
        
        # Execution statistics
        execution_stats = WorkflowExecution.objects.filter(
            created_at__gte=cutoff_time
        ).values('status').annotate(count=Count('id'))
        
        stats['executions'] = {
            'total': WorkflowExecution.objects.filter(created_at__gte=cutoff_time).count(),
            'by_status': list(execution_stats)
        }
        
        # Action execution statistics
        action_execution_stats = WorkflowActionExecution.objects.filter(
            queued_at__gte=cutoff_time
        ).values('status').annotate(count=Count('id'))
        
        stats['action_executions'] = {
            'total': WorkflowActionExecution.objects.filter(queued_at__gte=cutoff_time).count(),
            'by_status': list(action_execution_stats)
        }
        
        # Active system components
        stats['active_components'] = {
            'triggers': Trigger.objects.filter(is_active=True).count(),
            'workflows': Workflow.objects.filter(status='ACTIVE').count(),
            'associations': TriggerWorkflowAssociation.objects.filter(
                is_active=True,
                trigger__is_active=True,
                workflow__status='ACTIVE'
            ).count()
        }
        
        return stats
    
    @staticmethod
    def get_failed_executions(hours: int = 24) -> List[Dict[str, Any]]:
        """Get failed workflow executions with details"""
        cutoff_time = timezone.now() - timedelta(hours=hours)
        
        failed_executions = WorkflowExecution.objects.filter(
            status='FAILED',
            created_at__gte=cutoff_time
        ).select_related('workflow').order_by('-created_at')
        
        results = []
        for execution in failed_executions:
            results.append({
                'execution_id': execution.id,
                'workflow_name': execution.workflow.name,
                'workflow_id': str(execution.workflow.id),
                'error_message': execution.error_message,
                'created_at': execution.created_at.isoformat(),
                'user_id': execution.user,
                'conversation_id': execution.conversation,
                'trigger_data': execution.trigger_data
            })
        
        return results
    
    @staticmethod
    def test_trigger_matching(event_type: str, test_data: Dict[str, Any]) -> Dict[str, Any]:
        """Test trigger matching for a given event type and data"""
        from workflow.services.trigger_service import TriggerService
        from workflow.utils.condition_evaluator import build_context_from_event_log
        
        # Create a test event log
        test_event_log = TriggerEventLog(
            event_type=event_type,
            event_data=test_data,
            user_id=test_data.get('user_id'),
            conversation_id=test_data.get('conversation_id'),
            created_at=timezone.now()
        )
        
        # Build context
        context = build_context_from_event_log(test_event_log)
        
        # Get matching workflows
        workflows = TriggerService.process_event_get_workflows(test_event_log)
        
        # Get available triggers for this event type
        available_triggers = Trigger.objects.filter(
            trigger_type=event_type,
            is_active=True
        ).select_related().prefetch_related('workflow_associations__workflow')
        
        trigger_details = []
        for trigger in available_triggers:
            associations = trigger.workflow_associations.filter(
                is_active=True,
                workflow__status='ACTIVE'
            )
            
            trigger_details.append({
                'trigger_id': str(trigger.id),
                'trigger_name': trigger.name,
                'filters': trigger.filters,
                'active_associations': associations.count(),
                'associated_workflows': [
                    {
                        'workflow_id': str(assoc.workflow.id),
                        'workflow_name': assoc.workflow.name,
                        'priority': assoc.priority
                    }
                    for assoc in associations
                ]
            })
        
        return {
            'event_type': event_type,
            'test_data': test_data,
            'context': context,
            'matching_workflows': workflows,
            'available_triggers': trigger_details,
            'total_triggers': len(trigger_details),
            'total_matches': len(workflows)
        }
    
    @staticmethod
    def trace_execution(execution_id: int) -> Dict[str, Any]:
        """Get detailed execution trace for debugging"""
        try:
            execution = WorkflowExecution.objects.select_related('workflow').get(id=execution_id)
        except WorkflowExecution.DoesNotExist:
            return {'error': 'Execution not found'}
        
        # Get action executions
        action_executions = WorkflowActionExecution.objects.filter(
            workflow_execution=execution
        ).select_related('workflow_action__action').order_by('workflow_action__order')
        
        action_details = []
        for action_exec in action_executions:
            action_details.append({
                'action_execution_id': action_exec.id,
                'action_name': action_exec.workflow_action.action.name,
                'action_type': action_exec.workflow_action.action.action_type,
                'order': action_exec.workflow_action.order,
                'status': action_exec.status,
                'queued_at': action_exec.queued_at.isoformat() if action_exec.queued_at else None,
                'started_at': action_exec.started_at.isoformat() if action_exec.started_at else None,
                'completed_at': action_exec.completed_at.isoformat() if action_exec.completed_at else None,
                'error_message': action_exec.error_message,
                'retry_count': action_exec.retry_count,
                'input_data': action_exec.input_data,
                'result_data': action_exec.result_data
            })
        
        return {
            'execution_id': execution.id,
            'workflow_name': execution.workflow.name,
            'workflow_id': str(execution.workflow.id),
            'status': execution.status,
            'user_id': execution.user,
            'conversation_id': execution.conversation,
            'created_at': execution.created_at.isoformat(),
            'started_at': execution.started_at.isoformat() if execution.started_at else None,
            'completed_at': execution.completed_at.isoformat() if execution.completed_at else None,
            'error_message': execution.error_message,
            'trigger_data': execution.trigger_data,
            'context_data': execution.context_data,
            'result_data': execution.result_data,
            'action_executions': action_details,
            'total_actions': len(action_details)
        }
    
    @staticmethod
    def get_conversation_workflow_history(conversation_id: str, hours: int = 168) -> Dict[str, Any]:
        """Get workflow execution history for a specific conversation (default: 7 days)"""
        cutoff_time = timezone.now() - timedelta(hours=hours)
        
        executions = WorkflowExecution.objects.filter(
            conversation=conversation_id,
            created_at__gte=cutoff_time
        ).select_related('workflow').order_by('-created_at')
        
        execution_details = []
        for execution in executions:
            execution_details.append({
                'execution_id': execution.id,
                'workflow_name': execution.workflow.name,
                'status': execution.status,
                'created_at': execution.created_at.isoformat(),
                'error_message': execution.error_message if execution.status == 'FAILED' else None
            })
        
        # Get event logs for this conversation
        event_logs = TriggerEventLog.objects.filter(
            conversation_id=conversation_id,
            created_at__gte=cutoff_time
        ).order_by('-created_at')
        
        event_details = []
        for event_log in event_logs:
            event_details.append({
                'event_id': str(event_log.id),
                'event_type': event_log.event_type,
                'created_at': event_log.created_at.isoformat(),
                'event_data': event_log.event_data
            })
        
        return {
            'conversation_id': conversation_id,
            'period_hours': hours,
            'total_executions': len(execution_details),
            'total_events': len(event_details),
            'executions': execution_details,
            'events': event_details
        }
    
    @staticmethod
    def check_system_health() -> Dict[str, Any]:
        """Comprehensive system health check"""
        health = {
            'timestamp': timezone.now().isoformat(),
            'status': 'healthy',
            'issues': []
        }
        
        # Check for stale executions
        stale_executions = WorkflowExecution.objects.filter(
            status='RUNNING',
            created_at__lt=timezone.now() - timedelta(hours=1)
        ).count()
        
        if stale_executions > 0:
            health['issues'].append(f"{stale_executions} workflow executions have been running for over 1 hour")
            health['status'] = 'warning'
        
        # Check for failed actions
        recent_failed_actions = WorkflowActionExecution.objects.filter(
            status='FAILED',
            queued_at__gte=timezone.now() - timedelta(hours=1)
        ).count()
        
        if recent_failed_actions > 5:
            health['issues'].append(f"{recent_failed_actions} action executions failed in the last hour")
            health['status'] = 'warning'
        
        # Check for inactive triggers with associations
        inactive_associated_triggers = Trigger.objects.filter(
            is_active=False,
            workflow_associations__is_active=True
        ).count()
        
        if inactive_associated_triggers > 0:
            health['issues'].append(f"{inactive_associated_triggers} inactive triggers have active workflow associations")
            health['status'] = 'warning'
        
        # Check for workflows without triggers
        workflows_without_triggers = Workflow.objects.filter(
            status='ACTIVE',
            trigger_associations__isnull=True
        ).count()
        
        if workflows_without_triggers > 0:
            health['issues'].append(f"{workflows_without_triggers} active workflows have no trigger associations")
            health['status'] = 'warning'
        
        health['checks'] = {
            'stale_executions': stale_executions,
            'recent_failed_actions': recent_failed_actions,
            'inactive_associated_triggers': inactive_associated_triggers,
            'workflows_without_triggers': workflows_without_triggers
        }
        
        return health


def print_system_stats(hours: int = 24):
    """Print formatted system statistics"""
    stats = WorkflowDebugger.get_system_stats(hours)
    
    print(f"\n=== Workflow System Statistics (Last {hours} hours) ===")
    print(f"Period: {stats['cutoff_time']} to {stats['timestamp']}")
    
    print(f"\n📊 Events:")
    print(f"  Total: {stats['events']['total']}")
    for event in stats['events']['by_type']:
        print(f"  - {event['event_type']}: {event['count']}")
    
    print(f"\n⚙️  Executions:")
    print(f"  Total: {stats['executions']['total']}")
    for execution in stats['executions']['by_status']:
        print(f"  - {execution['status']}: {execution['count']}")
    
    print(f"\n🎬 Action Executions:")
    print(f"  Total: {stats['action_executions']['total']}")
    for action in stats['action_executions']['by_status']:
        print(f"  - {action['status']}: {action['count']}")
    
    print(f"\n🔧 Active Components:")
    for component, count in stats['active_components'].items():
        print(f"  - {component}: {count}")


def print_failed_executions(hours: int = 24):
    """Print formatted failed execution details"""
    failed = WorkflowDebugger.get_failed_executions(hours)
    
    print(f"\n=== Failed Executions (Last {hours} hours) ===")
    
    if not failed:
        print("✅ No failed executions found")
        return
    
    for execution in failed:
        print(f"\n❌ Execution #{execution['execution_id']}")
        print(f"   Workflow: {execution['workflow_name']}")
        print(f"   Error: {execution['error_message']}")
        print(f"   Created: {execution['created_at']}")
        if execution['user_id']:
            print(f"   User: {execution['user_id']}")
        if execution['conversation_id']:
            print(f"   Conversation: {execution['conversation_id']}")
