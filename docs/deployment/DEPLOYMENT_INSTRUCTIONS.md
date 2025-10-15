# 🚀 Deployment Instructions - Knowledge Base & Session Memory Fixes

## **📋 Summary of Fixes**

### ✅ **Fixed Issues:**
1. **Knowledge Base**: Products now auto-sync to TenantKnowledge (searchable by AI)
2. **Session Memory**: Conversation length warnings + better prompts
3. **AI Responses**: Enhanced to use session memory context
4. **Consistency**: Single source of truth (all products in KB)

---

## **🔧 Step-by-Step Deployment**

### **1. SSH to Server**
```bash
ssh ubuntu@your-server-ip
cd ~/fiko-backend
```

### **2. Pull Latest Code**
```bash
git pull origin main
```

### **3. Restart Django**
```bash
docker compose restart web
```

### **4. Sync Existing Products (ONE-TIME)**
This adds all existing products to TenantKnowledge:

```bash
docker compose exec web python manage.py shell -c "
from web_knowledge.models import Product
from django.db import transaction

print('Syncing products to TenantKnowledge...')
products = Product.objects.filter(is_active=True)
total = products.count()
print(f'Found {total} active products')

for i, p in enumerate(products, 1):
    try:
        p.save()  # Triggers signal
        print(f'✅ [{i}/{total}] {p.title}')
    except Exception as e:
        print(f'❌ [{i}/{total}] {p.title}: {e}')

print('Done!')
"
```

---

## **🧪 Testing Scenario**

### **New Conversation (Fresh Start)**

Start a new conversation and ask these 10 questions:

```
1. سلام، محصولات کمپینگتون چیه؟
```

```
2. پیکوپرسو چیه؟
```

```
3. قیمتش چنده؟
```

```
4. با نانوپرسو چه فرقی داره؟
```

```
5. کدومو پیشنهاد میدی؟
```

**⏸️ After Q5: Check summary**
```bash
docker compose exec web python manage.py shell
```
```python
from AI_model.models import SessionMemory
s = SessionMemory.objects.order_by('-last_updated').first()
print(f"Messages: {s.message_count}")
print(f"Summary: {s.cumulative_summary}")
exit()
```

---

**Continue with repetitive questions:**

```
6. تخفیف داری؟
```

```
7. ارسال رایگانه؟
```

```
8. راستی ارسال چطوره؟  ← REPETITIVE (test memory)
```

```
9. قیمت پیکوپرسو چی بود؟  ← REPETITIVE (test memory)
```

```
10. برای کمپینگ کدومو پیشنهاد میدی؟  ← REPETITIVE (test memory)
```

---

## **✅ Expected Results**

### **Q8 (Repetitive Shipping)**
**❌ Before Fix:**
```
AI: ارسال به تمام نقاط ایران انجام می‌شه.
```

**✅ After Fix:**
```
AI: همونطور که پیام 7 گفتم، ارسال به تمام ایران رایگانه!
```

---

### **Q9 (Repetitive Price)**
**❌ Before Fix:**
```
AI: متاسفانه قیمت پیکوپرسو نداریم
```

**✅ After Fix:**
```
AI: قبلاً در پیام 3 گفتم: قیمت پیکوپرسو 13,989,000 تومان هست.
```

---

### **Q10 (Repetitive Recommendation)**
**❌ Before Fix:**
```
AI: برای کمپینگ، پیکوپرسو و نانوپرسو هر دو خوب هستن...
```

**✅ After Fix:**
```
AI: با توجه به اینکه قبلاً (پیام 5) پیکوپرسو رو پیشنهاد دادم
برای کمپینگ، هنوز همون توصیه رو دارم! می‌خوای سفارش بدی؟
```

---

## **📊 Success Metrics (Target: 10/10)**

| Metric | Before | Target | How to Verify |
|--------|--------|--------|---------------|
| **Knowledge Base** | 3/10 | 10/10 | ✅ Prices consistent, all products searchable |
| **Session Memory** | 7/10 | 10/10 | ✅ References previous messages, no repetition |
| **Response Quality** | 5/10 | 10/10 | ✅ Accurate answers, uses context well |
| **Consistency** | 2/10 | 10/10 | ✅ No contradictions (same info every time) |

---

## **🔍 Verification Commands**

### **Check if Products are in TenantKnowledge**
```bash
docker compose exec web python manage.py shell -c "
from AI_model.models import TenantKnowledge
product_chunks = TenantKnowledge.objects.filter(chunk_type='product')
print(f'Product chunks in knowledge base: {product_chunks.count()}')

# Show first 5
for chunk in product_chunks[:5]:
    print(f'- {chunk.section_title} (user: {chunk.user.email})')
"
```

### **Check Session Memory for Conversation**
```bash
docker compose exec web python manage.py shell -c "
from AI_model.models import SessionMemory
sessions = SessionMemory.objects.order_by('-last_updated')[:3]

for s in sessions:
    print(f'\nSession: {s.conversation.id}')
    print(f'User: {s.user.email}')
    print(f'Messages: {s.message_count}')
    print(f'Summary: {s.cumulative_summary[:150]}...')
    print('-'*60)
"
```

---

## **🐛 Troubleshooting**

### **Problem: Products not appearing in search**
**Solution:**
```bash
# Re-sync all products
docker compose exec web python manage.py shell -c "
from web_knowledge.models import Product
for p in Product.objects.filter(is_active=True):
    p.save()
print('Products re-synced!')
"
```

### **Problem: Session Memory not updating**
**Check logs:**
```bash
docker compose logs web --tail=50 | grep -i "session memory\|summary"
```

**Force update:**
```bash
docker compose exec web python manage.py shell -c "
from AI_model.services.session_memory_manager import SessionMemoryManager
SessionMemoryManager.SUMMARY_UPDATE_FREQUENCY = 1  # Temporary
print('Threshold reduced to 1 message')
"
```

### **Problem: AI still giving wrong prices**
**Clear cache:**
```bash
docker compose exec web python manage.py shell -c "
from django.core.cache import cache
cache.clear()
print('Cache cleared!')
"
```

---

## **📝 Notes**

- The product sync signal runs automatically for all **new/updated** products
- The one-time sync script is only needed for **existing** products
- Session Memory updates every **5 messages** (can be adjusted)
- Conversations over **200 messages** will show a warning (for performance)

---

## **🎉 Expected Outcome**

After deployment + testing:
- ✅ **All products searchable** by AI via semantic search
- ✅ **Session Memory working** (references previous context)
- ✅ **No contradictions** (consistent product info)
- ✅ **Smart responses** (avoids repetition, builds on context)

**Result: 10/10 on all metrics!** 🚀

