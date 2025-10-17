"""
Marketing Workflow Settings Adapters

This module provides compatibility adapters to map the existing project's
model fields and choices to canonical keys used by the marketing workflow system.
"""

from typing import Dict, List, Optional, Any
from django.conf import settings


# Field name mappings
FIELD_MAPPINGS = {
    # User model field mappings (Customer is used as user proxy)
    'USER_MODEL': 'message.Customer',
    'USER_ID_FIELD': 'id',
    'USER_EMAIL_FIELD': 'email',
    'USER_FIRST_NAME_FIELD': 'first_name',
    'USER_LAST_NAME_FIELD': 'last_name',
    'USER_USERNAME_FIELD': 'username',
    'USER_TAGS_FIELD': 'tag',  # M2M field
    'USER_SOURCE_ID_FIELD': 'source_id',  # telegram_id/instagram_id
    'USER_SOURCE_FIELD': 'source',
    
    # Conversation model field mappings
    'CONVERSATION_MODEL': 'message.Conversation',
    'CONVERSATION_ID_FIELD': 'id',
    'CONVERSATION_USER_FIELD': 'customer',  # FK to Customer (user proxy)
    'CONVERSATION_STATUS_FIELD': 'status',
    'CONVERSATION_SOURCE_FIELD': 'source',
    'CONVERSATION_CREATED_AT_FIELD': 'created_at',
    'CONVERSATION_UPDATED_AT_FIELD': 'updated_at',
    
    # Message model field mappings
    'MESSAGE_MODEL': 'message.Message',
    'MESSAGE_ID_FIELD': 'id',
    'MESSAGE_CONVERSATION_FIELD': 'conversation',
    'MESSAGE_CONTENT_FIELD': 'content',
    'MESSAGE_SENDER_TYPE_FIELD': 'type',
    'MESSAGE_METADATA_FIELD': 'metadata',
    'MESSAGE_CREATED_AT_FIELD': 'created_at',
    'MESSAGE_CUSTOMER_FIELD': 'customer',
}


def get_conversation_status_values() -> Dict[str, str]:
    """
    Get the actual conversation status values from the project.
    Returns a mapping of canonical status names to project-specific values.
    """
    return {
        'ACTIVE': 'active',
        'MARKETING_ACTIVE': 'marketing_active',
        'SUPPORT_ACTIVE': 'support_active',
        'CLOSED': 'closed',
    }


def get_sender_type_values() -> Dict[str, str]:
    """
    Get the actual message sender type values from the project.
    Returns a mapping of canonical sender types to project-specific values.
    """
    return {
        'CUSTOMER': 'customer',
        'AI': 'AI',
        'SUPPORT': 'support',
        'MARKETING': 'marketing',
    }


def get_source_values() -> Dict[str, str]:
    """
    Get the actual source values from the project.
    """
    return {
        'TELEGRAM': 'telegram',
        'INSTAGRAM': 'instagram',
        'UNKNOWN': 'unknown',
    }


def get_model_class(canonical_name: str):
    """
    Get the actual Django model class for a canonical model name.
    
    Args:
        canonical_name: One of 'USER', 'CONVERSATION', 'MESSAGE'
    
    Returns:
        Django model class
    """
    from django.apps import apps
    
    model_mappings = {
        'USER': FIELD_MAPPINGS['USER_MODEL'],
        'CONVERSATION': FIELD_MAPPINGS['CONVERSATION_MODEL'],
        'MESSAGE': FIELD_MAPPINGS['MESSAGE_MODEL'],
    }
    
    if canonical_name not in model_mappings:
        raise ValueError(f"Unknown canonical model name: {canonical_name}")
    
    app_label, model_name = model_mappings[canonical_name].split('.')
    return apps.get_model(app_label, model_name)


def get_field_name(model_canonical_name: str, field_canonical_name: str) -> str:
    """
    Get the actual field name for a canonical field name.
    
    Args:
        model_canonical_name: One of 'USER', 'CONVERSATION', 'MESSAGE'
        field_canonical_name: The canonical field name (e.g., 'ID_FIELD', 'EMAIL_FIELD')
    
    Returns:
        Actual field name in the project
    """
    mapping_key = f"{model_canonical_name}_{field_canonical_name}"
    
    if mapping_key not in FIELD_MAPPINGS:
        raise ValueError(f"Unknown field mapping: {mapping_key}")
    
    return FIELD_MAPPINGS[mapping_key]


def check_marketing_active_status_available() -> bool:
    """
    Check if the 'marketing_active' status is available in the Conversation model.
    """
    status_values = get_conversation_status_values()
    return 'MARKETING_ACTIVE' in status_values


def get_telegram_id_from_user(user_instance) -> Optional[str]:
    """
    Extract telegram ID from user instance (Customer).
    
    Args:
        user_instance: Customer instance
    
    Returns:
        Telegram ID if available and source is telegram, None otherwise
    """
    if hasattr(user_instance, 'source') and user_instance.source == 'telegram':
        return getattr(user_instance, 'source_id', None)
    return None


def get_instagram_id_from_user(user_instance) -> Optional[str]:
    """
    Extract Instagram ID from user instance (Customer).
    
    Args:
        user_instance: Customer instance
    
    Returns:
        Instagram ID if available and source is instagram, None otherwise
    """
    if hasattr(user_instance, 'source') and user_instance.source == 'instagram':
        return getattr(user_instance, 'source_id', None)
    return None


def get_user_tags(user_instance) -> List[str]:
    """
    Get tags associated with a user instance (Customer).
    
    Args:
        user_instance: Customer instance
    
    Returns:
        List of tag names
    """
    try:
        tags_field = get_field_name('USER', 'TAGS_FIELD')
        tags_manager = getattr(user_instance, tags_field)
        return list(tags_manager.values_list('name', flat=True))
    except Exception:
        return []


def add_user_tag(user_instance, tag_name: str) -> bool:
    """
    Add a tag to a user instance (Customer).
    
    Args:
        user_instance: Customer instance
        tag_name: Name of the tag to add
    
    Returns:
        True if tag was added successfully
    """
    try:
        from message.models import Tag
        
        # Get or create the tag
        tag, created = Tag.objects.get_or_create(name=tag_name)
        
        # Add to user
        tags_field = get_field_name('USER', 'TAGS_FIELD')
        tags_manager = getattr(user_instance, tags_field)
        tags_manager.add(tag)
        
        return True
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Failed to add tag '{tag_name}' to user {user_instance.id}: {e}")
        return False


def remove_user_tag(user_instance, tag_name: str) -> bool:
    """
    Remove a tag from a user instance (Customer).
    
    Args:
        user_instance: Customer instance
        tag_name: Name of the tag to remove
    
    Returns:
        True if tag was removed successfully
    """
    try:
        from message.models import Tag
        
        # Find the tag
        try:
            tag = Tag.objects.get(name=tag_name)
        except Tag.DoesNotExist:
            return True  # Tag doesn't exist, consider it "removed"
        
        # Remove from user
        tags_field = get_field_name('USER', 'TAGS_FIELD')
        tags_manager = getattr(user_instance, tags_field)
        tags_manager.remove(tag)
        
        return True
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Failed to remove tag '{tag_name}' from user {user_instance.id}: {e}")
        return False


# Environment variable mappings for external integrations
INTEGRATION_SETTINGS = {
    'TELEGRAM_BOT_TOKEN': getattr(settings, 'TELEGRAM_BOT_TOKEN', None),
    'N8N_WEBHOOK_URL': getattr(settings, 'N8N_WEBHOOK_URL', None),
    'DEFAULT_FROM_EMAIL': getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@pilito.com'),
}


def get_ai_fallback_task_info() -> Optional[Dict[str, Any]]:
    """
    Get information about the existing AI fallback task.
    
    Returns:
        Dict with task info if available, None otherwise
    """
    try:
        return {
            'task_name': 'AI_model.tasks.process_ai_response_async',
            'function_name': 'process_ai_response_async',
            'module_path': 'AI_model.tasks',
            'description': 'Existing AI auto-reply task for customer messages',
            'parameters': ['message_id'],
        }
    except Exception:
        return None


def call_ai_fallback_task(message_id: str, conversation_id: str) -> bool:
    """
    Call the existing AI fallback task.
    
    Args:
        message_id: ID of the message to process
        conversation_id: ID of the conversation (not used by current AI task)
    
    Returns:
        True if task was queued successfully
    """
    try:
        from AI_model.tasks import process_ai_response_async
        
        # Queue the AI processing task
        process_ai_response_async.delay(message_id)
        return True
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Failed to call AI fallback task for message {message_id}: {e}")
        return False
