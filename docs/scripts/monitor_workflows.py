#!/usr/bin/env python3
"""
Workflow System Monitoring Script
Run this script to monitor workflow activity in real-time
"""

import os
import django
import time
from datetime import timedelta
from django.utils import timezone

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.development')
django.setup()

from workflow.models import TriggerEventLog, WorkflowExecution, WorkflowActionExecution
from message.models import Message, Conversation, Customer

def get_workflow_stats(hours=1):
    """Get workflow statistics for the last N hours"""
    cutoff = timezone.now() - timedelta(hours=hours)
    
    # Count events
    events = TriggerEventLog.objects.filter(created_at__gte=cutoff)
    events_by_type = {}
    for event in events:
        events_by_type[event.event_type] = events_by_type.get(event.event_type, 0) + 1
    
    # Count executions
    executions = WorkflowExecution.objects.filter(created_at__gte=cutoff)
    completed = executions.filter(status='COMPLETED').count()
    failed = executions.filter(status='FAILED').count()
    
    # Count messages
    messages = Message.objects.filter(
        created_at__gte=cutoff,
        type='customer'
    ).count()
    
    return {
        'period_hours': hours,
        'total_events': events.count(),
        'events_by_type': events_by_type,
        'total_executions': executions.count(),
        'successful_executions': completed,
        'failed_executions': failed,
        'success_rate': round(completed / executions.count() * 100, 1) if executions.count() > 0 else 0,
        'customer_messages': messages,
        'timestamp': timezone.now().strftime('%Y-%m-%d %H:%M:%S')
    }

def print_workflow_dashboard():
    """Print a real-time workflow dashboard"""
    print('\n' + '='*60)
    print('🎯 WORKFLOW SYSTEM DASHBOARD')
    print('='*60)
    
    # Last hour stats
    stats_1h = get_workflow_stats(1)
    print(f"📊 LAST HOUR ({stats_1h['timestamp']}):")
    print(f"   📋 Events: {stats_1h['total_events']}")
    for event_type, count in stats_1h['events_by_type'].items():
        print(f"      - {event_type}: {count}")
    print(f"   ⚡ Executions: {stats_1h['total_executions']} (Success: {stats_1h['success_rate']}%)")
    print(f"   💬 Customer Messages: {stats_1h['customer_messages']}")
    
    # Last 24 hours stats
    stats_24h = get_workflow_stats(24)
    print(f"\n📈 LAST 24 HOURS:")
    print(f"   📋 Events: {stats_24h['total_events']}")
    print(f"   ⚡ Executions: {stats_24h['total_executions']} (Success: {stats_24h['success_rate']}%)")
    print(f"   💬 Customer Messages: {stats_24h['customer_messages']}")
    
    # Recent activity
    print(f"\n🔄 RECENT ACTIVITY:")
    recent_executions = WorkflowExecution.objects.order_by('-created_at')[:5]
    for exec in recent_executions:
        time_str = exec.created_at.strftime('%H:%M:%S')
        status_emoji = '✅' if exec.status == 'COMPLETED' else '❌' if exec.status == 'FAILED' else '⏳'
        print(f"   {status_emoji} [{time_str}] {exec.workflow.name} (User: {exec.user})")
    
    # Active conversations
    active_convs = Conversation.objects.filter(
        updated_at__gte=timezone.now() - timedelta(hours=1)
    ).count()
    print(f"\n💬 ACTIVE CONVERSATIONS (last hour): {active_convs}")

def monitor_live():
    """Monitor workflow activity in real-time"""
    print("🎯 STARTING LIVE WORKFLOW MONITORING")
    print("Press Ctrl+C to stop")
    print("-" * 40)
    
    last_event_count = TriggerEventLog.objects.count()
    last_execution_count = WorkflowExecution.objects.count()
    
    try:
        while True:
            current_event_count = TriggerEventLog.objects.count()
            current_execution_count = WorkflowExecution.objects.count()
            
            if current_event_count > last_event_count:
                new_events = TriggerEventLog.objects.order_by('-created_at')[:current_event_count - last_event_count]
                for event in reversed(new_events):
                    print(f"🆕 {timezone.now().strftime('%H:%M:%S')} - {event.event_type} (User: {event.user_id})")
                last_event_count = current_event_count
            
            if current_execution_count > last_execution_count:
                new_executions = WorkflowExecution.objects.order_by('-created_at')[:current_execution_count - last_execution_count]
                for exec in reversed(new_executions):
                    status_emoji = '✅' if exec.status == 'COMPLETED' else '❌' if exec.status == 'FAILED' else '⏳'
                    print(f"⚡ {timezone.now().strftime('%H:%M:%S')} - {exec.workflow.name} {status_emoji}")
                last_execution_count = current_execution_count
            
            time.sleep(2)
            
    except KeyboardInterrupt:
        print("\n👋 Monitoring stopped")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == 'live':
        monitor_live()
    else:
        print_workflow_dashboard()
        print("\nℹ️  Run with 'live' argument for real-time monitoring:")
        print("   python monitor_workflows.py live")
