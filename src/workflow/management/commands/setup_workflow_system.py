"""
Management command to set up and fix the workflow system
"""

import logging
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction

from workflow.services.trigger_service import TriggerService
from workflow.models import EventType, Trigger, Workflow, TriggerWorkflowAssociation

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Set up and fix the workflow system'

    def add_arguments(self, parser):
        parser.add_argument(
            '--register-events',
            action='store_true',
            help='Register common event types',
        )
        parser.add_argument(
            '--check-signals',
            action='store_true',
            help='Check if signals are properly connected',
        )
        parser.add_argument(
            '--test-workflow',
            type=str,
            help='Test a specific workflow by ID',
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('Setting up workflow system...')
        )

        try:
            # Register common event types
            if options.get('register_events'):
                self.register_event_types()

            # Check signal connections
            if options.get('check_signals'):
                self.check_signal_connections()

            # Test specific workflow
            if options.get('test_workflow'):
                self.test_workflow(options['test_workflow'])

            # Always run system health check
            self.check_system_health()

            self.stdout.write(
                self.style.SUCCESS('Workflow system setup completed successfully!')
            )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error setting up workflow system: {e}')
            )
            logger.error(f"Workflow system setup failed: {e}", exc_info=True)

    def register_event_types(self):
        """Register common event types"""
        self.stdout.write('Registering common event types...')
        
        created_count = TriggerService.register_common_event_types()
        
        self.stdout.write(
            self.style.SUCCESS(f'Registered {created_count} new event types')
        )

    def check_signal_connections(self):
        """Check if Django signals are properly connected"""
        self.stdout.write('Checking signal connections...')
        
        try:
            # Import the signals module to ensure decorators are processed
            from workflow import signals
            
            # Test signal import
            from django.db.models.signals import post_save
            
            # Check if our signal handlers are connected
            connected_handlers = []
            for receiver in post_save._live_receivers(sender=None):
                if hasattr(receiver, '__module__') and 'workflow.signals' in str(receiver.__module__):
                    connected_handlers.append(str(receiver))
            
            if connected_handlers:
                self.stdout.write(
                    self.style.SUCCESS(f'Found {len(connected_handlers)} workflow signal handlers connected')
                )
                for handler in connected_handlers:
                    self.stdout.write(f'  - {handler}')
            else:
                self.stdout.write(
                    self.style.WARNING('No workflow signal handlers found - signals may not be connected')
                )
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error checking signal connections: {e}')
            )

    def test_workflow(self, workflow_id):
        """Test a specific workflow"""
        self.stdout.write(f'Testing workflow {workflow_id}...')
        
        try:
            workflow = Workflow.objects.get(id=workflow_id)
            
            # Check if workflow is active
            if not workflow.is_active():
                self.stdout.write(
                    self.style.WARNING(f'Workflow "{workflow.name}" is not active')
                )
                return
            
            # Check triggers
            triggers = Trigger.objects.filter(
                workflow_associations__workflow=workflow,
                is_active=True
            ).distinct()
            
            self.stdout.write(f'Workflow "{workflow.name}" has {triggers.count()} active triggers')
            
            for trigger in triggers:
                self.stdout.write(f'  - {trigger.name} ({trigger.trigger_type})')
            
            # Check actions
            workflow_actions = workflow.workflow_actions.all().order_by('order')
            self.stdout.write(f'Workflow has {workflow_actions.count()} actions')
            
            for wa in workflow_actions:
                self.stdout.write(f'  - {wa.order}: {wa.action.name} ({wa.action.action_type})')
            
            self.stdout.write(
                self.style.SUCCESS(f'Workflow "{workflow.name}" test completed')
            )
            
        except Workflow.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'Workflow with ID {workflow_id} not found')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error testing workflow: {e}')
            )

    def check_system_health(self):
        """Check overall system health"""
        self.stdout.write('Checking workflow system health...')
        
        try:
            # Check event types
            event_types = EventType.objects.filter(is_active=True).count()
            self.stdout.write(f'Active event types: {event_types}')
            
            # Check triggers
            active_triggers = Trigger.objects.filter(is_active=True).count()
            self.stdout.write(f'Active triggers: {active_triggers}')
            
            # Check workflows
            active_workflows = Workflow.objects.filter(status='ACTIVE').count()
            self.stdout.write(f'Active workflows: {active_workflows}')
            
            # Check associations
            active_associations = TriggerWorkflowAssociation.objects.filter(
                is_active=True,
                trigger__is_active=True,
                workflow__status='ACTIVE'
            ).count()
            self.stdout.write(f'Active trigger-workflow associations: {active_associations}')
            
            # Check recent executions
            from workflow.models import WorkflowExecution
            recent_executions = WorkflowExecution.objects.filter(
                created_at__gte=timezone.now() - timezone.timedelta(hours=24)
            ).count()
            self.stdout.write(f'Workflow executions in last 24 hours: {recent_executions}')
            
            # Check for failed executions
            failed_executions = WorkflowExecution.objects.filter(
                status='FAILED',
                created_at__gte=timezone.now() - timezone.timedelta(hours=24)
            ).count()
            
            if failed_executions > 0:
                self.stdout.write(
                    self.style.WARNING(f'Failed executions in last 24 hours: {failed_executions}')
                )
            
            # Check Celery imports
            try:
                from django.conf import settings
                celery_imports = getattr(settings, 'CELERY_IMPORTS', [])
                if 'workflow.tasks' in celery_imports:
                    self.stdout.write(
                        self.style.SUCCESS('Workflow tasks are configured in Celery imports')
                    )
                else:
                    self.stdout.write(
                        self.style.ERROR('Workflow tasks are NOT configured in Celery imports')
                    )
            except Exception as e:
                self.stdout.write(
                    self.style.WARNING(f'Could not check Celery configuration: {e}')
                )
            
            self.stdout.write(
                self.style.SUCCESS('System health check completed')
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error during health check: {e}')
            )
