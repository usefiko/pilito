# Days Remaining Fix - Prevent Negative Values

## Issue
The `days_left` field in the UserOverview API was showing negative values like `-1` or `-4` when subscriptions had expired, instead of showing `0`.

## Root Cause
The `Subscription.days_remaining()` method was calling `days_left_from_now()` which calculates the difference between the end date and current date. When the end date has passed, this calculation returns negative values.

## Solution
Modified the `days_remaining()` method in the `Subscription` model to return `0` when the subscription has expired (instead of negative values).

---

## Code Changes

### File: `src/billing/models.py`

**Before:**
```python
def days_remaining(self):
    """
    Calculate days remaining in subscription
    """
    if not self.end_date:
        return None  # Unlimited
    return days_left_from_now(self.end_date)
```

**After:**
```python
def days_remaining(self):
    """
    Calculate days remaining in subscription
    Returns 0 if expired, None if unlimited
    """
    if not self.end_date:
        return None  # Unlimited
    days_left = days_left_from_now(self.end_date)
    return max(0, days_left)  # Return 0 if negative (expired)
```

---

## Impact

### API Responses

#### Before (with bug):
```json
{
  "current_subscription": {
    "days_remaining": -4,  // ❌ Negative value
    "end_date": "2025-10-30T00:00:00Z",
    "is_active": false
  }
}
```

#### After (fixed):
```json
{
  "current_subscription": {
    "days_remaining": 0,  // ✅ Shows 0 when expired
    "end_date": "2025-10-30T00:00:00Z",
    "is_active": false
  }
}
```

---

## Affected Endpoints

This fix affects all endpoints that return subscription information:

1. **`GET /api/v1/usr/overview`** - UserOverview API
   - Field: `current_subscription.days_remaining`

2. **`GET /api/v1/billing/subscription/`** - Current Subscription
   - Field: `days_remaining`

3. **`GET /api/v1/billing/overview/`** - Billing Overview
   - Field: `current_subscription.days_remaining`

4. Any custom endpoints using `SubscriptionSerializer`

---

## Return Values

The `days_remaining()` method now returns:

| Scenario | Return Value |
|----------|--------------|
| Subscription has not expired | Positive integer (e.g., `5`, `30`) |
| Subscription expired today | `0` |
| Subscription expired in the past | `0` (not negative) |
| Unlimited subscription (no end_date) | `None` |
| No subscription | N/A (Exception) |

---

## Behavior Examples

```python
# Example 1: Active subscription
subscription.end_date = timezone.now() + timedelta(days=5)
subscription.days_remaining()  # Returns: 5 ✅

# Example 2: Expires today
subscription.end_date = timezone.now()
subscription.days_remaining()  # Returns: 0 ✅

# Example 3: Expired 4 days ago
subscription.end_date = timezone.now() - timedelta(days=4)
subscription.days_remaining()  # Returns: 0 ✅ (was -4 before)

# Example 4: Unlimited subscription
subscription.end_date = None
subscription.days_remaining()  # Returns: None ✅
```

---

## Related Functions

These functions were already handling negative values correctly but now benefit from the fix at the source:

### 1. `free_trial_days_left_for_user()` (billing/utils.py)
```python
days_left = subscription.days_remaining()
return max(0, days_left) if days_left is not None else 0
```
- Already had `max(0, days_left)` as a safety net
- Now receives `0` instead of negative values

### 2. `get_subscription_remaining()` (UserOverviewSerializer)
```python
days_remaining = subscription.days_remaining()
percentage = (days_remaining / total_days) * 100
return max(0, min(100, round(percentage, 1)))
```
- Already had percentage boundary checks
- Now calculates percentage from `0` instead of negative values

---

## Testing

### Manual Testing
```bash
# 1. Check user with expired subscription
curl -X GET "http://localhost:8000/api/v1/usr/overview" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Expected: days_remaining should be 0, not negative
```

### Django Shell Testing
```python
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta

User = get_user_model()
user = User.objects.first()
subscription = user.subscription

# Test expired subscription
subscription.end_date = timezone.now() - timedelta(days=4)
subscription.save()

print(subscription.days_remaining())  # Should print: 0 (not -4)
```

---

## Benefits

✅ **Consistent UI/UX**: Frontend doesn't need to handle negative days  
✅ **Cleaner Logic**: `if days_remaining > 0` works correctly  
✅ **Better Semantics**: 0 days = expired (not negative days)  
✅ **Fewer Edge Cases**: No need to check for negative values everywhere  

---

## Notes

- The underlying `days_left_from_now()` utility function still returns negative values (for other use cases), but the `days_remaining()` method now normalizes it to 0
- This is a non-breaking change - all existing code continues to work
- No database migration needed - this is a pure logic change

---

*Fixed on: November 3, 2025*

