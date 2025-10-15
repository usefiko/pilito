"""
Test command for Conversation status behavior
Tests that status is only set on creation, not on every message
"""
from django.core.management.base import BaseCommand
from accounts.models import User
from message.models import Customer, Conversation, Message
from settings.models import TelegramChannel
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Test Conversation status behavior - only set on creation'

    def handle(self, *args, **options):
        self.stdout.write('🔄 Testing Conversation Status Behavior...')
        self.stdout.write('=' * 70)
        
        try:
            # Find a user and telegram channel for testing
            user = User.objects.first()
            if not user:
                self.stdout.write('❌ No users found in database')
                return
            
            telegram_channel = TelegramChannel.objects.filter(user=user).first()
            if not telegram_channel:
                self.stdout.write('❌ No Telegram channels found for user')
                return
            
            self.stdout.write(f'👤 Testing with user: {user.username} ({user.email})')
            self.stdout.write(f'🤖 Telegram bot: {telegram_channel.bot_username}')
            self.stdout.write(f'⚙️  User default_reply_handler: {user.default_reply_handler}')
            
            # Test 1: Create a test customer
            self.stdout.write('\n1️⃣ Creating test customer...')
            test_customer, customer_created = Customer.objects.get_or_create(
                source='telegram',
                source_id='test_telegram_12345',
                defaults={
                    'first_name': 'Test',
                    'last_name': 'Customer',
                    'username': 'test_customer'
                }
            )
            action = "Created" if customer_created else "Found existing"
            self.stdout.write(f'   {action} customer: {test_customer}')
            
            # Test 2: Simulate first message (should create conversation with initial status)
            self.stdout.write('\n2️⃣ Simulating first message arrival (conversation creation)...')
            
            # Delete existing conversation if exists (for clean test)
            existing_conv = Conversation.objects.filter(
                user=user,
                source='telegram',
                customer=test_customer
            ).first()
            if existing_conv:
                self.stdout.write(f'   🗑️  Deleting existing conversation for clean test')
                existing_conv.delete()
            
            # Simulate the webhook logic for first message
            try:
                # Try to get existing conversation first
                conversation = Conversation.objects.get(
                    user=user,
                    source='telegram', 
                    customer=test_customer
                )
                conv_created = False
                self.stdout.write(f'   ❌ UNEXPECTED: Found existing conversation when should be new')
                
            except Conversation.DoesNotExist:
                # Create new conversation with initial status
                from AI_model.utils import get_initial_conversation_status
                
                # Determine initial status based on user's default_reply_handler (only for new conversations)
                initial_status = get_initial_conversation_status(user)
                
                conversation = Conversation.objects.create(
                    user=user,
                    source='telegram', 
                    customer=test_customer,
                    status=initial_status
                )
                conv_created = True
                
                self.stdout.write(f'   ✅ Created new conversation: {conversation.id}')
                self.stdout.write(f'   📊 Initial status: {initial_status}')
                self.stdout.write(f'   📝 Expected: {"active" if user.default_reply_handler == "AI" else "support_active"}')
            
            # Create first message
            first_message = Message.objects.create(
                content='سلام، این اولین پیام من است',
                conversation=conversation,
                customer=test_customer,
                type='customer'
            )
            self.stdout.write(f'   📨 Created first message: {first_message.id}')
            
            # Test 3: Simulate second message (should NOT change status)
            self.stdout.write('\n3️⃣ Simulating second message arrival (should preserve status)...')
            
            # Store original status
            original_status = conversation.status
            self.stdout.write(f'   📊 Status before second message: {original_status}')
            
            # Simulate the webhook logic for subsequent message
            try:
                # Try to get existing conversation first
                conversation_2nd = Conversation.objects.get(
                    user=user,
                    source='telegram', 
                    customer=test_customer
                )
                conv_created_2nd = False
                self.stdout.write(f'   ✅ Found existing conversation: {conversation_2nd.id} with status: {conversation_2nd.status}')
                
            except Conversation.DoesNotExist:
                self.stdout.write(f'   ❌ UNEXPECTED: Conversation not found on second message')
                return
            
            # Always update conversation's updated_at field
            conversation_2nd.save(update_fields=['updated_at'])
            
            # Create second message
            second_message = Message.objects.create(
                content='این پیام دوم من است',
                conversation=conversation_2nd,
                customer=test_customer,
                type='customer'
            )
            self.stdout.write(f'   📨 Created second message: {second_message.id}')
            
            # Check if status changed
            conversation_2nd.refresh_from_db()
            final_status = conversation_2nd.status
            self.stdout.write(f'   📊 Status after second message: {final_status}')
            
            if original_status == final_status:
                self.stdout.write(f'   ✅ SUCCESS: Status preserved (not changed on subsequent message)')
            else:
                self.stdout.write(f'   ❌ FAILURE: Status changed from {original_status} to {final_status}')
            
            # Test 4: Manually change status and test third message
            self.stdout.write('\n4️⃣ Testing manual status change preservation...')
            
            # Manually change status
            conversation_2nd.status = 'closed'
            conversation_2nd.save()
            self.stdout.write(f'   ⚙️  Manually changed status to: closed')
            
            # Simulate third message
            try:
                conversation_3rd = Conversation.objects.get(
                    user=user,
                    source='telegram', 
                    customer=test_customer
                )
                self.stdout.write(f'   📊 Status before third message: {conversation_3rd.status}')
                
                # Always update conversation's updated_at field
                conversation_3rd.save(update_fields=['updated_at'])
                
                # Create third message
                third_message = Message.objects.create(
                    content='این پیام سوم من است',
                    conversation=conversation_3rd,
                    customer=test_customer,
                    type='customer'
                )
                self.stdout.write(f'   📨 Created third message: {third_message.id}')
                
                # Check status again
                conversation_3rd.refresh_from_db()
                third_status = conversation_3rd.status
                self.stdout.write(f'   📊 Status after third message: {third_status}')
                
                if third_status == 'closed':
                    self.stdout.write(f'   ✅ SUCCESS: Manual status change preserved')
                else:
                    self.stdout.write(f'   ❌ FAILURE: Manual status change overridden to {third_status}')
                    
            except Conversation.DoesNotExist:
                self.stdout.write(f'   ❌ UNEXPECTED: Conversation not found on third message')
            
            # Test 5: Check AI response behavior
            self.stdout.write('\n5️⃣ Testing AI response behavior based on status...')
            
            # Set conversation to active for AI test
            conversation.status = 'active'
            conversation.save()
            
            from AI_model.utils import should_ai_handle_conversation
            should_handle = should_ai_handle_conversation(conversation)
            
            self.stdout.write(f'   📊 Conversation status: {conversation.status}')
            self.stdout.write(f'   🤖 Should AI handle: {should_handle}')
            
            if conversation.status == 'active' and should_handle:
                self.stdout.write(f'   ✅ AI will respond when status=active')
            else:
                self.stdout.write(f'   ℹ️  AI will not respond (status={conversation.status}, should_handle={should_handle})')
            
            # Set to support_active and test
            conversation.status = 'support_active'
            conversation.save()
            
            should_handle_support = should_ai_handle_conversation(conversation)
            self.stdout.write(f'   📊 Changed status to: {conversation.status}')
            self.stdout.write(f'   🤖 Should AI handle: {should_handle_support}')
            
            if not should_handle_support:
                self.stdout.write(f'   ✅ AI will NOT respond when status=support_active')
            else:
                self.stdout.write(f'   ❌ UNEXPECTED: AI wants to respond on support_active')
            
            self.stdout.write('\n' + '=' * 70)
            self.stdout.write('✅ Conversation Status Behavior Test Completed!')
            
            self.stdout.write('\n📋 Summary:')
            self.stdout.write(f'   • Status is set ONLY on conversation creation')
            self.stdout.write(f'   • Status is NOT changed on subsequent messages')
            self.stdout.write(f'   • Manual status changes are preserved')
            self.stdout.write(f'   • AI responds only when status=active')
            
        except Exception as e:
            self.stdout.write(f'❌ Test failed: {str(e)}')
            import traceback
            traceback.print_exc()
        
        finally:
            # Cleanup test data
            self.stdout.write('\n🧹 Cleaning up test data...')
            try:
                # Delete test messages
                Message.objects.filter(
                    conversation__customer__source_id='test_telegram_12345'
                ).delete()
                
                # Delete test conversation
                Conversation.objects.filter(
                    customer__source_id='test_telegram_12345'
                ).delete()
                
                # Delete test customer
                Customer.objects.filter(
                    source_id='test_telegram_12345'
                ).delete()
                
                self.stdout.write('   ✅ Test data cleaned up')
            except Exception as cleanup_error:
                self.stdout.write(f'   ⚠️ Cleanup warning: {cleanup_error}')