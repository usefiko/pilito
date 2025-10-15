# AI Model Integration Documentation

## Overview

The AI_model app provides automated customer chat functionality using Google's Gemini 1.5 Flash model. It integrates seamlessly with the existing message system to provide real-time AI responses to customer inquiries.

## Features

### 🤖 Core AI Functionality
- **Gemini 1.5 Flash Integration**: Advanced AI model for natural conversation with shared API key
- **Automatic Responses**: AI automatically responds to customer messages
- **Context Awareness**: Maintains conversation history for better responses
- **Customizable Prompts**: Business owners can configure AI behavior
- **Business Hours Support**: Optional restriction to business hours
- **Usage Tracking**: Detailed per-user usage statistics with shared API infrastructure

### 💬 Chat Management
- **Real-time Messaging**: Integration with existing WebSocket system
- **Session Management**: Organized chat sessions per customer
- **Message Threading**: Maintains conversation context
- **Performance Tracking**: Response times and analytics

### ⚙️ Configuration & Control
- **Per-User Settings**: Individual AI configuration for each business
- **API Key Management**: Secure storage of Gemini API keys
- **Auto-Response Toggle**: Enable/disable automatic responses
- **Manual Override**: Support agents can take over conversations

## API Endpoints

### Question & Answer
```
POST /api/v1/ai/ask/
```
Ask a single question and get an AI response.

**Request:**
```json
{
    "question": "What are your business hours?",
    "customer_id": "customer@example.com"
}
```

**Response:**
```json
{
    "session_id": "msg_abc123",
    "customer_id": "customer@example.com", 
    "question": "What are your business hours?",
    "answer": "We're open Monday-Friday 9AM-5PM EST.",
    "response_time_ms": 1250,
    "success": true,
    "auto_response_generated": true
}
```

### Chat Session Management
```
GET /api/v1/ai/sessions/
GET /api/v1/ai/sessions/{session_id}/
POST /api/v1/ai/sessions/{session_id}/send/
```

### AI Configuration
```
GET /api/v1/ai/config/
PUT /api/v1/ai/config/
```

### Analytics
```
GET /api/v1/ai/analytics/
```

### Usage Statistics
```
GET /api/v1/ai/usage/stats/
GET /api/v1/ai/usage/global/
```

### Conversation Status Management
```
GET /api/v1/ai/conversations/{conversation_id}/status/
PUT /api/v1/ai/conversations/{conversation_id}/status/
PUT /api/v1/ai/conversations/bulk-status/
```

### User Default Handler
```
GET /api/v1/ai/default-handler/
PUT /api/v1/ai/default-handler/
```

## Conversation Status Logic

### 🔄 Automatic Status Assignment

**New conversations automatically get their initial status based on the user's `default_reply_handler` setting:**

- **`default_reply_handler = "AI"`** → New conversations get `status = "active"` (AI handles)
- **`default_reply_handler = "Manual"`** → New conversations get `status = "support_active"` (Manual/Support handles)

### ⚙️ Status Validation

The system validates AI configuration before setting status to `"active"`:
- ✅ AI must be enabled (`auto_response_enabled = True`)
- ✅ Global Gemini API key must be configured on server
- ❌ If validation fails → defaults to `"support_active"`

### 📊 Shared API Infrastructure

- **Single API Key**: All users share one Gemini API key configured globally
- **Per-User Tracking**: Individual usage statistics tracked for each user
- **Cost Management**: Centralized API usage with detailed per-user analytics
- **Message Storage**: AI responses stored in existing Message model with `type = 'AI'`

### 🔀 Dynamic Status Switching

Users can switch individual conversations between AI and Manual handling:
- **`"active"`** → AI automatically responds to customer messages
- **`"support_active"`** → Manual/Support team handles messages
- API endpoints provided for real-time status management

## Setup Instructions

### 1. Install Dependencies
```bash
pip install google-generativeai==0.3.2
```

### 2. Environment Variables
Add to your `.env` file:
```env
GEMINI_API_KEY=your_gemini_api_key_here
```

### 3. Database Migration
```bash
python manage.py makemigrations AI_model
python manage.py migrate
```

### 4. Configure User Default Handler
Set user preference in Django admin (Accounts → Users):
- `default_reply_handler = "AI"` for automatic AI responses
- `default_reply_handler = "Manual"` for manual handling

### 5. Configure AI Settings
Access Django admin and configure:
- AI Prompts for each user (Settings app)
- AI Model Config for each user (AI_model app)

### 6. Enable Auto-Response
```bash
# Enable AI for specific user (uses global API key)
python manage.py ai_control enable --user username

# Validate configuration
python manage.py ai_control validate --user username

# Check conversation status distribution
python manage.py ai_control conversations --user username
```

## Management Commands

### Enable/Disable AI
```bash
# Enable for all users
python manage.py ai_control enable

# Enable for specific user (uses global API key)
python manage.py ai_control enable --user username

# Disable for all users  
python manage.py ai_control disable

# Check status
python manage.py ai_control status
```

### Test & Validation
```bash
# Test AI integration
python manage.py ai_control test

# Validate AI configurations
python manage.py ai_control validate

# Test setup with comprehensive checks
python manage.py test_ai_setup
```

### Conversation Management
```bash
# Sync message system conversations to AI chat sessions
python manage.py ai_control sync

# Show conversation status breakdown
python manage.py ai_control conversations

# Show conversations for specific user
python manage.py ai_control conversations --user username
```

## Configuration

### AI Prompts (Settings App)
Configure in Django admin under Settings > AI Prompts:

- **Manual Prompt**: Base instructions for the AI
- **Knowledge Source**: Company information and policies  
- **Product/Service**: Details about offerings
- **Question/Answer**: FAQ for common questions

### AI Model Config (AI_model App)
Configure in Django admin under AI Model > AI Model Configs:

- **Model Name**: Default is "gemini-1.5-flash"
- **Temperature**: Response creativity (0.0-1.0)
- **Max Tokens**: Maximum response length
- **Auto Response Enabled**: Toggle automatic responses
- **Business Hours**: Restrict responses to business hours

### Global API Configuration
Set in Django settings or environment variables:
- **GEMINI_API_KEY**: Single shared Gemini API key for all users

## Automatic Integration

### Message Processing Flow
1. Customer sends message via Telegram/Instagram
2. Signal handler detects new customer message  
3. Celery task processes message asynchronously
4. AI generates response using configured prompts
5. Response sent back through original channel
6. WebSocket notification for real-time updates

### Background Tasks
The system runs several periodic tasks:

- **Cleanup Sessions**: Mark inactive sessions (daily at 2 AM)
- **Generate Analytics**: Daily chat statistics (daily at 1 AM)  
- **Sync Conversations**: Keep AI sessions updated (every 30 min)
- **Test Integration**: Health checks (every 12 hours)

## API Integration Examples

### Basic Question/Answer
```python
import requests

response = requests.post('http://localhost:8000/api/v1/ai/ask/', {
    'question': 'What are your prices?',
    'customer_id': 'test@example.com'
}, headers={'Authorization': 'Bearer your_token'})

print(response.json())
```

### Send Message to Session
```python
response = requests.post(
    'http://localhost:8000/api/v1/ai/sessions/msg_abc123/send/',
    {'message': 'Can you tell me more about your services?'},
    headers={'Authorization': 'Bearer your_token'}
)
```

### Get Chat Analytics  
```python
response = requests.get(
    'http://localhost:8000/api/v1/ai/analytics/',
    headers={'Authorization': 'Bearer your_token'}
)
```

### Get User Usage Statistics
```python
# Get usage stats for last 30 days
response = requests.get(
    'http://localhost:8000/api/v1/ai/usage/stats/',
    headers={'Authorization': 'Bearer your_token'}
)

# Get usage stats for specific period
response = requests.get(
    'http://localhost:8000/api/v1/ai/usage/stats/?days=7',
    headers={'Authorization': 'Bearer your_token'}
)
```

### Get Global Usage Statistics (Admin)
```python
response = requests.get(
    'http://localhost:8000/api/v1/ai/usage/global/',
    headers={'Authorization': 'Bearer your_admin_token'}
)
```

### Manage Conversation Status
```python
# Get conversation status
response = requests.get(
    'http://localhost:8000/api/v1/ai/conversations/abc123/status/',
    headers={'Authorization': 'Bearer your_token'}
)

# Switch conversation to AI handling
response = requests.put(
    'http://localhost:8000/api/v1/ai/conversations/abc123/status/',
    {'status': 'active'},
    headers={'Authorization': 'Bearer your_token'}
)

# Switch conversation to manual handling
response = requests.put(
    'http://localhost:8000/api/v1/ai/conversations/abc123/status/',
    {'status': 'support_active'},
    headers={'Authorization': 'Bearer your_token'}
)

# Bulk update multiple conversations
response = requests.put(
    'http://localhost:8000/api/v1/ai/conversations/bulk-status/',
    {
        'conversation_ids': ['abc123', 'def456', 'ghi789'],
        'status': 'active'
    },
    headers={'Authorization': 'Bearer your_token'}
)
```

### Manage User Default Handler
```python
# Get user's default handler setting
response = requests.get(
    'http://localhost:8000/api/v1/ai/default-handler/',
    headers={'Authorization': 'Bearer your_token'}
)

# Set user's default handler to AI
response = requests.put(
    'http://localhost:8000/api/v1/ai/default-handler/',
    {'default_reply_handler': 'AI'},
    headers={'Authorization': 'Bearer your_token'}
)
```

## Troubleshooting

### Common Issues

**AI Not Responding**
- Check if auto-response is enabled
- Verify global Gemini API key is configured (`GEMINI_API_KEY` environment variable)
- Check business hours settings
- Review Django logs for errors
- Verify conversation status is `"active"`

**Slow Response Times**
- Monitor Celery worker performance
- Check Redis connection
- Verify API rate limits

**Missing Context**
- Ensure conversation history is syncing
- Check session management
- Verify message integration

### Logs and Monitoring
```bash
# Check AI-specific logs
grep "AI" /var/log/django.log

# Monitor Celery tasks
celery -A core inspect active

# Test Redis connection
redis-cli ping
```

## Security Considerations

- Single API key stored securely in environment variables
- Per-user usage tracking prevents abuse
- Rate limiting on API endpoints
- User authentication required
- CORS configuration for WebSocket
- Input validation on all endpoints

## Performance Optimization

- Celery for async processing
- Redis caching for session data
- Database indexing on frequently queried fields
- Connection pooling for external APIs
- Background cleanup tasks

## Extension Points

The AI system is designed to be extensible:

- Custom AI models (replace GeminiChatService)
- Additional messaging channels
- Advanced analytics and reporting
- Multi-language support
- Custom workflow rules

## Support

For issues or questions:
1. Check the Django admin logs
2. Review Celery task status
3. Monitor Redis connectivity
4. Verify API configurations
5. Test with management commands