# 📡 WebSocket API Documentation - Fiko Backend

## 📋 فهرست مطالب
- [Overview](#overview)
- [Authentication](#authentication)
- [Endpoints](#endpoints)
- [Event Types](#event-types)
- [Frontend Implementation](#frontend-implementation)
- [Error Handling](#error-handling)
- [Best Practices](#best-practices)
- [Examples](#examples)

---

## 🎯 Overview

سیستم WebSocket Fiko به شما امکان ارتباط real-time با backend را فراهم می‌کند. این سیستم شامل دو بخش اصلی است:

1. **Conversation List**: مدیریت لیست گفتگوها
2. **Chat**: گفتگوی خاص با مشتریان

### ویژگی‌های کلیدی:
- ✅ Real-time messaging
- ✅ Typing indicators  
- ✅ User presence (online/offline)
- ✅ Message read status
- ✅ Integration با Telegram و Instagram
- ✅ JWT Authentication
- ✅ Error handling

---

## 🔐 Authentication

### نحوه احراز هویت:
```javascript
const token = localStorage.getItem('access_token');
const wsUrl = `ws://api.fiko.net/ws/conversations/?token=${token}`;
```

### مدیریت توکن:
- توکن JWT را در query parameter ارسال کنید
- در صورت invalid بودن توکن، connection بسته می‌شود
- توکن expired در production باعث قطع connection می‌شود

---

## 🌐 Endpoints

### Base URL:
```
Production: wss://api.fiko.net
Development: ws://localhost:8000
```

### WebSocket Endpoints:

#### 1. Conversation List
```
ws://api.fiko.net/ws/conversations/?token={JWT_TOKEN}
```
- مدیریت لیست گفتگوها
- دریافت notification های جدید
- Real-time updates

#### 2. Specific Chat
```
ws://api.fiko.net/ws/chat/{conversation_id}/?token={JWT_TOKEN}
```
- گفتگوی خاص با مشتری
- ارسال و دریافت پیام
- Typing indicators و presence

---

## 📨 Event Types

### 🔵 Incoming Events (Frontend → Backend)

#### **Conversation List Events:**
```javascript
// دریافت لیست گفتگوها
{
  "type": "get_conversations"
}

// بازخوانی لیست گفتگوها
{
  "type": "refresh_conversations"
}
```

#### **Chat Events:**
```javascript
// ارسال پیام جدید
{
  "type": "chat_message",
  "content": "متن پیام شما"
}

// نمایش typing indicator
{
  "type": "typing",
  "is_typing": true  // یا false
}

// علامت‌گذاری پیام‌ها به عنوان خوانده شده
{
  "type": "mark_read"
}
```

---

### 🔴 Outgoing Events (Backend → Frontend)

#### **Conversation List Events:**

##### 📋 conversations_list
```javascript
{
  "type": "conversations_list",
  "conversations": [
    {
      "id": "conv_123",
      "title": "telegram - John Doe",
      "source": "telegram",
      "status": "active",
      "customer": {
        "id": 1,
        "first_name": "John",
        "last_name": "Doe",
        "source": "telegram"
      },
      "last_message": {
        "content": "آخرین پیام",
        "type": "customer",
        "created_at": "2024-01-15T10:30:00Z"
      },
      "unread_count": 3,
      "created_at": "2024-01-15T10:00:00Z",
      "updated_at": "2024-01-15T10:30:00Z"
    }
  ],
  "timestamp": "2024-01-15T10:30:00Z"
}
```

##### 🆕 new_customer_message
```javascript
{
  "type": "new_customer_message",
  "conversation_id": "conv_123",
  "message": {
    "id": "msg_456",
    "content": "پیام جدید از مشتری",
    "type": "customer",
    "created_at": "2024-01-15T10:30:00Z"
  },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

##### 🔄 conversation_updated
```javascript
{
  "type": "conversation_updated",
  "conversation_id": "conv_123"
}
```

#### **Chat Events:**

##### 💬 chat_message
```javascript
{
  "type": "chat_message",
  "message": {
    "id": "msg_789",
    "content": "پیام جدید",
    "type": "support",  // یا "customer"
    "customer": {
      "first_name": "John",
      "last_name": "Doe"
    },
    "created_at": "2024-01-15T10:30:00Z"
  },
  "external_send_result": {
    "success": true,
    "platform": "telegram"
  }
}
```

##### 📜 recent_messages
```javascript
{
  "type": "recent_messages",
  "messages": [
    {
      "id": "msg_123",
      "content": "پیام قدیمی",
      "type": "customer",
      "created_at": "2024-01-15T09:00:00Z"
    }
  ],
  "timestamp": "2024-01-15T10:30:00Z"
}
```

##### ⌨️ typing_indicator
```javascript
{
  "type": "typing_indicator",
  "user_id": 123,
  "username": "Support Agent",
  "is_typing": true,
  "conversation_id": "conv_123",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

##### 👁️ messages_read
```javascript
{
  "type": "messages_read",
  "user_id": 123
}
```

##### 🟢 user_presence
```javascript
{
  "type": "user_presence",
  "user_id": 123,
  "username": "Support Agent",
  "is_online": true,
  "timestamp": "2024-01-15T10:30:00Z"
}
```

#### **Error Events:**

##### ❌ error
```javascript
{
  "type": "error",
  "error": "Message content cannot be empty",
  "message": "خطا در ارسال پیام"
}
```

---

## 💻 Frontend Implementation

### 🔧 Basic Setup

```javascript
class FikoWebSocket {
  constructor(token) {
    this.token = token;
    this.conversationsSocket = null;
    this.chatSocket = null;
    this.currentConversationId = null;
  }

  // اتصال به لیست گفتگوها
  connectToConversations() {
    const wsUrl = `wss://api.fiko.net/ws/conversations/?token=${this.token}`;
    
    this.conversationsSocket = new WebSocket(wsUrl);
    
    this.conversationsSocket.onopen = () => {
      console.log('✅ Connected to conversations');
      this.requestConversations();
    };
    
    this.conversationsSocket.onmessage = (event) => {
      this.handleConversationsMessage(JSON.parse(event.data));
    };
    
    this.conversationsSocket.onclose = () => {
      console.log('❌ Conversations connection closed');
      // Auto reconnect logic
      setTimeout(() => this.connectToConversations(), 3000);
    };
    
    this.conversationsSocket.onerror = (error) => {
      console.error('❌ Conversations WebSocket error:', error);
    };
  }

  // اتصال به چت خاص
  connectToChat(conversationId) {
    if (this.chatSocket) {
      this.chatSocket.close();
    }
    
    this.currentConversationId = conversationId;
    const wsUrl = `wss://api.fiko.net/ws/chat/${conversationId}/?token=${this.token}`;
    
    this.chatSocket = new WebSocket(wsUrl);
    
    this.chatSocket.onopen = () => {
      console.log(`✅ Connected to chat ${conversationId}`);
    };
    
    this.chatSocket.onmessage = (event) => {
      this.handleChatMessage(JSON.parse(event.data));
    };
    
    this.chatSocket.onclose = () => {
      console.log('❌ Chat connection closed');
    };
  }

  // درخواست لیست گفتگوها
  requestConversations() {
    if (this.conversationsSocket?.readyState === WebSocket.OPEN) {
      this.conversationsSocket.send(JSON.stringify({
        type: 'get_conversations'
      }));
    }
  }

  // ارسال پیام
  sendMessage(content) {
    if (this.chatSocket?.readyState === WebSocket.OPEN) {
      this.chatSocket.send(JSON.stringify({
        type: 'chat_message',
        content: content
      }));
    }
  }

  // ارسال typing indicator
  sendTyping(isTyping) {
    if (this.chatSocket?.readyState === WebSocket.OPEN) {
      this.chatSocket.send(JSON.stringify({
        type: 'typing',
        is_typing: isTyping
      }));
    }
  }

  // علامت‌گذاری به عنوان خوانده شده
  markAsRead() {
    if (this.chatSocket?.readyState === WebSocket.OPEN) {
      this.chatSocket.send(JSON.stringify({
        type: 'mark_read'
      }));
    }
  }
}
```

### 📨 Message Handlers

```javascript
// مدیریت پیام‌های لیست گفتگوها
handleConversationsMessage(data) {
  switch (data.type) {
    case 'conversations_list':
      this.updateConversationsList(data.conversations);
      break;
      
    case 'new_customer_message':
      this.showNotification('پیام جدید دریافت شد!');
      this.updateConversationInList(data.conversation_id);
      this.playNotificationSound();
      break;
      
    case 'conversation_updated':
      this.refreshConversation(data.conversation_id);
      break;
      
    case 'error':
      this.showError(data.error);
      break;
  }
}

// مدیریت پیام‌های چت
handleChatMessage(data) {
  switch (data.type) {
    case 'recent_messages':
      this.loadRecentMessages(data.messages);
      break;
      
    case 'chat_message':
      this.addMessageToChat(data.message);
      this.scrollToBottom();
      break;
      
    case 'typing_indicator':
      this.showTypingIndicator(data.username, data.is_typing);
      break;
      
    case 'user_presence':
      this.updateUserPresence(data.user_id, data.is_online);
      break;
      
    case 'messages_read':
      this.markMessagesAsRead(data.user_id);
      break;
      
    case 'error':
      this.showError(data.error);
      break;
  }
}
```

### 🎨 UI Integration Examples

```javascript
// نمایش لیست گفتگوها
updateConversationsList(conversations) {
  const container = document.getElementById('conversations-list');
  container.innerHTML = '';
  
  conversations.forEach(conversation => {
    const element = this.createConversationElement(conversation);
    container.appendChild(element);
  });
}

// اضافه کردن پیام به چت
addMessageToChat(message) {
  const chatContainer = document.getElementById('chat-messages');
  const messageElement = this.createMessageElement(message);
  chatContainer.appendChild(messageElement);
  
  // Auto scroll to bottom
  chatContainer.scrollTop = chatContainer.scrollHeight;
}

// نمایش typing indicator
showTypingIndicator(username, isTyping) {
  const indicator = document.getElementById('typing-indicator');
  
  if (isTyping) {
    indicator.textContent = `${username} در حال تایپ...`;
    indicator.style.display = 'block';
  } else {
    indicator.style.display = 'none';
  }
}

// نمایش نوتیفیکیشن
showNotification(message) {
  // استفاده از browser notification API
  if (Notification.permission === 'granted') {
    new Notification('Fiko', {
      body: message,
      icon: '/path/to/icon.png'
    });
  }
  
  // یا نمایش toast notification
  this.showToast(message);
}
```

---

## ⚠️ Error Handling

### انواع خطاها:

```javascript
// خطاهای connection
websocket.onerror = (error) => {
  console.error('WebSocket error:', error);
  this.showConnectionError();
};

websocket.onclose = (event) => {
  if (event.code === 1008) {
    // Authentication failed
    this.redirectToLogin();
  } else {
    // Connection lost - attempt reconnect
    this.attemptReconnect();
  }
};

// خطاهای message
handleError(errorData) {
  switch (errorData.error) {
    case 'Message content cannot be empty':
      this.showError('پیام نمی‌تواند خالی باشد');
      break;
    case 'Authentication required':
      this.redirectToLogin();
      break;
    default:
      this.showError('خطای غیرمنتظره رخ داد');
  }
}
```

### Auto Reconnection:

```javascript
class WebSocketManager {
  constructor() {
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 5;
    this.reconnectInterval = 3000;
  }

  attemptReconnect() {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      
      setTimeout(() => {
        console.log(`🔄 Reconnection attempt ${this.reconnectAttempts}`);
        this.connect();
      }, this.reconnectInterval * this.reconnectAttempts);
    } else {
      console.error('❌ Max reconnection attempts reached');
      this.showConnectionError();
    }
  }

  onConnect() {
    this.reconnectAttempts = 0;
    console.log('✅ Connection restored');
  }
}
```

---

## 🏆 Best Practices

### 1. **Connection Management**
```javascript
// بستن connections هنگام خروج از صفحه
window.addEventListener('beforeunload', () => {
  fikoWebSocket.close();
});

// مدیریت multiple tabs
document.addEventListener('visibilitychange', () => {
  if (document.hidden) {
    // Reduce connection activity
  } else {
    // Resume full activity
  }
});
```

### 2. **Performance Optimization**
```javascript
// Debounce typing indicators
const sendTypingDebounced = debounce(() => {
  fikoWebSocket.sendTyping(false);
}, 1000);

// Throttle scroll events
const handleScroll = throttle(() => {
  // Handle infinite scroll
}, 100);
```

### 3. **Security**
```javascript
// همیشه token را validate کنید
if (!token || isTokenExpired(token)) {
  redirectToLogin();
  return;
}

// Sanitize message content
function sanitizeMessage(content) {
  return DOMPurify.sanitize(content);
}
```

### 4. **User Experience**
```javascript
// نمایش connection status
updateConnectionStatus(isConnected) {
  const indicator = document.getElementById('connection-status');
  indicator.className = isConnected ? 'connected' : 'disconnected';
  indicator.textContent = isConnected ? 'آنلاین' : 'آفلاین';
}

// Loading states
showLoading() {
  document.getElementById('loading').style.display = 'block';
}

hideLoading() {
  document.getElementById('loading').style.display = 'none';
}
```

---

## 📚 Complete Integration Example

```javascript
// کلاس کامل برای مدیریت WebSocket
class FikoChat {
  constructor(token) {
    this.token = token;
    this.ws = new FikoWebSocket(token);
    this.currentConversation = null;
    this.setupEventListeners();
  }

  init() {
    // اتصال اولیه
    this.ws.connectToConversations();
    
    // درخواست notification permission
    this.requestNotificationPermission();
  }

  setupEventListeners() {
    // Event listeners برای UI
    document.getElementById('send-button').addEventListener('click', () => {
      this.sendMessage();
    });

    document.getElementById('message-input').addEventListener('input', (e) => {
      this.handleTyping(e.target.value);
    });

    document.getElementById('message-input').addEventListener('keypress', (e) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        this.sendMessage();
      }
    });
  }

  selectConversation(conversationId) {
    this.currentConversation = conversationId;
    this.ws.connectToChat(conversationId);
    this.updateUIForConversation(conversationId);
  }

  sendMessage() {
    const input = document.getElementById('message-input');
    const content = input.value.trim();
    
    if (content) {
      this.ws.sendMessage(content);
      input.value = '';
      this.ws.sendTyping(false);
    }
  }

  handleTyping(value) {
    if (value.trim()) {
      this.ws.sendTyping(true);
      
      // Stop typing after 1 second of inactivity
      clearTimeout(this.typingTimeout);
      this.typingTimeout = setTimeout(() => {
        this.ws.sendTyping(false);
      }, 1000);
    } else {
      this.ws.sendTyping(false);
    }
  }

  requestNotificationPermission() {
    if ('Notification' in window && Notification.permission === 'default') {
      Notification.requestPermission();
    }
  }
}

// استفاده
const token = localStorage.getItem('access_token');
const fikoChat = new FikoChat(token);
fikoChat.init();
```

---

## 🔗 Message Flow Diagram

```
Frontend                    Backend                     External APIs
   |                          |                             |
   |--- Connect WebSocket ---->|                             |
   |<-- Connection Success ----|                             |
   |                          |                             |
   |--- Send Message --------->|                             |
   |                          |--- Send to Telegram ------->|
   |                          |<-- Telegram Response -------|
   |<-- Message Sent ---------|                             |
   |                          |                             |
   |                          |<-- Customer Reply ----------|
   |<-- New Message -----------|                             |
```

---

## 📞 Support & Contact

در صورت بروز مشکل یا سوال:

- **Backend Team**: [تیم بک‌اند]
- **Documentation**: این فایل
- **Test Environment**: `ws://localhost:8000`
- **Production Environment**: `wss://api.fiko.net`

---

## 📝 Change Log

### Version 1.0.0
- ✅ Basic WebSocket implementation
- ✅ Chat functionality
- ✅ Conversation list
- ✅ Typing indicators
- ✅ User presence
- ✅ Telegram/Instagram integration

---

**💡 نکته**: همیشه از latest version این documentation استفاده کنید و تغییرات را با تیم backend هماهنگ نمایید.

**🚀 موفق باشید!** 