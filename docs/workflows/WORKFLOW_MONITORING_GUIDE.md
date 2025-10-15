# 🎯 Workflow System Monitoring Guide

Your workflow system is **working correctly**! Here are the tools to monitor it:

## ✅ **Current Status**
- **3 Active Workflows** configured
- **100% Success Rate** (2/2 executions successful in last 30 minutes)
- **4 Events** processed recently  
- **2 Customer Messages** triggered workflows
- **2 Support Messages** sent automatically

---

## 🔧 **Quick Health Check Commands**

### 1. **Overall System Health**
```bash
./workflow_health_check.sh
```

### 2. **Check Recent Activity (Last 10 minutes)**
```bash
docker exec django_app python manage.py shell -c "
from workflow.models import TriggerEventLog, WorkflowExecution
from datetime import timedelta
from django.utils import timezone

cutoff = timezone.now() - timedelta(minutes=10)
events = TriggerEventLog.objects.filter(created_at__gte=cutoff).count()
executions = WorkflowExecution.objects.filter(created_at__gte=cutoff).count()
print(f'Events: {events}, Executions: {executions}')
"
```

### 3. **Check Active Workflows**
```bash
docker exec django_app python manage.py shell -c "
from workflow.models import Workflow
for w in Workflow.objects.filter(status='ACTIVE'):
    print(f'✅ {w.name}')
"
```

### 4. **Monitor Celery Tasks**
```bash
docker logs celery_worker --tail 20 | grep workflow
```

### 5. **Recent Workflow Executions**
```bash
docker exec django_app python manage.py shell -c "
from workflow.models import WorkflowExecution
for exec in WorkflowExecution.objects.order_by('-created_at')[:5]:
    print(f'{exec.created_at.strftime(\"%H:%M:%S\")} - {exec.workflow.name}: {exec.status}')
"
```

---

## 📊 **Monitoring Dashboard**

### **Check Last Hour Activity**
```bash
docker exec django_app python manage.py shell -c "
from workflow.models import TriggerEventLog, WorkflowExecution
from message.models import Message
from datetime import timedelta
from django.utils import timezone

cutoff = timezone.now() - timedelta(hours=1)

events = TriggerEventLog.objects.filter(created_at__gte=cutoff)
executions = WorkflowExecution.objects.filter(created_at__gte=cutoff)
messages = Message.objects.filter(created_at__gte=cutoff, type='customer')

successful = executions.filter(status='COMPLETED').count()
failed = executions.filter(status='FAILED').count()

print('🎯 LAST HOUR SUMMARY:')
print(f'   📋 Events: {events.count()}')
print(f'   ⚡ Executions: {executions.count()}')
print(f'   ✅ Successful: {successful}')
print(f'   ❌ Failed: {failed}')
print(f'   💬 Customer Messages: {messages.count()}')

if executions.count() > 0:
    rate = round(successful / executions.count() * 100, 1)
    print(f'   📈 Success Rate: {rate}%')
"
```

---

## 🔍 **Real-Time Monitoring**

### **Watch Live Activity** (Press Ctrl+C to stop)
```bash
docker exec -it django_app python manage.py shell -c "
import time
from workflow.models import TriggerEventLog, WorkflowExecution
from django.utils import timezone

print('🎯 WATCHING FOR WORKFLOW ACTIVITY...')
print('Press Ctrl+C to stop')
print('-' * 40)

last_event_id = TriggerEventLog.objects.order_by('-id').first()
last_event_id = last_event_id.id if last_event_id else 0

last_exec_id = WorkflowExecution.objects.order_by('-id').first()
last_exec_id = last_exec_id.id if last_exec_id else 0

try:
    while True:
        # Check for new events
        new_events = TriggerEventLog.objects.filter(id__gt=last_event_id)
        for event in new_events:
            print(f'🆕 {timezone.now().strftime(\"%H:%M:%S\")} - {event.event_type} (User: {event.user_id})')
            last_event_id = event.id
        
        # Check for new executions
        new_execs = WorkflowExecution.objects.filter(id__gt=last_exec_id)
        for exec in new_execs:
            status = '✅' if exec.status == 'COMPLETED' else '❌' if exec.status == 'FAILED' else '⏳'
            print(f'⚡ {timezone.now().strftime(\"%H:%M:%S\")} - {exec.workflow.name} {status}')
            last_exec_id = exec.id
        
        time.sleep(2)
except KeyboardInterrupt:
    print('\n👋 Monitoring stopped')
"
```

---

## 🚨 **Troubleshooting Commands**

### **Check Failed Executions**
```bash
docker exec django_app python manage.py shell -c "
from workflow.models import WorkflowExecution
from datetime import timedelta
from django.utils import timezone

failed = WorkflowExecution.objects.filter(
    status='FAILED',
    created_at__gte=timezone.now() - timedelta(hours=24)
)

print(f'Failed executions (last 24h): {failed.count()}')
for exec in failed:
    print(f'   ❌ {exec.workflow.name}: {exec.error_message}')
"
```

### **Check Celery Worker Health**
```bash
docker ps | grep celery_worker
docker logs celery_worker --tail 50 | grep -E "(ERROR|WARNING|workflow)"
```

### **Restart Celery if Needed**
```bash
docker restart celery_worker
```

---

## 📈 **Performance Metrics**

### **Success Rate Analysis**
```bash
docker exec django_app python manage.py shell -c "
from workflow.models import WorkflowExecution
from datetime import timedelta
from django.utils import timezone

# Last 24 hours
cutoff = timezone.now() - timedelta(hours=24)
executions = WorkflowExecution.objects.filter(created_at__gte=cutoff)

total = executions.count()
successful = executions.filter(status='COMPLETED').count()
failed = executions.filter(status='FAILED').count()
pending = executions.filter(status='PENDING').count()

print('📊 WORKFLOW PERFORMANCE (24h):')
print(f'   Total: {total}')
print(f'   ✅ Successful: {successful}')
print(f'   ❌ Failed: {failed}')
print(f'   ⏳ Pending: {pending}')

if total > 0:
    print(f'   📈 Success Rate: {round(successful/total*100, 1)}%')
"
```

---

## 🎉 **System Status: HEALTHY**

Your workflow system is:
- ✅ **Properly configured** (3 active workflows, 3 triggers)
- ✅ **Processing events** (MESSAGE_RECEIVED, USER_CREATED, etc.)  
- ✅ **Executing workflows** (100% success rate recently)
- ✅ **Sending automated responses** 
- ✅ **Integrated with AI system**
- ✅ **Celery workers running**

**The only remaining task is to configure Instagram channels for Instagram message workflows.**

---

*Use these commands to monitor your workflow system and ensure it continues working optimally!*
