"""
Management command to set up sample workflows for testing and demonstration
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from workflow.models import (
    EventType, Trigger, Condition, Action, Workflow,
    TriggerWorkflowAssociation, WorkflowAction
)
from workflow.services.trigger_service import TriggerService


class Command(BaseCommand):
    help = 'Set up sample workflows for testing and demonstration'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing sample data before creating new',
        )
    
    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write(self.style.WARNING('Clearing existing sample data...'))
            Workflow.objects.filter(name__startswith='[SAMPLE]').delete()
            Action.objects.filter(name__startswith='[SAMPLE]').delete()
            Trigger.objects.filter(name__startswith='[SAMPLE]').delete()
            Condition.objects.filter(name__startswith='[SAMPLE]').delete()
        
        # Register common event types first
        self.stdout.write('Registering common event types...')
        count = TriggerService.register_common_event_types()
        if count > 0:
            self.stdout.write(self.style.SUCCESS(f'Registered {count} new event types'))
        else:
            self.stdout.write('Event types already exist')
        
        # Create sample triggers
        self.stdout.write('Creating sample triggers...')
        
        message_trigger, created = Trigger.objects.get_or_create(
            name='[SAMPLE] Message Contains Coupon Keywords',
            defaults={
                'description': 'Triggers when a message contains coupon-related keywords',
                'trigger_type': 'MESSAGE_RECEIVED',
                'filters': {
                    'operator': 'or',
                    'conditions': [
                        {'field': 'event.data.content', 'operator': 'icontains', 'value': 'کد تخفیف'},
                        {'field': 'event.data.content', 'operator': 'icontains', 'value': 'coupon'},
                        {'field': 'event.data.content', 'operator': 'icontains', 'value': 'discount'}
                    ]
                },
                'is_active': True
            }
        )
        
        welcome_trigger, created = Trigger.objects.get_or_create(
            name='[SAMPLE] New User Registration',
            defaults={
                'description': 'Triggers when a new user registers',
                'trigger_type': 'USER_CREATED',
                'filters': {},
                'is_active': True
            }
        )
        
        # Create sample conditions
        self.stdout.write('Creating sample conditions...')
        
        user_interested_condition, created = Condition.objects.get_or_create(
            name='[SAMPLE] User Tagged as Interested',
            defaults={
                'description': 'Check if user has "interested" tag',
                'operator': 'and',
                'conditions': [
                    {'field': 'user.tags', 'operator': 'contains', 'value': 'interested'}
                ]
            }
        )
        
        # Create sample actions
        self.stdout.write('Creating sample actions...')
        
        send_coupon_action, created = Action.objects.get_or_create(
            name='[SAMPLE] Send Coupon Code',
            defaults={
                'description': 'Send a personalized coupon code to the user',
                'action_type': 'send_message',
                'configuration': {
                    'message': 'سلام {{user.first_name}}! کد تخفیف شما: SAVE20 - برای خرید بعدی استفاده کنید!'
                },
                'order': 1,
                'is_active': True
            }
        )
        
        add_coupon_tag_action, created = Action.objects.get_or_create(
            name='[SAMPLE] Add Coupon Sent Tag',
            defaults={
                'description': 'Add "coupon_sent" tag to user',
                'action_type': 'add_tag',
                'configuration': {
                    'tag_name': 'coupon_sent'
                },
                'order': 2,
                'is_active': True
            }
        )
        
        wait_action, created = Action.objects.get_or_create(
            name='[SAMPLE] Wait 10 Minutes',
            defaults={
                'description': 'Wait 10 minutes before next action',
                'action_type': 'wait',
                'configuration': {
                    'duration': 10,
                    'unit': 'minutes'
                },
                'order': 3,
                'is_active': True
            }
        )
        
        followup_email_action, created = Action.objects.get_or_create(
            name='[SAMPLE] Send Follow-up Email',
            defaults={
                'description': 'Send follow-up email about the coupon',
                'action_type': 'send_email',
                'configuration': {
                    'subject': 'Don\'t forget your discount code!',
                    'body': 'Hi {{user.first_name}},\n\nDon\'t forget to use your discount code SAVE20 for 20% off your next purchase!\n\nBest regards,\nFiko Team',
                    'recipient': '{{user.email}}'
                },
                'order': 4,
                'is_active': True
            }
        )
        
        welcome_message_action, created = Action.objects.get_or_create(
            name='[SAMPLE] Send Welcome Message',
            defaults={
                'description': 'Send welcome message to new users',
                'action_type': 'send_message',
                'configuration': {
                    'message': 'خوش آمدید {{user.first_name}}! به فیکو خوش آمدید. چطور می‌تونم کمکتون کنم؟'
                },
                'order': 1,
                'is_active': True
            }
        )
        
        # Create sample workflows
        self.stdout.write('Creating sample workflows...')
        
        User = get_user_model()
        admin_user = User.objects.filter(is_superuser=True).first()
        
        coupon_workflow, created = Workflow.objects.get_or_create(
            name='[SAMPLE] Coupon Request Workflow',
            defaults={
                'description': 'Automatically send coupon codes when users ask for discounts',
                'status': 'DRAFT',  # Start as draft for safety
                'max_executions': 1,  # Only once per user
                'delay_between_executions': 3600,  # 1 hour delay
                'created_by': admin_user
            }
        )
        
        welcome_workflow, created = Workflow.objects.get_or_create(
            name='[SAMPLE] Welcome New Users',
            defaults={
                'description': 'Welcome new users with a friendly message',
                'status': 'DRAFT',  # Start as draft for safety
                'max_executions': 1,  # Only once per user
                'created_by': admin_user
            }
        )
        
        # Associate triggers with workflows
        self.stdout.write('Associating triggers with workflows...')
        
        TriggerWorkflowAssociation.objects.get_or_create(
            trigger=message_trigger,
            workflow=coupon_workflow,
            defaults={
                'priority': 100,
                'specific_conditions': {},
                'is_active': True
            }
        )
        
        TriggerWorkflowAssociation.objects.get_or_create(
            trigger=welcome_trigger,
            workflow=welcome_workflow,
            defaults={
                'priority': 100,
                'specific_conditions': {},
                'is_active': True
            }
        )
        
        # Associate actions with workflows
        self.stdout.write('Associating actions with workflows...')
        
        # Coupon workflow actions
        WorkflowAction.objects.get_or_create(
            workflow=coupon_workflow,
            action=send_coupon_action,
            defaults={
                'order': 1,
                'is_required': True,
                'condition': user_interested_condition
            }
        )
        
        WorkflowAction.objects.get_or_create(
            workflow=coupon_workflow,
            action=add_coupon_tag_action,
            defaults={
                'order': 2,
                'is_required': False
            }
        )
        
        WorkflowAction.objects.get_or_create(
            workflow=coupon_workflow,
            action=wait_action,
            defaults={
                'order': 3,
                'is_required': False
            }
        )
        
        WorkflowAction.objects.get_or_create(
            workflow=coupon_workflow,
            action=followup_email_action,
            defaults={
                'order': 4,
                'is_required': False
            }
        )
        
        # Welcome workflow actions
        WorkflowAction.objects.get_or_create(
            workflow=welcome_workflow,
            action=welcome_message_action,
            defaults={
                'order': 1,
                'is_required': True
            }
        )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully created sample workflows!\n\n'
                f'Created workflows:\n'
                f'- {coupon_workflow.name} (Status: {coupon_workflow.status})\n'
                f'- {welcome_workflow.name} (Status: {welcome_workflow.status})\n\n'
                f'Note: Workflows are created in DRAFT status for safety.\n'
                f'You can activate them via the admin interface or API.\n\n'
                f'Test the coupon workflow by:\n'
                f'1. Create a customer with "interested" tag\n'
                f'2. Send a message containing "کد تخفیف" or "coupon"\n'
                f'3. Check workflow executions in admin'
            )
        )
