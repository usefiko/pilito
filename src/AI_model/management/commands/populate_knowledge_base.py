"""
Django management command to populate knowledge base
Usage: python manage.py populate_knowledge_base --user <username>
"""
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from AI_model.services.knowledge_ingestion_service import KnowledgeIngestionService

User = get_user_model()


class Command(BaseCommand):
    help = 'Populate TenantKnowledge from existing data (FAQ, Products, Manual, Website)'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--user',
            type=str,
            help='Username to populate knowledge for (required)'
        )
        
        parser.add_argument(
            '--sources',
            type=str,
            nargs='+',
            choices=['faq', 'products', 'manual', 'website'],
            help='Specific sources to ingest (default: all)',
            default=None
        )
        
        parser.add_argument(
            '--force',
            action='store_true',
            help='Delete existing chunks and recreate'
        )
        
        parser.add_argument(
            '--all-users',
            action='store_true',
            help='Populate for all users'
        )
    
    def handle(self, *args, **options):
        username = options.get('user')
        sources = options.get('sources')
        force = options.get('force', False)
        all_users = options.get('all_users', False)
        
        if not username and not all_users:
            raise CommandError('Please provide --user <username> or --all-users')
        
        if username and all_users:
            raise CommandError('Cannot use both --user and --all-users')
        
        # Get users
        if all_users:
            users = User.objects.filter(is_active=True)
            self.stdout.write(self.style.WARNING(f'Processing {users.count()} users...'))
        else:
            try:
                users = [User.objects.get(username=username)]
            except User.DoesNotExist:
                raise CommandError(f'User "{username}" does not exist')
        
        # Process each user
        total_chunks = 0
        total_errors = 0
        
        for user in users:
            self.stdout.write(f'\n{"="*60}')
            self.stdout.write(self.style.SUCCESS(f'Processing user: {user.username}'))
            self.stdout.write(f'{"="*60}\n')
            
            # Ingest knowledge
            results = KnowledgeIngestionService.ingest_user_knowledge(
                user=user,
                sources=sources,
                force_recreate=force
            )
            
            # Display results
            self.stdout.write(self.style.SUCCESS(f'\n📊 Results for {user.username}:'))
            self.stdout.write(f'  FAQ:      {results["faq"]["chunks"]:>4} chunks {"✅" if results["faq"]["success"] else "❌"}')
            self.stdout.write(f'  Products: {results["products"]["chunks"]:>4} chunks {"✅" if results["products"]["success"] else "❌"}')
            self.stdout.write(f'  Manual:   {results["manual"]["chunks"]:>4} chunks {"✅" if results["manual"]["success"] else "❌"}')
            self.stdout.write(f'  Website:  {results["website"]["chunks"]:>4} chunks {"✅" if results["website"]["success"] else "❌"}')
            self.stdout.write(f'  {"-"*30}')
            self.stdout.write(self.style.SUCCESS(f'  Total:    {results["total_chunks"]:>4} chunks\n'))
            
            if results['errors']:
                self.stdout.write(self.style.ERROR(f'  Errors ({len(results["errors"])}):'))
                for error in results['errors']:
                    self.stdout.write(self.style.ERROR(f'    • {error}'))
            
            total_chunks += results['total_chunks']
            total_errors += len(results['errors'])
        
        # Final summary
        self.stdout.write(f'\n{"="*60}')
        self.stdout.write(self.style.SUCCESS('🎉 INGESTION COMPLETE'))
        self.stdout.write(f'{"="*60}')
        self.stdout.write(f'Total users processed: {len(users)}')
        self.stdout.write(f'Total chunks created:  {total_chunks}')
        self.stdout.write(f'Total errors:          {total_errors}')
        self.stdout.write(f'{"="*60}\n')
        
        if total_errors == 0:
            self.stdout.write(self.style.SUCCESS('✅ All knowledge ingested successfully!'))
        else:
            self.stdout.write(self.style.WARNING(f'⚠️  Completed with {total_errors} errors'))

