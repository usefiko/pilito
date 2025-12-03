# Google OAuth Flow - Visual Guide

## 📊 The Complete Flow (What Should Happen)

```
┌─────────────┐
│   User      │
│   Clicks    │  1. User clicks "Login with Google" button
│   Login     │
└──────┬──────┘
       │
       │ 2. Frontend makes API call
       ▼
┌─────────────────────────────────────────┐
│ GET /api/v1/usr/google/auth-url         │
│ Response: { auth_url: "https://..." }  │
└──────┬──────────────────────────────────┘
       │
       │ 3. Frontend redirects to auth_url
       ▼
┌─────────────────────────────────────────┐
│  Google OAuth Page                      │
│  (accounts.google.com)                  │
│  User selects account & approves        │
└──────┬──────────────────────────────────┘
       │
       │ 4. Google redirects back with code
       ▼
┌─────────────────────────────────────────────────────────┐
│ GET /api/v1/usr/google/callback?code=XXXXX              │
│ Backend:                                                 │
│   - Exchanges code for tokens with Google               │
│   - Creates/logs in user                                │
│   - Sets cookies (HTTP_ACCESS, HTTP_REFRESH)           │
│   - Redirects to frontend                               │
└──────┬──────────────────────────────────────────────────┘
       │
       │ 5. Backend redirects to frontend
       ▼
┌─────────────────────────────────────────────────────────┐
│ https://app.pilito.com/auth/success                     │
│   ?success=true&data=BASE64_ENCODED_USER_DATA          │
└──────┬──────────────────────────────────────────────────┘
       │
       │ 6. Frontend callback page processes
       ▼
┌─────────────────────────────────────────┐
│ Frontend JavaScript:                     │
│   - Extracts URL parameters             │
│   - Decodes user data                   │
│   - Stores tokens in localStorage       │
│   - Redirects to dashboard              │
└──────┬──────────────────────────────────┘
       │
       │ 7. User is logged in!
       ▼
┌─────────────┐
│  Dashboard  │
│  (Logged In)│
└─────────────┘
```

## 🔍 Where Issues Usually Happen

### ❌ Issue at Step 2: Frontend doesn't call backend
```
User clicks button → Nothing happens
```
**Fix:** Frontend needs to fetch the auth URL from backend

### ❌ Issue at Step 4: Redirect URI mismatch
```
User approves on Google → Error: redirect_uri_mismatch
```
**Fix:** Update Google Console to match exact URI

### ❌ Issue at Step 6: No callback handler
```
User redirected to /auth/success → Blank page or 404
```
**Fix:** Create frontend page to handle the callback

## 🎯 Current State Analysis

Your backend handles Steps 2, 4, and 5 perfectly ✅

The issue is likely in:
- **Step 2**: Frontend not making the API call
- **Step 6**: Frontend not handling the callback
- **Step 4**: Google Console configuration

## 🛠 Where to Look in Your Code

### Frontend Files to Check:

1. **Login Button Component**
   ```
   src/components/LoginButton.jsx (or similar)
   app/login/page.tsx
   components/auth/GoogleLogin.tsx
   ```
   Should contain:
   ```javascript
   fetch('/api/v1/usr/google/auth-url')
   ```

2. **Callback Page**
   ```
   pages/auth/success.jsx
   app/auth/success/page.tsx
   src/pages/AuthSuccess.jsx
   ```
   Should exist and handle URL parameters

3. **Google Console**
   ```
   https://console.cloud.google.com
   → APIs & Services
   → Credentials
   → OAuth 2.0 Client IDs
   ```
   Check redirect URIs

## 💡 Quick Debug Commands

```bash
# Test if backend is working (spoiler: it is ✅)
curl https://api.pilito.com/api/v1/usr/google/test
curl https://api.pilito.com/api/v1/usr/google/auth-url

# Check what your frontend sends (open browser console)
# 1. Click login button
# 2. Check Network tab
# 3. Look for requests to /google/auth-url
```

## 📱 What the User Sees (Current vs Expected)

### Current (Broken):
```
1. User clicks "Login with Google"
2. ??? (Something doesn't happen here)
3. User is not logged in
```

### Expected (Working):
```
1. User clicks "Login with Google"
2. → Redirects to Google sign-in
3. → User selects account
4. → Redirects back to app
5. → Shows "Logging you in..."
6. → Lands on dashboard (logged in!)
```

## 🎬 Action Items

1. **Find your frontend login component**
2. **Check if it calls the backend API**
3. **Check if you have a callback page**
4. **Use the test page** (`google_oauth_test.html`) to verify each step

The backend is ready and waiting. Just need the frontend to use it! 🚀

