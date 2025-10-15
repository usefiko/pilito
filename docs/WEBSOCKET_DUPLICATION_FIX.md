# WebSocket Message Duplication Fix

## Problem Description

The websocket implementation was experiencing message duplication where:
- **Messages were received 3 times** instead of once
- **Messages were sent 2 times** instead of once

## Root Cause Analysis

### Message Receive Duplication (3x)
1. `notify_new_customer_message()` sent to chat room (`chat_message` type)
2. `notify_new_customer_message()` sent to conversation list (`new_customer_message` type)  
3. `ConversationListConsumer.new_customer_message()` handler **forwarded message again** to chat room

### Message Send Duplication (2x)
1. Message sent to external platform (Telegram/Instagram) - ✅ Correct
2. **Redundant websocket broadcast** via both `broadcast_to_chat_room()` and `notify_new_customer_message()`

## Changes Made

### 1. Fixed ConversationListConsumer (`src/message/consumers.py`)

**Before:**
```python
async def new_customer_message(self, event):
    await self.send_conversations()
    
    # Also send the specific message to the conversation if someone is listening
    conversation_id = event.get('conversation_id')
    message = event.get('message')
    
    if conversation_id and message:
        chat_group_name = f'chat_{conversation_id}'
        await self.channel_layer.group_send(
            chat_group_name,
            {
                'type': 'chat_message',
                'message': message
            }
        )
```

**After:**
```python
async def new_customer_message(self, event):
    await self.send_conversations()
    
    # Remove the redundant message forwarding to chat room
    # The message has already been sent to chat room by notify_new_customer_message()
    # Only refresh the conversation list here
```

### 2. Fixed API Message Notifications (`src/message/api/send_message.py`)

**Before:**
```python
def _notify_websocket(self, message, external_result):
    # Notify the specific chat room
    broadcast_to_chat_room(...)
    
    # Notify conversation list for user
    notify_new_customer_message(message)  # DUPLICATE!
```

**After:**
```python
def _notify_websocket(self, message, external_result):
    # Notify the specific chat room
    broadcast_to_chat_room(...)
    
    # Update conversation list for user (without sending the message again)
    from message.websocket_utils import notify_conversation_status_change
    notify_conversation_status_change(message.conversation)
```

### 3. Optimized Websocket Utils (`src/message/websocket_utils.py`)

Added clear documentation that `notify_new_customer_message()` should only be used for incoming customer messages from external platforms.

### 4. Added Clarity to ChatConsumer (`src/message/consumers.py`)

Added comments to clarify the message flow and prevent future confusion about websocket broadcasts.

## Message Flow After Fix

### For Incoming Customer Messages (Webhooks):
1. Webhook receives message → saves to DB
2. Calls `notify_new_customer_message()`:
   - **1x** to chat room (`chat_message` type) ✅
   - **1x** to conversation list (`new_customer_message` type) ✅
3. ConversationListConsumer updates conversation list only (no forwarding)

### For Outgoing Support Messages (WebSocket):
1. ChatConsumer receives → saves to DB
2. **1x** Send to external platform ✅
3. **1x** Broadcast to conversation group ✅  
4. Update conversation list (no duplicate sends)

### For Outgoing Support Messages (REST API):
1. API receives → saves to DB
2. **1x** Send to external platform ✅
3. **1x** Broadcast to chat room ✅
4. Update conversation list (separate from message notification)

## Verification

Use the provided test file `src/message/websocket_test_fixed.py` to verify that:
- Messages are received exactly once
- Messages are sent exactly once
- No redundant websocket notifications occur

## Benefits

- ✅ Eliminated message duplication
- ✅ Improved websocket performance
- ✅ Clearer separation of concerns
- ✅ Better user experience
- ✅ Reduced server load

## Files Modified

1. `src/message/consumers.py` - Removed redundant message forwarding
2. `src/message/api/send_message.py` - Fixed duplicate notifications  
3. `src/message/websocket_utils.py` - Added documentation and clarity
4. `src/message/websocket_test_fixed.py` - Added verification test 