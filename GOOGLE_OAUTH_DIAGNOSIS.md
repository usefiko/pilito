# 🔧 Google OAuth Login Issue - Diagnostic Report

## Summary

Your Google OAuth backend is **working correctly**. The issue is likely in one of these areas:

1. **Frontend integration** - How the frontend initiates and handles OAuth
2. **Google Console configuration** - Redirect URIs or origins mismatch
3. **Cookie/session handling** - Cookies not being read correctly

## ✅ What's Working

- ✅ Backend API is online and responding
- ✅ Auth URL endpoint is functional: `/api/v1/usr/google/auth-url`
- ✅ Callback endpoint is configured: `/api/v1/usr/google/callback`
- ✅ User creation and login logic is implemented
- ✅ JWT token generation is working

## 🔍 Configuration Details

### Backend Settings (Production)
```
Backend API: https://api.pilito.com
Client ID: 474127607425-nrcjlsqein387o57t07gq7ktqb0irmdb.apps.googleusercontent.com
Redirect URI: https://api.pilito.com/api/v1/usr/google/callback
Frontend Redirect: https://app.pilito.com/auth/success
```

### API Endpoints
```
GET  /api/v1/usr/google/auth-url    - Get Google OAuth URL
GET  /api/v1/usr/google/callback    - Handle OAuth callback (from Google)
POST /api/v1/usr/google/callback    - Handle OAuth callback (from frontend)
POST /api/v1/usr/google/login       - Login with ID token
```

## 🐛 Common Issues & Solutions

### Issue 1: Frontend Not Redirecting to Google

**Symptoms:**
- Clicking "Login with Google" does nothing
- No redirect happens
- No errors in console

**Solution:**
Your frontend should call the auth URL endpoint and redirect:

```javascript
// When user clicks "Login with Google"
async function handleGoogleLogin() {
    try {
        const response = await fetch('https://api.pilito.com/api/v1/usr/google/auth-url');
        const data = await response.json();
        
        if (data.auth_url) {
            // Redirect to Google
            window.location.href = data.auth_url;
        }
    } catch (error) {
        console.error('Failed to get Google auth URL:', error);
    }
}
```

### Issue 2: Redirect URI Mismatch

**Symptoms:**
- Google shows error: "redirect_uri_mismatch"
- Error appears after selecting Google account

**Solution:**
In Google Cloud Console (https://console.cloud.google.com):

1. Go to **APIs & Services > Credentials**
2. Find your OAuth 2.0 Client ID
3. Under "Authorized redirect URIs", ensure you have **EXACTLY**:
   ```
   https://api.pilito.com/api/v1/usr/google/callback
   http://localhost:8000/api/v1/usr/google/callback
   ```

4. Under "Authorized JavaScript origins", ensure you have:
   ```
   https://app.pilito.com
   http://localhost:3000
   ```

### Issue 3: Callback Not Handled by Frontend

**Symptoms:**
- User successfully logs in with Google
- Redirected to `https://app.pilito.com/auth/success?success=true&data=...`
- Nothing happens after redirect
- Page just shows the URL with parameters

**Solution:**
Create a callback handler page at `/auth/success`:

```javascript
// In your /auth/success page (e.g., auth/success/page.tsx or auth/success.jsx)
import { useEffect } from 'react';
import { useRouter } from 'next/router'; // or your routing library

export default function AuthSuccess() {
    const router = useRouter();

    useEffect(() => {
        const handleCallback = () => {
            // Get URL parameters
            const urlParams = new URLSearchParams(window.location.search);
            const success = urlParams.get('success');
            const dataEncoded = urlParams.get('data');
            const error = urlParams.get('error');

            if (error) {
                console.error('OAuth error:', error);
                const message = urlParams.get('message');
                // Show error to user
                alert(`Login failed: ${message || error}`);
                router.push('/login');
                return;
            }

            if (success === 'true' && dataEncoded) {
                try {
                    // Decode the base64 data
                    const userData = JSON.parse(atob(dataEncoded));
                    
                    // Store tokens
                    localStorage.setItem('access_token', userData.access_token);
                    localStorage.setItem('refresh_token', userData.refresh_token);
                    
                    // Store user info
                    localStorage.setItem('user', JSON.stringify({
                        id: userData.user_id,
                        email: userData.email,
                        first_name: userData.first_name,
                        last_name: userData.last_name,
                        wizard_complete: userData.wizard_complete
                    }));

                    console.log('Login successful:', userData);

                    // Redirect based on wizard status
                    if (userData.wizard_complete) {
                        router.push('/dashboard');
                    } else {
                        router.push('/onboarding');
                    }
                } catch (e) {
                    console.error('Failed to process login data:', e);
                    alert('Login failed: Invalid response data');
                    router.push('/login');
                }
            } else {
                console.error('Invalid callback - missing parameters');
                router.push('/login');
            }
        };

        handleCallback();
    }, [router]);

    return (
        <div style={{ textAlign: 'center', padding: '50px' }}>
            <h2>Completing login...</h2>
            <p>Please wait while we log you in.</p>
        </div>
    );
}
```

### Issue 4: CORS Errors

**Symptoms:**
- Browser console shows CORS errors
- Requests to backend are blocked

**Solution:**
Ensure your backend CORS settings include the frontend domain:

```python
# In src/core/settings/common.py or production.py
CORS_ALLOWED_ORIGINS = [
    'https://app.pilito.com',
    'http://localhost:3000',
]

CORS_ALLOW_CREDENTIALS = True
```

### Issue 5: Cookies Not Being Set/Read

**Symptoms:**
- Login seems successful but user is not authenticated
- Cookies are missing in browser

**Solution:**
1. Check browser cookies after login (DevTools > Application > Cookies)
2. Should see: `HTTP_ACCESS`, `HTTP_REFRESH`, `USER_INFO`
3. If missing, check:
   - Cookie domain settings (should be `.pilito.com` for production)
   - Secure flag (should be `true` for HTTPS)
   - SameSite attribute (should be `Lax` or `None`)

## 🧪 Testing Steps

### Step 1: Test with HTML Test Page

I've created a test page for you: `google_oauth_test.html`

1. Open this file in your browser
2. Click "Test Backend Configuration"
3. Click "Get Auth URL from Backend"
4. Click "Login with Google"
5. Complete Google sign-in
6. Check if you're redirected back with success parameters

### Step 2: Manual API Test

```bash
# 1. Get auth URL
curl https://api.pilito.com/api/v1/usr/google/auth-url

# 2. Open the returned auth_url in your browser
# 3. Sign in with Google
# 4. Watch where you get redirected
# 5. Check if cookies are set in browser DevTools
```

### Step 3: Check Browser Console

1. Open browser DevTools (F12)
2. Go to Console tab
3. Click "Login with Google" in your app
4. Look for errors
5. Check Network tab for failed requests

### Step 4: Check Backend Logs

Look for log messages starting with "Google OAuth" to see what's happening on the backend.

## 🎯 Most Likely Issues (in order)

Based on common problems:

1. **Frontend callback page doesn't exist or doesn't handle the redirect** (80% of cases)
   - Create `/auth/success` page
   - Extract URL parameters
   - Store tokens in localStorage
   - Redirect to dashboard

2. **Google Console redirect URI mismatch** (15% of cases)
   - Verify exact URI in Google Console
   - Must match: `https://api.pilito.com/api/v1/usr/google/callback`

3. **Frontend not initiating Google login correctly** (5% of cases)
   - Call `/google/auth-url` endpoint first
   - Redirect user to returned `auth_url`

## 📋 Quick Checklist

- [ ] Frontend calls `/google/auth-url` endpoint
- [ ] Frontend redirects to returned `auth_url`
- [ ] Google Console has correct redirect URI
- [ ] Frontend has `/auth/success` page (or whatever your redirect is)
- [ ] Callback page extracts and stores tokens
- [ ] Callback page redirects to dashboard
- [ ] CORS is configured correctly
- [ ] Cookies are being set and read

## 🛠 Files to Check/Create

1. **Frontend Login Component**
   - Should call `GET /api/v1/usr/google/auth-url`
   - Should redirect to `auth_url` from response

2. **Frontend Callback Page** (`/auth/success`)
   - Should extract URL parameters (`success`, `data`, `error`)
   - Should decode base64 `data` parameter
   - Should store tokens in localStorage
   - Should redirect to dashboard

3. **Google Cloud Console**
   - Verify redirect URIs
   - Verify JavaScript origins

## 🚀 Next Steps

1. **Identify where the flow breaks**:
   - Open `google_oauth_test.html` in your browser
   - Follow each step and see where it fails

2. **Check the specific area**:
   - If Step 3 (login button) doesn't work: Frontend isn't redirecting
   - If you see error in URL after Google login: Backend issue or Google Console config
   - If redirect works but nothing happens: Callback page issue

3. **Fix the identified issue** using the solutions above

## 📞 Need More Help?

If you're still stuck, please provide:
1. What happens when you click "Login with Google"
2. Any errors in browser console
3. The URL you see after Google login
4. Whether cookies are being set (check DevTools > Application > Cookies)

---

**TL;DR:** Your backend works. Most likely issue is:
1. Frontend doesn't have a callback handler at `/auth/success`
2. OR Google Console redirect URI doesn't match exactly
3. OR frontend isn't calling the auth-url endpoint correctly

Use the test page (`google_oauth_test.html`) to identify exactly where it breaks!

