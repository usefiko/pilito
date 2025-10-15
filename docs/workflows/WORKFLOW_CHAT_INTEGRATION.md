# Enhanced Workflow-Chat Integration

This document describes the comprehensive integration between the workflow system and chat functionality, enabling workflows to dynamically control AI behavior and affect conversations in real-time.

## Overview

The enhanced integration allows workflows to:
- **Control AI Response Behavior**: Enable/disable AI, set custom prompts, reset context
- **Provide Dynamic Context**: Add context data that AI can use for personalized responses
- **Send Real-time Messages**: Messages sent via workflows appear instantly in chat with WebSocket notifications
- **Affect User Conversations**: Workflows can modify conversation state, add tags, change statuses

## Key Features

### 🤖 AI Behavior Control

Workflows can now control how AI responds to customers:

```python
# Disable AI for a conversation
{
    "action_type": "control_ai_response",
    "action": "disable"
}

# Set custom AI prompt
{
    "action_type": "control_ai_response", 
    "action": "custom_prompt",
    "custom_prompt": "You are a premium support assistant for {{user.first_name}}. Be extra helpful."
}

# Enable AI with default behavior
{
    "action_type": "control_ai_response",
    "action": "enable"
}

# Reset AI conversation context
{
    "action_type": "control_ai_response",
    "action": "reset_context"
}
```

### 📊 Dynamic AI Context

Add context information that AI can use for personalized responses:

```python
{
    "action_type": "update_ai_context",
    "context_data": {
        "customer_tier": "premium",
        "last_purchase": "{{user.last_purchase}}",
        "support_priority": "high",
        "preferred_language": "English",
        "account_issues": ["billing", "technical"]
    }
}
```

### 💬 Enhanced Message Actions

Send messages that integrate seamlessly with the chat system:

```python
{
    "action_type": "send_message",
    "message": "Hello {{user.first_name}}! I've upgraded your support to premium tier.",
    "message_type": "marketing"  # or "support", "AI"
}
```

## How It Works

### 1. Trigger Integration

Workflows are automatically triggered by chat events:

- **MESSAGE_RECEIVED**: When customers send messages
- **CONVERSATION_CREATED**: When new conversations start
- **USER_CREATED**: When new customers are created
- **TAG_ADDED/REMOVED**: When customer tags change

### 2. AI Control Flow

1. **Signal Detection**: When a customer message is received, both workflow and AI signals fire
2. **Workflow Execution**: If triggers match, workflows execute their actions
3. **AI Check**: Before generating a response, AI checks for workflow control settings:
   ```python
   # Check if AI is disabled for this conversation
   ai_control = cache.get(f"ai_control_{conversation_id}", {})
   if ai_control.get('ai_enabled') is False:
       return  # Skip AI response
   ```
4. **Custom Prompt**: If workflow set a custom prompt, AI uses it instead of default
5. **Context Enhancement**: AI includes workflow context data in its prompt

### 3. Real-time Integration

- Workflow messages trigger WebSocket notifications
- Messages appear instantly in chat interfaces
- Metadata tracks workflow execution information

## Implementation Details

### New Action Types

#### `control_ai_response`
Controls AI behavior for conversations.

**Configuration:**
```json
{
    "action": "disable|enable|custom_prompt|reset_context",
    "custom_prompt": "Optional custom prompt text"
}
```

**Cache Keys:**
- `ai_control_{conversation_id}`: Stores AI control settings
- `ai_context_{conversation_id}`: Stores additional context data

#### `update_ai_context`
Adds context information for AI to use.

**Configuration:**
```json
{
    "context_data": {
        "key1": "value1",
        "key2": "{{template_variable}}"
    }
}
```

### Enhanced Send Message Action

Now includes:
- Real-time WebSocket notifications
- Workflow metadata tracking
- Message type specification
- External platform integration (Telegram/Instagram)

### Database Changes

New fields in `ActionNode` model:
- `ai_control_action`: Type of AI control action
- `ai_custom_prompt`: Custom prompt text
- `ai_context_data`: Additional context data

New choices in action types:
- `control_ai_response`
- `update_ai_context`

## Usage Examples

### Example 1: Premium Support Workflow

```python
# When customer mentions "help" or "support"
when_node = WhenNode(
    when_type="receive_message",
    keywords=["help", "support", "problem"]
)

# Set premium AI assistant
ai_control = ActionNode(
    action_type="control_ai_response",
    ai_control_action="custom_prompt",
    ai_custom_prompt="You are a premium support assistant. Prioritize customer satisfaction."
)

# Add customer context
context_update = ActionNode(
    action_type="update_ai_context",
    ai_context_data={
        "support_tier": "premium",
        "priority": "high"
    }
)

# Send acknowledgment
message_action = ActionNode(
    action_type="send_message",
    message_content="I've escalated your request to premium support!"
)
```

### Example 2: Language-Specific Support

```python
# When customer writes in Spanish
when_node = WhenNode(
    when_type="receive_message",
    keywords=["hola", "ayuda", "problema"]
)

# Set Spanish-speaking AI
ai_control = ActionNode(
    action_type="control_ai_response",
    ai_control_action="custom_prompt", 
    ai_custom_prompt="Eres un asistente de soporte en español. Responde en español de manera profesional."
)

# Update context
context_update = ActionNode(
    action_type="update_ai_context",
    ai_context_data={
        "preferred_language": "spanish",
        "detected_keywords": "{{event.data.content}}"
    }
)
```

### Example 3: Conditional AI Disable

```python
# When customer asks for human agent
when_node = WhenNode(
    when_type="receive_message",
    keywords=["human", "agent", "representative"]
)

# Disable AI
ai_control = ActionNode(
    action_type="control_ai_response",
    ai_control_action="disable"
)

# Notify customer
message_action = ActionNode(
    action_type="send_message",
    message_content="I'm connecting you with a human agent. Please wait a moment."
)

# Update conversation status
status_action = ActionNode(
    action_type="set_conversation_status", 
    configuration={"status": "support_active"}
)
```

## Technical Architecture

### Signal Flow
```
Customer Message → Django Signals → Workflow Triggers → Action Execution
                                        ↓
                  AI Signal Check ← Cache Check ← Workflow Actions
                                        ↓
                  AI Response Generation (with workflow context)
```

### Cache Architecture
```
ai_control_{conversation_id}: {
    "ai_enabled": true|false,
    "custom_prompt": "custom prompt text"
}

ai_context_{conversation_id}: {
    "key1": "value1", 
    "key2": "value2",
    ...
}
```

### WebSocket Integration
```
Workflow Message → Database Save → WebSocket Notification → Real-time UI Update
```

## Benefits

1. **Dynamic AI Behavior**: AI can adapt its responses based on conversation context
2. **Personalized Support**: Different AI personalities for different customer types
3. **Seamless Integration**: Workflow actions appear natively in chat
4. **Real-time Updates**: All changes reflect immediately in user interfaces
5. **Conditional Logic**: Complex business rules can control AI behavior
6. **Context Awareness**: AI has access to workflow-provided context data

## Testing

Run the integration test:
```bash
python test_workflow_chat_integration.py
```

This creates a test workflow that:
1. Triggers on support-related messages
2. Sets a premium AI prompt
3. Adds customer context
4. Sends a welcome message
5. Demonstrates real-time integration

## Configuration

### Cache Settings
Ensure Redis is configured for cache backend:
```python
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://localhost:6379/1',
    }
}
```

### Signal Configuration
Signals are automatically connected when apps are loaded. Ensure both `workflow` and `AI_model` apps are in `INSTALLED_APPS`.

## Best Practices

1. **Cache Timeouts**: AI control settings expire after 24 hours by default
2. **Template Variables**: Use `{{variable}}` syntax in prompts and context
3. **Error Handling**: Workflow failures don't break AI responses
4. **Performance**: Cache checks are fast and don't impact response time
5. **Testing**: Always test workflow changes with real conversations

## Migration

The integration requires the database migration:
```bash
python manage.py migrate workflow
```

This adds the new AI control fields to the `ActionNode` model.

## Troubleshooting

### AI Not Using Workflow Settings
- Check cache backend is working: `cache.get('test_key')`
- Verify conversation ID matches between workflow and AI
- Check workflow execution logs

### Messages Not Appearing in Chat
- Verify WebSocket connections are working
- Check `send_message_notification` is called
- Ensure message type is valid

### Workflow Not Triggering
- Check trigger conditions and keywords
- Verify workflow status is 'ACTIVE'
- Check signal connections in app initialization

## Future Enhancements

Potential future improvements:
- AI personality switching mid-conversation
- Workflow-controlled response delays
- Integration with external AI providers
- Advanced context templating
- Conversation flow control
- Automated A/B testing of AI responses
