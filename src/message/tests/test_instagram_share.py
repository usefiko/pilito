"""
Tests for Instagram Share Feature

Tests the delay logic for Instagram post/reel shares:
1. Share → Text: combines content
2. Share alone: timeout without AI response
3. Text without share: normal behavior
4. Two shares → Text: uses latest share
"""

from django.test import TestCase
from django.core.cache import cache
from message.models import Message, Conversation, Customer
from accounts.models import User
from unittest.mock import patch, MagicMock
import time


class InstagramShareDelayTestCase(TestCase):
    """
    Tests for Instagram Share delay logic
    """
    
    def setUp(self):
        """Setup test data"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@test.com',
            password='testpass123'
        )
        
        self.customer = Customer.objects.create(
            first_name='Test',
            last_name='Customer',
            source='instagram',
            source_id='ig_123456'
        )
        
        self.conversation = Conversation.objects.create(
            user=self.user,
            customer=self.customer,
            source='instagram',
            status='active'
        )
        
        # Clear cache before each test
        cache.clear()
    
    def tearDown(self):
        """Cleanup after test"""
        cache.clear()
    
    @patch('AI_model.tasks.process_ai_response_async.delay')
    @patch('message.tasks.process_pending_share_timeout.apply_async')
    def test_share_then_text_combines_content(self, mock_timeout, mock_ai):
        """
        ✅ Test 1: Share → Text
        Expected: content is combined, AI is called once for text
        """
        # 1. Create share message
        share_msg = Message.objects.create(
            conversation=self.conversation,
            customer=self.customer,
            type='customer',
            message_type='share',
            content="عنوان: لباس زیبا\nکپشن: این لباس خیلی شیکه",
            processing_status='completed'
        )
        
        # Check: timeout should be scheduled
        self.assertTrue(mock_timeout.called)
        
        # Check: AI should NOT be called for share alone
        self.assertFalse(mock_ai.called)
        
        # Check: cache should be set
        cache_key = f"pending_share_{self.conversation.id}"
        self.assertEqual(cache.get(cache_key), str(share_msg.id))
        
        # 2. Create text message
        mock_ai.reset_mock()
        text_msg = Message.objects.create(
            conversation=self.conversation,
            customer=self.customer,
            type='customer',
            message_type='text',
            content="این لباس چقدره؟"
        )
        
        # Check: content should be combined
        text_msg.refresh_from_db()
        self.assertIn("[CONTEXT:", text_msg.content)
        self.assertIn("لباس زیبا", text_msg.content)
        self.assertIn("چقدره؟", text_msg.content)
        
        # Check: cache should be cleared
        self.assertIsNone(cache.get(cache_key))
    
    @patch('AI_model.tasks.process_ai_response_async.delay')
    @patch('message.tasks.process_pending_share_timeout.apply_async')
    def test_share_alone_no_ai_response(self, mock_timeout, mock_ai):
        """
        ✅ Test 2: Share alone (without question)
        Expected: no AI response should be generated
        """
        # Create share message
        share_msg = Message.objects.create(
            conversation=self.conversation,
            customer=self.customer,
            type='customer',
            message_type='share',
            content="[پست/ریلز اینستاگرام]",
            processing_status='completed'
        )
        
        # Check: timeout scheduled
        self.assertTrue(mock_timeout.called)
        
        # Check: AI not called
        self.assertFalse(mock_ai.called)
        
        # Simulate timeout task
        from message.tasks import process_pending_share_timeout
        conversation_id = str(self.conversation.id)
        process_pending_share_timeout(conversation_id)
        
        # Check: cache cleared
        cache_key = f"pending_share_{conversation_id}"
        self.assertIsNone(cache.get(cache_key))
        
        # Check: no new messages created
        messages_count = Message.objects.filter(
            conversation=self.conversation
        ).count()
        self.assertEqual(messages_count, 1)  # Only the share
    
    @patch('AI_model.tasks.process_ai_response_async.delay')
    def test_text_without_pending_share_normal_behavior(self, mock_ai):
        """
        ✅ Test 3: Text without pending share
        Expected: normal behavior, no combine
        """
        original_content = "سلام، ساعت کاری شما چیه؟"
        
        text_msg = Message.objects.create(
            conversation=self.conversation,
            customer=self.customer,
            type='customer',
            message_type='text',
            content=original_content
        )
        
        # Check: content unchanged
        text_msg.refresh_from_db()
        self.assertEqual(text_msg.content, original_content)
        
        # Check: no share cache
        cache_key = f"pending_share_{self.conversation.id}"
        self.assertIsNone(cache.get(cache_key))
    
    @patch('AI_model.tasks.process_ai_response_async.delay')
    @patch('message.tasks.process_pending_share_timeout.apply_async')
    def test_two_shares_then_text_uses_latest(self, mock_timeout, mock_ai):
        """
        ✅ Test 4: Two Shares → Text
        Expected: only latest share is combined with text
        """
        # Share 1
        share1 = Message.objects.create(
            conversation=self.conversation,
            customer=self.customer,
            type='customer',
            message_type='share',
            content="کپشن: پست اول",
            processing_status='completed'
        )
        
        # Share 2 (overwrites cache)
        share2 = Message.objects.create(
            conversation=self.conversation,
            customer=self.customer,
            type='customer',
            message_type='share',
            content="کپشن: پست دوم",
            processing_status='completed'
        )
        
        # Check: cache is on share2
        cache_key = f"pending_share_{self.conversation.id}"
        self.assertEqual(cache.get(cache_key), str(share2.id))
        
        # Text
        text_msg = Message.objects.create(
            conversation=self.conversation,
            customer=self.customer,
            type='customer',
            message_type='text',
            content="نظرت چیه؟"
        )
        
        # Check: only share2 in content
        text_msg.refresh_from_db()
        self.assertIn("پست دوم", text_msg.content)
        self.assertNotIn("پست اول", text_msg.content)
    
    def test_share_message_created_with_correct_type(self):
        """
        Test that share messages are created with correct message_type
        """
        share_msg = Message.objects.create(
            conversation=self.conversation,
            customer=self.customer,
            type='customer',
            message_type='share',
            content="کپشن: تست",
            processing_status='completed'
        )
        
        self.assertEqual(share_msg.message_type, 'share')
        self.assertEqual(share_msg.processing_status, 'completed')

