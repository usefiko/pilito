# Testing RAG Status API

## Quick Test Commands

### 1. Using Docker Python Test Script

```bash
# Run the test script inside Docker
docker compose exec web python /app/test_rag_status_api.py
```

### 2. Using cURL (Local Development)

```bash
# First, get your auth token
TOKEN="your_auth_token_here"

# Call the API
curl -X GET "http://localhost:8000/api/v1/ai/rag/status/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" | jq
```

### 3. Using Django Shell

```bash
docker compose exec web python manage.py shell
```

Then in the shell:

```python
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework.authtoken.models import Token

User = get_user_model()
user = User.objects.first()
token, _ = Token.objects.get_or_create(user=user)

client = APIClient()
client.credentials(HTTP_AUTHORIZATION=f'Bearer {token.key}')

response = client.get('/api/v1/ai/rag/status/')
print(f"Status: {response.status_code}")
print(response.json())
```

### 4. Using Python Requests (Outside Docker)

```bash
# Install requests if needed
pip install requests

# Run test
python3 << 'EOF'
import requests

# Replace with your actual token
TOKEN = "your_token_here"
URL = "http://localhost:8000/api/v1/ai/rag/status/"

headers = {"Authorization": f"Bearer {TOKEN}"}
response = requests.get(URL, headers=headers)

print(f"Status Code: {response.status_code}")
print(response.json())
EOF
```

## Expected Response

### Healthy System

```json
{
  "rag_enabled": true,
  "pgvector_available": true,
  "embedding_service_available": true,
  "knowledge_base": {
    "faq": {"count": 45, "display_name": "FAQ"},
    "manual": {"count": 12, "display_name": "Manual Prompt"},
    "product": {"count": 23, "display_name": "Product"},
    "website": {"count": 67, "display_name": "Website Page"},
    "total": 147
  },
  "embedding_stats": {
    "total_chunks": 147,
    "chunks_with_tldr_embedding": 147,
    "chunks_with_full_embedding": 147,
    "chunks_without_embedding": 0,
    "embedding_coverage": 100.0
  },
  "intent_routing": {
    "keywords_configured": 42,
    "routing_rules_configured": 5,
    "has_custom_keywords": false
  },
  "session_memory": {
    "total_conversations": 15,
    "conversations_with_memory": 8,
    "memory_coverage": 53.33
  },
  "last_updated": "2025-10-09T14:30:22Z",
  "health_status": "healthy",
  "issues": []
}
```

### Empty Knowledge Base

```json
{
  "rag_enabled": false,
  "pgvector_available": true,
  "embedding_service_available": true,
  "knowledge_base": {
    "faq": {"count": 0, "display_name": "FAQ"},
    "manual": {"count": 0, "display_name": "Manual Prompt"},
    "product": {"count": 0, "display_name": "Product"},
    "website": {"count": 0, "display_name": "Website Page"},
    "total": 0
  },
  "embedding_stats": {
    "total_chunks": 0,
    "chunks_with_tldr_embedding": 0,
    "chunks_with_full_embedding": 0,
    "chunks_without_embedding": 0,
    "embedding_coverage": 0
  },
  "intent_routing": {
    "keywords_configured": 20,
    "routing_rules_configured": 5,
    "has_custom_keywords": false
  },
  "session_memory": {
    "total_conversations": 0,
    "conversations_with_memory": 0,
    "memory_coverage": 0
  },
  "last_updated": null,
  "health_status": "degraded",
  "issues": [
    "No knowledge base chunks found. Please populate the knowledge base."
  ]
}
```

### System Unavailable

```json
{
  "rag_enabled": false,
  "pgvector_available": false,
  "embedding_service_available": false,
  "knowledge_base": {
    "faq": {"count": 0, "display_name": "FAQ"},
    "manual": {"count": 0, "display_name": "Manual Prompt"},
    "product": {"count": 0, "display_name": "Product"},
    "website": {"count": 0, "display_name": "Website Page"},
    "total": 0
  },
  "embedding_stats": {
    "total_chunks": 0,
    "chunks_with_tldr_embedding": 0,
    "chunks_with_full_embedding": 0,
    "chunks_without_embedding": 0,
    "embedding_coverage": 0
  },
  "intent_routing": {
    "keywords_configured": 0,
    "routing_rules_configured": 0,
    "has_custom_keywords": false
  },
  "session_memory": {
    "total_conversations": 0,
    "conversations_with_memory": 0,
    "memory_coverage": 0
  },
  "last_updated": null,
  "health_status": "unavailable",
  "issues": [
    "RAG system is not fully operational",
    "pgvector extension not installed",
    "Embedding service error: ..."
  ]
}
```

## Troubleshooting

### 401 Unauthorized

```json
{"detail": "Authentication credentials were not provided."}
```

**Solution:** Include valid Bearer token in Authorization header

### 403 Forbidden

```json
{"detail": "You do not have permission to perform this action."}
```

**Solution:** User must be authenticated (IsAuthenticated permission)

### 500 Internal Server Error

Check server logs:
```bash
docker compose logs web --tail 100 | grep "RAG status"
```

## Integration Testing Checklist

- [ ] API returns 200 status code
- [ ] Response includes all required fields
- [ ] `rag_enabled` accurately reflects system state
- [ ] Knowledge base counts match database
- [ ] Embedding stats are accurate
- [ ] Intent routing config is correct
- [ ] Session memory stats are accurate
- [ ] Health status is calculated correctly
- [ ] Issues array contains relevant problems
- [ ] Last updated timestamp is correct

## Performance Notes

- Endpoint should respond in < 500ms
- Database queries are optimized with `.count()`
- No complex joins or aggregations
- Suitable for real-time dashboard polling (every 30-60 seconds)

