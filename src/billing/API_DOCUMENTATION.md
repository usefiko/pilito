# Billing & Subscriptions API – Complete Documentation

This document provides a complete reference for billing and subscription functionality, including data models, endpoints, Stripe integration, trial handling, and examples.

## Authentication

All endpoints (unless stated) require JWT authentication.

Header:
```http
Authorization: Bearer <your_jwt_token>
```

## Base

- Billing base URL: `{{base_url}}/api/v1/billing/`
- Accounts base URL (overview): `{{base_url}}/api/v1/usr/`

## Data Models (response shapes)

### TokenPlan
- id (int)
- name (string)
- price_en (decimal string)
- price_tr (decimal string)
- price_ar (decimal string)
- tokens_included (int)
- is_recurring (bool)
- is_active (bool)
- description (string|null)
- created_at (datetime)
- updated_at (datetime)

### FullPlan
- id (int)
- name (string)
- tokens_included (int)
- duration_days (int)
- is_recommended (bool)
- is_yearly (bool)
- price_en (decimal string)
- price_tr (decimal string)
- price_ar (decimal string)
- is_active (bool)
- description (string|null)
- user_has_active_subscription (bool) - indicates if the authenticated user currently has an active subscription
- created_at (datetime)
- updated_at (datetime)

### Subscription
- id (int)
- user (int)
- user_email (string)
- token_plan (int|null)
- token_plan_details (TokenPlan|null)
- full_plan (int|null)
- full_plan_details (FullPlan|null)
- start_date (datetime)
- end_date (datetime|null)
- tokens_remaining (int)
- is_active (bool)
- status (string: trialing, active, past_due, canceled, unpaid, incomplete, incomplete_expired)
- trial_end (datetime|null)
- days_remaining (int|null)
- is_subscription_active (bool)
- created_at (datetime)
- updated_at (datetime)

### Payment
- id (int)
- user (int)
- user_email (string)
- subscription (int|null)
- subscription_id (int|null)
- token_plan (int|null)
- full_plan (int|null)
- plan_name (string|null)
- amount (decimal string)
- payment_date (datetime)
- payment_method (string: credit_card, paypal, stripe, bank_transfer, other)
- status (string: pending, completed, failed, refunded, cancelled)
- transaction_id (string|null)
- payment_gateway_response (object|null)
- ref_id (string|null) – legacy
- authority (string|null) – legacy
- created_at (datetime)
- updated_at (datetime)

## Endpoints Overview

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/plans/` | GET | List both TokenPlans and FullPlans |
| `/plans/token/` | GET | List TokenPlans only |
| `/plans/full/` | GET | List FullPlans only |
| `/purchase/` | POST | Purchase TokenPlan or FullPlan (Stripe or immediate) |
| `/subscription/` | GET | Get current subscription |
| `/subscription/refresh/` | POST | Refresh subscription status |
| `/tokens/consume/` | POST | Consume tokens |
| `/payments/` | GET | Payment history |
| `/subscriptions/` | GET | Subscription history |
| `/tokens/usage/` | GET | Token usage history |
| `/overview/` | GET | Billing overview (aggregated) |
| `/stripe/checkout-session/` | POST | Create Stripe Checkout Session (redirect flow) |
| `/stripe/customer-portal/` | POST | Create Stripe Billing Portal session |
| `/stripe/webhook/` | POST | Stripe webhook receiver (no auth) |

## Endpoints – Details & Examples

### List Plans (combined)
GET `/plans/`
```json
{
  "token_plans": [
  {
    "id": 1,
    "name": "1M Tokens",
    "price_en": "10.00",
    "price_tr": "10.00",
    "price_ar": "10.00",
    "tokens_included": 1000000,
    "is_recurring": false,
    "is_active": true,
    "description": null,
    "created_at": "...",
    "updated_at": "..."
  }
  ],
  "full_plans": [
    {
      "id": 10,
      "name": "Monthly Basic",
      "tokens_included": 1000000,
    "duration_days": 30,
      "is_recommended": false,
      "is_yearly": false,
      "price_en": "15.00",
      "price_tr": "15.00",
      "price_ar": "15.00",
    "is_active": true,
      "description": null,
      "user_has_active_subscription": true,
      "created_at": "...",
      "updated_at": "..."
    }
  ]
}
```

Also available: GET `/plans/token/`, GET `/plans/full/`.

### Purchase Plan
POST `/purchase/`

Body (choose exactly one of the ids):
```json
{ "token_plan_id": 1, "payment_method": "stripe" }
```
OR
```json
{ "full_plan_id": 10, "payment_method": "credit_card" }
```

Stripe (PaymentIntent) response:
```json
{ "message": "Stripe payment initiated", "payment_id": 123, "client_secret": "pi_12345_secret_abc" }
```

Immediate (non-Stripe) completion response:
```json
{ "message": "Plan purchased successfully", "payment_id": 124, "subscription": { /* Subscription */ } }
```

Notes:
- For TokenPlan: adds tokens; no implicit `end_date`.
- For FullPlan: adds tokens; sets `end_date = start_date + duration_days`.

### Current Subscription
GET `/subscription/`
```json
{
  "id": 45,
  "user": 67,
  "user_email": "user@example.com",
  "token_plan": null,
  "token_plan_details": null,
  "full_plan": 10,
  "full_plan_details": { "id": 10, "name": "Monthly Basic", "tokens_included": 1000000, "duration_days": 30, "is_yearly": false, "is_recommended": false, "price_en": "15.00", "price_tr": "15.00", "price_ar": "15.00", "is_active": true, "description": null, "created_at": "...", "updated_at": "..." },
  "start_date": "2024-01-15T10:30:00Z",
  "end_date": "2024-02-14T10:30:00Z",
  "tokens_remaining": 750,
  "is_active": true,
  "status": "active",
  "trial_end": null,
  "days_remaining": 25,
  "is_subscription_active": true,
  "created_at": "...",
  "updated_at": "..."
}
```

### Refresh Subscription
POST `/subscription/refresh/`
```json
{ "message": "Subscription status refreshed", "subscription": { /* Subscription */ } }
```

### Consume Tokens
POST `/tokens/consume/`
```json
{ "tokens": 50, "description": "AI message processing" }
```
Response:
```json
{ "message": "Tokens consumed successfully", "tokens_consumed": 50, "tokens_remaining": 700, "subscription_active": true }
```

### Payment History
GET `/payments/`
```json
[
  {
    "id": 123,
    "user": 67,
    "user_email": "user@example.com",
    "subscription": 45,
    "subscription_id": 45,
    "token_plan": null,
    "full_plan": 10,
    "plan_name": "Monthly Basic",
    "amount": "15.00",
    "payment_date": "2024-01-15T10:30:00Z",
    "payment_method": "stripe",
    "status": "completed",
    "transaction_id": "pi_12345",
    "payment_gateway_response": null,
    "ref_id": null,
    "authority": null,
    "created_at": "...",
    "updated_at": "..."
  }
]
```

### Subscription History
GET `/subscriptions/` → list of user subscriptions.

### Token Usage History
GET `/tokens/usage/` → list of token usage events.

### Billing Overview
GET `/overview/` → aggregated overview including current subscription snapshot and usage counters.

## Stripe Integration

### Checkout Session (redirect flow)
POST `/stripe/checkout-session/`

Body (one of `price_id` or `product_id` with default price):
```json
{ "price_id": "price_ABC123", "mode": "subscription" }
```
Response:
```json
{ "url": "https://checkout.stripe.com/c/pay/cs_test_..." }
```
- Success URL: `http://app.fiko.net/dashboard/payment/success?status=success&transaction_id={CHECKOUT_SESSION_ID}&amount=29.99&plan_name=Pro Plan`
- Cancel/Failure URL: `http://app.fiko.net/dashboard/payment/failure?status=cancelled&error_code=USER_CANCELLED&error_message=Payment was cancelled by user`
- `client_reference_id` is set to the authenticated user id.
- Frontend receives all payment details in URL query parameters

### Customer Billing Portal
POST `/stripe/customer-portal/`
```json
{ "url": "https://billing.stripe.com/session/ABC..." }
```
- Requires `stripe_customer_id` on the user subscription.
- Return URL: `settings.STRIPE_PORTAL_RETURN_URL` (default `https://app.fiko.net/account`).

### Webhook
POST `/stripe/webhook/` (no auth)
- Verifies signature using `settings.STRIPE_WEBHOOK_SECRET`.
- Handled events:
  - `payment_intent.succeeded`: complete pending Payment and apply subscription changes.
  - `payment_intent.payment_failed`: mark Payment failed.
  - `checkout.session.completed`: link `stripe_customer_id` / `stripe_subscription_id` and mark active.
  - `invoice.paid`: mark subscription `active`.
  - `invoice.payment_failed`: mark subscription `past_due` and `is_active=false`.
  - `customer.subscription.deleted`/`canceled`: mark subscription `canceled` and `is_active=false`.

### Required Settings
```python
STRIPE_SECRET_KEY = 'sk_live_...'  # or test key
STRIPE_PUBLISHABLE_KEY = 'pk_live_...'  # or test key
STRIPE_WEBHOOK_SECRET = 'whsec_...'
STRIPE_CURRENCY = 'usd'
# Success/Cancel URLs are auto-generated with payment details
# Custom URLs can be passed to checkout-session API
STRIPE_PORTAL_RETURN_URL = 'https://app.fiko.net/account'
```

## Trials & User Overview

- On new user creation, a 14-day trial subscription is created:
  - `status = trialing`, `start_date = now`, `end_date = now + 14 days`, `trial_end = end_date`, `is_active = True`.
- User overview at `{{base_url}}/api/v1/usr/overview` includes:
  - `free_trial` and `free_trial_days_left` derived from `User.created_at`.
  - `current_subscription` with full details.
  - `subscription_remaining` (%):
    - If `end_date`: `(days_remaining / total_days) * 100` (clamped 0–100).
    - Else: `100`.
  - `token_usage_remaining` (%): `tokens_remaining / original_tokens` from `token_plan` or `full_plan`.

## Errors

- 400 Bad Request:
```json
{ "error": "Insufficient tokens. Available: 50" }
```
- 404 Not Found:
```json
{ "message": "No active subscription found" }
```
- Validation Errors:
```json
{ "token_plan_id": ["Invalid or inactive token plan."] }
```

## Legacy (Backward Compatibility)
- `GET /api/v1/billing/current-plan`
- `POST /api/v1/billing/payment`
- `POST /api/v1/billing/payment-verify/<id>/`
- `GET /api/v1/billing/payment-history`

## Testing Checklist
- Plans: `/plans/`, `/plans/token/`, `/plans/full/`
- Purchase (non-Stripe): `/purchase/` returns completed payment and updated subscription
- Purchase (Stripe): `/purchase/` returns `client_secret`, webhook finalizes
- Checkout Session: `/stripe/checkout-session/` returns URL, webhook activates
- Portal: `/stripe/customer-portal/` returns URL if `stripe_customer_id` is set
- Current subscription: `/subscription/`
- Consume tokens: `/tokens/consume/`
- Overview: `/overview/`
- Webhooks: Stripe events update Payment/Subscription as expected
