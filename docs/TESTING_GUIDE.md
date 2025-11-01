# 🧪 راهنمای تست سیستم Chunking و RAG

این فایل راهنمای **تست کامل** سیستم چانکینگ و RAG برای کاربر `Faracoach` است.

---

## 📋 **ترتیب تست:**

```
1️⃣ پاک کردن chunks قدیمی (Fresh Start)
   ↓
2️⃣ تست Manual Prompt Chunking
   ↓
3️⃣ تست Query Answering (RAG)
   ↓
4️⃣ تست Website Crawling
   ↓
5️⃣ تست نهایی Query با Website + Manual
```

---

## 🚀 **قدم به قدم:**

### **قدم 1: پاک کردن همه Chunks (Fresh Start)**

```bash
# در سرور:
cd /root/pilito
chmod +x clean_faracoach_chunks.sh
./clean_faracoach_chunks.sh
```

**نتیجه مورد انتظار:**
```
✅ Deleted X chunks for user: Faracoach
🎉 All chunks deleted successfully! Fresh start ready!
```

---

### **قدم 2: تست Manual Prompt Chunking**

#### **2.1. در Django Admin:**
```
1. برو به: https://api.pilito.com/admin/settings/aiprompts/
2. Manual Prompt رو باز کن
3. متن 1500-15000 کلمه‌ای رو Paste کن (مثلاً محتوای بورسیه)
4. Save کن
```

#### **2.2. تست Chunking:**
```bash
# در سرور (بعد از Save کردن):
cd /root/pilito
chmod +x test_manual_prompt.sh
./test_manual_prompt.sh
```

**نتیجه مورد انتظار:**
```
✅ Found 48 manual chunks!
📊 Chunk Statistics:
   Total chunks: 48
   Total words: 15000
   Avg words per chunk: 312

🔢 Embeddings:
   TL;DR embedding: ✅ Yes
   Full embedding: ✅ Yes
   Dimensions: 1536 (should be 1536 for OpenAI)

🎉 Manual prompt chunking successful!
```

---

### **قدم 3: تست Query Answering (RAG)**

```bash
# در سرور:
cd /root/pilito
chmod +x test_query_answer.sh
./test_query_answer.sh
```

**نتیجه مورد انتظار:**
```
🎯 STEP 1: Intent Classification
Intent: product
Confidence: 85%
Primary source: products
Keywords matched: ['بورسیه']

🔍 STEP 2: Embedding Generation
✅ Query embedding generated: 1536 dimensions

📚 STEP 3: Hybrid Search
Available chunks: 48 (manual: 48)
Retrieved chunks: 5

🎯 Top 3 Results:
1. Score: 0.923
   Title: Manual Prompt - Part 5
   TL;DR: بورسیه بر اساس بررسی سوابق...

✅ RAG is working!
```

#### **3.2. تست در UI:**
```
1. برو به chat interface
2. سوال بپرس: "بورسیه دارین؟"
3. AI باید از manual prompt استفاده کنه و جواب دقیق بده
```

---

### **قدم 4: تست Website Crawling**

#### **4.1. شروع Crawl در UI:**
```
1. برو به: Knowledge Base → Websites
2. Add Website: https://faracoach.com
3. Max Pages: 50
4. Start Crawl
```

#### **4.2. چک کردن Progress:**
```bash
# در سرور:
cd /root/pilito
chmod +x test_website_crawl.sh
./test_website_crawl.sh

# یا مستقیم logs:
docker logs -f celery_worker | grep -E "Crawled|progress|Chunked"
```

**نتیجه مورد انتظار:**
```
✅ Found website: Faracoach Website
   Status: crawling
   Progress: 45.0%
   Pages crawled: 22/50

📄 Pages Crawled:
   Total: 22
   Completed: 22

📦 Chunks Created:
   Total chunks: 156
   Avg words per chunk: 420

🛍️  Products Extracted: 8
```

#### **4.3. بعد از Complete شدن Crawl:**
```bash
# دوباره test_website_crawl.sh رو بزن
./test_website_crawl.sh
```

**نتیجه:**
```
✅ Crawl completed!
📦 Chunks Created: 200+
🛍️  Products Extracted: 15+
🎉 Website crawl & chunking successful!
```

---

### **قدم 5: تست نهایی - Query با ترکیب Manual + Website**

```bash
# تست query answering با هر دو source
./test_query_answer.sh
```

**سوالات تست پیشنهادی:**

```
✅ تست Manual Prompt:
   - "بورسیه دارین؟"
   - "شرایط بورسیه چیه؟"

✅ تست Website:
   - "قیمت دوره کوچینگ چنده؟"
   - "دوره های شما چیه؟"

✅ تست Product:
   - "محصولاتتون رو بگو"
   - "چه دوره‌هایی دارین؟"
```

---

## 🔍 **دستورات مفید برای Debug:**

### **1. چک کردن تعداد Chunks:**
```bash
docker-compose exec -T web python manage.py shell <<'PYTHON'
from AI_model.models import TenantKnowledge
from django.contrib.auth import get_user_model

User = get_user_model()
user = User.objects.get(username='Faracoach')

stats = {
    'manual': TenantKnowledge.objects.filter(user=user, chunk_type='manual').count(),
    'website': TenantKnowledge.objects.filter(user=user, chunk_type='website').count(),
    'product': TenantKnowledge.objects.filter(user=user, chunk_type='product').count(),
    'faq': TenantKnowledge.objects.filter(user=user, chunk_type='faq').count(),
}

total = sum(stats.values())
print(f"Total: {total}")
for k, v in stats.items():
    if v > 0:
        print(f"  {k}: {v}")
PYTHON
```

### **2. چک کردن Celery Worker:**
```bash
# Is celery running?
docker-compose ps celery_worker

# Recent logs
docker logs celery_worker --tail 100

# Follow logs
docker logs -f celery_worker
```

### **3. چک کردن Embeddings:**
```bash
docker-compose exec -T web python manage.py shell <<'PYTHON'
from AI_model.models import TenantKnowledge
from django.contrib.auth import get_user_model

User = get_user_model()
user = User.objects.get(username='Faracoach')

chunks = TenantKnowledge.objects.filter(user=user)[:10]

for chunk in chunks:
    has_full = chunk.full_embedding is not None
    has_tldr = chunk.tldr_embedding is not None
    
    if has_full:
        import numpy as np
        dims = len(np.array(chunk.full_embedding))
        print(f"✅ {chunk.section_title[:40]}: {dims} dims")
    else:
        print(f"❌ {chunk.section_title[:40]}: No embedding")
PYTHON
```

### **4. چک کردن Website Crawl Progress:**
```bash
docker logs celery_worker --tail 100 | grep -E "Crawl progress|Crawled:"
```

### **5. چک کردن Q&A Generation (باید disabled باشه):**
```bash
docker logs celery_worker --tail 500 | grep -i "generate_qa_pairs_task"

# اگه چیزی نشون نداد = خوبه (disabled شده)
# اگه نشون داد = هنوز enable هست
```

---

## 📊 **انتظارات:**

### **Manual Prompt (15000 کلمه):**
- ⏱️ زمان: ~40 ثانیه
- 📦 Chunks: ~48 تا
- 💰 Token: ~48K
- ✅ Quality: عالی (Persian-aware)

### **Website Crawl (50 صفحه):**
- ⏱️ زمان: ~5 دقیقه
- 📦 Chunks: ~200-300 تا
- 💰 Token: ~50K
- 🛍️ Products: 10-20 محصول
- ✅ Quality: عالی

### **Query Answering:**
- ⏱️ زمان: 2-3 ثانیه
- 🎯 Accuracy: 90%+
- 📚 Sources: Manual + Website + Products
- ✅ Quality: عالی (Persian-optimized)

---

## ❌ **مشکلات احتمالی:**

### **1. Chunks ساخته نمیشه:**
```bash
# Check celery worker
docker-compose ps celery_worker

# Restart if needed
docker-compose restart celery_worker

# Check logs
docker logs celery_worker --tail 100
```

### **2. Embeddings ساخته نمیشه:**
```bash
# Check OpenAI API key
docker-compose exec web python manage.py shell <<'PYTHON'
from settings.models import GeneralSettings
gs = GeneralSettings.get_solo()
print(f"OpenAI Key: {gs.openai_api_key[:10]}...")
PYTHON

# Check proxy
docker logs celery_worker | grep -i "proxy\|openai"
```

### **3. Query جواب نمیده:**
```bash
# Check chunks exist
docker-compose exec web python manage.py shell <<'PYTHON'
from AI_model.models import TenantKnowledge
from django.contrib.auth import get_user_model
User = get_user_model()
user = User.objects.get(username='Faracoach')
print(f"Total chunks: {TenantKnowledge.objects.filter(user=user).count()}")
PYTHON

# Check hybrid retriever
docker logs celery_worker | grep -i "hybrid search"
```

---

## ✅ **Success Criteria:**

✓ Chunks created for manual prompt (48+)  
✓ Chunks created for website (200+)  
✓ Embeddings generated (1536 dims)  
✓ Intent classification working (confidence 80%+)  
✓ Hybrid search returning results (3-10 chunks)  
✓ Query answering accurate (matches manual prompt)  
✓ Products extracted (10+ products)  
✓ Q&A generation disabled (no auto Q&A)  

---

## 🎉 **بعد از موفقیت آمیز بودن تست:**

1. ✅ System آماده production است
2. ✅ Persian chunking کار میکنه
3. ✅ RAG دقیق جواب میده
4. ✅ Token consumption کاهش یافته (70%+)
5. ✅ Speed بهبود یافته (3x faster)

---

**موفق باشی!** 🚀

