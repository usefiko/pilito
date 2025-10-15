"""
Django management command to automatically fix common workflow issues
"""

import logging
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from workflow.models import (
    Workflow, Trigger, TriggerWorkflowAssociation, WorkflowAction, Action,
    TriggerEventLog, WorkflowExecution
)
from workflow.utils.debug_utilities import WorkflowDebugger

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Automatically fix common workflow execution issues'

    def add_arguments(self, parser):
        parser.add_argument(
            '--activate-workflows',
            action='store_true',
            help='Activate workflows that are in DRAFT status but have triggers and actions'
        )
        parser.add_argument(
            '--create-missing-associations',
            action='store_true',
            help='Create trigger-workflow associations for MESSAGE_RECEIVED triggers'
        )
        parser.add_argument(
            '--cleanup-failed-executions',
            action='store_true',
            help='Clean up old failed workflow executions'
        )
        parser.add_argument(
            '--fix-all',
            action='store_true',
            help='Apply all available fixes'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be fixed without making changes'
        )

    def handle(self, *args, **options):
        self.dry_run = options['dry_run']
        
        if self.dry_run:
            self.stdout.write(self.style.WARNING('🔍 DRY RUN MODE - No changes will be made'))
        
        self.stdout.write(self.style.SUCCESS('🔧 Starting workflow issue fixes...'))
        
        # Check current state
        setup_status = WorkflowDebugger.check_workflow_setup()
        self.display_current_status(setup_status)
        
        # Apply fixes
        if options['activate_workflows'] or options['fix_all']:
            self.fix_inactive_workflows()
        
        if options['create_missing_associations'] or options['fix_all']:
            self.fix_missing_associations()
        
        if options['cleanup_failed_executions'] or options['fix_all']:
            self.cleanup_failed_executions()
        
        # Check status after fixes
        self.stdout.write('\n' + '='*50)
        self.stdout.write(self.style.SUCCESS('📊 Status after fixes:'))
        setup_status_after = WorkflowDebugger.check_workflow_setup()
        self.display_current_status(setup_status_after)
        
        self.stdout.write(self.style.SUCCESS('✅ Workflow fixes completed!'))

    def display_current_status(self, status):
        """Display current workflow system status"""
        self.stdout.write(f'📈 Workflows: {status["active_workflows"]}/{status["total_workflows"]} active')
        self.stdout.write(f'🎯 Triggers: {status["active_triggers"]}/{status["total_triggers"]} active')
        self.stdout.write(f'⚡ Actions: {status["active_actions"]}/{status["total_actions"]} active')
        self.stdout.write(f'🔗 Associations: {status["trigger_workflow_associations"]}')
        self.stdout.write(f'📋 Workflow Actions: {status["workflow_actions"]}')
        
        if status['issues']:
            self.stdout.write(self.style.ERROR('\n❌ Issues found:'))
            for issue in status['issues']:
                self.stdout.write(f'  - {issue}')
        
        if status['recommendations']:
            self.stdout.write(self.style.WARNING('\n💡 Recommendations:'))
            for rec in status['recommendations']:
                self.stdout.write(f'  - {rec}')

    def fix_inactive_workflows(self):
        """Activate workflows that have proper setup but are inactive"""
        self.stdout.write('\n🔄 Checking for workflows to activate...')
        
        # Find workflows that:
        # 1. Are in DRAFT status
        # 2. Have actions configured
        # 3. Have trigger associations
        inactive_workflows = Workflow.objects.filter(
            status='DRAFT'
        ).exclude(
            workflow_actions__isnull=True
        ).exclude(
            trigger_associations__isnull=True
        ).distinct()
        
        if not inactive_workflows.exists():
            self.stdout.write('  ✅ No workflows need activation')
            return
        
        activated_count = 0
        for workflow in inactive_workflows:
            action_count = workflow.workflow_actions.count()
            trigger_count = workflow.trigger_associations.filter(is_active=True).count()
            
            if action_count > 0 and trigger_count > 0:
                self.stdout.write(f'  🟢 Activating: {workflow.name} ({action_count} actions, {trigger_count} triggers)')
                
                if not self.dry_run:
                    workflow.status = 'ACTIVE'
                    workflow.save()
                
                activated_count += 1
        
        if activated_count > 0:
            self.stdout.write(self.style.SUCCESS(f'  ✅ Activated {activated_count} workflows'))
        else:
            self.stdout.write('  ℹ️  No workflows needed activation')

    def fix_missing_associations(self):
        """Create missing trigger-workflow associations"""
        self.stdout.write('\n🔗 Checking for missing trigger-workflow associations...')
        
        # Find MESSAGE_RECEIVED triggers without associations
        message_triggers = Trigger.objects.filter(
            trigger_type='MESSAGE_RECEIVED',
            is_active=True,
            workflow_associations__isnull=True
        )
        
        # Find active workflows without trigger associations
        workflows_without_triggers = Workflow.objects.filter(
            status='ACTIVE',
            trigger_associations__isnull=True
        ).exclude(
            workflow_actions__isnull=True
        )
        
        if not message_triggers.exists() or not workflows_without_triggers.exists():
            self.stdout.write('  ✅ No missing associations to create')
            return
        
        associations_created = 0
        
        # Create associations between message triggers and workflows
        for trigger in message_triggers:
            for workflow in workflows_without_triggers:
                # Check if association already exists
                existing = TriggerWorkflowAssociation.objects.filter(
                    trigger=trigger,
                    workflow=workflow
                ).exists()
                
                if not existing:
                    self.stdout.write(f'  🔗 Creating association: {trigger.name} → {workflow.name}')
                    
                    if not self.dry_run:
                        TriggerWorkflowAssociation.objects.create(
                            trigger=trigger,
                            workflow=workflow,
                            priority=100,
                            specific_conditions={},
                            is_active=True
                        )
                    
                    associations_created += 1
        
        if associations_created > 0:
            self.stdout.write(self.style.SUCCESS(f'  ✅ Created {associations_created} associations'))
        else:
            self.stdout.write('  ℹ️  No associations needed to be created')

    def cleanup_failed_executions(self):
        """Clean up old failed workflow executions"""
        self.stdout.write('\n🧹 Cleaning up old failed executions...')
        
        # Delete failed executions older than 7 days
        from datetime import timedelta
        cutoff_date = timezone.now() - timedelta(days=7)
        
        old_failed_executions = WorkflowExecution.objects.filter(
            status='FAILED',
            created_at__lt=cutoff_date
        )
        
        count = old_failed_executions.count()
        
        if count == 0:
            self.stdout.write('  ✅ No old failed executions to clean up')
            return
        
        self.stdout.write(f'  🗑️  Deleting {count} failed executions older than 7 days')
        
        if not self.dry_run:
            old_failed_executions.delete()
        
        self.stdout.write(self.style.SUCCESS(f'  ✅ Cleaned up {count} failed executions'))

    def create_sample_workflow_if_empty(self):
        """Create a sample workflow if the system is completely empty"""
        self.stdout.write('\n🆕 Checking if sample workflow is needed...')
        
        active_workflows = Workflow.objects.filter(status='ACTIVE').count()
        active_triggers = Trigger.objects.filter(is_active=True).count()
        associations = TriggerWorkflowAssociation.objects.filter(is_active=True).count()
        
        if active_workflows > 0 and active_triggers > 0 and associations > 0:
            self.stdout.write('  ✅ System already has active workflows')
            return
        
        self.stdout.write('  🔧 Creating sample workflow for testing...')
        
        if self.dry_run:
            self.stdout.write('  📝 Would create sample workflow, trigger, and associations')
            return
        
        try:
            with transaction.atomic():
                # Create trigger
                trigger, created = Trigger.objects.get_or_create(
                    name='Sample Message Trigger',
                    defaults={
                        'description': 'Sample trigger for message received events',
                        'trigger_type': 'MESSAGE_RECEIVED',
                        'configuration': {},
                        'filters': {},
                        'is_active': True
                    }
                )
                
                # Create action
                action, created = Action.objects.get_or_create(
                    name='Sample Welcome Action',
                    defaults={
                        'description': 'Sample action to send welcome message',
                        'action_type': 'send_message',
                        'configuration': {
                            'message': 'Hello! Thank you for your message. We will get back to you soon.',
                            'message_type': 'support'
                        },
                        'is_active': True
                    }
                )
                
                # Create workflow
                workflow, created = Workflow.objects.get_or_create(
                    name='Sample Welcome Workflow',
                    defaults={
                        'description': 'Sample workflow to welcome new customers',
                        'status': 'ACTIVE',
                        'max_executions': 0,
                        'delay_between_executions': 0
                    }
                )
                
                # Create trigger-workflow association
                association, created = TriggerWorkflowAssociation.objects.get_or_create(
                    trigger=trigger,
                    workflow=workflow,
                    defaults={
                        'priority': 100,
                        'specific_conditions': {},
                        'is_active': True
                    }
                )
                
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
                
                self.stdout.write(self.style.SUCCESS('  ✅ Created sample workflow system'))
                self.stdout.write(f'    Trigger: {trigger.name}')
                self.stdout.write(f'    Workflow: {workflow.name}')
                self.stdout.write(f'    Action: {action.name}')
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'  ❌ Error creating sample workflow: {e}'))
