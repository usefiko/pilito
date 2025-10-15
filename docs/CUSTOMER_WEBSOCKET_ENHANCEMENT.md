# CustomerListConsumer Enhancement

## Overview
Enhanced the `CustomerListConsumer` WebSocket consumer to include comprehensive conversation data for each customer, providing a richer real-time experience for customer management interfaces.

## Changes Made

### 1. New Serializer: `CustomerWithConversationSerializer`
**File:** `src/message/serializers.py`

Created a new serializer that extends customer data with conversation information:

```python
class CustomerWithConversationSerializer(serializers.ModelSerializer):
    """Enhanced customer serializer including conversation data for WebSocket"""
    conversations = serializers.SerializerMethodField()
```

**Features:**
- Includes all customer fields (name, email, phone, source, etc.)
- Adds `conversations` field with detailed conversation data
- Filters conversations by the current user context
- Optimized for WebSocket real-time updates

### 2. Enhanced Data Structure

**Before (CustomerSerializer):**
```json
{
  "id": "customer_id",
  "first_name": "John",
  "last_name": "Doe",
  "email": "john@example.com",
  "source": "instagram"
}
```

**After (CustomerWithConversationSerializer):**
```json
{
  "id": "customer_id",
  "first_name": "John",
  "last_name": "Doe",
  "email": "john@example.com",
  "source": "instagram",
  "conversations": [
    {
      "id": "conv_id",
      "title": "Instagram - John Doe",
      "status": "active",
      "source": "instagram",
      "priority": 1,
      "is_active": true,
      "created_at": "2023-01-01T00:00:00Z",
      "updated_at": "2023-01-01T12:00:00Z",
      "last_message": {
        "id": "msg_id",
        "content": "Hello, I need help with...",
        "type": "customer",
        "is_ai_response": false,
        "created_at": "2023-01-01T12:00:00Z"
      },
      "unread_count": 3
    }
  ]
}
```

### 3. Updated Consumer Logic
**File:** `src/message/consumers.py`

- **Enhanced Query Optimization:** Added prefetch for conversations and messages
- **Updated Serializer Usage:** Now uses `CustomerWithConversationSerializer` with user context
- **Performance Adjustment:** Reduced default pagination limit from 100 to 50 items
- **Improved Documentation:** Added comprehensive docstring with data structure example

### 4. Query Optimization

```python
# Enhanced prefetch strategy
customers_query = Customer.objects.filter(
    conversations__user=self.user
).select_related().prefetch_related(
    'tag',
    'conversations__messages',  # NEW: Prefetch messages for last_message
    'conversations'             # NEW: Prefetch conversations
).distinct()
```

## Benefits

### 1. **Rich Customer Context**
- Each customer now includes their conversation history
- Last message content and metadata
- Unread message counts
- Conversation status (active, closed, etc.)

### 2. **Real-time AI Integration**
- Shows if last message was an AI response
- Conversation status indicates AI handling mode
- Unread counts help prioritize customer attention

### 3. **Enhanced UX Possibilities**
- Customer list can show conversation previews
- Unread indicators for prioritization
- Status badges for conversation states
- Source-specific icons and handling

### 4. **Performance Optimized**
- Uses Django's `prefetch_related` for efficient queries
- Reduced pagination limit to handle larger payloads
- Optimized serializer for WebSocket performance

## Usage

### Frontend Integration
Connect to the WebSocket and receive enhanced customer data:

```javascript
const ws = new WebSocket('ws://localhost:8000/ws/customers/');

ws.onmessage = function(event) {
    const data = JSON.parse(event.data);
    
    if (data.type === 'customers_list') {
        data.customers.forEach(customer => {
            console.log(`Customer: ${customer.first_name}`);
            
            customer.conversations.forEach(conversation => {
                console.log(`  Conversation: ${conversation.status}`);
                console.log(`  Unread: ${conversation.unread_count}`);
                
                if (conversation.last_message) {
                    console.log(`  Last: ${conversation.last_message.content}`);
                }
            });
        });
    }
};
```

### Testing
Run the test command to verify functionality:

```bash
python manage.py test_customer_websocket
```

## Performance Considerations

1. **Pagination:** Default limit reduced to 50 customers due to richer data
2. **Prefetch Strategy:** Optimized to minimize database queries
3. **WebSocket Payload:** Larger payloads due to conversation data - monitor network usage
4. **Memory Usage:** Increased due to prefetched conversation data

## Migration Notes

- **Backward Compatible:** Existing WebSocket clients will receive additional data
- **No Database Changes:** Uses existing models and relationships
- **API Impact:** Only affects WebSocket responses, REST APIs unchanged

## Related Files Modified

1. `src/message/serializers.py` - Added `CustomerWithConversationSerializer`
2. `src/message/consumers.py` - Enhanced `CustomerListConsumer`
3. `src/message/management/commands/test_customer_websocket.py` - Test command

## Future Enhancements

- Add conversation filtering options
- Include message attachments in last_message
- Add typing indicators
- Include customer interaction analytics
- Add conversation priority sorting options