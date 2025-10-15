"""
Condition Evaluator Utilities

Pure functions to evaluate rule-trees and extract dot-path values from context data.
Supports complex condition evaluation with secure custom code execution.
"""

import re
import json
import logging
import operator
from typing import Any, Dict, List, Union, Optional
from datetime import datetime, date
from decimal import Decimal

logger = logging.getLogger(__name__)


def get_nested_value(data: Dict[str, Any], path: str, default: Any = None) -> Any:
    """
    Extract a value from nested dictionary using dot notation.
    
    Args:
        data: The data dictionary
        path: Dot-separated path (e.g., 'user.profile.name')
        default: Default value if path not found
    
    Returns:
        The value at the path or default if not found
    
    Examples:
        >>> data = {'user': {'profile': {'name': 'John'}}}
        >>> get_nested_value(data, 'user.profile.name')
        'John'
        >>> get_nested_value(data, 'user.missing.field', 'default')
        'default'
    """
    try:
        keys = path.split('.')
        value = data
        
        for key in keys:
            if isinstance(value, dict):
                value = value.get(key)
            elif isinstance(value, list) and key.isdigit():
                index = int(key)
                if 0 <= index < len(value):
                    value = value[index]
                else:
                    value = None
            else:
                value = None
            
            if value is None:
                return default
        
        return value
    except Exception as e:
        logger.debug(f"Error getting nested value for path '{path}': {e}")
        return default


def normalize_value(value: Any) -> Any:
    """
    Normalize a value for comparison operations.
    
    Args:
        value: The value to normalize
    
    Returns:
        Normalized value
    """
    if value is None:
        return None
    
    # Convert strings to appropriate types for comparison
    if isinstance(value, str):
        # Try to convert to number if it looks like one
        if value.isdigit():
            return int(value)
        try:
            if '.' in value:
                return float(value)
        except ValueError:
            pass
        
        # Convert boolean strings
        if value.lower() in ('true', 'yes', 'on', '1'):
            return True
        elif value.lower() in ('false', 'no', 'off', '0'):
            return False
    
    return value


def evaluate_ai_condition(condition: Dict[str, Any], context: Dict[str, Any]) -> bool:
    """
    Evaluate an AI-based condition using AI model.
    
    Args:
        condition: AI condition with prompt
        context: Context data containing message and user info
    
    Returns:
        True if AI determines condition is met, False otherwise
    """
    try:
        # Support both 'prompt' and 'ai_prompt' for compatibility
        ai_prompt = condition.get('prompt', condition.get('ai_prompt', ''))
        if not ai_prompt:
            logger.warning("AI condition missing prompt")
            return False
        
        # Get message content from context - try multiple paths
        message_content = (
            get_nested_value(context, 'event.data.content') or
            get_nested_value(context, 'message.content') or
            get_nested_value(context, 'message_content') or
            ''
        )
        if not message_content:
            logger.warning("No message content found for AI condition evaluation")
            return False
        
        # Use GeminiChatService for boolean evaluation
        try:
            from AI_model.services.gemini_service import GeminiChatService
            # Try to identify owner user from conversation context
            owner_user = None
            conversation_inst = None
            try:
                conversation_id = (
                    get_nested_value(context, 'event.conversation_id') or
                    get_nested_value(context, 'conversation.id')
                )
                if conversation_id:
                    from message.models import Conversation as ConvModel
                    conversation_inst = ConvModel.objects.select_related('user').get(id=conversation_id)
                    owner_user = conversation_inst.user
            except Exception as ue:
                logger.warning(f"Could not resolve conversation owner for AI condition: {ue}")
            # Initialize AI chat service (owner_user may be None; service handles global key)
            ai_chat = GeminiChatService(owner_user)
            # Build a strict boolean evaluation input as the customer_message
            customer_message = (
                f"Question: {ai_prompt}\n"
                f"Message: {message_content}\n"
                f"Answer with only one word: true or false."
            )
            ai_res = ai_chat.generate_response(customer_message, conversation_inst)
            ai_text = ''
            if isinstance(ai_res, dict):
                ai_text = (ai_res.get('response') or '').strip().lower()
            else:
                ai_text = str(ai_res).strip().lower()
            # Normalize and parse boolean-like responses
            truthy = ['true', 'yes', 'بله', '1']
            falsy = ['false', 'no', 'خیر', '0']
            if any(tok == ai_text for tok in truthy):
                logger.info(
                    "[ConditionNode][AI] prompt='%s' message='%s' ai_text='%s' -> True",
                    ai_prompt, str(message_content)[:200], ai_text
                )
                return True
            if any(tok == ai_text for tok in falsy):
                logger.info(
                    "[ConditionNode][AI] prompt='%s' message='%s' ai_text='%s' -> False",
                    ai_prompt, str(message_content)[:200], ai_text
                )
                return False
            # Heuristic: if contains the word 'true' and not 'false'
            if ('true' in ai_text or 'yes' in ai_text or 'بله' in ai_text) and not (
                'false' in ai_text or 'no' in ai_text or 'خیر' in ai_text
            ):
                logger.info(
                    "[ConditionNode][AI] prompt='%s' message='%s' ai_text='%s' -> True (heuristic)",
                    ai_prompt, str(message_content)[:200], ai_text
                )
                return True
            logger.info(
                "[ConditionNode][AI] prompt='%s' message='%s' ai_text='%s' -> False (fallback)",
                ai_prompt, str(message_content)[:200], ai_text
            )
            return False
        except Exception as e:
            logger.error(f"Error in AI condition evaluation via GeminiChatService: {e}")
            return False
    
    except Exception as e:
        logger.error(f"Error evaluating AI condition: {e}")
        return False


def evaluate_single_condition(condition: Dict[str, Any], context: Dict[str, Any]) -> bool:
    """
    Evaluate a single condition against context data.
    
    Args:
        condition: Single condition dictionary with field, operator, value
        context: Context data to evaluate against
    
    Returns:
        True if condition matches, False otherwise
    
    Expected condition format:
    {
        "type": "message|ai|user|tag|time",
        "field": "user.email",
        "operator": "equals",
        "value": "test@example.com",
        "ai_prompt": "Does this message express interest in products?" (for AI conditions)
    }
    """
    try:
        condition_type = condition.get('type', 'message')
        
        # Handle AI conditions
        if condition_type == 'ai':
            return evaluate_ai_condition(condition, context)
        
        # Handle other condition types
        field = condition.get('field', '')
        op = condition.get('operator', 'equals')
        expected_value = condition.get('value')
        
        # For message conditions without explicit field, use message content
        if condition_type == 'message' and not field:
            # Try multiple possible paths for message content
            field = 'event.data.content'
            if not get_nested_value(context, field):
                field = 'message.content'
            if not get_nested_value(context, field):
                field = 'message_content'
        
        # Get actual value from context
        actual_value = get_nested_value(context, field)
        
        # Normalize values for comparison
        actual_value = normalize_value(actual_value)
        expected_value = normalize_value(expected_value)
        
        # Handle different operators
        if op == 'equals' or op == 'equal' or op == 'equals_to':
            return actual_value == expected_value
        
        elif op == 'not_equals' or op == 'not_equal':
            return actual_value != expected_value
        
        elif op == 'contains':
            if actual_value is None:
                return False
            # Handle list fields like tags
            if isinstance(actual_value, list):
                return str(expected_value) in [str(item) for item in actual_value]
            return str(expected_value) in str(actual_value)
        
        elif op == 'not_contains':
            if actual_value is None:
                return True
            # Handle list fields like tags
            if isinstance(actual_value, list):
                return str(expected_value) not in [str(item) for item in actual_value]
            return str(expected_value) not in str(actual_value)
        
        elif op == 'icontains':
            if actual_value is None:
                return False
            return str(expected_value).lower() in str(actual_value).lower()
        
        elif op == 'starts_with' or op == 'start_with':
            if actual_value is None:
                return False
            return str(actual_value).startswith(str(expected_value))
        
        elif op == 'istarts_with':
            if actual_value is None:
                return False
            return str(actual_value).lower().startswith(str(expected_value).lower())
        
        elif op == 'ends_with' or op == 'end_with':
            if actual_value is None:
                return False
            return str(actual_value).endswith(str(expected_value))
        
        elif op == 'iends_with':
            if actual_value is None:
                return False
            return str(actual_value).lower().endswith(str(expected_value).lower())
        
        elif op == 'in':
            if not isinstance(expected_value, (list, tuple)):
                return False
            return actual_value in expected_value
        
        elif op == 'not_in':
            if not isinstance(expected_value, (list, tuple)):
                return True
            return actual_value not in expected_value
        
        elif op == 'is_null':
            return actual_value is None
        
        elif op == 'is_not_null':
            return actual_value is not None
        
        elif op == 'is_empty':
            if actual_value is None:
                return True
            if isinstance(actual_value, (str, list, dict)):
                return len(actual_value) == 0
            return False
        
        elif op == 'is_not_empty':
            if actual_value is None:
                return False
            if isinstance(actual_value, (str, list, dict)):
                return len(actual_value) > 0
            return True
        
        elif op == 'matches_regex':
            if actual_value is None:
                return False
            try:
                pattern = str(expected_value)
                return bool(re.search(pattern, str(actual_value)))
            except re.error:
                logger.warning(f"Invalid regex pattern: {expected_value}")
                return False
        
        elif op in ('greater', 'greater_than', 'gt'):
            try:
                return float(actual_value) > float(expected_value)
            except (TypeError, ValueError):
                return False
        
        elif op in ('less', 'less_than', 'lt'):
            try:
                return float(actual_value) < float(expected_value)
            except (TypeError, ValueError):
                return False
        
        elif op in ('greater_equal', 'greater_than_equal', 'gte'):
            try:
                return float(actual_value) >= float(expected_value)
            except (TypeError, ValueError):
                return False
        
        elif op in ('less_equal', 'less_than_equal', 'lte'):
            try:
                return float(actual_value) <= float(expected_value)
            except (TypeError, ValueError):
                return False
        
        elif op == 'between':
            if not isinstance(expected_value, (list, tuple)) or len(expected_value) != 2:
                return False
            try:
                min_val, max_val = expected_value
                actual_float = float(actual_value)
                return float(min_val) <= actual_float <= float(max_val)
            except (TypeError, ValueError):
                return False
        
        elif op == 'not_between':
            if not isinstance(expected_value, (list, tuple)) or len(expected_value) != 2:
                return True
            try:
                min_val, max_val = expected_value
                actual_float = float(actual_value)
                return not (float(min_val) <= actual_float <= float(max_val))
            except (TypeError, ValueError):
                return True
        
        else:
            logger.warning(f"Unknown operator: {op}")
            return False
    
    except Exception as e:
        logger.error(f"Error evaluating condition {condition}: {e}")
        return False


def evaluate_condition_group(conditions: List[Dict[str, Any]], operator: str, context: Dict[str, Any]) -> bool:
    """
    Evaluate a group of conditions with AND/OR logic.
    
    Args:
        conditions: List of condition dictionaries
        operator: 'and' or 'or'
        context: Context data to evaluate against
    
    Returns:
        True if condition group matches, False otherwise
    """
    if not conditions:
        return True
    
    results = []
    for condition in conditions:
        if 'conditions' in condition:
            # Nested condition group
            sub_operator = condition.get('operator', 'and')
            sub_conditions = condition.get('conditions', [])
            result = evaluate_condition_group(sub_conditions, sub_operator, context)
            try:
                logger.info(
                    "[ConditionNode][Group] operator='%s' nested_count=%s -> %s",
                    sub_operator, len(sub_conditions), result
                )
            except Exception:
                pass
        else:
            # Single condition
            result = evaluate_single_condition(condition, context)
            try:
                # Extract quick preview fields for logging
                ctype = condition.get('type')
                field = condition.get('field')
                op = condition.get('operator')
                expected = condition.get('value')
                message_preview = get_nested_value(context, 'event.data.content', '')
                logger.info(
                    "[ConditionNode][Single] type='%s' field='%s' op='%s' expected='%s' message='%s' -> %s",
                    ctype, field, op, str(expected)[:120], str(message_preview)[:200], result
                )
            except Exception:
                pass
        
        results.append(result)
    
    # Apply operator
    if operator.lower() == 'or':
        final = any(results)
    else:  # default to 'and'
        final = all(results)
    try:
        logger.info(
            "[ConditionNode][GroupSummary] operator='%s' results=%s -> %s",
            operator, results, final
        )
    except Exception:
        pass
    return final


def execute_custom_code(code: str, context: Dict[str, Any]) -> bool:
    """
    Execute custom Python code in a restricted environment.
    
    Args:
        code: Python code to execute
        context: Context data available to the code
    
    Returns:
        Boolean result of the code execution
    """
    if not code or not code.strip():
        return True
    
    try:
        # Create a restricted environment
        safe_globals = {
            '__builtins__': {
                'len': len,
                'str': str,
                'int': int,
                'float': float,
                'bool': bool,
                'list': list,
                'dict': dict,
                'tuple': tuple,
                'set': set,
                'abs': abs,
                'min': min,
                'max': max,
                'sum': sum,
                'round': round,
                'isinstance': isinstance,
                'type': type,
                'hasattr': hasattr,
                'getattr': getattr,
                're': re,
            },
            'context': context,
            'get_nested_value': get_nested_value,
        }
        
        # Create local namespace
        safe_locals = {}
        
        # Execute the code
        exec(code, safe_globals, safe_locals)
        
        # Return the result
        result = safe_locals.get('result', True)
        return bool(result)
    
    except Exception as e:
        logger.error(f"Error executing custom code: {e}")
        logger.debug(f"Custom code was: {code}")
        return False


def evaluate_conditions(condition_config: Dict[str, Any], context: Dict[str, Any]) -> bool:
    """
    Main function to evaluate conditions against context data.
    
    Args:
        condition_config: Condition configuration from Condition model
        context: Context data to evaluate against
    
    Returns:
        True if all conditions match, False otherwise
    
    Expected condition_config format:
    {
        "operator": "and",
        "conditions": [
            {
                "field": "user.email",
                "operator": "contains",
                "value": "@example.com"
            },
            {
                "operator": "or",
                "conditions": [
                    {"field": "user.tags", "operator": "contains", "value": "premium"},
                    {"field": "user.status", "operator": "equals", "value": "active"}
                ]
            }
        ],
        "use_custom_code": false,
        "custom_code": ""
    }
    """
    try:
        # Check if using custom code
        if condition_config.get('use_custom_code', False):
            custom_code = condition_config.get('custom_code', '')
            if custom_code:
                return execute_custom_code(custom_code, context)
        
        # Use standard condition evaluation
        operator = condition_config.get('operator', 'and')
        conditions = condition_config.get('conditions', [])
        
        return evaluate_condition_group(conditions, operator, context)
    
    except Exception as e:
        logger.error(f"Error evaluating conditions: {e}")
        return False


def substitute_template_placeholders(template: Union[str, Dict, List], context: Dict[str, Any]) -> Union[str, Dict, List]:
    """
    Recursively substitute {{path.to.value}} placeholders in templates.
    
    Args:
        template: Template string, dict, or list with placeholders
        context: Context data for substitution
    
    Returns:
        Template with placeholders substituted
    """
    if isinstance(template, str):
        # Replace placeholders in string
        def replace_placeholder(match):
            path = match.group(1)
            value = get_nested_value(context, path, '')
            return str(value) if value is not None else ''
        
        # Find all {{path.to.value}} patterns
        pattern = r'\{\{([^}]+)\}\}'
        return re.sub(pattern, replace_placeholder, template)
    
    elif isinstance(template, dict):
        # Recursively process dictionary
        return {
            key: substitute_template_placeholders(value, context)
            for key, value in template.items()
        }
    
    elif isinstance(template, list):
        # Recursively process list
        return [
            substitute_template_placeholders(item, context)
            for item in template
        ]
    
    else:
        # Return as-is for other types
        return template


def build_context_from_event_log(event_log) -> Dict[str, Any]:
    """
    Build a context dictionary from a TriggerEventLog instance.
    
    Args:
        event_log: TriggerEventLog instance
    
    Returns:
        Context dictionary with event data and enriched information
    """
    from workflow.settings_adapters import get_model_class, get_field_name
    from django.utils import timezone
    
    # Start with basic event context
    # Safely handle missing created_at (should rarely be None, but guard anyway)
    try:
        event_timestamp = event_log.created_at.isoformat() if getattr(event_log, 'created_at', None) else ''
    except Exception:
        event_timestamp = ''

    context = {
        'event': {
            'type': event_log.event_type,
            'event_type': event_log.event_type,  # Add both for compatibility
            'data': event_log.event_data.copy() if event_log.event_data else {},
            'timestamp': event_timestamp,
            'user_id': event_log.user_id,
            'conversation_id': event_log.conversation_id,
        }
    }
    
    # Add direct access to event data for easier condition writing
    if event_log.event_data:
        # Add message content directly for easier access
        if event_log.event_type == 'MESSAGE_RECEIVED' and 'content' in event_log.event_data:
            context['message'] = {
                'content': event_log.event_data['content'],
                'message_id': event_log.event_data.get('message_id', ''),
                'timestamp': event_log.event_data.get('timestamp', ''),
                'source': event_log.event_data.get('source', ''),
            }
    
    try:
        # Enrich with user data if available
        if event_log.user_id:
            try:
                UserModel = get_model_class('USER')  # This is Customer model
                user = UserModel.objects.get(id=event_log.user_id)
                
                # Build comprehensive user context
                user_context = {
                    'id': str(user.id),
                    'email': getattr(user, 'email', ''),
                    'first_name': getattr(user, 'first_name', ''),
                    'last_name': getattr(user, 'last_name', ''),
                    'username': getattr(user, 'username', ''),
                    'phone_number': getattr(user, 'phone_number', ''),
                    'description': getattr(user, 'description', ''),
                    'source': getattr(user, 'source', ''),
                    'source_id': getattr(user, 'source_id', ''),
                    'created_at': user.created_at.isoformat() if hasattr(user, 'created_at') and user.created_at else '',
                    'updated_at': user.updated_at.isoformat() if hasattr(user, 'updated_at') and user.updated_at else '',
                }
                
                # Add tags if available - try multiple tag field names
                if hasattr(user, 'tag'):
                    user_context['tags'] = list(user.tag.values_list('name', flat=True))
                elif hasattr(user, 'tags'):
                    if hasattr(user.tags, 'values_list'):
                        user_context['tags'] = list(user.tags.values_list('name', flat=True))
                    else:
                        user_context['tags'] = user.tags if isinstance(user.tags, list) else []
                else:
                    user_context['tags'] = []
                
                # Add computed fields
                user_context['full_name'] = f"{user_context['first_name']} {user_context['last_name']}".strip()
                user_context['display_name'] = user_context['full_name'] or user_context['username'] or f"User {user_context['id']}"
                
                context['user'] = user_context
                # Also add as customer for backwards compatibility
                context['customer'] = user_context
                
            except Exception as e:
                logger.warning(f"Could not load user {event_log.user_id} for context: {e}")
                # Add minimal user context to prevent condition failures
                context['user'] = {
                    'id': event_log.user_id,
                    'email': '',
                    'first_name': '',
                    'last_name': '',
                    'username': '',
                    'phone_number': '',
                    'description': '',
                    'source': '',
                    'tags': [],
                    'full_name': '',
                    'display_name': f"User {event_log.user_id}"
                }
                context['customer'] = context['user']
        
        # Enrich with conversation data if available
        if event_log.conversation_id:
            try:
                ConversationModel = get_model_class('CONVERSATION')
                conversation = ConversationModel.objects.get(id=event_log.conversation_id)
                
                context['conversation'] = {
                    'id': str(conversation.id),
                    'status': getattr(conversation, 'status', ''),
                    'source': getattr(conversation, 'source', ''),
                    'title': getattr(conversation, 'title', ''),
                    'is_active': getattr(conversation, 'is_active', True),
                    'created_at': conversation.created_at.isoformat() if hasattr(conversation, 'created_at') and conversation.created_at else '',
                    'updated_at': conversation.updated_at.isoformat() if hasattr(conversation, 'updated_at') and conversation.updated_at else '',
                }
                
            except Exception as e:
                logger.warning(f"Could not load conversation {event_log.conversation_id} for context: {e}")
                # Add minimal conversation context
                context['conversation'] = {
                    'id': event_log.conversation_id,
                    'status': '',
                    'source': '',
                    'title': '',
                    'is_active': True,
                    'created_at': '',
                    'updated_at': ''
                }
        
        # Add timestamp helpers
        context['now'] = timezone.now().isoformat()
        context['today'] = timezone.now().date().isoformat()
        
        # Add event-specific context
        if event_log.event_type == 'MESSAGE_RECEIVED':
            # Extract message content for easy condition checking
            message_content = event_log.event_data.get('content', '') if event_log.event_data else ''
            context['message_content'] = message_content
            context['message_content_lower'] = message_content.lower()
            context['message_words'] = message_content.split() if message_content else []
            context['message_word_count'] = len(context['message_words'])
        
        logger.debug(f"Built context for event {event_log.event_type}: {list(context.keys())}")
    
    except Exception as e:
        logger.error(f"Error building context from event log {event_log.id}: {e}")
        # Ensure we always have a basic context even if enrichment fails
        if 'user' not in context and event_log.user_id:
            context['user'] = {'id': event_log.user_id}
            context['customer'] = context['user']
        if 'conversation' not in context and event_log.conversation_id:
            context['conversation'] = {'id': event_log.conversation_id}
    
    return context
