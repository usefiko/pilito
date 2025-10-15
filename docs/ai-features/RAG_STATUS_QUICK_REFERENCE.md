# RAG Status API - Quick Reference Card

## 🔗 Endpoint
```
GET /api/v1/ai/rag/status/
```

## 🔐 Authentication
```bash
Authorization: Bearer <token>
```

## 📥 Request
No parameters or body required - just GET with auth header

## 📤 Response Keys

| Key | Type | Description |
|-----|------|-------------|
| `rag_enabled` | bool | RAG system operational? |
| `pgvector_available` | bool | pgvector installed? |
| `embedding_service_available` | bool | OpenAI embeddings configured? |
| `knowledge_base` | object | Chunk counts by type + total |
| `embedding_stats` | object | Embedding coverage stats |
| `intent_routing` | object | Intent keywords & routing config |
| `session_memory` | object | Conversation memory stats |
| `last_updated` | datetime | Last KB update (ISO 8601) |
| `health_status` | string | `healthy` / `degraded` / `unavailable` |
| `issues` | array | List of detected problems |

## 🎨 Health Status

| Status | Meaning | Action |
|--------|---------|--------|
| 🟢 `healthy` | All good | None needed |
| 🟡 `degraded` | Partial issues | Check `issues` array |
| 🔴 `unavailable` | Not working | Fix critical errors |

## 🧪 Quick Tests

### cURL
```bash
curl -H "Authorization: Bearer TOKEN" \
  http://localhost:8000/api/v1/ai/rag/status/ | jq
```

### Python
```python
import requests
r = requests.get(URL, headers={'Authorization': f'Bearer {TOKEN}'})
print(r.json()['health_status'])
```

### JavaScript
```javascript
fetch('/api/v1/ai/rag/status/', {
  headers: {'Authorization': `Bearer ${token}`}
})
.then(r => r.json())
.then(d => console.log(d.health_status))
```

## 🔧 Common Issues

| Issue | Solution |
|-------|----------|
| `rag_enabled: false` | Run `populate_knowledge_base` |
| Missing embeddings | Run `reconcile_knowledge_base` |
| pgvector unavailable | Install extension in PostgreSQL |
| 401 Unauthorized | Check Bearer token |

## 📊 Key Metrics to Monitor

```javascript
{
  knowledge_base.total,           // Total chunks
  embedding_stats.embedding_coverage,  // % with embeddings
  session_memory.memory_coverage,      // % conversations with memory
  health_status                        // Overall health
}
```

## 🚀 Frontend Integration

```jsx
// Minimal React example
const { data } = useFetch('/api/v1/ai/rag/status/');

<Badge color={
  data?.health_status === 'healthy' ? 'green' : 
  data?.health_status === 'degraded' ? 'yellow' : 'red'
}>
  RAG: {data?.health_status}
</Badge>
```

## 📝 Files
- 📖 Full docs: `RAG_STATUS_API.md`
- 🧪 Testing: `TEST_RAG_STATUS_API.md`
- 📋 Summary: `RAG_STATUS_API_IMPLEMENTATION.md`
- 🧾 This card: `RAG_STATUS_QUICK_REFERENCE.md`

