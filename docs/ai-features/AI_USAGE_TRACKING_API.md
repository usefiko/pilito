# AI Usage Tracking API - Complete Documentation

## Overview

The **AI Usage Tracking API** provides comprehensive tracking and analytics for all AI interactions across the Fiko platform. This system records every AI request with detailed information including user, section/feature, token consumption, performance metrics, and success status.

### Key Features

✅ **Per-Request Tracking** - Every AI interaction is logged with full details  
✅ **Section/Feature Categorization** - Track which modules use AI  
✅ **Token Consumption Analytics** - Monitor input/output tokens  
✅ **Performance Metrics** - Response time tracking  
✅ **Success/Failure Tracking** - Monitor AI reliability  
✅ **Advanced Filtering** - Filter by date, section, user, success status  
✅ **Export Capabilities** - Export data to CSV, Excel, JSON  
✅ **Django Admin Integration** - Beautiful admin interface with color-coded displays  
✅ **Statistics & Analytics** - Comprehensive usage statistics with breakdowns  

---

## Table of Contents

1. [Model Structure](#model-structure)
2. [API Endpoints](#api-endpoints)
3. [Django Admin Interface](#django-admin-interface)
4. [Usage Examples](#usage-examples)
5. [Integration Guide](#integration-guide)
6. [Database Schema](#database-schema)

---

## Model Structure

### AIUsageLog Model

The core model for tracking AI usage with per-request granularity.

#### Fields

| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID | Unique identifier (auto-generated) |
| `user` | ForeignKey | User who triggered the AI request |
| `section` | CharField | Feature/module that used AI |
| `prompt_tokens` | IntegerField | Number of input tokens |
| `completion_tokens` | IntegerField | Number of output tokens |
| `total_tokens` | IntegerField | Total tokens (prompt + completion) |
| `response_time_ms` | IntegerField | Response time in milliseconds |
| `success` | BooleanField | Whether request was successful |
| `model_name` | CharField | AI model used (e.g., gemini-1.5-flash) |
| `error_message` | TextField | Error details if failed (optional) |
| `metadata` | JSONField | Additional context (conversation_id, etc.) |
| `created_at` | DateTimeField | Timestamp of the request |

#### Section/Feature Choices

```python
SECTION_CHOICES = [
    ('chat', 'Customer Chat'),
    ('prompt_generation', 'Prompt Generation'),
    ('marketing_workflow', 'Marketing Workflow'),
    ('knowledge_qa', 'Knowledge Base Q&A'),
    ('product_recommendation', 'Product Recommendation'),
    ('rag_pipeline', 'RAG Pipeline'),
    ('web_knowledge', 'Web Knowledge Processing'),
    ('session_memory', 'Session Memory Summary'),
    ('intent_detection', 'Intent Detection'),
    ('embedding_generation', 'Embedding Generation'),
    ('other', 'Other'),
]
```

---

## API Endpoints

All endpoints are prefixed with `/api/v1/ai/usage/logs/`

### 1. Log AI Usage (POST)

**Endpoint:** `POST /api/v1/ai/usage/logs/`

**Authentication:** Required

**Description:** Create a new AI usage log entry.

#### Request Body

```json
{
  "section": "chat",
  "prompt_tokens": 150,
  "completion_tokens": 80,
  "response_time_ms": 1200,
  "success": true,
  "model_name": "gemini-1.5-flash",
  "error_message": null,
  "metadata": {
    "conversation_id": "abc-123",
    "message_id": 456
  }
}
```

#### Response (201 Created)

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "user": 1,
  "user_username": "john_doe",
  "user_email": "john@example.com",
  "section": "chat",
  "section_display": "Customer Chat",
  "prompt_tokens": 150,
  "completion_tokens": 80,
  "total_tokens": 230,
  "response_time_ms": 1200,
  "success": true,
  "model_name": "gemini-1.5-flash",
  "error_message": null,
  "metadata": {
    "conversation_id": "abc-123",
    "message_id": 456
  },
  "created_at": "2025-10-11T12:30:45.123456Z"
}
```

---

### 2. Retrieve Usage Logs (GET)

**Endpoint:** `GET /api/v1/ai/usage/logs/`

**Authentication:** Required

**Description:** Retrieve AI usage logs with optional filtering and pagination.

#### Query Parameters

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `section` | string | Filter by section/feature | `?section=chat` |
| `start_date` | date | Start date (YYYY-MM-DD) | `?start_date=2025-10-01` |
| `end_date` | date | End date (YYYY-MM-DD) | `?end_date=2025-10-11` |
| `success` | boolean | Filter by success status | `?success=true` |
| `limit` | integer | Records per page (max 500) | `?limit=50` |
| `offset` | integer | Pagination offset | `?offset=0` |

#### Example Request

```bash
GET /api/v1/ai/usage/logs/?section=chat&start_date=2025-10-01&limit=10
```

#### Response (200 OK)

```json
{
  "count": 150,
  "next": "?limit=10&offset=10&section=chat",
  "previous": null,
  "results": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "user": 1,
      "user_username": "john_doe",
      "user_email": "john@example.com",
      "section": "chat",
      "section_display": "Customer Chat",
      "prompt_tokens": 150,
      "completion_tokens": 80,
      "total_tokens": 230,
      "response_time_ms": 1200,
      "success": true,
      "model_name": "gemini-1.5-flash",
      "error_message": null,
      "metadata": {},
      "created_at": "2025-10-11T12:30:45.123456Z"
    }
    // ... more logs
  ]
}
```

---

### 3. Get Usage Statistics (GET)

**Endpoint:** `GET /api/v1/ai/usage/logs/stats/`

**Authentication:** Required

**Description:** Get comprehensive usage statistics with section breakdown and daily trends.

#### Query Parameters

| Parameter | Type | Description | Default |
|-----------|------|-------------|---------|
| `days` | integer | Number of days to include | 30 |
| `section` | string | Filter by specific section | (all) |

#### Example Request

```bash
GET /api/v1/ai/usage/logs/stats/?days=7
```

#### Response (200 OK)

```json
{
  "total_requests": 1250,
  "total_tokens": 345000,
  "total_prompt_tokens": 185000,
  "total_completion_tokens": 160000,
  "successful_requests": 1200,
  "failed_requests": 50,
  "success_rate": 96.0,
  "average_response_time_ms": 1350.5,
  "average_tokens_per_request": 276.0,
  "days_included": 7,
  "date_range": {
    "start": "2025-10-04",
    "end": "2025-10-11"
  },
  "by_section": {
    "chat": {
      "display_name": "Customer Chat",
      "count": 800,
      "total_tokens": 220000,
      "avg_response_time_ms": 1200.5,
      "percentage": 64.0
    },
    "rag_pipeline": {
      "display_name": "RAG Pipeline",
      "count": 300,
      "total_tokens": 90000,
      "avg_response_time_ms": 1800.2,
      "percentage": 24.0
    },
    "prompt_generation": {
      "display_name": "Prompt Generation",
      "count": 150,
      "total_tokens": 35000,
      "avg_response_time_ms": 900.8,
      "percentage": 12.0
    }
  },
  "daily_breakdown": [
    {
      "date": "2025-10-04",
      "requests": 150,
      "tokens": 42000,
      "successful_requests": 145,
      "failed_requests": 5
    }
    // ... more days
  ],
  "recent_logs": [
    // Last 10 logs
  ]
}
```

---

### 4. Global Usage Statistics (Admin Only)

**Endpoint:** `GET /api/v1/ai/usage/logs/global/`

**Authentication:** Required (Staff only)

**Description:** Get system-wide AI usage statistics across all users.

#### Query Parameters

| Parameter | Type | Description | Default |
|-----------|------|-------------|---------|
| `days` | integer | Number of days to include | 30 |

#### Response (200 OK)

```json
{
  "total_users": 45,
  "total_requests": 15000,
  "total_tokens": 4200000,
  "total_prompt_tokens": 2250000,
  "total_completion_tokens": 1950000,
  "successful_requests": 14500,
  "failed_requests": 500,
  "success_rate": 96.67,
  "average_response_time_ms": 1425.3,
  "days_included": 30,
  "date_range": {
    "start": "2025-09-11",
    "end": "2025-10-11"
  },
  "by_section": {
    "chat": {
      "display_name": "Customer Chat",
      "count": 9500,
      "total_tokens": 2600000,
      "percentage": 63.33
    }
    // ... more sections
  },
  "top_users": [
    {
      "user__username": "john_doe",
      "user__email": "john@example.com",
      "user_total_requests": 850,
      "user_total_tokens": 235000
    }
    // ... top 10 users
  ]
}
```

---

## Django Admin Interface

The Django Admin interface provides a powerful, visual way to view and manage AI usage logs.

### Features

#### 🎨 Color-Coded Display
- **Sections** are color-coded for easy identification
- **Success/Failure** badges with green (✓ Success) and red (✗ Failed)
- **Response times** are color-coded:
  - Green: < 1000ms (fast)
  - Orange: 1000-3000ms (moderate)
  - Red: > 3000ms (slow)

#### 🔍 Advanced Filtering
- Filter by success status
- Filter by section/feature
- Filter by model name
- Filter by date range
- Filter by user

#### 🔎 Search Functionality
Search by:
- Username
- Email
- Section name
- Model name
- Error message
- Record ID

#### 📊 Export Capabilities
Export data in multiple formats:
- CSV
- Excel (XLSX)
- JSON
- TSV

#### 📈 Summary Statistics
The admin interface displays real-time statistics:
- Total requests in current filter
- Total tokens consumed
- Successful vs failed requests

### Access

Navigate to: `https://api.pilito.com/admin/AI_model/aiusagelog/`

---

## Usage Examples

### Example 1: Log a Chat AI Request

```python
from AI_model.models import AIUsageLog

# Log AI usage for a chat response
log = AIUsageLog.log_usage(
    user=request.user,
    section='chat',
    prompt_tokens=150,
    completion_tokens=80,
    response_time_ms=1200,
    success=True,
    model_name='gemini-1.5-flash',
    metadata={
        'conversation_id': conversation.id,
        'message_id': message.id,
        'customer_name': conversation.customer.name
    }
)
```

### Example 2: Log a Failed Request

```python
try:
    # AI request logic
    response = ai_service.generate_response(prompt)
except Exception as e:
    # Log the failure
    AIUsageLog.log_usage(
        user=request.user,
        section='rag_pipeline',
        prompt_tokens=200,
        completion_tokens=0,
        response_time_ms=5000,
        success=False,
        error_message=str(e),
        metadata={'error_type': type(e).__name__}
    )
```

### Example 3: Retrieve User's Usage via API

```python
import requests

# Get last 7 days of chat logs
response = requests.get(
    'https://api.pilito.com/api/v1/ai/usage/logs/',
    params={
        'section': 'chat',
        'start_date': '2025-10-04',
        'end_date': '2025-10-11',
        'limit': 50
    },
    headers={'Authorization': f'Bearer {access_token}'}
)

logs = response.json()['results']
```

### Example 4: Get Statistics for Specific Section

```python
import requests

# Get statistics for prompt generation
response = requests.get(
    'https://api.pilito.com/api/v1/ai/usage/logs/stats/',
    params={
        'days': 30,
        'section': 'prompt_generation'
    },
    headers={'Authorization': f'Bearer {access_token}'}
)

stats = response.json()
print(f"Total requests: {stats['total_requests']}")
print(f"Total tokens: {stats['total_tokens']}")
print(f"Success rate: {stats['success_rate']}%")
```

---

## Integration Guide

### Step 1: Import the Model

```python
from AI_model.models import AIUsageLog
```

### Step 2: Log AI Usage

Whenever you make an AI request, log it:

```python
import time

start_time = time.time()

try:
    # Make AI request
    response = ai_service.generate_response(prompt)
    
    # Calculate metrics
    response_time_ms = int((time.time() - start_time) * 1000)
    
    # Log successful usage
    AIUsageLog.log_usage(
        user=user,
        section='your_section_name',  # Choose from SECTION_CHOICES
        prompt_tokens=response.usage.prompt_tokens,
        completion_tokens=response.usage.completion_tokens,
        response_time_ms=response_time_ms,
        success=True,
        model_name='gemini-1.5-flash',
        metadata={'any': 'additional', 'context': 'here'}
    )
    
except Exception as e:
    # Log failed usage
    response_time_ms = int((time.time() - start_time) * 1000)
    
    AIUsageLog.log_usage(
        user=user,
        section='your_section_name',
        prompt_tokens=estimated_prompt_tokens,  # Estimate if possible
        completion_tokens=0,
        response_time_ms=response_time_ms,
        success=False,
        error_message=str(e),
        metadata={'error_type': type(e).__name__}
    )
```

### Step 3: Best Practices

1. **Always log usage** - Even failed requests should be logged
2. **Use appropriate sections** - Choose the most specific section from SECTION_CHOICES
3. **Include metadata** - Add context that will help with debugging and analytics
4. **Handle errors gracefully** - Logging should never cause the main flow to fail
5. **Monitor regularly** - Use the statistics API to track usage trends

---

## Database Schema

### Table: `ai_usage_log`

```sql
CREATE TABLE ai_usage_log (
    id UUID PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES accounts_user(id),
    section VARCHAR(50) NOT NULL,
    prompt_tokens INTEGER NOT NULL DEFAULT 0,
    completion_tokens INTEGER NOT NULL DEFAULT 0,
    total_tokens INTEGER NOT NULL DEFAULT 0,
    response_time_ms INTEGER NOT NULL DEFAULT 0,
    success BOOLEAN NOT NULL DEFAULT TRUE,
    model_name VARCHAR(100) NOT NULL DEFAULT 'gemini-1.5-flash',
    error_message TEXT NULL,
    metadata JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE NOT NULL
);

-- Indexes for performance
CREATE INDEX ai_usage_l_user_id_2a5e9d_idx ON ai_usage_log(user_id, section, created_at);
CREATE INDEX ai_usage_l_user_id_f7c8a2_idx ON ai_usage_log(user_id, created_at);
CREATE INDEX ai_usage_l_section_8d3b1f_idx ON ai_usage_log(section, created_at);
CREATE INDEX ai_usage_l_created_2c4e5a_idx ON ai_usage_log(created_at);
CREATE INDEX ai_usage_l_success_9f6d3b_idx ON ai_usage_log(success);
```

---

## API Testing

### Using cURL

```bash
# Log AI usage
curl -X POST https://api.pilito.com/api/v1/ai/usage/logs/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "section": "chat",
    "prompt_tokens": 150,
    "completion_tokens": 80,
    "response_time_ms": 1200,
    "success": true
  }'

# Get usage logs
curl -X GET "https://api.pilito.com/api/v1/ai/usage/logs/?section=chat&limit=10" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Get statistics
curl -X GET "https://api.pilito.com/api/v1/ai/usage/logs/stats/?days=7" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Using Python Requests

```python
import requests

BASE_URL = 'https://api.pilito.com/api/v1/ai/usage/logs/'
HEADERS = {'Authorization': f'Bearer {YOUR_TOKEN}'}

# Log usage
response = requests.post(
    BASE_URL,
    headers=HEADERS,
    json={
        'section': 'chat',
        'prompt_tokens': 150,
        'completion_tokens': 80,
        'response_time_ms': 1200,
        'success': True
    }
)

# Get logs
response = requests.get(
    BASE_URL,
    headers=HEADERS,
    params={'section': 'chat', 'limit': 10}
)

# Get stats
response = requests.get(
    f'{BASE_URL}stats/',
    headers=HEADERS,
    params={'days': 7}
)
```

---

## Deployment Checklist

- [x] Model created with all necessary fields
- [x] Migration file created
- [x] API views implemented with proper authentication
- [x] URL routes configured
- [x] Django Admin interface configured with export
- [x] Serializers created for request/response
- [x] Documentation completed
- [ ] Run migrations: `python manage.py migrate AI_model`
- [ ] Test API endpoints
- [ ] Configure permissions
- [ ] Set up monitoring alerts

---

## Support & Troubleshooting

### Common Issues

**Issue:** Logs not appearing in admin
- **Solution:** Check that the user has proper permissions and the migration has been run

**Issue:** Export not working
- **Solution:** Ensure `django-import-export` is installed: `pip install django-import-export`

**Issue:** Statistics showing incorrect data
- **Solution:** Check date range filters and ensure logs are being created with correct timestamps

### Contact

For technical support or questions, contact the development team or refer to the main project documentation.

---

## Version History

- **v1.0** (2025-10-11) - Initial implementation
  - Per-request tracking
  - Django Admin with export
  - Statistics API
  - Comprehensive filtering

---

## License

This API is part of the Fiko Backend system. All rights reserved.

