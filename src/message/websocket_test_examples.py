"""
WebSocket Test Examples for Fiko Backend

Examples and utilities for testing WebSocket functionality
"""

# JavaScript Frontend Example
JAVASCRIPT_EXAMPLE = """
// Connect to conversations list
const conversationsSocket = new WebSocket(
    'ws://localhost:8000/ws/conversations/?token=' + jwtToken
);

conversationsSocket.onopen = function(e) {
    console.log('Connected to conversations list');
};

conversationsSocket.onmessage = function(e) {
    const data = JSON.parse(e.data);
    
    switch(data.type) {
        case 'conversations_list':
            updateConversationsList(data.conversations);
            break;
        case 'new_customer_message':
            refreshConversation(data.conversation_id);
            showNotification('New message received!');
            break;
        case 'error':
            console.error('WebSocket error:', data.message);
            break;
    }
};

// Connect to specific chat
const chatSocket = new WebSocket(
    'ws://localhost:8000/ws/chat/' + conversationId + '/?token=' + jwtToken
);

chatSocket.onmessage = function(e) {
    const data = JSON.parse(e.data);
    
    switch(data.type) {
        case 'recent_messages':
            loadMessages(data.messages);
            break;
        case 'chat_message':
            addNewMessage(data.message);
            break;
        case 'typing_indicator':
            showTypingIndicator(data.username, data.is_typing);
            break;
        case 'user_presence':
            updateUserPresence(data.user_id, data.is_online);
            break;
        case 'messages_read':
            markMessagesAsRead(data.user_id);
            break;
    }
};

// Send message
function sendMessage(content) {
    chatSocket.send(JSON.stringify({
        'type': 'chat_message',
        'content': content
    }));
}

// Send typing indicator
function sendTyping(isTyping) {
    chatSocket.send(JSON.stringify({
        'type': 'typing',
        'is_typing': isTyping
    }));
}
"""

# Python Client Example
PYTHON_EXAMPLE = """
import asyncio
import websockets
import json

async def test_websocket():
    uri = "ws://localhost:8000/ws/conversations/?token=YOUR_JWT_TOKEN"
    
    async with websockets.connect(uri) as websocket:
        async for message in websocket:
            data = json.loads(message)
            print(f"Received: {data}")

asyncio.run(test_websocket())
"""

# WebSocket Test Scenarios
TEST_SCENARIOS = """
Test Scenarios for WebSocket:

1. Connection Test:
   - Connect with valid JWT token ✓
   - Connect with invalid token (should fail) ✓
   - Connect without token (should fail) ✓

2. Conversation List:
   - Receive initial conversation list ✓
   - Receive updates when new messages arrive ✓
   - Real-time conversation sorting ✓

3. Chat Functionality:
   - Send/receive messages ✓
   - Typing indicators ✓
   - Message read status ✓
   - User presence indicators ✓

4. Multi-user Testing:
   - Multiple users in same conversation ✓
   - User isolation (users only see their conversations) ✓
   - Real-time updates across users ✓

5. Error Handling:
   - Network disconnection ✓
   - Invalid message format ✓
   - Server errors ✓
"""

print("WebSocket Examples and Test Scenarios")
print("="*50)
print(f"\nJavaScript Example:\n{JAVASCRIPT_EXAMPLE}")
print(f"\nPython Example:\n{PYTHON_EXAMPLE}")
print(f"\nTest Scenarios:\n{TEST_SCENARIOS}") 