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
- `AffiliationConfig` table
- `affiliate_active` field on User model
- `WalletTransaction` table

### 2. Configure Commission Percentage

1. Access Django Admin: `https://your-domain.com/admin/`
2. Go to **Settings → 🤝 Affiliation Configuration**
3. Set the commission percentage (e.g., 10 for 10%)
4. Enable the system: `is_active = True`
5. Save

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
✅ **Idempotent**: Won't pay commission twice for same payment  
✅ **Atomic**: Wallet update & transaction creation happen together  
✅ **Traceable**: Every commission linked to original payment  
✅ **User Control**: Each user can enable/disable their affiliate rewards  
✅ **Admin Control**: Global on/off switch for entire system  

## 📝 Files Created/Modified

### New Files:
- `src/billing/signals.py` - Commission processing logic
- `src/billing/api/affiliate.py` - API endpoints
- `src/settings/migrations/0018_affiliationconfig.py`
- `src/accounts/migrations/0011_user_affiliate_active.py`
- `src/billing/migrations/0002_wallettransaction.py`
- `AFFILIATE_SYSTEM_README.md` - Full documentation
- `AFFILIATE_DEPLOYMENT.md` - This file

### Modified Files:
- `src/settings/models.py` - Added AffiliationConfig model
- `src/accounts/models/user.py` - Added affiliate_active field
- `src/billing/models.py` - Added WalletTransaction model
- `src/billing/urls.py` - Added affiliate API routes
- `src/settings/admin.py` - Added AffiliationConfigAdmin
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
5. **Commissions are paid instantly** when payment completes

## 🐛 Troubleshooting

**No commission paid?**
```python
# Check in Django shell:
from settings.models import AffiliationConfig
config = AffiliationConfig.get_config()
print(f"Active: {config.is_active}, Percentage: {config.percentage}")

from accounts.models import User
referrer = User.objects.get(email="referrer@example.com")
print(f"Affiliate Active: {referrer.affiliate_active}")

referred = User.objects.get(email="referred@example.com")
print(f"Referred By: {referred.referred_by}")
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

# Configure 10% commission
config = AffiliationConfig.get_config()
config.percentage = 10.0
config.is_active = True
config.save()

print("✅ Affiliate system configured: 10% commission, active")
```

---

**For full documentation, see**: `AFFILIATE_SYSTEM_README.md`

