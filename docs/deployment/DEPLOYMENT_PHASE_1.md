# 🚀 Deployment راهنمای فاز 1: Database Models

## ✅ تغییرات انجام شده در کد:

1. ✅ `docker-compose.yml` - اضافه شدن pgvector config
2. ✅ `src/requirements/base.txt` - اضافه شدن pgvector + tiktoken
3. ✅ `src/AI_model/models.py` - 4 model جدید:
   - `TenantKnowledge` (vector store)
   - `SessionMemory` (rolling summaries)
   - `IntentKeyword` (optional)
   - `IntentRouting` (optional)
4. ✅ `src/AI_model/admin.py` - Admin panels برای models جدید

---

## 📋 دستورات اجرایی (به ترتیب)

### **Step 1: Commit تغییرات**

```bash
cd /path/to/Fiko-Backend

git status

# باید این فایل‌ها رو ببینید:
# modified:   docker-compose.yml
# modified:   src/requirements/base.txt
# modified:   src/AI_model/models.py
# modified:   src/AI_model/admin.py

git add docker-compose.yml
git add src/requirements/base.txt
git add src/AI_model/models.py
git add src/AI_model/admin.py

git commit -m "feat(AI): Add Lean RAG v2.1 database models

- Add TenantKnowledge model for vector store (pgvector)
- Add SessionMemory model for rolling summaries
- Add IntentKeyword and IntentRouting models for dynamic routing
- Configure PostgreSQL for pgvector extension
- Add pgvector and tiktoken to requirements"

git push origin main
```

---

### **Step 2: در سرور - Pull تغییرات**

```bash
ssh user@your-server

cd /path/to/Fiko-Backend

git pull origin main
```

---

### **Step 3: Restart PostgreSQL با config جدید**

```bash
# بررسی container ها
docker compose ps

# Restart PostgreSQL با shared_preload_libraries جدید
docker compose restart db

# صبر کنید تا PostgreSQL up بشه (5-10 ثانیه)
sleep 10

# تست: بررسی config
docker compose exec db psql -U postgres -c "SHOW shared_preload_libraries;"
# باید 'vector' رو نشون بده ✅
```

---

### **Step 4: نصب pgvector extension**

```bash
# ورود به PostgreSQL
docker compose exec db psql -U postgres -d YOUR_DB_NAME

# در psql:
CREATE EXTENSION IF NOT EXISTS vector;

# تست:
SELECT * FROM pg_extension WHERE extname = 'vector';
# باید 1 row برگردونه ✅

# خروج:
\q
```

---

### **Step 5: نصب Python packages جدید**

```bash
# نصب pgvector و tiktoken
docker compose exec web pip install pgvector==0.3.6 tiktoken==0.8.0

# یا rebuild کامل (بهتر):
docker compose build web

# Restart services
docker compose restart web celery_worker celery_beat
```

---

### **Step 6: تست import pgvector**

```bash
docker compose exec web python manage.py shell

# در Python shell:
>>> from pgvector.django import VectorField, CosineDistance
>>> print("pgvector imported successfully! ✅")
>>> exit()
```

---

### **Step 7: ساخت migrations**

```bash
docker compose exec web python manage.py makemigrations AI_model

# خروجی باید شبیه این باشه:
# Migrations for 'AI_model':
#   AI_model/migrations/0003_tenantknowledge_sessionmemory_intentkeyword_intentrouting.py
#     - Create model TenantKnowledge
#     - Create model SessionMemory
#     - Create model IntentKeyword
#     - Create model IntentRouting
```

---

### **Step 8: بررسی SQL migration (اختیاری ولی توصیه می‌شه)**

```bash
docker compose exec web python manage.py sqlmigrate AI_model 0003

# باید CREATE TABLE commands رو ببینید
# و vector fields به صورت vector(3072) ساخته بشن
```

---

### **Step 9: اجرای migrations**

```bash
docker compose exec web python manage.py migrate AI_model

# خروجی موفق:
# Running migrations:
#   Applying AI_model.0003_tenantknowledge_sessionmemory_intentkeyword_intentrouting... OK ✅
```

---

### **Step 10: ساخت vector index (CRITICAL!)**

```bash
# ورود به PostgreSQL
docker compose exec db psql -U postgres -d YOUR_DB_NAME

# ساخت index برای tldr_embedding
CREATE INDEX idx_tenant_knowledge_tldr_embedding 
ON tenant_knowledge 
USING ivfflat (tldr_embedding vector_cosine_ops) 
WITH (lists = 100);

# ساخت index برای full_embedding (optional)
CREATE INDEX idx_tenant_knowledge_full_embedding 
ON tenant_knowledge 
USING ivfflat (full_embedding vector_cosine_ops) 
WITH (lists = 100);

# تست: بررسی indexes
\d tenant_knowledge

# باید indexes رو ببینید ✅

# خروج:
\q
```

---

### **Step 11: تست models در Django shell**

```bash
docker compose exec web python manage.py shell
```

```python
from AI_model.models import TenantKnowledge, SessionMemory
from accounts.models import User

# Test 1: Import models
print("Models imported successfully! ✅")

# Test 2: Check database tables
from django.db import connection
cursor = connection.cursor()
cursor.execute("""
    SELECT table_name 
    FROM information_schema.tables 
    WHERE table_name IN ('tenant_knowledge', 'session_memory', 'intent_keywords', 'intent_routing')
""")
tables = cursor.fetchall()
print(f"Tables created: {tables}")  # باید 4 جدول رو ببینید ✅

# Test 3: Create a test chunk
user = User.objects.first()
if user:
    chunk = TenantKnowledge.objects.create(
        user=user,
        chunk_type='faq',
        full_text='این یک تست است',
        tldr='تست',
        language='fa',
        word_count=4
    )
    print(f"Test chunk created: {chunk.id} ✅")
    
    # Cleanup
    chunk.delete()
    print("Test chunk deleted ✅")

print("\n🎉 فاز 1 با موفقیت complete شد!")
```

---

## ✅ Checklist تکمیل فاز 1:

```
☐ docker-compose.yml updated با shared_preload_libraries
☐ PostgreSQL restarted
☐ pgvector extension نصب شد
☐ pgvector و tiktoken packages نصب شدند
☐ migrations ساخته شدند
☐ migrations اجرا شدند
☐ vector indexes ساخته شدند
☐ تست models موفق بود
```

---

## 🔍 Troubleshooting

### خطا: "CREATE EXTENSION vector" failed

**علت:** shared_preload_libraries درست config نشده

**راه حل:**
```bash
# چک کردن config
docker compose exec db psql -U postgres -c "SHOW shared_preload_libraries;"

# اگر 'vector' نبود:
docker compose exec db bash
echo "shared_preload_libraries = 'vector'" >> /var/lib/postgresql/data/postgresql.conf
exit

docker compose restart db
```

---

### خطا: "pgvector not found" در Python

**راه حل:**
```bash
# مطمئن شوید package نصب شده:
docker compose exec web pip list | grep pgvector

# اگر نبود:
docker compose exec web pip install pgvector==0.3.6
```

---

### خطا: Migration failed

**راه حل:**
```bash
# Check migration files
ls -la src/AI_model/migrations/

# اگر 0003 وجود نداره:
docker compose exec web python manage.py makemigrations AI_model --empty

# بعد دوباره بزنید:
docker compose exec web python manage.py makemigrations AI_model
docker compose exec web python manage.py migrate AI_model
```

---

## ⏭️ بعد از تکمیل فاز 1:

بهم خبر بدید تا **فاز 2: Services** رو شروع کنم! 🚀

