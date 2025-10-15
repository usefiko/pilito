"""
Debug command to check why AI is not responding to messages
"""
from django.core.management.base import BaseCommand
from accounts.models import User
from message.models import Customer, Conversation, Message
from AI_model.models import AIGlobalConfig
from AI_model.services.gemini_service import GeminiChatService
from AI_model.services.message_integration import MessageSystemIntegration
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Debug why AI is not responding to messages'

    def add_arguments(self, parser):
        parser.add_argument('--user-id', type=int, help='User ID to debug')
        parser.add_argument('--conversation-id', type=str, help='Conversation ID to debug')
        parser.add_argument('--message-id', type=str, help='Message ID to debug')

    def handle(self, *args, **options):
        self.stdout.write('🔍 Debugging AI Response Issues...')
        self.stdout.write('=' * 70)
        
        try:
            # Test 1: Check Global AI Configuration
            self.stdout.write('\n1️⃣ Checking Global AI Configuration...')
            global_config = AIGlobalConfig.get_config()
            self.stdout.write(f'   🌐 Global AI enabled: {global_config.auto_response_enabled}')
            self.stdout.write(f'   📊 API Key configured: {bool(global_config.gemini_api_key)}')
            
            if not global_config.auto_response_enabled:
                self.stdout.write('   ❌ ISSUE: Global AI is disabled!')
                self.stdout.write('   💡 Solution: Enable auto_response_enabled in AIGlobalConfig')
            
            # Find user to test
            user_id = options.get('user_id')
            if user_id:
                user = User.objects.get(id=user_id)
            else:
                # Find user with recent messages
                user = User.objects.filter(
                    conversations__messages__type='customer',
                    conversations__messages__is_answered=False
                ).first()
            
            if not user:
                self.stdout.write('❌ No suitable user found for testing')
                return
            
            self.stdout.write(f'\n2️⃣ Testing User: {user.username} ({user.email})')
            self.stdout.write(f'   ⚙️  Default reply handler: {user.default_reply_handler}')
            
            # Test 2: Check User AI Configuration
            self.stdout.write('\n3️⃣ Checking User AI Configuration...')
            ai_service = GeminiChatService(user)
            
            self.stdout.write(f'   🤖 AI Service configured: {ai_service.is_configured()}')
            self.stdout.write(f'   📋 AI Prompts available: {ai_service.ai_prompts is not None}')
            
            if ai_service.ai_prompts:
                self.stdout.write(f'   📝 Manual prompt set: {bool(ai_service.ai_prompts.manual_prompt and ai_service.ai_prompts.manual_prompt.strip())}')
                # Auto prompt is now in GeneralSettings
                from settings.models import GeneralSettings
                general_settings = GeneralSettings.get_settings()
                self.stdout.write(f'   🤖 Auto prompt set: {bool(general_settings.auto_prompt and general_settings.auto_prompt.strip())}')
                
                # Test prompt validation
                try:
                    ai_service.ai_prompts.validate_for_ai_response()
                    self.stdout.write(f'   ✅ Prompt validation: PASSED')
                except ValueError as e:
                    self.stdout.write(f'   ❌ Prompt validation: FAILED - {str(e)}')
            else:
                self.stdout.write(f'   ❌ ISSUE: No AI prompts found for user!')
                
            config_status = ai_service.get_configuration_status()
            for key, value in config_status.items():
                status_icon = "✅" if value else "❌"
                self.stdout.write(f'   {status_icon} {key}: {value}')
            
            # Test 3: Find problematic conversation/message
            conversation_id = options.get('conversation_id')
            message_id = options.get('message_id')
            
            if conversation_id:
                conversation = Conversation.objects.get(id=conversation_id)
            elif message_id:
                message = Message.objects.get(id=message_id)
                conversation = message.conversation
            else:
                # Find recent conversation with unanswered messages
                conversation = Conversation.objects.filter(
                    user=user,
                    messages__type='customer',
                    messages__is_answered=False
                ).first()
            
            if not conversation:
                self.stdout.write('❌ No suitable conversation found for testing')
                return
            
            self.stdout.write(f'\n4️⃣ Testing Conversation: {conversation.id}')
            self.stdout.write(f'   📊 Status: {conversation.status}')
            self.stdout.write(f'   👤 Customer: {conversation.customer}')
            self.stdout.write(f'   📱 Source: {conversation.source}')
            
            # Test 4: Check specific message
            if message_id:
                test_message = Message.objects.get(id=message_id)
            else:
                test_message = conversation.messages.filter(
                    type='customer',
                    is_answered=False
                ).first()
            
            if not test_message:
                self.stdout.write('❌ No unanswered customer message found')
                return
            
            self.stdout.write(f'\n5️⃣ Testing Message: {test_message.id}')
            self.stdout.write(f'   📝 Content: {test_message.content}')
            self.stdout.write(f'   🏷️  Type: {test_message.type}')
            self.stdout.write(f'   ✅ Is answered: {test_message.is_answered}')
            self.stdout.write(f'   🤖 Is AI response: {getattr(test_message, "is_ai_response", False)}')
            
            # Test 5: Test _should_process_message logic step by step
            self.stdout.write('\n6️⃣ Testing Message Processing Logic...')
            
            integration_service = MessageSystemIntegration(user)
            
            # Test each condition manually
            self.stdout.write(f'   📋 Message type is customer: {test_message.type == "customer"}')
            self.stdout.write(f'   📋 Message not answered: {not test_message.is_answered}')
            self.stdout.write(f'   📋 Message not AI response: {not getattr(test_message, "is_ai_response", False)}')
            self.stdout.write(f'   📋 Conversation status active: {conversation.status == "active"}')
            self.stdout.write(f'   📋 Global AI enabled: {global_config.auto_response_enabled}')
            
            # Test the actual method
            should_process = integration_service._should_process_message(test_message)
            self.stdout.write(f'   🎯 Should process message: {should_process}')
            
            if not should_process:
                self.stdout.write(f'   ❌ ISSUE: Message processing blocked!')
                
                # Individual checks to find the specific issue
                if test_message.type != 'customer':
                    self.stdout.write(f'      - Wrong message type: {test_message.type}')
                if test_message.is_answered:
                    self.stdout.write(f'      - Message already answered')
                if getattr(test_message, 'is_ai_response', False):
                    self.stdout.write(f'      - Message is AI response')
                if conversation.status != 'active':
                    self.stdout.write(f'      - Conversation status is: {conversation.status}')
                if not global_config.auto_response_enabled:
                    self.stdout.write(f'      - Global AI disabled')
            
            # Test 6: Try manual AI processing
            if should_process and ai_service.is_configured():
                self.stdout.write('\n7️⃣ Testing Manual AI Response...')
                
                try:
                    ai_response = ai_service.generate_response(
                        customer_message=test_message.content,
                        conversation=conversation
                    )
                    
                    self.stdout.write(f'   🤖 AI Response Success: {ai_response.get("success", False)}')
                    if ai_response.get('success'):
                        self.stdout.write(f'   📝 Response preview: {ai_response.get("response", "")[:100]}...')
                    else:
                        self.stdout.write(f'   ❌ AI Response Error: {ai_response.get("error", "Unknown")}')
                        
                except Exception as e:
                    self.stdout.write(f'   ❌ AI Response Exception: {str(e)}')
            
            # Test 7: Check Celery Task
            self.stdout.write('\n8️⃣ Recommendations...')
            
            if not global_config.auto_response_enabled:
                self.stdout.write('   💡 Enable global AI: Update AIGlobalConfig.auto_response_enabled = True')
            
            if not ai_service.ai_prompts:
                self.stdout.write('   💡 Create AI prompts: User needs AIPrompts configuration')
            elif ai_service.ai_prompts and not ai_service.ai_prompts.manual_prompt:
                self.stdout.write('   💡 Set manual prompt: User needs to fill manual_prompt field')
            
            if conversation.status != 'active':
                self.stdout.write(f'   💡 Fix conversation status: Change from "{conversation.status}" to "active"')
            
            if test_message.is_answered:
                self.stdout.write('   💡 Reset message status: Set is_answered = False for testing')
            
            self.stdout.write('\n' + '=' * 70)
            self.stdout.write('✅ AI Debug Analysis Completed!')
            
        except Exception as e:
            self.stdout.write(f'❌ Debug failed: {str(e)}')
            import traceback
            traceback.print_exc()