# 🔄 **Hybrid Auto-Chunking Architecture**

## 📋 **Overview**

This system implements a **hybrid chunking strategy** that combines **real-time** and **batch processing** to keep the `TenantKnowledge` vector store in sync with source data.

---

## 🏗️ **Architecture**

### **1. Real-Time Auto-Chunking (Django Signals)**
- **When**: Source data created/updated (QAPair, Product, WebsitePage, AIPrompts)
- **How**: Django `post_save` signals trigger async Celery tasks
- **Debouncing**: 5-30 seconds countdown to batch rapid changes
- **Cost**: Instant (<10s latency), but more Celery tasks

**Files:**
- `src/AI_model/signals.py` - Signal handlers
- `src/AI_model/tasks.py` - Async chunking tasks

**Triggers:**
```python
# Example: QAPair created/updated
@receiver(post_save, sender='web_knowledge.QAPair')
def on_qapair_saved_for_chunking(sender, instance, created, **kwargs):
    chunk_qapair_async.apply_async(args=[str(instance.id)], countdown=5)
```

---

### **2. Nightly Reconciliation (Celery Beat)**
- **When**: Every 24 hours @ 3 AM UTC
- **How**: Scans all source data vs `TenantKnowledge` for discrepancies
- **Purpose**: Catch missed signals, fix orphaned chunks, regenerate embeddings

**What It Does:**
1. **Delete orphaned chunks** (source data deleted but chunk remains)
2. **Queue missing chunks** (source exists but no chunk)
3. **Regenerate missing embeddings** (chunk exists but embedding is NULL)

**Files:**
- `src/AI_model/management/commands/reconcile_knowledge_base.py`
- `src/AI_model/tasks.py` → `reconcile_knowledge_base_task()`
- `src/core/celery.py` → Celery Beat schedule

**Run Manually:**
```bash
docker compose exec web python manage.py reconcile_knowledge_base
```

---

## 🚀 **Celery Tasks**

### **Chunking Tasks:**
1. **`chunk_qapair_async(qapair_id)`** - FAQ → TenantKnowledge
2. **`chunk_product_async(product_id)`** - Product → TenantKnowledge
3. **`chunk_webpage_async(page_id)`** - WebsitePage → TenantKnowledge
4. **`chunk_manual_prompt_async(user_id)`** - AIPrompts → TenantKnowledge
5. **`delete_chunks_for_source_async(user_id, source_id, chunk_type)`** - Cleanup

### **Reconciliation Task:**
6. **`reconcile_knowledge_base_task()`** - Nightly consistency check

**Idempotency:**
- All tasks delete old chunks before creating new ones
- Safe to run multiple times (e.g., retry on failure)

**Retry Logic:**
- Max 3 retries with exponential backoff
- Prevents cascading failures

---

## 📊 **Data Flow**

```
┌─────────────────┐
│ User Updates    │
│ (QAPair, etc.)  │
└────────┬────────┘
         │
         │ Django Signal
         ├──────────────────────────┐
         │                          │
         ▼                          ▼
┌─────────────────┐      ┌─────────────────┐
│ Real-Time       │      │ Nightly Batch   │
│ chunk_*_async() │      │ Reconciliation  │
│ (5-30s delay)   │      │ (3 AM daily)    │
└────────┬────────┘      └────────┬────────┘
         │                        │
         └────────────┬───────────┘
                      ▼
            ┌─────────────────┐
            │ TenantKnowledge │
            │  (Vector Store) │
            └─────────────────┘
```

---

## 📝 **Signal Handlers**

| **Source Model**       | **Trigger**                     | **Task**                     | **Countdown** |
|------------------------|---------------------------------|------------------------------|---------------|
| `QAPair`               | `post_save` (completed)         | `chunk_qapair_async`         | 5s            |
| `Product`              | `post_save`                     | `chunk_product_async`        | 5s            |
| `WebsitePage`          | `post_save` (crawl completed)   | `chunk_webpage_async`        | 10s           |
| `AIPrompts`            | `post_save` (manual_prompt)     | `chunk_manual_prompt_async`  | 30s           |
| **Deletes:**           |                                 |                              |               |
| `QAPair`               | `post_delete`                   | `delete_chunks_for_source`   | 2s            |
| `Product`              | `post_delete`                   | `delete_chunks_for_source`   | 2s            |
| `WebsitePage`          | `post_delete`                   | `delete_chunks_for_source`   | 2s            |

---

## 🔧 **Setup & Deployment**

### **1. Install Dependencies:**
```bash
pip install django-model-utils  # For FieldTracker (future use)
```

### **2. Register Signals:**
Add to `src/AI_model/apps.py`:
```python
class AIModelConfig(AppConfig):
    name = 'AI_model'
    
    def ready(self):
        import AI_model.signals  # Register signals
```

### **3. Restart Services:**
```bash
docker compose restart web celery_worker celery_beat
```

### **4. Verify Celery Beat Schedule:**
```bash
docker compose exec celery_beat celery -A core inspect scheduled
```

---

## 🧪 **Testing**

### **Test Real-Time Chunking:**
```python
# Create a QAPair
from web_knowledge.models import QAPair, WebsitePage
from AI_model.models import TenantKnowledge

qa = QAPair.objects.create(
    question="Test question",
    answer="Test answer",
    generation_status='completed',
    page=WebsitePage.objects.first()
)

# Wait 5-10 seconds, then check:
TenantKnowledge.objects.filter(source_id=qa.id, chunk_type='faq')
# Should have 1 chunk
```

### **Test Nightly Reconciliation:**
```bash
# Run manually
docker compose exec web python manage.py reconcile_knowledge_base

# Check logs
docker compose logs celery_worker --tail 100 | grep reconcile
```

---

## 📈 **Monitoring**

### **Check Chunking Status:**
```python
from AI_model.models import TenantKnowledge
from web_knowledge.models import QAPair, Product, WebsitePage

# Count chunks by type
TenantKnowledge.objects.values('chunk_type').annotate(count=Count('id'))

# Find sources without chunks
completed_qa = QAPair.objects.filter(generation_status='completed').count()
chunked_qa = TenantKnowledge.objects.filter(chunk_type='faq').values('source_id').distinct().count()
print(f"QA Coverage: {chunked_qa}/{completed_qa}")
```

### **Check Celery Queue:**
```bash
docker compose exec celery_worker celery -A core inspect active
docker compose exec celery_worker celery -A core inspect reserved
```

---

## 🚨 **Troubleshooting**

### **Chunks Not Created:**
1. Check Celery worker logs:
   ```bash
   docker compose logs celery_worker --tail 200 | grep chunk_
   ```
2. Check if signals are registered:
   ```bash
   docker compose exec web python -c "import AI_model.signals; print('Signals loaded')"
   ```

### **Orphaned Chunks:**
- Run reconciliation manually:
  ```bash
  docker compose exec web python manage.py reconcile_knowledge_base
  ```

### **Missing Embeddings:**
- Check OpenAI API key in settings
- Check reconciliation logs for regeneration attempts

---

## ⚙️ **Configuration**

### **Celery Beat Schedule:**
Edit `src/core/celery.py`:
```python
app.conf.beat_schedule = {
    'reconcile-knowledge-base-nightly': {
        'task': 'AI_model.tasks.reconcile_knowledge_base_task',
        'schedule': 60 * 60 * 24,  # Every 24 hours
    },
}
```

### **Debounce Delays:**
Edit `src/AI_model/signals.py`:
```python
# Example: Increase QAPair countdown from 5s to 10s
chunk_qapair_async.apply_async(args=[str(instance.id)], countdown=10)
```

---

## 📦 **Files Modified/Created**

| **File**                                              | **Status** | **Purpose**                          |
|-------------------------------------------------------|------------|--------------------------------------|
| `src/AI_model/signals.py`                             | ✅ Updated | Signal handlers for auto-chunking    |
| `src/AI_model/tasks.py`                               | ✅ Updated | Chunking tasks + reconciliation      |
| `src/AI_model/services/incremental_chunker.py`        | ✅ Created | Single-item chunking logic           |
| `src/AI_model/management/commands/reconcile_knowledge_base.py` | ✅ Created | Nightly reconciliation command       |
| `src/core/celery.py`                                  | ✅ Updated | Celery Beat schedule                 |
| `src/requirements/base.txt`                           | ✅ Updated | Added `django-model-utils`           |

---

## 🎯 **Benefits**

| **Feature**                | **Benefit**                                                                 |
|----------------------------|-----------------------------------------------------------------------------|
| **Real-Time Updates**      | Users see changes in AI responses within 10s                                |
| **Fault Tolerance**        | Nightly reconciliation catches missed signals                               |
| **Idempotency**            | Safe to re-run tasks without duplicates                                     |
| **Scalability**            | Async tasks prevent blocking the web server                                 |
| **Visibility**             | Django admin + management commands for debugging                            |

---

## 🔮 **Future Enhancements**

1. **FieldTracker**: Use `django-model-utils` to detect specific field changes (e.g., only chunk if `question` or `answer` changed, not just `updated_at`)
2. **Batch Chunking**: Group multiple small changes into a single batch task
3. **Priority Queue**: High-priority users get chunked first
4. **Health Checks**: Expose `/api/chunking-health/` endpoint for monitoring

---

## ✅ **Status**

- ✅ Real-time signals implemented
- ✅ Async chunking tasks created
- ✅ Nightly reconciliation scheduled
- ✅ Delete cleanup handlers added
- ✅ Documentation complete

**Next Steps:**
1. Deploy to server
2. Monitor Celery logs for 24 hours
3. Verify nightly reconciliation runs successfully
4. Add FieldTracker for fine-grained change detection (optional)

---

**Last Updated:** October 7, 2025  
**Author:** Fiko AI Backend Team

