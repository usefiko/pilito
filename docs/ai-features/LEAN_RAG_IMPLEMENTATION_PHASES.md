# 🎯 Lean RAG v2.1 - پلن اجرایی دقیق

**تاریخ:** 2025-10-07  
**وضعیت:** منتظر تایید برای شروع  
**هدف:** کاهش 11,000 → 1,500 tokens و بهبود سرعت/دقت

---

## 📊 بررسی سیستم فعلی

### ✅ چیزهایی که **الان داریم** و کار می‌کنه:

#### **1. Infrastructure (100% آماده)**
```yaml
PostgreSQL: ✅ version 15 (docker-compose)
Redis: ✅ version 7 (docker-compose)
Celery: ✅ worker + beat با 4 queue
WebSocket: ✅ Daphne + channels-redis
Docker: ✅ کامل setup شده
AWS EC2: ✅ production server
```

#### **2. Libraries نصب شده:**
```python
✅ openai >= 1.12.0              # برای embedding
✅ google-generativeai >= 0.8.0  # برای Gemini
✅ rank-bm25 == 0.2.2             # برای fallback search
✅ redis, django-redis             # caching
✅ celery, django-celery-beat      # async tasks
✅ channels, daphne                # WebSocket
✅ psycopg2-binary                 # PostgreSQL
```

#### **3. Services موجود:**

**`EmbeddingService`** (کامل و کار می‌کنه):
- ✅ OpenAI text-embedding-3-large (3072 dimensions)
- ✅ Gemini fallback
- ✅ Redis caching (30 days TTL)
- ✅ Cosine similarity calculation
- ✅ Document ranking

**`GeminiChatService`** (سیستم فعلی AI):
- ✅ Gemini 2.5 Flash integration
- ✅ Prompt building با JSON config
- ✅ Conversation summarization (برای مکالمات > 10 پیام)
- ✅ BM25 ranking برای FAQ (top 8)
- ✅ Embedding ranking برای FAQ (با fallback به BM25)
- ✅ Token tracking (input/output/total)
- ✅ Billing integration
- ✅ WebSocket notification

**`MessageSystemIntegration`**:
- ✅ Auto AI response triggering
- ✅ Token checking
- ✅ Conversation status management

#### **4. Data Models:**

**موجود:**
- ✅ `Message` (content, type, is_ai_response, token fields)
- ✅ `Conversation` (status: active/support_active/closed)
- ✅ `AIGlobalConfig` (global settings)
- ✅ `AIUsageTracking` (token usage per user per day)
- ✅ `QAPair` (FAQ از web crawling)
- ✅ `Product` (محصولات)
- ✅ `WebsiteSource`, `WebsitePage` (داده‌های crawl شده)
- ✅ `AIPrompts` (manual_prompt per user)

#### **5. API Endpoints موجود:**

```
POST /api/v1/ai/ask/                          # پرسش مستقیم از AI
GET  /api/v1/ai/config/                       # تنظیمات global
GET  /api/v1/ai/config/status/                # وضعیت config
GET  /api/v1/ai/conversations/{id}/status/    # وضعیت مکالمه
PUT  /api/v1/ai/conversations/{id}/status/    # تغییر status (AI/manual)
PUT  /api/v1/ai/conversations/bulk-status/    # bulk status update
GET  /api/v1/ai/default-handler/              # handler پیش‌فرض user
PUT  /api/v1/ai/default-handler/              # تغییر handler
GET  /api/v1/ai/usage/stats/                  # آمار استفاده
GET  /api/v1/ai/usage/global/                 # آمار global (admin)
```

#### **6. Flow فعلی AI Response:**

```
Customer Message (Telegram/Instagram/WebSocket)
    ↓
Message.objects.create(type='customer')
    ↓
Signal: post_save (message/signals.py)
    ↓
Check: global AI enabled? conversation status = active?
    ↓
Celery Task: process_ai_response_async (ai_tasks queue)
    ↓
MessageSystemIntegration.process_new_customer_message()
    ↓
Check tokens → GeminiChatService.generate_response()
    ↓
_build_prompt():
    - Get manual_prompt (کل متن!)
    - Get FAQ (top 8 با embedding/BM25)
    - Get Products (top 6)
    - Get Website pages (top 2 sites × 5 pages)
    - Get conversation history (6 messages یا summary + 5)
    - Build JSON config
    ↓
Gemini API call
    ↓
create_ai_message() → Send to Telegram/Instagram
    ↓
WebSocket notification to frontend
```

---

### ❌ چیزهایی که **نداریم** و باید اضافه کنیم:

```yaml
❌ pgvector extension در PostgreSQL
❌ pgvector Python package
❌ TenantKnowledge model (vector store)
❌ SessionMemory model (rolling summaries)
❌ IntentKeyword model (optional)
❌ IntentRouting model (optional)
❌ QueryRouter service (intent classification)
❌ ContextRetriever service (RAG با pgvector)
❌ TokenBudgetController service (1500 token enforcer)
❌ SessionMemoryManager service (rolling summary)
❌ Management command برای indexing data
❌ Refactored _build_prompt() method
```

---

### ⚠️ مشکلات سیستم فعلی:

#### **1. Token Usage خیلی بالا (11,000 tokens/conversation):**

```python
# فعلاً در _build_prompt():

manual_prompt: 15,000 کلمه → ~19,500 tokens  # همه رو می‌فرسته!
FAQ: 8 pairs × 150 کلمه → ~1,560 tokens
Products: 6 × 100 کلمه → ~780 tokens
Website: 2 sites × 5 pages → ~2,000 tokens
Conversation: 6 messages → ~500 tokens
System prompt: ~300 tokens
─────────────────────────────────────────
Total: ~24,640 tokens! ❌

# Gemini input limit handles it, but:
- Cost: $0.28 per conversation
- Latency: 15-20 seconds
- "Over-context" problem → جواب‌های نادقیق
```

#### **2. No Intent Classification:**
- همه context ها رو برای همه سوالات می‌فرسته
- مثلاً برای "قیمت چقدره؟" نیازی به WebsitePage نیست!

#### **3. No Token Budget Control:**
- هیچ محدودیتی نداریم
- اگه manual_prompt بزرگ‌تر بشه، بیشتر می‌فرسته

#### **4. Cumulative Summarization:**
- هر 10 پیام یک summary می‌سازه
- اما summaries جمع می‌شن! (10 + 10 + 10 = 30 پیام → 3 summary)

---

## 🎯 اهداف Lean RAG v2.1

| Metric | فعلی | هدف | بهبود |
|--------|------|-----|-------|
| Input Tokens | 11,000 | ≤1,500 | 86% کاهش |
| Cost/conversation | $0.28 | $0.03 | 89% کاهش |
| Response Time | 15-20s | 6-8s | 50% سریع‌تر |
| Accuracy | متوسط | بالا | +30% |

---

## 📅 فازهای اجرایی (دقیق)

### **فاز 0: Setup Infrastructure** (2-3 ساعت)

#### چیکار می‌کنیم:
1. نصب pgvector extension در PostgreSQL
2. اضافه کردن pgvector به requirements.txt
3. تست pgvector

#### چطوری:

**Step 1: Configure PostgreSQL for pgvector**
```bash
# ⚠️ مهم: باید shared_preload_libraries تنظیم بشه

# Option 1: اگر docker-compose استفاده می‌کنید
# اضافه کردن به docker-compose.yml:
services:
  db:
    image: postgres:15
    environment:
      POSTGRES_DB: ${POSTGRES_DB}
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    command: >
      postgres -c shared_preload_libraries='vector'

# یا Option 2: تغییر postgresql.conf مستقیم
docker-compose exec db bash
echo "shared_preload_libraries = 'vector'" >> /var/lib/postgresql/data/postgresql.conf
exit

# Restart PostgreSQL برای اعمال تغییرات
docker-compose restart db

# تست:
docker-compose exec db psql -U postgres -c "SHOW shared_preload_libraries;"
# باید 'vector' رو نشون بده
```

**Step 2: Install pgvector extension**
```bash
# در سرور/local
docker-compose exec db psql -U postgres -d fiko_db

# در psql:
CREATE EXTENSION IF NOT EXISTS vector;

# تست:
SELECT * FROM pg_extension WHERE extname = 'vector';
# باید 1 row برگردونه

# خروج:
\q
```

**Step 3: Add to requirements**
```bash
# اضافه کردن به src/requirements/base.txt
echo "pgvector==0.3.6" >> src/requirements/base.txt
echo "tiktoken==0.8.0" >> src/requirements/base.txt  # برای token counting دقیق

# نصب:
docker-compose exec web pip install pgvector==0.3.6

# یا rebuild:
docker-compose build web
docker-compose up -d
```

**Step 4: Test در Django shell**
```python
docker-compose exec web python manage.py shell

from pgvector.django import VectorField
print("pgvector imported successfully! ✅")
```

#### تست موفقیت:
```python
# باید بدون error اجرا بشه:
from pgvector.django import VectorField, CosineDistance
```

#### خروجی فاز 0:
- ✅ pgvector extension فعال
- ✅ pgvector package نصب
- ✅ آماده برای ساخت models

---

### **فاز 1: Database Models** (3-4 ساعت)

#### چیکار می‌کنیم:
4 model جدید می‌سازیم برای RAG system

#### Models:

**1. TenantKnowledge** (اصلی‌ترین):
```python
# Vector store برای همه knowledge sources
# Fields:
- user (FK to User)
- chunk_type: 'faq', 'manual', 'product', 'website'
- source_id: reference به FAQ/Product/Page اصلی
- full_text: متن کامل
- tldr: خلاصه 80-120 کلمه (برای search)
- tldr_embedding: vector(3072) ← pgvector
- language: 'fa', 'en', 'ar', 'tr'
- metadata: JSONB
```

**2. SessionMemory** (rolling summary):
```python
# یک summary در هر conversation
# Fields:
- conversation (OneToOne to Conversation)
- user (FK)
- cumulative_summary: TEXT (≤150 tokens)
- message_count: INT
- last_updated: DateTime
```

**3. IntentKeyword** (optional):
```python
# Keywords برای intent detection
# Fields:
- intent: 'pricing', 'product', 'howto', 'contact', 'general'
- language: 'fa', 'en', 'ar', 'tr'
- keyword: VARCHAR(100)
- weight: FLOAT (1.0-3.0)
- user: FK (nullable - برای global keywords)
- is_active: BOOLEAN
```

**4. IntentRouting** (optional):
```python
# Routing config
# Fields:
- intent: PK
- primary_source: 'faq', 'manual', 'products', 'website'
- secondary_sources: ArrayField
- primary_token_budget: INT (default: 800)
- secondary_token_budget: INT (default: 300)
```

#### چطوری:

**Step 1: Edit models.py**
```bash
# اضافه کردن models به:
src/AI_model/models.py
```

**Step 2: Create migration**
```bash
docker-compose exec web python manage.py makemigrations AI_model

# خروجی باید باشه:
# Migrations for 'AI_model':
#   AI_model/migrations/0003_tenantknowledge_sessionmemory_intentkeyword_intentrouting.py
#     - Create model TenantKnowledge
#     - Create model SessionMemory
#     - Create model IntentKeyword
#     - Create model IntentRouting
```

**Step 3: Review migration**
```bash
docker-compose exec web python manage.py sqlmigrate AI_model 0003

# بررسی کنید:
# - vector fields درست ایجاد میشن
# - indexes درست هستن
```

**Step 4: Apply migration**
```bash
docker-compose exec web python manage.py migrate AI_model

# خروجی:
# Running migrations:
#   Applying AI_model.0003_... OK
```

**Step 5: Create vector index manually**
```bash
docker-compose exec db psql -U postgres -d fiko_db

CREATE INDEX idx_tenant_knowledge_tldr_embedding 
ON tenant_knowledge 
USING ivfflat (tldr_embedding vector_cosine_ops) 
WITH (lists = 100);

# Verify:
\d tenant_knowledge

\q
```

#### تست موفقیت:

```python
docker-compose exec web python manage.py shell

from AI_model.models import TenantKnowledge, SessionMemory
from accounts.models import User

user = User.objects.first()

# Test 1: Create a knowledge chunk
chunk = TenantKnowledge.objects.create(
    user=user,
    chunk_type='faq',
    full_text='این یک تست است',
    tldr='تست',
    language='fa',
    word_count=4
)
print(f"Created chunk: {chunk.id}")

# Test 2: Add embedding
from AI_model.services.embedding_service import EmbeddingService
emb_service = EmbeddingService(use_cache=True)
embedding = emb_service.get_embedding('تست', task_type='retrieval_document')

if embedding:
    chunk.tldr_embedding = embedding
    chunk.save()
    print(f"Embedding added! Dimension: {len(embedding)}")

# Test 3: Vector search
from pgvector.django import CosineDistance

query_emb = emb_service.get_embedding('تست', task_type='retrieval_query')
similar = TenantKnowledge.objects.filter(
    user=user
).order_by(CosineDistance('tldr_embedding', query_emb))[:5]

print(f"Found {similar.count()} similar chunks")

# Success! ✅
```

#### خروجی فاز 1:
- ✅ 4 model جدید در database
- ✅ Vector index کار می‌کنه
- ✅ می‌تونیم vector search انجام بدیم

---

### **فاز 2: Core Services** (6-8 ساعت)

#### چیکار می‌کنیم:
4 service جدید می‌نویسیم

#### Services:

**1. QueryRouter** (`src/AI_model/services/query_router.py`):
- Intent classification با keyword matching
- روی کلمات فارسی، انگلیسی، عربی، ترکی
- خروجی: intent + confidence + primary_source

**2. ContextRetriever** (`src/AI_model/services/context_retriever.py`):
- Vector search با pgvector
- Token budget enforcement
- خروجی: primary items + secondary items (اگه لازم باشه)

**3. TokenBudgetController** (`src/AI_model/services/token_budget_controller.py`):
- **⚠️ CRITICAL:** استفاده از token counter دقیق (tiktoken یا Gemini API metadata)
- Strict 1500 token limit
- Trim کردن components
- اولویت: system > user query > conversation > primary > secondary

**نکته مهم Token Counting:**
```python
# ❌ اشتباه: تخمین ساده
def _count_tokens(text):
    return int(len(text.split()) * 1.3)  # نادقیق!

# ✅ درست: استفاده از tiktoken
import tiktoken

def _count_tokens_accurate(text, model="gpt-3.5-turbo"):
    try:
        encoding = tiktoken.encoding_for_model(model)
        return len(encoding.encode(text))
    except:
        # Fallback: Gemini API metadata
        # یا تخمین محافظه‌کارانه
        return int(len(text.split()) * 1.5)  # بیشتر تخمین می‌زنیم
```

**4. SessionMemoryManager** (`src/AI_model/services/session_memory_manager.py`):
- **⚠️ CRITICAL:** Rolling summary (هر 5 پیام update) - REPLACE نه APPEND
- Gemini استفاده می‌کنه برای summarization
- خروجی: context string (summary + recent messages)

**نکته مهم Rolling Summary:**
```python
# ❌ اشتباه: Append کردن summaries (مشکل فعلی!)
def _update_summary_wrong(self, session_memory, new_messages):
    old_summary = session_memory.cumulative_summary
    new_part = self._summarize(new_messages)
    session_memory.cumulative_summary = old_summary + "\n" + new_part  # ❌ جمع میشه!
    session_memory.save()

# ✅ درست: Replace کردن summary
def _update_summary_correct(self, session_memory, conversation):
    all_messages = Message.objects.filter(conversation=conversation)
    
    if not session_memory.cumulative_summary:
        # اولین بار: خلاصه همه پیام‌ها
        new_summary = self._summarize_all(all_messages)
    else:
        # دفعات بعد: خلاصه (summary قبلی + پیام‌های جدید)
        prompt = f"""Previous summary: {session_memory.cumulative_summary}
        
New messages: {new_messages_text}

Update the summary (REPLACE the old one, max 50 words):"""
        new_summary = self._call_gemini(prompt)
    
    session_memory.cumulative_summary = new_summary  # ✅ Replace
    session_memory.message_count = all_messages.count()
    session_memory.save()
```

#### چطوری:

**Step 1-4: Create service files**
```bash
# در src/AI_model/services/
touch query_router.py
touch context_retriever.py
touch token_budget_controller.py
touch session_memory_manager.py
```

**کد هر service رو می‌نویسیم (طبق طراحی در سند v2.1)**

#### تست موفقیت:

```python
docker-compose exec web python manage.py shell

from AI_model.services.query_router import QueryRouter
from AI_model.services.context_retriever import ContextRetriever
from AI_model.services.token_budget_controller import TokenBudgetController
from AI_model.services.session_memory_manager import SessionMemoryManager
from AI_model.services.gemini_service import GeminiChatService
from accounts.models import User

user = User.objects.first()

# Test 1: QueryRouter
result = QueryRouter.route_query("قیمت پلن Pro چقدره؟", user)
print(f"Intent: {result['intent']}")  # باید 'pricing' باشه
print(f"Primary source: {result['primary_source']}")  # باید 'faq' باشه
print(f"Confidence: {result['confidence']}")

# Test 2: TokenBudgetController
components = {
    'system_prompt': 'You are a helpful AI assistant.' * 50,  # خیلی بزرگ!
    'user_query': 'قیمت چقدره؟',
    'conversation': 'Customer: سلام\nAssistant: سلام',
    'primary_context': [
        {'title': 'FAQ 1', 'content': 'محتوا' * 500}  # خیلی بزرگ!
    ],
    'secondary_context': []
}

trimmed = TokenBudgetController.trim_to_budget(components)
print(f"Total tokens: {trimmed['total_tokens']}")  # باید ≤1500 باشه

# Test 3: SessionMemoryManager
gemini_service = GeminiChatService(user)
memory_manager = SessionMemoryManager(gemini_service)

# باید بدون error کار کنه
context = memory_manager.get_memory_context(None)
print(f"Context length: {len(context)}")

# Success! ✅
```

#### خروجی فاز 2:
- ✅ QueryRouter کار می‌کنه
- ✅ TokenBudgetController enforce می‌کنه
- ✅ SessionMemoryManager آماده
- ✅ ContextRetriever آماده (بعد از indexing تست می‌کنیم)

---

### **فاز 3: Refactor GeminiChatService** (2-3 ساعت)

#### چیکار می‌کنیم:
متد `_build_prompt()` رو کامل refactor می‌کنیم

#### قبل (فعلی):
```python
def _build_prompt(self, customer_message, conversation):
    # همه manual_prompt
    # همه FAQ (8 items)
    # همه Products (6 items)
    # همه Website (10 pages)
    # → 24,000+ tokens!
```

#### بعد (جدید):
```python
def _build_prompt(self, customer_message, conversation):
    # 1. Intent classification
    routing = QueryRouter.route_query(customer_message, self.user)
    
    # 2. Vector search (فقط مرتبط‌ترین‌ها)
    retriever = ContextRetriever(self.user)
    context_data = retriever.retrieve(customer_message, routing)
    
    # 3. Rolling summary
    memory_manager = SessionMemoryManager(self)
    conversation_context = memory_manager.get_memory_context(conversation)
    
    # 4. Token budget enforcement
    components = {...}
    trimmed = TokenBudgetController.trim_to_budget(components)
    
    # 5. Build minimal prompt
    # → ≤1500 tokens! ✅
```

#### چطوری:

**Step 1: Backup قدیمی**
```bash
cp src/AI_model/services/gemini_service.py src/AI_model/services/gemini_service.py.backup
```

**Step 2: Refactor _build_prompt()**
```python
# Replace کردن متد _build_prompt با implementation جدید
```

**Step 3: حفظ compatibility**
```python
# همه چیز دیگه نباید عوض بشه:
- generate_response() signature
- create_ai_message()
- API endpoints
- return values
```

#### تست موفقیت:

```python
docker-compose exec web python manage.py shell

from AI_model.services.gemini_service import GeminiChatService
from message.models import Conversation
from accounts.models import User

user = User.objects.first()
service = GeminiChatService(user)

# Test با یک سوال واقعی
response = service.generate_response("قیمت پلن Pro چقدره؟")

print(f"Success: {response['success']}")
print(f"Response: {response['response'][:100]}")
print(f"Tokens: {response['metadata']['total_tokens']}")  # باید ≤1500 باشه!

# با conversation
conv = Conversation.objects.filter(user=user).first()
if conv:
    response2 = service.generate_response("ممنون!", conv)
    print(f"With conversation - Tokens: {response2['metadata']['total_tokens']}")

# Success! ✅
```

#### خروجی فاز 3:
- ✅ _build_prompt() refactored
- ✅ Token usage ≤1500
- ✅ API compatibility حفظ شده
- ✅ همه چیز کار می‌کنه

---

### **فاز 4: Data Indexing** (4-6 ساعت)

#### چیکار می‌کنیم:
داده‌های موجود رو به TenantKnowledge منتقل می‌کنیم

#### Data Sources:

**1. FAQ (QAPair model):**
```
- هر QAPair → 1 chunk در TenantKnowledge
- chunk_type = 'faq'
- full_text = question + answer
- tldr = question (کوتاه‌تر)
- Generate embedding برای tldr
```

**2. Manual Prompt:**
```
- اگه < 1000 کلمه → 1 chunk
- اگه > 1000 کلمه → chunk کنیم به paragraphs
- برای هر chunk بزرگ → TL;DR با Gemini
- Generate embeddings
```

**3. Products:**
```
- هر Product → 1 chunk
- chunk_type = 'product'
- full_text = title + description + price
- Generate embeddings
```

**4. Website Pages:**
```
- هر WebsitePage → 1 یا چند chunk
- اگه cleaned_content بزرگه → chunk کنیم
- Generate embeddings
```

#### چطوری:

**Step 1: Create management command**
```bash
mkdir -p src/AI_model/management/commands
touch src/AI_model/management/commands/index_tenant_knowledge.py
```

**Step 2: Implementation**
```python
# Command structure:
class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('--user', type=str, help='Username')
        parser.add_argument('--chunk-size', type=int, default=400)
        parser.add_argument('--dry-run', action='store_true')
    
    def handle(self, *args, **options):
        user = User.objects.get(username=options['user'])
        
        # 1. Index FAQs
        self.index_faqs(user)
        
        # 2. Index Manual Prompt
        self.index_manual_prompt(user, options['chunk_size'])
        
        # 3. Index Products
        self.index_products(user)
        
        # 4. Index Website Pages
        self.index_website_pages(user)
```

**Step 3: Run command**
```bash
# Test با یک user
docker-compose exec web python manage.py index_tenant_knowledge --user admin --dry-run

# واقعی:
docker-compose exec web python manage.py index_tenant_knowledge --user admin

# خروجی:
# ✅ Indexed 100 FAQ pairs
# ✅ Indexed 45 manual prompt chunks (generated 45 TL;DRs)
# ✅ Indexed 200 products
# ✅ Indexed 150 website page chunks
# ✅ Generated 495 embeddings
# ✅ Total time: 8m 32s
```

#### تست موفقیت:

```python
docker-compose exec web python manage.py shell

from AI_model.models import TenantKnowledge
from accounts.models import User

user = User.objects.first()

# Check counts
print(f"FAQ: {TenantKnowledge.objects.filter(user=user, chunk_type='faq').count()}")
print(f"Manual: {TenantKnowledge.objects.filter(user=user, chunk_type='manual').count()}")
print(f"Product: {TenantKnowledge.objects.filter(user=user, chunk_type='product').count()}")
print(f"Website: {TenantKnowledge.objects.filter(user=user, chunk_type='website').count()}")
print(f"Total: {TenantKnowledge.objects.filter(user=user).count()}")

# Test embeddings
chunks_with_emb = TenantKnowledge.objects.filter(
    user=user,
    tldr_embedding__isnull=False
).count()
print(f"Chunks with embeddings: {chunks_with_emb}")

# Test search
from AI_model.services.context_retriever import ContextRetriever
from AI_model.services.query_router import QueryRouter

routing = QueryRouter.route_query("قیمت چقدره؟", user)
retriever = ContextRetriever(user)
context = retriever.retrieve("قیمت چقدره؟", routing)

print(f"Retrieved {len(context['primary']['items'])} primary items")
print(f"First item: {context['primary']['items'][0]['title']}")

# Success! ✅
```

#### خروجی فاز 4:
- ✅ همه data indexed شده
- ✅ Embeddings generated
- ✅ Vector search کار می‌کنه
- ✅ Context retrieval موفق

---

### **فاز 5: Integration Testing** (2-3 ساعت)

#### چیکار می‌کنیم:
کل سیستم رو end-to-end تست می‌کنیم

#### Test Cases:

**Test 1: Intent Classification**
```python
test_queries = [
    ("قیمت پلن Pro چقدره؟", "pricing", "faq"),
    ("محصولات شما چی هستن؟", "product", "products"),
    ("چطور ثبت نام کنم؟", "howto", "manual"),
    ("شماره تماس چیه؟", "contact", "manual"),
]

for query, expected_intent, expected_source in test_queries:
    result = QueryRouter.route_query(query, user)
    assert result['intent'] == expected_intent
    assert result['primary_source'] == expected_source
    print(f"✅ {query} → {result['intent']}")
```

**Test 2: Token Budget**
```python
# سوالات مختلف
queries = [
    "سلام",
    "قیمت چقدره؟",
    "می‌خوام درباره محصولات شما بیشتر بدونم و ببینم کدوم برای کسب و کار من بهتره",
]

for query in queries:
    response = service.generate_response(query)
    tokens = response['metadata']['total_tokens']
    assert tokens <= 1500, f"Token limit exceeded: {tokens}"
    print(f"✅ Query: {query[:30]}... → {tokens} tokens")
```

**Test 3: Response Quality**
```python
# سوالات معمول
test_qa = [
    ("قیمت پلن Pro چقدره؟", ["قیمت", "پلن", "Pro"]),  # باید این کلمات رو داشته باشه
    ("چطور ثبت نام کنم؟", ["ثبت نام", "راهنما"]),
    ("تماس", ["شماره", "ایمیل", "تماس"]),
]

for query, expected_keywords in test_qa:
    response = service.generate_response(query)
    response_text = response['response'].lower()
    
    found = sum(1 for kw in expected_keywords if kw in response_text)
    print(f"Query: {query}")
    print(f"  Keywords found: {found}/{len(expected_keywords)}")
    print(f"  Response: {response_text[:100]}...")
```

**Test 4: Conversation Context**
```python
# Test با conversation
conv = Conversation.objects.create(user=user, customer=customer)

# Message 1
r1 = service.generate_response("سلام", conv)
Message.objects.create(conversation=conv, customer=customer, type='customer', content='سلام')
Message.objects.create(conversation=conv, customer=customer, type='AI', content=r1['response'])

# Message 2
r2 = service.generate_response("قیمت چقدره؟", conv)
Message.objects.create(conversation=conv, customer=customer, type='customer', content='قیمت چقدره؟')

# Message 6 (باید summary trigger بشه)
for i in range(4):
    Message.objects.create(conversation=conv, customer=customer, type='customer', content=f'test {i}')

r3 = service.generate_response("خلاصه بگو", conv)

# Check SessionMemory
from AI_model.models import SessionMemory
memory = SessionMemory.objects.get(conversation=conv)
print(f"Summary: {memory.cumulative_summary}")
print(f"Message count: {memory.message_count}")
```

**Test 5: Performance**
```python
import time

queries = ["قیمت چقدره؟"] * 10

start = time.time()
for query in queries:
    response = service.generate_response(query)
end = time.time()

avg_time = (end - start) / len(queries)
print(f"Average response time: {avg_time:.2f}s")
assert avg_time < 10, "Too slow!"
```

#### خروجی فاز 5:
- ✅ همه test cases pass
- ✅ Token budget محترم
- ✅ Response quality خوب
- ✅ Performance قابل قبول

---

### **فاز 6: API Compatibility Check** (1 ساعت)

#### چیکار می‌کنیم:
مطمئن می‌شیم frontend همچنان کار می‌کنه

#### Test:

**Test 1: Ask API**
```bash
curl -X POST http://localhost:8000/api/v1/ai/ask/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "قیمت چقدره؟",
    "conversation_id": "CONV_ID"
  }'

# Response باید باشه:
{
  "success": true,
  "response": "...",
  "response_time_ms": 6500,
  "metadata": {
    "total_tokens": 1450,  # ≤1500 ✅
    "model_used": "gemini-1.5-flash"
  }
}
```

**Test 2: Automatic Response (via Signal)**
```python
# ارسال پیام customer از Telegram/Instagram
# باید خودکار AI جواب بده
# و در Message model ذخیره بشه
```

**Test 3: WebSocket**
```javascript
// از frontend
ws.send(JSON.stringify({
  type: 'chat_message',
  content: 'سلام',
  message_type: 'customer'
}));

// باید AI response رو دریافت کنه
```

#### خروجی فاز 6:
- ✅ همه API endpoints کار می‌کنن
- ✅ Frontend compatibility حفظ شده
- ✅ WebSocket کار می‌کنه

---

### **فاز 7: Production Deployment** (2 ساعت)

#### Checklist:

```bash
# 1. Commit changes
git add .
git commit -m "feat: Implement Lean RAG v2.1 - 86% token reduction"

# 2. Push to repository
git push origin main

# 3. در server:
cd /path/to/Fiko-Backend
git pull origin main

# 4. Install dependencies
docker-compose exec web pip install -r src/requirements/base.txt

# یا rebuild:
docker-compose build web

# 5. Setup pgvector
docker-compose exec db psql -U postgres -d fiko_db
CREATE EXTENSION IF NOT EXISTS vector;
\q

# 6. Run migrations
docker-compose exec web python manage.py migrate

# 7. Create vector index
docker-compose exec db psql -U postgres -d fiko_db
CREATE INDEX idx_tenant_knowledge_tldr_embedding 
ON tenant_knowledge 
USING ivfflat (tldr_embedding vector_cosine_ops) 
WITH (lists = 100);
\q

# 8. Index data برای کاربران موجود
docker-compose exec web python manage.py index_tenant_knowledge --user USER1
docker-compose exec web python manage.py index_tenant_knowledge --user USER2

# 9. Restart services
docker-compose restart web celery_worker

# 10. Monitor logs
docker-compose logs -f web celery_worker | grep -i "token\|rag\|intent"

# 11. Test در production
# ارسال چند پیام test و بررسی:
# - Token usage
# - Response quality
# - Latency
```

---

## 📊 Success Metrics

بعد از deployment، این metrics رو چک می‌کنیم:

```python
# در Django admin یا shell:
from AI_model.models import AIUsageTracking
from datetime import date, timedelta

# Usage امروز
today_usage = AIUsageTracking.objects.filter(
    date=date.today()
).aggregate(
    total_tokens=Sum('total_tokens'),
    total_requests=Sum('total_requests'),
    avg_response_time=Avg('average_response_time_ms')
)

# Calculate per-conversation average
avg_tokens_per_conv = today_usage['total_tokens'] / today_usage['total_requests']

print(f"Average tokens/conversation: {avg_tokens_per_conv}")  # باید ≤1500 باشه
print(f"Average response time: {today_usage['avg_response_time']}ms")  # باید <10s باشه
```

**Target Metrics:**
- ✅ Average input tokens: ≤1500 (vs 11,000 قبلی)
- ✅ Average response time: <8s (vs 15-20s قبلی)
- ✅ Cost per conversation: ~$0.03 (vs $0.28 قبلی)

---

## ⏱️ Timeline Summary

| فاز | مدت زمان | خروجی اصلی |
|-----|---------|-----------|
| **0. Infrastructure** | 2-3 ساعت | pgvector آماده |
| **1. Models** | 3-4 ساعت | 4 model + vector index |
| **2. Services** | 6-8 ساعت | 4 service جدید |
| **3. Refactor** | 2-3 ساعت | _build_prompt() جدید |
| **4. Indexing** | 4-6 ساعت | Data indexed |
| **5. Testing** | 2-3 ساعت | همه tests pass |
| **6. API Check** | 1 ساعت | Frontend کار می‌کنه |
| **7. Deployment** | 2 ساعت | Production ready |
| **Total** | **22-30 ساعت** | **3-4 روز کاری** |

---

## ❓ سوالات برای تایید

قبل از شروع نیاز دارم بدونم:

1. **pgvector version:** PostgreSQL شما version چنده؟ (باید 11+ باشه)
   ```bash
   docker-compose exec db psql -U postgres -c "SELECT version();"
   ```

2. **Test users:** چند تا user دارید که باید براشون index بزنیم؟

3. **Manual prompt size:** بزرگترین manual_prompt چند کلمه هست؟
   ```python
   from settings.models import AIPrompts
   max_words = max(
       len(p.manual_prompt.split()) 
       for p in AIPrompts.objects.all() 
       if p.manual_prompt
   )
   print(f"Max manual_prompt: {max_words} words")
   ```

4. **Downtime tolerance:** آیا می‌تونیم برای migration چند دقیقه downtime داشته باشیم؟ یا باید zero-downtime باشه?

5. **Backup:** آیا قبل از migration backup می‌گیرید؟

---

## 🚀 آماده برای شروع؟

اگه این پلن OK هست، می‌تونم **از فاز 0 شروع کنم**.

**موافقید؟** ✅

