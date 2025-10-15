# Google OAuth Implementation Guide

This document explains how to use the Google OAuth authentication system implemented in the Fiko Backend project.

## Overview

The Google OAuth implementation provides secure login and registration functionality using Google accounts. Users can authenticate using either:
1. **ID Token method** - Frontend receives Google ID token and sends it to backend
2. **Authorization Code method** - Backend handles the full OAuth flow

## Setup Requirements

### 1. Google Cloud Console Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable the Google+ API and People API
4. Go to "Credentials" → "Create Credentials" → "OAuth 2.0 Client IDs"
5. Configure OAuth consent screen
6. Add authorized redirect URIs:
   - `http://localhost:3000/auth/google/callback` (development)
   - `https://yourdomain.com/auth/google/callback` (production)

### 2. Environment Variables

Add these environment variables to your `.env` file:

```env
# Google OAuth Configuration
GOOGLE_OAUTH2_CLIENT_ID=your-google-client-id
GOOGLE_OAUTH2_CLIENT_SECRET=your-google-client-secret
GOOGLE_OAUTH2_REDIRECT_URI=http://localhost:3000/auth/google/callback
```

### 3. Install Dependencies

The required Google OAuth dependencies are already added to `requirements/base.txt`:
- `google-auth==2.29.0`
- `google-auth-oauthlib==1.2.0`
- `google-auth-httplib2==0.2.0`

## API Endpoints

### 1. Test Configuration
**GET** `/api/v1/accounts/google/test`

Check if Google OAuth is properly configured.

**Response:**
```json
{
    "configured": true,
    "client_id_configured": true,
    "client_secret_configured": true,
    "redirect_uri": "http://localhost:3000/auth/google/callback"
}
```

### 2. Get Authorization URL
**GET/POST** `/api/v1/accounts/google/auth-url`

Generate Google OAuth authorization URL for frontend redirection.

**Request (POST):**
```json
{
    "state": "optional-csrf-token"
}
```

**Response:**
```json
{
    "auth_url": "https://accounts.google.com/o/oauth2/auth?client_id=...",
    "state": "optional-csrf-token"
}
```

### 3. Login with ID Token
**POST** `/api/v1/accounts/google/login`

Authenticate user using Google ID token (recommended for frontend apps).

**Request:**
```json
{
    "id_token": "google-id-token-here"
}
```

**Response:**
```json
{
    "access_token": "jwt-access-token",
    "refresh_token": "jwt-refresh-token",
    "user": {
        "id": 1,
        "email": "user@gmail.com",
        "username": "user",
        "first_name": "John",
        "last_name": "Doe",
        "google_id": "google-user-id",
        "is_google_user": true,
        "google_avatar_url": "https://...",
        "wizard_complete": false,
        "created_at": "2024-01-01T00:00:00Z"
    },
    "message": "Login successful"
}
```

### 4. Login with Authorization Code
**POST** `/api/v1/accounts/google/callback`

Authenticate user using Google authorization code (for server-side flow).

**Request:**
```json
{
    "code": "authorization-code-from-google",
    "state": "optional-csrf-token"
}
```

**Response:**
```json
{
    "access_token": "jwt-access-token",
    "refresh_token": "jwt-refresh-token",
    "user": {
        // same user object as above
    },
    "google_access_token": "google-access-token",
    "google_refresh_token": "google-refresh-token",
    "message": "Login successful"
}
```

## Frontend Integration Examples

### React.js with Google Identity Services

```javascript
import { GoogleAuth } from '@google-cloud/auth-library';

// 1. Initialize Google Sign-In
useEffect(() => {
    const initializeGoogleSignIn = () => {
        window.google.accounts.id.initialize({
            client_id: 'your-google-client-id',
            callback: handleGoogleResponse
        });
        
        window.google.accounts.id.renderButton(
            document.getElementById('google-signin-button'),
            { theme: 'outline', size: 'large' }
        );
    };
    
    initializeGoogleSignIn();
}, []);

// 2. Handle Google response
const handleGoogleResponse = async (response) => {
    try {
        const result = await fetch('/api/v1/accounts/google/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                id_token: response.credential
            })
        });
        
        const data = await result.json();
        
        if (result.ok) {
            // Store tokens and redirect user
            localStorage.setItem('access_token', data.access_token);
            localStorage.setItem('refresh_token', data.refresh_token);
            localStorage.setItem('user', JSON.stringify(data.user));
            
            // Redirect to dashboard
            window.location.href = '/dashboard';
        } else {
            console.error('Login failed:', data);
        }
    } catch (error) {
        console.error('Error during Google login:', error);
    }
};
```

### Vue.js with Authorization Code Flow

```javascript
// 1. Get authorization URL
const getGoogleAuthUrl = async () => {
    try {
        const response = await fetch('/api/v1/accounts/google/auth-url', {
            method: 'GET',
        });
        const data = await response.json();
        
        // Redirect to Google
        window.location.href = data.auth_url;
    } catch (error) {
        console.error('Error getting auth URL:', error);
    }
};

// 2. Handle callback (in your callback page)
const handleGoogleCallback = async () => {
    const urlParams = new URLSearchParams(window.location.search);
    const code = urlParams.get('code');
    const state = urlParams.get('state');
    
    if (code) {
        try {
            const response = await fetch('/api/v1/accounts/google/callback', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ code, state })
            });
            
            const data = await response.json();
            
            if (response.ok) {
                // Store tokens and redirect
                localStorage.setItem('access_token', data.access_token);
                localStorage.setItem('refresh_token', data.refresh_token);
                localStorage.setItem('user', JSON.stringify(data.user));
                
                // Redirect to dashboard
                this.$router.push('/dashboard');
            }
        } catch (error) {
            console.error('Callback error:', error);
        }
    }
};
```

## Security Features

### 1. Token Validation
- Google ID tokens are verified using Google's public keys
- Issuer and audience validation
- Email verification requirement
- Signature verification

### 2. User Account Security
- Google users have unusable passwords (can't login with password)
- Automatic linking of existing accounts by email
- Secure random username generation
- Avatar URL updates from Google

### 3. JWT Integration
- Standard JWT access/refresh token flow
- HTTP-only cookie support
- Same security as regular login

## User Flow

### New User Registration
1. User clicks "Login with Google"
2. User authenticates with Google
3. Backend receives and verifies Google token
4. New user account created with Google information
5. JWT tokens generated and returned
6. User logged in automatically

### Existing User Login
1. User clicks "Login with Google"
2. User authenticates with Google
3. Backend finds existing user by Google ID or email
4. User information updated from Google (avatar, etc.)
5. JWT tokens generated and returned
6. User logged in

### Account Linking
If a user exists with the same email but no Google ID:
1. The account is automatically linked to Google
2. `google_id` and `is_google_user` fields are updated
3. User can now login with both Google and password

## Error Handling

Common error responses:

```json
// Invalid token
{
    "id_token": ["Invalid Google token"]
}

// Missing configuration
{
    "error": "Google OAuth not configured"
}

// Email not verified
{
    "id_token": ["Email not verified by Google"]
}

// Network error
{
    "error": "Failed to communicate with Google"
}
```

## Testing

### 1. Test Configuration
```bash
curl -X GET http://localhost:8000/api/v1/accounts/google/test
```

### 2. Test with Postman
1. Get ID token from Google OAuth Playground
2. Use the `/google/login` endpoint with the token

### 3. Frontend Testing
Use Google's test accounts or create a test Google account for development.

## Production Deployment

### 1. Update Environment Variables
```env
GOOGLE_OAUTH2_CLIENT_ID=production-client-id
GOOGLE_OAUTH2_CLIENT_SECRET=production-client-secret
GOOGLE_OAUTH2_REDIRECT_URI=https://yourdomain.com/auth/google/callback
```

### 2. Update Google Cloud Console
- Add production domain to authorized origins
- Add production redirect URI
- Verify OAuth consent screen

### 3. Security Settings
- Set `secure=True` for cookies in production
- Use HTTPS for all OAuth redirects
- Implement proper CORS settings

## Troubleshooting

### Common Issues

1. **"Invalid token issuer"**
   - Check that the ID token is from Google
   - Verify client ID configuration

2. **"Email not verified by Google"**
   - User must verify their email with Google first
   - Use a verified Google account for testing

3. **"Configuration not found"**
   - Check environment variables are set
   - Restart server after adding variables

4. **CORS errors**
   - Add frontend domain to `CORS_ALLOWED_ORIGINS`
   - Check redirect URI matches exactly

5. **"User not found" after login**
   - Check database migration was applied
   - Verify User model has Google fields

## Database Schema

The User model includes these Google OAuth fields:

```python
class User(AbstractUser):
    # ... existing fields ...
    
    # Google OAuth fields
    google_id = models.CharField(max_length=250, unique=True, null=True, blank=True)
    is_google_user = models.BooleanField(default=False)
    google_avatar_url = models.URLField(max_length=500, null=True, blank=True)
```

## Migration

Apply the database migration:

```bash
python src/manage.py migrate accounts
```

This adds the Google OAuth fields to existing User table.
