# AI Access Control - Implementation Summary

## What Was Implemented

A comprehensive access control system that prevents users from using Gemini AI features when they have:
- No remaining tokens (tokens_remaining <= 0)
- Expired subscription (past end_date)
- Inactive subscription (is_active = False)
- No subscription at all

## Changes Made

### 1. Created Centralized Validation Function
**File:** `src/billing/utils.py`

New function: `check_ai_access_for_user(user, estimated_tokens, feature_name)`

This function checks:
- ✅ Subscription exists
- ✅ Subscription is active (is_active flag)
- ✅ Subscription not expired (end_date check)
- ✅ Has remaining tokens (tokens_remaining > 0)
- ✅ Has enough tokens for operation (tokens_remaining >= estimated_tokens)

### 2. Protected All AI Features

#### API Endpoints Protected:
1. **Ask Question API** (`src/AI_model/views.py`)
   - Endpoint: `/api/ai/ask-question/`
   - Returns HTTP 402 if access denied

2. **Prompt Enhancement API** (`src/web_knowledge/views.py`)
   - Endpoint: `/api/web-knowledge/generate-prompt/`
   - Returns HTTP 402 if access denied

#### Background Tasks Protected:
3. **Async Prompt Enhancement** (`src/web_knowledge/tasks.py`)
   - Task fails with clear error message

#### AI Services Protected:
4. **Product Extraction** (`src/web_knowledge/services/product_extractor.py`)
   - Returns empty list if access denied

5. **Voice Transcription** (`src/AI_model/services/media_processor.py`)
   - Returns error dict if access denied

6. **Image Analysis** (`src/AI_model/services/media_processor.py`)
   - Returns error dict if access denied

7. **Chat AI** (`src/AI_model/services/message_integration.py`)
   - Already had protection, now uses consistent validation

### 3. Updated Media Processing
**Files:** 
- `src/message/tasks.py`
- `src/message/tasks_instagram_media.py`

Updated `MediaProcessorService` to:
- Accept optional `user` parameter
- Check access before processing voice/image
- Pass user from message conversation

## Files Modified

1. ✅ `src/billing/utils.py` - NEW FILE (centralized validation)
2. ✅ `src/AI_model/views.py` - Added access check to AskQuestionAPIView
3. ✅ `src/web_knowledge/views.py` - Added access check to GeneratePromptAPIView
4. ✅ `src/web_knowledge/tasks.py` - Added access check to generate_prompt_async_task
5. ✅ `src/web_knowledge/services/product_extractor.py` - Added access check to extract_products_ai
6. ✅ `src/AI_model/services/media_processor.py` - Added user parameter and access checks
7. ✅ `src/message/tasks.py` - Pass user to MediaProcessorService
8. ✅ `src/message/tasks_instagram_media.py` - Pass user to MediaProcessorService

## Documentation Created

1. ✅ `docs/billing/AI_ACCESS_CONTROL.md` - Comprehensive documentation
2. ✅ `docs/billing/test_ai_access_control.py` - Test script
3. ✅ `docs/billing/AI_ACCESS_CONTROL_SUMMARY.md` - This file

## Testing

### Manual Testing Steps:

1. **Test with no tokens:**
   ```python
   user.subscription.tokens_remaining = 0
   user.subscription.save()
   # Try any AI feature - should be denied
   ```

2. **Test with expired subscription:**
   ```python
   from django.utils import timezone
   from datetime import timedelta
   user.subscription.end_date = timezone.now() - timedelta(days=1)
   user.subscription.save()
   # Try any AI feature - should be denied
   ```

3. **Test with inactive subscription:**
   ```python
   user.subscription.is_active = False
   user.subscription.save()
   # Try any AI feature - should be denied
   ```

### Automated Test Script:
```bash
python manage.py shell < docs/billing/test_ai_access_control.py
```

## Error Response Format

When access is denied, APIs return:

```json
{
  "success": false,
  "error": "No tokens remaining in subscription",
  "error_code": "no_tokens_remaining",
  "tokens_remaining": 0,
  "days_remaining": 15
}
```

HTTP Status: `402 Payment Required`

## Error Codes

- `no_subscription` - User has no subscription
- `subscription_deactivated` - Subscription is_active is False
- `no_tokens_remaining` - tokens_remaining is 0 or None
- `subscription_expired` - Current date past end_date
- `insufficient_tokens` - Not enough tokens for operation

## Backward Compatibility

✅ **Fully backward compatible:**
- No database migrations required
- Existing API contracts unchanged (only adds fields)
- MediaProcessorService user parameter is optional
- Users with valid subscriptions unaffected

## Security

✅ **Server-side enforcement:**
- All checks performed on backend
- No client-side bypass possible
- Consistent validation across all features
- Comprehensive logging of denied requests

## Monitoring Recommendations

Track these metrics:
1. Number of denied AI requests per day
2. Distribution of denial reasons
3. Users hitting token limits
4. Users attempting AI with expired subscriptions

## Next Steps for Frontend

The frontend should:
1. **Check subscription status** before showing AI features
2. **Handle HTTP 402 responses** gracefully
3. **Show clear upgrade prompts** when access denied
4. **Display token/day counters** prominently
5. **Disable AI buttons** when subscription invalid

Example frontend code:
```javascript
// Check before enabling AI features
if (user.subscription.tokens_remaining <= 0) {
  disableAIFeatures();
  showUpgradePrompt();
}

// Handle API errors
if (response.status === 402) {
  showUpgradeModal({
    message: response.data.error,
    tokensRemaining: response.data.tokens_remaining,
    daysRemaining: response.data.days_remaining
  });
}
```

## Verification Checklist

- ✅ Created centralized validation function
- ✅ Protected all AI API endpoints
- ✅ Protected all AI background tasks
- ✅ Protected all AI services
- ✅ Updated media processing to pass user
- ✅ No linter errors
- ✅ Backward compatible
- ✅ Comprehensive documentation
- ✅ Test script created
- ✅ Error responses include helpful info

## Estimated Token Costs

Reference for different AI operations:
- **Ask Question:** 1500 tokens
- **Prompt Enhancement:** 700 tokens
- **Voice Transcription:** 500 tokens
- **Image Analysis:** 800 tokens
- **Product Extraction:** 1000 tokens
- **Chat Message:** 1500 tokens (minimum)

These are estimates used for pre-validation. Actual usage is tracked separately.

## Support

For questions or issues:
1. Check `docs/billing/AI_ACCESS_CONTROL.md` for detailed documentation
2. Run test script: `python manage.py shell < docs/billing/test_ai_access_control.py`
3. Check logs for denied access attempts
4. Verify subscription status in admin panel

---

**Implementation Date:** November 1, 2025
**Status:** ✅ Complete and Ready for Testing

