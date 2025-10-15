# ⚠️ CRITICAL: Embedding Dimensions Fix

## مشکل:
- OpenAI `text-embedding-3-large` → 3072 dimensions
- PostgreSQL 15 با ivfflat → **MAX 2000 dimensions**
- نمی‌تونیم vector index بسازیم!

## راه حل:
استفاده از `text-embedding-3-small` → **1536 dimensions** ✅

---

## تغییرات لازم:

### 1. **models.py** (فاز 2)
```python
# ❌ قبلی (3072):
tldr_embedding = VectorField(dimensions=3072)

# ✅ جدید (1536):
tldr_embedding = VectorField(dimensions=1536)
```

### 2. **EmbeddingService** (فاز 2)
```python
# ❌ قبلی:
response = self.openai_client.embeddings.create(
    model="text-embedding-3-large",  # 3072 dims
    input=text_truncated
)

# ✅ جدید:
response = self.openai_client.embeddings.create(
    model="text-embedding-3-small",  # 1536 dims
    input=text_truncated
)
```

### 3. **Vector Index** (بعد از تغییرات)
```sql
-- این رو بعد از migration جدید می‌زنیم:
CREATE INDEX idx_tenant_knowledge_tldr_embedding 
ON tenant_knowledge 
USING ivfflat (tldr_embedding vector_cosine_ops) 
WITH (lists = 100);
```

---

## مزایای text-embedding-3-small:
- ✅ 1536 dimensions (compatible با ivfflat)
- ✅ سریع‌تر
- ✅ ارزان‌تر ($0.00002 vs $0.00013 per 1K tokens)
- ✅ کیفیت خوب برای RAG

---

## TODO در فاز 2:
- [ ] تغییر dimensions در models.py
- [ ] تغییر model در EmbeddingService
- [ ] ساخت migration جدید
- [ ] اجرای migration
- [ ] ساخت vector index
- [ ] تست

**این رو حتماً انجام می‌دیم! ✅**

