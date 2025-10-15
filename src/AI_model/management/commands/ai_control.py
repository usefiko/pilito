from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
from AI_model.models import AIModelConfig
from AI_model.services.message_integration import MessageSystemIntegration
from message.models import Conversation
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Control AI auto-response system'

    def add_arguments(self, parser):
        parser.add_argument(
            'action',
            choices=['enable', 'disable', 'status', 'test', 'sync', 'validate', 'conversations'],
            help='Action to perform'
        )
        parser.add_argument(
            '--user',
            type=str,
            help='Username to operate on (if not provided, affects all users)'
        )


    def handle(self, *args, **options):
        action = options['action']
        username = options.get('user')

        if username:
            try:
                user = User.objects.get(username=username)
                users = [user]
            except User.DoesNotExist:
                raise CommandError(f'User "{username}" does not exist.')
        else:
            users = User.objects.all()

        if action == 'enable':
            self.enable_ai(users)
        elif action == 'disable':
            self.disable_ai(users)
        elif action == 'status':
            self.show_status(users)
        elif action == 'test':
            self.test_ai(users)
        elif action == 'sync':
            self.sync_conversations(users)
        elif action == 'validate':
            self.validate_configurations(users)
        elif action == 'conversations':
            self.manage_conversations(users)

    def enable_ai(self, users):
        """Enable AI auto-response for users"""
        from django.conf import settings
        
        # Check if global API key is configured
        global_api_key = getattr(settings, 'GEMINI_API_KEY', None)
        if not global_api_key:
            self.stdout.write(
                self.style.ERROR('❌ Global Gemini API key not configured in settings')
            )
            return
        
        enabled_count = 0
        
        for user in users:
            config, created = AIModelConfig.objects.get_or_create(
                user=user,
                defaults={'auto_response_enabled': True}
            )
            
            if not created:
                config.auto_response_enabled = True
                config.save()
            
            enabled_count += 1
            
            self.stdout.write(
                self.style.SUCCESS(f'✅ Enabled AI auto-response for user: {user.username}')
            )
        
        self.stdout.write(
            self.style.SUCCESS(f'AI auto-response enabled for {enabled_count} users')
        )

    def disable_ai(self, users):
        """Disable AI auto-response for users"""
        disabled_count = 0
        
        for user in users:
            try:
                config = AIModelConfig.objects.get(user=user)
                config.auto_response_enabled = False
                config.save()
                
                disabled_count += 1
                
                self.stdout.write(
                    self.style.WARNING(f'❌ Disabled AI auto-response for user: {user.username}')
                )
            except AIModelConfig.DoesNotExist:
                self.stdout.write(
                    self.style.WARNING(f'⚠️  No AI config found for user: {user.username}')
                )
        
        self.stdout.write(
            self.style.SUCCESS(f'AI auto-response disabled for {disabled_count} users')
        )

    def show_status(self, users):
        """Show AI status for users"""
        self.stdout.write(self.style.HTTP_INFO('AI Auto-Response Status:'))
        self.stdout.write('=' * 50)
        
        enabled_users = 0
        total_users = len(users)
        
        for user in users:
            try:
                from django.conf import settings
                global_api_key = getattr(settings, 'GEMINI_API_KEY', None)
                
                config = AIModelConfig.objects.get(user=user)
                status = "✅ ENABLED" if config.auto_response_enabled else "❌ DISABLED"
                has_global_api = "🔑" if global_api_key else "❗"
                model = config.model_name
                
                self.stdout.write(
                    f'{user.username:20} | {status:12} | {has_global_api} | {model}'
                )
                
                if config.auto_response_enabled:
                    enabled_users += 1
                    
            except AIModelConfig.DoesNotExist:
                self.stdout.write(
                    f'{user.username:20} | ⚪ NOT CONFIGURED'
                )
        
        self.stdout.write('=' * 50)
        self.stdout.write(f'Summary: {enabled_users}/{total_users} users have AI enabled')

    def test_ai(self, users):
        """Test AI integration for users"""
        self.stdout.write(self.style.HTTP_INFO('Testing AI Integration:'))
        
        success_count = 0
        
        for user in users:
            try:
                # Check AI configuration
                config = AIModelConfig.objects.get(user=user)
                
                if not config.auto_response_enabled:
                    self.stdout.write(f'❌ {user.username}: AI disabled')
                    continue
                
                # Check global API key
                from django.conf import settings
                global_api_key = getattr(settings, 'GEMINI_API_KEY', None)
                if not global_api_key:
                    self.stdout.write(f'⚠️  {user.username}: Global API key not configured')
                    continue
                
                # Test Gemini service initialization
                from AI_model.services.gemini_service import GeminiChatService
                gemini_service = GeminiChatService(user)
                
                if gemini_service.model:
                    self.stdout.write(f'✅ {user.username}: AI service ready')
                    success_count += 1
                else:
                    self.stdout.write(f'❌ {user.username}: Failed to initialize Gemini model')
                
            except AIModelConfig.DoesNotExist:
                self.stdout.write(f'⚪ {user.username}: No AI configuration')
            except Exception as e:
                self.stdout.write(f'❌ {user.username}: Error - {str(e)}')
        
        self.stdout.write(f'\nTest Results: {success_count}/{len(users)} users ready for AI')

    def sync_conversations(self, users):
        """Sync existing conversations to AI chat sessions"""
        self.stdout.write(self.style.HTTP_INFO('Syncing conversations to AI chat sessions...'))
        
        total_synced = 0
        
        for user in users:
            try:
                # Get active conversations for user
                conversations = Conversation.objects.filter(
                    user=user,
                    is_active=True,
                    status='active'
                )
                
                integration = MessageSystemIntegration(user)
                user_synced = 0
                
                for conversation in conversations:
                    try:
                        # Create AI chat session
                        ai_session = integration._get_or_create_ai_chat_session(conversation)
                        
                        # Sync conversation history
                        integration._sync_conversation_history(conversation, ai_session)
                        
                        user_synced += 1
                        
                    except Exception as e:
                        self.stdout.write(f'❌ Error syncing conversation {conversation.id}: {str(e)}')
                
                self.stdout.write(f'✅ {user.username}: Synced {user_synced} conversations')
                total_synced += user_synced
                
            except Exception as e:
                self.stdout.write(f'❌ Error processing user {user.username}: {str(e)}')
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully synced {total_synced} conversations')
        )
    
    def validate_configurations(self, users):
        """Validate AI configurations for users"""
        self.stdout.write(self.style.HTTP_INFO('Validating AI Configurations:'))
        self.stdout.write('=' * 60)
        
        from AI_model.utils import validate_ai_configuration
        
        valid_count = 0
        
        for user in users:
            try:
                validation = validate_ai_configuration(user)
                
                if validation['is_valid']:
                    status_icon = "✅"
                    valid_count += 1
                else:
                    status_icon = "❌"
                
                self.stdout.write(f'{status_icon} {user.username:20} | Valid: {validation["is_valid"]}')
                
                if validation['issues']:
                    for issue in validation['issues']:
                        self.stdout.write(f'    ⚠️  {issue}')
                
                # Show configuration details
                details = []
                if validation['has_config']:
                    details.append(f"Config: ✅")
                else:
                    details.append(f"Config: ❌")
                    
                if validation['has_api_key']:
                    details.append(f"API Key: ✅")
                else:
                    details.append(f"API Key: ❌")
                    
                if validation['auto_response_enabled']:
                    details.append(f"Auto-Response: ✅")
                else:
                    details.append(f"Auto-Response: ❌")
                    
                if validation['has_prompts']:
                    details.append(f"Prompts: ✅")
                else:
                    details.append(f"Prompts: ❌")
                
                self.stdout.write(f'    {" | ".join(details)}')
                self.stdout.write('')
                
            except Exception as e:
                self.stdout.write(f'❌ {user.username:20} | Error: {str(e)}')
        
        self.stdout.write('=' * 60)
        self.stdout.write(f'Summary: {valid_count}/{len(users)} users have valid AI configuration')
    
    def manage_conversations(self, users):
        """Show conversation status management information"""
        self.stdout.write(self.style.HTTP_INFO('Conversation Status Management:'))
        self.stdout.write('=' * 60)
        
        for user in users:
            try:
                from message.models import Conversation
                
                # Count conversations by status
                conversations = Conversation.objects.filter(user=user, is_active=True)
                total_conversations = conversations.count()
                active_count = conversations.filter(status='active').count()
                support_active_count = conversations.filter(status='support_active').count()
                other_count = total_conversations - active_count - support_active_count
                
                # Show user info
                self.stdout.write(f'👤 {user.username:20} | Default Handler: {user.default_reply_handler}')
                self.stdout.write(f'   📊 Total: {total_conversations:3} | AI: {active_count:3} | Manual: {support_active_count:3} | Other: {other_count:3}')
                
                # Show AI configuration status
                try:
                    from AI_model.models import AIModelConfig
                    from django.conf import settings
                    
                    global_api_key = getattr(settings, 'GEMINI_API_KEY', None)
                    ai_config = AIModelConfig.objects.get(user=user)
                    ai_status = "✅ Enabled" if ai_config.auto_response_enabled else "❌ Disabled"
                    api_key_status = "✅" if global_api_key else "❌"
                    self.stdout.write(f'   🤖 AI Status: {ai_status} | Global API Key: {api_key_status}')
                except AIModelConfig.DoesNotExist:
                    self.stdout.write(f'   🤖 AI Status: ❌ Not Configured')
                
                self.stdout.write('')
                
            except Exception as e:
                self.stdout.write(f'❌ Error for user {user.username}: {str(e)}')
        
        self.stdout.write('=' * 60)
        self.stdout.write('Commands to manage conversations:')
        self.stdout.write('  • Switch all conversations to AI:     python manage.py ai_control enable --user username')
        self.stdout.write('  • Switch all conversations to Manual: python manage.py ai_control disable --user username')
        self.stdout.write('  • Use API endpoints for individual conversation control')
        self.stdout.write('')
        self.stdout.write('Note: Uses global Gemini API key from GEMINI_API_KEY environment variable')
        self.stdout.write('')
        self.stdout.write('API Endpoints:')
        self.stdout.write('  • GET/PUT /api/v1/ai/conversations/<id>/status/')
        self.stdout.write('  • PUT /api/v1/ai/conversations/bulk-status/')
        self.stdout.write('  • GET/PUT /api/v1/ai/default-handler/')