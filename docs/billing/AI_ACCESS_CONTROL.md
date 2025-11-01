# AI Access Control Implementation

## Overview

This document describes the implementation of AI access control based on user subscription status, remaining tokens, and days remaining.

## Requirements

Users should NOT be able to use Gemini AI in any part of the system if they have:
1. No active subscription
2. No remaining tokens (tokens_remaining <= 0)
3. Expired subscription (past end_date)

## Implementation

### Centralized Validation Function

Location: `src/billing/utils.py`

```python
def check_ai_access_for_user(user, estimated_tokens: int = 0, feature_name: str = "AI") -> Dict[str, Any]
```

This function validates:
1. User has an active subscription
2. Subscription is not expired (end_date check)
3. User has remaining tokens (> 0)
4. User has enough tokens for the estimated usage

**Returns:**
```python
{
    'has_access': bool,          # Whether user can access AI
    'reason': str,                # Reason code if access denied
    'message': str,               # Human-readable message
    'tokens_remaining': int,      # Current tokens remaining
    'days_remaining': int|None    # Days until subscription expires
}
```

**Reason Codes:**
- `no_subscription`: User has no subscription record
- `subscription_deactivated`: Subscription is_active flag is False
- `no_tokens_remaining`: tokens_remaining is 0 or None
- `subscription_expired`: Current date is past end_date
- `insufficient_tokens`: tokens_remaining < estimated_tokens

## Protected AI Features

All Gemini AI usage points are now protected with access checks:

### 1. Ask Question API
**Location:** `src/AI_model/views.py` - `AskQuestionAPIView`
- **Estimated Tokens:** 1500
- **Feature Name:** "Ask Question"
- **Response:** HTTP 402 Payment Required if access denied

### 2. Prompt Enhancement API
**Location:** `src/web_knowledge/views.py` - `GeneratePromptAPIView`
- **Estimated Tokens:** 700
- **Feature Name:** "Prompt Enhancement"
- **Response:** HTTP 402 Payment Required if access denied

### 3. Async Prompt Enhancement Task
**Location:** `src/web_knowledge/tasks.py` - `generate_prompt_async_task`
- **Estimated Tokens:** 700
- **Feature Name:** "Async Prompt Enhancement"
- **Behavior:** Task fails with error message in cache

### 4. Product Extraction
**Location:** `src/web_knowledge/services/product_extractor.py` - `ProductExtractor.extract_products_ai()`
- **Estimated Tokens:** 1000
- **Feature Name:** "Product Extraction"
- **Behavior:** Returns empty list if access denied

### 5. Voice Transcription
**Location:** `src/AI_model/services/media_processor.py` - `MediaProcessorService.process_voice()`
- **Estimated Tokens:** 500
- **Feature Name:** "Voice Transcription"
- **Behavior:** Returns error dict with access denied message

### 6. Image Analysis
**Location:** `src/AI_model/services/media_processor.py` - `MediaProcessorService.process_image()`
- **Estimated Tokens:** 800
- **Feature Name:** "Image Analysis"
- **Behavior:** Returns error dict with access denied message

### 7. Chat Message Processing (Already Protected)
**Location:** `src/AI_model/services/message_integration.py` - `MessageSystemIntegration.process_new_customer_message()`
- **Minimum Tokens:** 1500
- **Feature Name:** "AI Chat"
- **Behavior:** Returns dict with processed=False

## Usage Examples

### API Response When Access Denied

```json
{
  "success": false,
  "error": "No tokens remaining in subscription",
  "error_code": "no_tokens_remaining",
  "tokens_remaining": 0,
  "days_remaining": 15
}
```

### Checking Access in Code

```python
from billing.utils import check_ai_access_for_user

# Check if user can access AI
access_check = check_ai_access_for_user(
    user=request.user,
    estimated_tokens=1000,
    feature_name="My AI Feature"
)

if not access_check['has_access']:
    # Handle access denied
    return Response({
        'error': access_check['message'],
        'error_code': access_check['reason'],
        'tokens_remaining': access_check['tokens_remaining'],
        'days_remaining': access_check['days_remaining']
    }, status=status.HTTP_402_PAYMENT_REQUIRED)

# Proceed with AI operation
```

## Testing

To test the implementation:

1. **Create a test user with expired subscription:**
   ```python
   from django.utils import timezone
   from datetime import timedelta
   
   user.subscription.end_date = timezone.now() - timedelta(days=1)
   user.subscription.save()
   ```

2. **Create a test user with no tokens:**
   ```python
   user.subscription.tokens_remaining = 0
   user.subscription.save()
   ```

3. **Test each AI endpoint:**
   - POST /api/ai/ask-question/
   - POST /api/web-knowledge/generate-prompt/
   - Try uploading voice/image messages
   - Try product extraction
   - Try chat with AI

4. **Verify responses:**
   - All should return HTTP 402 or appropriate error
   - Error messages should be clear
   - tokens_remaining and days_remaining should be included

## Frontend Integration

The frontend should:

1. **Display token/subscription status prominently**
2. **Disable AI features when access is denied**
3. **Show clear upgrade/renewal prompts**
4. **Handle HTTP 402 responses gracefully**

Example frontend check:
```javascript
if (response.status === 402) {
  // Show upgrade modal
  showUpgradeModal({
    message: response.data.error,
    tokensRemaining: response.data.tokens_remaining,
    daysRemaining: response.data.days_remaining
  });
}
```

## Monitoring

Key metrics to monitor:
- Number of denied AI requests per day
- Reason codes distribution
- Users hitting token limits
- Users with expired subscriptions attempting AI usage

## Future Enhancements

1. **Grace Period:** Allow limited AI usage for X days after expiration
2. **Soft Limits:** Warn users when tokens are low (e.g., < 10%)
3. **Feature-Specific Limits:** Different token costs for different features
4. **Token Packages:** Allow users to purchase additional tokens
5. **Usage Analytics:** Show users their AI usage patterns

## Related Files

- `src/billing/utils.py` - Centralized access control
- `src/billing/models.py` - Subscription model with `is_subscription_active()`
- `src/AI_model/services/message_integration.py` - Chat AI access control
- `src/AI_model/views.py` - Ask Question API
- `src/web_knowledge/views.py` - Prompt Enhancement API
- `src/web_knowledge/tasks.py` - Async Prompt Enhancement
- `src/web_knowledge/services/product_extractor.py` - Product Extraction
- `src/AI_model/services/media_processor.py` - Voice/Image Processing

## Migration Notes

This implementation does NOT require database migrations. It only adds validation logic before AI operations.

## Backward Compatibility

- Existing AI operations continue to work for users with active subscriptions
- No breaking changes to API responses (only adds new fields)
- MediaProcessorService now accepts optional `user` parameter (backward compatible)

## Security Considerations

1. **Server-Side Validation:** All checks are performed server-side
2. **No Client Bypass:** Frontend cannot bypass token checks
3. **Consistent Enforcement:** All AI endpoints use the same validation logic
4. **Audit Trail:** All denied requests are logged with user info and reason

