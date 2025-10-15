# 🚀 Lean RAG v2.1 - راهنمای استقرار

## مراحل استقرار

### ✅ فاز 1 و 2: تکمیل شده
- ✅ Database models
- ✅ pgvector setup
- ✅ Core services
- ✅ Migrations

---

### 📦 فاز 3: Populate Knowledge Base

#### **مرحله 1: Sync کردن فایل‌های جدید**

```bash
cd /home/ubuntu/fiko-backend
git pull origin main  # اگر از git استفاده می‌کنید
```

**یا** فایل‌های جدید رو manually کپی کنید:
- `src/AI_model/services/knowledge_ingestion_service.py`
- `src/AI_model/management/commands/populate_knowledge_base.py`
- `test_lean_rag_e2e.py`

#### **مرحله 2: Restart کردن Services**

```bash
docker compose restart web celery_worker celery_beat
```

#### **مرحله 3: Populate کردن Knowledge Base**

**برای یک کاربر خاص:**
```bash
docker compose exec web python manage.py populate_knowledge_base --user <username>
```

**برای همه کاربران:**
```bash
docker compose exec web python manage.py populate_knowledge_base --all-users
```

**با force recreate (حذف و ساخت مجدد):**
```bash
docker compose exec web python manage.py populate_knowledge_base --user <username> --force
```

**فقط منابع خاص:**
```bash
docker compose exec web python manage.py populate_knowledge_base --user <username> --sources faq products
```

#### **مرحله 4: Verify Knowledge Base**

```bash
docker compose exec web python manage.py shell
```

```python
from AI_model.models import TenantKnowledge
from django.contrib.auth import get_user_model

User = get_user_model()
user = User.objects.get(username='<username>')

# Check chunk counts
print(f"FAQ: {TenantKnowledge.objects.filter(user=user, chunk_type='faq').count()}")
print(f"Products: {TenantKnowledge.objects.filter(user=user, chunk_type='product').count()}")
print(f"Manual: {TenantKnowledge.objects.filter(user=user, chunk_type='manual').count()}")
print(f"Website: {TenantKnowledge.objects.filter(user=user, chunk_type='website').count()}")
print(f"Total: {TenantKnowledge.objects.filter(user=user).count()}")

exit()
```

---

### 🧪 تست End-to-End

```bash
docker compose exec web python /app/test_lean_rag_e2e.py
```

این script تست می‌کنه:
1. ✅ Knowledge Ingestion
2. ✅ Query Routing (Intent Detection)
3. ✅ Context Retrieval (pgvector RAG)
4. ✅ Token Budget Control
5. ✅ Gemini Service Integration

---

### 📊 Monitoring در Production

#### **1. Check Token Usage:**

```bash
docker compose exec web python manage.py shell
```

```python
from AI_model.models import AIUsageTracking
from django.contrib.auth import get_user_model
from datetime import date

User = get_user_model()
user = User.objects.get(username='<username>')

# Today's usage
usage = AIUsageTracking.objects.filter(user=user, date=date.today()).first()
if usage:
    print(f"Total requests: {usage.total_requests}")
    print(f"Avg tokens/request: {usage.average_tokens_per_request:.0f}")
    print(f"Total cost: ${usage.estimated_total_cost:.4f}")

exit()
```

#### **2. Check Logs:**

```bash
# Web logs (Lean RAG logs)
docker compose logs web --tail 100 | grep -E "🎯|📚|📊|✅"

# Check for errors
docker compose logs web --tail 200 | grep -E "ERROR|❌"
```

#### **3. Monitor Performance:**

```python
# In Django shell
from AI_model.services.context_retriever import ContextRetriever

# Check knowledge stats
stats = ContextRetriever.preload_user_knowledge(user)
print(stats)
```

---

### ⚙️ تنظیمات (اختیاری)

#### **1. تغییر Token Budgets:**

فایل: `src/AI_model/services/token_budget_controller.py`

```python
BUDGET = {
    'system_prompt': 250,      # افزایش/کاهش دهید
    'conversation': 400,        # بیشتر برای conversation طولانی
    'primary_context': 650,     # بیشتر برای context بیشتر
    'secondary_context': 200,
}
```

بعد از تغییر:
```bash
docker compose restart web
```

#### **2. تنظیم Intent Keywords:**

از Django Admin:
1. برو به: `/admin/AI_model/intentkeyword/`
2. کلمات کلیدی جدید اضافه کن
3. وزن (weight) رو تنظیم کن (0.1-3.0)
4. برای user خاص یا global

Cache به صورت خودکار بعد از 1 ساعت refresh میشه.

#### **3. تنظیم Routing Rules:**

از Django Admin:
1. برو به: `/admin/AI_model/intentrouting/`
2. Intent رو انتخاب کن (pricing, product, howto, contact, general)
3. Primary/Secondary sources رو تنظیم کن
4. Token budgets رو تنظیم کن

---

### 🔧 Troubleshooting

#### **مشکل: "No chunks retrieved"**

```bash
# Check if embeddings are generated
docker compose exec db psql -U FikoUsr -d FikoDB -c "SELECT COUNT(*) FROM tenant_knowledge WHERE tldr_embedding IS NOT NULL;"
```

اگر 0 بود:
1. Check embedding service logs
2. Verify OpenAI API key in settings
3. Re-run populate command with --force

#### **مشکل: "Token count exceeds 1500"**

```python
# Reduce budgets in token_budget_controller.py
BUDGET = {
    'system_prompt': 200,      # کاهش از 250
    'conversation': 300,        # کاهش از 400
    'primary_context': 700,     # افزایش (اینجا مهمه!)
    'secondary_context': 150,   # کاهش از 200
}
```

#### **مشکل: "Gemini API errors"**

```bash
# Check API key
docker compose exec web python manage.py shell
```

```python
from settings.models import GeneralSettings
settings = GeneralSettings.get_settings()
print(f"API Key exists: {bool(settings.gemini_api_key)}")
print(f"API Key length: {len(settings.gemini_api_key or '')}")
exit()
```

---

### 📈 بهینه‌سازی Performance

#### **1. Index Optimization:**

بعد از populate، اگر data زیاد شد:

```bash
docker compose exec db psql -U FikoUsr -d FikoDB
```

```sql
-- Rebuild indexes با lists بیشتر
DROP INDEX idx_tenant_knowledge_tldr_embedding;
DROP INDEX idx_tenant_knowledge_full_embedding;

CREATE INDEX idx_tenant_knowledge_tldr_embedding 
ON tenant_knowledge 
USING ivfflat (tldr_embedding vector_cosine_ops) 
WITH (lists = 500);  -- 100 → 500 برای data بیشتر

CREATE INDEX idx_tenant_knowledge_full_embedding 
ON tenant_knowledge 
USING ivfflat (full_embedding vector_cosine_ops) 
WITH (lists = 500);

\q
```

#### **2. Redis Caching:**

Cache به صورت پیش‌فرض فعاله برای:
- Intent keywords (1 hour)
- Intent routing config (1 hour)
- Session memories (1 hour)
- Knowledge stats (1 hour)

برای clear کردن cache:
```bash
docker compose exec redis_cache redis-cli FLUSHDB
```

---

### 🎯 نکات مهم برای Production

1. **⚠️ همیشه از `text-embedding-3-small` استفاده کنید** (1536 dimensions)
2. **🔄 Rolling Summary:** هر 5 پیام یکبار update میشه (REPLACE نه APPEND)
3. **📊 Token Counting:** tiktoken برای دقت بالا استفاده میشه
4. **🗄️ Knowledge Base:** باید منظم update بشه (هر بار که FAQ/Product/Website تغییر کرد)
5. **📉 Cost Monitoring:** روزانه `AIUsageTracking` رو check کنید

---

### 🔄 Update کردن Knowledge Base

**وقتی FAQ/Products/Website تغییر می‌کنه:**

```bash
# Option 1: Update specific source
docker compose exec web python manage.py populate_knowledge_base --user <username> --sources faq --force

# Option 2: Incremental (فقط جدیدها اضافه میشه)
docker compose exec web python manage.py populate_knowledge_base --user <username>

# Option 3: Full recreate
docker compose exec web python manage.py populate_knowledge_base --user <username> --force
```

**Scheduled Update (با Celery):**

می‌تونید یک Celery task بنویسید که شبانه knowledge base رو update کنه:

```python
# در AI_model/tasks.py
from celery import shared_task

@shared_task
def update_knowledge_base_nightly():
    from django.contrib.auth import get_user_model
    from AI_model.services.knowledge_ingestion_service import KnowledgeIngestionService
    
    User = get_user_model()
    for user in User.objects.filter(is_active=True):
        KnowledgeIngestionService.ingest_user_knowledge(
            user=user,
            force_recreate=True
        )
```

---

## ✅ Checklist قبل از Production

- [ ] همه migrations اجرا شدن
- [ ] pgvector extension فعاله
- [ ] Vector indexes ساخته شدن
- [ ] Knowledge base برای test user populate شده
- [ ] End-to-end test موفق بود
- [ ] Token usage < 1500 تایید شده
- [ ] Gemini API key تنظیم شده
- [ ] Logs بررسی شدن (بدون error)
- [ ] Django admin accessible
- [ ] Redis cache کار می‌کنه
- [ ] Monitoring راه‌اندازی شده

---

## 🆘 پشتیبانی

برای مشکلات:
1. Check logs: `docker compose logs web --tail 200`
2. Check database: `docker compose exec db psql -U FikoUsr -d FikoDB`
3. Run test script: `docker compose exec web python /app/test_lean_rag_e2e.py`
4. Check این فایل: `CRITICAL_EMBEDDING_DIMENSIONS.md`

---

**🎉 موفق باشید!**

