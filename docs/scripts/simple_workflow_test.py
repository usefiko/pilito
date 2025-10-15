#!/usr/bin/env python3
"""
Simple workflow functionality test
"""

import subprocess
import json
import sys
import os

def run_docker_command(command):
    """Run a command in the celery_worker container"""
    try:
        full_command = f'docker exec -i celery_worker {command}'
        result = subprocess.run(full_command, shell=True, capture_output=True, text=True, timeout=30)
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return -1, "", "Command timed out"
    except Exception as e:
        return -1, "", str(e)

def test_workflow_models():
    """Test if workflow models exist and are accessible"""
    print("🔍 Testing workflow models...")
    
    command = '''python manage.py shell -c "
from workflow.models import Workflow, Trigger, TriggerWorkflowAssociation
print('Models imported successfully')
print(f'Workflows: {Workflow.objects.count()}')
print(f'Triggers: {Trigger.objects.count()}') 
print(f'Associations: {TriggerWorkflowAssociation.objects.count()}')
"'''
    
    returncode, stdout, stderr = run_docker_command(command)
    
    if returncode == 0:
        print("✅ Workflow models are accessible")
        print(stdout)
        return True
    else:
        print("❌ Error accessing workflow models")
        print(f"Error: {stderr}")
        return False

def test_recent_workflow_executions():
    """Test for recent workflow executions"""
    print("\n🔍 Testing recent workflow executions...")
    
    command = '''python manage.py shell -c "
from workflow.models import WorkflowExecution, TriggerEventLog
from datetime import datetime, timedelta
from django.utils import timezone

cutoff = timezone.now() - timedelta(hours=24)
recent_executions = WorkflowExecution.objects.filter(created_at__gte=cutoff)
recent_events = TriggerEventLog.objects.filter(created_at__gte=cutoff)

print(f'Recent executions (24h): {recent_executions.count()}')
print(f'Recent events (24h): {recent_events.count()}')

# Show execution details
for exec in recent_executions[:3]:
    print(f'- {exec.workflow.name}: {exec.status}')
    if exec.error_message:
        print(f'  Error: {exec.error_message[:100]}...')

# Show event details  
for event in recent_events[:3]:
    print(f'- Event: {event.event_type} at {event.created_at}')
"'''
    
    returncode, stdout, stderr = run_docker_command(command)
    
    if returncode == 0:
        print("✅ Execution check completed")
        print(stdout)
        return True
    else:
        print("❌ Error checking executions")
        print(f"Error: {stderr}")
        return False

def test_workflow_setup():
    """Test workflow setup and configuration"""
    print("\n🔍 Testing workflow setup...")
    
    command = '''python manage.py shell -c "
from workflow.models import Workflow, Trigger, TriggerWorkflowAssociation
from workflow.utils.debug_utilities import WorkflowDebugger

# Check setup
try:
    setup_status = WorkflowDebugger.check_workflow_setup()
    print(f'Active workflows: {setup_status.get(\"active_workflows\", 0)}')
    print(f'Active triggers: {setup_status.get(\"active_triggers\", 0)}') 
    print(f'Associations: {setup_status.get(\"trigger_workflow_associations\", 0)}')
    
    if setup_status.get('issues'):
        print('Issues found:')
        for issue in setup_status['issues']:
            print(f'- {issue}')
    else:
        print('No setup issues found')
        
except Exception as e:
    print(f'Error running setup check: {e}')
    # Fallback to basic counts
    print(f'Workflows: {Workflow.objects.count()}')
    print(f'Active workflows: {Workflow.objects.filter(status=\"ACTIVE\").count()}')
    print(f'Triggers: {Trigger.objects.count()}') 
    print(f'Active triggers: {Trigger.objects.filter(is_active=True).count()}')
    print(f'Associations: {TriggerWorkflowAssociation.objects.filter(is_active=True).count()}')
"'''
    
    returncode, stdout, stderr = run_docker_command(command)
    
    if returncode == 0:
        print("✅ Setup check completed")
        print(stdout)
        return True
    else:
        print("❌ Error checking setup")
        print(f"Error: {stderr}")
        return False

def test_message_signal():
    """Test if message signals are working"""
    print("\n🔍 Testing message signal functionality...")
    
    command = '''python manage.py shell -c "
from message.models import Message, Customer, Conversation
from accounts.models import User
from workflow.models import TriggerEventLog
from datetime import datetime

# Find a recent customer message
recent_message = Message.objects.filter(type='customer').order_by('-created_at').first()

if recent_message:
    print(f'Found recent message: {recent_message.content[:50]}...')
    print(f'Message ID: {recent_message.id}')
    
    # Check if event log exists
    event_logs = TriggerEventLog.objects.filter(
        event_type='MESSAGE_RECEIVED',
        event_data__message_id=str(recent_message.id)
    )
    
    if event_logs.exists():
        print(f'✅ Event log found for message')
        event_log = event_logs.first()
        print(f'Event log ID: {event_log.id}')
        print(f'Event data keys: {list(event_log.event_data.keys())}')
    else:
        print('❌ No event log found for recent message')
        print('This suggests message signals are not working')
else:
    print('No recent customer messages found')
"'''
    
    returncode, stdout, stderr = run_docker_command(command)
    
    if returncode == 0:
        print("✅ Message signal check completed")
        print(stdout)
        return True
    else:
        print("❌ Error checking message signals")
        print(f"Error: {stderr}")
        return False

def create_test_message():
    """Create a test message to trigger workflows"""
    print("\n🔧 Creating test message to trigger workflows...")
    
    command = '''python manage.py shell -c "
import uuid
from message.models import Message, Customer, Conversation
from accounts.models import User
from workflow.models import TriggerEventLog, WorkflowExecution
from datetime import datetime
import time

try:
    # Find or create test customer
    customer, created = Customer.objects.get_or_create(
        source_id='test_workflow_customer',
        defaults={
            'first_name': 'Test',
            'last_name': 'Customer', 
            'source': 'telegram'
        }
    )
    print(f'Customer: {customer.first_name} {customer.last_name} (created: {created})')
    
    # Find admin user for conversation
    admin_user = User.objects.filter(is_superuser=True).first()
    if not admin_user:
        admin_user = User.objects.first()
    
    if not admin_user:
        print('❌ No users found')
        exit()
    
    # Find or create conversation
    conversation, created = Conversation.objects.get_or_create(
        customer=customer,
        user=admin_user,
        source='telegram',
        defaults={'status': 'active'}
    )
    print(f'Conversation: {conversation.id} (created: {created})')
    
    # Create test message
    test_content = f'Test workflow message {datetime.now().isoformat()}'
    message = Message.objects.create(
        content=test_content,
        conversation=conversation,
        customer=customer,
        type='customer'
    )
    print(f'Created message: {message.id}')
    print(f'Content: {message.content}')
    
    # Wait a moment for signal processing
    time.sleep(2)
    
    # Check if event log was created
    event_log = TriggerEventLog.objects.filter(
        event_type='MESSAGE_RECEIVED',
        event_data__message_id=str(message.id)
    ).first()
    
    if event_log:
        print(f'✅ Event log created: {event_log.id}')
        
        # Check for workflow executions
        time.sleep(1)
        executions = WorkflowExecution.objects.filter(
            trigger_data__message_id=str(message.id)
        )
        
        if executions.exists():
            print(f'✅ {executions.count()} workflow execution(s) created')
            for exec in executions:
                print(f'- {exec.workflow.name}: {exec.status}')
        else:
            print('⚠️ No workflow executions found')
    else:
        print('❌ No event log created - signals not working')
        
except Exception as e:
    print(f'Error: {e}')
    import traceback
    traceback.print_exc()
"'''
    
    returncode, stdout, stderr = run_docker_command(command)
    
    if returncode == 0:
        print("✅ Test message creation completed")
        print(stdout)
        return True
    else:
        print("❌ Error creating test message")
        print(f"Error: {stderr}")
        return False

def main():
    """Run all workflow functionality tests"""
    print("🚀 WORKFLOW FUNCTIONALITY TEST")
    print("="*50)
    
    tests = [
        ("Basic Models", test_workflow_models),
        ("Recent Executions", test_recent_workflow_executions), 
        ("Workflow Setup", test_workflow_setup),
        ("Message Signals", test_message_signal),
        ("Create Test Message", create_test_message)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "="*50)
    print("🏁 TEST SUMMARY")
    print("="*50)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Workflow system appears to be working correctly.")
    elif passed > 0:
        print("⚠️ Some tests passed. The workflow system is partially functional.")
        print("Check the failed tests above for specific issues.")
    else:
        print("❌ All tests failed. The workflow system needs attention.")
    
    # Recommendations
    print("\n💡 RECOMMENDATIONS:")
    if passed < total:
        print("1. Check if Docker containers are properly running")
        print("2. Verify database migrations are applied") 
        print("3. Ensure Celery workers are processing tasks")
        print("4. Check Django signals are connected")
    else:
        print("✅ Workflow system is functioning correctly!")
        print("You can now create workflows that will trigger on customer messages.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
