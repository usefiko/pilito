"""
Trigger Service

Handles trigger processing, event filtering, and workflow discovery.
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

from django.utils import timezone
from django.db import transaction

from workflow.models import (
    Trigger, 
    TriggerWorkflowAssociation, 
    TriggerEventLog,
    EventType,
    Workflow,
    WorkflowExecution
)
from workflow.utils.condition_evaluator import (
    evaluate_conditions,
    build_context_from_event_log
)

logger = logging.getLogger(__name__)


class TriggerService:
    """
    Service for handling trigger processing and workflow discovery
    """
    
    @staticmethod
    def process_event_get_workflows(event_log: TriggerEventLog) -> List[Dict[str, Any]]:
        """
        Process an event and get all workflows that should be triggered.
        Only returns workflows that belong to the conversation owner.
        
        Args:
            event_log: TriggerEventLog instance
        
        Returns:
            List of workflow info dictionaries:
            [
                {
                    'workflow_id': str,
                    'workflow_name': str,
                    'trigger_id': str,
                    'association_id': str,
                    'context': dict,
                    'priority': int
                }
            ]
        """
        try:
            workflows = []
            
            # Build context from event log
            context = build_context_from_event_log(event_log)
            conversation_id_in_context = context.get('event', {}).get('conversation_id')
            
            # Get the conversation owner (User) from the event
            conversation_owner_id = TriggerService._get_conversation_owner_id(event_log)
            if not conversation_owner_id:
                logger.warning(f"No conversation owner found for event {event_log.id}, skipping workflow processing")
                return workflows
            
            logger.info(f"🔒 Processing workflows for conversation owner: {conversation_owner_id}")
            
            # Before matching, ensure the owner has an active subscription with tokens
            try:
                from billing.models import Subscription
                owner_subscription = Subscription.objects.select_related('full_plan', 'token_plan').get(user_id=conversation_owner_id)
                if not owner_subscription.is_subscription_active():
                    logger.info(f"Owner {conversation_owner_id} has no active subscription; skipping all workflows")
                    return []
            except Subscription.DoesNotExist:
                logger.info(f"Owner {conversation_owner_id} has no subscription; skipping all workflows")
                return []
            except Exception as e:
                logger.error(f"Error checking subscription for owner {conversation_owner_id}: {e}")
                return []

            # 1. Find old-style triggers that match this event type AND have workflows owned by conversation owner
            matching_triggers = Trigger.objects.filter(
                trigger_type=event_log.event_type,
                is_active=True,
                workflow_associations__workflow__created_by_id=conversation_owner_id,  # Only triggers with workflows owned by conversation owner
                workflow_associations__is_active=True,
                workflow_associations__workflow__status='ACTIVE'
            ).distinct().prefetch_related('workflow_associations__workflow')
            
            for trigger in matching_triggers:
                try:
                    # Check if trigger filters match
                    if not TriggerService._evaluate_trigger_filters(trigger, context):
                        continue
                    
                    # Get active workflow associations for this trigger
                    # FILTER BY CONVERSATION OWNER
                    associations = trigger.workflow_associations.filter(
                        is_active=True,
                        workflow__status='ACTIVE',
                        workflow__created_by_id=conversation_owner_id  # Only workflows owned by conversation owner
                    ).select_related('workflow').order_by('priority')
                    
                    for association in associations:
                        # Check workflow date constraints
                        if not association.workflow.is_active():
                            continue
                        
                        # Check association-specific conditions
                        if not TriggerService._evaluate_association_conditions(association, context):
                            continue
                        
                        # Optional run-once guard (disabled by default)
                        try:
                            run_once_enabled = False  # set True if you want single-fire per conversation
                            if (
                                run_once_enabled and
                                event_log.event_type == 'MESSAGE_RECEIVED' and
                                conversation_id_in_context
                            ):
                                if WorkflowExecution.objects.filter(
                                    workflow=association.workflow,
                                    conversation=conversation_id_in_context
                                ).exists():
                                    logger.info(
                                        f"⏭️  Skipping workflow '{association.workflow.name}' for conversation "
                                        f"{conversation_id_in_context} (already executed once for this conversation)"
                                    )
                                    continue
                        except Exception as guard_err:
                            logger.warning(f"Run-once guard check failed: {guard_err}")
                        
                        workflows.append({
                            'workflow_id': str(association.workflow.id),
                            'workflow_name': association.workflow.name,
                            'trigger_id': str(trigger.id),
                            'association_id': str(association.id),
                            'context': context,
                            'priority': association.priority,
                            'workflow_owner_id': conversation_owner_id
                        })
                        
                        logger.info(f"✅ Matched workflow '{association.workflow.name}' for user {conversation_owner_id}")
                        
                except Exception as e:
                    logger.error(f"Error processing trigger {trigger.id}: {e}")
                    continue
            
            # 2. Find new-style node-based workflows with matching when nodes
            # Pass conversation owner ID to filter node-based workflows as well
            node_workflows = TriggerService._find_node_based_workflows(event_log, context, conversation_owner_id)
            workflows.extend(node_workflows)
            
            # Sort by priority (lower numbers first)
            workflows.sort(key=lambda x: x['priority'])
            
            logger.info(f"📊 Event {event_log.event_type} matched {len(workflows)} workflows (old: {len(workflows) - len(node_workflows)}, node-based: {len(node_workflows)})")
            
            # Log details for debugging
            if workflows:
                logger.info(f"🎯 Matched workflows:")
                for workflow in workflows:
                    logger.info(f"  - '{workflow['workflow_name']}' (Priority: {workflow['priority']})")
            else:
                logger.warning(f"⚠️  No workflows matched for event {event_log.event_type}")
                logger.info(f"🔍 Event context keys: {list(context.keys())}")
                if 'event' in context:
                    logger.info(f"🔍 Event data keys: {list(context['event'].keys())}")
                if 'user' in context:
                    logger.info(f"🔍 User data keys: {list(context['user'].keys())}")
            
            return workflows
            
        except Exception as e:
            logger.error(f"Error processing event {event_log.id}: {e}")
            return []
    
    @staticmethod
    def _get_conversation_owner_id(event_log: TriggerEventLog) -> Optional[int]:
        """
        Get the conversation owner (User) ID from the event log.
        
        Args:
            event_log: TriggerEventLog instance
        
        Returns:
            User ID who owns the conversation, or None if not found
        """
        try:
            # If conversation_id is available, get the owner from the conversation
            if event_log.conversation_id:
                from message.models import Conversation
                try:
                    conversation = Conversation.objects.select_related('user').get(id=event_log.conversation_id)
                    return conversation.user.id
                except Conversation.DoesNotExist:
                    logger.warning(f"Conversation {event_log.conversation_id} not found")
                    return None
            
            # For events without conversation_id (like USER_CREATED), resolve owner from Customer.user
            if event_log.event_type in ['USER_CREATED', 'INSTAGRAM_COMMENT']:
                try:
                    # ✅ First: try event_log.user (direct relationship)
                    if event_log.user:
                        return event_log.user.id
                    
                    # ✅ For INSTAGRAM_COMMENT: fallback to channel_id in event_data
                    if event_log.event_type == 'INSTAGRAM_COMMENT':
                        channel_id = event_log.event_data.get('channel_id')
                        if channel_id:
                            from settings.models import InstagramChannel
                            try:
                                channel = InstagramChannel.objects.select_related('user').get(id=channel_id)
                                return channel.user.id
                            except InstagramChannel.DoesNotExist:
                                logger.warning(f"Instagram channel {channel_id} not found")
                    
                    # For USER_CREATED: try from Customer
                    if event_log.event_type == 'USER_CREATED' and event_log.user_id:
                        from workflow.settings_adapters import get_model_class
                        CustomerModel = get_model_class('USER')  # In this project this maps to message.Customer
                        customer = CustomerModel.objects.select_related('user').get(id=event_log.user_id)
                        owner = getattr(customer, 'user', None)
                        if owner and getattr(owner, 'id', None):
                            return owner.id
                except Exception as ue:
                    logger.warning(f"Could not resolve owner for {event_log.event_type} {event_log.user_id}: {ue}")
                # If cannot resolve, skip to preserve isolation
                logger.info(f"{event_log.event_type} event: owner not resolved; skipping for isolation")
                return None
            
            # For other events, if no conversation_id, we can't determine ownership
            logger.warning(f"Cannot determine conversation owner for event {event_log.event_type} without conversation_id")
            return None
            
        except Exception as e:
            logger.error(f"Error getting conversation owner for event {event_log.id}: {e}")
            return None
    
    @staticmethod
    def _evaluate_trigger_filters(trigger: Trigger, context: Dict[str, Any]) -> bool:
        """
        Evaluate trigger filters against context data.
        
        Args:
            trigger: Trigger instance
            context: Context data
        
        Returns:
            True if filters match, False otherwise
        """
        try:
            if not trigger.filters:
                return True
            
            return evaluate_conditions(trigger.filters, context)
            
        except Exception as e:
            logger.error(f"Error evaluating trigger filters for {trigger.id}: {e}")
            return False
    
    @staticmethod
    def _evaluate_association_conditions(association: TriggerWorkflowAssociation, context: Dict[str, Any]) -> bool:
        """
        Evaluate association-specific conditions.
        
        Args:
            association: TriggerWorkflowAssociation instance
            context: Context data
        
        Returns:
            True if conditions match, False otherwise
        """
        try:
            if not association.specific_conditions:
                return True
            
            return evaluate_conditions(association.specific_conditions, context)
            
        except Exception as e:
            logger.error(f"Error evaluating association conditions for {association.id}: {e}")
            return False
    
    @staticmethod
    def _find_node_based_workflows(event_log: TriggerEventLog, context: Dict[str, Any], conversation_owner_id: int) -> List[Dict[str, Any]]:
        """
        Find node-based workflows that should be triggered by this event.
        Only returns workflows that belong to the conversation owner.
        
        Args:
            event_log: TriggerEventLog instance
            context: Context data
            conversation_owner_id: ID of the user who owns the conversation
        
        Returns:
            List of workflow info dictionaries for node-based workflows
        """
        try:
            from workflow.models import WhenNode
            
            workflows = []
            
            # Map event types to when types
            event_to_when_mapping = {
                'MESSAGE_RECEIVED': 'receive_message',
                'USER_CREATED': 'new_customer',
                'TAG_ADDED': 'add_tag',
                'SCHEDULED': 'scheduled',
                'INSTAGRAM_COMMENT': 'instagram_comment',
            }
            
            when_type = event_to_when_mapping.get(event_log.event_type)
            if not when_type:
                logger.info(f"🚫 No when type mapping for event type: {event_log.event_type}")
                logger.info(f"🗺️  Available mappings: {list(event_to_when_mapping.keys())}")
                return workflows
            
            logger.info(f"🔄 Looking for node-based workflows with when_type: '{when_type}'")
            
            # For MESSAGE_RECEIVED, also check add_tag nodes (they can act as tag filters)
            when_types_to_check = [when_type]
            if event_log.event_type == 'MESSAGE_RECEIVED':
                when_types_to_check.append('add_tag')
                logger.info(f"🏷️  Also checking 'add_tag' when nodes for MESSAGE_RECEIVED (tag filtering)")
            
            # Find when nodes that match this event type AND belong to the conversation owner
            matching_when_nodes = WhenNode.objects.filter(
                when_type__in=when_types_to_check,
                is_active=True,
                workflow__status='ACTIVE',
                workflow__created_by_id=conversation_owner_id  # Only workflows owned by conversation owner
            ).select_related('workflow').prefetch_related('workflow__nodes')
            
            logger.info(f"🔍 Found {matching_when_nodes.count()} when nodes with types {when_types_to_check}")
            if matching_when_nodes.count() == 0:
                # Extra diagnostics to help identify why nothing matched
                try:
                    owner_when_nodes_any = WhenNode.objects.filter(
                        workflow__created_by_id=conversation_owner_id
                    ).count()
                    owner_active_when_nodes_any = WhenNode.objects.filter(
                        workflow__created_by_id=conversation_owner_id,
                        is_active=True
                    ).count()
                    owner_active_when_nodes_type = WhenNode.objects.filter(
                        workflow__created_by_id=conversation_owner_id,
                        is_active=True,
                        when_type__in=when_types_to_check
                    ).count()
                    all_active_type = WhenNode.objects.filter(
                        is_active=True,
                        when_type__in=when_types_to_check,
                        workflow__status='ACTIVE'
                    ).count()
                    logger.info(
                        f"🧪 Diagnostics: owner_when_nodes_any={owner_when_nodes_any}, "
                        f"owner_active_when_nodes_any={owner_active_when_nodes_any}, "
                        f"owner_active_when_nodes_type={owner_active_when_nodes_type}, "
                        f"all_active_type={all_active_type}"
                    )
                except Exception as diag_err:
                    logger.warning(f"Diagnostics for when nodes failed: {diag_err}")
            
            for when_node in matching_when_nodes:
                try:
                    logger.info(f"🔍 Evaluating when node: '{when_node.title}' in workflow '{when_node.workflow.name}'")
                    
                    # Check if workflow is active and within date constraints
                    if not when_node.workflow.is_active():
                        logger.info(f"⏸️  Workflow '{when_node.workflow.name}' is not active")
                        continue
                    
                    # Check when node specific conditions
                    if not TriggerService._evaluate_when_node_conditions(when_node, context):
                        logger.info(f"❌ When node conditions failed for '{when_node.title}'")
                        continue
                    
                        # Check if workflow is currently running or has just completed
                        try:
                            conversation_id_in_context = context.get('event', {}).get('conversation_id')
                            if conversation_id_in_context and event_log.event_type == 'MESSAGE_RECEIVED':
                                # Don't re-trigger if workflow is currently active for this conversation
                                active_executions = WorkflowExecution.objects.filter(
                                    workflow=when_node.workflow,
                                    conversation=conversation_id_in_context,
                                    status__in=['RUNNING', 'WAITING']
                                )
                                logger.info(f"🔍 [Guard] Checking active executions for workflow {when_node.workflow.name}, conversation {conversation_id_in_context}")
                                logger.info(f"🔍 [Guard] Found {active_executions.count()} active executions: {[f'#{e.id}({e.status})' for e in active_executions]}")
                                
                                if active_executions.exists():
                                    logger.info(f"⏭️ Skipping workflow '{when_node.workflow.name}' - already active executions found")
                                    continue
                                else:
                                    logger.info(f"✅ [Guard] No active executions - workflow can proceed")
                        except Exception as guard_err:
                            logger.warning(f"Active workflow guard check failed: {guard_err}")
                    
                    # Add workflow to list with default priority 100 for node-based workflows
                    # Include start_node_id in context so executor can begin from this When
                    ctx_with_start = context.copy()
                    try:
                        # Shallow copy is enough; ensure key is string
                        ctx_with_start['start_node_id'] = str(when_node.id)
                    except Exception:
                        ctx_with_start = context
                    workflows.append({
                        'workflow_id': str(when_node.workflow.id),
                        'workflow_name': when_node.workflow.name,
                        'trigger_id': f'when_node_{when_node.id}',  # Use when node as trigger reference
                        'association_id': f'when_node_{when_node.id}',
                        'context': ctx_with_start,
                        'priority': 100,  # Default priority for node-based workflows
                        'is_node_based': True,
                        'when_node_id': str(when_node.id),
                        'workflow_owner_id': conversation_owner_id,
                        'when_type': getattr(when_node, 'when_type', None)
                    })
                    
                    logger.info(f"✅ Node-based workflow '{when_node.workflow.name}' matched for user {conversation_owner_id}")
                    logger.info(f"   When node: '{when_node.title}' (ID: {when_node.id})")
                    
                except Exception as e:
                    logger.error(f"Error evaluating when node {when_node.id}: {e}")
                    continue

            # Additional bridge: allow 'new_customer' When nodes to fire on the first MESSAGE_RECEIVED
            if event_log.event_type == 'MESSAGE_RECEIVED':
                try:
                    new_customer_when_nodes = WhenNode.objects.filter(
                        when_type='new_customer',
                        is_active=True,
                        workflow__status='ACTIVE',
                        workflow__created_by_id=conversation_owner_id
                    ).select_related('workflow')
                    logger.info(f"🔄 Checking 'new_customer' when nodes on MESSAGE_RECEIVED: {new_customer_when_nodes.count()} candidates")
                    for when_node in new_customer_when_nodes:
                        try:
                            if TriggerService._is_first_message_for_owner(event_log, conversation_owner_id):
                                ctx_with_start = context.copy()
                                try:
                                    ctx_with_start['start_node_id'] = str(when_node.id)
                                except Exception:
                                    ctx_with_start = context
                                workflows.append({
                                    'workflow_id': str(when_node.workflow.id),
                                    'workflow_name': when_node.workflow.name,
                                    'trigger_id': f'when_node_{when_node.id}',
                                    'association_id': f'when_node_{when_node.id}',
                                    'context': ctx_with_start,
                                    'priority': 100,
                                    'is_node_based': True,
                                    'when_node_id': str(when_node.id),
                                    'workflow_owner_id': conversation_owner_id,
                                    'when_type': getattr(when_node, 'when_type', 'new_customer'),
                                    'bridged': True
                                })
                                logger.info(f"✅ Bridged 'new_customer' when node matched on first message for user {conversation_owner_id}")
                        except Exception as be:
                            logger.warning(f"Bridge check failed for when_node {when_node.id}: {be}")
                except Exception as br:
                    logger.warning(f"Error bridging new_customer on message: {br}")
            
            return workflows
            
        except Exception as e:
            logger.error(f"Error finding node-based workflows: {e}")
            return []

    @staticmethod
    def _is_first_message_for_owner(event_log: TriggerEventLog, conversation_owner_id: int) -> bool:
        """
        Determine whether this MESSAGE_RECEIVED is the first customer message for this owner+customer pair.
        Used to bridge 'new_customer' When nodes to the first message scenario.
        """
        try:
            if event_log.event_type != 'MESSAGE_RECEIVED':
                return False
            from workflow.settings_adapters import get_model_class
            MessageModel = get_model_class('MESSAGE')
            ConversationModel = get_model_class('CONVERSATION')
            # Require conversation and user_id in event
            conv_id = event_log.conversation_id
            user_id = event_log.user_id
            if not conv_id or not user_id:
                return False
            conv = ConversationModel.objects.select_related('user').get(id=conv_id)
            if getattr(conv.user, 'id', None) != conversation_owner_id:
                return False
            # Count previous customer messages in this conversation
            qs = MessageModel.objects.filter(
                conversation_id=conv_id,
                type='customer'
            )
            # If there is exactly one (the current), treat as first
            return qs.count() <= 1
        except Exception as e:
            logger.warning(f"First-message check failed: {e}")
            return False
    
    @staticmethod
    def _evaluate_when_node_conditions(when_node, context: Dict[str, Any]) -> bool:
        """
        Evaluate when node specific conditions (keywords, tags, channels).
        
        Args:
            when_node: WhenNode instance
            context: Context data
        
        Returns:
            True if when node conditions match, False otherwise
        """
        try:
            event_data = context.get('event', {}).get('data', {})
            
            logger.info(f"🔍 Evaluating when node '{when_node.title}' conditions:")
            logger.info(f"   Type: {when_node.when_type}")
            logger.info(f"   Keywords: {when_node.keywords}")
            logger.info(f"   Channels: {when_node.channels}")
            logger.info(f"   Tags: {when_node.tags}")
            
            # Check conditions based on when type
            if when_node.when_type == 'receive_message':
                # Check keywords
                if when_node.keywords:
                    message_content = event_data.get('content', '').lower()
                    logger.info(f"   Message content: '{message_content}'")
                    keyword_match = any(keyword.lower() in message_content for keyword in when_node.keywords)
                    if not keyword_match:
                        logger.info(f"❌ Message content '{message_content}' doesn't contain any keywords: {when_node.keywords}")
                        return False
                    else:
                        logger.info(f"✅ Keyword match found in message")
                
                # Check channels
                if when_node.channels and 'all' not in when_node.channels:
                    source = context.get('user', {}).get('source', '')
                    logger.info(f"   User source: '{source}'")
                    if source not in when_node.channels:
                        logger.info(f"❌ User source '{source}' not in allowed channels: {when_node.channels}")
                        return False
                    else:
                        logger.info(f"✅ Channel match found")
            
            elif when_node.when_type == 'add_tag':
                # Two modes for add_tag:
                # 1. TAG_ADDED event: check if the added tag matches
                # 2. MESSAGE_RECEIVED event: filter by user tags (frontend "by tag" feature)
                
                event_type = context.get('event', {}).get('type') or context.get('event', {}).get('event_type', '')
                
                if event_type == 'TAG_ADDED':
                    # Original behavior: trigger when a specific tag is added
                    if when_node.tags:
                        added_tag = event_data.get('tag_name', '')
                        # Normalize for case-insensitive comparison
                        normalized_added_tag = str(added_tag).lower().strip() if added_tag else ''
                        normalized_when_tags = [str(tag).lower().strip() for tag in when_node.tags if tag]
                        
                        if normalized_added_tag not in normalized_when_tags:
                            logger.debug(f"Added tag '{added_tag}' not in required tags: {when_node.tags}")
                            return False
                
                elif event_type == 'MESSAGE_RECEIVED':
                    # New behavior: filter by user tags when message is received
                    logger.info(f"🏷️  add_tag node acting as tag filter for MESSAGE_RECEIVED")
                    if when_node.tags:
                        user_tags = context.get('user', {}).get('tags', [])
                        logger.info(f"   User tags: {user_tags}")
                        logger.info(f"   Required tags: {when_node.tags}")
                        
                        # Normalize tags for case-insensitive comparison
                        normalized_user_tags = [str(tag).lower().strip() for tag in user_tags if tag]
                        normalized_when_tags = [str(tag).lower().strip() for tag in when_node.tags if tag]
                        
                        # Check if user has ALL of the required tags (case-insensitive)
                        has_required_tag = all(tag in normalized_user_tags for tag in normalized_when_tags)
                        
                        if not has_required_tag:
                            logger.info(f"❌ User does not have all required tags: {when_node.tags}")
                            logger.debug(f"   Normalized: user_tags={normalized_user_tags}, when_tags={normalized_when_tags}")
                            return False
                        else:
                            logger.info(f"✅ User has ALL required tags: {when_node.tags}")
                    
                    # Also check keywords if configured (just like receive_message)
                    if when_node.keywords:
                        message_content = event_data.get('content', '').lower()
                        logger.info(f"   Message content: '{message_content}'")
                        if not any(keyword.lower() in message_content for keyword in when_node.keywords):
                            logger.info(f"❌ Message content '{message_content}' doesn't contain any keywords: {when_node.keywords}")
                            return False
                        else:
                            logger.info(f"✅ Keyword match found")
                    
                    # Also check channels if configured
                    if when_node.channels and 'all' not in when_node.channels:
                        source = context.get('user', {}).get('source', '')
                        logger.info(f"   User source: '{source}'")
                        if source not in when_node.channels:
                            logger.info(f"❌ User source '{source}' not in allowed channels: {when_node.channels}")
                            return False
                        else:
                            logger.info(f"✅ Channel match found")
            
            elif when_node.when_type == 'instagram_comment':
                # Instagram Comment specific filters
                logger.info(f"📸 Evaluating Instagram comment filters")
                
                # 1. Check specific post URL filter
                if when_node.instagram_post_url:
                    media_id = event_data.get('media_id', '')
                    post_permalink = event_data.get('post_url', '')
                    
                    logger.info(f"   Filter: Specific post URL = {when_node.instagram_post_url}")
                    logger.info(f"   Event: media_id = {media_id}, post_url = {post_permalink}")
                    
                    # Extract media ID from configured URL (e.g., https://instagram.com/p/ABC123/)
                    import re
                    url_match = re.search(r'/p/([^/]+)', when_node.instagram_post_url)
                    if url_match:
                        expected_shortcode = url_match.group(1)
                        # Check if event's post URL contains this shortcode
                        if expected_shortcode not in post_permalink and expected_shortcode not in media_id:
                            logger.info(f"❌ Post URL mismatch: expected shortcode '{expected_shortcode}' not in event")
                            return False
                        else:
                            logger.info(f"✅ Post URL match: shortcode '{expected_shortcode}' found")
                    else:
                        logger.warning(f"⚠️  Could not extract shortcode from URL: {when_node.instagram_post_url}")
                
                # 2. Check media type filter
                if when_node.instagram_media_type and when_node.instagram_media_type != 'all':
                    media_type = event_data.get('media_type', 'post').lower()
                    expected_type = when_node.instagram_media_type.lower()
                    
                    logger.info(f"   Filter: Media type = {expected_type}")
                    logger.info(f"   Event: media_type = {media_type}")
                    
                    # Normalize media types (Instagram API might return different values)
                    type_mapping = {
                        'image': 'post',
                        'photo': 'post',
                        'carousel_album': 'post',
                        'video': 'video',
                        'reel': 'reel',
                    }
                    normalized_media_type = type_mapping.get(media_type, media_type)
                    
                    if normalized_media_type != expected_type:
                        logger.info(f"❌ Media type mismatch: expected '{expected_type}', got '{normalized_media_type}'")
                        return False
                    else:
                        logger.info(f"✅ Media type match: {normalized_media_type}")
                
                # 3. Check comment keywords filter
                if when_node.comment_keywords:
                    comment_text = event_data.get('comment_text', '').lower()
                    
                    logger.info(f"   Filter: Keywords = {when_node.comment_keywords}")
                    logger.info(f"   Event: comment = '{comment_text}'")
                    
                    keyword_match = any(
                        keyword.lower() in comment_text 
                        for keyword in when_node.comment_keywords
                    )
                    
                    if not keyword_match:
                        logger.info(f"❌ Comment doesn't contain any required keywords: {when_node.comment_keywords}")
                        return False
                    else:
                        matched_keywords = [
                            kw for kw in when_node.comment_keywords 
                            if kw.lower() in comment_text
                        ]
                        logger.info(f"✅ Keyword match found: {matched_keywords}")
            
            # For new_customer and scheduled, no additional conditions to check
            logger.info(f"✅ All when node conditions passed for '{when_node.title}'")
            return True
            
        except Exception as e:
            logger.error(f"Error evaluating when node conditions: {e}")
            return False
    
    @staticmethod
    def register_common_event_types():
        """
        Register common event types in the database.
        """
        common_events = [
            {
                'name': 'User Registered',
                'code': 'USER_CREATED',
                'category': 'user',
                'description': 'Triggered when a new user/customer registers',
                'available_fields': {
                    'user_id': 'string',
                    'email': 'string',
                    'first_name': 'string',
                    'last_name': 'string',
                    'source': 'string',
                    'timestamp': 'datetime'
                }
            },
            {
                'name': 'User Login',
                'code': 'USER_LOGIN',
                'category': 'user',
                'description': 'Triggered when a user logs in',
                'available_fields': {
                    'user_id': 'string',
                    'login_method': 'string',
                    'ip_address': 'string',
                    'timestamp': 'datetime'
                }
            },
            {
                'name': 'Message Received',
                'code': 'MESSAGE_RECEIVED',
                'category': 'message',
                'description': 'Triggered when a customer message is received',
                'available_fields': {
                    'message_id': 'string',
                    'conversation_id': 'string',
                    'user_id': 'string',
                    'content': 'string',
                    'source': 'string',
                    'timestamp': 'datetime'
                }
            },
            {
                'name': 'Message Sent',
                'code': 'MESSAGE_SENT',
                'category': 'message',
                'description': 'Triggered when a message is sent to customer',
                'available_fields': {
                    'message_id': 'string',
                    'conversation_id': 'string',
                    'user_id': 'string',
                    'content': 'string',
                    'sender_type': 'string',
                    'timestamp': 'datetime'
                }
            },
            {
                'name': 'Conversation Started',
                'code': 'CONVERSATION_CREATED',
                'category': 'conversation',
                'description': 'Triggered when a new conversation is created',
                'available_fields': {
                    'conversation_id': 'string',
                    'user_id': 'string',
                    'source': 'string',
                    'timestamp': 'datetime'
                }
            },
            {
                'name': 'Conversation Closed',
                'code': 'CONVERSATION_CLOSED',
                'category': 'conversation',
                'description': 'Triggered when a conversation is closed',
                'available_fields': {
                    'conversation_id': 'string',
                    'user_id': 'string',
                    'closed_by': 'string',
                    'duration_minutes': 'number',
                    'timestamp': 'datetime'
                }
            },
            {
                'name': 'Tag Added',
                'code': 'TAG_ADDED',
                'category': 'user',
                'description': 'Triggered when a tag is added to a user',
                'available_fields': {
                    'user_id': 'string',
                    'tag_name': 'string',
                    'added_by': 'string',
                    'timestamp': 'datetime'
                }
            },
            {
                'name': 'Tag Removed',
                'code': 'TAG_REMOVED',
                'category': 'user',
                'description': 'Triggered when a tag is removed from a user',
                'available_fields': {
                    'user_id': 'string',
                    'tag_name': 'string',
                    'removed_by': 'string',
                    'timestamp': 'datetime'
                }
            },
            {
                'name': 'Scheduled Time',
                'code': 'SCHEDULED',
                'category': 'system',
                'description': 'Triggered at scheduled times',
                'available_fields': {
                    'trigger_id': 'string',
                    'schedule_type': 'string',
                    'timestamp': 'datetime'
                }
            }
        ]
        
        created_count = 0
        for event_data in common_events:
            event_type, created = EventType.objects.get_or_create(
                code=event_data['code'],
                defaults=event_data
            )
            if created:
                created_count += 1
                logger.info(f"Created event type: {event_type.name}")
        
        logger.info(f"Registered {created_count} new event types")
        return created_count
    
    @staticmethod
    def create_event_log(
        event_type: str,
        event_data: Dict[str, Any],
        user_id: Optional[str] = None,
        conversation_id: Optional[str] = None
    ) -> TriggerEventLog:
        """
        Create a new trigger event log.
        
        Args:
            event_type: Event type code
            event_data: Event data dictionary
            user_id: Optional user ID
            conversation_id: Optional conversation ID
        
        Returns:
            Created TriggerEventLog instance
        """
        try:
            event_log = TriggerEventLog.objects.create(
                event_type=event_type,
                event_data=event_data,
                user_id=user_id,
                conversation_id=conversation_id
            )
            
            logger.debug(f"Created event log {event_log.id} for {event_type}")
            return event_log
            
        except Exception as e:
            logger.error(f"Error creating event log for {event_type}: {e}")
            raise
    
    @staticmethod
    def get_trigger_statistics(days: int = 30) -> Dict[str, Any]:
        """
        Get trigger statistics for the last N days.
        
        Args:
            days: Number of days to analyze
        
        Returns:
            Statistics dictionary
        """
        try:
            from django.db.models import Count
            from datetime import timedelta
            
            cutoff_date = timezone.now() - timedelta(days=days)
            
            # Event type statistics
            event_stats = list(
                TriggerEventLog.objects.filter(created_at__gte=cutoff_date)
                .values('event_type')
                .annotate(count=Count('id'))
                .order_by('-count')
            )
            
            # Trigger performance
            trigger_stats = list(
                Trigger.objects.filter(is_active=True)
                .annotate(
                    associations_count=Count('workflow_associations'),
                    active_associations_count=Count('workflow_associations', filter=lambda q: q.filter(is_active=True))
                )
                .values('id', 'name', 'trigger_type', 'associations_count', 'active_associations_count')
            )
            
            total_events = TriggerEventLog.objects.filter(created_at__gte=cutoff_date).count()
            
            return {
                'period_days': days,
                'total_events': total_events,
                'event_type_stats': event_stats,
                'trigger_stats': trigger_stats,
                'generated_at': timezone.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error generating trigger statistics: {e}")
            return {
                'error': str(e),
                'generated_at': timezone.now().isoformat()
            }
