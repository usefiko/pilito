from django.core.management.base import BaseCommand
from accounts.models import User
from AI_model.models import AIGlobalConfig, AIUsageTracking
from AI_model.services.gemini_service import GeminiChatService
from AI_model.services.message_integration import MessageSystemIntegration
from settings.models import AIPrompts
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Test AI model setup and integration'

    def handle(self, *args, **options):
        self.stdout.write(self.style.HTTP_INFO('🤖 Testing AI Model Setup...'))
        self.stdout.write('=' * 60)
        
        # Test 1: Check models are properly created
        self.test_models()
        
        # Test 2: Check if users have AI configuration
        self.test_user_configs()
        
        # Test 3: Test AI service initialization
        self.test_ai_service()
        
        # Test 4: Test message integration
        self.test_message_integration()
        
        # Test 5: Check Celery tasks
        self.test_celery_tasks()
        
        self.stdout.write('=' * 60)
        self.stdout.write(self.style.SUCCESS('✅ AI Model setup test completed!'))

    def test_models(self):
        """Test if all AI models are properly created"""
        self.stdout.write('\n🔍 Testing Models...')
        
        try:
            # Test model creation
            user_count = User.objects.count()
            global_config = AIGlobalConfig.get_config()
            usage_count = AIUsageTracking.objects.count()
            prompt_count = AIPrompts.objects.count()
            
            self.stdout.write(f'✅ Users: {user_count}')
            self.stdout.write(f'✅ Global AI Config: {global_config.model_name if global_config else "Not configured"}')
            self.stdout.write(f'✅ Usage Records: {usage_count}')
            self.stdout.write(f'✅ AI Prompts: {prompt_count}')
            
        except Exception as e:
            self.stdout.write(f'❌ Model test failed: {str(e)}')

    def test_user_configs(self):
        """Test user AI configurations"""
        self.stdout.write('\n⚙️ Testing User Configurations...')
        
        users = User.objects.all()[:5]  # Test first 5 users
        
        for user in users:
            try:
                # Check global AI config
                global_config = AIGlobalConfig.get_config()
                created = False  # Global config always exists
                
                # Check AI prompts
                try:
                    prompts = user.ai_prompts
                except AIPrompts.DoesNotExist:
                    prompts = None
                
                status = "GLOBAL"
                prompt_status = "✅" if prompts else "❗"
                
                self.stdout.write(f'  {user.username:15} | Config: {status:6} | Prompts: {prompt_status}')
                
            except Exception as e:
                self.stdout.write(f'  {user.username:15} | ❌ Error: {str(e)}')

    def test_ai_service(self):
        """Test AI service initialization"""
        self.stdout.write('\n🧠 Testing AI Service...')
        
        users = User.objects.all()[:3]  # Test first 3 users
        
        for user in users:
            try:
                # Test Gemini service initialization
                service = GeminiChatService(user)
                
                configured_status = "✅" if service.is_configured() else "❌"
                prompts_status = "✅" if service.ai_prompts else "❗"
                model_status = "✅" if hasattr(service, 'model') and service.model else "❗"
                
                self.stdout.write(
                    f'  {user.username:15} | Configured: {configured_status} | Prompts: {prompts_status} | Model: {model_status}'
                )
                
            except Exception as e:
                self.stdout.write(f'  {user.username:15} | ❌ Error: {str(e)}')

    def test_message_integration(self):
        """Test message system integration"""
        self.stdout.write('\n📨 Testing Message Integration...')
        
        users = User.objects.all()[:2]  # Test first 2 users
        
        for user in users:
            try:
                # Test integration service
                integration = MessageSystemIntegration(user)
                
                self.stdout.write(f'  {user.username:15} | Integration service: ✅')
                
                # Test if user has conversations
                from message.models import Conversation
                conv_count = Conversation.objects.filter(user=user).count()
                
                self.stdout.write(f'  {user.username:15} | Conversations: {conv_count}')
                
            except Exception as e:
                self.stdout.write(f'  {user.username:15} | ❌ Error: {str(e)}')

    def test_celery_tasks(self):
        """Test Celery task availability"""
        self.stdout.write('\n⚡ Testing Celery Tasks...')
        
        try:
            # Test task imports
            from AI_model.tasks import (
                process_ai_response_async,
                cleanup_old_usage_data,
                generate_usage_analytics,
                test_ai_configuration
            )
            
            self.stdout.write('  ✅ AI tasks imported successfully')
            
            # Test a simple task
            result = test_ai_configuration.delay()
            self.stdout.write(f'  ✅ Test task queued: {result.id}')
            
        except ImportError as e:
            self.stdout.write(f'  ❌ Task import failed: {str(e)}')
        except Exception as e:
            self.stdout.write(f'  ⚠️ Celery not available (development mode): {str(e)}')

    def create_test_data(self):
        """Create some test data for demonstration"""
        self.stdout.write('\n🔧 Creating Test Data...')
        
        try:
            # Get or create a test user
            user, created = User.objects.get_or_create(
                username='ai_test_user',
                defaults={
                    'email': 'test@example.com',
                    'first_name': 'AI',
                    'last_name': 'Test'
                }
            )
            
            # Ensure global AI configuration exists
            global_config = AIGlobalConfig.get_config()
            config_created = False  # Global config is singleton
            
            # Create AI prompts
            prompts, prompts_created = AIPrompts.objects.get_or_create(
                user=user,
                defaults={
                    'manual_prompt': 'You are a helpful customer service assistant.',
                    'knowledge_source': {'company': 'AI Test Company'},
                    'product_service': {'services': ['AI Chat Support']},
                    'question_answer': {'greeting': 'Hello! How can I help you today?'}
                }
            )
            
            status_user = "CREATED" if created else "EXISTS"
            status_config = "CREATED" if config_created else "EXISTS"
            status_prompts = "CREATED" if prompts_created else "EXISTS"
            
            self.stdout.write(f'  Test User: {status_user}')
            self.stdout.write(f'  AI Config: {status_config}')
            self.stdout.write(f'  AI Prompts: {status_prompts}')
            
            return user
            
        except Exception as e:
            self.stdout.write(f'  ❌ Test data creation failed: {str(e)}')
            return None