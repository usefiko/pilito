"""
Instagram Comment Action Service

Handles Instagram Comment → DM + Public Reply workflow action
"""

import logging
from typing import Dict, Any
from django.template import Template, Context

from message.services.instagram_service import InstagramService
from web_knowledge.models import Product
from AI_model.services.gemini_service import GeminiService
from message.utils.cta_utils import extract_cta_from_text

logger = logging.getLogger(__name__)


def render_template(template_str: str, context: Dict[str, Any]) -> str:
    """Simple Django template rendering with {{variable}} syntax"""
    try:
        t = Template(template_str)
        c = Context(context)
        return t.render(c).strip()
    except Exception as e:
        logger.warning(f"Template render failed: {e}")
        return template_str


def handle_instagram_comment_dm_reply(
    workflow_action,
    event_data: Dict[str, Any],
    user
) -> Dict[str, Any]:
    """
    Main handler for 'instagram_comment_dm_reply' action
    
    Returns result dict (for workflow execution service)
    
    Config structure:
    {
        "dm_mode": "STATIC" | "PRODUCT",
        "dm_text_template": "...",
        "product_id": "uuid",
        "public_reply_enabled": true,
        "public_reply_template": "..."
    }
    
    Event data structure:
    {
        "comment_id": "...",
        "comment_text": "...",
        "post_id": "...",
        "post_url": "..." | null,
        "ig_username": "...",
        "ig_user_id": "...",
        "channel_id": "..."
    }
    
    Returns:
        Dict with 'success', 'dm_sent', 'reply_sent', 'error'
    """
    config = workflow_action.config or {}
    dm_mode = config.get('dm_mode')
    dm_text_template = config.get('dm_text_template', '')
    product_id = config.get('product_id')
    public_reply_enabled = config.get('public_reply_enabled', False)
    public_reply_template = config.get('public_reply_template', '')
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # Validation
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    if dm_mode not in ['STATIC', 'PRODUCT']:
        error = f"Invalid dm_mode: {dm_mode}"
        logger.error(f"[InstagramCommentAction] {error}")
        return {'success': False, 'error': error}
    
    if dm_mode == 'STATIC' and not dm_text_template:
        error = "dm_text_template required for STATIC mode"
        logger.error(f"[InstagramCommentAction] {error}")
        return {'success': False, 'error': error}
    
    if dm_mode == 'PRODUCT' and not product_id:
        error = "product_id required for PRODUCT mode"
        logger.error(f"[InstagramCommentAction] {error}")
        return {'success': False, 'error': error}
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # Extract event data
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    comment_id = event_data.get('comment_id')
    comment_text = event_data.get('comment_text') or ''
    post_url = event_data.get('post_url')  # May be None
    ig_username = event_data.get('ig_username') or ''
    ig_user_id = event_data.get('ig_user_id')
    channel_id = event_data.get('channel_id')
    
    if not (comment_id and ig_user_id and channel_id):
        error = f"Missing required fields in event_data: {event_data}"
        logger.error(f"[InstagramCommentAction] {error}")
        return {'success': False, 'error': error}
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # Get Instagram service (with account_type enforcement)
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    instagram_service = InstagramService.get_service_for_channel_id(channel_id)
    if not instagram_service:
        error = f"Could not get Instagram service for channel {channel_id}"
        logger.error(f"[InstagramCommentAction] {error}")
        return {'success': False, 'error': error}
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # Base context for templates
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    base_ctx = {
        'username': ig_username,
        'comment_text': comment_text,
        'post_url': post_url or '',  # Empty string if null
    }
    
    result = {
        'success': True,
        'dm_sent': False,
        'reply_sent': False,
        'error': None
    }
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 1️⃣ Send DM
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    product = None
    dm_text = None
    
    if dm_mode == 'STATIC':
        # Static template
        dm_text = render_template(dm_text_template, base_ctx)
        clean_dm, buttons = extract_cta_from_text(dm_text)
        
        dm_result = instagram_service.send_dm_by_instagram_id(
            ig_user_id=ig_user_id,
            text=clean_dm,
            buttons=buttons
        )
        
        result['dm_sent'] = dm_result.get('success', False)
        if not result['dm_sent']:
            result['error'] = dm_result.get('error')
        
        logger.info(f"[InstagramCommentAction] STATIC DM to {ig_username}: {result['dm_sent']}")
    
    elif dm_mode == 'PRODUCT':
        # Load product
        try:
            product = Product.objects.get(id=product_id, user=user)
        except Product.DoesNotExist:
            error = f"Product {product_id} not found for user {user.id}"
            logger.error(f"[InstagramCommentAction] {error}")
            result['success'] = False
            result['error'] = error
            return result
        
        # Generate AI response
        ai_service = GeminiService.get_for_user(user)
        ai_response = ai_service.generate_product_dm_for_instagram_comment(
            comment_text=comment_text,
            product=product,
            extra_context={
                'username': ig_username,
                'post_url': post_url,
            }
        )
        
        if not ai_response.get('success'):
            logger.warning(f"[InstagramCommentAction] AI failed, using fallback")
        
        dm_text = ai_response['response']
        clean_dm, buttons = extract_cta_from_text(dm_text)
        
        dm_result = instagram_service.send_dm_by_instagram_id(
            ig_user_id=ig_user_id,
            text=clean_dm,
            buttons=buttons
        )
        
        result['dm_sent'] = dm_result.get('success', False)
        if not result['dm_sent']:
            result['error'] = dm_result.get('error')
        
        logger.info(f"[InstagramCommentAction] PRODUCT DM to {ig_username}: {result['dm_sent']}")
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 2️⃣ Public reply (optional)
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    if public_reply_enabled and public_reply_template:
        reply_ctx = dict(base_ctx)
        if product:
            reply_ctx['product_name'] = product.title
        
        reply_text = render_template(public_reply_template, reply_ctx)
        if reply_text:
            reply_result = instagram_service.reply_to_comment(
                comment_id=comment_id,
                text=reply_text
            )
            
            result['reply_sent'] = reply_result.get('success', False)
            
            logger.info(f"[InstagramCommentAction] Public reply: {result['reply_sent']}")
    
    logger.info(f"[InstagramCommentAction] Completed: {result}")
    return result

