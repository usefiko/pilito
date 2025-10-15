from django.core.management.base import BaseCommand
from workflow_template.models import Language, Type, Template


class Command(BaseCommand):
    help = 'Populate sample data for workflow templates'

    def handle(self, *args, **options):
        self.stdout.write('Creating sample languages...')
        
        # Create sample languages
        languages_data = [
            {'name': 'English'},
            {'name': 'Persian'},
            {'name': 'Arabic'},
            {'name': 'Turkish'},
            {'name': 'Spanish'},
            {'name': 'French'},
        ]
        
        for lang_data in languages_data:
            language, created = Language.objects.get_or_create(
                name=lang_data['name'],
                defaults=lang_data
            )
            if created:
                self.stdout.write(f'Created language: {language.name}')
            else:
                self.stdout.write(f'Language already exists: {language.name}')
        
        self.stdout.write('Creating sample types...')
        
        # Create sample types
        types_data = [
            {'name': 'Customer Service', 'description': 'Templates for customer service workflows'},
            {'name': 'Sales', 'description': 'Templates for sales and lead generation'},
            {'name': 'Marketing', 'description': 'Templates for marketing campaigns'},
            {'name': 'Support', 'description': 'Templates for technical support'},
            {'name': 'Onboarding', 'description': 'Templates for user onboarding'},
            {'name': 'Follow Up', 'description': 'Templates for follow-up communications'},
        ]
        
        for type_data in types_data:
            type_obj, created = Type.objects.get_or_create(
                name=type_data['name'],
                defaults=type_data
            )
            if created:
                self.stdout.write(f'Created type: {type_obj.name}')
            else:
                self.stdout.write(f'Type already exists: {type_obj.name}')
        
        self.stdout.write('Creating sample templates...')
        
        # Get the first language and type for sample templates
        english_lang = Language.objects.get(name='English')
        persian_lang = Language.objects.get(name='Persian')
        customer_service_type = Type.objects.get(name='Customer Service')
        sales_type = Type.objects.get(name='Sales')
        
        # Create sample templates
        templates_data = [
            {
                'name': 'Welcome New Customer',
                'description': 'A warm welcome message for new customers',
                'jsonfield': {
                    'nodes': [
                        {
                            'id': 'welcome_node',
                            'type': 'action',
                            'title': 'Send Welcome Message',
                            'content': 'Welcome to our service! We\'re excited to have you on board.',
                            'position': {'x': 100, 'y': 100}
                        }
                    ],
                    'connections': []
                },
                'language': english_lang,
                'type': customer_service_type
            },
            {
                'name': 'خوش آمدید - مشتری جدید',
                'description': 'پیام خوش آمدگویی برای مشتریان جدید',
                'jsonfield': {
                    'nodes': [
                        {
                            'id': 'welcome_node_fa',
                            'type': 'action',
                            'title': 'ارسال پیام خوش آمدگویی',
                            'content': 'به سرویس ما خوش آمدید! خوشحالیم که شما را در کنارمان داریم.',
                            'position': {'x': 100, 'y': 100}
                        }
                    ],
                    'connections': []
                },
                'language': persian_lang,
                'type': customer_service_type
            },
            {
                'name': 'Lead Qualification',
                'description': 'Template for qualifying sales leads',
                'jsonfield': {
                    'nodes': [
                        {
                            'id': 'qualification_node',
                            'type': 'condition',
                            'title': 'Check Lead Quality',
                            'conditions': [
                                {'field': 'budget', 'operator': 'greater_than', 'value': 1000},
                                {'field': 'timeline', 'operator': 'equals', 'value': 'immediate'}
                            ],
                            'position': {'x': 100, 'y': 100}
                        },
                        {
                            'id': 'high_quality_action',
                            'type': 'action',
                            'title': 'Send to Sales Team',
                            'content': 'This lead meets our qualification criteria. Please contact them immediately.',
                            'position': {'x': 300, 'y': 100}
                        }
                    ],
                    'connections': [
                        {'from': 'qualification_node', 'to': 'high_quality_action', 'condition': 'high_quality'}
                    ]
                },
                'language': english_lang,
                'type': sales_type
            }
        ]
        
        for template_data in templates_data:
            template, created = Template.objects.get_or_create(
                name=template_data['name'],
                language=template_data['language'],
                defaults=template_data
            )
            if created:
                self.stdout.write(f'Created template: {template.name}')
            else:
                self.stdout.write(f'Template already exists: {template.name}')
        
        self.stdout.write(
            self.style.SUCCESS('Successfully populated sample data for workflow templates!')
        )
