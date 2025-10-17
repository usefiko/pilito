# 🔌 WebSocket Connection & Reconnect Management Guide

## ✅ Backend Changes Applied

### 1. Connection Established Messages
در تمام 3 consumer (ChatConsumer, ConversationListConsumer, CustomerListConsumer) بعد از `accept()` پیام زیر ارسال می‌شود:

```json
{
  "type": "connection_established",
  "message": "✅ WebSocket connected successfully",
  "timestamp": "2023-10-17T12:00:00Z"
}
```

### 2. JWT Token Validation
- اگر token منقضی شده یا invalid باشد، connection بسته می‌شود با close code `4001`
- پیام error ارسال می‌شود:

```json
{
  "type": "authentication_error",
  "message": "Invalid or expired authentication token",
  "error_code": "AUTH_REQUIRED",
  "timestamp": "2023-10-17T12:00:00Z"
}
```

### 3. Disconnect Handling
- تمام connections در disconnect به درستی cleanup می‌شوند
- Groups به درستی leave می‌شوند
- User presence به درستی update می‌شود

---

## 🎯 Frontend Implementation Guide

### مشکل فعلی:
1. ✖️ چندین WebSocket به صورت همزمان باز می‌شود
2. ✖️ Reconnect بی‌پایان رخ می‌دهد
3. ✖️ Token expiration مدیریت نمی‌شود

### راه‌حل:

## 1️⃣ WebSocket Manager Class

```javascript
// websocketManager.js
class WebSocketManager {
  constructor(url, token) {
    this.url = url;
    this.token = token;
    this.ws = null;
    this.isConnected = false;
    this.isConnecting = false;
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 5;
    this.reconnectDelay = 2000; // 2 seconds
    this.reconnectTimeout = null;
    this.listeners = new Map();
    this.shouldReconnect = true; // Flag to control reconnection
  }

  connect() {
    // ✅ Prevent multiple simultaneous connections
    if (this.ws && (this.ws.readyState === WebSocket.CONNECTING || this.ws.readyState === WebSocket.OPEN)) {
      console.warn('❌ WebSocket already connecting or connected');
      return;
    }

    if (this.isConnecting) {
      console.warn('❌ Connection attempt already in progress');
      return;
    }

    this.isConnecting = true;
    console.log('🔌 Connecting to WebSocket:', this.url);

    try {
      this.ws = new WebSocket(`${this.url}?token=${this.token}`);
      
      this.ws.onopen = this.handleOpen.bind(this);
      this.ws.onmessage = this.handleMessage.bind(this);
      this.ws.onerror = this.handleError.bind(this);
      this.ws.onclose = this.handleClose.bind(this);
    } catch (error) {
      console.error('❌ Error creating WebSocket:', error);
      this.isConnecting = false;
      this.scheduleReconnect();
    }
  }

  handleOpen(event) {
    console.log('✅ WebSocket connected:', this.url);
    this.isConnected = false; // Wait for connection_established
    this.isConnecting = false;
    this.reconnectAttempts = 0;

    // Clear any pending reconnect timeout
    if (this.reconnectTimeout) {
      clearTimeout(this.reconnectTimeout);
      this.reconnectTimeout = null;
    }
  }

  handleMessage(event) {
    try {
      const data = JSON.parse(event.data);
      
      // ✅ Handle connection_established
      if (data.type === 'connection_established') {
        console.log('✅ Connection established confirmed:', data.message);
        this.isConnected = true;
        this.reconnectAttempts = 0;
        this.shouldReconnect = true; // Enable reconnection
        this.emit('connected', data);
        return;
      }

      // ✅ Handle authentication errors
      if (data.type === 'authentication_error') {
        console.error('❌ Authentication error:', data.message);
        this.shouldReconnect = false; // Disable reconnection for auth errors
        this.emit('authError', data);
        this.disconnect();
        return;
      }

      // Emit message to listeners
      this.emit(data.type, data);
    } catch (error) {
      console.error('❌ Error parsing WebSocket message:', error);
    }
  }

  handleError(event) {
    console.error('❌ WebSocket error:', event);
    this.isConnecting = false;
    this.emit('error', event);
  }

  handleClose(event) {
    console.log('🔌 WebSocket closed:', event.code, event.reason);
    this.isConnected = false;
    this.isConnecting = false;
    this.ws = null;

    this.emit('disconnected', {
      code: event.code,
      reason: event.reason,
      wasClean: event.wasClean
    });

    // ✅ Only reconnect if:
    // 1. shouldReconnect is true (not auth error)
    // 2. Close code is not 4001 (auth error)
    // 3. Max attempts not reached
    if (this.shouldReconnect && event.code !== 4001 && this.reconnectAttempts < this.maxReconnectAttempts) {
      this.scheduleReconnect();
    } else if (event.code === 4001) {
      console.warn('❌ Authentication error - not reconnecting');
      this.emit('authError', { message: 'Token expired or invalid' });
    } else if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error('❌ Max reconnect attempts reached');
      this.emit('maxReconnectReached');
    }
  }

  scheduleReconnect() {
    // Clear any existing timeout
    if (this.reconnectTimeout) {
      clearTimeout(this.reconnectTimeout);
    }

    this.reconnectAttempts++;
    const delay = Math.min(this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1), 30000); // Max 30s
    
    console.log(`🔄 Scheduling reconnect attempt ${this.reconnectAttempts} in ${delay}ms`);

    this.reconnectTimeout = setTimeout(() => {
      console.log(`🔄 Reconnecting... (attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
      this.connect();
    }, delay);
  }

  disconnect() {
    console.log('👋 Disconnecting WebSocket');
    this.shouldReconnect = false; // Prevent reconnection

    // Clear reconnect timeout
    if (this.reconnectTimeout) {
      clearTimeout(this.reconnectTimeout);
      this.reconnectTimeout = null;
    }

    // Close WebSocket
    if (this.ws) {
      try {
        this.ws.close(1000, 'Client disconnect');
      } catch (error) {
        console.error('Error closing WebSocket:', error);
      }
      this.ws = null;
    }

    this.isConnected = false;
    this.isConnecting = false;
  }

  send(data) {
    if (!this.ws || !this.isConnected) {
      console.error('❌ Cannot send message: WebSocket not connected');
      return false;
    }

    try {
      this.ws.send(JSON.stringify(data));
      return true;
    } catch (error) {
      console.error('❌ Error sending message:', error);
      return false;
    }
  }

  on(event, callback) {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, []);
    }
    this.listeners.get(event).push(callback);
  }

  off(event, callback) {
    if (this.listeners.has(event)) {
      const callbacks = this.listeners.get(event);
      const index = callbacks.indexOf(callback);
      if (index !== -1) {
        callbacks.splice(index, 1);
      }
    }
  }

  emit(event, data) {
    if (this.listeners.has(event)) {
      this.listeners.get(event).forEach(callback => {
        try {
          callback(data);
        } catch (error) {
          console.error(`Error in listener for ${event}:`, error);
        }
      });
    }
  }

  // ✅ Update token (for token refresh scenarios)
  updateToken(newToken) {
    this.token = newToken;
    console.log('🔑 Token updated');
  }
}

export default WebSocketManager;
```

---

## 2️⃣ React Hook Usage Example

```javascript
// useWebSocket.js
import { useEffect, useRef, useState } from 'react';
import WebSocketManager from './websocketManager';

export function useWebSocket(url, token, onMessage) {
  const wsManager = useRef(null);
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    // ✅ Only create WebSocket if token exists
    if (!token) {
      console.warn('❌ No token provided, skipping WebSocket connection');
      return;
    }

    // ✅ Prevent multiple connections
    if (wsManager.current) {
      console.log('♻️ WebSocket manager already exists, reusing');
      return;
    }

    console.log('🆕 Creating new WebSocket manager');
    wsManager.current = new WebSocketManager(url, token);

    // Setup event listeners
    wsManager.current.on('connected', () => {
      console.log('✅ WebSocket connected successfully');
      setIsConnected(true);
      setError(null);
    });

    wsManager.current.on('disconnected', () => {
      console.log('🔌 WebSocket disconnected');
      setIsConnected(false);
    });

    wsManager.current.on('authError', (data) => {
      console.error('❌ Authentication error:', data);
      setError('Authentication failed. Please login again.');
      setIsConnected(false);
      
      // Redirect to login or show error
      // window.location.href = '/login';
    });

    wsManager.current.on('error', (error) => {
      console.error('❌ WebSocket error:', error);
      setError('Connection error');
    });

    wsManager.current.on('maxReconnectReached', () => {
      console.error('❌ Max reconnect attempts reached');
      setError('Unable to connect. Please refresh the page.');
    });

    // Setup message handler
    if (onMessage) {
      // Listen to all message types
      const messageTypes = ['chat_message', 'conversations_list', 'customers_list', 'ai_message'];
      messageTypes.forEach(type => {
        wsManager.current.on(type, onMessage);
      });
    }

    // Connect
    wsManager.current.connect();

    // ✅ Cleanup on unmount
    return () => {
      console.log('🧹 Cleaning up WebSocket');
      if (wsManager.current) {
        wsManager.current.disconnect();
        wsManager.current = null;
      }
    };
  }, [url, token]); // Only reconnect if URL or token changes

  // ✅ Handle visibility change (tab switching)
  useEffect(() => {
    const handleVisibilityChange = () => {
      if (document.hidden) {
        console.log('👁️ Tab hidden, keeping connection alive');
        // Keep connection alive even when tab is hidden
      } else {
        console.log('👁️ Tab visible');
        // Optionally refresh data when tab becomes visible
        if (wsManager.current && wsManager.current.isConnected) {
          // Send refresh request
          wsManager.current.send({ type: 'refresh_conversations' });
        }
      }
    };

    document.addEventListener('visibilitychange', handleVisibilityChange);
    
    return () => {
      document.removeEventListener('visibilitychange', handleVisibilityChange);
    };
  }, []);

  return {
    isConnected,
    error,
    send: (data) => wsManager.current?.send(data),
    disconnect: () => wsManager.current?.disconnect()
  };
}
```

---

## 3️⃣ Usage in Component

```javascript
// ConversationList.jsx
import React, { useEffect, useState } from 'react';
import { useWebSocket } from './hooks/useWebSocket';

function ConversationList() {
  const [conversations, setConversations] = useState([]);
  const token = localStorage.getItem('access_token'); // Get from your auth system

  const handleMessage = (data) => {
    console.log('📨 Received message:', data.type);

    switch (data.type) {
      case 'conversations_list':
        setConversations(data.conversations);
        break;
      case 'conversation_updated':
        // Refresh conversations
        send({ type: 'refresh_conversations' });
        break;
      default:
        console.log('Unknown message type:', data.type);
    }
  };

  const { isConnected, error, send } = useWebSocket(
    'wss://api.pilito.com/ws/conversations/',
    token,
    handleMessage
  );

  // ✅ Handle authentication errors
  useEffect(() => {
    if (error && error.includes('Authentication')) {
      // Redirect to login
      window.location.href = '/login';
    }
  }, [error]);

  return (
    <div>
      {/* Connection Status */}
      {!isConnected && <div>🔄 Connecting...</div>}
      {error && <div className="error">❌ {error}</div>}
      
      {/* Conversations */}
      {conversations.map(conv => (
        <div key={conv.id}>{conv.title}</div>
      ))}
    </div>
  );
}
```

---

## 4️⃣ Multiple WebSocket Prevention

```javascript
// App.jsx
import React, { createContext, useContext, useRef } from 'react';
import WebSocketManager from './websocketManager';

const WebSocketContext = createContext(null);

export function WebSocketProvider({ children, token }) {
  const managersRef = useRef({
    chat: null,
    conversations: null,
    customers: null
  });

  // ✅ Create managers only once
  useEffect(() => {
    if (!token) return;

    // Cleanup old managers
    Object.values(managersRef.current).forEach(manager => {
      if (manager) manager.disconnect();
    });

    // Create new managers
    managersRef.current = {
      chat: new WebSocketManager('wss://api.pilito.com/ws/chat/', token),
      conversations: new WebSocketManager('wss://api.pilito.com/ws/conversations/', token),
      customers: new WebSocketManager('wss://api.pilito.com/ws/customers/', token)
    };

    return () => {
      // Cleanup on unmount
      Object.values(managersRef.current).forEach(manager => {
        if (manager) manager.disconnect();
      });
    };
  }, [token]);

  return (
    <WebSocketContext.Provider value={managersRef.current}>
      {children}
    </WebSocketContext.Provider>
  );
}

// Hook to use WebSocket managers
export function useWebSocketManager(type) {
  const managers = useContext(WebSocketContext);
  return managers[type];
}
```

---

## ✅ Checklist برای Frontend

- [ ] پیاده‌سازی WebSocketManager class
- [ ] اضافه کردن listener برای `connection_established`
- [ ] مدیریت `authentication_error` و redirect به login
- [ ] Prevent multiple connections با check کردن readyState
- [ ] Exponential backoff برای reconnect (2s, 4s, 8s, ...)
- [ ] Max reconnect attempts (5 بار)
- [ ] Cleanup در useEffect return
- [ ] مدیریت visibility change (tab switching)
- [ ] Global WebSocket context برای prevent duplicate
- [ ] Test token expiration scenario
- [ ] Test network disconnection scenario
- [ ] Test tab close/reopen scenario

---

## 🧪 Testing Scenarios

### 1. Token Expiration Test
```javascript
// Manually expire token and check behavior
localStorage.setItem('access_token', 'invalid_token');
// Expected: connection_established نمی‌آید، authentication_error می‌آید، redirect به login
```

### 2. Network Disconnection Test
```javascript
// Open DevTools -> Network -> Offline
// Expected: Reconnect بعد از 2s, 4s, 8s, ...
```

### 3. Tab Close/Reopen Test
```javascript
// Close tab and reopen
// Expected: فقط یک connection برقرار می‌شود
```

### 4. Multiple Tabs Test
```javascript
// Open 3 tabs of the app
// Expected: هر tab یک connection دارد (OK)، نه بیشتر
```

---

## 📊 Success Metrics

✅ **موفقیت‌آمیز:**
- فقط 1 WebSocket connection per tab per endpoint
- connection_established بعد از connect دریافت می‌شود
- Token expiration → No infinite reconnect
- Network error → Controlled reconnect با delay
- Tab close → Connection cleanup

✅ **لاگ‌های مورد انتظار:**
```
🔌 Connecting to WebSocket: ws://...
✅ WebSocket connected: ws://...
✅ Connection established confirmed: ✅ WebSocket connected successfully
📨 Received message: conversations_list
```

❌ **لاگ‌های نامطلوب:**
```
❌ WebSocket already connecting or connected (repeated multiple times)
🔄 Reconnecting... (infinite loop)
❌ Authentication error (without redirect)
```

---

## 🎯 نتیجه‌گیری

با پیاده‌سازی این تغییرات:
1. ✅ Backend پیام `connection_established` می‌فرستد
2. ✅ Token validation درست انجام می‌شود
3. ✅ Frontend reconnect logic کنترل شده است
4. ✅ Multiple connection prevent می‌شود
5. ✅ Cleanup درست انجام می‌شود

**نتیجه:** یک WebSocket connection پایدار، قابل اعتماد و بدون reconnect بی‌پایان! 🎉

