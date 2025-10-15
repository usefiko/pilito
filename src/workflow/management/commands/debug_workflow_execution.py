"""
Django management command to debug workflow execution issues
"""

import logging
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from workflow.models import (
    Workflow, Trigger, TriggerWorkflowAssociation, WorkflowAction, Action,
    TriggerEventLog, WorkflowExecution, WorkflowActionExecution
)
from workflow.services.trigger_service import TriggerService
from workflow.tasks import process_event
from message.models import Message, Customer, Conversation

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Debug workflow execution issues and provide diagnostics'

    def add_arguments(self, parser):
        parser.add_argument(
            '--check-associations',
            action='store_true',
            help='Check trigger-workflow associations'
        )
        parser.add_argument(
            '--check-workflows',
            action='store_true',
            help='Check workflow configurations'
        )
        parser.add_argument(
            '--test-message-flow',
            action='store_true',
            help='Test message-to-workflow flow'
        )
        parser.add_argument(
            '--create-test-data',
            action='store_true',
            help='Create test workflow, trigger, and associations'
        )
        parser.add_argument(
            '--check-recent-executions',
            action='store_true',
            help='Check recent workflow executions'
        )
        parser.add_argument(
            '--simulate-message',
            type=str,
            help='Simulate a customer message with the given content'
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting workflow execution diagnostics...'))

        if options['check_associations']:
            self.check_trigger_workflow_associations()

        if options['check_workflows']:
            self.check_workflow_configurations()

        if options['test_message_flow']:
            self.test_message_to_workflow_flow()

        if options['create_test_data']:
            self.create_test_workflow_data()

        if options['check_recent_executions']:
            self.check_recent_executions()

        if options['simulate_message']:
            self.simulate_customer_message(options['simulate_message'])

        self.stdout.write(self.style.SUCCESS('Diagnostics completed!'))

    def check_trigger_workflow_associations(self):
        """Check if triggers are properly associated with workflows"""
        self.stdout.write('\n=== CHECKING TRIGGER-WORKFLOW ASSOCIATIONS ===')
        
        total_triggers = Trigger.objects.filter(is_active=True).count()
        total_workflows = Workflow.objects.filter(status='ACTIVE').count()
        total_associations = TriggerWorkflowAssociation.objects.filter(is_active=True).count()
        
        self.stdout.write(f'Active Triggers: {total_triggers}')
        self.stdout.write(f'Active Workflows: {total_workflows}')
        self.stdout.write(f'Active Associations: {total_associations}')
        
        if total_associations == 0:
            self.stdout.write(self.style.ERROR('❌ NO TRIGGER-WORKFLOW ASSOCIATIONS FOUND!'))
            self.stdout.write('This is likely the main issue. Workflows won\'t execute without associations.')
        else:
            self.stdout.write(self.style.SUCCESS(f'✅ Found {total_associations} associations'))
        
        # Show details of associations
        associations = TriggerWorkflowAssociation.objects.filter(is_active=True).select_related(
            'trigger', 'workflow'
        )
        for assoc in associations:
            self.stdout.write(f'  - {assoc.trigger.name} → {assoc.workflow.name} (Priority: {assoc.priority})')

    def check_workflow_configurations(self):
        """Check workflow configurations and status"""
        self.stdout.write('\n=== CHECKING WORKFLOW CONFIGURATIONS ===')
        
        workflows = Workflow.objects.all()
        
        for workflow in workflows:
            self.stdout.write(f'\nWorkflow: {workflow.name}')
            self.stdout.write(f'  Status: {workflow.status}')
            self.stdout.write(f'  Active: {workflow.is_active()}')
            
            # Check if it has actions
            action_count = workflow.workflow_actions.count()
            self.stdout.write(f'  Actions: {action_count}')
            
            # Check if it has trigger associations
            trigger_count = workflow.trigger_associations.filter(is_active=True).count()
            self.stdout.write(f'  Trigger Associations: {trigger_count}')
            
            if workflow.status != 'ACTIVE':
                self.stdout.write(self.style.WARNING(f'  ⚠️  Workflow is in {workflow.status} status (should be ACTIVE)'))
            
            if action_count == 0:
                self.stdout.write(self.style.ERROR(f'  ❌ No actions configured'))
            
            if trigger_count == 0:
                self.stdout.write(self.style.ERROR(f'  ❌ No trigger associations'))

    def test_message_to_workflow_flow(self):
        """Test the complete flow from message to workflow execution"""
        self.stdout.write('\n=== TESTING MESSAGE-TO-WORKFLOW FLOW ===')
        
        # Find a recent customer message
        recent_message = Message.objects.filter(type='customer').order_by('-created_at').first()
        
        if not recent_message:
            self.stdout.write(self.style.ERROR('❌ No customer messages found to test'))
            return
        
        self.stdout.write(f'Testing with message: {recent_message.content[:50]}...')
        
        # Check if event log was created for this message
        event_logs = TriggerEventLog.objects.filter(
            event_type='MESSAGE_RECEIVED',
            event_data__message_id=str(recent_message.id)
        )
        
        if not event_logs.exists():
            self.stdout.write(self.style.ERROR('❌ No event log found for this message'))
            self.stdout.write('This suggests the signal handler is not working')
        else:
            event_log = event_logs.first()
            self.stdout.write(f'✅ Event log found: {event_log.id}')
            
            # Check if workflows were triggered
            trigger_service = TriggerService()
            workflows = trigger_service.process_event_get_workflows(event_log)
            
            if not workflows:
                self.stdout.write(self.style.ERROR('❌ No workflows matched this event'))
                self.stdout.write('Check trigger conditions and associations')
            else:
                self.stdout.write(f'✅ {len(workflows)} workflows matched')
                for wf in workflows:
                    self.stdout.write(f'  - {wf["workflow_name"]} (Priority: {wf["priority"]})')

    def check_recent_executions(self):
        """Check recent workflow executions"""
        self.stdout.write('\n=== CHECKING RECENT WORKFLOW EXECUTIONS ===')
        
        # Check executions from last 24 hours
        from datetime import timedelta
        cutoff = timezone.now() - timedelta(hours=24)
        
        recent_executions = WorkflowExecution.objects.filter(
            created_at__gte=cutoff
        ).order_by('-created_at')
        
        if not recent_executions.exists():
            self.stdout.write(self.style.ERROR('❌ No workflow executions in the last 24 hours'))
        else:
            self.stdout.write(f'✅ Found {recent_executions.count()} executions in last 24h')
            
            for execution in recent_executions[:5]:  # Show last 5
                self.stdout.write(f'  - {execution.workflow.name}: {execution.status} ({execution.created_at})')
                
                if execution.status == 'FAILED':
                    self.stdout.write(f'    Error: {execution.error_message}')

    def create_test_workflow_data(self):
        """Create test workflow data to verify the system works"""
        self.stdout.write('\n=== CREATING TEST WORKFLOW DATA ===')
        
        try:
            with transaction.atomic():
                # Create a test trigger for message received
                trigger, created = Trigger.objects.get_or_create(
                    name='[TEST] Message Received Trigger',
                    defaults={
                        'description': 'Test trigger for debugging',
                        'trigger_type': 'MESSAGE_RECEIVED',
                        'configuration': {},
                        'filters': {},
                        'is_active': True
                    }
                )
                
                if created:
                    self.stdout.write('✅ Created test trigger')
                else:
                    self.stdout.write('ℹ️  Test trigger already exists')
                
                # Create a test action for sending message
                action, created = Action.objects.get_or_create(
                    name='[TEST] Send Welcome Message',
                    defaults={
                        'description': 'Test action for debugging',
                        'action_type': 'send_message',
                        'configuration': {
                            'message': 'Hello! This is a test message from workflow system.',
                            'message_type': 'marketing'
                        },
                        'is_active': True
                    }
                )
                
                if created:
                    self.stdout.write('✅ Created test action')
                else:
                    self.stdout.write('ℹ️  Test action already exists')
                
                # Create a test workflow
                workflow, created = Workflow.objects.get_or_create(
                    name='[TEST] Debug Workflow',
                    defaults={
                        'description': 'Test workflow for debugging execution issues',
                        'status': 'ACTIVE',  # Make sure it's active
                        'max_executions': 0,  # Unlimited
                        'delay_between_executions': 0
                    }
                )
                
                if created:
                    self.stdout.write('✅ Created test workflow')
                else:
                    workflow.status = 'ACTIVE'  # Ensure it's active
                    workflow.save()
                    self.stdout.write('ℹ️  Test workflow already exists (updated to ACTIVE)')
                
                # Create trigger-workflow association
                association, created = TriggerWorkflowAssociation.objects.get_or_create(
                    trigger=trigger,
                    workflow=workflow,
                    defaults={
                        'priority': 50,
                        'specific_conditions': {},
                        'is_active': True
                    }
                )
                
                if created:
                    self.stdout.write('✅ Created trigger-workflow association')
                else:
                    self.stdout.write('ℹ️  Trigger-workflow association already exists')
                
                # Create workflow action
                workflow_action, created = WorkflowAction.objects.get_or_create(
                    workflow=workflow,
                    action=action,
                    defaults={
                        'order': 1,
                        'is_required': True,
                        'add_result_to_context': False
                    }
                )
                
                if created:
                    self.stdout.write('✅ Created workflow action')
                else:
                    self.stdout.write('ℹ️  Workflow action already exists')
                
                self.stdout.write(self.style.SUCCESS('🎉 Test workflow data created successfully!'))
                self.stdout.write(f'    Trigger ID: {trigger.id}')
                self.stdout.write(f'    Workflow ID: {workflow.id}')
                self.stdout.write(f'    Action ID: {action.id}')
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Error creating test data: {e}'))

    def simulate_customer_message(self, content):
        """Simulate a customer message to test the complete flow"""
        self.stdout.write(f'\n=== SIMULATING CUSTOMER MESSAGE: "{content}" ===')
        
        try:
            # Find or create a test customer
            customer, created = Customer.objects.get_or_create(
                source_id='test_debug_customer',
                defaults={
                    'first_name': 'Test',
                    'last_name': 'Customer',
                    'source': 'telegram'
                }
            )
            
            if created:
                self.stdout.write('✅ Created test customer')
            
            # Find or create a test conversation
            from accounts.models import User
            admin_user = User.objects.filter(is_superuser=True).first()
            
            if not admin_user:
                self.stdout.write(self.style.ERROR('❌ No admin user found to create conversation'))
                return
            
            conversation, created = Conversation.objects.get_or_create(
                customer=customer,
                user=admin_user,
                source='telegram',
                defaults={
                    'status': 'active'
                }
            )
            
            if created:
                self.stdout.write('✅ Created test conversation')
            
            # Create the message (this should trigger the workflow)
            message = Message.objects.create(
                content=content,
                conversation=conversation,
                customer=customer,
                type='customer'
            )
            
            self.stdout.write(f'✅ Created message: {message.id}')
            
            # Wait a moment and check if event log was created
            import time
            time.sleep(1)
            
            event_log = TriggerEventLog.objects.filter(
                event_type='MESSAGE_RECEIVED',
                event_data__message_id=str(message.id)
            ).first()
            
            if event_log:
                self.stdout.write(f'✅ Event log created: {event_log.id}')
                
                # Check if any workflow executions were created
                time.sleep(2)  # Give Celery time to process
                
                executions = WorkflowExecution.objects.filter(
                    trigger_data__message_id=str(message.id)
                ).order_by('-created_at')
                
                if executions.exists():
                    self.stdout.write(f'✅ {executions.count()} workflow execution(s) created:')
                    for exec in executions:
                        self.stdout.write(f'   - {exec.workflow.name}: {exec.status}')
                else:
                    self.stdout.write(self.style.WARNING('⚠️  No workflow executions found'))
                    self.stdout.write('Check if triggers and associations are properly configured')
            else:
                self.stdout.write(self.style.ERROR('❌ No event log created'))
                self.stdout.write('The signal handler may not be working')
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Error simulating message: {e}'))
