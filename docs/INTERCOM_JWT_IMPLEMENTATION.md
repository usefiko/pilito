# Intercom JWT Implementation Guide

This document provides comprehensive guidance for implementing Intercom JWT authentication in the Fiko backend and frontend integration.

## Overview

Intercom JWT authentication provides secure user authentication for the Intercom Messenger, preventing unauthorized access and ensuring user data integrity. This implementation follows [Intercom's official JWT documentation](https://www.intercom.com/help/en/articles/10589769-authenticating-users-in-the-messenger-with-json-web-tokens-jwts).

## Backend Implementation

### 1. Environment Configuration

Add the following environment variables to your `.env` file:

```bash
# Intercom Configuration
INTERCOM_APP_ID=your_intercom_app_id
INTERCOM_API_SECRET=your_intercom_api_secret
INTERCOM_SESSION_DURATION=604800000  # 7 days in milliseconds (optional)
```

### 2. Available API Endpoints

#### Generate JWT Token
- **Endpoint**: `POST /api/v1/accounts/intercom/jwt`
- **Authentication**: Required (Bearer token)
- **Purpose**: Generate JWT token for Intercom authentication

**Request Body:**
```json
{
    "expiration_minutes": 5,  // Optional: 1-60 minutes (default: 5)
    "custom_attributes": {    // Optional: Additional user data
        "subscription_plan": "pro",
        "last_login": "2024-01-15"
    }
}
```

**Response:**
```json
{
    "intercom_user_jwt": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "expires_at": "2024-01-15T10:05:00Z",
    "user_id": "123",
    "expires_in_seconds": 300
}
```

#### Get Intercom Configuration
- **Endpoint**: `GET /api/v1/accounts/intercom/config`
- **Authentication**: Required (Bearer token)
- **Purpose**: Get Intercom configuration for frontend

**Response:**
```json
{
    "app_id": "your_app_id",
    "api_base": "https://api-iam.intercom.io",
    "session_duration": 604800000
}
```

#### Generate User Hash (Legacy)
- **Endpoint**: `POST /api/v1/accounts/intercom/user-hash`
- **Authentication**: Required (Bearer token)
- **Purpose**: Generate user hash for legacy Identity Verification

**Response:**
```json
{
    "user_hash": "a1b2c3d4e5f6...",
    "user_id": "123"
}
```

#### Validate JWT Token (Debug)
- **Endpoint**: `POST /api/v1/accounts/intercom/validate-jwt`
- **Authentication**: Required (Bearer token)
- **Purpose**: Validate JWT token (for debugging)

**Request Body:**
```json
{
    "jwt_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

**Response:**
```json
{
    "valid": true,
    "payload": {
        "user_id": "123",
        "email": "user@example.com",
        "iat": 1642246800,
        "exp": 1642247100
    },
    "user_id": "123"
}
```

### 3. JWT Payload Structure

The generated JWT includes the following user data:

**Required Fields:**
- `user_id`: User identifier (required by Intercom)
- `email`: User email address
- `iat`: Issued at timestamp
- `exp`: Expiration timestamp

**Optional User Profile Fields:**
- `name`: Full name (first_name + last_name)
- `phone`: Phone number
- `created_at`: User registration timestamp
- `company`: Organization information
- `business_type`: User's business type
- `location`: Address information (country, state, zip_code, address)
- `language`: User's preferred language
- `time_zone`: User's time zone
- `currency`: User's currency preference

**Custom Attributes:**
Any additional attributes passed in the `custom_attributes` parameter.

## Frontend Integration

### 1. Fetch JWT Token

```javascript
// Fetch JWT token from your backend
const fetchIntercomJWT = async () => {
    try {
        const response = await fetch('/api/v1/accounts/intercom/jwt', {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${userAccessToken}`,
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                expiration_minutes: 5,
                custom_attributes: {
                    subscription_plan: 'pro',
                    feature_flags: ['chat_enabled', 'support_priority']
                }
            })
        });
        
        const data = await response.json();
        return data.intercom_user_jwt;
    } catch (error) {
        console.error('Failed to fetch Intercom JWT:', error);
        return null;
    }
};
```

### 2. Get Intercom Configuration

```javascript
// Fetch Intercom configuration
const fetchIntercomConfig = async () => {
    try {
        const response = await fetch('/api/v1/accounts/intercom/config', {
            headers: {
                'Authorization': `Bearer ${userAccessToken}`,
            }
        });
        
        return await response.json();
    } catch (error) {
        console.error('Failed to fetch Intercom config:', error);
        return null;
    }
};
```

### 3. Initialize Intercom Messenger

```javascript
// Initialize Intercom with JWT authentication
const initializeIntercom = async () => {
    const config = await fetchIntercomConfig();
    const jwt = await fetchIntercomJWT();
    
    if (!config || !jwt) {
        console.error('Failed to initialize Intercom');
        return;
    }
    
    window.Intercom('boot', {
        api_base: config.api_base,
        app_id: config.app_id,
        intercom_user_jwt: jwt,
        session_duration: config.session_duration
    });
};

// Call when user logs in
initializeIntercom();
```

### 4. Handle Token Refresh

```javascript
// Refresh JWT token before expiration
const refreshIntercomJWT = async () => {
    const newJWT = await fetchIntercomJWT();
    
    if (newJWT) {
        // Update Intercom with new JWT
        window.Intercom('boot', {
            api_base: config.api_base,
            app_id: config.app_id,
            intercom_user_jwt: newJWT,
            session_duration: config.session_duration
        });
    }
};

// Set up periodic refresh (every 4 minutes for 5-minute tokens)
setInterval(refreshIntercomJWT, 4 * 60 * 1000);
```

### 5. Handle User Logout

```javascript
// Shutdown Intercom when user logs out
const handleUserLogout = () => {
    // Shutdown Intercom to clear session
    window.Intercom('shutdown');
    
    // Perform your app's logout logic
    logout();
};
```

## Security Best Practices

### 1. Token Expiration
- Use short-lived tokens (5 minutes recommended)
- Refresh tokens before expiration
- Never store JWT tokens in localStorage for extended periods

### 2. Environment Variables
- Keep `INTERCOM_API_SECRET` secure and never expose it to frontend
- Use different secrets for different environments
- Rotate secrets regularly

### 3. User Data Protection
- Only include necessary user data in JWT payload
- Mark sensitive attributes as "protected" in Intercom settings
- Validate user permissions before including custom attributes

### 4. Error Handling
- Implement proper error handling for JWT generation failures
- Provide fallback for users when Intercom is unavailable
- Log errors for monitoring and debugging

## Testing

### 1. Test JWT Generation

```bash
# Test JWT generation
curl -X POST http://localhost:8000/api/v1/accounts/intercom/jwt \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"expiration_minutes": 5}'
```

### 2. Test JWT Validation

```bash
# Test JWT validation
curl -X POST http://localhost:8000/api/v1/accounts/intercom/validate-jwt \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"jwt_token": "YOUR_JWT_TOKEN"}'
```

### 3. Test Configuration

```bash
# Test configuration endpoint
curl -X GET http://localhost:8000/api/v1/accounts/intercom/config \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

## Troubleshooting

### Common Issues

1. **"INTERCOM_API_SECRET is not configured"**
   - Ensure the environment variable is set correctly
   - Check that the Django settings are loading the environment variable

2. **"Invalid JWT token"**
   - Verify the secret key matches between backend and Intercom
   - Check token expiration time
   - Ensure the payload includes required fields

3. **"Missing user_id in payload"**
   - The JWT must include `user_id` as a required field
   - Verify user authentication is working correctly

4. **Frontend Integration Issues**
   - Ensure CORS settings allow requests from your frontend domain
   - Check that authentication headers are included in requests
   - Verify the Intercom script is loaded before calling `window.Intercom`

### Debug Mode

To enable detailed logging for debugging:

```python
# In your Django settings
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'accounts.services.intercom': {
            'handlers': ['console'],
            'level': 'DEBUG',
        },
    },
}
```

## Migration from Identity Verification

If you're migrating from Intercom's legacy Identity Verification:

1. Keep both systems running during transition
2. Use the user hash endpoint for legacy compatibility
3. Gradually migrate frontend components to use JWT
4. Remove user hash implementation after complete migration

## Production Deployment

1. Set environment variables in your production environment
2. Ensure HTTPS is used for all API calls
3. Configure proper CORS settings
4. Set up monitoring for JWT generation failures
5. Implement rate limiting for JWT endpoints
6. Use a secure secret management system for API secrets

## Support

For issues related to this implementation:
1. Check the troubleshooting section above
2. Review Intercom's official documentation
3. Check application logs for detailed error messages
4. Verify environment configuration and user authentication
