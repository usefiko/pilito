# Google OAuth Profile Picture Implementation

## Summary

Successfully implemented automatic profile picture download and saving during Google OAuth login/registration process. When a user logs in or registers with Google OAuth, their Google profile picture is now automatically downloaded and saved as their profile picture in the system.

## Changes Made

### 1. Enhanced Google OAuth Serializers (`src/accounts/serializers/google_oauth.py`)

#### Added GoogleProfilePictureService Class
- **Purpose**: Handles downloading and saving Google profile pictures
- **Key Features**:
  - Downloads images from Google avatar URLs
  - Validates image content types (PNG/JPEG)
  - Generates unique filenames with format: `user_img/google_{user_id}_{random_hash}.{ext}`
  - Handles errors gracefully (network issues, invalid content types, etc.)
  - Respects existing custom profile pictures (won't override unless it's a Google avatar)
  - Proper logging for debugging

#### Key Methods:
```python
@staticmethod
def download_and_save_profile_picture(user, google_avatar_url):
    """
    Download Google profile picture and save it as user's profile picture
    
    Args:
        user: User instance
        google_avatar_url: URL of the Google profile picture
        
    Returns:
        bool: True if successfully downloaded and saved, False otherwise
    """
```

### 2. Updated User Creation Flow

#### GoogleOAuthLoginSerializer._create_google_user()
- Added call to download and save profile picture after user creation
- Ensures new Google users get their profile picture immediately

#### GoogleOAuthCodeSerializer._create_google_user()  
- Added call to download and save profile picture after user creation
- Consistent behavior for both OAuth flows (ID token and authorization code)

### 3. Updated User Information Update Flow

#### Both Serializers._update_user_info()
- Added profile picture update when Google avatar URL changes
- Ensures existing users get updated profile pictures if they change their Google avatar

## Implementation Logic

### Profile Picture Download Process:
1. **Validation**: Check if Google avatar URL exists
2. **Existing Picture Check**: Skip if user already has a custom (non-Google) profile picture
3. **Download**: Make HTTP request to Google avatar URL with 10-second timeout
4. **Content Validation**: Verify response contains valid image data (PNG/JPEG)
5. **File Generation**: Create unique filename with user ID and random hash
6. **Save**: Save image using Django's ContentFile and ImageField
7. **Database Update**: Save user record with new profile picture
8. **Error Handling**: Log errors but don't fail the OAuth process

### Security Considerations:
- **Timeout Protection**: 10-second timeout prevents hanging requests
- **Content Type Validation**: Only accepts image/* content types
- **File Name Safety**: Uses UUID for unique, safe filenames
- **Error Isolation**: Profile picture download failures don't break OAuth login
- **Existing Picture Respect**: Won't override user's custom profile pictures

### When Profile Pictures Are Downloaded:
1. **New User Registration**: When a new user registers via Google OAuth
2. **Avatar URL Changes**: When an existing user's Google avatar URL changes
3. **Account Linking**: When an existing email account is linked to Google OAuth

### When Profile Pictures Are NOT Downloaded:
1. **Empty/None URLs**: If Google doesn't provide an avatar URL
2. **Custom Pictures**: If user already has a non-default, non-Google profile picture
3. **Network Errors**: If download fails (graceful fallback)
4. **Invalid Content**: If the URL doesn't return valid image data

## File Structure

```
src/accounts/serializers/google_oauth.py
├── GoogleProfilePictureService (new)
│   └── download_and_save_profile_picture()
├── GoogleOAuthLoginSerializer (enhanced)
│   ├── _create_google_user() - added profile picture download
│   └── _update_user_info() - added profile picture update
└── GoogleOAuthCodeSerializer (enhanced)
    ├── _create_google_user() - added profile picture download
    └── _update_user_info() - added profile picture update
```

## Dependencies Added

```python
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
import requests
import uuid
import os
```

## Error Handling

The implementation includes comprehensive error handling:

- **Network Errors**: Caught and logged, OAuth continues successfully
- **Invalid Content Types**: Detected and rejected
- **File System Errors**: Handled gracefully
- **Missing URLs**: Handled without errors
- **Timeouts**: 10-second timeout prevents hanging

## Logging

Detailed logging is implemented for debugging:

- Info level: Successful downloads, URL validation
- Warning level: Invalid content types
- Error level: Network failures, unexpected errors

## Testing

The implementation has been designed with testability in mind:

- Service is a static method for easy mocking
- Clear return values (True/False) for success/failure
- Separated concerns (download logic vs OAuth logic)
- Mock-friendly design

## Usage Examples

### For New Users:
When a user registers with Google OAuth, their profile picture is automatically downloaded and saved.

### For Existing Users:
If an existing user's Google avatar changes, the next time they log in, their profile picture will be updated.

### Manual Testing:
1. Create a new user via Google OAuth
2. Check that `user.profile_picture` contains a file starting with `user_img/google_`
3. Verify the image file exists in the media storage
4. Update the user's Google avatar and log in again
5. Verify the profile picture is updated

## Benefits

1. **Improved User Experience**: Users get their familiar profile picture immediately
2. **Consistent Branding**: Google users maintain their visual identity
3. **Automatic Updates**: Profile pictures stay current with Google changes
4. **Robust Implementation**: Handles errors gracefully without breaking OAuth
5. **Respects User Choice**: Won't override custom profile pictures

## Integration Points

This enhancement integrates seamlessly with:
- Existing Google OAuth flow
- User model's profile_picture field  
- Media storage system (local or cloud)
- Frontend profile picture display
- Profile management APIs

The implementation maintains backward compatibility and doesn't affect any existing functionality.
