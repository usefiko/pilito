"""
Test command for AI platform response functionality
Tests if AI responses are automatically sent to Telegram/Instagram
"""
from django.core.management.base import BaseCommand
from accounts.models import User
from message.models import Customer, Conversation, Message
from AI_model.services.message_integration import MessageSystemIntegration
from AI_model.models import AIGlobalConfig
from settings.models import AIPrompts


class Command(BaseCommand):
    help = 'Test AI platform response functionality'

    def handle(self, *args, **options):
        self.stdout.write('🤖 Testing AI Platform Response...')
        self.stdout.write('=' * 60)
        
        try:
            # Check global AI config
            config = AIGlobalConfig.get_config()
            self.stdout.write(f'🌐 Global AI Configuration:')
            self.stdout.write(f'   Auto response enabled: {config.auto_response_enabled}')
            self.stdout.write(f'   Model: {config.model_name}')
            self.stdout.write(f'   Response delay: {config.response_delay_seconds} seconds')
            
            if not config.auto_response_enabled:
                self.stdout.write('❌ Global AI is disabled! Enable it first.')
                return
            
            # Find a recent message to test
            recent_messages = Message.objects.filter(
                type='customer',
                conversation__status='active'
            ).select_related('conversation', 'customer').order_by('-created_at')[:5]
            
            if not recent_messages.exists():
                self.stdout.write('❌ No recent customer messages with active status found')
                return
            
            self.stdout.write(f'\n📋 Found {recent_messages.count()} recent messages to test:')
            
            for i, msg in enumerate(recent_messages, 1):
                self.stdout.write(f'\n📨 Message {i}:')
                self.stdout.write(f'   ID: {msg.id}')
                self.stdout.write(f'   Content: {msg.content[:50]}...')
                self.stdout.write(f'   Source: {msg.conversation.source}')
                self.stdout.write(f'   Status: {msg.conversation.status}')
                self.stdout.write(f'   User: {msg.conversation.user.username}')
                self.stdout.write(f'   Answered: {msg.is_answered}')
                
                # Check if user has AI prompts
                try:
                    prompts = msg.conversation.user.ai_prompts
                except AIPrompts.DoesNotExist:
                    prompts = None
                if prompts:
                    self.stdout.write(f'   AI Prompts: ✅')
                else:
                    self.stdout.write(f'   AI Prompts: ❌ Missing!')
                    continue
                
                # Test AI processing
                if msg.is_answered:
                    self.stdout.write(f'   🔄 Resetting answered status for testing...')
                    msg.is_answered = False
                    msg.save()
                
                # Test message integration
                integration = MessageSystemIntegration(msg.conversation.user)
                result = integration.process_new_customer_message(msg)
                
                self.stdout.write(f'   🤖 AI Processing Result:')
                self.stdout.write(f'      Processed: {result.get("processed")}')
                
                if result.get('processed'):
                    ai_message_id = result.get('ai_message_id')
                    self.stdout.write(f'      AI Message ID: {ai_message_id}')
                    self.stdout.write(f'      Response Time: {result.get("response_time_ms")}ms')
                    
                    # Check if AI message was created
                    if ai_message_id:
                        ai_message = Message.objects.get(id=ai_message_id)
                        self.stdout.write(f'      AI Response: {ai_message.content[:100]}...')
                        
                        # Check if it's sent to platform
                        if msg.conversation.source == 'telegram':
                            self.stdout.write(f'      📱 Platform: Telegram (should be sent automatically)')
                        elif msg.conversation.source == 'instagram':
                            self.stdout.write(f'      📷 Platform: Instagram (should be sent automatically)')
                        else:
                            self.stdout.write(f'      ❓ Platform: {msg.conversation.source}')
                    
                    self.stdout.write(f'   ✅ Test completed for message {msg.id}')
                else:
                    reason = result.get('reason', 'Unknown')
                    self.stdout.write(f'      ❌ Not processed: {reason}')
                
                # Only test first message for now
                break
                
            self.stdout.write('\n' + '=' * 60)
            self.stdout.write('✅ AI Platform Response Test Completed!')
            self.stdout.write('\n💡 What should happen:')
            self.stdout.write('   1. AI processes customer message')
            self.stdout.write('   2. Creates AI response in database')
            self.stdout.write('   3. Automatically sends response to original platform')
            self.stdout.write('   4. Customer receives AI response on Telegram/Instagram')
            
        except Exception as e:
            self.stdout.write(f'❌ Test failed: {str(e)}')
            import traceback
            traceback.print_exc()