# AI Usage Tracking - Quick Start Guide

## 🚀 Quick Integration

### 1. Import the Model
```python
from AI_model.models import AIUsageLog
```

### 2. Log AI Usage (Simple)
```python
AIUsageLog.log_usage(
    user=request.user,
    section='chat',  # See choices below
    prompt_tokens=150,
    completion_tokens=80,
    response_time_ms=1200
)
```

### 3. Log with Full Context
```python
import time

start_time = time.time()

try:
    response = ai_service.generate_response(prompt)
    
    AIUsageLog.log_usage(
        user=request.user,
        section='chat',
        prompt_tokens=response.usage.prompt_tokens,
        completion_tokens=response.usage.completion_tokens,
        response_time_ms=int((time.time() - start_time) * 1000),
        success=True,
        model_name='gemini-1.5-flash',
        metadata={
            'conversation_id': str(conversation.id),
            'message_id': message.id
        }
    )
except Exception as e:
    AIUsageLog.log_usage(
        user=request.user,
        section='chat',
        prompt_tokens=150,
        completion_tokens=0,
        response_time_ms=int((time.time() - start_time) * 1000),
        success=False,
        error_message=str(e)
    )
```

---

## 📋 Section Choices

Use these values for the `section` parameter:

| Code | Display Name |
|------|--------------|
| `chat` | Customer Chat |
| `prompt_generation` | Prompt Generation |
| `marketing_workflow` | Marketing Workflow |
| `knowledge_qa` | Knowledge Base Q&A |
| `product_recommendation` | Product Recommendation |
| `rag_pipeline` | RAG Pipeline |
| `web_knowledge` | Web Knowledge Processing |
| `session_memory` | Session Memory Summary |
| `intent_detection` | Intent Detection |
| `embedding_generation` | Embedding Generation |
| `other` | Other |

---

## 🌐 API Endpoints

All endpoints require authentication via Bearer token.

### Log Usage
```bash
POST /api/v1/ai/usage/logs/
```

### Get Logs (with filters)
```bash
GET /api/v1/ai/usage/logs/?section=chat&start_date=2025-10-01&limit=50
```

### Get Statistics
```bash
GET /api/v1/ai/usage/logs/stats/?days=30
```

### Get Global Stats (Admin only)
```bash
GET /api/v1/ai/usage/logs/global/?days=30
```

---

## 📊 Django Admin

Access the admin interface at:
```
https://api.pilito.com/admin/AI_model/aiusagelog/
```

**Features:**
- ✅ Color-coded sections
- ✅ Success/failure badges
- ✅ Advanced filtering
- ✅ Search by user, section, error
- ✅ Export to CSV/Excel
- ✅ Real-time statistics

---

## 💡 Best Practices

1. **Always log both success and failure**
   ```python
   try:
       # AI call
       AIUsageLog.log_usage(..., success=True)
   except Exception as e:
       AIUsageLog.log_usage(..., success=False, error_message=str(e))
   ```

2. **Include meaningful metadata**
   ```python
   metadata={
       'conversation_id': str(conv_id),
       'customer_name': customer.name,
       'context': 'product_inquiry'
   }
   ```

3. **Use appropriate section names**
   - Choose the most specific section from the SECTION_CHOICES
   - Use `'other'` only when no other category fits

4. **Track response time accurately**
   ```python
   start = time.time()
   # ... AI call ...
   response_time_ms = int((time.time() - start) * 1000)
   ```

---

## 🔍 Query Examples

### Python
```python
from AI_model.models import AIUsageLog
from datetime import datetime, timedelta

# Get user's logs from last 7 days
logs = AIUsageLog.objects.filter(
    user=request.user,
    created_at__gte=datetime.now() - timedelta(days=7)
)

# Get failed requests
failed = AIUsageLog.objects.filter(
    user=request.user,
    success=False
)

# Get total tokens used
from django.db.models import Sum
total_tokens = AIUsageLog.objects.filter(
    user=request.user
).aggregate(Sum('total_tokens'))
```

### API (cURL)
```bash
# Get last 7 days of chat logs
curl "https://api.pilito.com/api/v1/ai/usage/logs/?section=chat&start_date=2025-10-04" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Get statistics
curl "https://api.pilito.com/api/v1/ai/usage/logs/stats/?days=30" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## ⚡ Common Use Cases

### 1. Track Chat AI Usage
```python
def handle_customer_message(conversation, message):
    start = time.time()
    
    try:
        ai_response = gemini_service.generate_response(message.text)
        
        AIUsageLog.log_usage(
            user=conversation.user,
            section='chat',
            prompt_tokens=ai_response.usage.prompt_tokens,
            completion_tokens=ai_response.usage.completion_tokens,
            response_time_ms=int((time.time() - start) * 1000),
            success=True,
            metadata={'conversation_id': str(conversation.id)}
        )
        
        return ai_response
    except Exception as e:
        AIUsageLog.log_usage(
            user=conversation.user,
            section='chat',
            response_time_ms=int((time.time() - start) * 1000),
            success=False,
            error_message=str(e)
        )
        raise
```

### 2. Track RAG Pipeline
```python
def rag_query(user, query):
    start = time.time()
    
    try:
        # Retrieve relevant chunks
        chunks = retrieve_chunks(query)
        
        # Generate response
        response = generate_with_context(query, chunks)
        
        AIUsageLog.log_usage(
            user=user,
            section='rag_pipeline',
            prompt_tokens=response.prompt_tokens,
            completion_tokens=response.completion_tokens,
            response_time_ms=int((time.time() - start) * 1000),
            success=True,
            metadata={
                'chunks_retrieved': len(chunks),
                'query_length': len(query)
            }
        )
        
        return response
    except Exception as e:
        AIUsageLog.log_usage(
            user=user,
            section='rag_pipeline',
            response_time_ms=int((time.time() - start) * 1000),
            success=False,
            error_message=str(e)
        )
        raise
```

### 3. Monitor Usage via API
```python
import requests

def get_my_usage_stats(days=30):
    response = requests.get(
        'https://api.pilito.com/api/v1/ai/usage/logs/stats/',
        params={'days': days},
        headers={'Authorization': f'Bearer {token}'}
    )
    
    stats = response.json()
    
    print(f"Total Requests: {stats['total_requests']}")
    print(f"Total Tokens: {stats['total_tokens']:,}")
    print(f"Success Rate: {stats['success_rate']}%")
    print(f"Avg Response Time: {stats['average_response_time_ms']}ms")
    
    print("\nBy Section:")
    for section, data in stats['by_section'].items():
        print(f"  {data['display_name']}: {data['count']} requests")
    
    return stats
```

---

## 🐛 Troubleshooting

### Issue: Logs not being created
**Check:**
1. User is authenticated
2. Section name is valid (from SECTION_CHOICES)
3. Migration has been run: `python manage.py migrate AI_model`

### Issue: Export not working in admin
**Solution:** Install django-import-export
```bash
pip install django-import-export
```

### Issue: Can't access global stats
**Solution:** Ensure user has staff permissions
```python
request.user.is_staff = True
```

---

## 📖 Full Documentation

For complete documentation, see [AI_USAGE_TRACKING_API.md](./AI_USAGE_TRACKING_API.md)

---

## 🔄 Migration

To apply the database changes:

```bash
cd /path/to/Fiko-Backend
source venv/bin/activate  # Activate virtual environment
python src/manage.py migrate AI_model
```

---

## ✅ Deployment Checklist

- [ ] Run migration: `python src/manage.py migrate AI_model`
- [ ] Test logging in development
- [ ] Test API endpoints
- [ ] Verify admin interface
- [ ] Test export functionality
- [ ] Configure monitoring/alerts
- [ ] Update API documentation
- [ ] Train team on usage

---

**Last Updated:** 2025-10-11  
**Version:** 1.0

