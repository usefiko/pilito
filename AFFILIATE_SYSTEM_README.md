# Affiliate/Referral Reward System Documentation

## 📋 Overview

This document describes the complete affiliate/referral reward system implemented for the Pilito platform. The system automatically rewards users when their referrals make payments.

---

## 🎯 Features

1. **Configurable Commission System**
   - Admin-controlled commission percentage
   - Global on/off switch for the entire system
   - Singleton configuration (only one instance)

2. **User-Level Control**
   - Each user can enable/disable their affiliate rewards
   - Default: disabled (opt-in system)
   - Users get a unique invite code automatically

3. **Automatic Commission Processing**
   - Triggers when referred users make completed payments
   - Calculates commission based on configured percentage
   - Adds commission to referrer's wallet balance
   - Creates transaction record for transparency
   - **Idempotent**: Won't pay twice for the same payment

4. **Comprehensive API**
   - View affiliate statistics
   - List all referred users with payment history
   - Toggle affiliate system on/off
   - See commission breakdown per referral

---

## 🗂️ Architecture

### Models

#### 1. `AffiliationConfig` (settings app)
```python
class AffiliationConfig(SingletonModel):
    percentage = DecimalField()            # Commission % (e.g., 10 = 10%)
    commission_validity_days = IntegerField()  # Days after registration to apply commission (0 = unlimited)
    is_active = BooleanField()             # Global enable/disable
    created_at = DateTimeField()
    updated_at = DateTimeField()
```

**Location**: `src/settings/models.py`

**Key Methods**:
- `get_config()`: Get or create the config instance
- `calculate_commission(amount)`: Calculate commission for a payment amount
- `is_within_validity_period(user_registration_date, payment_date)`: Check if payment qualifies for commission
- `get_validity_display()`: Human-readable validity period

#### 2. `User` model updates (accounts app)
```python
class User(AbstractUser):
    # Existing fields
    invite_code = CharField()     # Auto-generated unique code
    referred_by = ForeignKey()    # Who referred this user
    wallet_balance = DecimalField()
    
    # NEW FIELD
    affiliate_active = BooleanField(default=False)  # Enable affiliate for this user
```

**Location**: `src/accounts/models/user.py`

#### 3. `WalletTransaction` (billing app)
```python
class WalletTransaction(models.Model):
    user = ForeignKey(User)              # Who received the transaction
    transaction_type = CharField()        # 'commission', 'payment', etc.
    amount = DecimalField()              # Transaction amount
    balance_after = DecimalField()       # Balance after transaction
    description = TextField()            # Human-readable description
    
    # Reference fields
    related_payment = ForeignKey(Payment, null=True)    # Payment that triggered this
    referred_user = ForeignKey(User, null=True)         # User who made the payment
    created_at = DateTimeField()
```

**Location**: `src/billing/models.py`

**Indexes**:
- `(user, -created_at)`: Fast lookups for user transaction history
- `(related_payment)`: Fast lookups for payment-related transactions

---

## 🔄 How It Works

### Payment Flow

1. **User A** registers using **User B's** invite code
   - `User A.referred_by` = `User B`
   - `User A.invite_code` = auto-generated unique code
   - `User A.date_joined` = registration timestamp (validity period starts)

2. **User A** makes a payment
   - Payment status changes to `'completed'`

3. **Signal triggers** (`post_save` on Payment model)
   - Checks if payment is completed
   - Checks if commission already paid (idempotent check)
   - Checks if User A has a referrer (User B)
   - Checks if User B has `affiliate_active = True`
   - Checks if global affiliate system is active
   - ✨ **NEW**: Checks if payment is within validity period (X days after registration)

4. **Commission calculation**
   - Gets `AffiliationConfig.percentage` (e.g., 10%)
   - Gets `AffiliationConfig.commission_validity_days` (e.g., 30 days)
   - Verifies payment date is within `registration_date + validity_days`
   - Calculates: `commission = payment_amount * percentage / 100`

5. **Atomic transaction**
   - Updates `User B.wallet_balance += commission`
   - Creates `WalletTransaction` record
   - Links to original payment for traceability

### ⏰ Commission Validity Period

The `commission_validity_days` field controls how long after registration a user's payments qualify for affiliate commissions:

| Setting | Behavior |
|---------|----------|
| `0` | **Unlimited** - Commissions apply to all payments, forever |
| `30` | Commissions apply only to payments made within 30 days of registration |
| `90` | Commissions apply only to payments made within 90 days of registration |

**Example:**
- User registers on **January 1**
- `commission_validity_days = 30`
- Payment on **January 15** → ✅ Commission applies
- Payment on **February 5** (35 days later) → ❌ No commission

### Signal Implementation

**File**: `src/billing/signals.py`

```python
@receiver(post_save, sender=Payment)
def process_affiliate_commission(sender, instance, created, **kwargs):
    # Only process completed payments
    if instance.status != 'completed':
        return
    
    # Idempotent check
    if WalletTransaction.objects.filter(
        related_payment=instance,
        transaction_type='commission'
    ).exists():
        return
    
    # Check referral chain
    if not instance.user.referred_by:
        return
    
    referrer = instance.user.referred_by
    
    # Check if referrer has affiliate active
    if not referrer.affiliate_active:
        return
    
    # Get config and check if active
    config = AffiliationConfig.get_config()
    if not config.is_active:
        return
    
    # ✨ NEW: Check if payment is within validity period
    if not config.is_within_validity_period(
        user_registration_date=instance.user.date_joined,
        payment_date=instance.payment_date
    ):
        return  # Payment is outside the validity period
    
    # Calculate and pay commission
    commission = config.calculate_commission(instance.amount)
    
    with transaction.atomic():
        referrer.wallet_balance += commission
        referrer.save()
        
        WalletTransaction.objects.create(...)
```

**Registered in**: `src/billing/apps.py` → `ready()` method

---

## 🌐 API Endpoints

### 1. Get Affiliate Statistics

**Endpoint**: `GET /api/billing/affiliate/stats/`

**Authentication**: Required

**Response**:
```json
{
  "affiliate_active": true,
  "invite_code": "ABC123XYZ0",
  "commission_percentage": 10.0,
  "commission_validity_days": 30,
  "validity_display": "30 days after registration",
  "stats": {
    "total_commission_earned": 1250.50,
    "total_amount_from_referrals": 12505.00,
    "total_registrations": 15,
    "active_referrals": 12
  },
  "referred_users": [
    {
      "user_id": 42,
      "email": "user@example.com",
      "username": "john_doe",
      "first_name": "John",
      "last_name": "Doe",
      "registered_at": "2025-01-15T10:30:00Z",
      "total_paid": 1500.00,
      "commission_earned_from_user": 150.00,
      "payment_count": 3,
      "is_within_validity": true,
      "validity_expires_at": "2025-02-14T10:30:00Z",
      "payments": [
        {
          "payment_id": 101,
          "amount": 500.00,
          "payment_date": "2025-01-20T14:20:00Z",
          "plan_name": "Pro Monthly"
        }
      ]
    }
  ],
  "recent_commissions": [
    {
      "transaction_id": 501,
      "amount": 50.00,
      "from_user": {
        "email": "user@example.com",
        "username": "john_doe"
      },
      "payment_amount": 500.00,
      "date": "2025-01-20T14:20:05Z",
      "description": "Affiliate commission (10%) from user@example.com's payment of 500",
      "balance_after": 1250.50
    }
  ]
}
```

**If affiliate not active**:
```json
{
  "affiliate_active": false,
  "message": "Affiliate system is not active for your account",
  "invite_code": "ABC123XYZ0"
}
```

### 2. Toggle Affiliate System

**Endpoint**: `POST /api/billing/affiliate/toggle/`

**Authentication**: Required

**Request Body**:
```json
{
  "action": "enable"  // or "disable" or "toggle"
}
```

**Response**:
```json
{
  "success": true,
  "affiliate_active": true,
  "invite_code": "ABC123XYZ0",
  "message": "Affiliate system enabled successfully"
}
```

---

## 🎨 Admin Interface

### 1. Affiliation Config Admin

**Location**: Django Admin → Settings → 🤝 Affiliation Configuration

**Fields**:
- **Percentage**: Commission percentage (e.g., 10 = 10%)
- **Validity Days**: Number of days after registration during which payments qualify for commission (0 = unlimited)
- **Active**: Global enable/disable switch

**Statistics**:
- Total referrals in system
- Total commissions paid out
- Example calculations (100, 500, 1000 payment amounts)
- Validity period details

**Permissions**:
- ✅ Can edit
- ❌ Cannot add (singleton - only one instance)
- ❌ Cannot delete (singleton)

### 2. Wallet Transaction Admin

**Location**: Django Admin → Billing → 💰 Wallet Transactions

**List Display**:
- Transaction ID
- User email
- Transaction type
- Amount (color-coded: green for credits, red for debits)
- Balance after
- Referred user email (who generated commission)
- Created date

**Filters**:
- Transaction type
- Created date

**Permissions**:
- ✅ Can view
- ✅ Can edit (for manual adjustments)
- ❌ Cannot add (transactions created automatically)

---

## 📊 Database Schema

### Migrations

1. **Settings App** - `0018_affiliationconfig.py`
   - Creates `AffiliationConfig` table

2. **Settings App** - `0019_affiliationconfig_commission_validity_days.py`
   - Adds `commission_validity_days` field to AffiliationConfig

3. **Accounts App** - `0011_user_affiliate_active.py`
   - Adds `affiliate_active` field to User model

4. **Billing App** - `0002_wallettransaction.py`
   - Creates `WalletTransaction` table with indexes

### Relationships

```
User (Referrer)
 ├─ referred_by ← User (Referred)
 ├─ wallet_balance
 └─ affiliate_active

Payment (by Referred User)
 └─ triggers signal
     └─ creates WalletTransaction
         ├─ user → Referrer
         ├─ referred_user → Referred User
         └─ related_payment → Payment
```

---

## 🔒 Security Features

1. **Idempotency**
   - Check if commission already paid before processing
   - Prevents double-payment for same payment

2. **Atomic Transactions**
   - Wallet update and transaction creation in single DB transaction
   - Ensures consistency (both succeed or both fail)

3. **User Control**
   - Default: affiliate disabled (`affiliate_active = False`)
   - Users must opt-in to receive commissions

4. **Admin Control**
   - Global on/off switch (`AffiliationConfig.is_active`)
   - Can disable entire system instantly

5. **Traceability**
   - Every commission linked to original payment
   - Full audit trail via `WalletTransaction`

---

## 🚀 Usage Examples

### For Users

1. **Enable affiliate system**:
   ```bash
   POST /api/billing/affiliate/toggle/
   {"action": "enable"}
   ```

2. **Share invite code**:
   - Get code from: `GET /api/billing/affiliate/stats/`
   - Share: `https://pilito.com/register?invite_code=ABC123XYZ0`

3. **Track earnings**:
   - View stats: `GET /api/billing/affiliate/stats/`
   - See which users generated commissions
   - See payment history per referral

### For Admins

1. **Configure commission**:
   - Go to Django Admin → Settings → Affiliation Configuration
   - Set percentage (e.g., 10%)
   - Enable/disable globally

2. **Monitor system**:
   - View all wallet transactions
   - Filter by commission type
   - See total payouts in config admin

3. **Manual adjustments** (if needed):
   - Can create manual `WalletTransaction` entries
   - Useful for corrections or special cases

---

## 📝 Testing Checklist

- [ ] User A registers with User B's invite code
- [ ] User A makes payment → commission added to User B's wallet
- [ ] Check `WalletTransaction` created correctly
- [ ] Try to pay commission again → should skip (idempotent)
- [ ] Disable User B's affiliate → new payments don't trigger commission
- [ ] Disable global affiliate → no commissions paid
- [ ] API returns correct stats for User B
- [ ] Toggle affiliate on/off via API
- [ ] Admin can view and edit config
- [ ] Admin can see all wallet transactions

---

## 🐛 Troubleshooting

### Commission not being paid?

1. Check if payment status is `'completed'`
2. Check if referred user has `referred_by` set
3. Check if referrer has `affiliate_active = True`
4. Check if `AffiliationConfig.is_active = True`
5. **Check if payment is within validity period** (user registered within X days)
6. Check Django logs for errors in signal

### Payment is within validity period but no commission?

```python
# Check in Django shell:
from settings.models import AffiliationConfig
from accounts.models import User

config = AffiliationConfig.get_config()
print(f"Validity days: {config.commission_validity_days}")

user = User.objects.get(email="referred@example.com")
print(f"Registered: {user.date_joined}")

# Check if still valid
is_valid = config.is_within_validity_period(user.date_joined)
print(f"Within validity: {is_valid}")
```

### Duplicate commissions?

- Should not happen due to idempotency check
- If happens, check database indexes on `related_payment`

### Wallet balance incorrect?

- Check `WalletTransaction` history
- Each transaction has `balance_after` for audit
- Can recalculate by summing all transactions for user

---

## 🔄 Future Enhancements

Possible additions:

1. **Tiered Commissions**
   - Different percentages based on referral count
   - Higher % for top performers

2. **Commission Withdrawal**
   - Allow users to withdraw wallet balance
   - Integration with payment gateways

3. **Referral Analytics**
   - Conversion rates
   - Average revenue per referral
   - Lifetime value tracking

4. **Promo Codes**
   - Custom invite codes instead of random
   - Time-limited campaigns

5. **Multi-Level Marketing**
   - Second-level referrals (referral's referrals)
   - Configurable depth

---

## 📚 File Reference

### Models
- `src/settings/models.py` - AffiliationConfig
- `src/accounts/models/user.py` - User (affiliate_active field)
- `src/billing/models.py` - WalletTransaction

### Signals
- `src/billing/signals.py` - process_affiliate_commission

### API
- `src/billing/api/affiliate.py` - AffiliateStatsView, ToggleAffiliateSystemView
- `src/billing/urls.py` - URL routing

### Admin
- `src/settings/admin.py` - AffiliationConfigAdmin
- `src/billing/admin.py` - WalletTransactionAdmin

### Migrations
- `src/settings/migrations/0018_affiliationconfig.py`
- `src/accounts/migrations/0011_user_affiliate_active.py`
- `src/billing/migrations/0002_wallettransaction.py`

---

## ✅ Implementation Complete

All features have been implemented:

- ✅ AffiliationConfig model with singleton logic
- ✅ Commission percentage configuration
- ✅ **Commission validity period** (X days after registration)
- ✅ User.affiliate_active field (default: disabled)
- ✅ WalletTransaction model for audit trail
- ✅ Signal for automatic commission processing
- ✅ Validity period check before paying commission
- ✅ Idempotent payment logic
- ✅ API endpoints for stats and toggle
- ✅ Admin UI for configuration and monitoring
- ✅ Migrations for all database changes
- ✅ Comprehensive documentation

**Next Steps**:
1. Run migrations on server: `python manage.py migrate`
2. Access Django Admin to configure percentage and validity days
3. Test with real payment flows
4. Monitor via admin and API

---

*Generated: 2025-12-01*
*Version: 1.1 - Added commission validity period*

