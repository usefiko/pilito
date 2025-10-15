"""
Management command to sync Fiko conversations to Intercom.

Usage:
    python manage.py sync_conversations_to_intercom
    python manage.py sync_conversations_to_intercom --user-id=123
    python manage.py sync_conversations_to_intercom --async
"""

from django.core.management.base import BaseCommand
from message.models import Conversation
from message.tasks import sync_conversation_to_intercom_async
from message.services.intercom_conversation_sync import IntercomConversationSyncService
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Sync Fiko conversations to Intercom'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--user-id',
            type=int,
            help='Sync only conversations for specific user ID'
        )
        
        parser.add_argument(
            '--conversation-id',
            type=str,
            help='Sync specific conversation by ID'
        )
        
        parser.add_argument(
            '--async',
            action='store_true',
            help='Run sync asynchronously via Celery'
        )
        
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force re-sync even if already synced'
        )
    
    def handle(self, *args, **options):
        user_id = options.get('user_id')
        conversation_id = options.get('conversation_id')
        use_async = options.get('async')
        force = options.get('force')
        
        self.stdout.write(self.style.WARNING('🔄 Starting Intercom conversation sync...'))
        self.stdout.write('')
        
        try:
            # Filter conversations
            conversations = Conversation.objects.all()
            
            if conversation_id:
                conversations = conversations.filter(id=conversation_id)
                self.stdout.write(f'Syncing specific conversation: {conversation_id}')
            elif user_id:
                conversations = conversations.filter(user_id=user_id)
                self.stdout.write(f'Syncing conversations for user: {user_id}')
            else:
                self.stdout.write('Syncing all conversations')
            
            # Exclude already synced if not forcing
            if not force:
                conversations = conversations.filter(intercom_conversation_id__isnull=True)
                self.stdout.write('(Excluding already synced conversations)')
            
            total = conversations.count()
            self.stdout.write(f'Total conversations to sync: {total}')
            self.stdout.write('')
            
            if total == 0:
                self.stdout.write(self.style.SUCCESS('✅ No conversations to sync!'))
                return
            
            if use_async:
                # Async via Celery
                self.stdout.write('📤 Dispatching sync tasks to Celery...')
                for conv in conversations:
                    task = sync_conversation_to_intercom_async.delay(conv.id)
                    self.stdout.write(f'  ✅ Queued: {conv.id} (Task: {task.id})')
                
                self.stdout.write('')
                self.stdout.write(self.style.SUCCESS(f'✅ Dispatched {total} tasks!'))
                self.stdout.write('Check Celery logs for progress.')
            else:
                # Sync synchronously
                success = 0
                failed = 0
                
                for i, conv in enumerate(conversations, 1):
                    self.stdout.write(f'[{i}/{total}] Syncing conversation {conv.id}...')
                    
                    try:
                        # Get first customer message
                        first_message = conv.messages.filter(type='customer').first()
                        if not first_message:
                            self.stdout.write(self.style.WARNING(f'  ⚠️ No customer message, skipping'))
                            failed += 1
                            continue
                        
                        # Sync to Intercom
                        result = IntercomConversationSyncService.create_conversation(
                            user_id=conv.user.id,
                            message_text=first_message.content,
                            subject=conv.title
                        )
                        
                        if result:
                            conv.intercom_conversation_id = result['id']
                            conv.save(update_fields=['intercom_conversation_id'])
                            self.stdout.write(self.style.SUCCESS(f'  ✅ Success! Intercom ID: {result["id"]}'))
                            success += 1
                        else:
                            self.stdout.write(self.style.ERROR(f'  ❌ Failed'))
                            failed += 1
                            
                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f'  ❌ Error: {str(e)}'))
                        failed += 1
                
                self.stdout.write('')
                self.stdout.write(self.style.SUCCESS('✅ Sync completed!'))
                self.stdout.write(f'Success: {success}')
                self.stdout.write(f'Failed: {failed}')
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Error: {str(e)}'))
            raise

