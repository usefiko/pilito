"""
Utility functions for AI model integration
"""
import logging
from accounts.models import User

logger = logging.getLogger(__name__)


def get_initial_conversation_status(user: User) -> str:
    """
    Determine the initial status for a new conversation based on user's default_reply_handler
    
    Args:
        user: The User instance who owns the conversation
        
    Returns:
        str: Either 'active' (AI handles) or 'support_active' (Manual/Support handles)
    """
    try:
        # Check user's default reply handler preference
        if user.default_reply_handler == 'AI':
            # Verify AI is properly configured before setting to 'active'
            try:
                from AI_model.services.gemini_service import GeminiChatService
                from AI_model.models import AIGlobalConfig
                
                # Check if global AI is enabled
                global_config = AIGlobalConfig.get_config()
                if not global_config.auto_response_enabled:
                    logger.warning(f"Global AI is disabled. Setting conversation to 'support_active' for user {user.username}")
                    return 'support_active'
                
                # Check if AI service is configured
                ai_service = GeminiChatService(user)
                
                if ai_service.is_configured():
                    logger.info(f"Setting conversation to 'active' for user {user.username} - AI configured and enabled")
                    return 'active'
                else:
                    logger.warning(f"User {user.username} has default_reply_handler='AI' but AI service is not properly configured. Setting to 'support_active'")
                    return 'support_active'
                    
            except Exception as e:
                logger.error(f"Error checking AI configuration for user {user.username}: {str(e)}")
                return 'support_active'
        else:
            # default_reply_handler is 'Manual' or any other value
            logger.info(f"Setting conversation to 'support_active' for user {user.username} - default_reply_handler is '{user.default_reply_handler}'")
            return 'support_active'
            
    except Exception as e:
        logger.error(f"Error determining initial conversation status for user {user.username}: {str(e)}")
        return 'support_active'  # Default to manual handling on error


def should_ai_handle_conversation(conversation) -> bool:
    """
    Check if AI should handle a specific conversation
    
    Args:
        conversation: Conversation instance
        
    Returns:
        bool: True if AI should handle this conversation
    """
    try:
        # Only AI handles conversations with 'active' status
        if conversation.status != 'active':
            return False
        
        # Check if global AI is enabled
        from AI_model.models import AIGlobalConfig
        global_config = AIGlobalConfig.get_config()
        if not global_config.auto_response_enabled:
            return False
        
        # Check if AI is configured and enabled for the user
        from AI_model.services.gemini_service import GeminiChatService
        
        try:
            ai_service = GeminiChatService(conversation.user)
            return ai_service.is_configured()
        except Exception as e:
            logger.error(f"Error checking AI configuration for conversation {conversation.id}: {str(e)}")
            return False
            
    except Exception as e:
        logger.error(f"Error checking if AI should handle conversation {conversation.id}: {str(e)}")
        return False


def log_conversation_status_change(conversation, old_status: str, new_status: str, reason: str = ""):
    """
    Log conversation status changes for debugging and monitoring
    """
    try:
        logger.info(
            f"Conversation status changed: "
            f"ID={conversation.id}, User={conversation.user.username}, "
            f"Customer={conversation.customer}, Source={conversation.source}, "
            f"Status: {old_status} → {new_status}"
            f"{f', Reason: {reason}' if reason else ''}"
        )
    except Exception as e:
        logger.error(f"Error logging conversation status change: {str(e)}")


def validate_ai_configuration(user: User) -> dict:
    """
    Validate if AI is properly configured for a user
    
    Args:
        user: User instance to check
        
    Returns:
        dict: Validation result with status and details
    """
    try:
        from AI_model.services.gemini_service import GeminiChatService
        from AI_model.models import AIGlobalConfig
        
        result = {
            'is_valid': False,
            'global_enabled': False,
            'has_api_key': False,
            'user_configured': False,
            'has_prompts': False,
            'issues': []
        }
        
        # Check global configuration
        global_config = AIGlobalConfig.get_config()
        result['global_enabled'] = global_config.auto_response_enabled
        if not global_config.auto_response_enabled:
            result['issues'].append('Global AI auto-response is disabled')
        
        # Use the service to check configuration
        ai_service = GeminiChatService(user)
        config_status = ai_service.get_configuration_status()
        
        # Map service status to result
        result['has_api_key'] = config_status.get('api_key_configured', False)
        result['user_configured'] = config_status.get('model_initialized', False)
        result['has_prompts'] = config_status.get('ai_prompts_configured', False)
        
        # Check for issues
        if not config_status.get('gemini_available'):
            result['issues'].append('Gemini AI library not installed')
        
        if not config_status.get('api_key_configured'):
            result['issues'].append('Gemini API key not configured in service')
        
        if not config_status.get('model_initialized'):
            result['issues'].append('Gemini model could not be initialized')
        
        if not config_status.get('ai_prompts_configured'):
            result['issues'].append('AI prompts not configured')
        
        # Determine if configuration is valid
        result['is_valid'] = ai_service.is_configured() and global_config.auto_response_enabled
        
        return result
        
    except Exception as e:
        logger.error(f"Error validating AI configuration for user {user.username}: {str(e)}")
        return {
            'is_valid': False,
            'global_enabled': False,
            'has_api_key': False,
            'user_configured': False,
            'has_prompts': False,
            'issues': [f'Validation error: {str(e)}']
        }


def get_ai_usage_summary(user: User, days: int = 30) -> dict:
    """
    Get AI usage summary for a user
    
    Args:
        user: User instance
        days: Number of days to include in summary
        
    Returns:
        dict: Usage summary
    """
    try:
        from AI_model.models import AIUsageTracking
        from django.db.models import Sum
        from datetime import date, timedelta
        
        # Calculate date range
        end_date = date.today()
        start_date = end_date - timedelta(days=days-1)
        
        # Get usage data
        usage_records = AIUsageTracking.objects.filter(
            user=user,
            date__gte=start_date,
            date__lte=end_date
        )
        
        # Calculate totals
        aggregates = usage_records.aggregate(
            total_requests=Sum('total_requests'),
            total_tokens=Sum('total_tokens'),
            successful_requests=Sum('successful_requests'),
            failed_requests=Sum('failed_requests')
        )
        
        total_requests = aggregates['total_requests'] or 0
        successful_requests = aggregates['successful_requests'] or 0
        success_rate = (successful_requests / total_requests * 100) if total_requests > 0 else 0
        
        return {
            'user': user.username,
            'period_days': days,
            'total_requests': total_requests,
            'total_tokens': aggregates['total_tokens'] or 0,
            'successful_requests': successful_requests,
            'failed_requests': aggregates['failed_requests'] or 0,
            'success_rate': round(success_rate, 2),
            'date_range': {
                'start': start_date.isoformat(),
                'end': end_date.isoformat()
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting AI usage summary for user {user.username}: {str(e)}")
        return {
            'user': user.username,
            'error': str(e),
            'total_requests': 0,
            'total_tokens': 0,
            'success_rate': 0
        }