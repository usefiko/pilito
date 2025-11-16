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

### دو حفره پیدا شده:

#### حفره 1: No workflows triggered
```python
# در src/workflow/tasks.py - خط 385
success = call_ai_fallback_task(message_id, event_log.conversation_id)
# این برای همه message ها (حتی share) AI را صدا می‌زد!
```

#### حفره 2: Workflows triggered but didn't reply  
```python
# در src/workflow/tasks.py - خط 308
if not workflow_replied and trigger_message_id:
    cache.set(f"ai_force_{trigger_message_id}", True, timeout=30)
    process_ai_response_async.delay(trigger_message_id)
# حتی اگر trigger_message یک share بود، AI را force می‌کرد!
```

### لاگ تأییدکننده:
```log
celery_worker | Called AI fallback for message Me7ofp  # share message!
celery_worker | Called AI fallback for message bWbE6s  # share message!
```

## ✅ راه‌حل

### Fix 1: در بخش "No workflows triggered" (خط 376-408)

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

### Fix 2: در بخش "Workflows triggered but didn't reply" (خط 307-332)

```python
# If workflows did not send a reply, trigger AI now for the original message
if not workflow_replied and trigger_message_id:
    try:
        # ✅ Check if message is Instagram share (skip forced AI)
        is_instagram_share = False
        try:
            MessageModel = get_model_class('MESSAGE')
            msg = MessageModel.objects.get(id=trigger_message_id)
            is_instagram_share = (
                hasattr(msg, 'message_type') and
                hasattr(msg.conversation, 'source') and
                msg.conversation.source == 'instagram' and
                msg.message_type == 'share'
            )
        except Exception as _me:
            logger.debug(f"Unable to load trigger message {trigger_message_id} for forced AI decision: {_me}")
        
        if is_instagram_share:
            logger.info(f"🎯 Skipping forced AI for Instagram share message {trigger_message_id} (waiting for follow-up question)")
        else:
            cache.set(f"ai_force_{trigger_message_id}", True, timeout=30)
            from AI_model.tasks import process_ai_response_async
            process_ai_response_async.delay(trigger_message_id)
            logger.info(f"🎯 Forced AI processing for message {trigger_message_id} after workflows completed")
    except Exception as _fe:
        logger.warning(f"Failed to force AI processing post-workflow: {_fe}")
```

## 🎯 نتیجه - سه لایه دفاعی

حالا Instagram share از **سه جهت** محافظت می‌شود:

1. ✅ **Signal** (`signals.py`): روی share، AI auto-trigger نمی‌شود
2. ✅ **Workflow Fallback** (no workflows): share را می‌فهمد و AI را skip می‌کند
3. ✅ **Post-Workflow Force**: روی share دوباره AI را مجبور نمی‌کند

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
2. Share → workflow trigger (no reply) → 1 جواب بدون context ❌

**بعد از fix**:
1. Share → هیچ جوابی ❌
2. Share → workflow trigger (no reply) → هیچ جوابی ❌
3. Text بعد از share → 1 جواب با context ✅

## 📊 لاگ مورد انتظار

### سناریو 1: Share بدون workflow
```log
[INFO] AI fallback skipped for message xxx: Instagram share (waiting for follow-up question)
[INFO] ⏳ Instagram share detected - waiting for follow-up question
```

### سناریو 2: Share + workflow (no reply)
```log
[INFO] 🎯 Skipping forced AI for Instagram share message xxx (waiting for follow-up question)
```

### سناریو 3: Share + Text
```log
[INFO] ⏳ Instagram share detected - waiting for follow-up question
[INFO] ✅ Combined share + question for AI processing
```

---

**تاریخ**: 2025-11-16  
**مشکل**: Double AI response برای share + Missing guard in post-workflow force  
**Status**: ✅ Fixed (2 holes patched)


