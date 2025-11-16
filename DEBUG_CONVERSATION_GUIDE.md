# 🔍 راهنمای دیباگ کانورسیشن Tt7bxs

## مشکل
AI می‌گوید "متأسفانه این اطلاعات الان در دسترس نیست" در حالی که اطلاعات در manual prompt هست.

## مراحل بررسی

### 1️⃣ اجرای Command دیباگ

```bash
cd /Users/omidataei/Documents/GitHub/pilito2/Untitled/src
python manage.py debug_conversation Tt7bxs
```

این command بررسی می‌کند:
- ✅ آیا manual chunks وجود دارند؟
- ✅ آیا routing به manual انجام می‌شود؟
- ✅ آیا retrieval chunks را پیدا می‌کند؟
- ✅ آیا chunks در prompt هستند؟

### 2️⃣ بررسی Manual Chunks

اگر manual chunks وجود ندارند:

```python
# در Django shell
from accounts.models import User
from AI_model.tasks import chunk_manual_prompt_async

# پیدا کردن کاربر
user = User.objects.get(email="ایمیل کاربر")

# Chunk کردن manual prompt
chunk_manual_prompt_async.delay(user.id)
```

یا دستی:

```python
from AI_model.services.incremental_chunker import IncrementalChunker

chunker = IncrementalChunker(user)
success = chunker.chunk_manual_prompt()
print(f"Chunking success: {success}")
```

### 3️⃣ بررسی Routing

برای سوال "یک بیوگرافی از مزونتون میدی بهم کامل":
- Intent باید: `general` یا `contact`
- Primary Source باید: `manual` (اگر routing درست تنظیم شده)

اگر routing به `faq` می‌رود:
- باید IntentKeyword برای "بیوگرافی" اضافه کنید
- یا routing را تغییر دهید

### 4️⃣ بررسی Retrieval

اگر retrieval chunks را پیدا نمی‌کند:

#### الف) چک کردن Query Embedding
```python
from AI_model.services.embedding_service import EmbeddingService

query = "یک بیوگرافی از مزونتون میدی بهم کامل"
embedding_service = EmbeddingService()
embedding = embedding_service.get_embedding(query, task_type="retrieval_query")
print(f"Embedding generated: {embedding is not None}")
```

#### ب) چک کردن Hybrid Search
```python
from AI_model.services.hybrid_retriever import HybridRetriever
from AI_model.services.embedding_service import EmbeddingService

query = "یک بیوگرافی از مزونتون میدی بهم کامل"
user = User.objects.get(email="ایمیل کاربر")

embedding_service = EmbeddingService()
query_embedding = embedding_service.get_embedding(query, task_type="retrieval_query")

results = HybridRetriever.hybrid_search(
    query=query,
    user=user,
    chunk_type='manual',
    query_embedding=query_embedding,
    top_k=5
)

print(f"Found {len(results)} chunks")
for i, result in enumerate(results, 1):
    print(f"{i}. {result.get('title', 'N/A')} (score: {result.get('score', 0):.3f})")
```

### 5️⃣ بررسی Prompt

اگر chunks پیدا می‌شوند ولی در prompt نیستند:

```python
from AI_model.services.gemini_service import GeminiChatService
from message.models import Conversation

conversation = Conversation.objects.get(id="Tt7bxs")
user = conversation.user
query = "یک بیوگرافی از مزونتون میدی بهم کامل"

ai_service = GeminiChatService(user)
prompt = ai_service._build_prompt(query, conversation)

# چک کردن آیا manual chunks در prompt هستند
if "مزون" in prompt or "manual" in prompt.lower():
    print("✅ Manual content در prompt هست")
else:
    print("❌ Manual content در prompt نیست")

# نمایش بخش knowledge base
if "KNOWLEDGE BASE" in prompt:
    kb_start = prompt.find("KNOWLEDGE BASE")
    print(prompt[kb_start:kb_start+1000])
```

## مشکلات احتمالی و راه حل

### مشکل 1: Manual Chunks وجود ندارند
**راه حل**: Manual prompt را chunk کنید (مرحله 2)

### مشکل 2: Routing به manual نمی‌رود
**راه حل**: 
- IntentKeyword برای "بیوگرافی" اضافه کنید
- یا routing را تغییر دهید تا برای intent `general` به `manual` برود

### مشکل 3: Retrieval chunks را پیدا نمی‌کند
**راه حل**:
- چک کنید که query embedding درست کار می‌کند
- چک کنید که manual chunks embedding دارند
- ممکن است similarity score پایین باشد (threshold: 0.1)

### مشکل 4: Chunks پیدا می‌شوند ولی در prompt نیستند
**راه حل**:
- چک کنید که token budget کافی است
- چک کنید که TokenBudgetController chunks را trim نمی‌کند

### مشکل 5: Chunks در prompt هستند ولی AI هنوز می‌گوید "متأسفانه..."
**راه حل**:
- قوانین Anti-Hallucination را نرم‌تر کنید (✅ انجام شد)
- Instruction را قوی‌تر کنید (✅ انجام شد)

## لاگ‌های مفید

برای دیدن لاگ‌های واقعی:

```bash
# لاگ‌های AI
docker logs -f <container> | grep -E "(Routed to|Retrieved|FULL PROMPT|Hybrid Search)"

# یا برای یک conversation خاص
docker logs -f <container> | grep "Tt7bxs"
```

## خلاصه تغییرات انجام شده

1. ✅ قوانین Anti-Hallucination نرم‌تر شدند
2. ✅ Instruction در prompt قوی‌تر شد
3. ✅ Command دیباگ اضافه شد

## بعد از بررسی

بعد از اجرای `debug_conversation` command، نتایج را بفرستید تا بررسی کنم.

