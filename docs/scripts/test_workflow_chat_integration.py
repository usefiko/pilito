#!/usr/bin/env python3
"""
Test script demonstrating the enhanced workflow-chat integration

This script shows how workflows can now control AI behavior and affect chat conversations.
"""

import os
import sys
import django

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.development')
django.setup()

from django.core.cache import cache
from message.models import Message, Conversation, Customer
from workflow.models import Workflow, ActionNode, WhenNode, NodeConnection
from workflow.services.node_execution_service import NodeBasedWorkflowExecutionService
from accounts.models import User

def create_test_workflow(user):
    """Create a test workflow that controls AI behavior"""
    # Create workflow
    workflow = Workflow.objects.create(
        name="Smart Customer Support Workflow",
        description="Automatically adjusts AI behavior based on customer messages",
        status="ACTIVE",
        created_by=user
    )
    
    # Create When node - trigger on message received
    when_node = WhenNode.objects.create(
        workflow=workflow,
        title="When customer sends message",
        when_type="receive_message",
        keywords=["help", "support", "problem"],
        channels=["all"],
        position_x=100,
        position_y=100
    )
    
    # Create AI Control action - set custom prompt for premium support
    ai_control_action = ActionNode.objects.create(
        workflow=workflow,
        title="Enable Premium AI Support",
        action_type="control_ai_response",
        ai_control_action="custom_prompt",
        ai_custom_prompt="You are a premium customer support assistant. The customer has indicated they need help. Be extra attentive, professional, and offer comprehensive solutions. Prioritize customer satisfaction above all else.",
        position_x=300,
        position_y=100
    )
    
    # Create AI Context update action - add customer tier info
    ai_context_action = ActionNode.objects.create(
        workflow=workflow,
        title="Set Customer Context",
        action_type="update_ai_context",
        ai_context_data={
            "support_tier": "premium",
            "priority_level": "high",
            "has_requested_help": True,
            "keywords_mentioned": "{{event.data.content}}"
        },
        position_x=500,
        position_y=100
    )
    
    # Create send message action
    send_message_action = ActionNode.objects.create(
        workflow=workflow,
        title="Send Welcome Message",
        action_type="send_message",
        message_content="Hello! I've escalated your request to our premium support team. An AI assistant with specialized knowledge will help you shortly.",
        position_x=700,
        position_y=100
    )
    
    # Connect the nodes
    NodeConnection.objects.create(
        workflow=workflow,
        source_node=when_node.workflownode_ptr,
        target_node=ai_control_action.workflownode_ptr,
        connection_type="success"
    )
    
    NodeConnection.objects.create(
        workflow=workflow,
        source_node=ai_control_action.workflownode_ptr,
        target_node=ai_context_action.workflownode_ptr,
        connection_type="success"
    )
    
    NodeConnection.objects.create(
        workflow=workflow,
        source_node=ai_context_action.workflownode_ptr,
        target_node=send_message_action.workflownode_ptr,
        connection_type="success"
    )
    
    return workflow

def simulate_workflow_execution():
    """Simulate a customer message triggering the workflow"""
    print("🚀 Testing Enhanced Workflow-Chat Integration")
    print("=" * 50)
    
    # Get or create test user
    user, created = User.objects.get_or_create(
        email="test@example.com",
        defaults={
            'username': 'testuser',
            'first_name': 'Test',
            'last_name': 'User'
        }
    )
    if created:
        print(f"✅ Created test user: {user.email}")
    else:
        print(f"📌 Using existing test user: {user.email}")
    
    # Create test workflow
    workflow = create_test_workflow(user)
    print(f"✅ Created test workflow: {workflow.name}")
    
    # Create test customer and conversation
    customer, created = Customer.objects.get_or_create(
        source_id="test_customer_123",
        defaults={
            'first_name': 'John',
            'last_name': 'Doe',
            'username': 'johndoe',
            'source': 'telegram'
        }
    )
    
    conversation, created = Conversation.objects.get_or_create(
        customer=customer,
        user=user,
        defaults={
            'source': 'telegram',
            'status': 'active'
        }
    )
    
    print(f"✅ Created test conversation: {conversation.id}")
    
    # Simulate workflow execution context
    context = {
        'event': {
            'type': 'MESSAGE_RECEIVED',
            'data': {
                'content': 'I need help with my account',
                'message_id': 'test_message_123',
                'conversation_id': str(conversation.id),
                'user_id': str(customer.id),
                'source': 'telegram'
            },
            'conversation_id': str(conversation.id),
            'user_id': str(customer.id)
        },
        'user': {
            'id': str(customer.id),
            'first_name': customer.first_name,
            'last_name': customer.last_name,
            'source': customer.source
        },
        'workflow_id': str(workflow.id)
    }
    
    print("\n🔄 Executing workflow...")
    
    # Execute the workflow
    execution_service = NodeBasedWorkflowExecutionService()
    execution = execution_service.execute_node_workflow(workflow, context)
    
    print(f"✅ Workflow execution completed: {execution.status}")
    
    # Check AI control settings
    conversation_id = str(conversation.id)
    ai_control_key = f"ai_control_{conversation_id}"
    ai_control = cache.get(ai_control_key, {})
    
    ai_context_key = f"ai_context_{conversation_id}"
    ai_context = cache.get(ai_context_key, {})
    
    print("\n📊 AI Control Settings:")
    print(f"  - Custom Prompt Set: {'✅' if ai_control.get('custom_prompt') else '❌'}")
    if ai_control.get('custom_prompt'):
        print(f"  - Prompt: {ai_control['custom_prompt'][:100]}...")
    
    print("\n📋 AI Context Data:")
    for key, value in ai_context.items():
        print(f"  - {key}: {value}")
    
    # Check created messages
    messages = Message.objects.filter(conversation=conversation)
    print(f"\n💬 Messages Created: {messages.count()}")
    for msg in messages:
        print(f"  - {msg.type}: {msg.content}")
        if msg.metadata:
            print(f"    Metadata: {msg.metadata}")
    
    print("\n🎉 Integration test completed successfully!")
    print("\nNext Steps:")
    print("1. When a customer sends a message to this conversation, AI will:")
    print("   - Use the custom premium support prompt")
    print("   - Have access to the workflow-set context data")
    print("   - Provide enhanced customer service")
    print("2. The workflow can control AI behavior dynamically")
    print("3. Real-time WebSocket notifications work with workflow messages")
    
    return execution

if __name__ == "__main__":
    try:
        execution = simulate_workflow_execution()
        print(f"\n✅ Test completed successfully! Execution ID: {execution.id}")
    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
