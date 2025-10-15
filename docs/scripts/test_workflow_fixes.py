#!/usr/bin/env python
"""
Test script to validate workflow fixes and execution
"""

import os
import sys
import django
import json
from datetime import datetime

# Setup Django
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.development')
django.setup()

from workflow.models import (
    Workflow, Trigger, TriggerWorkflowAssociation, WorkflowAction, Action,
    TriggerEventLog, WorkflowExecution
)
from workflow.utils.debug_utilities import WorkflowDebugger
from workflow.services.trigger_service import TriggerService
from message.models import Message, Customer, Conversation
from accounts.models import User


def print_header(title):
    """Print a formatted header"""
    print("\n" + "="*60)
    print(f"🔍 {title}")
    print("="*60)


def print_status(message, status="info"):
    """Print a status message with emoji"""
    emoji_map = {
        "success": "✅",
        "error": "❌", 
        "warning": "⚠️",
        "info": "ℹ️"
    }
    print(f"{emoji_map.get(status, 'ℹ️')} {message}")


def test_workflow_setup():
    """Test basic workflow setup"""
    print_header("Testing Workflow Setup")
    
    setup_status = WorkflowDebugger.check_workflow_setup()
    
    print(f"Total Workflows: {setup_status['total_workflows']}")
    print(f"Active Workflows: {setup_status['active_workflows']}")
    print(f"Total Triggers: {setup_status['total_triggers']}")
    print(f"Active Triggers: {setup_status['active_triggers']}")
    print(f"Trigger-Workflow Associations: {setup_status['trigger_workflow_associations']}")
    
    if setup_status['issues']:
        print_status("Issues found:", "warning")
        for issue in setup_status['issues']:
            print(f"  - {issue}")
    else:
        print_status("No setup issues found", "success")
    
    return len(setup_status['issues']) == 0


def test_event_simulation():
    """Test event simulation"""
    print_header("Testing Event Simulation")
    
    # Simulate a message received event
    event_data = {
        'message_id': 'test_123',
        'content': 'Hello, I need help',
        'source': 'telegram',
        'timestamp': datetime.now().isoformat()
    }
    
    result = WorkflowDebugger.simulate_trigger_event(
        event_type='MESSAGE_RECEIVED',
        event_data=event_data,
        user_id='test_user_123',
        conversation_id='test_conv_123'
    )
    
    print(f"Event Type: {result['event_type']}")
    print(f"Matching Workflows: {result['workflow_count']}")
    
    if result['workflow_count'] > 0:
        print_status(f"Found {result['workflow_count']} matching workflows", "success")
        for workflow in result['matching_workflows']:
            print(f"  - {workflow['workflow_name']} (Priority: {workflow['priority']})")
    else:
        print_status("No workflows matched the event", "warning")
        print("This could indicate:")
        print("  - No active workflows")
        print("  - No trigger-workflow associations")
        print("  - Trigger filters not matching")
    
    # Print context structure
    context_keys = list(result['context'].keys())
    print(f"Context keys available: {context_keys}")
    
    return result['workflow_count'] > 0


def test_recent_executions():
    """Test recent execution statistics"""
    print_header("Testing Recent Executions")
    
    stats = WorkflowDebugger.get_recent_execution_stats(hours=24)
    
    print(f"Total Executions (24h): {stats['total_executions']}")
    
    if stats['by_status']:
        print("Status Breakdown:")
        for status, count in stats['by_status'].items():
            print(f"  - {status}: {count}")
    
    if stats['by_workflow']:
        print("Workflow Breakdown:")
        for workflow, count in stats['by_workflow'].items():
            print(f"  - {workflow}: {count}")
    
    if stats['failed_executions']:
        print_status(f"Found {len(stats['failed_executions'])} failed executions", "warning")
        for failed in stats['failed_executions'][:3]:  # Show first 3
            print(f"  - {failed['workflow']}: {failed['error'][:100]}...")
    
    return stats['total_executions'] > 0


def test_workflow_conditions():
    """Test workflow condition evaluation"""
    print_header("Testing Workflow Conditions")
    
    # Find an active workflow to test
    workflow = Workflow.objects.filter(status='ACTIVE').first()
    
    if not workflow:
        print_status("No active workflows found to test", "error")
        return False
    
    # Create test context
    test_context = {
        'event': {
            'type': 'MESSAGE_RECEIVED',
            'data': {
                'content': 'hello world',
                'message_id': 'test123',
                'source': 'telegram'
            },
            'user_id': 'test_user',
            'conversation_id': 'test_conv'
        },
        'user': {
            'id': 'test_user',
            'first_name': 'Test',
            'last_name': 'User',
            'source': 'telegram',
            'tags': ['new_customer']
        },
        'message_content': 'hello world',
        'message_content_lower': 'hello world'
    }
    
    result = WorkflowDebugger.test_workflow_conditions(str(workflow.id), test_context)
    
    print(f"Testing workflow: {result['workflow_name']}")
    print(f"Workflow active: {result['workflow_active']}")
    
    if result.get('triggers'):
        print(f"Triggers tested: {len(result['triggers'])}")
        for trigger in result['triggers']:
            print(f"  - {trigger['trigger_name']}: filters_pass={trigger['filters_pass']}")
    
    if result.get('actions'):
        print(f"Actions tested: {len(result['actions'])}")
        for action in result['actions']:
            print(f"  - {action['action_name']}: condition_pass={action['condition_pass']}")
    
    return True


def test_message_to_workflow_flow():
    """Test the complete message to workflow flow"""
    print_header("Testing Message-to-Workflow Flow")
    
    try:
        # Find or create test customer
        customer, created = Customer.objects.get_or_create(
            source_id='test_debug_customer_flow',
            defaults={
                'first_name': 'Test',
                'last_name': 'Customer',
                'source': 'telegram'
            }
        )
        
        if created:
            print_status("Created test customer", "info")
        
        # Find admin user
        admin_user = User.objects.filter(is_superuser=True).first()
        if not admin_user:
            print_status("No admin user found - cannot create conversation", "error")
            return False
        
        # Find or create test conversation
        conversation, created = Conversation.objects.get_or_create(
            customer=customer,
            user=admin_user,
            source='telegram',
            defaults={
                'status': 'active'
            }
        )
        
        if created:
            print_status("Created test conversation", "info")
        
        # Create test message (this should trigger workflows)
        test_content = f"Test message for workflow validation {datetime.now().isoformat()}"
        message = Message.objects.create(
            content=test_content,
            conversation=conversation,
            customer=customer,
            type='customer'
        )
        
        print_status(f"Created test message: {message.id}", "success")
        
        # Wait a moment for async processing
        import time
        time.sleep(2)
        
        # Check if event log was created
        event_log = TriggerEventLog.objects.filter(
            event_type='MESSAGE_RECEIVED',
            event_data__message_id=str(message.id)
        ).first()
        
        if event_log:
            print_status(f"Event log created: {event_log.id}", "success")
            
            # Check for workflow executions
            executions = WorkflowExecution.objects.filter(
                trigger_data__message_id=str(message.id)
            ).order_by('-created_at')
            
            if executions.exists():
                print_status(f"Found {executions.count()} workflow execution(s)", "success")
                for execution in executions:
                    print(f"  - {execution.workflow.name}: {execution.status}")
                    if execution.error_message:
                        print(f"    Error: {execution.error_message}")
            else:
                print_status("No workflow executions found", "warning")
                print("This could mean:")
                print("  - No workflows matched the trigger")
                print("  - Trigger conditions not met")
                print("  - Celery workers not processing tasks")
                
                # Test trigger matching manually
                trigger_service = TriggerService()
                workflows = trigger_service.process_event_get_workflows(event_log)
                print(f"Manual trigger check found {len(workflows)} matching workflows")
                
        else:
            print_status("No event log created - signal handler not working", "error")
            return False
        
        return True
        
    except Exception as e:
        print_status(f"Error in message flow test: {e}", "error")
        return False


def test_problematic_workflows():
    """Test for problematic workflow configurations"""
    print_header("Checking for Problematic Workflows")
    
    problems = WorkflowDebugger.find_problematic_workflows()
    
    total_problems = sum(len(v) for v in problems.values())
    
    if total_problems == 0:
        print_status("No problematic workflows found", "success")
        return True
    
    print_status(f"Found {total_problems} workflow configuration issues", "warning")
    
    for problem_type, items in problems.items():
        if items:
            print(f"\n{problem_type.replace('_', ' ').title()}:")
            for item in items:
                if 'name' in item:
                    print(f"  - {item['name']} (ID: {item['id']})")
                else:
                    print(f"  - {item}")
    
    return False


def run_all_tests():
    """Run all tests"""
    print_header("WORKFLOW SYSTEM VALIDATION TESTS")
    print(f"Test started at: {datetime.now()}")
    
    tests = [
        ("Workflow Setup", test_workflow_setup),
        ("Event Simulation", test_event_simulation),
        ("Recent Executions", test_recent_executions),
        ("Workflow Conditions", test_workflow_conditions),
        ("Message-to-Workflow Flow", test_message_to_workflow_flow),
        ("Problematic Workflows", test_problematic_workflows),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print_status(f"Error in {test_name}: {e}", "error")
            results[test_name] = False
    
    # Summary
    print_header("TEST SUMMARY")
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    for test_name, result in results.items():
        status = "success" if result else "error"
        print_status(f"{test_name}: {'PASSED' if result else 'FAILED'}", status)
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print_status("All tests passed! Workflow system is working correctly.", "success")
    else:
        print_status("Some tests failed. Check the output above for details.", "warning")
        print("\nRecommended actions:")
        print("1. Run: python manage.py fix_workflow_issues --fix-all")
        print("2. Check Celery workers are running")
        print("3. Verify database migrations are applied")
        print("4. Check Django signals are connected")
    
    return passed == total


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
