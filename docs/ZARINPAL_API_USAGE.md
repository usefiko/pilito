# Zarinpal Payment API - Usage Guide

## Overview
The Zarinpal payment integration has been updated to work with the modern billing system using `TokenPlan`, `FullPlan`, `Subscription`, and `Payment` models.

## API Endpoints

### 1. Initiate Payment - `ZPPayment`
**Endpoint:** `POST /billing/zp-pay`

**Authentication:** Required (IsAuthenticated)

**Request Body:**
```json
{
  "token_plan_id": 1     // For token-only plans (OR use full_plan_id)
}
```

OR

```json
{
  "full_plan_id": 2      // For full plans with duration (OR use token_plan_id)
}
```

**Response:**
```json
{
  "payment": {
    "id": 123,
    "user": 456,
    "token_plan": 1,
    "full_plan": null,
    "amount": "49.99",
    "status": "pending",
    "authority": "A00000000000000000000000000123456789",
    ...
  },
  "data": {
    "status": true,
    "url": "https://www.zarinpal.com/pg/StartPay/A00000000000000000000000000123456789",
    "payment_id": 123,
    "authority": "A00000000000000000000000000123456789"
  }
}
```

**Usage Flow:**
1. User selects a plan (TokenPlan or FullPlan)
2. Frontend calls this API with plan_id and language
3. API creates a Payment record with status='pending'
4. API requests payment authorization from Zarinpal
5. API returns payment URL
6. Redirect user to the payment URL

---

### 2. Verify Payment - `ZPVerify`
**Endpoint:** `GET /billing/zp-verify/{payment_id}/?Authority=xxx&Status=OK`

**Authentication:** Not required (AllowAny - called by Zarinpal)

**Query Parameters:**
- `Authority`: Payment authority from Zarinpal
- `Status`: Payment status ("OK" or "NOK")

**Automatic Flow:**
1. Zarinpal redirects user to this endpoint after payment
2. API verifies payment with Zarinpal
3. If successful:
   - Updates Payment status to 'completed'
   - Creates or updates user Subscription
   - Adds tokens to user account
4. Redirects user to success/failure page

---

## Subscription Logic

### For New/Inactive Subscriptions:
- Creates new subscription immediately
- Sets tokens_remaining to plan's tokens_included
- For TokenPlan: No expiration date
- For FullPlan: Sets expiration based on duration_days

### For Active Subscriptions:
- Queues the new plan for later activation
- Sets queued_token_plan or queued_full_plan
- Sets queued_tokens_amount
- Plan activates automatically when current plan expires

---

## Payment Status Flow

1. **pending**: Payment created, waiting for user to complete payment
2. **completed**: Payment verified and subscription activated
3. **failed**: Payment verification failed
4. **cancelled**: User cancelled payment
5. **refunded**: Payment refunded (manual)

---

## Example Frontend Integration

```javascript
// Step 1: Initiate Payment
const response = await fetch('/billing/zp-pay', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${accessToken}`
  },
  body: JSON.stringify({
    full_plan_id: 2
  })
});

const data = await response.json();

// Step 2: Redirect to Zarinpal
if (data.data.status) {
  window.location.href = data.data.url;
}

// Step 3: User completes payment on Zarinpal
// Step 4: Zarinpal redirects to /billing/zp-verify/{payment_id}/
// Step 5: API verifies and creates subscription
// Step 6: User redirected to success/failure page
```

---

## Models Used

### TokenPlan
- Token-only plans without expiration
- Fields: name, price, tokens_included
- Example: "100 Tokens Package"

### FullPlan  
- Complete plans with tokens and duration
- Fields: name, price, tokens_included, duration_days
- Example: "Pro Monthly - 1000 tokens for 30 days"

### Subscription
- User's active subscription
- Fields: user, token_plan/full_plan, tokens_remaining, start_date, end_date, status
- Supports queued plans for renewals

### Payment
- Payment transaction records
- Fields: user, subscription, token_plan/full_plan, amount, status, authority, ref_id
- Tracks all payment attempts and completions

---

## Testing

### Test Payment Flow:
```bash
# 1. Get available plans
curl -H "Authorization: Bearer {token}" http://localhost:8000/billing/plans/

# 2. Initiate payment
curl -X POST http://localhost:8000/billing/zp-pay \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{"full_plan_id": 1}'

# 3. Visit returned URL in browser
# 4. Complete payment on Zarinpal (use test card in sandbox mode)
# 5. Verify redirect to success page
# 6. Check subscription status
curl -H "Authorization: Bearer {token}" http://localhost:8000/billing/subscription/
```

---

## Configuration Required

Make sure these settings are configured in `settings.py`:

```python
# Zarinpal Configuration
ZARRINPAL_MERCHANT_ID = 'your-merchant-id'
ZP_API_REQUEST = 'https://api.zarinpal.com/pg/v4/payment/request.json'
ZP_API_VERIFY = 'https://api.zarinpal.com/pg/v4/payment/verify.json'
ZP_API_STARTPAY = 'https://www.zarinpal.com/pg/StartPay/'
ZARIN_CALL_BACK = 'https://api.pilito.com/billing/zp-verify/'
```

For testing, use Zarinpal Sandbox:
```python
ZARRINPAL_MERCHANT_ID = 'sandbox-merchant-id'
ZP_API_REQUEST = 'https://sandbox.zarinpal.com/pg/v4/payment/request.json'
ZP_API_VERIFY = 'https://sandbox.zarinpal.com/pg/v4/payment/verify.json'
ZP_API_STARTPAY = 'https://sandbox.zarinpal.com/pg/StartPay/'
```

---

## Changes Made

### Files Modified:

1. **`billing/serializers.py`**
   - Added `ZarinpalPaymentSerializer` for payment initiation
   - Validates token_plan_id or full_plan_id

2. **`billing/api/zarinpal.py`**
   - Added `ZPPayment` class for payment initiation
   - Added `ZPVerify` class for payment verification
   - Implements subscription creation/update logic
   - Handles queued plans for active subscriptions

3. **`billing/api/__init__.py`**
   - Exported ZPPayment and ZPVerify classes

4. **`billing/urls.py`** (already configured)
   - `path("zp-pay", ZPPayment.as_view(), name="zp-payment")`
   - `path("zp-verify/<int:id>/", ZPVerify.as_view(), name="zp-verify")`

---

## Notes

- Currency conversion: Zarinpal uses Rials, code multiplies Toman by 10
- Transaction safety: Uses `@transaction.atomic` for database integrity
- Idempotency: Checks if payment already completed to prevent double-processing
- Error handling: Proper status updates for failed/cancelled payments
- Legacy support: Old Payment/PaymentVerify classes still available for backward compatibility

