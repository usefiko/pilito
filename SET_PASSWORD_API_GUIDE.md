# Set Password API Guide

## Overview
This API endpoint allows authenticated users to set a new password without requiring their current password. The user only needs to be authenticated (provide a valid JWT token).

## Endpoint

**URL:** `/accounts/set-password`  
**Method:** `POST`  
**Authentication:** Required (JWT Bearer Token)

## Request

### Headers
```
Authorization: Bearer <your_access_token>
Content-Type: application/json
```

### Body Parameters
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `new_password` | string | Yes | The new password to set (must meet password requirements) |
| `confirm_new_password` | string | Yes | Confirmation of the new password (must match `new_password`) |

### Password Requirements
- Minimum 8 characters long
- At least one lowercase character (a-z)
- At least one number, symbol, or whitespace character

### Example Request
```json
{
  "new_password": "MyNewSecurePass123!",
  "confirm_new_password": "MyNewSecurePass123!"
}
```

## Response

### Success Response (200 OK)
```json
{
  "message": "Password set successfully"
}
```

### Error Responses

#### 400 Bad Request - Validation Errors
```json
{
  "new_password": [
    "Password must be at least 8 characters long."
  ]
}
```

```json
{
  "non_field_errors": [
    "New password and confirm password do not match."
  ]
}
```

#### 401 Unauthorized
```json
{
  "detail": "Authentication credentials were not provided."
}
```

## Usage Examples

### cURL
```bash
curl -X POST https://your-domain.com/accounts/set-password \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "new_password": "MyNewSecurePass123!",
    "confirm_new_password": "MyNewSecurePass123!"
  }'
```

### Python (requests)
```python
import requests

url = "https://your-domain.com/accounts/set-password"
headers = {
    "Authorization": "Bearer YOUR_ACCESS_TOKEN",
    "Content-Type": "application/json"
}
data = {
    "new_password": "MyNewSecurePass123!",
    "confirm_new_password": "MyNewSecurePass123!"
}

response = requests.post(url, headers=headers, json=data)
print(response.json())
```

### JavaScript (fetch)
```javascript
const url = 'https://your-domain.com/accounts/set-password';
const accessToken = 'YOUR_ACCESS_TOKEN';

fetch(url, {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${accessToken}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    new_password: 'MyNewSecurePass123!',
    confirm_new_password: 'MyNewSecurePass123!'
  })
})
.then(response => response.json())
.then(data => console.log(data))
.catch(error => console.error('Error:', error));
```

## Security Notes

1. **Authentication Required**: This endpoint requires a valid JWT access token. The user must be authenticated before they can set a new password.

2. **No Current Password Required**: Unlike the `/accounts/change-password` endpoint, this endpoint does NOT require the user to provide their current password. This is useful for:
   - Users who logged in via OAuth (Google) and don't have a password yet
   - Password recovery scenarios where the user is authenticated but doesn't remember their current password
   - Admin-initiated password resets

3. **Password Validation**: The new password must meet security requirements to ensure strong passwords.

4. **Session Management**: After setting a new password, existing sessions remain valid. Users do not need to log in again immediately.

## Comparison with Other Password Endpoints

| Endpoint | Purpose | Current Password Required | Authentication Required |
|----------|---------|--------------------------|------------------------|
| `/accounts/set-password` | Set new password | ❌ No | ✅ Yes (JWT) |
| `/accounts/change-password` | Change existing password | ✅ Yes | ✅ Yes (JWT) |
| `/accounts/forget-password` | Request password reset | ❌ No | ❌ No |
| `/accounts/reset-password` | Reset password with token | ❌ No | ❌ No (uses reset token) |

## Use Cases

1. **OAuth Users Setting First Password**: Users who registered via Google OAuth can use this endpoint to set a password for traditional login.

2. **Simplified Password Management**: Authenticated users can quickly set a new password without needing to remember their current one.

3. **Administrative Password Changes**: When an admin needs to help a user change their password while the user is authenticated.

4. **Post-Recovery Password Setting**: After verifying identity through other means, users can set a new password.

