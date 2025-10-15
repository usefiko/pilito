"""
Management command to initialize the workflow system
This should be run after migrations to set up event types and system defaults
"""

from django.core.management.base import BaseCommand
from workflow.services.trigger_service import TriggerService


class Command(BaseCommand):
    help = 'Initialize workflow system by registering event types and setting up defaults'
    
    def handle(self, *args, **options):
        self.stdout.write('🚀 Initializing Marketing Workflow System...')
        
        # Register common event types
        self.stdout.write('📝 Registering common event types...')
        count = TriggerService.register_common_event_types()
        
        if count > 0:
            self.stdout.write(
                self.style.SUCCESS(f'✅ Registered {count} new event types')
            )
        else:
            self.stdout.write(
                self.style.WARNING('ℹ️  All event types already exist')
            )
        
        self.stdout.write()
        self.stdout.write(
            self.style.SUCCESS(
                '🎉 Workflow system initialization complete!\n\n'
                'Next steps:\n'
                '1. Run "python manage.py setup_sample_workflows" for demo data\n'
                '2. Access admin at /admin/ to manage workflows\n'
                '3. Use API at /api/v1/workflow/api/ for integration'
            )
        )
