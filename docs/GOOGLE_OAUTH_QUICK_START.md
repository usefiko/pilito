# Google OAuth Quick Start Guide

## Setup (5 minutes)

### 1. Google Cloud Console
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create OAuth 2.0 credentials
3. Add redirect URI: `http://localhost:3000/auth/google/callback`

### 2. Environment Variables
Add to your `.env` file:
```env
GOOGLE_OAUTH2_CLIENT_ID=your-client-id-here
GOOGLE_OAUTH2_CLIENT_SECRET=your-client-secret-here
```

### 3. Database Migration
```bash
python src/manage.py migrate accounts
```

## API Endpoints

- **GET** `/api/v1/accounts/google/test` - Check configuration
- **GET** `/api/v1/accounts/google/auth-url` - Get authorization URL  
- **POST** `/api/v1/accounts/google/login` - Login with ID token
- **POST** `/api/v1/accounts/google/callback` - Login with auth code

## Frontend Integration

```javascript
// Simple Google Sign-In
window.google.accounts.id.initialize({
    client_id: 'your-client-id',
    callback: async (response) => {
        const result = await fetch('/api/v1/accounts/google/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ id_token: response.credential })
        });
        const data = await result.json();
        // Handle login response
    }
});
```

📖 **Full Documentation**: [GOOGLE_OAUTH_IMPLEMENTATION.md](./GOOGLE_OAUTH_IMPLEMENTATION.md)
