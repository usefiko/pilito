#!/usr/bin/env python3
"""
Workflow System Diagnostic Script

This script tests the workflow system to ensure it's working correctly.
Run this script to diagnose workflow issues.
"""

import os
import sys
import django
from datetime import datetime

# Add the src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.development')
django.setup()

from django.utils import timezone
from workflow.services.trigger_service import TriggerService
from workflow.models import TriggerEventLog, Workflow, Trigger, WorkflowExecution
from workflow.tasks import process_event
from message.models import Message, Conversation, Customer


def test_signal_triggering():
    """Test if signals are properly triggering workflow events"""
    print("\n=== Testing Signal Triggering ===")
    
    try:
        # Get a recent customer message
        recent_message = Message.objects.filter(type='customer').order_by('-created_at').first()
        
        if not recent_message:
            print("❌ No customer messages found to test with")
            return False
            
        print(f"✅ Found recent customer message: {recent_message.id}")
        print(f"   Content: {recent_message.content[:50]}...")
        print(f"   Customer: {recent_message.customer.id}")
        print(f"   Conversation: {recent_message.conversation.id}")
        
        # Check if event logs were created for this message
        event_logs = TriggerEventLog.objects.filter(
            event_type='MESSAGE_RECEIVED',
            user_id=str(recent_message.customer.id),
            conversation_id=str(recent_message.conversation.id),
            created_at__gte=recent_message.created_at
        )
        
        if event_logs.exists():
            print(f"✅ Found {event_logs.count()} event log(s) for this message")
            for log in event_logs:
                print(f"   Event log: {log.id} created at {log.created_at}")
        else:
            print("❌ No event logs found - signals may not be working")
            return False
            
        return True
        
    except Exception as e:
        print(f"❌ Error testing signal triggering: {e}")
        return False


def test_trigger_matching():
    """Test if triggers are matching events correctly"""
    print("\n=== Testing Trigger Matching ===")
    
    try:
        # Get recent event logs
        recent_event_logs = TriggerEventLog.objects.filter(
            event_type='MESSAGE_RECEIVED'
        ).order_by('-created_at')[:5]
        
        if not recent_event_logs.exists():
            print("❌ No recent event logs found")
            return False
            
        print(f"✅ Found {recent_event_logs.count()} recent event logs")
        
        for event_log in recent_event_logs:
            print(f"\n--- Testing event log {event_log.id} ---")
            
            # Test trigger matching
            workflows = TriggerService.process_event_get_workflows(event_log)
            
            if workflows:
                print(f"✅ Found {len(workflows)} matching workflows:")
                for workflow_info in workflows:
                    print(f"   - {workflow_info['workflow_name']} (Priority: {workflow_info['priority']})")
            else:
                print("⚠️  No workflows matched this event")
                
                # Check if there are any active MESSAGE_RECEIVED triggers
                message_triggers = Trigger.objects.filter(
                    trigger_type='MESSAGE_RECEIVED',
                    is_active=True
                )
                print(f"   Available MESSAGE_RECEIVED triggers: {message_triggers.count()}")
                
                for trigger in message_triggers:
                    print(f"   - {trigger.name}")
                    
                    # Check if trigger has workflow associations
                    associations = trigger.workflow_associations.filter(
                        is_active=True,
                        workflow__status='ACTIVE'
                    )
                    print(f"     Active associations: {associations.count()}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing trigger matching: {e}")
        return False


def test_workflow_execution():
    """Test workflow execution"""
    print("\n=== Testing Workflow Execution ===")
    
    try:
        # Get recent workflow executions
        recent_executions = WorkflowExecution.objects.order_by('-created_at')[:10]
        
        if not recent_executions.exists():
            print("❌ No workflow executions found")
            return False
            
        print(f"✅ Found {recent_executions.count()} recent workflow executions")
        
        status_counts = {}
        for execution in recent_executions:
            status = execution.status
            status_counts[status] = status_counts.get(status, 0) + 1
            
            print(f"   - {execution.workflow.name}: {status} ({execution.created_at})")
            
            if execution.status == 'FAILED':
                print(f"     Error: {execution.error_message}")
        
        print(f"\nStatus summary: {status_counts}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing workflow execution: {e}")
        return False


def test_celery_task_discovery():
    """Test if Celery can find workflow tasks"""
    print("\n=== Testing Celery Task Discovery ===")
    
    try:
        from django.conf import settings
        
        # Check Celery imports
        celery_imports = getattr(settings, 'CELERY_IMPORTS', [])
        if 'workflow.tasks' in celery_imports:
            print("✅ workflow.tasks is in CELERY_IMPORTS")
        else:
            print("❌ workflow.tasks is NOT in CELERY_IMPORTS")
            return False
            
        # Check task routes
        task_routes = getattr(settings, 'CELERY_TASK_ROUTES', {})
        workflow_routes = [route for route in task_routes.keys() if 'workflow.tasks' in route]
        
        if workflow_routes:
            print(f"✅ Found {len(workflow_routes)} workflow task routes:")
            for route in workflow_routes:
                print(f"   - {route}")
        else:
            print("❌ No workflow task routes found")
            return False
        
        # Try to import workflow tasks
        try:
            from workflow.tasks import process_event, execute_workflow_action
            print("✅ Successfully imported workflow tasks")
        except ImportError as e:
            print(f"❌ Failed to import workflow tasks: {e}")
            return False
            
        return True
        
    except Exception as e:
        print(f"❌ Error testing Celery task discovery: {e}")
        return False


def test_create_test_event():
    """Create a test event to trigger workflows"""
    print("\n=== Creating Test Event ===")
    
    try:
        # Get a customer to test with
        customer = Customer.objects.first()
        if not customer:
            print("❌ No customers found to test with")
            return False
            
        # Get or create a conversation
        conversation, created = Conversation.objects.get_or_create(
            customer=customer,
            source='test',
            defaults={'user_id': 1}  # Assume user ID 1 exists
        )
        
        if created:
            print(f"✅ Created test conversation: {conversation.id}")
        else:
            print(f"✅ Using existing conversation: {conversation.id}")
        
        # Create a test event log
        event_log = TriggerService.create_event_log(
            event_type='MESSAGE_RECEIVED',
            event_data={
                'message_id': 'test-message',
                'conversation_id': str(conversation.id),
                'user_id': str(customer.id),
                'content': 'Hello, this is a test message for workflow testing',
                'source': 'test',
                'timestamp': timezone.now().isoformat()
            },
            user_id=str(customer.id),
            conversation_id=str(conversation.id)
        )
        
        print(f"✅ Created test event log: {event_log.id}")
        
        # Test trigger matching
        workflows = TriggerService.process_event_get_workflows(event_log)
        
        if workflows:
            print(f"✅ Test event matched {len(workflows)} workflows")
            for workflow_info in workflows:
                print(f"   - {workflow_info['workflow_name']}")
        else:
            print("⚠️  Test event didn't match any workflows")
            
        # Try to process the event
        try:
            result = process_event.delay(str(event_log.id))
            print(f"✅ Queued test event processing: {result.id}")
        except Exception as e:
            print(f"❌ Failed to queue test event processing: {e}")
            
        return True
        
    except Exception as e:
        print(f"❌ Error creating test event: {e}")
        return False


def main():
    """Run all diagnostic tests"""
    print("🚀 Starting Workflow System Diagnostics")
    print("=" * 50)
    
    tests = [
        test_celery_task_discovery,
        test_signal_triggering,
        test_trigger_matching,
        test_workflow_execution,
        test_create_test_event,
    ]
    
    results = []
    
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"❌ Test {test.__name__} failed with exception: {e}")
            results.append(False)
    
    print("\n" + "=" * 50)
    print("🏁 Diagnostic Summary")
    print("=" * 50)
    
    passed = sum(results)
    total = len(results)
    
    print(f"Tests passed: {passed}/{total}")
    
    if passed == total:
        print("✅ All tests passed! Workflow system appears to be working correctly.")
    elif passed > total // 2:
        print("⚠️  Some tests failed. There may be minor issues with the workflow system.")
    else:
        print("❌ Multiple tests failed. There are significant issues with the workflow system.")
    
    print("\n📋 Next Steps:")
    if passed < total:
        print("1. Check the Django logs for detailed error messages")
        print("2. Ensure Celery workers are running: celery -A core worker")
        print("3. Verify database migrations are applied: python manage.py migrate")
        print("4. Run: python manage.py setup_workflow_system --register-events")
        print("5. Check that workflow app is properly installed in settings.INSTALLED_APPS")
    else:
        print("1. Monitor workflow executions in the Django admin")
        print("2. Check Celery logs for any task execution issues")
        print("3. Create workflows and test them with real customer messages")
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
