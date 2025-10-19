# WebSocket System Documentation

## نمای کلی سیستم

این سیستم WebSocket یک پلتفرم چت آنلاین حرفه‌ای مشابه Intercom یا Crisp ارائه می‌دهد که امکان ارتباط realtime بین کاربران و مشتریان را فراهم می‌کند.

## ویژگی‌های کلیدی

### 🔥 امکانات اصلی
- **Realtime Messaging**: ارسال و دریافت پیام‌ها به صورت آنی
- **Multi-Platform Support**: پشتیبانی از تلگرام و اینستاگرام
- **User Isolation**: هر کاربر فقط داده‌های خود را می‌بیند
- **Auto External Sending**: ارسال خودکار پیام‌ها به تلگرام/اینستاگرام
- **Typing Indicators**: نمایش وضعیت تایپ کردن
- **Read Receipts**: علامت خوانده شدن پیام‌ها
- **User Presence**: نمایش وضعیت آنلاین/آفلاین
- **Security Features**: امنیت پیشرفته و محافظت در برابر حملات

### 🛡️ امنیت
- **JWT Authentication**: احراز هویت امن با توکن JWT
- **Rate Limiting**: محدودیت تعداد پیام و اتصال
- **IP Blacklisting**: مسدود کردن IP های مشکوک
- **Spam Detection**: تشخیص خودکار اسپم
- **Content Validation**: اعتبارسنجی محتوای پیام‌ها

## ساختار WebSocket URLs

### 1. Chat Room Connection
```
ws://domain.com/ws/chat/{conversation_id}/?token=JWT_TOKEN
```

### 2. Conversation List Connection  
```
ws://domain.com/ws/conversations/?token=JWT_TOKEN
```

## نحوه اتصال از Frontend

### JavaScript Example
```javascript
// اتصال به یک مکالمه خاص
const chatSocket = new WebSocket(
    'ws://localhost:8000/ws/chat/ABC123/?token=' + jwtToken
);

// اتصال به لیست مکالمات
const conversationsSocket = new WebSocket(
    'ws://localhost:8000/ws/conversations/?token=' + jwtToken
);

// Handle chat messages
chatSocket.onmessage = function(e) {
    const data = JSON.parse(e.data);
    
    switch(data.type) {
        case 'chat_message':
            displayMessage(data.message);
            showExternalSendStatus(data.external_send_result);
            break;
        case 'typing_indicator':
            showTypingIndicator(data);
            break;
        case 'user_presence':
            updateUserPresence(data);
            break;
        case 'recent_messages':
            loadRecentMessages(data.messages);
            break;
    }
};

// ارسال پیام
function sendMessage(content) {
    chatSocket.send(JSON.stringify({
        'type': 'chat_message',
        'content': content
    }));
}

// نمایش حالت تایپ
function sendTypingIndicator(isTyping) {
    chatSocket.send(JSON.stringify({
        'type': 'typing',
        'is_typing': isTyping
    }));
}
```

## پیام‌های WebSocket

### ورودی (از Client به Server)

#### 1. ارسال پیام
```json
{
    "type": "chat_message",
    "content": "متن پیام"
}
```

#### 2. نمایش تایپ کردن
```json
{
    "type": "typing",
    "is_typing": true
}
```

#### 3. علامت خواندن
```json
{
    "type": "mark_read"
}
```

### خروجی (از Server به Client)

#### 1. پیام جدید
```json
{
    "type": "chat_message",
    "message": {
        "id": "MSG123",
        "content": "متن پیام",
        "type": "support",
        "customer": {
            "id": 1,
            "first_name": "علی",
            "source": "telegram"
        },
        "created_at": "2023-12-01T10:30:00Z"
    },
    "external_send_result": {
        "success": true,
        "message_id": "telegram_msg_123"
    }
}
```

#### 2. حالت تایپ
```json
{
    "type": "typing_indicator",
    "user_id": 123,
    "username": "احمد محمدی",
    "is_typing": true,
    "timestamp": "2023-12-01T10:30:00Z"
}
```

#### 3. حضور کاربر
```json
{
    "type": "user_presence",
    "user_id": 123,
    "username": "احمد محمدی", 
    "is_online": true,
    "timestamp": "2023-12-01T10:30:00Z"
}
```

#### 4. پیام‌های اخیر
```json
{
    "type": "recent_messages",
    "messages": [...],
    "timestamp": "2023-12-01T10:30:00Z"
}
```

## REST API Endpoints

### 1. ارسال پیام
```http
POST /api/v1/message/conversation/{conversation_id}/send-message/
Authorization: Bearer JWT_TOKEN
Content-Type: application/json

{
    "content": "متن پیام",
    "type": "support"
}
```

### 2. تغییر وضعیت مکالمه
```http
PATCH /api/v1/message/conversation/{conversation_id}/status/
Authorization: Bearer JWT_TOKEN
Content-Type: application/json

{
    "status": "support_active"
}
```

## تنظیمات امنیتی

### در فایل settings.py:
```python
# WebSocket Security Settings
WEBSOCKET_SECURITY = {
    'MAX_MESSAGES_PER_MINUTE': 20,
    'MAX_CONNECTIONS_PER_USER': 5,
    'MAX_FAILED_AUTH_ATTEMPTS': 5,
    'BLACKLIST_DURATION_HOURS': 24,
    'ENABLE_SPAM_DETECTION': True,
    'ENABLE_RATE_LIMITING': True,
}

# Channel Layer Configuration
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            "hosts": [('127.0.0.1', 6379)],
        },
    },
}
```

## مراحل راه‌اندازی

### 1. تنظیم Redis
```bash
# نصب Redis
sudo apt-get install redis-server

# یا با Docker
docker run -d -p 6379:6379 redis:latest
```

### 2. تنظیم Django Channels
```bash
pip install channels channels-redis
```

### 3. اعمال Migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

### 4. راه‌اندازی سرور
```bash
# راه‌اندازی Django با پشتیبانی WebSocket
python manage.py runserver
```

## مثال Frontend کامل

```html
<!DOCTYPE html>
<html>
<head>
    <title>Chat System</title>
</head>
<body>
    <div id="chat-messages"></div>
    <input type="text" id="message-input" placeholder="پیام خود را بنویسید...">
    <button onclick="sendMessage()">ارسال</button>
    
    <script>
        const conversationId = 'ABC123';
        const jwtToken = 'your_jwt_token_here';
        
        const chatSocket = new WebSocket(
            `ws://localhost:8000/ws/chat/${conversationId}/?token=${jwtToken}`
        );
        
        chatSocket.onmessage = function(e) {
            const data = JSON.parse(e.data);
            
            if (data.type === 'chat_message') {
                addMessageToChat(data.message);
                
                if (data.external_send_result) {
                    showSendStatus(data.external_send_result);
                }
            }
        };
        
        function sendMessage() {
            const messageInput = document.getElementById('message-input');
            const message = messageInput.value.trim();
            
            if (message) {
                chatSocket.send(JSON.stringify({
                    'type': 'chat_message',
                    'content': message
                }));
                
                messageInput.value = '';
            }
        }
        
        function addMessageToChat(message) {
            const chatMessages = document.getElementById('chat-messages');
            const messageElement = document.createElement('div');
            messageElement.innerHTML = `
                <strong>${message.customer.first_name}:</strong> 
                ${message.content}
                <small>(${new Date(message.created_at).toLocaleString()})</small>
            `;
            chatMessages.appendChild(messageElement);
            chatMessages.scrollTop = chatMessages.scrollHeight;
        }
        
        function showSendStatus(result) {
            if (result.success) {
                console.log('پیام با موفقیت ارسال شد');
            } else {
                console.error('خطا در ارسال پیام:', result.error);
            }
        }
    </script>
</body>
</html>
```

## مشکلات رایج و راه‌حل

### 1. خطای اتصال WebSocket
**مشکل**: WebSocket connection failed
**راه‌حل**: 
- بررسی کنید Redis در حال اجرا باشد
- توکن JWT معتبر باشد
- URL صحیح باشد

### 2. پیام‌ها ارسال نمی‌شوند
**مشکل**: پیام‌ها در دیتابیس ذخیره نمی‌شوند
**راه‌حل**:
- دسترسی کاربر به مکالمه را بررسی کنید
- محدودیت rate limiting بررسی شود

### 3. ارسال به تلگرام/اینستاگرام کار نمی‌کند
**مشکل**: پیام‌ها به پلتفرم خارجی ارسال نمی‌شوند
**راه‌حل**:
- تنظیمات bot token تلگرام
- access token اینستاگرام معتبر باشد
- اتصال اینترنت سرور

## مانیتورینگ و نظارت

### دیدن آمار امنیتی:
```python
from message.security import WebSocketSecurityManager, WebSocketMonitor

# آمار کاربر
stats = WebSocketSecurityManager.get_user_websocket_stats(user_id)
print(stats)

# خلاصه امنیتی
summary = WebSocketMonitor.get_security_summary(hours=24)
print(summary)

# گزارش فعالیت کاربر
report = WebSocketMonitor.get_user_activity_report(user_id)
print(report)
```

## نکات عملکرد

1. **Cache**: استفاده از Redis برای بهبود عملکرد
2. **Database Optimization**: ایندکس مناسب روی فیلدهای مورد استفاده
3. **Connection Pooling**: مدیریت اتصالات پایگاه داده
4. **Monitoring**: نظارت مداوم بر عملکرد سیستم

## پشتیبانی

برای مشکلات فنی یا سوالات، لطفاً با تیم توسعه تماس بگیرید. 