# Affiliate Marketing Implementation - Summary

## Overview
Successfully implemented a comprehensive affiliate marketing system in the accounts app. Users can now invite friends and earn rewards when those friends register using their invite code.

## Features Implemented

### 1. User Model Updates
Added three new fields to the User model:
- **invite_code**: A unique 10-character alphanumeric code automatically generated for each user
- **referred_by**: ForeignKey to track which user referred this user
- **wallet_balance**: Decimal field to track earnings from referrals (default: 0.00)

The invite code is automatically generated when a user is created using a custom `save()` method.

### 2. Registration Flow
Updated the registration process to handle affiliate codes:
- Added `affiliate` parameter to RegisterSerializer (optional)
- When a user registers with an affiliate code:
  - The new user is linked to the referrer via `referred_by` field
  - The referrer receives a bonus of 10.00 in their wallet
  - Invalid codes don't block registration (silently ignored)

### 3. Affiliate API Endpoint
Created a new authenticated API endpoint: `/api/v1/accounts/affiliate`

**Response includes:**
```json
{
    "invite_link": "https://app.pilito.com/auth/register?affiliate=ABC123XYZ0",
    "invite_code": "ABC123XYZ0",
    "direct_referrals": [
        {
            "id": 123,
            "username": "john_doe",
            "email": "john@example.com",
            "first_name": "John",
            "last_name": "Doe",
            "created_at": "2025-11-25T10:30:00Z"
        }
    ],
    "total_referrals": 5,
    "wallet_balance": "50.00"
}
```

### 4. Admin Panel Updates
Enhanced the Django admin panel with:
- Display of invite_code and wallet_balance in user list
- New "Referral Count" column showing number of direct referrals
- New "Affiliate Marketing" fieldset with:
  - Invite code (read-only)
  - Referred by (editable)
  - Wallet balance (editable)
  - Referral list showing all users referred by this user
- Search capability by invite_code

## Files Modified/Created

### Created:
1. `src/accounts/migrations/0015_add_affiliate_fields.py` - Database migration
2. `src/accounts/serializers/affiliate.py` - Affiliate serializers
3. `src/accounts/api/affiliate.py` - Affiliate API view

### Modified:
1. `src/accounts/models/user.py` - Added affiliate fields and invite code generation
2. `src/accounts/serializers/register.py` - Added affiliate parameter handling
3. `src/accounts/serializers/__init__.py` - Exported affiliate serializers
4. `src/accounts/api/__init__.py` - Exported affiliate API view
5. `src/accounts/urls.py` - Added affiliate endpoint
6. `src/accounts/admin.py` - Enhanced admin panel with affiliate fields

## Usage

### For Frontend Developers

#### 1. Registration with Affiliate Code
```javascript
// Register endpoint: POST /api/v1/accounts/register
const response = await fetch('/api/v1/accounts/register', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
        username: 'newuser',
        email: 'newuser@example.com',
        password: 'SecurePass123',
        affiliate: 'ABC123XYZ0'  // Optional affiliate code from URL parameter
    })
});
```

#### 2. Get Affiliate Information
```javascript
// Affiliate endpoint: GET /api/v1/accounts/affiliate
const response = await fetch('/api/v1/accounts/affiliate', {
    method: 'GET',
    headers: { 
        'Authorization': 'Bearer YOUR_ACCESS_TOKEN',
        'Content-Type': 'application/json'
    }
});

const data = await response.json();
console.log('Invite Link:', data.invite_link);
console.log('Total Referrals:', data.total_referrals);
console.log('Wallet Balance:', data.wallet_balance);
```

#### 3. Example URL with Affiliate Code
```
https://app.pilito.com/auth/register?affiliate=ABC123XYZ0
```

Extract the affiliate code from URL parameters and pass it to the registration API.

## Configuration

### Referral Bonus Amount
Currently set to 10.00 in the RegisterSerializer. To change this:
- Edit `src/accounts/serializers/register.py`
- Modify line: `referrer.wallet_balance += Decimal('10.00')`

### Frontend URL
The base URL for invite links is configured via Django settings:
- Add `FRONTEND_URL` to your settings (defaults to 'https://app.pilito.com')
- Edit `src/accounts/serializers/affiliate.py` if needed

## Database Migration

To apply the database changes:
```bash
# Run the migration
python manage.py migrate accounts

# Or if using Docker
docker-compose exec web python manage.py migrate accounts
```

## Security Considerations

1. **Invite Code Uniqueness**: Automatically enforced by database constraint
2. **Referral Validation**: Invalid codes don't break registration
3. **Authentication Required**: Affiliate info endpoint requires authentication
4. **Wallet Balance**: Only modifiable by admin or through controlled processes

## Future Enhancements (Optional)

Consider adding:
1. Multi-level referral system (referrals of referrals)
2. Different bonus amounts based on conditions
3. Wallet transaction history
4. Wallet payout/withdrawal functionality
5. Referral analytics dashboard
6. Time-limited promotional bonus amounts
7. Maximum referral limits per user
8. Webhook notifications when new referrals sign up

## Testing

### Manual Testing Steps:
1. Create a user account (invite code auto-generated)
2. Get invite link from `/api/v1/accounts/affiliate`
3. Register a new user with the affiliate code
4. Verify the referrer's wallet increased by 10.00
5. Check the referrer's direct_referrals list includes the new user
6. Verify admin panel shows correct referral count

### API Testing with curl:
```bash
# Get affiliate info
curl -X GET http://localhost:8000/api/v1/accounts/affiliate \
  -H "Authorization: Bearer YOUR_TOKEN"

# Register with affiliate code
curl -X POST http://localhost:8000/api/v1/accounts/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@example.com",
    "password": "TestPass123",
    "affiliate": "ABC123XYZ0"
  }'
```

## Support

For questions or issues:
1. Check Django logs for errors
2. Verify migration was applied successfully
3. Ensure FRONTEND_URL is configured correctly
4. Confirm authentication is working properly

