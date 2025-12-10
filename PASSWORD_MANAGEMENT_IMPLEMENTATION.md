# Password Management & pass_correct Field Implementation

## Summary

This document outlines the implementation of automatic `pass_correct` field management across all password-related operations in the Pilito authentication system.

## What is `pass_correct`?

The `pass_correct` field is a boolean field in the User model that indicates whether a user has set a valid password:
- `False` (default): User has not set a password (OTP-only users, Google OAuth users without password)
- `True`: User has a valid password set

## Implementation Details

### 1. User Registration with Password (`/accounts/register`)

**File:** `/src/accounts/serializers/register.py`

When users register with email/username and password:
- Password is hashed and saved
- `pass_correct` is automatically set to `True`
- Applies to both new user creation and re-registration of unconfirmed users

```python
user = User.objects.create_user(
    username=validated_data['username'],
    email=validated_data['email'],
    password=validated_data['password']
)
user.pass_correct = True
user.save()
```

### 2. Password Reset (`/accounts/reset-password`)

**File:** `/src/accounts/api/forget_password.py`

When users reset their password via the forgot password flow:
- New password is set
- `pass_correct` is automatically set to `True`

```python
user = reset_token.user
user.set_password(new_password)
user.pass_correct = True
user.save()
```

### 3. Set Password (`/accounts/set-password`) - NEW

**File:** `/src/accounts/api/set_password.py`

New endpoint for authenticated users to set a password without providing current password:
- Useful for OAuth users who want to add password authentication
- Useful for OTP-only users who want to set a password
- `pass_correct` is automatically set to `True`

```python
user = self.context['request'].user
user.set_password(self.validated_data['new_password'])
user.pass_correct = True
user.save()
```

### 4. Change Password (`/accounts/change-password`)

**File:** `/src/accounts/serializers/user.py`

When users change their existing password:
- Current password is verified
- New password is set
- `pass_correct` is automatically set to `True` (reinforced, should already be True)

```python
user = self.context['request'].user
user.set_password(self.validated_data['new_password'])
user.pass_correct = True
user.save()
```

### 5. OTP Registration (`/accounts/otp/verify`)

**File:** `/src/accounts/serializers/otp.py`

When users register/login via OTP:
- User is created without a password
- `pass_correct` remains `False` (default value)
- Users can later use `/accounts/set-password` to set a password

```python
user, created = User.objects.get_or_create(
    phone_number=phone_number,
    defaults={
        'username': phone_number.replace('+', ''),
        'email': f"{phone_number.replace('+', '')}@temp.pilito.com",
        # pass_correct defaults to False
    }
)
```

### 6. Google OAuth Registration

**File:** `/src/accounts/serializers/google_oauth.py`

When users register via Google OAuth:
- User is created with unusable password
- `pass_correct` remains `False` (default value)
- Users can later use `/accounts/set-password` to add password authentication

```python
user = User.objects.create(
    email=user_data['email'],
    username=username,
    # ... other fields ...
)
user.set_unusable_password()  # No password set
user.save()
# pass_correct remains False
```

## User Flow Examples

### Example 1: Google OAuth User Adding Password

1. User registers via Google OAuth → `pass_correct = False`
2. User is authenticated via Google
3. User wants to add password for traditional login
4. User calls `/accounts/set-password` with new password
5. System sets password and updates `pass_correct = True`
6. User can now login with email/password OR Google OAuth

### Example 2: OTP User Adding Password

1. User registers via OTP → `pass_correct = False`
2. User is authenticated via OTP
3. User wants to add password for traditional login
4. User calls `/accounts/set-password` with new password
5. System sets password and updates `pass_correct = True`
6. User can now login with email/password OR OTP

### Example 3: Traditional Registration

1. User registers with email/username/password
2. System sets password and updates `pass_correct = True`
3. User can login with email/password immediately

### Example 4: Password Reset

1. User forgets password
2. User requests password reset via `/accounts/forget-password`
3. User receives reset link via email
4. User sets new password via `/accounts/reset-password`
5. System updates `pass_correct = True`
6. User can login with new password

## API Endpoints Summary

| Endpoint | Sets Password? | Updates pass_correct? | Auth Required? |
|----------|---------------|----------------------|----------------|
| `/accounts/register` | ✅ Yes | ✅ Yes → True | ❌ No |
| `/accounts/reset-password` | ✅ Yes | ✅ Yes → True | ❌ No (uses token) |
| `/accounts/set-password` | ✅ Yes | ✅ Yes → True | ✅ Yes (JWT) |
| `/accounts/change-password` | ✅ Yes | ✅ Yes → True | ✅ Yes (JWT) |
| `/accounts/otp/verify` | ❌ No | ❌ Remains False | ❌ No |
| `/accounts/google/login` | ❌ No | ❌ Remains False | ❌ No |

## Database Schema

```python
class User(AbstractUser):
    # ... other fields ...
    
    pass_correct = models.BooleanField(
        default=False,
        verbose_name="Password Set",
        help_text="Whether the user has set a valid password (False for OTP-only registrations)"
    )
```

## Benefits

1. **Clear User State**: Easy to determine if a user has a password or uses only OAuth/OTP
2. **Flexible Authentication**: Users can have multiple authentication methods
3. **Better UX**: OAuth/OTP users can add password authentication when needed
4. **Admin Visibility**: Admins can see which users have passwords vs. OAuth-only
5. **Security**: Prevents confusion about authentication methods

## Frontend Integration

Frontend can check the `pass_correct` field to:
- Show "Set Password" option for OAuth/OTP users
- Show "Change Password" option for users with passwords
- Display appropriate authentication options on login screen

## Testing Scenarios

1. ✅ Register with password → `pass_correct = True`
2. ✅ Register with OTP → `pass_correct = False`
3. ✅ Register with Google OAuth → `pass_correct = False`
4. ✅ OTP user sets password → `pass_correct = True`
5. ✅ OAuth user sets password → `pass_correct = True`
6. ✅ User resets password → `pass_correct = True`
7. ✅ User changes password → `pass_correct = True`

## Files Modified

1. `/src/accounts/api/set_password.py` - New file
2. `/src/accounts/serializers/user.py` - Updated ChangePasswordSerializer & SetPasswordSerializer
3. `/src/accounts/serializers/register.py` - Updated RegisterSerializer
4. `/src/accounts/api/forget_password.py` - Updated ResetPasswordAPIView
5. `/src/accounts/serializers/__init__.py` - Added SetPasswordSerializer export
6. `/src/accounts/api/__init__.py` - Added SetPasswordAPIView export
7. `/src/accounts/urls.py` - Added set-password endpoint

## Backward Compatibility

Existing users:
- Users with passwords should have `pass_correct = True` (may need a one-time migration)
- OAuth-only users will have `pass_correct = False` (correct default)
- OTP-only users will have `pass_correct = False` (correct default)

## Future Enhancements

1. Add migration to set `pass_correct = True` for existing users with usable passwords
2. Add admin action to bulk update `pass_correct` field
3. Add API endpoint to check user's authentication methods
4. Add analytics on authentication method usage

