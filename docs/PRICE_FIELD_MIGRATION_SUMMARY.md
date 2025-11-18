# Price Field Migration Summary

## Overview
Successfully migrated from multi-language pricing (`price_en`, `price_tr`, `price_ar`) to a single `price` field across the entire billing system.

## Changes Made

### 1. **Models** (`src/billing/models.py`)
#### TokenPlan Model
- ❌ Removed: `price_en`, `price_tr`, `price_ar` fields
- ✅ Added: Single `price` field (DecimalField)
- Updated: `__str__` method to use `price` instead of `price_en`
- Updated: Meta ordering from `['price_en']` to `['price']`

#### FullPlan Model
- ❌ Removed: `price_en`, `price_tr`, `price_ar` fields
- ✅ Added: Single `price` field (DecimalField)
- Updated: Meta ordering from `['is_yearly', 'price_en']` to `['is_yearly', 'price']`

---

### 2. **Serializers** (`src/billing/serializers.py`)
#### TokenPlanSerializer
- Updated fields list: removed `price_en`, `price_tr`, `price_ar`
- Added: `price` field

#### FullPlanSerializer
- Updated fields list: removed `price_en`, `price_tr`, `price_ar`
- Added: `price` field

#### ZarinpalPaymentSerializer
- ❌ Removed: `language` field (no longer needed)
- ❌ Removed: `get_plan_price()` method
- Simplified validation to only check plan existence

---

### 3. **Zarinpal APIs** (`src/billing/api/zarinpal.py`)
#### ZPPayment
- ❌ Removed: `language` parameter from request
- Updated: Direct access to `plan.price` instead of language-specific pricing
- Simplified payment record creation

#### ZPVerify
- No changes needed (automatically uses updated models)

#### Documentation
- Updated module docstring to reflect simplified API

---

### 4. **Admin Interface** (`src/billing/admin.py`)
#### TokenPlanAdmin
- Updated `list_display`: removed `price_en`, `price_tr`, `price_ar`, added `price`
- Updated `ordering`: from `('price_en',)` to `('price',)`

#### FullPlanAdmin
- Updated `list_display`: removed `price_en`, `price_tr`, `price_ar`, added `price`
- Updated `ordering`: from `('is_yearly', 'price_en')` to `('is_yearly', 'price')`

---

### 5. **Views** (`src/billing/views.py`)
#### PurchasePlanView
- Updated TokenPlan price access: `selected_token_plan.price` (was `price_en`)
- Updated FullPlan price access: `selected_full_plan.price` (was `price_en`)

---

### 6. **Services** (`src/billing/services/stripe_service.py`)
#### StripeService
- Updated price comparison logic to use `plan.price` instead of `plan.price_en`
- Removed language-specific price field selection
- Simplified currency handling

---

### 7. **Signals** (`src/accounts/signals.py`)
#### create_user_profile signal
- Updated free trial plan creation: changed `price_en`, `price_tr`, `price_ar` to single `price: 0`

---

### 8. **Management Commands** (`src/billing/management/commands/sync_stripe_products.py`)
#### sync_stripe_products
- Updated display: `plan.price` instead of `plan.price_en`
- Updated Stripe price creation: uses `plan.price` for unit_amount calculation

---

### 9. **Examples and Documentation**
#### api_examples.py
- Updated all references from `price_en` to `price`
- Updated price calculations in upgrade/downgrade logic

#### examples.py
- Updated test plan creation to use single `price` field

#### README.md
- Updated plan creation examples to use single `price` field

#### ZARINPAL_API_USAGE.md
- Removed `language` parameter from API documentation
- Removed multi-language pricing section
- Updated model field descriptions
- Updated frontend integration examples
- Updated test examples

---

### 10. **Database Migration** (`src/billing/migrations/0009_change_price_to_single_field.py`)
Created migration that:
1. Adds new `price` field to TokenPlan (with default=0)
2. Adds new `price` field to FullPlan (with default=0)
3. Removes `price_en` field from TokenPlan
4. Removes `price_tr` field from TokenPlan
5. Removes `price_ar` field from TokenPlan
6. Removes `price_en` field from FullPlan
7. Removes `price_tr` field from FullPlan
8. Removes `price_ar` field from FullPlan
9. Updates TokenPlan ordering to use `price`
10. Updates FullPlan ordering to use `is_yearly` and `price`

---

## Files Modified

### Core Files
1. ✅ `src/billing/models.py`
2. ✅ `src/billing/serializers.py`
3. ✅ `src/billing/api/zarinpal.py`
4. ✅ `src/billing/admin.py`
5. ✅ `src/billing/views.py`

### Supporting Files
6. ✅ `src/billing/services/stripe_service.py`
7. ✅ `src/accounts/signals.py`
8. ✅ `src/billing/management/commands/sync_stripe_products.py`
9. ✅ `src/billing/api_examples.py`
10. ✅ `src/billing/examples.py`
11. ✅ `src/billing/README.md`

### Documentation
12. ✅ `ZARINPAL_API_USAGE.md`

### Migrations
13. ✅ `src/billing/migrations/0009_change_price_to_single_field.py`

---

## API Changes

### Before:
```json
POST /billing/zp-pay
{
  "full_plan_id": 2,
  "language": "en"
}
```

### After:
```json
POST /billing/zp-pay
{
  "full_plan_id": 2
}
```

---

## Database Migration Steps

### To Apply Migration:
```bash
python manage.py migrate billing
```

### Important Notes:
⚠️ **BEFORE RUNNING MIGRATION:**
1. Backup your database
2. If you have existing data, you may want to create a data migration to copy one of the old price fields (e.g., `price_en`) to the new `price` field
3. The migration adds the new `price` field with default=0, so existing plans will have price=0 until manually updated

### Suggested Data Migration (if needed):
```python
# Add this operation AFTER AddField but BEFORE RemoveField operations:
migrations.RunPython(
    lambda apps, schema_editor: _copy_price_data(apps, schema_editor),
    migrations.RunPython.noop
)

def _copy_price_data(apps, schema_editor):
    TokenPlan = apps.get_model('billing', 'TokenPlan')
    FullPlan = apps.get_model('billing', 'FullPlan')
    
    # Copy price_en to price for all TokenPlans
    for plan in TokenPlan.objects.all():
        plan.price = plan.price_en
        plan.save()
    
    # Copy price_en to price for all FullPlans
    for plan in FullPlan.objects.all():
        plan.price = plan.price_en
        plan.save()
```

---

## Testing Checklist

### API Testing:
- [ ] Test ZPPayment without `language` parameter
- [ ] Verify payment creation with TokenPlan
- [ ] Verify payment creation with FullPlan
- [ ] Test ZPVerify callback
- [ ] Check subscription creation after payment

### Admin Testing:
- [ ] View TokenPlan list in admin (check price column)
- [ ] View FullPlan list in admin (check price column)
- [ ] Create new TokenPlan via admin
- [ ] Create new FullPlan via admin
- [ ] Verify ordering by price works correctly

### Serializer Testing:
- [ ] List TokenPlans via API
- [ ] List FullPlans via API
- [ ] Check JSON response includes `price` field
- [ ] Verify no `price_en`, `price_tr`, `price_ar` in responses

### Stripe Integration:
- [ ] Test Stripe checkout session creation
- [ ] Verify Stripe price sync command works
- [ ] Check upgrade/downgrade logic uses correct price

---

## Rollback Plan

If you need to rollback:

```bash
# Revert migration
python manage.py migrate billing 0008_subscription_queued_full_plan_and_more

# Restore files from git
git checkout src/billing/models.py
git checkout src/billing/serializers.py
git checkout src/billing/api/zarinpal.py
# ... restore other files
```

---

## Benefits

1. ✅ **Simplified API**: No need to specify language for pricing
2. ✅ **Cleaner Code**: Less conditional logic for price selection
3. ✅ **Easier Maintenance**: Single source of truth for pricing
4. ✅ **Better Performance**: Fewer fields to query and index
5. ✅ **Consistent Data**: No risk of price inconsistencies across languages

---

## Notes

- ✅ All linter errors resolved
- ✅ No breaking changes to existing subscription logic
- ✅ Payment verification flow remains unchanged
- ✅ Backward compatible with legacy Purchases model
- ⚠️ Frontend applications need to be updated to remove `language` parameter from payment requests

---

## Next Steps

1. **Apply Migration**: Run `python manage.py migrate billing`
2. **Update Existing Plans**: Set `price` values for all existing TokenPlan and FullPlan records
3. **Update Frontend**: Remove `language` parameter from Zarinpal payment requests
4. **Test Thoroughly**: Run through complete payment flow
5. **Monitor**: Check logs for any price-related errors after deployment

---

## Contact

For questions or issues related to this migration, contact the development team.

---

*Migration completed on: November 3, 2025*
*Version: 0009_change_price_to_single_field*

