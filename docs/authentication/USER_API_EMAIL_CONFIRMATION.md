# 📧 User APIs with Email Confirmation Data

## ✅ Implementation Complete

All user APIs now include email confirmation status and data.

---

## **Updated APIs**

### **1. Login API**
**POST** `/api/v1/accounts/login`

**Request:**
```json
{
  "email_or_username": "user@example.com",
  "password": "password123"
}
```

**Response:**
```json
{
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "user_data": {
    "id": "12345",
    "email": "user@example.com",
    "email_confirmed": false,
    "email_confirmation_status": {
      "email_confirmed": false,
      "has_pending_confirmation": true,
      "pending_tokens_count": 1,
      "confirmation_required": true,
      "latest_token_expires_at": "2024-08-24T10:15:30Z",
      "can_resend_confirmation": true
    },
    "first_name": "John",
    "last_name": "Doe",
    "username": "johndoe",
    "phone_number": "+1234567890",
    // ... all other user fields
  }
}
```

---

### **2. Profile API**
**GET** `/api/v1/accounts/profile`

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response:**
```json
{
  "id": "12345",
  "email": "user@example.com",
  "email_confirmed": false,
  "email_confirmation_status": {
    "email_confirmed": false,
    "has_pending_confirmation": true,
    "pending_tokens_count": 1,
    "confirmation_required": true,
    "latest_token_expires_at": "2024-08-24T10:15:30Z",
    "can_resend_confirmation": true
  },
  "first_name": "John",
  "last_name": "Doe",
  "username": "johndoe",
  "phone_number": "+1234567890",
  "age": 30,
  "gender": "M",
  "address": "123 Main St",
  "organisation": "Tech Corp",
  "description": "Software Developer",
  "profile_picture": "https://example.com/profile.jpg",
  "state": "CA",
  "zip_code": "90210",
  "country": "USA",
  "language": "en",
  "time_zone": "UTC",
  "currency": "USD",
  "business_type": "Technology",
  "default_reply_handler": "AI",
  "wizard_complete": true,
  "created_at": "2024-08-20T10:00:00Z",
  "updated_at": "2024-08-24T09:30:00Z",
  // ... all other user fields
}
```

---

### **3. Profile Update API**
**PATCH** `/api/v1/accounts/profile`

**Headers:**
```
Authorization: Bearer <access_token>
```

**Request:**
```json
{
  "first_name": "Jane",
  "last_name": "Smith"
}
```

**Response:**
```json
{
  "id": "12345",
  "email": "user@example.com",
  "email_confirmed": false,
  "email_confirmation_status": {
    "email_confirmed": false,
    "has_pending_confirmation": true,
    "pending_tokens_count": 1,
    "confirmation_required": true,
    "latest_token_expires_at": "2024-08-24T10:15:30Z",
    "can_resend_confirmation": true
  },
  "first_name": "Jane",  // Updated
  "last_name": "Smith",  // Updated
  // ... all other fields
}
```

**Note:** `email_confirmed` is read-only and can only be updated via the email confirmation API.

---

## **Email Confirmation Status Fields**

| Field | Type | Description |
|-------|------|-------------|
| `email_confirmed` | boolean | Whether user's email is confirmed |
| `email_confirmation_status` | object | Detailed confirmation status |
| `├─ email_confirmed` | boolean | Same as above (for consistency) |
| `├─ has_pending_confirmation` | boolean | Whether user has valid pending tokens |
| `├─ pending_tokens_count` | integer | Number of valid pending tokens |
| `├─ confirmation_required` | boolean | Whether confirmation is required |
| `├─ latest_token_expires_at` | string | ISO datetime of latest token expiry |
| `└─ can_resend_confirmation` | boolean | Whether user can request new code |

---

## **Email Confirmation Status Examples**

### **Unconfirmed Email with Pending Token:**
```json
{
  "email_confirmed": false,
  "email_confirmation_status": {
    "email_confirmed": false,
    "has_pending_confirmation": true,
    "pending_tokens_count": 1,
    "confirmation_required": true,
    "latest_token_expires_at": "2024-08-24T10:15:30Z",
    "can_resend_confirmation": true
  }
}
```

### **Confirmed Email:**
```json
{
  "email_confirmed": true,
  "email_confirmation_status": {
    "email_confirmed": true,
    "has_pending_confirmation": false,
    "pending_tokens_count": 0,
    "confirmation_required": false,
    "latest_token_expires_at": null,
    "can_resend_confirmation": false
  }
}
```

### **Unconfirmed Email with Expired Token:**
```json
{
  "email_confirmed": false,
  "email_confirmation_status": {
    "email_confirmed": false,
    "has_pending_confirmation": false,
    "pending_tokens_count": 0,
    "confirmation_required": true,
    "latest_token_expires_at": null,
    "can_resend_confirmation": true
  }
}
```

---

## **Frontend Integration Guide**

### **Login Flow:**
```javascript
// After successful login
const response = await login(email, password);
const user = response.user_data;

if (!user.email_confirmed) {
  // Show email confirmation prompt
  showEmailConfirmationPrompt({
    email: user.email,
    hasToken: user.email_confirmation_status.has_pending_confirmation,
    expiresAt: user.email_confirmation_status.latest_token_expires_at
  });
}
```

### **Profile Display:**
```javascript
// In profile component
const user = await getProfile();

if (!user.email_confirmed) {
  showBanner({
    type: 'warning',
    message: 'Please confirm your email address',
    action: user.email_confirmation_status.can_resend_confirmation ? 'Resend' : null
  });
}
```

### **Email Confirmation Banner:**
```javascript
function EmailConfirmationBanner({ user }) {
  const status = user.email_confirmation_status;
  
  if (status.email_confirmed) return null;
  
  return (
    <div className="confirmation-banner warning">
      <p>Please confirm your email address to activate all features.</p>
      {status.has_pending_confirmation ? (
        <p>Check your inbox for the confirmation code (expires at {status.latest_token_expires_at})</p>
      ) : (
        <button onClick={resendConfirmation}>Send Confirmation Email</button>
      )}
    </div>
  );
}
```

---

## **API Endpoints Summary**

| API | Email Confirmation Data | Notes |
|-----|------------------------|-------|
| `POST /accounts/login` | ✅ In `user_data` | Includes status on login |
| `GET /accounts/profile` | ✅ In response | Full profile with status |
| `PATCH /accounts/profile` | ✅ In response | Status after updates |
| `POST /accounts/register` | ✅ In `user_data` | New registrations |
| `POST /accounts/email/confirm` | ✅ In response | Confirmation result |
| `POST /accounts/email/resend` | ✅ In response | Resend result |
| `GET /accounts/email/status` | ✅ Full response | Dedicated status check |

---

## **Benefits**

1. **Consistent Data:** All user APIs include email confirmation status
2. **Frontend Ready:** Easy to build UI based on confirmation state
3. **Real-time Status:** Always up-to-date token information
4. **User Experience:** Clear indication of confirmation requirements
5. **Security:** Read-only email_confirmed field prevents manipulation

The email confirmation system is now fully integrated into all user APIs! 🎉
