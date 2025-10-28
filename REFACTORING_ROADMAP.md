# 🔧 **Crawl & Chunking System - Refactoring Roadmap**

## 📋 **Executive Summary**

این سیستم برای **10-50 کاربر** به خوبی کار می‌کنه، اما برای **500+ کاربر همزمان** نیاز به refactoring دارد.

**مشکلات کلیدی:**
- ❌ Race condition در signals
- ❌ Thundering herd در task dispatch  
- ❌ N+1 API calls برای embedding generation
- ❌ Database lock contention
- ❌ Memory leaks در crawler
- ❌ No monitoring/alerting

---

## 🎯 **Phase 1: Quick Wins (1-2 روز، Critical)**

### ✅ **1.1 Fix Race Condition در Chunking Signal**

**فایل:** `src/AI_model/signals.py`

**مشکل فعلی:**
```python
# ❌ Race condition: Two signals can both pass exists() check
already_chunked = TenantKnowledge.objects.filter(
    source_id=instance.id,
    chunk_type='website'
).exists()

if already_chunked:
    return
    
chunk_webpage_async.apply_async(args=[str(instance.id)], countdown=10)
```

**راه حل:**
```python
from django.db import transaction
from django.db.models import F

@receiver(post_save, sender='web_knowledge.WebsitePage')
def on_webpage_saved_for_chunking(sender, instance, **kwargs):
    """
    Auto-chunk WebPage when processing completes (thread-safe)
    """
    if instance.processing_status != 'completed':
        return
    
    from AI_model.models import TenantKnowledge
    from web_knowledge.models import WebsitePage
    
    # ✅ Atomic check-and-mark to prevent race conditions
    with transaction.atomic():
        # Lock the page row
        page = WebsitePage.objects.select_for_update().filter(
            id=instance.id,
            processing_status='completed'
        ).first()
        
        if not page:
            return
        
        # Check if already chunked
        if TenantKnowledge.objects.filter(
            source_id=page.id,
            chunk_type='website'
        ).exists():
            logger.debug(f"WebPage {page.id} already chunked")
            return
        
        # Mark as chunking_queued to prevent duplicate signals
        page.chunking_status = 'queued'  # Add this field to model
        page.save(update_fields=['chunking_status'])
    
    # Queue task outside transaction (non-blocking)
    from AI_model.tasks import chunk_webpage_async
    chunk_webpage_async.apply_async(args=[str(page.id)], countdown=10)
    logger.info(f"✅ Queued chunking for WebPage {page.id}")
```

**Migration needed:**
```python
# Add to WebsitePage model
chunking_status = models.CharField(
    max_length=20, 
    choices=[
        ('not_started', 'Not Started'),
        ('queued', 'Queued'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('failed', 'Failed')
    ],
    default='not_started'
)
```

---

### ✅ **1.2 Stagger Task Dispatch (Prevent Thundering Herd)**

**فایل:** `src/web_knowledge/tasks.py` (خط 132)

**مشکل فعلی:**
```python
# ❌ 200 tasks در <1 ثانیه queue میشن
for page_data in crawled_pages:
    page.save()
    process_page_content_task.delay(str(page.id))  # Instant dispatch
```

**راه حل:**
```python
# ✅ Distribute tasks over time
for i, page_data in enumerate(crawled_pages):
    try:
        # ... save page logic ...
        
        # Stagger tasks: 200 pages over 3 minutes = 1 task every 0.9 seconds
        # This prevents Redis/Celery overload
        countdown = int(i * 0.9)  # Spread over ~3 minutes
        
        process_page_content_task.apply_async(
            args=[str(page.id)],
            countdown=countdown
        )
        
        if (i + 1) % 50 == 0:
            logger.info(f"Queued {i + 1}/{len(crawled_pages)} page processing tasks")
    except Exception as e:
        logger.error(f"Error queuing page {page_data.get('url')}: {str(e)}")
        failed_pages += 1

logger.info(f"✅ All {len(crawled_pages)} tasks queued (staggered over ~{int(len(crawled_pages) * 0.9 / 60)} minutes)")
```

---

### ✅ **1.3 Bulk Database Operations در Chunking**

**فایل:** `src/AI_model/services/incremental_chunker.py` (خط 174-240)

**مشکل فعلی:**
```python
# ❌ 1 DELETE + N INSERTs = N+1 database locks
TenantKnowledge.objects.filter(...).delete()

for chunk_text, metadata in chunks_with_metadata:
    TenantKnowledge.objects.create(...)  # Separate INSERT per chunk
```

**راه حل:**
```python
def chunk_webpage(self, page) -> bool:
    try:
        from AI_model.models import TenantKnowledge
        from AI_model.services.embedding_service import EmbeddingService
        
        # Delete existing chunks (idempotency)
        TenantKnowledge.objects.filter(
            user=self.user,
            source_id=page.id,
            chunk_type='website'
        ).delete()
        
        # ... chunking logic ...
        
        # ✅ Prepare all chunks first (no DB writes yet)
        chunks_to_create = []
        embedding_service = EmbeddingService()
        document_id = uuid.uuid4()
        
        for chunk_text, metadata in chunks_with_metadata:
            tldr = PersianChunker.extract_tldr_persian(chunk_text, max_words=100)
            
            # Generate embeddings
            tldr_embedding = embedding_service.get_embedding(tldr)
            full_embedding = embedding_service.get_embedding(chunk_text)
            
            if not tldr_embedding or not full_embedding:
                continue
            
            section_title = (
                page.title if metadata.chunk_index == 0 
                else f"{page.title} - Part {metadata.chunk_index + 1}"
            )
            
            chunk_metadata = {
                'page_url': metadata.page_url,
                'keywords': metadata.keywords,
                'h1_tags': metadata.h1_tags,
                'h2_tags': metadata.h2_tags,
                'chunk_index': metadata.chunk_index,
                'total_chunks': metadata.total_chunks,
            }
            
            # Append to list (not saved yet)
            chunks_to_create.append(
                TenantKnowledge(
                    user=self.user,
                    chunk_type='website',
                    source_id=page.id,
                    document_id=document_id,
                    full_text=chunk_text,
                    tldr=tldr,
                    section_title=section_title,
                    word_count=len(chunk_text.split()),
                    tldr_embedding=tldr_embedding,
                    full_embedding=full_embedding,
                    metadata=chunk_metadata,
                    parent_chunk_id=None,  # Parent-child logic if needed
                )
            )
        
        # ✅ Single bulk insert (much faster, single lock)
        if chunks_to_create:
            TenantKnowledge.objects.bulk_create(
                chunks_to_create,
                batch_size=100  # Insert 100 at a time
            )
            logger.info(f"✅ Created {len(chunks_to_create)} chunks for WebPage {page.id}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error chunking WebPage {page.id}: {str(e)}")
        return False
```

---

### ✅ **1.4 Add Basic Monitoring**

**فایل جدید:** `src/monitoring/metrics.py`

```python
from prometheus_client import Counter, Histogram, Gauge

# Crawl metrics
crawl_total = Counter(
    'crawl_total', 
    'Total website crawls', 
    ['status', 'user_id']
)

crawl_pages_total = Counter(
    'crawl_pages_total',
    'Total pages crawled',
    ['website_id']
)

# Processing metrics
page_process_duration = Histogram(
    'page_process_duration_seconds',
    'Time to process a single page',
    buckets=[1, 5, 10, 30, 60, 120, 300]
)

page_process_total = Counter(
    'page_process_total',
    'Total pages processed',
    ['status']
)

# Chunking metrics
chunk_duration = Histogram(
    'chunk_duration_seconds',
    'Time to chunk a single page',
    buckets=[1, 5, 10, 30, 60]
)

chunk_total = Counter(
    'chunk_total',
    'Total pages chunked',
    ['status']
)

chunks_created = Counter(
    'chunks_created_total',
    'Total TenantKnowledge chunks created',
    ['chunk_type']
)

# Queue metrics (updated by periodic task)
queue_size = Gauge(
    'celery_queue_size',
    'Number of tasks in Celery queue',
    ['queue_name']
)
```

**استفاده در tasks:**

```python
# در process_page_content_task
from monitoring.metrics import page_process_duration, page_process_total

@shared_task(bind=True, max_retries=2)
def process_page_content_task(self, page_id: str):
    with page_process_duration.time():
        try:
            # ... processing logic ...
            page_process_total.labels(status='success').inc()
        except Exception as e:
            page_process_total.labels(status='error').inc()
            raise
```

---

## 🎯 **Phase 2: Performance Optimization (3-5 روز، High Priority)**

### ✅ **2.1 Batch Embedding API Calls**

**مشکل:** 5 chunks × 2 embeddings = **10 API calls per page**

**راه حل:** Batch API calls

**فایل:** `src/AI_model/services/embedding_service.py`

```python
def get_embeddings_batch(self, texts: List[str], batch_size: int = 10) -> List[List[float]]:
    """
    Generate embeddings for multiple texts in batches
    
    Args:
        texts: List of texts to embed
        batch_size: Number of texts per API call (OpenAI allows up to 2048)
        
    Returns:
        List of embedding vectors
    """
    all_embeddings = []
    
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        
        try:
            # Single API call for batch
            response = self.client.embeddings.create(
                input=batch,
                model=self.model
            )
            
            # Extract embeddings in order
            embeddings = [item.embedding for item in response.data]
            all_embeddings.extend(embeddings)
            
        except Exception as e:
            logger.error(f"Batch embedding failed: {str(e)}")
            # Fallback: Individual embeddings
            for text in batch:
                embedding = self.get_embedding(text)
                all_embeddings.append(embedding)
    
    return all_embeddings
```

**استفاده در incremental_chunker.py:**

```python
# Extract all texts first
tldrs = []
full_texts = []

for chunk_text, metadata in chunks_with_metadata:
    tldr = PersianChunker.extract_tldr_persian(chunk_text, max_words=100)
    tldrs.append(tldr)
    full_texts.append(chunk_text)

# ✅ Batch API calls (2 calls instead of 10)
tldr_embeddings = embedding_service.get_embeddings_batch(tldrs)
full_embeddings = embedding_service.get_embeddings_batch(full_texts)

# Create chunks with pre-generated embeddings
for i, (chunk_text, metadata) in enumerate(chunks_with_metadata):
    chunks_to_create.append(
        TenantKnowledge(
            ...
            tldr_embedding=tldr_embeddings[i],
            full_embedding=full_embeddings[i],
            ...
        )
    )
```

**Impact:** 10 API calls → 2 API calls = **5x reduction**

---

### ✅ **2.2 Memory Optimization (Generator Pattern)**

**فایل:** `src/web_knowledge/tasks.py`

**مشکل:** همه crawled pages تو memory نگه داشته میشن

**راه حل:**

```python
def crawl_website_task(self, website_source_id: str):
    # ... setup code ...
    
    # ✅ Process pages incrementally (don't load all into memory)
    page_generator = crawler.crawl_generator(progress_callback=progress_callback)
    
    saved_pages = 0
    failed_pages = 0
    
    for page_data in page_generator:
        try:
            # Save immediately
            page = save_single_page(page_data, website_source)
            saved_pages += 1
            
            # Queue processing (staggered)
            countdown = saved_pages * 0.9
            process_page_content_task.apply_async(
                args=[str(page.id)],
                countdown=countdown
            )
            
        except Exception as e:
            logger.error(f"Error saving page: {str(e)}")
            failed_pages += 1
        
        # Update progress every 10 pages
        if saved_pages % 10 == 0:
            website_source.crawl_progress = (saved_pages / crawler.max_pages) * 100
            website_source.save(update_fields=['crawl_progress'])
```

---

### ✅ **2.3 Add Circuit Breaker for External APIs**

**فایل جدید:** `src/core/circuit_breaker.py`

```python
from functools import wraps
from time import time
from threading import Lock

class CircuitBreaker:
    """
    Simple circuit breaker for external API calls
    """
    def __init__(self, failure_threshold=5, recovery_timeout=60):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failures = 0
        self.last_failure_time = None
        self.state = 'closed'  # closed, open, half_open
        self.lock = Lock()
    
    def call(self, func, *args, **kwargs):
        with self.lock:
            if self.state == 'open':
                # Check if recovery timeout passed
                if time() - self.last_failure_time > self.recovery_timeout:
                    self.state = 'half_open'
                else:
                    raise Exception("Circuit breaker is OPEN")
            
            try:
                result = func(*args, **kwargs)
                
                # Success: reset or close circuit
                if self.state == 'half_open':
                    self.state = 'closed'
                    self.failures = 0
                
                return result
                
            except Exception as e:
                self.failures += 1
                self.last_failure_time = time()
                
                if self.failures >= self.failure_threshold:
                    self.state = 'open'
                
                raise

# Global circuit breakers
embedding_circuit = CircuitBreaker(failure_threshold=5, recovery_timeout=60)
gemini_circuit = CircuitBreaker(failure_threshold=3, recovery_timeout=120)
```

**استفاده:**

```python
def get_embedding(self, text: str):
    try:
        return embedding_circuit.call(self._get_embedding_internal, text)
    except Exception as e:
        logger.error(f"Circuit breaker prevented embedding call: {str(e)}")
        return None  # Graceful degradation
```

---

## 🎯 **Phase 3: Horizontal Scaling (1 هفته، Medium Priority)**

### ✅ **3.1 Database Connection Pooling (PgBouncer)**

**docker-compose.yml:**

```yaml
pgbouncer:
  image: pgbouncer/pgbouncer:latest
  environment:
    DATABASES: "pilito = host=db port=5432 dbname=pilito"
    POOL_MODE: transaction
    MAX_CLIENT_CONN: 1000
    DEFAULT_POOL_SIZE: 25
    RESERVE_POOL_SIZE: 5
  ports:
    - "6432:6432"
  depends_on:
    - db
```

**Update Django settings:**

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'HOST': 'pgbouncer',  # Changed from 'db'
        'PORT': '6432',       # Changed from 5432
        # ... other settings
    }
}
```

---

### ✅ **3.2 Redis Sentinel (High Availability)**

### ✅ **3.3 Multiple Celery Worker Nodes**

### ✅ **3.4 Task Priority Queue Tuning**

---

## 🎯 **Phase 4: Advanced Features (2-3 هفته، Low Priority)**

### ✅ **4.1 Distributed Rate Limiting**
### ✅ **4.2 Auto-scaling Workers (based on queue depth)**
### ✅ **4.3 Kafka Event Streaming (replace signals)**
### ✅ **4.4 Elasticsearch for Full-Text Search**

---

## 📊 **Testing Strategy**

### **Load Testing Script:**

```python
# tests/load_test_crawl.py
import concurrent.futures
import requests
from time import time

def test_concurrent_crawls(num_users=50):
    """
    Simulate 50 users simultaneously crawling websites
    """
    def crawl_for_user(user_id):
        start = time()
        response = requests.post(
            'https://api.pilito.com/api/v1/web-knowledge/websites/create-and-crawl/',
            json={'url': f'https://example{user_id}.com', 'max_pages': 200},
            headers={'Authorization': f'Bearer {get_token(user_id)}'}
        )
        elapsed = time() - start
        return {'user_id': user_id, 'status': response.status_code, 'time': elapsed}
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
        futures = [executor.submit(crawl_for_user, i) for i in range(num_users)]
        results = [f.result() for f in concurrent.futures.as_completed(futures)]
    
    # Analyze results
    success_rate = sum(1 for r in results if r['status'] == 200) / len(results)
    avg_time = sum(r['time'] for r in results) / len(results)
    
    print(f"Success Rate: {success_rate * 100}%")
    print(f"Average Time: {avg_time:.2f}s")
```

---

## 📈 **Success Metrics**

| Metric | Current | Target (500 Users) |
|--------|---------|-------------------|
| Crawl Success Rate | 95% | 99% |
| Page Process Time | 5-10s | <5s |
| Chunking Time | 10-20s | <10s |
| Queue Backlog | <1K | <5K |
| API Error Rate | 2% | <0.5% |
| Database Deadlocks | Occasional | Zero |

---

## 🚀 **Implementation Priority:**

1. **Week 1:** Phase 1 (Quick Wins) - Fix critical race conditions & bottlenecks
2. **Week 2-3:** Phase 2 (Performance) - Batch APIs, memory optimization, circuit breakers
3. **Week 4:** Phase 3 (Scaling) - PgBouncer, Redis Sentinel, multi-node Celery
4. **Week 5+:** Phase 4 (Advanced) - Auto-scaling, Kafka, Elasticsearch

---

## 📝 **Notes:**

- هر phase رو می‌شه به صورت **incremental** پیاده‌سازی کرد
- بعد از هر phase باید **load test** بزنیم
- Monitoring و alerting از همون روز اول باید باشه
- Database migrations رو باید با **zero downtime** انجام بدیم

---

**مهم:** این refactoring باید به صورت **backward compatible** باشه - سیستم فعلی نباید break بشه!

