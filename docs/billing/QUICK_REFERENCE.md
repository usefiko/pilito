# AI Access Control - Quick Reference

## ✅ Implementation Complete

Users **CANNOT** use Gemini AI if they have:
- ❌ No remaining tokens (tokens_remaining <= 0)
- ❌ Expired subscription (past end_date)
- ❌ Inactive subscription (is_active = False)
- ❌ No subscription at all

## Protected Features

All 7 Gemini AI usage points are now protected:

| Feature | Location | Estimated Tokens | Behavior When Denied |
|---------|----------|------------------|---------------------|
| Ask Question API | `AI_model/views.py` | 1500 | HTTP 402 response |
| Prompt Enhancement API | `web_knowledge/views.py` | 700 | HTTP 402 response |
| Async Prompt Enhancement | `web_knowledge/tasks.py` | 700 | Task fails with error |
| Product Extraction | `web_knowledge/services/product_extractor.py` | 1000 | Returns empty list |
| Voice Transcription | `AI_model/services/media_processor.py` | 500 | Returns error dict |
| Image Analysis | `AI_model/services/media_processor.py` | 800 | Returns error dict |
| Chat AI | `AI_model/services/message_integration.py` | 1500 | Returns processed=False |

## How to Use

### In Your Code

```python
from billing.utils import check_ai_access_for_user

# Check access
access_check = check_ai_access_for_user(
    user=request.user,
    estimated_tokens=1000,
    feature_name="My Feature"
)

if not access_check['has_access']:
    # Access denied - handle error
    return Response({
        'error': access_check['message'],
        'error_code': access_check['reason']
    }, status=402)

# Access granted - proceed with AI
```

## Error Codes

| Code | Meaning |
|------|---------|
| `no_subscription` | User has no subscription |
| `subscription_deactivated` | Subscription is_active = False |
| `no_tokens_remaining` | tokens_remaining = 0 |
| `subscription_expired` | Past end_date |
| `insufficient_tokens` | Not enough tokens |

## Testing

### Quick Test
```bash
python manage.py shell < docs/billing/test_ai_access_control.py
```

### Manual Test
```python
# In Django shell
from django.contrib.auth import get_user_model
User = get_user_model()

user = User.objects.first()
user.subscription.tokens_remaining = 0
user.subscription.save()

# Now try any AI feature - should be denied
```

## Files Modified

1. ✅ `src/billing/utils.py` - NEW (validation function)
2. ✅ `src/AI_model/views.py` - Ask Question API
3. ✅ `src/web_knowledge/views.py` - Prompt Enhancement API
4. ✅ `src/web_knowledge/tasks.py` - Async task
5. ✅ `src/web_knowledge/services/product_extractor.py` - Product extraction
6. ✅ `src/AI_model/services/media_processor.py` - Voice/Image processing
7. ✅ `src/message/tasks.py` - Media tasks
8. ✅ `src/message/tasks_instagram_media.py` - Instagram media tasks

## Documentation

- 📖 **Full Docs:** `docs/billing/AI_ACCESS_CONTROL.md`
- 📝 **Summary:** `docs/billing/AI_ACCESS_CONTROL_SUMMARY.md`
- 🧪 **Test Script:** `docs/billing/test_ai_access_control.py`
- ⚡ **Quick Ref:** `docs/billing/QUICK_REFERENCE.md` (this file)

## Status

✅ **Implementation Complete**
✅ **No Linter Errors**
✅ **Backward Compatible**
✅ **Ready for Testing**

---
Last Updated: November 1, 2025

