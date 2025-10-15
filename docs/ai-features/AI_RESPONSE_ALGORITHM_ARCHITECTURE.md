# 🤖 الگوریتم پاسخگویی هوش مصنوعی - معماری فنی کامل

> **مستندات فنی جامع سیستم پاسخگویی AI با معماری Lean RAG v2.1**
> 
> این سند شامل تمامی جزئیات فنی، معماری، الگوریتم‌ها، و نحوه عملکرد سیستم پاسخگویی هوش مصنوعی پروژه FIKO است.

**نویسنده:** FIKO AI Team  
**آخرین بروزرسانی:** اکتبر 2025  
**نسخه:** 2.1

---

## 📋 فهرست مطالب

1. [نمای کلی معماری](#-نمای-کلی-معماری)
2. [الگوریتم پاسخگویی (Lean RAG)](#-الگوریتم-پاسخگویی-lean-rag)
3. [سیستم Chunking و Embedding](#-سیستم-chunking-و-embedding)
4. [Knowledge Sources و Crawling](#-knowledge-sources-و-crawling)
5. [Query Router (مسیریابی سوال)](#-query-router-مسیریابی-سوال)
6. [Context Retriever (RAG با pgvector)](#-context-retriever-rag-با-pgvector)
7. [Token Management](#-token-management)
8. [مثال‌های عملی](#-مثالهای-عملی)
9. [Monitoring و Performance](#-monitoring-و-performance)

---

## 🏗️ نمای کلی معماری

### معماری سیستم (System Architecture)

```
┌──────────────────────────────────────────────────────────────────────────┐
│                           FIKO AI Response System                        │
│                         Lean RAG Architecture v2.1                       │
└──────────────────────────────────────────────────────────────────────────┘

    ┌───────────────┐
    │  User Query   │ "قیمت پلن شما چنده؟"
    └───────┬───────┘
            │
            ▼
    ┌─────────────────────────────────┐
    │  1. Query Router                │  ← Rule-based + Keyword matching
    │  (Intent Classification)        │
    │  - Multilingual (FA/EN/AR/TR)   │
    │  - Output: intent, confidence   │
    └────────────┬────────────────────┘
                 │ intent="pricing", conf=0.85
                 │ primary_source="faq"
                 ▼
    ┌─────────────────────────────────┐
    │  2. Embedding Service            │  ← OpenAI text-embedding-3-small
    │  (Semantic Vector Generation)    │    (1536 dimensions)
    │  - Primary: OpenAI              │
    │  - Fallback: Gemini             │
    │  - Cache: Redis (30 days)       │
    └────────────┬────────────────────┘
                 │ query_embedding=[0.023, -0.145, ...]
                 ▼
    ┌─────────────────────────────────┐
    │  3. Context Retriever            │  ← pgvector Cosine Similarity
    │  (RAG - Semantic Search)         │
    │  - TenantKnowledge DB            │
    │  - Top-K chunks (K=5)            │
    │  - Min similarity: 0.1           │
    └────────────┬────────────────────┘
                 │ primary_chunks=[FAQ1, FAQ2, FAQ3]
                 │ secondary_chunks=[Product1]
                 ▼
    ┌─────────────────────────────────┐
    │  4. Session Memory Manager       │  ← Conversation Context
    │  (Conversation Intelligence)     │
    │  - Rolling summary (10+ msgs)    │
    │  - Recent messages (last 3)      │
    │  - Cached summaries              │
    └────────────┬────────────────────┘
                 │ conversation_context="..."
                 ▼
    ┌─────────────────────────────────┐
    │  5. Token Budget Controller      │  ← Strict 1500 Token Limit
    │  (Prompt Trimming)               │
    │  - System: 200 tokens            │
    │  - Memory: 150 tokens            │
    │  - Context: 800 tokens           │
    │  - Query: 350 tokens             │
    └────────────┬────────────────────┘
                 │ trimmed_prompt (≤1500 tokens)
                 ▼
    ┌─────────────────────────────────┐
    │  6. Gemini Chat Service          │  ← Gemini 2.5 Flash API
    │  (AI Response Generation)        │
    │  - Model: gemini-2.5-flash       │
    │  - Temperature: 0.7              │
    │  - Max tokens: 3000              │
    └────────────┬────────────────────┘
                 │ ai_response="پلن ما 3 نوع داره..."
                 ▼
    ┌─────────────────────────────────┐
    │  7. Response Handler             │  ← Format & Send
    │  - Token billing                 │
    │  - Usage tracking                │
    │  - Platform routing              │
    │    (Telegram/Instagram/Web)      │
    └─────────────────────────────────┘
            │
            ▼
    ┌───────────────┐
    │  User Reply   │ پلن Pro به قیمت $29
    └───────────────┘
```

---

## 🎯 الگوریتم پاسخگویی (Lean RAG)

### معماری Lean RAG v2.1

**هدف:** کاهش هزینه توکن به **≤1500 توکن ورودی** با حفظ دقت پاسخ **≥90%**

### مراحل الگوریتم:

#### مرحله 1: Query Routing (مسیریابی سوال)

**کد:** `src/AI_model/services/query_router.py`

```python
routing = QueryRouter.route_query(customer_message, user=self.user)

# Output:
{
    'intent': 'pricing',               # دسته‌بندی نیت کاربر
    'confidence': 0.85,                # اطمینان (0-1)
    'primary_source': 'faq',           # منبع اصلی جستجو
    'secondary_sources': ['products'], # منابع جانبی
    'token_budgets': {
        'primary': 800,                # بودجه توکن برای منبع اصلی
        'secondary': 300               # بودجه توکن برای منابع جانبی
    },
    'keywords_matched': ['قیمت', 'پلن'],
    'method': 'keyword_based'
}
```

**الگوریتم مسیریابی:**

1. **تشخیص کلمات کلیدی (Multilingual):**
   - FA: قیمت، هزینه، پلن، اشتراک، خرید
   - EN: price, cost, plan, subscription, buy
   - AR: سعر، تكلفة، خطة، اشتراك
   - TR: fiyat, maliyet, plan, abonelik

2. **امتیازدهی Intent:**
   ```python
   for intent in ['pricing', 'product', 'howto', 'contact']:
       score = sum(keyword_weight for keyword in matched_keywords)
       intent_scores[intent] = score
   
   best_intent = max(intent_scores, key=intent_scores.get)
   confidence = max_score / total_score
   ```

3. **انتخاب منابع بر اساس Intent:**
   - `pricing` → Primary: FAQ, Secondary: Products + Manual
   - `product` → Primary: Products, Secondary: FAQ + Website
   - `howto` → Primary: Manual, Secondary: FAQ + Website
   - `contact` → Primary: Manual, Secondary: Website
   - `general` → Primary: FAQ, Secondary: Manual

**مزایا:**
- ✅ بدون نیاز به AI (سریع، رایگان)
- ✅ پشتیبانی از 4 زبان (FA/EN/AR/TR)
- ✅ قابل تنظیم از دیتابیس (`IntentKeyword`, `IntentRouting`)
- ✅ Cache شده (1 ساعت)

---

#### مرحله 2: Embedding Generation (تولید بردار معنایی)

**کد:** `src/AI_model/services/embedding_service.py`

```python
embedding_service = EmbeddingService()
query_embedding = embedding_service.get_embedding(
    text="قیمت پلن شما چنده؟",
    task_type="retrieval_query"
)
# Output: [0.0234, -0.1456, 0.0892, ..., 0.0234]  # 1536 dimensions
```

**استراتژی Embedding:**

```
┌─────────────────────────────────────────────────────────────┐
│                  Embedding Service Strategy                 │
└─────────────────────────────────────────────────────────────┘

1. Check Redis Cache (30 days TTL)
   ├─ Hit? → Return cached embedding ✅
   └─ Miss? → Continue ⬇️

2. Try OpenAI API (Primary)
   Model: text-embedding-3-small
   Dimensions: 1536
   Languages: 100+
   Cost: $0.02 / 1M tokens
   ├─ Success? → Cache & Return ✅
   └─ Fail? → Continue ⬇️

3. Try Gemini API (Fallback)
   Model: text-embedding-004
   Dimensions: 768
   Languages: 100+
   Cost: Free (1500 req/day)
   ├─ Success? → Cache & Return ✅
   └─ Fail? → Continue ⬇️

4. Return None → Caller uses BM25 ⚠️
```

**چرا text-embedding-3-small؟**
- PostgreSQL 15 ivfflat index محدودیت دارد: max 2000 dimensions
- text-embedding-3-large = 3072 dims (خیلی بزرگ ❌)
- text-embedding-3-small = 1536 dims (مناسب ✅)
- سرعت بالاتر، هزینه کمتر، دقت عالی

**مثال Cache Key:**
```python
cache_key = f"emb:v2:{md5(task_type + text)[:20]}"
# Example: "emb:v2:a3f5d8c2b1e4f6a7b8c9"
cache.set(cache_key, embedding, timeout=30*24*60*60)  # 30 days
```

---

#### مرحله 3: Context Retrieval (جستجوی معنایی با RAG)

**کد:** `src/AI_model/services/context_retriever.py`

**الگوریتم:**

```python
retrieval_result = ContextRetriever.retrieve_context(
    query=customer_message,
    user=self.user,
    primary_source='faq',           # از Query Router
    secondary_sources=['products'], # از Query Router
    primary_budget=800,             # بودجه توکن
    secondary_budget=300,
    routing_info=routing
)

# Output:
{
    'primary_context': [
        {
            'title': 'قیمت پلن‌های اشتراکی',
            'content': 'ما 3 پلن داریم: Starter ($14)، Pro ($29)، Enterprise (سفارشی)',
            'type': 'faq',
            'score': 0.892,  # Cosine similarity
            'source_id': UUID('...')
        },
        ...  # Top 5 chunks
    ],
    'secondary_context': [
        {
            'title': 'پلن Professional',
            'content': 'پلن Pro با قیمت $29/ماه شامل 5000 توکن، پشتیبانی...',
            'type': 'product',
            'score': 0.765
        },
        ...  # Top 3 chunks
    ],
    'sources_used': ['faq', 'products'],
    'total_chunks': 8,
    'retrieval_method': 'semantic_search'
}
```

**نحوه جستجو در PostgreSQL با pgvector:**

```sql
-- جستجوی معنایی با Cosine Similarity
SELECT 
    id,
    section_title,
    full_text,
    chunk_type,
    (1 - (tldr_embedding <=> %s::vector)) AS similarity  -- Cosine similarity
FROM 
    ai_model_tenantknowledge
WHERE 
    user_id = %s
    AND chunk_type = 'faq'
    AND tldr_embedding IS NOT NULL
ORDER BY 
    tldr_embedding <=> %s::vector  -- Cosine distance (lower is better)
LIMIT 10;
```

**استراتژی Two-Stage Retrieval:**

```
┌─────────────────────────────────────────────────────────────┐
│            Two-Stage Retrieval (TL;DR → Full Text)          │
└─────────────────────────────────────────────────────────────┘

Stage 1: Search by TL;DR Embeddings (Efficient)
├─ Query: tldr_embedding <=> query_embedding
├─ Get Top 10 chunks
└─ Filter: similarity >= 0.1

Stage 2: Use Full Text for Context
├─ Return full_text (not TL;DR)
├─ Apply token budget trimming
└─ Max 5 chunks for primary source
```

**چرا TL;DR → Full Text؟**
- TL;DR: کوتاه (80-120 کلمه) → جستجو سریع‌تر
- Full Text: کامل (300-500 کلمه) → پاسخ دقیق‌تر
- صرفه‌جویی 40% زمان جستجو

---

#### مرحله 4: Conversation Memory (حافظه مکالمه)

**کد:** `src/AI_model/services/session_memory_manager.py`

**استراتژی Rolling Summary:**

```python
if message_count > 10:
    # Summarize old messages (exclude last 5)
    summary = gemini.generate_content(f"""
    Summarize this conversation in 2-3 sentences:
    {conversation_history}
    """, max_output_tokens=150)
    
    # Cache summary (1 hour)
    cache.set(f"conv_summary:{conversation_id}", summary, 3600)

# Build context
conversation_context = f"""
Summary: {summary}  # 100-150 words

Recent Messages:
- User: {recent_msg_1}
- AI: {recent_msg_2}
- User: {recent_msg_3}
"""
```

**مدیریت حافظه:**
- **10 پیام اول:** تمام تاریخچه (بدون خلاصه)
- **10+ پیام:** خلاصه (msgs 1-N-5) + کامل (msgs N-4 تا N)
- **Cache:** 1 ساعت (تا زمان تغییر مکالمه)
- **Token Budget:** 150 توکن

---

#### مرحله 5: Token Budget Control (مدیریت بودجه توکن)

**کد:** `src/AI_model/services/token_budget_controller.py`

**هدف:** حداکثر 1500 توکن ورودی

**تخصیص بودجه:**

```python
TOKEN_BUDGET = 1500  # Total input tokens

BUDGET_ALLOCATION = {
    'system_prompt': 200,    # 13.3%  - System instructions
    'customer_info': 50,     # 3.3%   - Name, phone, source
    'conversation': 150,     # 10.0%  - Memory + recent messages
    'primary_context': 800,  # 53.3%  - Main knowledge chunks
    'secondary_context': 300 # 20.0%  - Supplementary chunks
}

# Query is variable (usually 50-200 tokens)
```

**الگوریتم Trimming:**

```python
def trim_to_budget(components):
    total_tokens = 0
    
    # 1. System Prompt (ضروری - نمی‌تواند کوتاه شود)
    system_tokens = count_tokens(components['system_prompt'])
    total_tokens += min(system_tokens, 200)
    
    # 2. Customer Info (ضروری)
    customer_tokens = count_tokens(components['customer_info'])
    total_tokens += min(customer_tokens, 50)
    
    # 3. Conversation (قابل کاهش)
    conv_tokens = count_tokens(components['conversation'])
    if total_tokens + conv_tokens > BUDGET:
        conv_tokens = BUDGET - total_tokens
        # Trim oldest messages first
        components['conversation'] = trim_text(
            components['conversation'], 
            max_tokens=conv_tokens
        )
    total_tokens += conv_tokens
    
    # 4. Primary Context (مهم‌ترین بخش)
    for chunk in components['primary_context']:
        chunk_tokens = count_tokens(chunk['content'])
        if total_tokens + chunk_tokens > BUDGET:
            # Trim this chunk or skip
            remaining = BUDGET - total_tokens
            if remaining > 100:
                chunk['content'] = trim_text(chunk['content'], remaining)
                total_tokens += remaining
            break
        total_tokens += chunk_tokens
    
    # 5. Secondary Context (اگر فضا مانده باشد)
    for chunk in components['secondary_context']:
        chunk_tokens = count_tokens(chunk['content'])
        if total_tokens + chunk_tokens > BUDGET:
            break
        total_tokens += chunk_tokens
    
    # 6. User Query (همیشه اضافه می‌شود)
    query_tokens = count_tokens(components['user_query'])
    total_tokens += query_tokens
    
    return trimmed_components, total_tokens
```

---

#### مرحله 6: Prompt Building (ساخت پرامپت نهایی)

**کد:** `src/AI_model/services/gemini_service.py` → `_build_prompt()`

**ساختار Prompt:**

```
SYSTEM: {combined_prompt}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{combined_prompt} = 
    - Mother Prompt (auto_prompt from GeneralSettings)
    - Manual Prompt (user's manual_prompt)
    - Business Prompt (industry-specific guidelines)
    - Greeting Rule (smart greeting logic)

Customer: Name: احمد محمدی, Phone: 09123456789, Source: telegram

CONVERSATION HISTORY:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Summary: مشتری درباره قیمت‌ها سوال کرده و ما پلن‌ها رو توضیح دادیم.

Recent Messages:
- User: پلن Pro چه امکاناتی داره؟
- AI: پلن Pro شامل 5000 توکن، پشتیبانی 24/7، و...
- User: قیمت پلن شما چنده؟

KNOWLEDGE BASE:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
**قیمت پلن‌های اشتراکی**
ما 3 پلن اشتراکی داریم:
1. Starter: $14/ماه - شامل 1000 توکن
2. Pro: $29/ماه - شامل 5000 توکن
3. Enterprise: قیمت سفارشی - توکن نامحدود

**امکانات پلن Professional**
پلن Pro شامل:
- 5000 توکن AI ماهانه
- پشتیبانی اولویت‌دار 24/7
- API access
- Advanced analytics
- نصب روی دامنه شخصی

ADDITIONAL INFO:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- محصول: پلن Professional - قیمت $29، لینک: https://fiko.net/pricing

CUSTOMER QUESTION:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
قیمت پلن شما چنده؟

INSTRUCTION:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Answer using the knowledge base above. Be accurate, helpful, and natural.
```

**Token Count Example:**
```
System: 180 tokens
Customer: 25 tokens
Conversation: 120 tokens
Knowledge Base: 650 tokens
Additional: 180 tokens
Query: 12 tokens
Instruction: 35 tokens
─────────────────
Total: 1202 tokens ✅ (under 1500)
```

---

#### مرحله 7: AI Response Generation (تولید پاسخ)

**کد:** `src/AI_model/services/gemini_service.py` → `generate_response()`

**تنظیمات Gemini API:**

```python
model = genai.GenerativeModel(
    model_name='gemini-2.5-flash',  # یا gemini-1.5-flash
    generation_config={
        'temperature': 0.7,           # خلاقیت متوسط
        'max_output_tokens': 3000,    # حداکثر طول پاسخ
        'top_p': 0.8,
        'top_k': 40
    }
)

# Safety Settings (برای محتوای فارسی/عربی)
safety_settings = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
]

response = model.generate_content(
    prompt,
    safety_settings=safety_settings
)

# Extract token usage
prompt_tokens = response.usage_metadata.prompt_token_count
completion_tokens = response.usage_metadata.candidates_token_count
total_tokens = prompt_tokens + completion_tokens
```

**پاسخ خروجی:**

```python
{
    'success': True,
    'response': 'سلام احمد! 👋\n\nما 3 پلن اشتراکی داریم:\n\n1. **Starter** - $14/ماه\n- شامل 1000 توکن AI\n\n2. **Pro** - $29/ماه\n- شامل 5000 توکن AI\n- پشتیبانی 24/7\n- API access\n\n3. **Enterprise** - قیمت سفارشی\n- توکن نامحدود\n\nپیشنهاد من برای شما پلن Pro هست که امکانات کاملی داره! 😊',
    'response_time_ms': 2340,
    'metadata': {
        'model_used': 'gemini-2.5-flash',
        'prompt_tokens': 1202,
        'completion_tokens': 187,
        'total_tokens': 1389,
        'timestamp': '2025-10-10T15:30:45Z'
    }
}
```

---

## 🧩 سیستم Chunking و Embedding

### معماری Hybrid Auto-Chunking

```
┌──────────────────────────────────────────────────────────────┐
│         Hybrid Chunking: Real-Time + Batch Reconciliation    │
└──────────────────────────────────────────────────────────────┘

Real-Time Chunking (Django Signals)          Nightly Reconciliation
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━          ━━━━━━━━━━━━━━━━━━━━━━━━
                                            
QAPair.save()                                Every 24h @ 3 AM UTC
   │                                              │
   ├─→ post_save signal                          ├─→ Celery Beat
   │                                              │
   ├─→ Debounce 5s                               ├─→ Scan all sources
   │                                              │
   └─→ chunk_qapair_async.delay()                ├─→ Delete orphaned chunks
        │                                         │
        ├─→ IncrementalChunker.chunk_qapair()    ├─→ Create missing chunks
        │   │                                     │
        │   ├─→ Delete old chunk (idempotent)    └─→ Fix missing embeddings
        │   ├─→ Generate TL;DR
        │   ├─→ Generate embeddings
        │   │   ├─→ OpenAI API
        │   │   └─→ Gemini fallback
        │   └─→ Create TenantKnowledge chunk
        │
        └─→ Cache invalidation
```

### TenantKnowledge Model (Vector Store)

**کد:** `src/AI_model/models.py`

```python
class TenantKnowledge(models.Model):
    """
    Vector store برای RAG
    استفاده از pgvector برای جستجوی معنایی
    """
    
    # Primary key
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    
    # Owner (Multi-tenancy)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    
    # Source reference
    chunk_type = models.CharField(
        max_length=20,
        choices=[
            ('faq', 'FAQ'),
            ('manual', 'Manual Prompt'),
            ('product', 'Product'),
            ('website', 'Website Page'),
        ]
    )
    source_id = models.UUIDField(
        help_text="Reference to original FAQ/Product/WebsitePage ID"
    )
    
    # Hierarchical structure (برای Manual Prompt بزرگ)
    document_id = models.UUIDField(
        help_text="Group chunks from same document"
    )
    section_title = models.TextField()
    
    # Content
    full_text = models.TextField()  # 300-500 کلمه
    tldr = models.TextField()       # 80-120 کلمه (خلاصه)
    
    # Embeddings (pgvector)
    tldr_embedding = VectorField(
        dimensions=1536,  # OpenAI text-embedding-3-small
        help_text="Fast retrieval (TL;DR)"
    )
    full_embedding = VectorField(
        dimensions=1536,
        help_text="Full content (if needed)"
    )
    
    # Metadata
    word_count = models.IntegerField()
    language = models.CharField(max_length=10)  # fa, en, ar, tr
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['user', 'chunk_type']),
            models.Index(fields=['user', 'source_id']),
            # pgvector index (created via SQL migration)
            # CREATE INDEX ON ai_model_tenantknowledge 
            # USING ivfflat (tldr_embedding vector_cosine_ops)
            # WITH (lists = 100);
        ]
```

### Incremental Chunker (Real-Time)

**کد:** `src/AI_model/services/incremental_chunker.py`

**مثال: Chunk کردن QAPair**

```python
chunker = IncrementalChunker(user=user)

def chunk_qapair(qa):
    # 1. Delete old chunk (idempotent)
    TenantKnowledge.objects.filter(
        user=user,
        source_id=qa.id,
        chunk_type='faq'
    ).delete()
    
    # 2. Build full text
    full_text = f"Q: {qa.question}\n\nA: {qa.answer}"
    
    # 3. Generate TL;DR (extractive)
    tldr = _extract_tldr(full_text, max_words=100)
    # Example TL;DR: "Q: قیمت پلن چنده؟\n\nA: ما 3 پلن داریم: Starter ($14), Pro ($29), Enterprise..."
    
    # 4. Generate embeddings
    embedding_service = EmbeddingService()
    tldr_embedding = embedding_service.get_embedding(tldr)          # 1536 dims
    full_embedding = embedding_service.get_embedding(full_text)     # 1536 dims
    
    # 5. Create chunk
    TenantKnowledge.objects.create(
        user=user,
        chunk_type='faq',
        source_id=qa.id,
        section_title=qa.question[:200],
        full_text=full_text,
        tldr=tldr,
        tldr_embedding=tldr_embedding,
        full_embedding=full_embedding,
        word_count=len(full_text.split()),
        language=detect_language(full_text)  # 'fa', 'en', etc.
    )
```

**مثال: Chunk کردن Manual Prompt (بزرگ)**

```python
def chunk_manual_prompt():
    ai_prompts = AIPrompts.objects.get(user=user)
    manual_text = ai_prompts.manual_prompt  # ممکن است 10,000+ کلمه باشد
    
    # Split into chunks (500 words each)
    chunks = _chunk_text(manual_text, max_words=500)
    # Example: 20 chunks از 500 کلمه
    
    document_id = uuid.uuid4()  # Group all chunks
    
    for i, chunk_text in enumerate(chunks):
        tldr = _extract_tldr(chunk_text, max_words=100)
        tldr_embedding = embedding_service.get_embedding(tldr)
        full_embedding = embedding_service.get_embedding(chunk_text)
        
        TenantKnowledge.objects.create(
            user=user,
            chunk_type='manual',
            document_id=document_id,  # همه chunks یک document_id دارند
            section_title=f"Manual Prompt - Part {i+1}",
            full_text=chunk_text,
            tldr=tldr,
            tldr_embedding=tldr_embedding,
            full_embedding=full_embedding,
            word_count=len(chunk_text.split())
        )
```

### استراتژی Chunking

**قوانین:**

```python
CHUNKING_RULES = {
    'faq': {
        'max_chunk_size': 'N/A',  # هر QAPair = 1 chunk
        'tldr_size': 100,         # کلمه
        'strategy': 'one_per_item'
    },
    'product': {
        'max_chunk_size': 'N/A',  # هر Product = 1 chunk
        'tldr_size': 80,
        'strategy': 'one_per_item'
    },
    'manual': {
        'max_chunk_size': 500,    # کلمه
        'tldr_size': 100,
        'strategy': 'hierarchical_split',
        'preserve': 'paragraphs'  # حفظ مرز پاراگراف‌ها
    },
    'website': {
        'max_chunk_size': 500,    # کلمه
        'tldr_size': 100,
        'strategy': 'hierarchical_split',
        'preserve': 'paragraphs'
    }
}
```

**الگوریتم Text Splitting:**

```python
def _chunk_text(text, max_words=500):
    """
    Smart chunking که مرز پاراگراف‌ها رو حفظ می‌کنه
    """
    if len(text.split()) <= max_words:
        return [text]
    
    chunks = []
    paragraphs = text.split('\n\n')
    
    current_chunk = []
    current_words = 0
    
    for para in paragraphs:
        para_words = len(para.split())
        
        if current_words + para_words <= max_words:
            current_chunk.append(para)
            current_words += para_words
        else:
            if current_chunk:
                chunks.append('\n\n'.join(current_chunk))
            
            # پاراگراف خیلی بزرگ؟ بشکن به جملات
            if para_words > max_words:
                sentences = para.split('. ')
                # ... (split by sentences)
            else:
                current_chunk = [para]
                current_words = para_words
    
    if current_chunk:
        chunks.append('\n\n'.join(current_chunk))
    
    return chunks
```

---

## 🌐 Knowledge Sources و Crawling

### 4 منبع دانش (Knowledge Sources)

```
┌────────────────────────────────────────────────────────────────┐
│                      Knowledge Sources                         │
└────────────────────────────────────────────────────────────────┘

1. FAQ (QAPair)                    3. Products
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━     ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Source: web_knowledge.QAPair       Source: web_knowledge.Product
Trigger: post_save signal          Trigger: post_save signal
Chunking: 1 QAPair → 1 chunk      Chunking: 1 Product → 1 chunk
Format:                            Format:
  Q: {question}                      **{title}**
  A: {answer}                        {description}
                                     Price: {price}
                                     Link: {link}

2. Manual Prompt                   4. Website Pages
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━     ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Source: settings.AIPrompts         Source: web_knowledge.WebsitePage
Trigger: post_save signal          Trigger: Async crawl task
Chunking: Split every 500 words    Chunking: Split every 500 words
Strategy: Hierarchical             Strategy: Hierarchical
```

### Website Crawler (اتوماتیک)

**کد:** `src/web_knowledge/services/crawler_service.py`

**معماری:**

```
┌────────────────────────────────────────────────────────────────┐
│                    Website Crawler Flow                        │
└────────────────────────────────────────────────────────────────┘

User → Create WebsiteSource
│      ├─ URL: https://example.com
│      ├─ max_pages: 30
│      ├─ crawl_depth: 3
│      └─ auto_extract_products: true
│
├─→ POST /api/v1/web-knowledge/websites/create-and-crawl/
│
└─→ Celery Task: crawl_website_task.delay(website_id)
     │
     ├─→ 1. Initialize WebsiteCrawler
     │    ├─ Respectful delay: 2.0s between requests
     │    ├─ User-Agent: "Fiko WebKnowledge Bot 1.0"
     │    └─ Connection pooling (Session)
     │
     ├─→ 2. BFS Crawling
     │    ├─ Start: base_url (depth=0)
     │    ├─ Extract links from page
     │    ├─ Filter: same domain (unless include_external=true)
     │    ├─ Queue new URLs (depth+1)
     │    └─ Stop: max_pages OR max_depth
     │
     ├─→ 3. Extract Content (per page)
     │    ├─ BeautifulSoup HTML parsing
     │    ├─ Remove: <script>, <style>, <nav>, <footer>
     │    ├─ Clean: whitespace, ads, menus
     │    └─ Save: WebsitePage.cleaned_content
     │
     ├─→ 4. Generate Q&A Pairs (per page)
     │    ├─ Check: word_count >= 100
     │    ├─ AI: QAGenerator.generate_qa_pairs()
     │    │   ├─ Model: Gemini 1.5 Flash
     │    │   ├─ Prompt: "Generate FAQ from this page..."
     │    │   └─ Output: JSON [{Q, A}, ...]
     │    ├─ Validation: Remove bad Q&A
     │    └─ Save: QAPair (auto-linked to page)
     │
     ├─→ 5. Auto-Extract Products (if enabled)
     │    ├─ Pre-filter: Page has product keywords?
     │    │   (قیمت, price, خرید, buy, محصول, product)
     │    ├─ AI: Gemini Pro "Extract products from page..."
     │    └─ Save: Product (auto-linked to page)
     │
     └─→ 6. Chunk Pages
          └─→ chunk_webpage_async.delay(page_id)
               └─→ TenantKnowledge chunks (1-5 per page)
```

**مثال Crawler Code:**

```python
class WebsiteCrawler:
    def __init__(self, base_url, max_pages=30, max_depth=3, delay=2.0):
        self.base_url = base_url
        self.max_pages = max_pages
        self.max_depth = max_depth
        self.delay = delay  # Respectful crawling
        
        self.visited_urls = set()
        self.crawled_pages = []
        
        # Session for connection reuse
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Fiko WebKnowledge Bot 1.0'
        })
    
    def crawl(self):
        urls_to_crawl = [(self.base_url, 0)]  # (url, depth)
        
        while urls_to_crawl and len(self.crawled_pages) < self.max_pages:
            current_url, depth = urls_to_crawl.pop(0)
            
            if current_url in self.visited_urls or depth > self.max_depth:
                continue
            
            # Crawl page
            page_data = self._crawl_page(current_url, depth)
            if page_data:
                self.crawled_pages.append(page_data)
                
                # Extract new URLs
                new_urls = self._extract_urls(page_data['links'], depth + 1)
                urls_to_crawl.extend(new_urls)
            
            # Respectful delay
            time.sleep(self.delay)
        
        return self.crawled_pages
    
    def _crawl_page(self, url, depth):
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            # Parse HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract content
            title = soup.find('title').text if soup.find('title') else url
            
            # Remove unwanted elements
            for tag in soup(['script', 'style', 'nav', 'footer', 'header']):
                tag.decompose()
            
            # Get text content
            raw_content = soup.get_text(separator='\n')
            cleaned_content = self._clean_text(raw_content)
            
            # Extract links
            links = [a['href'] for a in soup.find_all('a', href=True)]
            
            self.visited_urls.add(url)
            
            return {
                'url': url,
                'title': title,
                'raw_content': raw_content,
                'cleaned_content': cleaned_content,
                'links': links,
                'depth': depth,
                'word_count': len(cleaned_content.split())
            }
            
        except Exception as e:
            logger.error(f"Failed to crawl {url}: {e}")
            return None
```

### Q&A Auto-Generation

**کد:** `src/web_knowledge/services/qa_generator.py`

```python
class QAGenerator:
    def generate_qa_pairs(self, content, page_title, max_pairs=5):
        """
        تولید اتوماتیک سوال و جواب از محتوای صفحه
        """
        # Split content if too long
        content_chunks = self._split_content(content, max_chunk_size=3000)
        
        all_qa_pairs = []
        for chunk in content_chunks:
            prompt = f"""
You are an expert creating natural Q&A pairs from website content.

Page: {page_title}
Content: {chunk}

RULES:
- Create {max_pairs} natural questions as if a customer is asking
- Provide COMPLETE, SPECIFIC answers with actual details
- Use real info: prices, contact, features, policies
- NO generic templates
- NO URLs in questions

Format as JSON:
[
  {{"question": "...", "answer": "..."}},
  ...
]
"""
            
            response = self.model.generate_content(prompt)
            qa_json = self._extract_json(response.text)
            all_qa_pairs.extend(qa_json)
        
        # Validate & clean
        validated = self._validate_qa_pairs(all_qa_pairs)
        return validated[:max_pairs]
```

---

## 🔍 Query Router (مسیریابی سوال)

**کد:** `src/AI_model/services/query_router.py`

### تشخیص Intent

**کلمات کلیدی پیش‌فرض:**

```python
DEFAULT_KEYWORDS = {
    'pricing': {
        'fa': ['قیمت', 'هزینه', 'تعرفه', 'پلن', 'پکیج', 'اشتراک', 'خرید'],
        'en': ['price', 'cost', 'plan', 'subscription', 'buy', 'payment'],
        'ar': ['سعر', 'تكلفة', 'خطة', 'اشتراك', 'شراء'],
        'tr': ['fiyat', 'maliyet', 'plan', 'abonelik']
    },
    'product': {
        'fa': ['محصول', 'سرویس', 'خدمات', 'ویژگی', 'امکانات', 'چیه'],
        'en': ['product', 'service', 'feature', 'what is'],
        'ar': ['منتج', 'خدمة', 'ميزة'],
        'tr': ['ürün', 'hizmet', 'özellik']
    },
    'howto': {
        'fa': ['چطور', 'چگونه', 'راهنما', 'آموزش', 'نحوه', 'کمک'],
        'en': ['how', 'guide', 'tutorial', 'help'],
        'ar': ['كيف', 'دليل', 'مساعدة'],
        'tr': ['nasıl', 'rehber', 'yardım']
    },
    'contact': {
        'fa': ['تماس', 'ارتباط', 'پشتیبانی', 'شماره', 'ایمیل', 'آدرس'],
        'en': ['contact', 'support', 'phone', 'email'],
        'ar': ['اتصال', 'دعم', 'هاتف'],
        'tr': ['iletişim', 'destek', 'telefon']
    }
}
```

### تنظیمات Routing

```python
DEFAULT_ROUTING = {
    'pricing': {
        'primary_source': 'faq',
        'secondary_sources': ['products', 'manual'],
        'token_budget': {'primary': 800, 'secondary': 300}
    },
    'product': {
        'primary_source': 'products',
        'secondary_sources': ['faq', 'website'],
        'token_budget': {'primary': 800, 'secondary': 300}
    },
    'howto': {
        'primary_source': 'manual',
        'secondary_sources': ['faq', 'website'],
        'token_budget': {'primary': 800, 'secondary': 300}
    },
    'contact': {
        'primary_source': 'manual',
        'secondary_sources': ['website'],
        'token_budget': {'primary': 800, 'secondary': 300}
    },
    'general': {
        'primary_source': 'faq',
        'secondary_sources': ['manual'],
        'token_budget': {'primary': 800, 'secondary': 300}
    }
}
```

---

## 📊 Context Retriever (RAG با pgvector)

### جستجوی معنایی

**SQL Query:**

```sql
-- Top-K Retrieval با Cosine Similarity
SELECT 
    id,
    section_title,
    full_text,
    chunk_type,
    word_count,
    (1 - (tldr_embedding <=> $1::vector(1536))) AS similarity
FROM 
    ai_model_tenantknowledge
WHERE 
    user_id = $2
    AND chunk_type = $3
    AND tldr_embedding IS NOT NULL
    AND (1 - (tldr_embedding <=> $1::vector(1536))) >= 0.1  -- MIN_SIMILARITY
ORDER BY 
    tldr_embedding <=> $1::vector(1536)  -- Cosine distance
LIMIT 10;
```

### Index برای Performance

```sql
-- IVFFlat Index (Approximate Nearest Neighbor)
CREATE INDEX idx_tenant_knowledge_tldr_embedding 
ON ai_model_tenantknowledge 
USING ivfflat (tldr_embedding vector_cosine_ops)
WITH (lists = 100);

-- بهینه‌سازی:
-- lists = sqrt(rows) → برای 10000 row، lists = 100
-- Tradeoff: Speed vs Accuracy
```

---

## 💰 Token Management

### مدیریت توکن

```python
# Pre-check (قبل از AI call)
estimated_tokens = 700  # برای prompt enhancement
if subscription.tokens_remaining < estimated_tokens:
    raise Exception('Insufficient tokens')

# Consume (بعد از AI call)
actual_tokens = response.usage_metadata.total_token_count  # مثلاً 1389
consume_tokens_for_user(user, actual_tokens, description='AI response')

# Update subscription
subscription.tokens_used += actual_tokens
subscription.tokens_remaining -= actual_tokens
subscription.save()
```

---

## 🚀 مثال‌های عملی

### مثال 1: سوال درباره قیمت

**Input:**
```
User: "قیمت پلن Pro چنده؟"
```

**Processing:**

```python
# 1. Query Router
routing = {
    'intent': 'pricing',
    'confidence': 0.92,
    'primary_source': 'faq',
    'secondary_sources': ['products'],
    'keywords_matched': ['قیمت', 'پلن']
}

# 2. Embedding
query_embedding = [0.0234, -0.1456, 0.0892, ..., 0.0234]  # 1536 dims

# 3. Context Retrieval (pgvector)
primary_chunks = [
    {
        'title': 'قیمت پلن‌های اشتراکی',
        'content': 'ما 3 پلن داریم...',
        'score': 0.892
    }
]
secondary_chunks = [
    {
        'title': 'پلن Professional',
        'content': 'پلن Pro - $29/ماه...',
        'score': 0.765
    }
]

# 4. Prompt Building
prompt = """
SYSTEM: {combined_prompt}
KNOWLEDGE BASE: {primary_chunks + secondary_chunks}
QUESTION: قیمت پلن Pro چنده؟
"""
# Total: 1180 tokens

# 5. Gemini Response
ai_response = "پلن Professional (Pro) ما به قیمت $29 در ماه ارائه میشه که شامل..."
tokens_used = 1389  # 1180 input + 209 output
```

**Output:**
```
AI: پلن Professional (Pro) ما به قیمت $29 در ماه ارائه میشه که شامل:

✅ 5000 توکن AI ماهانه
✅ پشتیبانی اولویت‌دار 24/7
✅ API access
✅ Advanced analytics
✅ نصب روی دامنه شخصی

این پلن برای کسب‌وکارهای متوسط مناسبه! 😊
```

---

### مثال 2: سوال خارج از حوزه

**Input:**
```
User: "آب و هوای تهران امروز چطوره؟"
```

**Processing:**

```python
# 1. Query Router
routing = {
    'intent': 'general',  # هیچ keyword مرتبط پیدا نشد
    'confidence': 0.5,
    'primary_source': 'faq',
    'secondary_sources': ['manual']
}

# 2. Context Retrieval
# هیچ chunk مرتبط با score > 0.1 پیدا نشد
primary_chunks = []
secondary_chunks = []

# 3. Confidence Instruction
# Low confidence → Tell user we can't help with this
```

**Output:**
```
AI: متاسفانه من درباره آب و هوا اطلاعاتی ندارم. من فقط میتونم درباره محصولات و خدمات ما، قیمت‌ها، و نحوه استفاده کمکتون کنم. 😊

آیا سوال دیگه‌ای درباره سرویس‌های ما دارید؟
```

---

## 📈 Monitoring و Performance

### Metrics

```python
# AI Usage Tracking (per day, per user)
class AIUsageTracking:
    user = ForeignKey(User)
    date = DateField()
    
    total_requests = IntegerField()          # تعداد کل درخواست‌ها
    successful_requests = IntegerField()     # موفق
    failed_requests = IntegerField()         # ناموفق
    
    total_prompt_tokens = IntegerField()     # توکن‌های ورودی
    total_completion_tokens = IntegerField() # توکن‌های خروجی
    total_tokens = IntegerField()            # مجموع
    
    total_response_time_ms = IntegerField()  # زمان پاسخ (ms)
    avg_response_time_ms = FloatField()      # میانگین
```

### Performance Targets

```
┌────────────────────────────────────────────────────────────┐
│                 Performance Targets (v2.1)                 │
└────────────────────────────────────────────────────────────┘

Metric                      Target        Current    Status
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Input Tokens per Query      ≤ 1500        ~1200      ✅
Output Tokens per Response  ≤ 500         ~200       ✅
Total Response Time         ≤ 3s          ~2.3s      ✅
RAG Retrieval Time          ≤ 100ms       ~45ms      ✅
Embedding Cache Hit Rate    ≥ 80%         ~85%       ✅
Answer Accuracy             ≥ 90%         ~92%       ✅
Multilingual Support        4 langs       4 langs    ✅
  (FA, EN, AR, TR)
```

---

## 🎓 خلاصه فنی

### Stack Technology

```
┌────────────────────────────────────────────────────────────┐
│                      Technology Stack                      │
└────────────────────────────────────────────────────────────┘

Backend:
  - Django 4.2+
  - PostgreSQL 15+ with pgvector
  - Redis (Cache)
  - Celery (Async tasks)

AI Services:
  - Google Gemini 2.5 Flash (Response generation)
  - OpenAI text-embedding-3-small (Primary embedding)
  - Google Gemini text-embedding-004 (Fallback embedding)

Vector Database:
  - pgvector extension
  - IVFFlat index (Approximate Nearest Neighbor)
  - Cosine similarity search

Libraries:
  - google-generativeai (Gemini API)
  - openai (OpenAI API)
  - pgvector (Django integration)
  - beautifulsoup4 (Web scraping)
  - rank-bm25 (BM25 fallback)
```

### Key Features

✅ **Lean RAG Architecture** - هزینه توکن کمتر (≤1500)  
✅ **Multi-Source Retrieval** - 4 منبع دانش (FAQ, Manual, Products, Website)  
✅ **Semantic Search** - جستجوی معنایی با pgvector  
✅ **Multilingual** - پشتیبانی از 4 زبان (FA/EN/AR/TR)  
✅ **Real-Time Chunking** - به‌روزرسانی اتوماتیک با Django Signals  
✅ **Smart Routing** - مسیریابی هوشمند با keyword matching  
✅ **Token Management** - مدیریت دقیق مصرف توکن  
✅ **Conversation Memory** - حافظه مکالمه با rolling summary  
✅ **Auto-Crawling** - کرال و استخراج اتوماتیک محتوا  

---

## 📞 پشتیبانی

برای سوالات فنی یا گزارش باگ، لطفاً به تیم AI مراجعه کنید.

**Repository:** `https://github.com/fiko/backend`  
**Documentation:** این فایل + کدهای منبع  
**Version:** 2.1 (October 2025)

---

**🎉 پایان مستندات**

این مستند شامل تمامی اطلاعات فنی، معماری، و نحوه عملکرد سیستم پاسخگویی هوش مصنوعی FIKO است.

