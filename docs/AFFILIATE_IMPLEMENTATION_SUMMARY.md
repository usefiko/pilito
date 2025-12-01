# Affiliate Marketing Implementation - Summary

## Overview
Successfully implemented a comprehensive affiliate marketing system. Users can now invite friends and earn **commission-based rewards** when those friends make payments (within a configurable validity period after registration).

## Features Implemented

### 1. User Model Updates
Added fields to the User model:
- **invite_code**: A unique 10-character alphanumeric code automatically generated for each user
- **referred_by**: ForeignKey to track which user referred this user
- **wallet_balance**: Decimal field to track earnings from referrals (default: 0.00)
- **affiliate_active**: Boolean field to enable/disable affiliate rewards (default: False)

The invite code is automatically generated when a user is created using a custom `save()` method.

### 2. Affiliation Configuration (NEW)
Added `AffiliationConfig` singleton model in the settings app:
- **percentage**: Commission percentage (e.g., 10 = 10% of payment)
- **commission_validity_days**: Number of days after registration during which payments qualify for commission (0 = unlimited)
- **is_active**: Global enable/disable switch for the entire affiliate system

### 3. Registration Flow
Updated the registration process to handle affiliate codes:
- Added `affiliate` parameter to RegisterSerializer (optional)
- When a user registers with an affiliate code:
  - The new user is linked to the referrer via `referred_by` field
  - Invalid codes don't block registration (silently ignored)

### 4. Commission-Based Rewards (NEW)
Instead of a fixed bonus at registration, commissions are now paid when:
- The referred user makes a **completed payment**
- The referrer has **affiliate_active = True**
- The **global affiliate system is active**
- The payment is **within the validity period** (X days after registration)

**How it works:**
1. User A invites User B using their invite code
2. User B registers (no immediate bonus)
3. User B makes a payment within 30 days (configurable)
4. User A receives X% of the payment as commission (e.g., 10%)
5. Commission is added to User A's wallet_balance
6. A WalletTransaction record is created for audit trail

### 5. Affiliate API Endpoints

#### GET `/api/billing/affiliate/stats/`
Returns comprehensive affiliate statistics:

```json
{
    "affiliate_active": true,
    "invite_code": "ABC123XYZ0",
    "commission_percentage": 10.0,
    "commission_validity_days": 30,
    "validity_display": "30 days after registration",
    "stats": {
        "total_commission_earned": 125.00,
        "total_amount_from_referrals": 1250.00,
        "total_registrations": 5,
        "active_referrals": 4
    },
    "referred_users": [
        {
            "user_id": 123,
            "email": "john@example.com",
            "username": "john_doe",
            "registered_at": "2025-11-25T10:30:00Z",
            "total_paid": 500.00,
            "commission_earned_from_user": 50.00,
            "is_within_validity": true,
            "validity_expires_at": "2025-12-25T10:30:00Z",
            "payment_count": 2,
            "payments": [...]
        }
    ],
    "recent_commissions": [...]
}
```

#### POST `/api/billing/affiliate/toggle/`
Enable/disable affiliate system for the user:
```json
// Request
{ "action": "enable" }  // or "disable" or "toggle"

// Response
{
    "success": true,
    "affiliate_active": true,
    "invite_code": "ABC123XYZ0",
    "message": "Affiliate system enabled successfully"
}
```

### 6. Admin Panel Updates
Enhanced the Django admin panel with:
- Display of invite_code, wallet_balance, and affiliate_active in user list
- New "Referral Count" column showing number of direct referrals
- New "Affiliate Marketing" fieldset with:
  - Invite code (read-only)
  - Referred by (editable)
  - Wallet balance (editable)
  - Affiliate active toggle
  - Referral list showing all users referred by this user
- Search capability by invite_code

#### AffiliationConfig Admin (NEW)
- **Location**: Settings → 🤝 Affiliation Configuration
- Configure commission percentage and validity period
- View total referrals and commissions paid
- Example calculations

#### WalletTransaction Admin (NEW)
- **Location**: Billing → 💰 Wallet Transactions
- View all commission transactions
- Filter by transaction type and date
- Full audit trail

## Files Modified/Created

### New Files (Commission System):
1. `src/billing/signals.py` - Commission processing logic with validity check
2. `src/billing/api/affiliate.py` - Affiliate stats and toggle API endpoints
3. `src/settings/migrations/0018_affiliationconfig.py` - AffiliationConfig model
4. `src/settings/migrations/0019_affiliationconfig_commission_validity_days.py` - Validity field
5. `src/accounts/migrations/0011_user_affiliate_active.py` - User affiliate_active field
6. `src/billing/migrations/0002_wallettransaction.py` - WalletTransaction model
7. `AFFILIATE_SYSTEM_README.md` - Complete documentation
8. `AFFILIATE_DEPLOYMENT.md` - Quick deployment guide

### Modified Files:
1. `src/accounts/models/user.py` - Added affiliate_active field
2. `src/settings/models.py` - Added AffiliationConfig model with validity period
3. `src/billing/models.py` - Added WalletTransaction model
4. `src/billing/urls.py` - Added affiliate API routes
5. `src/settings/admin.py` - Added AffiliationConfigAdmin
6. `src/billing/admin.py` - Added WalletTransactionAdmin
7. `src/accounts/serializers/register.py` - Added affiliate parameter handling
8. `src/accounts/admin.py` - Enhanced admin panel with affiliate fields

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

### Commission Settings (Admin Panel)
All commission settings are now configurable via Django Admin:

1. Go to **Settings → 🤝 Affiliation Configuration**
2. Set:
   - **Percentage**: Commission % (e.g., 10 = 10% of payment)
   - **Validity Days**: How many days after registration payments qualify (0 = unlimited)
   - **Active**: Enable/disable the entire system
3. Save

**Example Configuration:**
- Percentage: 10%
- Validity Days: 30
- Active: Yes

This means referrers get 10% of each payment made by their referrals within 30 days of registration.

### Frontend URL
The base URL for invite links is configured via Django settings:
- Add `FRONTEND_URL` to your settings (defaults to 'https://app.pilito.com')
- Edit `src/accounts/serializers/affiliate.py` if needed

## Database Migration

### Migration Files Created:
1. `0015_add_affiliate_fields.py` - Adds affiliate marketing fields to User model
2. `0016_otptoken.py` - Creates OTPToken model (if not already present)
3. `0017_merge_20251125_1010.py` - Merge migration to resolve conflict

To apply the database changes:
```bash
# Run the migration
python manage.py migrate accounts

# Or if using Docker
docker-compose exec web python manage.py migrate accounts
```

### Migration Conflict Resolution
If you encountered the error:
```
CommandError: Conflicting migrations detected; multiple leaf nodes in the migration graph
```

This has been resolved by creating a merge migration (`0017_merge_20251125_1010.py`) that combines both migration branches.

## Security Considerations

1. **Invite Code Uniqueness**: Automatically enforced by database constraint
2. **Referral Validation**: Invalid codes don't break registration
3. **Authentication Required**: Affiliate info endpoint requires authentication
4. **Wallet Balance**: Only modifiable by admin or through controlled processes

## Features Status

### ✅ Implemented:
1. ✅ Commission-based rewards (% of payments)
2. ✅ Configurable commission validity period
3. ✅ Wallet transaction history (WalletTransaction model)
4. ✅ User-level affiliate enable/disable
5. ✅ Global system enable/disable
6. ✅ Idempotent commission processing
7. ✅ Full audit trail

### 🔮 Future Enhancements (Optional)
Consider adding:
1. Multi-level referral system (referrals of referrals)
2. Tiered commission rates based on referral count
3. Wallet payout/withdrawal functionality
4. Referral analytics dashboard
5. Maximum referral limits per user
6. Webhook notifications when new referrals sign up
7. Custom promotional invite codes

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

