# Registration API - Affiliate Code Reference

## Endpoint
**POST** `/api/v1/usr/register`

## Request Body

### Required Fields
- `username` (string): Unique username for the user
- `email` (string): Valid email address
- `password` (string): User password

### Optional Fields
- `affiliate` (string): Invite code from another user (4-digit code)

## Example Requests

### 1. Registration with Affiliate Code
```json
{
  "username": "johndoe",
  "email": "john@example.com",
  "password": "SecurePass123!",
  "affiliate": "5678"
}
```

### 2. Registration without Affiliate Code
```json
{
  "username": "janedoe",
  "email": "jane@example.com",
  "password": "SecurePass123!"
}
```

## Response Format

### Success Response (201 Created)

#### With Valid Affiliate Code
```json
{
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "user_data": {
    "is_profile_fill": false,
    "id": 123,
    "first_name": null,
    "last_name": null,
    "email": "john@example.com",
    "phone_number": null,
    "username": "johndoe",
    "age": null,
    "gender": null,
    "address": null,
    "organisation": null,
    "description": null,
    "profile_picture": "/media/user_img/default.png",
    "updated_at": "2025-12-03T10:30:00Z",
    "created_at": "2025-12-03T10:30:00Z",
    "state": null,
    "zip_code": null,
    "country": null,
    "language": null,
    "time_zone": null,
    "currency": null,
    "business_type": null,
    "default_reply_handler": "AI",
    "wizard_complete": false,
    "email_confirmed": false,
    "email_confirmation_status": {
      "email_confirmed": false,
      "has_pending_confirmation": true,
      "pending_tokens_count": 1,
      "confirmation_required": true,
      "latest_token_expires_at": "2025-12-03T10:45:00Z"
    },
    "free_trial_days_left": 14,
    "free_trial": true,
    "invite_code": "1234",
    "referred_by": 456,
    "referrer_username": "referrer_user",
    "affiliate_active": false,
    "wallet_balance": "0.00"
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

#### With Invalid Affiliate Code
```json
{
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "user_data": {
    ...
    "invite_code": "1234",
    "referred_by": null,
    "referrer_username": null,
    "affiliate_active": false,
    "wallet_balance": "0.00"
  },
  "email_confirmation_sent": true,
  "message": "Registration successful! Please check your email for confirmation code.",
  "affiliate_info": {
    "affiliate_code_provided": "9999",
    "affiliate_applied": false,
    "referrer": null,
    "error": "Invalid affiliate code"
  }
}
```

#### Without Affiliate Code
```json
{
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "user_data": {
    ...
    "invite_code": "1234",
    "referred_by": null,
    "referrer_username": null,
    "affiliate_active": false,
    "wallet_balance": "0.00"
  },
  "email_confirmation_sent": true,
  "message": "Registration successful! Please check your email for confirmation code."
}
```

### Error Response (400 Bad Request)
```json
{
  "username": ["This field is required."],
  "email": ["This field is required."],
  "password": ["This field is required."]
}
```

## Response Fields Explanation

### Root Level Fields
- `refresh_token`: JWT refresh token for obtaining new access tokens
- `access_token`: JWT access token for authenticated requests
- `user_data`: Complete user profile information (see below)
- `email_confirmation_sent`: Boolean indicating if confirmation email was sent
- `message`: Success message
- `affiliate_info`: (Optional) Only present if affiliate code was provided

### User Data Fields (Key Affiliate Fields)
- `invite_code`: User's own unique 4-digit invite code (auto-generated)
- `referred_by`: ID of the user who referred them (null if not referred)
- `referrer_username`: Username of the referrer (null if not referred)
- `affiliate_active`: Whether user has affiliate system enabled
- `wallet_balance`: User's current wallet balance (decimal, starts at 0.00)

### Affiliate Info Fields (when affiliate code is provided)
- `affiliate_code_provided`: The affiliate code that was submitted
- `affiliate_applied`: Boolean - true if code was valid and applied
- `referrer`: Object with referrer details (null if invalid code)
  - `id`: Referrer's user ID
  - `username`: Referrer's username
  - `invite_code`: Referrer's invite code (same as provided)
- `error`: Error message if code was invalid (null if valid)

## Business Logic

### When Valid Affiliate Code is Provided:
1. System finds the user with matching `invite_code`
2. Sets new user's `referred_by` field to the referrer
3. Adds $10.00 to referrer's `wallet_balance`
4. Returns referrer information in response
5. Returns success confirmation in `affiliate_info`

### When Invalid Affiliate Code is Provided:
1. Registration proceeds normally (doesn't fail)
2. `referred_by` remains null
3. No bonus is added to any wallet
4. Returns error message in `affiliate_info.error`

### When No Affiliate Code is Provided:
1. Registration proceeds normally
2. User still gets their own unique `invite_code`
3. `affiliate_info` is not included in response

## Frontend Integration Tips

### Check if Affiliate was Applied
```javascript
const response = await registerUser(data);
const affiliateApplied = response.affiliate_info?.affiliate_applied || false;

if (affiliateApplied) {
  showSuccessMessage(`Successfully registered with referral from ${response.affiliate_info.referrer.username}`);
} else if (response.affiliate_info?.error) {
  showWarningMessage(`Registration successful, but: ${response.affiliate_info.error}`);
}
```

### Display User's Own Invite Code
```javascript
const userInviteCode = response.user_data.invite_code;
const inviteLink = `https://yourapp.com/register?affiliate=${userInviteCode}`;

// Display to user: "Share your invite code: 1234"
// Or: "Share your invite link: [URL]"
```

### Check if User was Referred
```javascript
const wasReferred = response.user_data.referred_by !== null;

if (wasReferred) {
  console.log(`Referred by: ${response.user_data.referrer_username}`);
}
```

## HTTP Status Codes
- `201 Created`: Registration successful
- `400 Bad Request`: Invalid input data (missing required fields, invalid email, etc.)
- `500 Internal Server Error`: Server error during registration

## Authentication
This endpoint does **not** require authentication (public endpoint).

## Rate Limiting
Standard rate limiting applies. Consider implementing throttling for abuse prevention.

## Notes
- Invite codes are always 4 digits (numbers only)
- Invite codes are automatically generated for all users upon registration
- Invalid affiliate codes do NOT prevent registration from succeeding
- Referral bonus amount is currently fixed at $10.00
- The response includes JWT tokens that should be stored for subsequent authenticated requests
- The access token should be included in subsequent requests as: `Authorization: Bearer <access_token>`

