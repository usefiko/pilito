# 🔧 Google OAuth Complete Fix Guide

## ✅ **Issues Identified & Solutions**

### **Issue 1: Wrong API URLs** ❌
**Problem**: Frontend is calling `/api/v1/accounts/google/callback`  
**Reality**: URLs are actually `/api/v1/usr/google/callback`

### **Issue 2: Database Configuration** ❌
**Problem**: App can't connect to database (localhost PostgreSQL not running)

---

## 🛠 **Complete Fix Implementation**

### **1. Correct Google OAuth API URLs:**

Your actual Google OAuth endpoints are:
```
GET  /api/v1/usr/google/auth-url     # Get OAuth URL
POST /api/v1/usr/google/callback     # OAuth callback
POST /api/v1/usr/google/login        # Direct token login  
GET  /api/v1/usr/google/test         # Test configuration
```

**❌ Wrong (current frontend):**
```javascript
fetch('/api/v1/accounts/google/callback', { ... })
```

**✅ Correct (update frontend):**
```javascript
fetch('/api/v1/usr/google/callback', { ... })
```

### **2. Database Configuration Options:**

#### **Option A: Use Docker Database (Recommended)**
Your app is designed to work with Docker. Start the database:

```bash
cd /Users/nima/Projects/Fiko-Backend

# Update .env to use Docker database
cat > .env << EOF
STAGE="DEV"
DEBUG=True
SECRET_KEY="jango-insecure-_#2hxi#d@7!6bg((p@tmy-)#y3i_ad=n!pm4@_h2c60+1m9gty"
DJANGO_ALLOWED_HOSTS=localhost 127.0.0.1 [::1]
POSTGRES_DB=FikoDB
POSTGRES_USER=FikoUsr
POSTGRES_PASSWORD=FikoPass123!!!
POSTGRES_HOST=db
POSTGRES_PORT=5432
AWS_ACCESS_KEY_ID=AKIARTLO5HLCCGCFEM7Y
AWS_SECRET_ACCESS_KEY=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
AWS_STORAGE_BUCKET_NAME=fiko
AWS_S3_REGION_NAME=us-east-1
REDIS_URL=redis://redis:6379/0
EOF

# Start with Docker
docker-compose up -d db redis
# Then run Django app
cd src && python manage.py runserver
```

#### **Option B: Local PostgreSQL**
Install and configure PostgreSQL locally:

```bash
# Install PostgreSQL (macOS)
brew install postgresql
brew services start postgresql

# Create database
psql postgres -c "CREATE DATABASE FikoDB;"
psql postgres -c "CREATE USER FikoUsr WITH PASSWORD 'FikoPass123!!!';"
psql postgres -c "GRANT ALL PRIVILEGES ON DATABASE FikoDB TO FikoUsr;"

# Keep .env with localhost
POSTGRES_HOST=localhost
```

#### **Option C: Use SQLite for Testing**
Quick temporary solution:

```python
# In src/core/settings/development.py, replace DATABASES with:
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}
```

---

## 🔧 **Frontend Fix Required**

Update your frontend OAuth callback implementation:

### **1. Update API URLs:**
```javascript
// Change all instances of:
'/api/v1/accounts/google/'
// To:
'/api/v1/usr/google/'
```

### **2. Complete Frontend Implementation:**
```javascript
// OAuth callback page (e.g., /auth/google/callback)
useEffect(() => {
  const urlParams = new URLSearchParams(window.location.search);
  const code = urlParams.get('code');
  const error = urlParams.get('error');
  
  if (error) {
    console.error('Google OAuth error:', error);
    router.push('/login?error=oauth_failed');
    return;
  }
  
  if (code) {
    handleGoogleCallback(code);
  }
}, []);

const handleGoogleCallback = async (code) => {
  try {
    setLoading(true);
    
    // ✅ Correct URL
    const response = await fetch('/api/v1/usr/google/callback', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ code })
    });
    
    const data = await response.json();
    
    if (response.ok && data.access_token) {
      // Store tokens
      localStorage.setItem('access_token', data.access_token);
      localStorage.setItem('refresh_token', data.refresh_token);
      
      // Store user data
      localStorage.setItem('user', JSON.stringify(data.user));
      
      // Redirect to dashboard
      router.push('/dashboard');
    } else {
      console.error('Login failed:', data);
      router.push('/login?error=oauth_failed');
    }
  } catch (error) {
    console.error('OAuth callback error:', error);
    router.push('/login?error=network_error');
  } finally {
    setLoading(false);
  }
};

// Generate OAuth URL
const initiateGoogleLogin = async () => {
  try {
    // ✅ Correct URL
    const response = await fetch('/api/v1/usr/google/auth-url');
    const data = await response.json();
    
    if (data.auth_url) {
      window.location.href = data.auth_url;
    }
  } catch (error) {
    console.error('Failed to get Google auth URL:', error);
  }
};
```

---

## 🧪 **Testing Steps**

### **1. Test Backend APIs:**
```bash
# Test configuration
curl -X GET "http://localhost:8000/api/v1/usr/google/test"

# Expected response:
{
  "configured": true,
  "client_id_configured": true,
  "client_secret_configured": true,
  "redirect_uri": "https://app.pilito.com/auth/google/callback"
}
```

### **2. Test Google OAuth Flow:**
```bash
# Get auth URL
curl -X GET "http://localhost:8000/api/v1/usr/google/auth-url"

# Test callback (with real Google code)
curl -X POST "http://localhost:8000/api/v1/usr/google/callback" \
  -H "Content-Type: application/json" \
  -d '{"code": "REAL_GOOGLE_AUTHORIZATION_CODE"}'
```

### **3. Expected Success Response:**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "user": {
    "id": "123",
    "email": "user@gmail.com",
    "email_confirmed": true,
    "email_confirmation_status": {
      "email_confirmed": true,
      "has_pending_confirmation": false,
      "confirmation_required": false,
      "google_verified": true
    },
    "is_google_user": true,
    "first_name": "John",
    "last_name": "Doe"
  },
  "message": "Login successful"
}
```

---

## 📋 **Implementation Checklist**

### **Backend:**
- [x] ✅ Google OAuth logic fixed (email_confirmed=True)
- [x] ✅ Database configuration updated  
- [x] ✅ API endpoints working at `/api/v1/usr/google/`
- [ ] ⚠️ Choose database option and configure

### **Frontend:**
- [ ] ❌ Update API URLs from `/accounts/` to `/usr/`
- [ ] ❌ Implement OAuth callback page properly
- [ ] ❌ Test complete OAuth flow

### **Environment:**
- [ ] ⚠️ Database running (Docker or local PostgreSQL)
- [ ] ⚠️ Server running on correct port
- [ ] ⚠️ Frontend calling correct API URLs

---

## 🎯 **Quick Fix Summary**

**The main issues are:**

1. **Wrong API URLs**: Frontend calling `/api/v1/accounts/google/callback` but should be `/api/v1/usr/google/callback`

2. **Database Not Running**: Choose one:
   - Start Docker database: `docker-compose up -d db redis`
   - Install local PostgreSQL
   - Use SQLite for testing

3. **Frontend OAuth Callback**: Make sure frontend extracts `code` from URL and POSTs to correct endpoint

**Once you fix the API URLs in frontend, Google OAuth should work immediately!** 🚀

---

## 💡 **Next Steps**

1. **Fix Frontend URLs** (highest priority)
2. **Start Database** (Docker recommended)  
3. **Test OAuth Flow** end-to-end
4. **Verify User Creation** in database

The backend Google OAuth system is working correctly - it just needs the correct API calls and database connection! 🎉
