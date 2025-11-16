# Instagram Share Feature - Bug Fix: Double Response

## 🐛 مشکل

بعد از پیاده‌سازی اولیه، کاربر گزارش کرد که سیستم **2 بار** به share جواب می‌دهد:
- یک بار اشتباه (بدون context)
- یک بار درست (با context از share)

## 🔍 علت

از بررسی لاگ‌ها مشخص شد:

### Timeline مشکل:
1. **Signal** (`AI_model/signals.py`): برای share return می‌کرد و AI را trigger نمی‌کرد ✅
2. **Workflow** (`workflow/tasks.py`): "AI fallback" برای share هم صدا می‌شد ❌

### کد مشکل‌دار:
```python
# در src/workflow/tasks.py - خط 385
success = call_ai_fallback_task(message_id, event_log.conversation_id)
# این برای همه message ها (حتی share) AI را صدا می‌زد!
```

### لاگ تأییدکننده:
```log
celery_worker | Called AI fallback for message Me7ofp  # share message!
celery_worker | Called AI fallback for message bWbE6s  # share message!
```

## ✅ راه‌حل

در `src/workflow/tasks.py` - خط 376-408، یک check اضافه شد:

```python
# ✅ Check if message is a share (waiting for follow-up)
try:
    msg = Message.objects.get(id=message_id)
    if (hasattr(msg, 'message_type') and 
        hasattr(msg.conversation, 'source') and
        msg.conversation.source == 'instagram' and 
        msg.message_type == 'share'):
        logger.info(f"AI fallback skipped for message {message_id}: Instagram share (waiting for follow-up question)")
        # Skip AI fallback for share - handled by signals.py delay logic
        pass
    else:
        # Normal AI fallback logic...
        cache.set(cache_key, True, timeout=300)
        success = call_ai_fallback_task(message_id, event_log.conversation_id)
        # ...
except Message.DoesNotExist:
    logger.warning(f"Message {message_id} not found, skipping AI fallback")
```

## 🎯 نتیجه

- ✅ Signal (`signals.py`): برای share return می‌کند
- ✅ Workflow (`workflow/tasks.py`): برای share AI fallback را skip می‌کند
- ✅ فقط 1 بار جواب می‌دهد (بعد از text + combine)

## 🚀 Deploy

```bash
git pull origin main
docker stack deploy -c docker-compose.swarm.yml pilito
# یا
systemctl restart celery-worker
```

## 🧪 تست

**قبل از fix**:
1. Share → 2 جواب (یکی بدون context، یکی با context)

**بعد از fix**:
1. Share → هیچ جوابی ❌
2. Text بعد از share → 1 جواب با context ✅

## 📊 لاگ مورد انتظار

```log
[INFO] AI fallback skipped for message xxx: Instagram share (waiting for follow-up question)
[INFO] ⏳ Instagram share detected - waiting for follow-up question
[INFO] ✅ Combined share + question for AI processing
```

---

**تاریخ**: 2025-11-16  
**مشکل**: Double AI response برای share  
**Status**: ✅ Fixed

