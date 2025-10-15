from django.core.management.base import BaseCommand
from message.tasks import auto_refresh_instagram_tokens
from settings.models import InstagramChannel


class Command(BaseCommand):
    help = 'Test Instagram token refresh system'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=30,
            help='Days before expiry to test with (default: 30)'
        )
        
        parser.add_argument(
            '--sync',
            action='store_true',
            help='Run synchronously instead of async'
        )

    def handle(self, *args, **options):
        days = options['days']
        sync = options['sync']
        
        self.stdout.write(f'🧪 Testing Instagram token refresh system...')
        self.stdout.write(f'📅 Testing with {days} days before expiry')
        
        # Check current Instagram channels
        channels = InstagramChannel.objects.filter(is_connect=True)
        self.stdout.write(f'🔍 Found {channels.count()} connected Instagram channels')
        
        if channels.exists():
            for channel in channels:
                self.stdout.write(f'   • {channel.telegram_channel.channel_name}: {channel.instagram_username}')
        else:
            self.stdout.write('⚠️  No connected Instagram channels found')
        
        try:
            if sync:
                # Run synchronously for testing
                self.stdout.write('🔧 Running token refresh synchronously...')
                result = auto_refresh_instagram_tokens(days)
                self.stdout.write(f'📊 Result: {result}')
            else:
                # Run asynchronously
                self.stdout.write('🔧 Queuing token refresh task...')
                result = auto_refresh_instagram_tokens.delay(days)
                self.stdout.write(f'📝 Task ID: {result.id}')
                
                # Try to get result (with timeout)
                try:
                    task_result = result.get(timeout=30)
                    self.stdout.write(f'📊 Task completed: {task_result}')
                except Exception as e:
                    self.stdout.write(f'⏳ Task is running in background: {e}')
            
            self.stdout.write('✅ Token refresh test completed')
            
        except Exception as e:
            self.stdout.write(f'❌ Error testing token refresh: {e}')
            raise