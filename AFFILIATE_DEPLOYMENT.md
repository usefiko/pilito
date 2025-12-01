# Affiliate System - Quick Deployment Guide

## 🚀 Deployment Steps

### 1. Run Migrations

```bash
# On your server
cd /path/to/pilito
python manage.py migrate settings
python manage.py migrate accounts  
python manage.py migrate billing
```

This will create:
- `AffiliationConfig` table with `percentage` and `commission_validity_days` fields
- `affiliate_active` field on User model
- `WalletTransaction` table

### 2. Configure Commission Settings

1. Access Django Admin: `https://your-domain.com/admin/`
2. Go to **Settings → 🤝 Affiliation Configuration**
3. Set the commission percentage (e.g., 10 for 10%)
4. Set the validity period (e.g., 30 for 30 days, or 0 for unlimited)
5. Enable the system: `is_active = True`
6. Save

### 3. API Endpoints

Add these to your frontend:

**Get Affiliate Stats:**
```http
GET /api/billing/affiliate/stats/
Authorization: Bearer {token}
```

**Toggle Affiliate System:**
```http
POST /api/billing/affiliate/toggle/
Authorization: Bearer {token}
Content-Type: application/json

{
  "action": "enable"  // or "disable" or "toggle"
}
```

### 4. Testing

1. **User A** enables affiliate in their profile
2. **User B** registers with User A's invite code
3. **User B** makes a payment
4. Check User A's wallet balance increased
5. Verify in Django Admin → Billing → Wallet Transactions

### 5. Monitoring

- **View all commissions**: Django Admin → Billing → Wallet Transactions
- **View config stats**: Django Admin → Settings → Affiliation Configuration
- **API monitoring**: `GET /api/billing/affiliate/stats/`

## 🔑 Key Points

✅ **Default State**: Affiliate is **disabled** for all users (opt-in)  
✅ **Validity Period**: Commission only applies within X days of registration  
✅ **Idempotent**: Won't pay commission twice for same payment  
✅ **Atomic**: Wallet update & transaction creation happen together  
✅ **Traceable**: Every commission linked to original payment  
✅ **User Control**: Each user can enable/disable their affiliate rewards  
✅ **Admin Control**: Global on/off switch for entire system

## ⏰ Commission Validity Period

The `commission_validity_days` setting controls how long after a user registers their payments can generate commissions:

| Value | Meaning |
|-------|---------|
| `0` | **Unlimited** - All payments generate commission forever |
| `30` | Only payments within 30 days of registration |
| `90` | Only payments within 90 days of registration |

**Example**: If validity = 30 days
- User registers Jan 1 → Payments until Jan 31 generate commission
- Payment on Feb 5 → No commission (outside validity period)  

## 📝 Files Created/Modified

### New Files:
- `src/billing/signals.py` - Commission processing logic (with validity check)
- `src/billing/api/affiliate.py` - API endpoints
- `src/settings/migrations/0018_affiliationconfig.py`
- `src/settings/migrations/0019_affiliationconfig_commission_validity_days.py`
- `src/accounts/migrations/0011_user_affiliate_active.py`
- `src/billing/migrations/0002_wallettransaction.py`
- `AFFILIATE_SYSTEM_README.md` - Full documentation
- `AFFILIATE_DEPLOYMENT.md` - This file

### Modified Files:
- `src/settings/models.py` - Added AffiliationConfig model with validity period
- `src/accounts/models/user.py` - Added affiliate_active field
- `src/billing/models.py` - Added WalletTransaction model
- `src/billing/urls.py` - Added affiliate API routes
- `src/settings/admin.py` - Added AffiliationConfigAdmin with validity settings
- `src/billing/admin.py` - Added WalletTransactionAdmin

## 🔗 Database Relationships

```
User (Referrer)
 └─ affiliate_active = True
 └─ wallet_balance = 0.00
     ↑
     | referred_by
     |
User (Referred)
 └─ makes Payment → triggers Signal
                    ↓
              WalletTransaction
               - commission added
               - balance updated
               - audit record created
```

## ⚠️ Important Notes

1. **Signals are registered** in `src/billing/apps.py` → `ready()` method
2. **Only completed payments** trigger commissions (`status = 'completed'`)
3. **Referrer must have affiliate enabled** to receive commissions
4. **Global system must be active** (`AffiliationConfig.is_active = True`)
5. **Payment must be within validity period** (X days after registration)
6. **Commissions are paid instantly** when payment completes

## 🐛 Troubleshooting

**No commission paid?**
```python
# Check in Django shell:
from settings.models import AffiliationConfig
config = AffiliationConfig.get_config()
print(f"Active: {config.is_active}")
print(f"Percentage: {config.percentage}")
print(f"Validity: {config.commission_validity_days} days")

from accounts.models import User
referrer = User.objects.get(email="referrer@example.com")
print(f"Affiliate Active: {referrer.affiliate_active}")

referred = User.objects.get(email="referred@example.com")
print(f"Referred By: {referred.referred_by}")
print(f"Registered: {referred.date_joined}")

# Check if still within validity period
is_valid = config.is_within_validity_period(referred.date_joined)
print(f"Within Validity Period: {is_valid}")
```

**Check signal is working:**
```python
from billing.models import Payment, WalletTransaction

payment = Payment.objects.filter(status='completed').last()
commission = WalletTransaction.objects.filter(
    related_payment=payment,
    transaction_type='commission'
)
print(f"Commission: {commission}")
```

## 📊 Sample Data for Testing

```python
# Django shell
from settings.models import AffiliationConfig

# Configure 10% commission with 30-day validity
config = AffiliationConfig.get_config()
config.percentage = 10.0
config.commission_validity_days = 30  # Commission applies for 30 days after registration
config.is_active = True
config.save()

print("✅ Affiliate system configured:")
print(f"   - Commission: {config.percentage}%")
print(f"   - Validity: {config.get_validity_display()}")
print(f"   - Active: {config.is_active}")
```

### Check if a user's payments still qualify:

```python
from settings.models import AffiliationConfig
from accounts.models import User

config = AffiliationConfig.get_config()
user = User.objects.get(email="referred@example.com")

is_valid = config.is_within_validity_period(user.date_joined)
print(f"User {user.email} - Payments qualify for commission: {is_valid}")
```

---

**For full documentation, see**: `AFFILIATE_SYSTEM_README.md`

