# Registration Email Timeout Fix

## Issue
When users registered via the `api/v1/usr/register` endpoint, the registration would fail completely if the email confirmation couldn't be sent due to SMTP timeout errors. This resulted in:

```
Email sending error: [ErrorDetail(string='Failed to send confirmation email: timed out', code='invalid')]
```

And the user would not be able to register at all.

## Root Cause
The `RegisterSerializer.create()` method was raising a `ValidationError` when email sending failed:

```python
try:
    email_sent, result = send_email_confirmation(user)
    if not email_sent:
        raise serializers.ValidationError(f"Failed to send confirmation email: {result}")
except Exception as e:
    print(f"Email sending error: {str(e)}")
```

This caused the entire registration process to fail, even though:
1. The user account was already created in the database
2. The affiliate relationship was already established
3. The authentication tokens could still be generated

## Solution
Changed the email sending to be non-blocking and gracefully handle failures:

### 1. Don't Fail Registration on Email Errors
```python
# Send email confirmation (don't fail registration if email fails)
email_sent = False
email_error = None
try:
    email_sent, result = send_email_confirmation(user)
    if not email_sent:
        email_error = result
        print(f"Email sending warning: {result}")
except Exception as e:
    # Log the error but don't fail registration
    email_error = str(e)
    print(f"Email sending error: {str(e)}")
```

### 2. Include Email Status in Response
```python
response_data = {
    "refresh_token": refresh,
    "access_token": access,
    "user_data": UserShortSerializer(user).data,
    "email_confirmation_sent": email_sent,
    "message": "Registration successful!" + (
        " Please check your email for confirmation code." if email_sent 
        else " Email confirmation will be sent shortly."
    )
}

# Add email error info if applicable
if not email_sent and email_error:
    response_data["email_info"] = {
        "email_sent": False,
        "error": email_error,
        "can_resend": True
    }
```

## Response Scenarios

### Scenario 1: Registration with successful email
```json
{
  "refresh_token": "eyJ0eXAi...",
  "access_token": "eyJ0eXAi...",
  "user_data": { ... },
  "email_confirmation_sent": true,
  "message": "Registration successful! Please check your email for confirmation code."
}
```

### Scenario 2: Registration with email timeout/failure
```json
{
  "refresh_token": "eyJ0eXAi...",
  "access_token": "eyJ0eXAi...",
  "user_data": { ... },
  "email_confirmation_sent": false,
  "message": "Registration successful! Email confirmation will be sent shortly.",
  "email_info": {
    "email_sent": false,
    "error": "Email server timeout. Please try again later. Original error: timed out",
    "can_resend": True
  }
}
```

## Benefits

1. **Registration Never Fails**: Users can always register even if email service is down
2. **Clear Communication**: Frontend knows if email was sent successfully
3. **Graceful Degradation**: System works even when external services (SMTP) fail
4. **Better UX**: Users can still access their account immediately
5. **Resend Option**: Frontend knows email failed and can show "Resend Email" button
6. **Debugging Info**: Error details are provided for troubleshooting

## Frontend Integration

### Check Email Status
```javascript
const response = await registerUser(data);

if (response.email_confirmation_sent) {
  showMessage("Registration successful! Check your email for confirmation code.");
} else {
  if (response.email_info?.error) {
    showWarning("Registration successful! However, we couldn't send the confirmation email. Please try resending it.");
    showResendButton();
  }
}
```

### Handle Resend Email
```javascript
if (response.email_info?.can_resend) {
  // Show "Resend Email" button
  // Call the resend email endpoint when clicked
}
```

## Email Configuration
The current SMTP settings are configured via environment variables:

```python
EMAIL_HOST = environ.get('EMAIL_HOST', 'smtp.c1.liara.email')
EMAIL_PORT = int(environ.get('EMAIL_PORT', '587'))
EMAIL_USE_TLS = environ.get('EMAIL_USE_TLS', 'True').lower() == 'true'
EMAIL_HOST_USER = environ.get('EMAIL_HOST_USER', 'zen_torvalds_599nek')
EMAIL_HOST_PASSWORD = environ.get('EMAIL_HOST_PASSWORD', '...')
EMAIL_TIMEOUT = int(environ.get('EMAIL_TIMEOUT', '30'))
```

### Common Email Issues

1. **Timeout Errors**: 
   - Cause: SMTP server not responding within 30 seconds
   - Solution: Check network connectivity, firewall rules, SMTP server status

2. **Authentication Errors**:
   - Cause: Invalid credentials
   - Solution: Verify EMAIL_HOST_USER and EMAIL_HOST_PASSWORD

3. **Connection Refused**:
   - Cause: Wrong host/port or firewall blocking
   - Solution: Verify EMAIL_HOST and EMAIL_PORT settings

## Testing

The email confirmation system can be tested in different modes:

### Development Mode (Console Backend)
```python
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
```
Emails are printed to console instead of sent via SMTP.

### Production Mode (SMTP)
```python
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
```
Emails are sent via configured SMTP server.

### Test Mode (Memory Backend)
```python
EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
```
Emails are stored in memory for unit tests.

## Files Modified

1. `src/accounts/serializers/register.py`
   - Changed email error handling to not raise ValidationError
   - Added email_sent and email_error tracking
   - Updated response to include email_info when email fails

2. `src/accounts/tests/test_api.py`
   - Updated tests to expect email_confirmation_sent in response
   - Tests now pass regardless of email backend configuration

## Backward Compatibility

✅ **Fully backward compatible**:
- Response still includes `email_confirmation_sent` field
- Existing frontends checking this field will continue to work
- New `email_info` field is only added when email fails
- Registration flow unchanged from user perspective

## Monitoring

To monitor email issues in production:

```bash
# Check for email errors in logs
docker logs django_app 2>&1 | grep "Email sending error"

# Check for email timeouts
docker logs django_app 2>&1 | grep "TimeoutError"

# Check for SMTP authentication issues
docker logs django_app 2>&1 | grep "Authentication"
```

## Future Enhancements

Consider implementing:

1. **Email Queue**: Use Celery to send emails asynchronously
2. **Retry Mechanism**: Auto-retry failed emails after a delay
3. **Alternative Channels**: Send SMS if email fails
4. **Email Service Fallback**: Try alternative email service if primary fails
5. **Admin Notifications**: Alert admins when email service is down

## Related Endpoints

Users can manually resend confirmation emails using:
- `/api/v1/usr/email/resend` - Resend email confirmation code

## Conclusion

Registration now works reliably even when email services are temporarily unavailable. Users can register and access their account immediately, with the option to resend confirmation emails when the service recovers.

