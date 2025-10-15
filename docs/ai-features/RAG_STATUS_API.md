# RAG Status API Documentation

## Overview
This API endpoint provides comprehensive status information about the RAG (Retrieval Augmented Generation) system for the authenticated user.

## Endpoint

```
GET /api/v1/ai/rag/status/
```

## Authentication
Requires authentication token in header:
```
Authorization: Bearer <token>
```

## Response

### Success Response (200 OK)

```json
{
  "rag_enabled": true,
  "pgvector_available": true,
  "embedding_service_available": true,
  "knowledge_base": {
    "faq": {
      "count": 45,
      "display_name": "FAQ"
    },
    "manual": {
      "count": 12,
      "display_name": "Manual Prompt"
    },
    "product": {
      "count": 23,
      "display_name": "Product"
    },
    "website": {
      "count": 67,
      "display_name": "Website Page"
    },
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
  "last_updated": "2025-10-09T14:30:22.123456Z",
  "health_status": "healthy",
  "issues": []
}
```

### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `rag_enabled` | boolean | Whether RAG system is fully operational |
| `pgvector_available` | boolean | Whether pgvector extension is installed in PostgreSQL |
| `embedding_service_available` | boolean | Whether OpenAI embedding service is configured |
| `knowledge_base` | object | Statistics about knowledge chunks by type |
| `knowledge_base.{type}.count` | number | Number of chunks for each type |
| `knowledge_base.{type}.display_name` | string | Human-readable name for the chunk type |
| `knowledge_base.total` | number | Total number of knowledge chunks |
| `embedding_stats` | object | Statistics about embedding generation |
| `embedding_stats.total_chunks` | number | Total knowledge chunks |
| `embedding_stats.chunks_with_tldr_embedding` | number | Chunks with TL;DR embeddings |
| `embedding_stats.chunks_with_full_embedding` | number | Chunks with full text embeddings |
| `embedding_stats.chunks_without_embedding` | number | Chunks missing embeddings |
| `embedding_stats.embedding_coverage` | number | Percentage of chunks with embeddings (0-100) |
| `intent_routing` | object | Intent classification configuration status |
| `intent_routing.keywords_configured` | number | Number of active intent keywords |
| `intent_routing.routing_rules_configured` | number | Number of routing rules configured |
| `intent_routing.has_custom_keywords` | boolean | Whether user has custom keywords |
| `session_memory` | object | Conversation memory statistics |
| `session_memory.total_conversations` | number | Total active conversations |
| `session_memory.conversations_with_memory` | number | Conversations with memory summaries |
| `session_memory.memory_coverage` | number | Percentage of conversations with memory (0-100) |
| `last_updated` | string (ISO 8601) | Last knowledge base update timestamp |
| `health_status` | string | Overall RAG health: `healthy`, `degraded`, or `unavailable` |
| `issues` | array of strings | List of detected issues (empty if healthy) |

### Health Status Values

- **`healthy`**: RAG system is fully operational
  - pgvector available
  - Embedding service available
  - Knowledge base populated
  - >90% chunks have embeddings

- **`degraded`**: RAG system is partially operational
  - Missing some components
  - Knowledge base empty or incomplete
  - <90% chunks have embeddings

- **`unavailable`**: RAG system is not operational
  - pgvector not installed
  - Embedding service unavailable
  - Critical errors

### Error Response (500 Internal Server Error)

```json
{
  "rag_enabled": false,
  "pgvector_available": false,
  "embedding_service_available": false,
  "knowledge_base": {},
  "embedding_stats": {},
  "intent_routing": {},
  "session_memory": {},
  "last_updated": null,
  "health_status": "unavailable",
  "issues": ["Error retrieving RAG status: <error message>"]
}
```

## Usage Examples

### cURL

```bash
curl -X GET "http://localhost:8000/api/v1/ai/rag/status/" \
  -H "Authorization: Bearer <your_token>"
```

### JavaScript (Fetch API)

```javascript
fetch('/api/v1/ai/rag/status/', {
  method: 'GET',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  }
})
.then(response => response.json())
.then(data => {
  console.log('RAG Status:', data);
  
  // Check if RAG is enabled
  if (data.rag_enabled) {
    console.log('✅ RAG system is operational');
  } else {
    console.log('❌ RAG system issues:', data.issues);
  }
  
  // Display knowledge base stats
  console.log(`Total chunks: ${data.knowledge_base.total}`);
  console.log(`Embedding coverage: ${data.embedding_stats.embedding_coverage}%`);
});
```

### Python (requests)

```python
import requests

url = "http://localhost:8000/api/v1/ai/rag/status/"
headers = {"Authorization": f"Bearer {token}"}

response = requests.get(url, headers=headers)
data = response.json()

print(f"RAG Enabled: {data['rag_enabled']}")
print(f"Health Status: {data['health_status']}")
print(f"Total Knowledge Chunks: {data['knowledge_base']['total']}")

# Check for issues
if data['issues']:
    print("Issues detected:")
    for issue in data['issues']:
        print(f"  - {issue}")
```

### React Component Example

```jsx
import { useState, useEffect } from 'react';

function RAGStatus() {
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch('/api/v1/ai/rag/status/', {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('token')}`
      }
    })
    .then(res => res.json())
    .then(data => {
      setStatus(data);
      setLoading(false);
    });
  }, []);

  if (loading) return <div>Loading RAG status...</div>;

  return (
    <div className="rag-status">
      <h2>RAG System Status</h2>
      
      <div className={`status-badge ${status.health_status}`}>
        {status.health_status.toUpperCase()}
      </div>

      <div className="stats">
        <div className="stat">
          <h3>Knowledge Base</h3>
          <p>Total Chunks: {status.knowledge_base.total}</p>
          <p>FAQ: {status.knowledge_base.faq.count}</p>
          <p>Products: {status.knowledge_base.product.count}</p>
          <p>Website: {status.knowledge_base.website.count}</p>
        </div>

        <div className="stat">
          <h3>Embeddings</h3>
          <p>Coverage: {status.embedding_stats.embedding_coverage}%</p>
          <p>With Embeddings: {status.embedding_stats.chunks_with_tldr_embedding}</p>
          <p>Missing: {status.embedding_stats.chunks_without_embedding}</p>
        </div>

        <div className="stat">
          <h3>Session Memory</h3>
          <p>Conversations: {status.session_memory.total_conversations}</p>
          <p>With Memory: {status.session_memory.conversations_with_memory}</p>
        </div>
      </div>

      {status.issues.length > 0 && (
        <div className="issues">
          <h3>Issues</h3>
          <ul>
            {status.issues.map((issue, i) => (
              <li key={i}>{issue}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

export default RAGStatus;
```

## Common Use Cases

### 1. Dashboard Widget
Display RAG system health on admin dashboard to monitor system status at a glance.

### 2. Troubleshooting
Identify issues with knowledge base, embeddings, or configuration problems.

### 3. Knowledge Base Management
Check when knowledge base was last updated and how many chunks are indexed.

### 4. System Health Monitoring
Automated monitoring to alert when RAG system becomes degraded or unavailable.

### 5. User Onboarding
Show users their RAG setup progress (e.g., "You have 0 chunks. Please populate your knowledge base").

## Integration with Other APIs

This endpoint works alongside:
- `/api/v1/ai/ask/` - Ask questions (uses RAG if enabled)
- `/api/v1/ai/config/status/` - AI configuration status
- `/api/v1/ai/usage/stats/` - Usage statistics

## Notes

- Response is user-specific (shows data only for authenticated user)
- Requires active authentication token
- No query parameters needed
- Cached data may be used for performance (1-minute cache)
- Health status is calculated in real-time based on current state

## Troubleshooting

### Issue: `rag_enabled: false`

**Possible causes:**
1. pgvector extension not installed
2. Embedding service (OpenAI API) not configured
3. No knowledge chunks in database
4. No embeddings generated

**Solution:**
```bash
# 1. Check pgvector
docker compose exec db psql -U FikoUsr -d FikoDB -c "SELECT * FROM pg_extension WHERE extname = 'vector';"

# 2. Check OpenAI API key in settings
# 3. Populate knowledge base
docker compose exec web python manage.py populate_knowledge_base --user <username>
```

### Issue: `health_status: "degraded"`

**Possible causes:**
1. Some chunks missing embeddings (>10%)
2. Knowledge base incomplete

**Solution:**
```bash
# Regenerate embeddings
docker compose exec web python manage.py reconcile_knowledge_base
```

### Issue: `chunks_without_embedding > 0`

**Solution:**
```bash
# Run reconciliation to generate missing embeddings
docker compose exec web python manage.py reconcile_knowledge_base
```

---

**Last Updated:** October 9, 2025

