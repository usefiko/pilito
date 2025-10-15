#!/bin/bash
# Workflow System Health Check Script
# Quick script to check if workflows are running properly

echo "🔍 WORKFLOW SYSTEM HEALTH CHECK"
echo "================================"

echo "📊 System Status:"
docker exec django_app python manage.py setup_workflow_system --check-health

echo ""
echo "🔧 Celery Worker Status:"
if docker ps | grep -q celery_worker; then
    echo "   ✅ Celery worker container is running"
    
    # Check recent workflow tasks
    echo "   📋 Recent workflow tasks:"
    docker logs celery_worker --tail 10 | grep -E "(workflow|succeeded|failed)" | tail -3
else
    echo "   ❌ Celery worker container is not running"
fi

echo ""
echo "📈 Recent Activity (last 30 minutes):"
docker exec django_app python manage.py shell -c "
from workflow.models import TriggerEventLog, WorkflowExecution
from datetime import timedelta
from django.utils import timezone

cutoff = timezone.now() - timedelta(minutes=30)
events = TriggerEventLog.objects.filter(created_at__gte=cutoff).count()
executions = WorkflowExecution.objects.filter(created_at__gte=cutoff).count()
successful = WorkflowExecution.objects.filter(created_at__gte=cutoff, status='COMPLETED').count()

print(f'   Events: {events}')
print(f'   Executions: {executions}')
print(f'   Successful: {successful}')
if executions > 0:
    print(f'   Success Rate: {round(successful/executions*100, 1)}%')
"

echo ""
echo "💬 Recent Messages:"
docker exec django_app python manage.py shell -c "
from message.models import Message
from datetime import timedelta
from django.utils import timezone

cutoff = timezone.now() - timedelta(minutes=30)
customer_messages = Message.objects.filter(
    created_at__gte=cutoff,
    type='customer'
).count()

support_messages = Message.objects.filter(
    created_at__gte=cutoff,
    type='support'
).count()

print(f'   Customer Messages: {customer_messages}')
print(f'   Support Messages: {support_messages}')
"

echo ""
echo "🎯 System Health: "
docker exec django_app python manage.py shell -c "
from workflow.models import Workflow, Trigger, TriggerWorkflowAssociation

active_workflows = Workflow.objects.filter(status='ACTIVE').count()
active_triggers = Trigger.objects.filter(is_active=True).count()
active_associations = TriggerWorkflowAssociation.objects.filter(is_active=True).count()

if active_workflows > 0 and active_triggers > 0 and active_associations > 0:
    print('   ✅ System is healthy and configured')
else:
    print('   ⚠️  System may need configuration')
    print(f'      Workflows: {active_workflows}, Triggers: {active_triggers}, Associations: {active_associations}')
"

echo ""
echo "================================"
echo "Health check completed at $(date)"
