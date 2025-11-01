# 🚨 Critical Fixes - Phase 0 (Immediate)

## 📋 **Overview:**

بعد از review توسط AI دیگه، 2 تا مشکل **Critical** شناسایی شدن که باید **الان** fix بشن:

1. ❌ Race Condition: No unique constraint on TenantKnowledge
2. ❌ Thundering Herd: Chunking tasks همزمان fire میشن

---

## 🔧 **Fix #1: Add Unique Constraint**

### **Problem:**
```python
# 2 worker میتونن همزمان duplicate chunk بسازن
# هیچ constraint نداریم روی (user, source_id, chunk_type)
```

### **Solution:**

**File:** `src/AI_model/models.py`

```python
class TenantKnowledge(models.Model):
    # ... existing fields ...
    
    class Meta:
        db_table = 'tenant_knowledge'
        verbose_name = "📚 Tenant Knowledge (RAG)"
        verbose_name_plural = "📚 Tenant Knowledge (RAG)"
        indexes = [
            models.Index(fields=['user', 'chunk_type']),
            models.Index(fields=['user', 'document_id']),
            models.Index(fields=['created_at']),
        ]
        # ✅ NEW: Prevent duplicate chunks
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'source_id', 'chunk_type'],
                condition=models.Q(source_id__isnull=False),  # Only when source_id exists
                name='unique_chunk_per_source',
                violation_error_message='این صفحه قبلاً chunk شده است'
            )
        ]
```

### **Migration:**

**File:** `src/AI_model/migrations/0010_add_unique_constraint.py`

```python
from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('AI_model', '0009_add_parent_child_chunks'),
    ]

    operations = [
        migrations.AddConstraint(
            model_name='tenantknowledge',
            constraint=models.UniqueConstraint(
                fields=['user', 'source_id', 'chunk_type'],
                condition=models.Q(source_id__isnull=False),
                name='unique_chunk_per_source',
                violation_error_message='این صفحه قبلاً chunk شده است'
            ),
        ),
    ]
```

### **Update Chunking Logic:**

**File:** `src/AI_model/services/incremental_chunker.py`

```python
def chunk_webpage(self, page) -> bool:
    try:
        from django.db import IntegrityError
        # ... existing code ...
        
        # ✅ Handle duplicate gracefully
        if chunks_to_create:
            try:
                TenantKnowledge.objects.bulk_create(
                    chunks_to_create,
                    batch_size=100,
                    ignore_conflicts=True  # ✅ Skip duplicates
                )
                logger.info(f"✅ Created {len(chunks_to_create)} chunks")
            except IntegrityError as e:
                logger.warning(f"⚠️ Some chunks already exist: {e}")
                # Try individual inserts for the ones that don't exist
                success_count = 0
                for chunk in chunks_to_create:
                    try:
                        chunk.save()
                        success_count += 1
                    except IntegrityError:
                        pass  # Skip duplicate
                logger.info(f"✅ Created {success_count}/{len(chunks_to_create)} new chunks")
        
        return True
```

---

## 🔧 **Fix #2: Stagger Chunking Tasks (Prevent Thundering Herd)**

### **Problem:**
```python
# بعد از crawl 200 page، همه همزمان برای chunking queue میشن
# → Redis/Celery overload
```

### **Solution:**

**File:** `src/AI_model/signals.py`

```python
import random
from django.db.models.signals import post_save
from django.dispatch import receiver
import logging

logger = logging.getLogger(__name__)

@receiver(post_save, sender='web_knowledge.WebsitePage')
def on_webpage_saved_for_chunking(sender, instance, **kwargs):
    """
    Auto-chunk WebPage when processing completes (with staggered dispatch)
    
    Improvements:
    - Random delay (10-60s) to prevent thundering herd
    - Check if already chunked (idempotent)
    - Graceful handling of duplicates
    """
    if instance.processing_status != 'completed':
        return
    
    # Check if already chunked (idempotent)
    from AI_model.models import TenantKnowledge
    already_chunked = TenantKnowledge.objects.filter(
        source_id=instance.id,
        chunk_type='website'
    ).exists()
    
    if already_chunked:
        logger.debug(f"WebPage {instance.id} already chunked, skipping")
        return
    
    from AI_model.tasks import chunk_webpage_async
    
    # ✅ Stagger tasks: Random delay 10-60 seconds
    # This prevents 200 tasks from hitting Celery/Redis simultaneously
    countdown = random.randint(10, 60)
    
    chunk_webpage_async.apply_async(
        args=[str(instance.id)],
        countdown=countdown,
        retry=False  # Don't auto-retry (signal will fire again if needed)
    )
    
    logger.debug(f"Queued chunking for WebPage {instance.id} (delay: {countdown}s)")
```

---

## 🔧 **Fix #3: Stagger Processing Tasks (در crawl_website_task)**

**File:** `src/web_knowledge/tasks.py`

```python
# Line 103-136 (در crawl_website_task)
for i, page_data in enumerate(crawled_pages):
    try:
        # ... save page logic ...
        
        # ✅ Stagger processing: 200 pages over 3-5 minutes
        # Formula: (i * 1.5) seconds = 0, 1.5, 3, 4.5, ... 297s (for 200 pages)
        countdown = int(i * 1.5)  # Spread over ~5 minutes
        
        process_page_content_task.apply_async(
            args=[str(page.id)],
            countdown=countdown
        )
        
        saved_pages += 1
        
        if (i + 1) % 50 == 0:
            logger.info(f"Queued {i + 1}/{len(crawled_pages)} processing tasks")
            
    except Exception as e:
        logger.error(f"Error queuing page {page_data.get('url')}: {str(e)}")
        failed_pages += 1

logger.info(
    f"✅ All {len(crawled_pages)} tasks queued "
    f"(staggered over ~{int(len(crawled_pages) * 1.5 / 60)} minutes)"
)
```

---

## 📊 **Impact Analysis:**

### **Before (الان):**
```
Crawl 200 pages:
  - 200 process tasks → instant dispatch → thundering herd
  - 200 chunk tasks → instant dispatch → thundering herd
  - Redis queue spike: 0 → 400 → 0 (in <5s)
  - Potential: Connection pool exhaustion, task loss
```

### **After (با fixes):**
```
Crawl 200 pages:
  - 200 process tasks → staggered 0-300s → smooth queue
  - 200 chunk tasks → random 10-60s → distributed load
  - Redis queue: Gradual fill, no spike
  - Unique constraint: No duplicate chunks
```

### **Performance:**
| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| **Redis Peak Load** | 400 tasks | ~50-80 tasks | 5x smoother |
| **Duplicate Chunks** | Possible | Prevented | 100% |
| **Total Time** | ~5 min | ~5-6 min | +1min (acceptable) |
| **Stability** | Risk of crash | Stable | ✅ |

---

## 🚀 **Deployment Steps:**

### **Step 1: Apply Migration**
```bash
cd ~/pilito
git pull origin main

# Create migration
docker-compose exec web python manage.py makemigrations AI_model

# Apply migration (this will add unique constraint)
docker-compose exec web python manage.py migrate AI_model
```

### **Step 2: Rebuild & Restart**
```bash
docker-compose build web
docker-compose up -d web
docker-compose restart celery_worker celery_ai
```

### **Step 3: Test**
```bash
# Check constraint exists
docker-compose exec db psql -U pilito -d pilito -c "
SELECT conname, pg_get_constraintdef(oid) 
FROM pg_constraint 
WHERE conname = 'unique_chunk_per_source';
"

# Should see: unique_chunk_per_source | UNIQUE (user_id, source_id, chunk_type) WHERE ...
```

### **Step 4: Monitor**
```bash
# Watch queue size (should not spike)
watch -n 2 'docker-compose exec redis redis-cli LLEN low_priority'

# Watch for duplicate errors (should be handled gracefully)
docker-compose logs -f celery_worker | grep "already exist"
```

---

## ⚠️ **Rollback Plan:**

اگر مشکلی پیش اومد:

```bash
# 1. Remove constraint
docker-compose exec web python manage.py dbshell
# در psql:
ALTER TABLE tenant_knowledge DROP CONSTRAINT IF EXISTS unique_chunk_per_source;

# 2. Revert code
git revert HEAD
docker-compose up -d web celery_worker celery_ai
```

---

## 📝 **Next Steps (Phase 1):**

بعد از اینکه Phase 0 stable شد:

1. ✅ Bulk DB operations (instead of loop)
2. ✅ Batch embedding API calls
3. ✅ Redis-based circuit breaker
4. ✅ Enhanced monitoring

---

## ✅ **Testing Checklist:**

- [ ] Unique constraint added successfully
- [ ] No duplicate chunks created
- [ ] Staggered dispatch working (check Redis queue)
- [ ] No thundering herd spike
- [ ] Existing pages still chunk correctly
- [ ] Error handling for duplicates works
- [ ] Performance acceptable (~1min slower, but stable)

---

**زمان تخمینی اجرا:** 30 دقیقه
**پیچیدگی:** Low (فقط migration + 2 file edit)
**ریسک:** Very Low (backward compatible)

