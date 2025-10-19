# OTP Authentication with Kavenegar

This document explains how to use the new OTP (One-Time Password) authentication feature integrated with Kavenegar SMS service.

## Overview

The OTP authentication system allows users to log in using their phone number by receiving a 6-digit verification code via SMS. This provides a secure and convenient authentication method.

## Features

- ✅ Send OTP code to Iranian phone numbers
- ✅ 6-digit verification code
- ✅ Configurable expiry time (default: 5 minutes)
- ✅ Rate limiting to prevent abuse
- ✅ Maximum verification attempts (default: 3 attempts)
- ✅ Automatic user creation on first login
- ✅ JWT token generation upon successful verification
- ✅ Admin panel for managing OTP tokens

## Configuration

### 1. Environment Variables

Add the following environment variables to your `.env` file:

```bash
# Kavenegar SMS Configuration
KAVENEGAR_API_KEY=your_kavenegar_api_key_here
KAVENEGAR_SENDER=10008663  # Your Kavenegar sender number
OTP_EXPIRY_TIME=300  # OTP expiry time in seconds (default: 5 minutes)
OTP_MAX_ATTEMPTS=3   # Maximum verification attempts (default: 3)
```

### 2. Install Requirements

The required package `kavenegar==1.1.2` has been added to `requirements/base.txt`. Install it:

```bash
pip install -r src/requirements/base.txt
```

Or specifically:

```bash
pip install kavenegar==1.1.2
```

### 3. Run Migrations

Apply the new OTP model migration:

```bash
cd src
python manage.py migrate accounts
```

## API Endpoints

### 1. Send OTP

**Endpoint:** `POST /api/v1/usr/otp`

**Description:** Sends a 6-digit OTP code to the specified phone number via SMS.

**Request Body:**
```json
{
  "phone_number": "+989123456789"
}
```

Or:
```json
{
  "phone_number": "09123456789"
}
```

**Response (Success):**
```json
{
  "phone_number": "+989123456789",
  "message": "OTP sent successfully",
  "expires_in": 300
}
```

**Response (Error):**
```json
{
  "phone_number": ["Please provide a valid Iranian phone number starting with +98 or 09"]
}
```

**Rate Limiting:**
- Maximum 5 requests per minute
- Maximum 3 OTP requests per phone number within 2 minutes

### 2. Verify OTP

**Endpoint:** `POST /api/v1/usr/otp/verify`

**Description:** Verifies the OTP code and authenticates/creates the user.

**Request Body:**
```json
{
  "phone_number": "+989123456789",
  "code": "123456"
}
```

**Response (Success):**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "is_new_user": false,
  "user": {
    "id": 1,
    "phone_number": "+989123456789",
    "email": "989123456789@temp.pilito.com",
    "username": "989123456789",
    "first_name": null,
    "last_name": null
  }
}
```

**Response (Error - Invalid Code):**
```json
{
  "code": ["Invalid OTP code. 2 attempt(s) remaining."]
}
```

**Response (Error - Expired):**
```json
{
  "code": ["OTP has expired or maximum attempts exceeded. Please request a new one."]
}
```

## SMS Message Format

The SMS sent to users contains:

```
کد تایید شما: 123456

این کد تا 5 دقیقه اعتبار دارد.
```

Translation: "Your verification code: 123456. This code is valid for 5 minutes."

## Security Features

### Rate Limiting
- Anonymous users: 5 requests per minute
- Phone-specific: Maximum 3 OTP requests within 2 minutes

### OTP Validation
- ✅ 6-digit numeric code only
- ✅ Time-based expiration (default: 5 minutes)
- ✅ Maximum attempts limit (default: 3 attempts)
- ✅ Single-use tokens (marked as used after verification)
- ✅ Automatic invalidation of previous OTPs when requesting new one

### User Creation
When a user verifies OTP for the first time:
- Username: Phone number (without + sign)
- Email: Temporary email format: `{phone}@temp.pilito.com`
- Phone: Stored in international format (+98...)

## Admin Panel

The OTP tokens can be managed in Django Admin at `/admin/accounts/otptoken/`:

**List View Shows:**
- Phone number
- OTP code
- Creation time
- Expiration time
- Usage status
- Verification attempts
- Validation status

**Actions Available:**
- View OTP details
- Check if OTP is still valid
- Track verification attempts

## Usage Examples

### Frontend Integration (JavaScript)

```javascript
// Step 1: Send OTP
async function sendOTP(phoneNumber) {
  const response = await fetch('/api/v1/usr/otp', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      phone_number: phoneNumber
    })
  });
  
  const data = await response.json();
  
  if (response.ok) {
    console.log('OTP sent successfully');
    return data;
  } else {
    console.error('Error:', data);
    throw new Error(data.phone_number?.[0] || 'Failed to send OTP');
  }
}

// Step 2: Verify OTP
async function verifyOTP(phoneNumber, code) {
  const response = await fetch('/api/v1/usr/otp/verify', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      phone_number: phoneNumber,
      code: code
    })
  });
  
  const data = await response.json();
  
  if (response.ok) {
    // Store tokens
    localStorage.setItem('access_token', data.access_token);
    localStorage.setItem('refresh_token', data.refresh_token);
    
    // Check if new user
    if (data.is_new_user) {
      console.log('Welcome new user!');
      // Redirect to profile completion
    } else {
      console.log('Welcome back!');
      // Redirect to dashboard
    }
    
    return data;
  } else {
    console.error('Error:', data);
    throw new Error(data.code?.[0] || 'Failed to verify OTP');
  }
}

// Usage
try {
  await sendOTP('+989123456789');
  // User receives SMS...
  const result = await verifyOTP('+989123456789', '123456');
  console.log('Logged in:', result.user);
} catch (error) {
  console.error('Authentication failed:', error.message);
}
```

### Python Integration

```python
import requests

# Send OTP
response = requests.post(
    'https://api.pilito.com/api/v1/usr/otp',
    json={'phone_number': '+989123456789'}
)
print(response.json())

# Verify OTP
response = requests.post(
    'https://api.pilito.com/api/v1/usr/otp/verify',
    json={
        'phone_number': '+989123456789',
        'code': '123456'
    }
)

if response.status_code == 200:
    data = response.json()
    access_token = data['access_token']
    refresh_token = data['refresh_token']
    print(f"Logged in as user {data['user']['id']}")
```

## Testing

### Manual Testing

1. **Test sending OTP:**
   ```bash
   curl -X POST http://localhost:8000/api/v1/usr/otp \
     -H "Content-Type: application/json" \
     -d '{"phone_number": "+989123456789"}'
   ```

2. **Check the OTP in admin panel:**
   - Go to http://localhost:8000/admin/accounts/otptoken/
   - Find the latest OTP code for your phone number

3. **Test verifying OTP:**
   ```bash
   curl -X POST http://localhost:8000/api/v1/usr/otp/verify \
     -H "Content-Type: application/json" \
     -d '{"phone_number": "+989123456789", "code": "123456"}'
   ```

### Development Mode

For development/testing without sending actual SMS, you can:

1. Comment out the Kavenegar SMS sending code in `accounts/serializers/otp.py`
2. Always check the OTP code in the admin panel
3. Or log the OTP code to console instead of sending SMS

## Troubleshooting

### Common Issues

**Issue: "SMS service is not configured"**
- **Solution:** Make sure `KAVENEGAR_API_KEY` is set in your environment variables

**Issue: "Too many OTP requests"**
- **Solution:** Wait 2 minutes before requesting a new OTP for the same phone number

**Issue: "Invalid OTP code"**
- **Solution:** Check that you're using the most recent OTP code
- **Solution:** Verify the code hasn't expired (5 minutes by default)
- **Solution:** Check remaining attempts (max 3 by default)

**Issue: "Failed to send OTP"**
- **Solution:** Check Kavenegar API key is valid
- **Solution:** Verify Kavenegar account has sufficient credit
- **Solution:** Check phone number format (must be Iranian: +98 or 09)

### Logs

Check Django logs for detailed error messages:
```bash
tail -f src/logs/django.log
```

## Production Checklist

Before deploying to production:

- [ ] Set proper `KAVENEGAR_API_KEY` in production environment
- [ ] Configure `KAVENEGAR_SENDER` with your verified sender number
- [ ] Set appropriate `OTP_EXPIRY_TIME` (recommended: 300 seconds)
- [ ] Set appropriate `OTP_MAX_ATTEMPTS` (recommended: 3)
- [ ] Enable HTTPS for secure cookie transmission
- [ ] Set `secure=True` in cookie settings (line 100 in `accounts/api/otp.py`)
- [ ] Monitor SMS costs and usage through Kavenegar dashboard
- [ ] Set up monitoring for failed OTP attempts
- [ ] Configure rate limiting based on your needs

## Database Schema

### OTPToken Model

| Field | Type | Description |
|-------|------|-------------|
| id | BigAutoField | Primary key |
| phone_number | CharField(100) | Phone number in international format |
| code | CharField(6) | 6-digit OTP code |
| created_at | DateTimeField | When OTP was created |
| expires_at | DateTimeField | When OTP expires |
| is_used | BooleanField | Whether OTP has been used |
| attempts | IntegerField | Number of verification attempts |

**Indexes:**
- `phone_number` + `created_at` (descending)

## Support

For issues related to:
- **Kavenegar SMS:** Visit https://kavenegar.com/ or contact Kavenegar support
- **This implementation:** Create an issue in your project repository
- **Django/Backend:** Check Django documentation at https://docs.djangoproject.com/

## References

- [Kavenegar API Documentation](https://kavenegar.com/rest.html)
- [Django REST Framework](https://www.django-rest-framework.org/)
- [JWT Authentication](https://jwt.io/)

