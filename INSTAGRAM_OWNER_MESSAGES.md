# Instagram Owner Messages Feature

## Overview
This feature enables the system to capture and sync messages that account owners send **directly from Instagram** (not through our app) into our database and websocket system.

## Problem Statement
Previously, when an account owner replied to a customer **directly from the Instagram app**, these messages were:
- ❌ Not saved to our database
- ❌ Not visible in our app's conversation history
- ❌ Not broadcasted via websocket to connected clients

This created inconsistencies where conversations in our app would be incomplete, missing messages sent from Instagram directly.

## Solution
We've enhanced the Instagram webhook handler (`src/message/insta.py`) to:
1. **Detect message direction**: Identify whether a message is from the account owner or from a customer
2. **Save owner messages**: Store messages sent by the account owner as `type='support'` 
3. **Broadcast to websocket**: Notify all connected clients when owner messages arrive
4. **Update conversation**: Keep conversation timestamps and status current

## Technical Changes

### 1. Message Direction Detection (`insta.py`)
```python
# Determine message direction
account_owner_id = page_id  # The webhook owner's Instagram ID
is_customer_message = (sender_id != account_owner_id)
is_owner_message = (sender_id == account_owner_id)
```

**How it works:**
- Instagram webhooks send messages with `sender` and `recipient` fields
- When the account owner sends a message:
  - `sender_id` = account owner's Instagram ID
  - `recipient_id` = customer's Instagram ID
- When a customer sends a message:
  - `sender_id` = customer's Instagram ID
  - `recipient_id` = account owner's Instagram ID

### 2. Deduplication Logic (Anti-Echo Prevention)

**Problem**: When AI or support sends a message through our app → Instagram → Instagram webhooks it back → Creating duplicate

**Solution**: Check if message already exists before creating
```python
# Check for recent messages (last 30 seconds) with same content
recent_cutoff = timezone.now() - timedelta(seconds=30)
existing_message = Message.objects.filter(
    conversation=conversation,
    content=message_text,
    created_at__gte=recent_cutoff,
    type__in=['support', 'AI']  # Could be either support or AI
).first()

if existing_message:
    logger.info("⚠️ Duplicate owner message detected - skipping")
    return {"status": "success", "duplicate": True}
```

**Why this works**:
- When we send a message via our app, it's saved immediately to database
- Instagram webhooks typically arrive within 1-2 seconds
- We check if an identical message exists in the last 30 seconds
- If found, skip creating the duplicate

**Edge cases handled**:
- ✅ AI messages (type='AI', is_ai_response=True)
- ✅ Support messages (type='support')
- ✅ Messages sent from Instagram app directly (no duplicate = create new)
- ✅ Time window of 30 seconds handles webhook delays

### 3. Customer Identification
```python
# For owner messages, the customer is the RECIPIENT
# For customer messages, the customer is the SENDER
customer_instagram_id = recipient_id if is_owner_message else sender_id
```

This ensures we always identify the correct customer, regardless of message direction.

### 3. Channel Lookup
Updated channel lookup to use `account_owner_id` (instead of always using `recipient_id`):
```python
lookup_id = account_owner_id
channel = InstagramChannel.objects.filter(page_id=lookup_id, is_connect=True).first()
```

### 4. Message Type Assignment
```python
# Determine message type based on sender
msg_type = 'support' if is_owner_message else 'customer'

# Create message with correct type
Message.objects.create(
    content=message_text,
    conversation=conversation,
    customer=customer,
    type=msg_type,  # 'support' for owner, 'customer' for customer
    message_type='text',
    processing_status='completed'
)
```

### 5. WebSocket Broadcasting

**For Customer Messages** (existing behavior):
```python
notify_new_customer_message(message_obj)
```

**For Owner Messages** (new behavior):
```python
from message.websocket_utils import broadcast_to_chat_room, notify_conversation_status_change
from message.serializers import WSMessageSerializer

# Broadcast message to chat room
broadcast_to_chat_room(
    conversation.id,
    'chat_message',
    {
        'message': WSMessageSerializer(message_obj).data,
        'external_send_result': {'success': True, 'source': 'instagram_direct'}
    }
)

# Update conversation list
notify_conversation_status_change(conversation)
```

### 6. Enhanced Serializer (`serializers.py`)
Updated `WSMessageSerializer` to include media fields:
```python
fields = ['id', 'content', 'type', 'customer', 'conversation_id', 'is_ai_response', 
         'is_answered', 'created_at', 'feedback', 'feedback_comment', 'feedback_at', 
         'message_type', 'media_url', 'media_file', 'processing_status', 'transcription']
```

This ensures websocket clients receive complete message information including media attachments.

## Message Flow

### Scenario: Account Owner Sends Message from Instagram

1. **Owner sends message** in Instagram app to customer
2. **Instagram webhook** fires and sends data to our endpoint
3. **Our system detects** this is an owner message (sender = account_owner_id)
4. **Customer is identified** from recipient_id
5. **Conversation is fetched/created** for this customer
6. **Message is saved** to database with `type='support'`
7. **WebSocket broadcasts** the message to all connected clients
8. **Conversation list updates** to reflect the new message

### Scenario: Customer Sends Message to Owner (existing flow, unchanged)

1. **Customer sends message** in Instagram app
2. **Instagram webhook** fires
3. **Our system detects** this is a customer message (sender ≠ account_owner_id)
4. **Customer is identified** from sender_id
5. **Conversation is fetched/created**
6. **Message is saved** with `type='customer'`
7. **WebSocket broadcasts** via `notify_new_customer_message()`
8. **AI/workflow triggers** may activate if configured

## Testing

### Manual Testing Steps

1. **Setup**: Ensure Instagram channel is connected in your app
2. **Send message from Instagram**:
   - Open Instagram app on your phone
   - Go to Direct Messages
   - Find a customer conversation
   - Send a message
3. **Verify in App**:
   - Check conversation in your app
   - Message should appear immediately (via websocket)
   - Message type should be 'support'
   - Conversation timestamp should update
4. **Check Database**:
   ```sql
   SELECT id, content, type, message_type, created_at 
   FROM message_message 
   WHERE conversation_id = 'CONVERSATION_ID'
   ORDER BY created_at DESC;
   ```

### Expected Results

✅ Message appears in app conversation immediately
✅ Message type is 'support' (not 'customer')
✅ Message content matches what was sent from Instagram
✅ Conversation updated_at timestamp is current
✅ WebSocket clients receive real-time notification
✅ No duplicate messages created

## API Response Format

When an owner message is received, the webhook returns:

```json
{
  "status": "success",
  "message": "Message received and processed successfully",
  "data": {
    "message_direction": "owner_to_customer",
    "channel": {
      "username": "your_instagram_username",
      "owner": {
        "id": 123,
        "email": "owner@example.com"
      }
    },
    "customer": {
      "id": "abc123",
      "instagram_id": "987654321",
      "first_name": "John",
      "last_name": "Doe",
      "source": "instagram",
      "was_created": false,
      "enhanced_data_fetched": true
    },
    "conversation": {
      "id": "conv_xyz",
      "source": "instagram",
      "was_created": false
    },
    "message": {
      "id": "msg_123",
      "content": "Hello from Instagram!",
      "type": "support",
      "message_type": "text",
      "timestamp": "2025-11-07T10:30:00Z"
    }
  }
}
```

## Benefits

1. **Complete Conversation History**: All messages (from app or Instagram) are stored
2. **Real-time Sync**: Messages appear instantly via websocket
3. **Better Customer Experience**: Customers see all responses regardless of where they were sent
4. **Accurate Analytics**: Reporting includes all support messages
5. **Multi-Channel Support**: Staff can reply from Instagram or the app interchangeably

## Limitations & Considerations

1. **Instagram API Rate Limits**: Heavy usage may hit Instagram API limits
2. **Webhook Delays**: Instagram webhooks typically deliver within 1-2 seconds
3. **Message Order**: Messages are ordered by `created_at` timestamp
4. **Media Messages**: Image/voice messages from Instagram are queued for async processing

## Future Enhancements

- [ ] Add notification when owner messages arrive
- [ ] Show indicator in UI for messages sent from Instagram vs app
- [ ] Add message editing/deletion sync
- [ ] Add read receipts sync
- [ ] Support Instagram Stories mentions and replies

## Related Files

- `src/message/insta.py` - Instagram webhook handler (main changes)
- `src/message/serializers.py` - Message serializers (enhanced fields)
- `src/message/websocket_utils.py` - WebSocket utilities (used for broadcasting)
- `src/message/models.py` - Message model definition

## Troubleshooting

### Messages not appearing in app

1. **Check webhook logs**:
   ```bash
   # Look for Instagram webhook POST requests
   grep "Instagram Webhook Data" logs/app.log
   ```

2. **Verify channel mapping**:
   ```python
   # Check if page_id matches webhook recipient_id
   InstagramChannel.objects.filter(is_connect=True).values('id', 'username', 'page_id', 'instagram_user_id')
   ```

3. **Check message creation**:
   ```bash
   # Look for message creation logs
   grep "Text message created" logs/app.log
   ```

### Messages saved but not broadcasting

1. **Check websocket connection**:
   - Open browser console
   - Look for websocket errors
   
2. **Check Redis** (if using Redis for channels):
   ```bash
   redis-cli ping
   ```

3. **Verify channel layer**:
   ```python
   from channels.layers import get_channel_layer
   channel_layer = get_channel_layer()
   print(channel_layer)
   ```

## Support

For issues or questions, check:
- Django logs: `logs/django.log`
- Webhook logs: Look for Instagram webhook entries
- Database: Verify messages are being created
- WebSocket: Check browser console for connection issues

---

## Bug Fixes

### Duplicate AI Messages (Fixed)

**Issue**: AI-generated messages were appearing twice - once as AI message and once as support message.

**Root Cause**: 
1. AI generates response → saved to DB as `type='AI'`
2. AI service sends message to Instagram API
3. Instagram webhooks the message back to us
4. Our code treated it as "owner message" → saved again as `type='support'`
5. Result: Duplicate messages in conversation

**Fix**: Added deduplication logic that checks for existing messages before creating new ones:
```python
# For owner messages, check if identical message exists in last 30 seconds
existing_message = Message.objects.filter(
    conversation=conversation,
    content=message_text,
    created_at__gte=recent_cutoff,
    type__in=['support', 'AI']
).first()

if existing_message:
    # Skip creating duplicate
    return {"status": "success", "duplicate": True}
```

**Result**: ✅ No more duplicates - AI messages appear only once

