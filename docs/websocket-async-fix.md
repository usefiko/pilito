# WebSocket Async/Sync Context Fix

## Problem
The error you were seeing:
```
message.middleware.websocket_auth ERROR    Error authenticating WebSocket token: You cannot call this from an async context - use a thread or sync_to_async.
```

This occurs when synchronous database or cache operations are called from an async context in Django Channels.

## Root Cause
In `src/message/middleware/websocket_auth.py`, the following synchronous operations were being called from async methods:

1. **Database operations**: `User.objects.get(id=user_id)`
2. **Cache operations**: `cache.get()`, `cache.set()`, `cache.has_key()`  
3. **JWT operations**: `validate_token()`, `claim_token()` (which internally use cache)

## Solution Applied

### 1. Added Required Import
```python
from channels.db import database_sync_to_async
```

### 2. Wrapped Synchronous Operations

**JWT Functions:**
```python
# Before (causing async/sync error)
if not validate_token(token, check_time=check_cache):
    return None
payload = claim_token(token)

# After (async-safe)
is_valid = await database_sync_to_async(validate_token)(token, check_time=check_cache)
if not is_valid:
    return None
payload = await database_sync_to_async(claim_token)(token)
```

**Database Operations:**
```python
# Before (causing async/sync error)
user = User.objects.get(id=user_id)

# After (async-safe)
user = await database_sync_to_async(User.objects.get)(id=user_id)
```

**Cache Operations:**
```python
# Before (potentially problematic)
connections = cache.get(cache_key, [])
cache.set(cache_key, connections, timeout=window_seconds)

# After (async-safe)
connections = await database_sync_to_async(cache.get)(cache_key, [])
await database_sync_to_async(cache.set)(cache_key, connections, timeout=window_seconds)
```

## Files Modified

1. **`src/message/middleware/websocket_auth.py`**:
   - Added `database_sync_to_async` import
   - Wrapped all synchronous operations in `get_user_from_token()`
   - Wrapped cache operations in `check_rate_limit()`
   - Wrapped cache operations in `is_ip_blacklisted()`
   - Added documentation for utility functions

## Testing the Fix

### 1. Check Logs After Restart
After restarting your Django development server, you should no longer see:
```
message.middleware.websocket_auth ERROR    Error authenticating WebSocket token: You cannot call this from an async context
```

### 2. WebSocket Connection Test
Your WebSocket connections to `/ws/customers/` and `/ws/conversations/` should now work without async/sync context errors.

### 3. Expected Log Behavior
You should now see (if any auth issues exist):
```
message.middleware.websocket_auth DEBUG    Token validation failed for token: eyJhbGciOiJIUzUxMiIs...
message.middleware.websocket_auth DEBUG    Development mode: Allowing connection with invalid token
```

Instead of the ERROR level async context messages.

## Performance Impact

The fix adds minimal overhead:
- `database_sync_to_async` creates a thread pool for sync operations
- JWT validation and database lookups are already relatively fast operations
- Cache operations are wrapped but remain efficient
- No change to the actual authentication logic

## Additional Notes

### Utility Functions
The IP blacklist utility functions (`blacklist_ip`, `whitelist_ip`) remain synchronous but are documented for proper async usage:

```python
# For async contexts, use:
await database_sync_to_async(blacklist_ip)(ip, duration_hours)
await database_sync_to_async(whitelist_ip)(ip)
```

### JWT Function Compatibility
The JWT functions (`validate_token`, `claim_token`) were not modified as they are used throughout the codebase in synchronous contexts. The async wrapper is applied only in the WebSocket middleware.

## Potential Future Improvements

1. **Async-native JWT library**: Consider using an async-native JWT library for better performance
2. **Async cache backend**: Use an async-compatible cache backend like `django-redis` with async support
3. **Connection pooling**: For high-traffic scenarios, consider optimizing the database connection pooling

## Troubleshooting

If you still see async/sync errors:

1. **Check for other synchronous operations** in your WebSocket consumers
2. **Verify Django Channels version** - ensure you're using a compatible version
3. **Check custom middleware** - ensure any custom middleware follows async patterns
4. **Review JWT configuration** - ensure JWT functions don't have hidden synchronous dependencies

The fix addresses the core async/sync context issue in your WebSocket authentication middleware.