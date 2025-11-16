"""
Integration service for AI model with existing message system
Uses existing Message model instead of separate chat models
"""
import logging
import re
from typing import Dict, Any, Optional
from django.utils import timezone

logger = logging.getLogger(__name__)

# Minimum tokens required for AI response
# Changed from 100 to 500 to prevent partial free usage
# Average AI response: 300-800 tokens
# Based on actual usage data: average 1500-2000 tokens (input + output)
MINIMUM_TOKENS_FOR_AI = 1500


def _is_only_url(text: str) -> bool:
    """
    Check if message is just a URL with no meaningful text.
    Used to prevent AI hallucination on link-only messages.
    
    Args:
        text: Original user message text
        
    Returns:
        True if message contains only URL(s) with minimal/no additional text
    """
    if not text:
        return False
        
    text = text.strip()
    
    # Find all URLs
    url_pattern = r'https?://\S+'
    urls = re.findall(url_pattern, text)
    
    if not urls:
        return False
    
    # Remove URLs from text
    text_without_urls = re.sub(url_pattern, '', text).strip()
    
    # Remove common punctuation and whitespace
    text_without_urls = re.sub(r'[،,\.؟?\s]+', '', text_without_urls)
    
    # If remaining text is very short (< 10 chars), consider it "only URL"
    return len(text_without_urls) < 10


class MessageSystemIntegration:
    """
    Handles integration between AI model and existing Message system
    """
    
    def __init__(self, user):
        self.user = user
    
    def process_new_customer_message(self, message_instance) -> Dict[str, Any]:
        """
        Process a new customer message and generate AI response
        
        Args:
            message_instance: Message model instance
            
        Returns:
            Dict with processing result
        """
        try:
            from AI_model.services.gemini_service import GeminiChatService
            
            # Check if AI should handle this conversation
            if not self._should_process_message(message_instance):
                return {
                    'processed': False,
                    'reason': 'AI not enabled for this conversation or user'
                }
            
            # ✅ GUARD: Check if message is ONLY a URL (no context)
            # Prevents AI hallucination on link-only messages (e.g., case T2epjS)
            # Only check for text messages (not shares or combined content)
            original_message_text = message_instance.content
            if (message_instance.message_type == 'text' and 
                _is_only_url(original_message_text)):
                
                logger.info(
                    f"🔗 Message {message_instance.id} is only URL - returning static response "
                    f"(anti-hallucination guard)"
                )
                
                # Return fixed response - do NOT call AI
                from settings.models import GeneralSettings
                settings = GeneralSettings.get_settings()
                static_response = (
                    "متأسفانه من نمی‌تونم محتوای لینک‌ها را ببینم. "
                    "اگر سوالی راجع به این لینک داری، لطفاً با متن توضیح بده تا بتونم کمکت کنم. 😊"
                )
                
                # Create AI response message
                from message.models import Message
                response_message = Message.objects.create(
                    conversation=message_instance.conversation,
                    content=static_response,
                    type='operator',
                    is_ai_response=True
                )
                
                return {
                    'processed': True,
                    'response': static_response,
                    'response_message': response_message,
                    'reason': 'url_only_guard'
                }
            
            # ✅ CHECK TOKENS BEFORE AI CALL
            token_check = self._check_user_tokens()
            if not token_check['has_tokens']:
                logger.warning(
                    f"User {self.user.username} has insufficient tokens. "
                    f"Remaining: {token_check.get('tokens_remaining', 0)}"
                )
                
                # ❌ DO NOT send notification to conversation!
                # User is chatting with their CUSTOMERS, not with the system
                # Frontend will show token status in dashboard
                
                return {
                    'processed': False,
                    'reason': token_check.get('reason', 'Insufficient tokens'),
                    'tokens_remaining': token_check.get('tokens_remaining', 0),
                    'error_type': 'insufficient_tokens'
                }
            
            # Initialize AI service
            ai_service = GeminiChatService(self.user)
            
            if not ai_service.is_configured():
                logger.warning(f"AI not configured for user {self.user.username}")
                return {
                    'processed': False,
                    'reason': 'AI not configured'
                }
            
            # Generate AI response
            ai_response = ai_service.generate_response(
                customer_message=message_instance.content,
                conversation=message_instance.conversation
            )
            
            if ai_response['success']:
                # Create AI response message using the service
                ai_message = ai_service.create_ai_message(
                    conversation=message_instance.conversation,
                    ai_response=ai_response
                )
                
                if ai_message:
                    # Mark original message as answered
                    message_instance.is_answered = True
                    message_instance.save()
                    
                    # Send real-time notification if available
                    self._send_realtime_notification(ai_message)
                    
                    logger.info(f"Successfully processed message {message_instance.id} with AI response {ai_message.id}")
                    return {
                        'processed': True,
                        'ai_message_id': ai_message.id,
                        'response_time_ms': ai_response.get('response_time_ms', 0)
                    }
                else:
                    logger.error(f"Failed to create AI message for {message_instance.id}")
                    return {
                        'processed': False,
                        'reason': 'Failed to create AI message'
                    }
            else:
                # Handle specific AI configuration errors
                error_code = ai_response.get('error', '')
                if error_code == 'AI_PROMPTS_NOT_CONFIGURED':
                    logger.error(f"❌ AI Prompts not configured for user {self.user.username}. "
                               f"Please create AIPrompts in admin panel.")
                    return {
                        'processed': False,
                        'reason': 'AI prompts not configured',
                        'user_action_required': 'Configure AI prompts in admin panel',
                        'error_type': 'configuration_error'
                    }
                elif error_code == 'MANUAL_PROMPT_NOT_SET':
                    logger.error(f"❌ Manual prompt not set for user {self.user.username}. "
                               f"Please set manual_prompt field in AI prompts.")
                    return {
                        'processed': False,
                        'reason': 'Manual prompt not set',
                        'user_action_required': 'Set manual_prompt in AI prompts configuration',
                        'error_type': 'configuration_error'
                    }
                else:
                    logger.error(f"AI response failed for message {message_instance.id}: {ai_response.get('response', 'Unknown error')}")
                    return {
                        'processed': False,
                        'reason': f"AI generation failed: {ai_response.get('response', 'Unknown error')}"
                    }
                
        except Exception as e:
            logger.error(f"Error processing customer message {message_instance.id}: {str(e)}")
            return {
                'processed': False,
                'reason': f"Processing error: {str(e)}"
            }
    
    def _check_user_tokens(self) -> Dict[str, Any]:
        """
        Check if user has enough tokens for AI processing
        
        Returns:
            Dict with token check results
        """
        try:
            from billing.models import Subscription
            
            try:
                subscription = self.user.subscription
            except Subscription.DoesNotExist:
                logger.warning(f"User {self.user.username} has no subscription")
                return {
                    'has_tokens': False,
                    'reason': 'no_subscription',
                    'tokens_remaining': 0
                }
            
            # Check if subscription is active
            if not subscription.is_subscription_active():
                logger.warning(
                    f"User {self.user.username} subscription is not active. "
                    f"Status: {subscription.status}, "
                    f"Tokens: {subscription.tokens_remaining}, "
                    f"End date: {subscription.end_date}"
                )
                return {
                    'has_tokens': False,
                    'reason': 'subscription_inactive',
                    'tokens_remaining': subscription.tokens_remaining or 0
                }
            
            # Check if user has minimum required tokens
            tokens_remaining = subscription.tokens_remaining or 0
            if tokens_remaining < MINIMUM_TOKENS_FOR_AI:
                logger.warning(
                    f"User {self.user.username} has insufficient tokens. "
                    f"Required: {MINIMUM_TOKENS_FOR_AI}, "
                    f"Available: {tokens_remaining}"
                )
                return {
                    'has_tokens': False,
                    'reason': 'insufficient_tokens',
                    'tokens_remaining': tokens_remaining
                }
            
            # All checks passed
            return {
                'has_tokens': True,
                'tokens_remaining': tokens_remaining
            }
            
        except Exception as e:
            logger.error(f"Error checking tokens for user {self.user.username}: {str(e)}")
            return {
                'has_tokens': False,
                'reason': 'error_checking_tokens',
                'tokens_remaining': 0,
                'error': str(e)
            }
    
    def _should_process_message(self, message_instance) -> bool:
        """
        Check if a message should be processed by AI
        """
        try:
            # Only process customer messages
            if message_instance.type != 'customer':
                return False
            
            # Don't process if already answered or is AI response
            if message_instance.is_answered or getattr(message_instance, 'is_ai_response', False):
                return False
            
            # Check conversation status - AI should only respond when status is 'active'
            conversation = message_instance.conversation
            if conversation.status != 'active':
                logger.info(f"Skipping AI processing for conversation {conversation.id} - status is '{conversation.status}', not 'active'")
                return False
            
            # Check if AI is enabled globally
            from AI_model.models import AIGlobalConfig
            global_config = AIGlobalConfig.get_config()
            if not global_config.auto_response_enabled:
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error checking if message should be processed: {str(e)}")
            return False
    
    def _send_realtime_notification(self, ai_message):
        """
        Send real-time notification for new AI message
        Uses existing message app's WebSocket utilities
        """
        try:
            # Try to use existing message app's real-time system
            from message.utils import send_message_notification
            send_message_notification(ai_message)
            logger.info(f"Sent real-time notification for AI message {ai_message.id}")
        except ImportError:
            logger.warning("Message notification utility not found")
        except Exception as e:
            logger.error(f"Error sending real-time notification: {str(e)}")
    
    def enable_ai_for_conversation(self, conversation):
        """
        Enable AI for a specific conversation
        """
        try:
            conversation.status = 'active'
            conversation.save()
            logger.info(f"Enabled AI for conversation {conversation.id}")
        except Exception as e:
            logger.error(f"Error enabling AI for conversation {conversation.id}: {str(e)}")
    
    def disable_ai_for_conversation(self, conversation):
        """
        Disable AI for a specific conversation
        """
        try:
            conversation.status = 'support_active'
            conversation.save()
            logger.info(f"Disabled AI for conversation {conversation.id}")
        except Exception as e:
            logger.error(f"Error disabling AI for conversation {conversation.id}: {str(e)}")
    
    def get_conversation_ai_status(self, conversation) -> Dict[str, Any]:
        """
        Get AI status for a conversation
        """
        try:
            from AI_model.services.gemini_service import GeminiChatService
            from AI_model.models import AIGlobalConfig
            
            ai_service = GeminiChatService(self.user)
            global_config = AIGlobalConfig.get_config()
            
            return {
                'conversation_id': conversation.id,
                'status': conversation.status,
                'ai_handling': conversation.status == 'active',
                'ai_configured': ai_service.is_configured(),
                'global_ai_enabled': global_config.auto_response_enabled,
                'can_enable_ai': ai_service.is_configured() and global_config.auto_response_enabled,
                'user_has_prompts': ai_service.ai_prompts is not None
            }
            
        except Exception as e:
            logger.error(f"Error getting AI status for conversation {conversation.id}: {str(e)}")
            return {
                'conversation_id': conversation.id,
                'status': conversation.status,
                'ai_handling': False,
                'ai_configured': False,
                'error': str(e)
            }