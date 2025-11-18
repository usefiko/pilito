# Account Linking API Documentation

This document describes the new API endpoints for linking email addresses to phone-based accounts and phone numbers to email-based accounts.

## Overview

Users can now add additional authentication methods to their existing accounts:
- **Phone users** can add and verify an email address
- **Email users** can add and verify a phone number

All endpoints require authentication and follow the same OTP/email verification patterns already used in the application.

---

## 🔐 Authentication Required

All endpoints in this document require the user to be authenticated. Include the JWT token in the request headers:

```
Authorization: Bearer <your_access_token>
```

---

## 📧 Add Email to Phone-Based Account

### 1. Send Email Verification Code

**Endpoint:** `POST /api/accounts/link/email`

**Description:** Sends a 6-digit verification code to the provided email address.

**Request Body:**
```json
{
  "email": "user@example.com"
}
```

**Success Response (200):**
```json
{
  "email": "user@example.com",
  "message": "Verification code sent to your email",
  "expires_in": 900
}
```

**Error Responses:**
- `400 Bad Request` - Email already linked to another account or invalid email
- `401 Unauthorized` - Not authenticated
- `429 Too Many Requests` - Rate limit exceeded (2 minute wait time)

**Example:**
```bash
curl -X POST http://localhost:8000/api/accounts/link/email \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com"}'
```

---

### 2. Verify Email Code

**Endpoint:** `POST /api/accounts/link/email/verify`

**Description:** Verifies the code sent to email and links the email to the user's account.

**Request Body:**
```json
{
  "code": "123456"
}
```

**Success Response (200):**
```json
{
  "message": "Email linked successfully!",
  "email": "user@example.com",
  "email_confirmed": true
}
```

**Error Responses:**
- `400 Bad Request` - Invalid or expired code
- `401 Unauthorized` - Not authenticated

**Example:**
```bash
curl -X POST http://localhost:8000/api/accounts/link/email/verify \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"code": "123456"}'
```

---

## 📱 Add Phone to Email-Based Account

### 1. Send Phone OTP

**Endpoint:** `POST /api/accounts/link/phone`

**Description:** Sends a 6-digit OTP code to the provided phone number via SMS.

**Request Body:**
```json
{
  "phone_number": "+989123456789"
}
```

**Success Response (200):**
```json
{
  "phone_number": "+989123456789",
  "message": "OTP sent successfully",
  "expires_in": 300
}
```

**Error Responses:**
- `400 Bad Request` - Phone already linked to another account or invalid format
- `401 Unauthorized` - Not authenticated
- `429 Too Many Requests` - Rate limit exceeded (5 minute wait time)

**Example:**
```bash
curl -X POST http://localhost:8000/api/accounts/link/phone \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"phone_number": "+989123456789"}'
```

---

### 2. Verify Phone OTP

**Endpoint:** `POST /api/accounts/link/phone/verify`

**Description:** Verifies the OTP sent to phone and links the phone number to the user's account.

**Request Body:**
```json
{
  "phone_number": "+989123456789",
  "code": "123456"
}
```

**Success Response (200):**
```json
{
  "message": "Phone number linked successfully!",
  "phone_number": "+989123456789"
}
```

**Error Responses:**
- `400 Bad Request` - Invalid OTP, expired, or phone already linked to another account
- `401 Unauthorized` - Not authenticated

**Note:** Maximum 3 verification attempts per OTP. After 3 failed attempts, request a new OTP.

**Example:**
```bash
curl -X POST http://localhost:8000/api/accounts/link/phone/verify \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"phone_number": "+989123456789", "code": "123456"}'
```

---

## ⚡ Rate Limits

To prevent abuse, the following rate limits are enforced:

- **Email verification**: 1 code every 2 minutes per user
- **Phone OTP**: 1 OTP every 5 minutes per phone number
- **API requests**: 10 requests per minute for authenticated users

---

## 🔒 Security Features

1. **Duplicate Prevention**: Cannot link email/phone already used by another account
2. **Expiration**: 
   - Email codes expire after 15 minutes
   - Phone OTPs expire after 5 minutes
3. **Attempt Limiting**: Maximum 3 verification attempts per OTP
4. **Rate Limiting**: Prevents spam and abuse
5. **Authentication Required**: Only logged-in users can add credentials

---

## 📋 Error Handling

### Common Error Codes

| Status Code | Meaning |
|-------------|---------|
| 400 | Bad Request - Validation error or invalid input |
| 401 | Unauthorized - Authentication required |
| 429 | Too Many Requests - Rate limit exceeded |
| 500 | Internal Server Error - Server-side error |

### Example Error Response:
```json
{
  "email": ["This email is already linked to another account."]
}
```

Or for rate limiting:
```json
{
  "detail": "Please wait 1 minute(s) and 30 second(s) before requesting a new code."
}
```

---

## 🎯 Implementation Details

### New Files Created:

1. **`accounts/serializers/linking.py`**
   - `SendEmailCodeForLinkingSerializer`
   - `VerifyEmailCodeForLinkingSerializer`
   - `SendOTPForLinkingSerializer`
   - `VerifyOTPForLinkingSerializer`

2. **`accounts/api/linking.py`**
   - `AddEmailSendCodeAPIView`
   - `AddEmailVerifyCodeAPIView`
   - `AddPhoneSendOTPAPIView`
   - `AddPhoneVerifyOTPAPIView`

### Updated Files:
- `accounts/urls.py` - Added new URL patterns
- `accounts/api/__init__.py` - Exported new views
- `accounts/serializers/__init__.py` - Exported new serializers

### Existing Models Used:
- `EmailConfirmationToken` - For email verification codes
- `OTPToken` - For phone OTP codes
- `User` - Updated with new email/phone fields

### Utilities Reused:
- `send_email_confirmation()` - Sends email verification codes
- Kavenegar API - Sends SMS OTP codes

---

## 🧪 Testing

### Test Flow 1: Add Email to Phone User

1. Register/login with phone number
2. Call `POST /api/accounts/link/email` with email
3. Check email inbox for 6-digit code
4. Call `POST /api/accounts/link/email/verify` with code
5. Verify user now has email linked and confirmed

### Test Flow 2: Add Phone to Email User

1. Register/login with email
2. Call `POST /api/accounts/link/phone` with phone number
3. Check SMS for 6-digit OTP
4. Call `POST /api/accounts/link/phone/verify` with phone and OTP
5. Verify user now has phone number linked

---

## 📚 Swagger/OpenAPI Documentation

All endpoints are documented with Swagger annotations and will appear in your API documentation at:

```
http://localhost:8000/swagger/
http://localhost:8000/redoc/
```

**Tags:**
- All new endpoints are tagged as `Account Linking` for easy navigation

---

## ✅ Requirements Met

- ✅ Uses existing OTP + email code utilities
- ✅ All APIs are authenticated (require login)
- ✅ Handles duplicate email/phone cases
- ✅ Handles already verified email/phone cases
- ✅ Stores verified data in User model
- ✅ Follows Django DRF best practices
- ✅ Complete Swagger/OpenAPI documentation
- ✅ Comprehensive serializers and views
- ✅ Proper error handling and validation
- ✅ Rate limiting to prevent abuse

---

## 🚀 Next Steps

1. **Run migrations** (if any new migrations were created)
2. **Test endpoints** using Swagger UI or Postman
3. **Verify SMS sending** works with Kavenegar
4. **Verify email sending** works with configured SMTP
5. **Update frontend** to call these new endpoints

---

## 📞 Support

For questions or issues with these endpoints:
- Check server logs for detailed error messages
- Verify Kavenegar API key is configured correctly
- Verify email SMTP settings are configured
- Check rate limiting settings in Django settings

---

**Version:** 1.0  
**Created:** November 2025  
**Project:** Pilito

