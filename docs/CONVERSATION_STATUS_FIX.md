# Conversation Status Fix - فقط در ایجاد تنظیم شود

## ❌ **مشکل قبلی:**

### **کد قبلی (اشتباه):**
```python
# در telegram_webhook.py و insta.py
conversation, conv_created = Conversation.objects.update_or_create(
    user=bot_user,
    source='telegram', 
    customer=customer,
    defaults={'status': initial_status}  # ❌ این هر بار status را تغییر می‌داد!
)
```

### **رفتار اشتباه:**
- ❌ **هر بار که پیام جدید می‌آمد، status تغییر می‌کرد**
- ❌ اگر کاربر status را دستی تغییر می‌داد، پیام بعدی آن را برمی‌گرداند
- ❌ `update_or_create` با `defaults` همیشه مقادیر defaults را اعمال می‌کند

---

## ✅ **راه‌حل درست:**

### **کد جدید (درست):**
```python
# Get or create Conversation - only set status on creation
try:
    # Try to get existing conversation first
    conversation = Conversation.objects.get(
        user=bot_user,
        source='telegram', 
        customer=customer
    )
    conv_created = False
    logger.info(f"Found existing conversation: {conversation} with status: {conversation.status}")
    
except Conversation.DoesNotExist:
    # Create new conversation with initial status
    from AI_model.utils import get_initial_conversation_status
    
    # Determine initial status based on user's default_reply_handler (only for new conversations)
    initial_status = get_initial_conversation_status(bot_user)
    
    conversation = Conversation.objects.create(
        user=bot_user,
        source='telegram', 
        customer=customer,
        status=initial_status  # ✅ فقط در ایجاد status تنظیم می‌شود
    )
    conv_created = True
    
    # Log the initial status for new conversation
    from AI_model.utils import log_conversation_status_change
    log_conversation_status_change(conversation, 'new', initial_status, 
                                 f"Initial status based on user's default_reply_handler: {bot_user.default_reply_handler}")
    logger.info(f"Created new conversation: {conversation} with initial status: {initial_status}")

# Always update conversation's updated_at field
conversation.save(update_fields=['updated_at'])  # ✅ فقط updated_at تغییر می‌کند
```

---

## 🎯 **رفتار درست جدید:**

### **1. اولین پیام (ایجاد Conversation):**
```python
# اگر Conversation وجود نداشته باشد:
if user.default_reply_handler == 'AI':
    status = 'active'     # ✅ هوش مصنوعی پاسخ می‌دهد
else:
    status = 'support_active'  # ✅ دستی/پشتیبانی پاسخ می‌دهد
```

### **2. پیام‌های بعدی:**
```python
# اگر Conversation موجود باشد:
# ✅ status تغییر نمی‌کند
# ✅ فقط updated_at به‌روزرسانی می‌شود
# ✅ پیام جدید ایجاد می‌شود
```

### **3. تغییر دستی status:**
```python
# اگر کاربر status را دستی تغییر دهد:
conversation.status = 'closed'  # یا هر status دیگری
conversation.save()

# پیام‌های بعدی status را تغییر نمی‌دهند ✅
```

---

## 📁 **فایل‌های تغییر یافته:**

### **1. Telegram Webhook:**
- **File:** `src/message/telegram_bot/telegram_webhook.py`
- **Lines:** 66-98

### **2. Instagram Webhook:**
- **File:** `src/message/insta.py`  
- **Lines:** 517-549

### **3. Test Command:**
- **File:** `src/message/management/commands/test_conversation_status_behavior.py`
- **تست کامل رفتار**

---

## 🧪 **تست کردن:**

```bash
# تست رفتار conversation status
python manage.py test_conversation_status_behavior
```

### **تست‌های انجام شده:**
1. ✅ **ایجاد conversation جدید** → status بر اساس default_reply_handler تنظیم می‌شود
2. ✅ **پیام دوم** → status تغییر نمی‌کند
3. ✅ **تغییر دستی status** → در پیام‌های بعدی حفظ می‌شود
4. ✅ **رفتار AI** → فقط وقتی که status=active پاسخ می‌دهد

---

## 🔄 **جریان کامل:**

### **سناریو 1: کاربر با AI**
```
User.default_reply_handler = 'AI'

1. اولین پیام → Conversation ایجاد با status='active'
2. پیام دوم → status همچنان 'active' 
3. AI پاسخ می‌دهد ✅
4. کاربر status را 'closed' می‌کند
5. پیام سوم → status همچنان 'closed'
6. AI پاسخ نمی‌دهد ✅
```

### **سناریو 2: کاربر دستی**
```
User.default_reply_handler = 'Manual'

1. اولین پیام → Conversation ایجاد با status='support_active'
2. پیام دوم → status همچنان 'support_active'
3. AI پاسخ نمی‌دهد ✅
4. کاربر status را 'active' می‌کند
5. پیام سوم → status همچنان 'active'
6. AI پاسخ می‌دهد ✅
```

---

## 🎯 **نتیجه:**

### ✅ **مزایای راه‌حل جدید:**
1. **Status فقط در ایجاد تنظیم می‌شود**
2. **تغییرات دستی کاربر حفظ می‌شوند**
3. **رفتار قابل پیش‌بینی و منطقی**
4. **کنترل کامل کاربر بر روی conversation**

### 🔄 **تغییرات کلیدی:**
- **جایگزینی `update_or_create`** با منطق `get` + `create`
- **حذف `defaults` که status را تغییر می‌داد**
- **افزودن logging بهتر**
- **تست جامع رفتار**

**حالا conversation status فقط یکبار در ایجاد تنظیم می‌شود و دیگر تغییر نمی‌کند! 🎉**