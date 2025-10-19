# WebSocket Real-Time Chat API Documentation

This document describes the WebSocket APIs for real-time chat functionality in the Fiko Backend.

## Overview

The system provides two main WebSocket endpoints:
1. **Chat WebSocket** - For real-time messaging within a specific conversation
2. **Conversation List WebSocket** - For real-time updates to the user's conversation list

## Authentication

WebSocket connections require JWT authentication via query parameter:
```
ws://your-domain/ws/endpoint/?token=YOUR_JWT_ACCESS_TOKEN
```

## WebSocket Endpoints

### 1. Chat WebSocket
**Endpoint:** `ws://your-domain/ws/chat/{conversation_id}/`

**Purpose:** Real-time messaging within a specific conversation

**Connection Example:**
```javascript
const token = 'your-jwt-access-token';
const conversationId = 'abc123';
const chatSocket = new WebSocket(`ws://localhost:8000/ws/chat/${conversationId}/?token=${token}`);
```

#### Sending Messages

**Send Chat Message:**
```javascript
chatSocket.send(JSON.stringify({
    'type': 'chat_message',
    'content': 'Hello, how can I help you?'
}));
```

**Send Typing Indicator:**
```javascript
chatSocket.send(JSON.stringify({
    'type': 'typing',
    'is_typing': true
}));
```

**Mark Messages as Read:**
```javascript
chatSocket.send(JSON.stringify({
    'type': 'mark_read'
}));
```

#### Receiving Messages

**Chat Message:**
```javascript
chatSocket.onmessage = function(e) {
    const data = JSON.parse(e.data);
    
    switch(data.type) {
        case 'chat_message':
            console.log('New message:', data.message);
            // data.message contains: id, content, type, customer, created_at, etc.
            break;
            
        case 'typing_indicator':
            console.log(`${data.username} is typing:`, data.is_typing);
            break;
            
        case 'messages_read':
            console.log('Messages marked as read by user:', data.user_id);
            break;
            
        case 'recent_messages':
            console.log('Recent messages loaded:', data.messages);
            break;
    }
};
```

### 2. Conversation List WebSocket
**Endpoint:** `ws://your-domain/ws/conversations/`

**Purpose:** Real-time updates to user's conversation list

**Connection Example:**
```javascript
const token = 'your-jwt-access-token';
const conversationSocket = new WebSocket(`ws://localhost:8000/ws/conversations/?token=${token}`);
```

#### Sending Messages

**Get Conversations:**
```javascript
conversationSocket.send(JSON.stringify({
    'type': 'get_conversations'
}));
```

**Refresh Conversations:**
```javascript
conversationSocket.send(JSON.stringify({
    'type': 'refresh_conversations'
}));
```

#### Receiving Messages

```javascript
conversationSocket.onmessage = function(e) {
    const data = JSON.parse(e.data);
    
    switch(data.type) {
        case 'conversations_list':
            console.log('Conversations:', data.conversations);
            // data.conversations contains array of conversation objects
            break;
            
        case 'new_customer_message':
            console.log('New customer message in conversation:', data.conversation_id);
            console.log('Message:', data.message);
            // Refresh conversation list or show notification
            break;
    }
};
```

## Message Structure

### Chat Message Object
```javascript
{
    "id": "msg123",
    "content": "Hello, how can I help you?",
    "type": "support", // or "customer", "AI", "marketing"
    "customer": {
        "id": 1,
        "first_name": "John",
        "last_name": "Doe",
        "source": "telegram"
    },
    "is_ai_response": false,
    "is_answered": true,
    "created_at": "2024-01-15T10:30:00Z"
}
```

### Conversation Object
```javascript
{
    "id": "conv123",
    "title": "telegram - John Doe",
    "status": "active", // or "support_active", "marketing_active", "closed"
    "customer": {
        "id": 1,
        "first_name": "John",
        "last_name": "Doe",
        "source": "telegram",
        "profile_picture": "https://example.com/profile.jpg"
    },
    "priority": 1,
    "created_at": "2024-01-15T09:00:00Z",
    "updated_at": "2024-01-15T10:30:00Z",
    "last_message": {
        "id": "msg123",
        "content": "Hello, how can I help you?",
        "type": "customer",
        "created_at": "2024-01-15T10:30:00Z"
    },
    "unread_count": 3
}
```

## Integration with External Platforms

When customers send messages via Telegram or Instagram, the system automatically:
1. Creates/updates the Customer record
2. Creates/updates the Conversation record  
3. Creates a new Message record
4. Notifies connected WebSocket consumers in real-time

This means users will receive instant notifications when customers message them from external platforms.

## Error Handling

**Connection Errors:**
- Invalid JWT token: Connection will be immediately closed
- No access to conversation: Connection will be closed
- Invalid conversation ID: Connection will be closed

**Message Errors:**
```javascript
{
    "error": "Invalid JSON format"
}
```

## Example Frontend Implementation

```javascript
class ChatManager {
    constructor(token) {
        this.token = token;
        this.chatSocket = null;
        this.conversationSocket = null;
    }
    
    connectToConversationList() {
        this.conversationSocket = new WebSocket(
            `ws://localhost:8000/ws/conversations/?token=${this.token}`
        );
        
        this.conversationSocket.onmessage = (e) => {
            const data = JSON.parse(e.data);
            this.handleConversationUpdate(data);
        };
    }
    
    connectToChat(conversationId) {
        if (this.chatSocket) {
            this.chatSocket.close();
        }
        
        this.chatSocket = new WebSocket(
            `ws://localhost:8000/ws/chat/${conversationId}/?token=${this.token}`
        );
        
        this.chatSocket.onmessage = (e) => {
            const data = JSON.parse(e.data);
            this.handleChatMessage(data);
        };
    }
    
    sendMessage(content) {
        if (this.chatSocket) {
            this.chatSocket.send(JSON.stringify({
                'type': 'chat_message',
                'content': content
            }));
        }
    }
    
    handleConversationUpdate(data) {
        // Update UI with new conversation list
        if (data.type === 'conversations_list') {
            this.updateConversationList(data.conversations);
        }
    }
    
    handleChatMessage(data) {
        // Update UI with new message
        if (data.type === 'chat_message') {
            this.addMessageToChat(data.message);
        }
    }
}
```

## Testing

You can test the WebSocket connections using tools like:
- **wscat** (command line): `wscat -c "ws://localhost:8000/ws/conversations/?token=YOUR_TOKEN"`
- **Postman** (WebSocket support)
- **Browser Developer Tools** (JavaScript console)

## Production Considerations

1. **SSL/TLS**: Use `wss://` instead of `ws://` in production
2. **Load Balancing**: Configure sticky sessions or use Redis for channel layers
3. **Rate Limiting**: Implement rate limiting for WebSocket messages
4. **Monitoring**: Monitor WebSocket connection counts and message throughput
5. **Scaling**: Use Redis Cluster for larger deployments 