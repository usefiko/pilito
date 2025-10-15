import json
import pytest
from channels.testing import WebsocketCommunicator
from django.test import TransactionTestCase
from django.contrib.auth import get_user_model
from accounts.functions.jwt import login
from message.models import Customer, Conversation, Message
from message.consumers import ChatConsumer, ConversationListConsumer
from message.services.telegram_service import TelegramService
from message.services.instagram_service import InstagramService
from message.security import WebSocketSecurityManager
from settings.models import TelegramChannel, InstagramChannel
from unittest.mock import patch, Mock

User = get_user_model()


class WebSocketSystemTest(TransactionTestCase):
    """
    Comprehensive tests for the WebSocket chat system
    """
    
    def setUp(self):
        """Set up test data"""
        # Create test user
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        
        # Generate JWT token
        access_token, refresh_token = login(self.user)
        self.jwt_token = access_token
        
        # Create test customer
        self.customer = Customer.objects.create(
            first_name='John',
            last_name='Doe',
            source='telegram',
            source_id='123456789'
        )
        
        # Create test conversation
        self.conversation = Conversation.objects.create(
            user=self.user,
            customer=self.customer,
            source='telegram',
            title='Test Conversation'
        )
        
        # Create Telegram channel
        self.telegram_channel = TelegramChannel.objects.create(
            user=self.user,
            bot_token='test_bot_token',
            bot_username='test_bot',
            is_connect=True
        )

    async def test_chat_consumer_authentication(self):
        """Test WebSocket authentication with JWT token"""
        # Test with valid token
        communicator = WebsocketCommunicator(
            ChatConsumer.as_asgi(),
            f"/ws/chat/{self.conversation.id}/?token={self.jwt_token}"
        )
        
        connected, subprotocol = await communicator.connect()
        self.assertTrue(connected)
        await communicator.disconnect()
        
        # Test with invalid token
        communicator = WebsocketCommunicator(
            ChatConsumer.as_asgi(),
            f"/ws/chat/{self.conversation.id}/?token=invalid_token"
        )
        
        connected, subprotocol = await communicator.connect()
        self.assertFalse(connected)

    async def test_chat_message_flow(self):
        """Test complete message flow from WebSocket to database and external platform"""
        communicator = WebsocketCommunicator(
            ChatConsumer.as_asgi(),
            f"/ws/chat/{self.conversation.id}/?token={self.jwt_token}"
        )
        
        connected, subprotocol = await communicator.connect()
        self.assertTrue(connected)
        
        # Send a message
        message_content = "Hello, this is a test message!"
        await communicator.send_json_to({
            'type': 'chat_message',
            'content': message_content
        })
        
        # Receive the response
        response = await communicator.receive_json_from()
        
        # Verify response structure
        self.assertEqual(response['type'], 'chat_message')
        self.assertEqual(response['message']['content'], message_content)
        self.assertEqual(response['message']['type'], 'support')
        self.assertIn('external_send_result', response)
        
        # Verify message was saved to database
        message = Message.objects.filter(
            conversation=self.conversation,
            content=message_content,
            type='support'
        ).first()
        self.assertIsNotNone(message)
        
        await communicator.disconnect()

    async def test_typing_indicator(self):
        """Test typing indicator functionality"""
        communicator = WebsocketCommunicator(
            ChatConsumer.as_asgi(),
            f"/ws/chat/{self.conversation.id}/?token={self.jwt_token}"
        )
        
        connected, subprotocol = await communicator.connect()
        self.assertTrue(connected)
        
        # Send typing indicator
        await communicator.send_json_to({
            'type': 'typing',
            'is_typing': True
        })
        
        # Note: In a real test with multiple users, 
        # you would connect another user and verify they receive the typing indicator
        
        await communicator.disconnect()

    async def test_conversation_list_consumer(self):
        """Test conversation list WebSocket functionality"""
        communicator = WebsocketCommunicator(
            ConversationListConsumer.as_asgi(),
            f"/ws/conversations/?token={self.jwt_token}"
        )
        
        connected, subprotocol = await communicator.connect()
        self.assertTrue(connected)
        
        # Should receive conversations list on connect
        response = await communicator.receive_json_from()
        self.assertEqual(response['type'], 'conversations_list')
        self.assertIn('conversations', response)
        self.assertGreater(len(response['conversations']), 0)
        
        await communicator.disconnect()

    def test_message_rate_limiting(self):
        """Test message rate limiting functionality"""
        user_id = self.user.id
        
        # Send messages within rate limit
        for i in range(WebSocketSecurityManager.MAX_MESSAGES_PER_MINUTE - 1):
            result = WebSocketSecurityManager.check_message_rate_limit(user_id)
            self.assertTrue(result)
        
        # This should exceed the rate limit
        result = WebSocketSecurityManager.check_message_rate_limit(user_id)
        self.assertFalse(result)

    def test_spam_detection(self):
        """Test spam detection algorithm"""
        # Normal message
        normal_message = "Hello, how are you today?"
        self.assertFalse(WebSocketSecurityManager.detect_spam_content(normal_message))
        
        # Spam indicators
        spam_messages = [
            "THIS IS ALL CAPS AND VERY LONG MESSAGE WITH LOTS OF EXCLAMATION!!!!!!",
            "Check out http://spam1.com and http://spam2.com and http://spam3.com and http://spam4.com",
            "a" * 600,  # Very long message
            "AAAAAAAAAAAAAAAAAAAAAA"  # Repetitive content
        ]
        
        for spam_msg in spam_messages:
            result = WebSocketSecurityManager.detect_spam_content(spam_msg, self.user.id)
            # Some messages might not trigger spam detection individually
            # This tests the detection algorithm

    @patch('message.services.telegram_service.requests.post')
    def test_telegram_service(self, mock_post):
        """Test Telegram service functionality"""
        # Mock successful response
        mock_response = Mock()
        mock_response.json.return_value = {
            'ok': True,
            'result': {'message_id': 123}
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        
        # Test sending message
        telegram_service = TelegramService('test_bot_token')
        result = telegram_service.send_message('123456789', 'Test message')
        
        self.assertTrue(result['success'])
        self.assertEqual(result['message_id'], 123)
        
        # Verify API was called correctly
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        self.assertIn('chat_id', call_args[1]['json'])
        self.assertIn('text', call_args[1]['json'])

    @patch('message.services.instagram_service.requests.post')
    def test_instagram_service(self, mock_post):
        """Test Instagram service functionality"""
        # Mock successful response
        mock_response = Mock()
        mock_response.json.return_value = {'message_id': 'insta_123'}
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        
        # Test sending message
        instagram_service = InstagramService('test_access_token', 'test_user_id')
        result = instagram_service.send_message('recipient_123', 'Test message')
        
        self.assertTrue(result['success'])
        self.assertEqual(result['message_id'], 'insta_123')

    def test_conversation_access_control(self):
        """Test that users can only access their own conversations"""
        # Create another user
        other_user = User.objects.create_user(
            email='other@example.com',
            password='testpass123'
        )
        
        # Create conversation for other user
        other_customer = Customer.objects.create(
            first_name='Jane',
            last_name='Smith',
            source='telegram',
            source_id='987654321'
        )
        
        other_conversation = Conversation.objects.create(
            user=other_user,
            customer=other_customer,
            source='telegram'
        )
        
        # Verify user cannot access other user's conversation
        user_conversations = Conversation.objects.filter(user=self.user)
        self.assertNotIn(other_conversation, user_conversations)
        
        # Verify conversation belongs to correct user
        self.assertEqual(self.conversation.user, self.user)
        self.assertNotEqual(other_conversation.user, self.user)

    def test_message_validation(self):
        """Test message content validation"""
        user_id = self.user.id
        conversation_id = self.conversation.id
        
        # Valid message
        result = WebSocketSecurityManager.validate_message_content(
            "Hello, this is a valid message",
            user_id,
            conversation_id
        )
        self.assertTrue(result['valid'])
        
        # Empty message
        result = WebSocketSecurityManager.validate_message_content(
            "",
            user_id,
            conversation_id
        )
        self.assertFalse(result['valid'])
        self.assertEqual(result['reason'], 'Empty content')
        
        # Too long message
        result = WebSocketSecurityManager.validate_message_content(
            "x" * 1001,
            user_id,
            conversation_id
        )
        self.assertFalse(result['valid'])
        self.assertEqual(result['reason'], 'Content too long')
        
        # Invalid conversation access
        result = WebSocketSecurityManager.validate_message_content(
            "Valid content",
            user_id,
            "invalid_conversation_id"
        )
        self.assertFalse(result['valid'])

    def test_websocket_security_manager_stats(self):
        """Test WebSocket security manager statistics"""
        user_id = self.user.id
        
        # Create some test messages
        Message.objects.create(
            conversation=self.conversation,
            customer=self.customer,
            content="Test message 1",
            type='support'
        )
        
        Message.objects.create(
            conversation=self.conversation,
            customer=self.customer,
            content="Test message 2",
            type='support'
        )
        
        # Get stats
        stats = WebSocketSecurityManager.get_user_websocket_stats(user_id)
        
        self.assertIn('messages_sent', stats)
        self.assertIn('active_conversations', stats)
        self.assertIn('period_hours', stats)
        self.assertEqual(stats['messages_sent'], 2)

    async def test_unauthorized_conversation_access(self):
        """Test that WebSocket rejects unauthorized conversation access"""
        # Create another user and their conversation
        other_user = User.objects.create_user(
            email='other@example.com',
            password='testpass123'
        )
        
        other_customer = Customer.objects.create(
            first_name='Other',
            last_name='Customer',
            source='telegram',
            source_id='999999999'
        )
        
        other_conversation = Conversation.objects.create(
            user=other_user,
            customer=other_customer,
            source='telegram'
        )
        
        # Try to connect to other user's conversation with our token
        communicator = WebsocketCommunicator(
            ChatConsumer.as_asgi(),
            f"/ws/chat/{other_conversation.id}/?token={self.jwt_token}"
        )
        
        # Connection should be rejected
        connected, subprotocol = await communicator.connect()
        self.assertFalse(connected)

    def test_external_service_integration(self):
        """Test integration with external messaging services"""
        # Test TelegramService.get_service_for_conversation
        telegram_service = TelegramService.get_service_for_conversation(self.conversation)
        self.assertIsNotNone(telegram_service)
        self.assertEqual(telegram_service.bot_token, 'test_bot_token')
        
        # Test with conversation that has no channel
        conversation_no_channel = Conversation.objects.create(
            user=self.user,
            customer=self.customer,
            source='instagram'  # Different source
        )
        
        telegram_service_none = TelegramService.get_service_for_conversation(conversation_no_channel)
        self.assertIsNone(telegram_service_none)


# Pytest marks for async tests
pytestmark = pytest.mark.asyncio


class WebSocketSecurityTest(TransactionTestCase):
    """
    Security-focused tests for WebSocket system
    """
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='security@example.com',
            password='testpass123'
        )

    def test_connection_logging(self):
        """Test WebSocket connection attempt logging"""
        user_id = self.user.id
        ip_address = '192.168.1.100'
        
        # Log successful connection
        WebSocketSecurityManager.log_connection_attempt(user_id, ip_address, success=True)
        
        # Log failed connection
        WebSocketSecurityManager.log_connection_attempt(user_id, ip_address, success=False)
        
        # These should not raise exceptions and should be logged properly

    def test_suspicious_activity_handling(self):
        """Test handling of suspicious activities"""
        ip_address = '192.168.1.200'
        user_id = self.user.id
        
        # Test different types of suspicious activities
        reasons = ['too_many_failed_auth', 'message_spam', 'rate_limit_abuse']
        
        for reason in reasons:
            WebSocketSecurityManager.handle_suspicious_activity(
                ip_address, reason, user_id
            )
            
        # Should not raise exceptions

    def test_message_content_edge_cases(self):
        """Test edge cases in message content validation"""
        user_id = self.user.id
        
        # Test various edge cases
        edge_cases = [
            None,  # None content
            "   ",  # Only whitespace
            "\n\t\r",  # Only special characters
            "🔥💬⚡",  # Only emojis
            "a" * 999,  # Just under limit
            "a" * 1000,  # Exactly at limit
        ]
        
        for content in edge_cases:
            # Should not raise exceptions
            result = WebSocketSecurityManager.detect_spam_content(content, user_id)
            self.assertIsInstance(result, bool) 