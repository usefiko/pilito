# Affiliate Response Fix for Registration API

## Issue
When users register with an affiliate code via the `api/v1/usr/register` endpoint, the response was not showing correct or complete affiliate information. The affiliate code was being processed in the backend, but the response didn't reflect:
1. Whether the affiliate code was successfully applied
2. Information about the referrer
3. The user's own invite code and affiliate fields

## Root Cause
The issue was in the response serializer. While the `RegisterSerializer` was correctly processing affiliate codes and updating the database, the `UserShortSerializer` (used to return user data) was not including affiliate-related fields in its output.

## Changes Made

### 1. Updated `UserShortSerializer` (`src/accounts/serializers/user.py`)

#### Added affiliate fields to the response:
- `invite_code` - The user's own unique invite code (auto-generated)
- `referred_by` - The ID of the user who referred them
- `referrer_username` - The username of the referrer (via SerializerMethodField)
- `affiliate_active` - Whether the user has affiliate system enabled
- `wallet_balance` - The user's current wallet balance

#### Added helper method:
```python
def get_referrer_username(self, obj):
    """Get the username of the user who referred this user"""
    if obj.referred_by:
        return obj.referred_by.username
    return None
```

### 2. Enhanced `RegisterSerializer` (`src/accounts/serializers/register.py`)

#### Improved affiliate code processing:
- Added tracking of whether affiliate code was successfully applied
- Added referrer information to the response
- Added error messages for invalid affiliate codes
- Registration still succeeds even if affiliate code is invalid

#### New response structure includes `affiliate_info` when an affiliate code is provided:
```json
{
  "refresh_token": "...",
  "access_token": "...",
  "user_data": {
    "id": 123,
    "username": "newuser",
    "email": "user@example.com",
    "invite_code": "1234",
    "referred_by": 456,
    "referrer_username": "referrer_user",
    "affiliate_active": false,
    "wallet_balance": "0.00",
    ...other fields...
  },
  "email_confirmation_sent": true,
  "message": "Registration successful! Please check your email for confirmation code.",
  "affiliate_info": {
    "affiliate_code_provided": "5678",
    "affiliate_applied": true,
    "referrer": {
      "id": 456,
      "username": "referrer_user",
      "invite_code": "5678"
    },
    "error": null
  }
}
```

## Response Scenarios

### Scenario 1: Registration with valid affiliate code
```json
{
  "user_data": {
    "invite_code": "1234",
    "referred_by": 456,
    "referrer_username": "referrer_user",
    "wallet_balance": "0.00",
    ...
  },
  "affiliate_info": {
    "affiliate_code_provided": "5678",
    "affiliate_applied": true,
    "referrer": {
      "id": 456,
      "username": "referrer_user",
      "invite_code": "5678"
    },
    "error": null
  }
}
```

### Scenario 2: Registration with invalid affiliate code
```json
{
  "user_data": {
    "invite_code": "1234",
    "referred_by": null,
    "referrer_username": null,
    "wallet_balance": "0.00",
    ...
  },
  "affiliate_info": {
    "affiliate_code_provided": "9999",
    "affiliate_applied": false,
    "referrer": null,
    "error": "Invalid affiliate code"
  }
}
```

### Scenario 3: Registration without affiliate code
```json
{
  "user_data": {
    "invite_code": "1234",
    "referred_by": null,
    "referrer_username": null,
    "wallet_balance": "0.00",
    ...
  }
  // No affiliate_info field
}
```

## Benefits

1. **Complete Transparency**: Frontend can now display whether the affiliate code was successfully applied
2. **Better UX**: Users can see their referrer's information immediately after registration
3. **Error Handling**: Invalid affiliate codes are clearly communicated without failing the registration
4. **Immediate Access**: New users can see their own invite code right after registration
5. **Wallet Tracking**: Users can see their initial wallet balance

## Testing the Changes

### Test 1: Register with valid affiliate code
```bash
curl -X POST http://your-domain/api/v1/usr/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@example.com",
    "password": "SecurePass123!",
    "affiliate": "5678"
  }'
```

### Test 2: Register with invalid affiliate code
```bash
curl -X POST http://your-domain/api/v1/usr/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser2",
    "email": "test2@example.com",
    "password": "SecurePass123!",
    "affiliate": "9999"
  }'
```

### Test 3: Register without affiliate code
```bash
curl -X POST http://your-domain/api/v1/usr/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser3",
    "email": "test3@example.com",
    "password": "SecurePass123!"
  }'
```

## Backend Processing

When a valid affiliate code is provided:
1. The system looks up the user with the matching `invite_code`
2. Sets the new user's `referred_by` field to the referrer
3. Adds $10.00 to the referrer's `wallet_balance`
4. Returns complete information about the referrer and confirmation status

## No Breaking Changes

These changes are **backward compatible**:
- Existing API calls without affiliate codes continue to work
- Only adds new fields to the response, doesn't remove or change existing ones
- Invalid affiliate codes don't cause registration to fail (same as before)

## Files Modified

1. `src/accounts/serializers/user.py`
   - Added affiliate fields to `UserShortSerializer.Meta.fields`
   - Added `get_referrer_username()` method

2. `src/accounts/serializers/register.py`
   - Enhanced affiliate code processing with status tracking
   - Added `affiliate_info` to response data

## Next Steps

Consider adding these enhancements in the future:
1. Add affiliate statistics endpoint to show referral count and earnings
2. Add webhook/notification when a referral registers
3. Add admin panel to manage affiliate relationships
4. Add configurable referral bonus amounts
5. Add affiliate link generator endpoint

