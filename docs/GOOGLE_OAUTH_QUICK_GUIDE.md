# Google OAuth Frontend Quick Guide

## 🚀 TL;DR - What Frontend Needs to Do

After Google OAuth, users are redirected to:
```
https://app.fiko.net/auth/success?success=true&data=<base64_data>
```

**You need to create this route and handle the callback!**

## ⚡ Quick Implementation

### 1. Create `/auth/success` Page

```jsx
import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

function AuthSuccess() {
    const navigate = useNavigate();

    useEffect(() => {
        const urlParams = new URLSearchParams(window.location.search);
        
        if (urlParams.get('success') === 'true') {
            // Decode OAuth data
            const data = JSON.parse(atob(urlParams.get('data')));
            
            // Store tokens
            localStorage.setItem('access_token', data.access_token);
            localStorage.setItem('refresh_token', data.refresh_token);
            localStorage.setItem('user', JSON.stringify({
                user_id: data.user_id,
                email: data.email,
                first_name: data.first_name,
                last_name: data.last_name,
                wizard_complete: data.wizard_complete
            }));
            
            // Redirect to dashboard
            navigate('/dashboard');
        } else {
            navigate('/login?error=oauth_failed');
        }
    }, []);

    return <div>Processing login...</div>;
}
```

### 2. Update API Requests

```javascript
// Include token in API calls
const token = localStorage.getItem('access_token');

fetch('/api/endpoint', {
    headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
    },
    credentials: 'include' // Important for cookies
});
```

### 3. Google Login Button

```jsx
const handleGoogleLogin = async () => {
    const response = await fetch('https://api.fiko.net/api/v1/usr/google/auth-url');
    const { auth_url } = await response.json();
    window.location.href = auth_url;
};
```

## 🔍 Test in Browser Console

When redirected to `/auth/success`, run this in console:

```javascript
// Check the OAuth data
const urlParams = new URLSearchParams(window.location.search);
const data = JSON.parse(atob(urlParams.get('data')));
console.log('OAuth Data:', data);

// Store tokens manually
localStorage.setItem('access_token', data.access_token);
localStorage.setItem('user', JSON.stringify(data));

// Then go to dashboard
window.location.href = '/dashboard';
```

## 📊 OAuth Data Structure

```javascript
{
    "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...", 
    "user_id": 123,
    "email": "user@example.com",
    "first_name": "John",
    "last_name": "Doe", 
    "wizard_complete": false,
    "success": true
}
```

## ✅ That's It!

The backend handles everything. Frontend just needs to:
1. Handle `/auth/success` route
2. Extract and store tokens from URL
3. Include tokens in API requests

**Backend is working perfectly - this is purely a frontend routing issue!** 🎉
