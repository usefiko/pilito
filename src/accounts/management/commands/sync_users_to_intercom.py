"""
Management command to sync all Fiko users to Intercom.

Usage:
    python manage.py sync_users_to_intercom
    python manage.py sync_users_to_intercom --batch-size=100
    python manage.py sync_users_to_intercom --async
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from accounts.services.intercom_contact_sync import IntercomContactSyncService
from accounts.tasks import bulk_sync_users_to_intercom_async
import logging

logger = logging.getLogger(__name__)
User = get_user_model()


class Command(BaseCommand):
    help = 'Sync all Fiko users to Intercom contacts'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--batch-size',
            type=int,
            default=50,
            help='Number of users to process in each batch (default: 50)'
        )
        
        parser.add_argument(
            '--async',
            action='store_true',
            help='Run sync asynchronously via Celery'
        )
    
    def handle(self, *args, **options):
        batch_size = options['batch_size']
        use_async = options['async']
        
        self.stdout.write(self.style.WARNING('🔄 Starting Intercom user sync...'))
        self.stdout.write(f'Batch size: {batch_size}')
        self.stdout.write(f'Async mode: {use_async}')
        self.stdout.write('')
        
        try:
            if use_async:
                # Run via Celery
                self.stdout.write('📤 Dispatching sync task to Celery...')
                task = bulk_sync_users_to_intercom_async.delay(batch_size=batch_size)
                self.stdout.write(
                    self.style.SUCCESS(f'✅ Task dispatched! Task ID: {task.id}')
                )
                self.stdout.write('Check Celery logs for progress.')
            else:
                # Run synchronously
                stats = IntercomContactSyncService.sync_all_users(batch_size=batch_size)
                
                self.stdout.write('')
                self.stdout.write(self.style.SUCCESS('✅ Sync completed!'))
                self.stdout.write(f"Total users: {stats['total']}")
                self.stdout.write(self.style.SUCCESS(f"✅ Success: {stats['success']}"))
                self.stdout.write(self.style.ERROR(f"❌ Failed: {stats['failed']}"))
                self.stdout.write(self.style.WARNING(f"⏭️  Skipped: {stats['skipped']}"))
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Error: {str(e)}'))
            raise

