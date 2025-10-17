# Development Testing Guide: Google OAuth Profile Picture

## Current Status ✅
- Docker containers are running successfully
- Django app is accessible at http://localhost:8000
- Google OAuth is properly configured
- Profile picture download functionality is implemented

## Testing the Google OAuth Profile Picture Feature

### 1. Prerequisites
Make sure Docker containers are running:
```bash
docker compose up -d
docker compose ps  # Verify all containers are up
```

### 2. Available Endpoints

#### Google OAuth Test Endpoint
```bash
curl http://localhost:8000/api/v1/usr/google/test
```
**Expected Response:**
```json
{
    "configured": true,
    "client_id_configured": true,
    "client_secret_configured": true,
    "redirect_uri": "https://api.pilito.com/api/v1/usr/google/callback"
}
```

#### Google OAuth Authorization URL
```bash
curl -X POST http://localhost:8000/api/v1/usr/google/auth-url \
  -H "Content-Type: application/json" \
  -d '{}'
```

### 3. Testing Profile Picture Download

#### Method 1: Frontend Integration Test
1. **Get Authorization URL:**
   ```bash
   curl -X GET http://localhost:8000/api/v1/usr/google/auth-url
   ```

2. **Copy the `auth_url` from response and open it in browser**

3. **Complete Google OAuth flow** - this will redirect to the callback endpoint

4. **Check logs for profile picture download:**
   ```bash
   docker compose logs web --tail=20 | grep -i "profile\|avatar\|google"
   ```

#### Method 2: Direct API Testing with ID Token
If you have a Google ID token, you can test directly:
```bash
curl -X POST http://localhost:8000/api/v1/usr/google/login \
  -H "Content-Type: application/json" \
  -d '{
    "id_token": "YOUR_GOOGLE_ID_TOKEN_HERE"
  }'
```

### 4. Monitoring Profile Picture Downloads

#### Check Application Logs
```bash
# Real-time logs
docker compose logs -f web

# Filter for profile picture related logs
docker compose logs web | grep -i "profile\|avatar\|google"
```

#### Expected Log Messages
When profile picture download works correctly, you should see:
```
INFO Downloading Google profile picture for user user@example.com from https://lh3.googleusercontent.com/...
INFO Successfully saved Google profile picture for user user@example.com as user_img/google_123_abc12345.jpg
```

### 5. Database Verification

#### Access Django Shell in Container
```bash
docker compose exec web python manage.py shell
```

#### Check User Profile Pictures
```python
from django.contrib.auth import get_user_model
User = get_user_model()

# List all Google users with profile pictures
google_users = User.objects.filter(is_google_user=True)
for user in google_users:
    print(f"User: {user.email}")
    print(f"Google Avatar URL: {user.google_avatar_url}")
    print(f"Profile Picture: {user.profile_picture.name if user.profile_picture else 'None'}")
    print(f"Profile Picture URL: {user.profile_picture.url if user.profile_picture else 'None'}")
    print("-" * 50)
```

### 6. File System Verification

#### Check Media Files
```bash
# List uploaded profile pictures
docker compose exec web ls -la /app/media/user_img/

# Look for Google-downloaded pictures (they start with 'google_')
docker compose exec web ls -la /app/media/user_img/ | grep google_
```

### 7. Testing Different Scenarios

#### Scenario 1: New User Registration
1. Use a Google account that hasn't been used with the system
2. Complete OAuth flow
3. Verify user gets profile picture automatically

#### Scenario 2: Existing User Login
1. Use a Google account that already exists in the system
2. Complete OAuth flow
3. Verify profile picture is updated if Google avatar changed

#### Scenario 3: User with Custom Profile Picture
1. User that already has a custom (non-Google) profile picture
2. Complete OAuth flow
3. Verify custom picture is preserved (not overwritten)

### 8. Troubleshooting

#### Common Issues and Solutions

**Profile Picture Not Downloading:**
```bash
# Check if user has google_avatar_url
docker compose exec web python manage.py shell
>>> from django.contrib.auth import get_user_model
>>> User = get_user_model()
>>> user = User.objects.get(email='test@example.com')
>>> print(user.google_avatar_url)
```

**Network/Download Issues:**
```bash
# Check if the avatar URL is accessible
curl -I "GOOGLE_AVATAR_URL_HERE"
```

**File Permission Issues:**
```bash
# Check media directory permissions
docker compose exec web ls -la /app/media/user_img/
```

### 9. Development Workflow

#### Making Changes to Profile Picture Logic
1. **Edit the file:**
   ```
   src/accounts/serializers/google_oauth.py
   ```

2. **Restart the web container:**
   ```bash
   docker compose restart web
   ```

3. **Test changes:**
   ```bash
   docker compose logs -f web
   ```

#### Testing with Mock Data
You can create a test script inside the container:
```bash
docker compose exec web python manage.py shell
```

Then run:
```python
from accounts.serializers.google_oauth import GoogleProfilePictureService
from django.contrib.auth import get_user_model

User = get_user_model()
user = User.objects.first()  # Get any user
test_url = "https://lh3.googleusercontent.com/a/default-user=s96-c"

# Test the download function
result = GoogleProfilePictureService.download_and_save_profile_picture(user, test_url)
print(f"Download result: {result}")
```

### 10. Production Considerations

When moving to production, ensure:
- Google OAuth redirect URIs are updated
- Media storage is properly configured (S3, etc.)
- Error monitoring is in place
- Rate limiting is considered for image downloads

### 11. API Documentation

The enhanced Google OAuth endpoints now automatically handle profile pictures:

- `POST /api/v1/usr/google/login` - Login with ID token (downloads profile pic)
- `GET/POST /api/v1/usr/google/callback` - OAuth callback (downloads profile pic)
- `POST /api/v1/usr/google/auth-url` - Get authorization URL

All endpoints will now automatically download and save Google profile pictures for new users and update them for existing users when their Google avatar changes.

## Current Development Environment Status

✅ **All systems running successfully:**
- Django app: http://localhost:8000
- PostgreSQL database: Running
- Redis cache: Running  
- Celery worker: Running
- Celery beat: Running

✅ **Google OAuth Configuration:**
- Client ID: Configured
- Client Secret: Configured
- Redirect URI: https://api.pilito.com/api/v1/usr/google/callback

✅ **Profile Picture Feature:**
- Implementation complete
- Service integrated into OAuth flow
- Error handling implemented
- Logging configured
