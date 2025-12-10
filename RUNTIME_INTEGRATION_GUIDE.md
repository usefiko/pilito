# Runtime Integration Guide for Key-Values

## Overview
This guide shows how to integrate the `key_values` field with the workflow execution system to send CTA buttons in messages.

## Where to Integrate

The integration should happen in the workflow execution service where action nodes and waiting nodes are processed.

### Relevant Files
- `src/workflow/services/workflow_execution_service.py` - Main execution logic
- `src/workflow/services/action_executor.py` - Action execution logic
- `src/message/utils/cta_utils.py` - CTA extraction utilities (already exists)

## Implementation Approach

### Option 1: Append key_values to message_content

This is the simplest approach and leverages the existing CTA extraction system.

```python
# In action_executor.py or similar execution logic

def execute_send_message_action(action_node, context):
    """Execute send_message action with CTA support"""
    message_content = action_node.message_content
    
    # If key_values exist, append them to the message
    if action_node.key_values:
        for key_value in action_node.key_values:
            # key_value format: "CTA:Title|https://url.com"
            # Wrap in [[]] format for CTA extraction
            message_content += f" [[{key_value}]]"
    
    # Use existing CTA extraction
    from message.utils.cta_utils import extract_cta_from_text
    clean_message, buttons = extract_cta_from_text(message_content)
    
    # Send message based on channel
    channel = context.get('channel')
    if channel == 'instagram':
        from message.services.instagram_service import InstagramService
        instagram_service = InstagramService()
        result = instagram_service.send_message(
            recipient_id=context['recipient_id'],
            message_text=clean_message,
            buttons=buttons
        )
    elif channel == 'telegram':
        # Similar for Telegram
        pass
    
    return result
```

### Option 2: Direct Button Creation

If you want more control, you can directly create buttons from key_values:

```python
def extract_buttons_from_key_values(key_values):
    """Convert key_values to button format"""
    if not key_values:
        return None
    
    buttons = []
    for kv in key_values:
        # Expected format: "CTA:Title|https://url.com"
        if not kv or not isinstance(kv, str):
            continue
            
        # Parse the key_value string
        if kv.startswith('CTA:') and '|' in kv:
            parts = kv[4:].split('|', 1)  # Remove "CTA:" prefix
            if len(parts) == 2:
                title, url = parts
                buttons.append({
                    'type': 'web_url',
                    'title': title.strip(),
                    'url': url.strip()
                })
    
    return buttons if buttons else None


def execute_send_message_action(action_node, context):
    """Execute send_message action with direct button creation"""
    message_content = action_node.message_content
    
    # Extract buttons from CTA tags in message content
    from message.utils.cta_utils import extract_cta_from_text
    clean_message, cta_buttons = extract_cta_from_text(message_content)
    
    # Extract buttons from key_values field
    kv_buttons = extract_buttons_from_key_values(action_node.key_values)
    
    # Combine buttons (CTA from message + key_values)
    all_buttons = []
    if cta_buttons:
        all_buttons.extend(cta_buttons)
    if kv_buttons:
        all_buttons.extend(kv_buttons)
    
    # Limit to 3 buttons (Instagram limitation)
    final_buttons = all_buttons[:3] if all_buttons else None
    
    # Send message
    channel = context.get('channel')
    if channel == 'instagram':
        from message.services.instagram_service import InstagramService
        instagram_service = InstagramService()
        result = instagram_service.send_message(
            recipient_id=context['recipient_id'],
            message_text=clean_message,
            buttons=final_buttons
        )
    
    return result
```

## Waiting Node Integration

For waiting nodes, the integration is similar:

```python
def execute_waiting_node(waiting_node, context):
    """Execute waiting node with CTA buttons"""
    customer_message = waiting_node.customer_message
    
    # Append key_values to customer message
    if waiting_node.key_values:
        for key_value in waiting_node.key_values:
            customer_message += f" [[{key_value}]]"
    
    # Extract CTAs
    from message.utils.cta_utils import extract_cta_from_text
    clean_message, buttons = extract_cta_from_text(customer_message)
    
    # Send the prompt message to customer
    channel = context.get('channel')
    if channel == 'instagram':
        from message.services.instagram_service import InstagramService
        instagram_service = InstagramService()
        instagram_service.send_message(
            recipient_id=context['recipient_id'],
            message_text=clean_message,
            buttons=buttons
        )
    
    # Store waiting state and wait for customer response
    # ... (existing waiting logic)
```

## Instagram Comment DM Reply Integration

For Instagram comment DM reply actions:

```python
# In src/workflow/services/instagram_comment_action.py

def handle_instagram_comment_dm_reply(workflow_action, event_data, user):
    """Handle Instagram Comment → DM + Reply action"""
    
    # Get action node
    action_node = workflow_action.actionnode
    
    # ... existing code for getting Instagram details ...
    
    if action_node.instagram_dm_mode == 'STATIC':
        # Get DM template
        dm_text = action_node.instagram_dm_text_template
        
        # Render template with context
        from workflow.services.template_renderer import render_template
        dm_text = render_template(dm_text, context)
        
        # Append key_values if they exist
        if action_node.key_values:
            for key_value in action_node.key_values:
                dm_text += f" [[{key_value}]]"
        
        # Extract CTA buttons
        from message.utils.cta_utils import extract_cta_from_text
        clean_dm, buttons = extract_cta_from_text(dm_text)
        
        # Send DM with buttons
        dm_result = instagram_service.send_dm_by_instagram_id(
            ig_user_id=ig_user_id,
            text=clean_dm,
            buttons=buttons
        )
    
    # ... rest of the function ...
```

## Example: Complete Action Executor Enhancement

Here's a complete example of how to enhance the action executor:

```python
# src/workflow/services/action_executor.py (enhancement)

class ActionExecutor:
    """Enhanced action executor with key_values support"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def execute_action(self, action_node, context):
        """Execute an action based on its type"""
        action_type = action_node.action_type
        
        if action_type == 'send_message':
            return self._execute_send_message(action_node, context)
        elif action_type == 'instagram_comment_dm_reply':
            return self._execute_instagram_comment_reply(action_node, context)
        # ... other action types
    
    def _execute_send_message(self, action_node, context):
        """Execute send message action with CTA support"""
        message_content = action_node.message_content
        
        # Render template variables if any
        message_content = self._render_template(message_content, context)
        
        # Append key_values as CTA tags
        if action_node.key_values:
            self.logger.info(f"Processing {len(action_node.key_values)} key_values for CTA buttons")
            for key_value in action_node.key_values:
                message_content += f" [[{key_value}]]"
        
        # Extract CTA buttons using existing utility
        from message.utils.cta_utils import extract_cta_from_text
        clean_message, buttons = extract_cta_from_text(message_content)
        
        if buttons:
            self.logger.info(f"Extracted {len(buttons)} CTA button(s) from message")
        
        # Send message via appropriate channel
        return self._send_via_channel(context, clean_message, buttons)
    
    def _send_via_channel(self, context, message, buttons=None):
        """Send message via the appropriate channel"""
        channel = context.get('channel', 'instagram')
        
        if channel == 'instagram':
            from message.services.instagram_service import InstagramService
            service = InstagramService()
            return service.send_message(
                recipient_id=context['recipient_id'],
                message_text=message,
                buttons=buttons
            )
        elif channel == 'telegram':
            # Add Telegram support
            pass
        else:
            self.logger.warning(f"Unsupported channel: {channel}")
            return {'success': False, 'error': 'Unsupported channel'}
    
    def _render_template(self, template, context):
        """Render template variables"""
        # Simple variable replacement
        # You can enhance this with proper templating engine
        import re
        
        def replace_var(match):
            var_name = match.group(1)
            return str(context.get(var_name, match.group(0)))
        
        return re.sub(r'{{(\w+)}}', replace_var, template)
```

## Testing the Integration

### Manual Test Script

```python
# test_key_values_integration.py

from workflow.models import ActionNode, WaitingNode
from workflow.services.action_executor import ActionExecutor

# Test 1: Create action node with key_values
action_node = ActionNode.objects.create(
    workflow=workflow,
    title="Test Send Message",
    action_type="send_message",
    message_content="Check out our products!",
    key_values=[
        "CTA:View Products|https://example.com/products",
        "CTA:Contact Us|https://example.com/contact"
    ],
    position_x=100,
    position_y=100
)

# Test 2: Execute action
executor = ActionExecutor()
context = {
    'channel': 'instagram',
    'recipient_id': 'test_user_123',
    'user': 'test_customer'
}

result = executor.execute_action(action_node, context)
print(f"Execution result: {result}")

# Test 3: Create waiting node with key_values
waiting_node = WaitingNode.objects.create(
    workflow=workflow,
    title="Test Waiting Node",
    storage_type="text",
    customer_message="Please provide feedback",
    key_values=[
        "CTA:Rate Us|https://example.com/rate"
    ],
    position_x=200,
    position_y=200
)

# Test 4: Execute waiting node
# (Similar execution logic)
```

## Best Practices

1. **Always validate key_values format**: Ensure each item follows "CTA:Title|URL" format
2. **Respect platform limits**: Instagram allows max 3 buttons
3. **Combine intelligently**: If message content has CTA tags AND key_values exist, combine them but respect limits
4. **Log button generation**: Log when buttons are created for debugging
5. **Graceful degradation**: If button creation fails, still send the message without buttons
6. **URL validation**: Validate URLs before creating buttons

## Error Handling

```python
def safe_extract_buttons(message_content, key_values):
    """Safely extract buttons with error handling"""
    try:
        # Extract from message content
        from message.utils.cta_utils import extract_cta_from_text
        clean_message, buttons = extract_cta_from_text(message_content)
    except Exception as e:
        logger.error(f"Error extracting CTAs from message: {e}")
        clean_message = message_content
        buttons = None
    
    try:
        # Extract from key_values
        if key_values:
            kv_buttons = extract_buttons_from_key_values(key_values)
            if buttons and kv_buttons:
                buttons.extend(kv_buttons)
            elif kv_buttons:
                buttons = kv_buttons
    except Exception as e:
        logger.error(f"Error extracting buttons from key_values: {e}")
    
    # Limit to 3 buttons
    if buttons and len(buttons) > 3:
        logger.warning(f"Too many buttons ({len(buttons)}), keeping first 3")
        buttons = buttons[:3]
    
    return clean_message, buttons
```

## Summary

The key_values field is now fully integrated into the database and API layer. To complete the implementation, you need to:

1. Update the action executor to process key_values
2. Update the waiting node executor to process key_values
3. Update the Instagram comment DM reply handler to process key_values
4. Add tests to verify the integration
5. Deploy the database migration

The existing CTA extraction system (`message/utils/cta_utils.py`) already handles the button creation, so you mainly need to append key_values to the message content in the CTA format before calling `extract_cta_from_text()`.

