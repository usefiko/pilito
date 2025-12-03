# SMTP Email Timeout - Troubleshooting Guide

## Current Issue

```
TimeoutError: timed out
```

The Django application cannot connect to the Liara SMTP server (`smtp.c1.liara.email:587`) within the 30-second timeout.

**Good News**: Registration now continues successfully even with email failures! ✅

**Issue to Fix**: Email delivery is still not working.

---

## Quick Diagnosis

### Step 1: Run the SMTP Diagnostic Tool

From your project root:

```bash
# On host machine
python test_smtp_connection.py

# Inside Docker container
docker exec -it django_app python /app/test_smtp_connection.py
```

This will test:
- ✅ DNS resolution
- ✅ Port connectivity  
- ✅ SMTP handshake
- ✅ STARTTLS
- ✅ Authentication

### Step 2: Test from Docker Container

```bash
# Enter the container
docker exec -it django_app bash

# Test DNS resolution
nslookup smtp.c1.liara.email

# Test port connectivity
nc -zv smtp.c1.liara.email 587

# Or use telnet
telnet smtp.c1.liara.email 587
```

---

## Common Causes & Solutions

### 🔥 Cause 1: Docker Network Isolation

**Symptom**: Works on host machine but fails in Docker

**Solution**: Ensure Docker container has network access

```yaml
# docker-compose.yml
services:
  django_app:
    # ... other config ...
    network_mode: "bridge"  # or "host" for testing
```

**Test**:
```bash
docker exec -it django_app ping smtp.c1.liara.email
docker exec -it django_app curl -v telnet://smtp.c1.liara.email:587
```

---

### 🔥 Cause 2: Firewall Blocking Outbound SMTP

**Symptom**: Connection timeout after 30 seconds

**Solution**: Allow outbound traffic on port 587

#### For Ubuntu/Debian:
```bash
# Check firewall status
sudo ufw status

# Allow outbound SMTP
sudo ufw allow out 587/tcp
sudo ufw allow out 25/tcp  # Traditional SMTP (optional)

# For iptables
sudo iptables -A OUTPUT -p tcp --dport 587 -j ACCEPT
```

#### For Docker Host:
```bash
# Ensure Docker has network access
sudo iptables -L DOCKER-USER

# If blocked, allow SMTP
sudo iptables -I DOCKER-USER -p tcp --dport 587 -j ACCEPT
```

---

### 🔥 Cause 3: Liara Email Service Configuration

**Symptom**: Authentication errors or connection refused

**Solution**: Verify Liara email configuration

1. **Check Liara Dashboard**:
   - Go to https://console.liara.ir
   - Navigate to Email service
   - Verify service is active and running
   - Check credentials match your environment variables

2. **Verify Environment Variables**:
```bash
# Inside container
echo $EMAIL_HOST
echo $EMAIL_PORT
echo $EMAIL_HOST_USER
echo $EMAIL_HOST_PASSWORD
```

3. **Update if needed**:
```bash
# In your .env file or docker-compose.yml
EMAIL_HOST=smtp.c1.liara.email
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your_liara_username
EMAIL_HOST_PASSWORD=your_liara_password
EMAIL_TIMEOUT=30
```

---

### 🔥 Cause 4: DNS Resolution Issues

**Symptom**: "Name or service not known"

**Solution**: Fix DNS configuration

```bash
# Check DNS resolution
docker exec -it django_app cat /etc/resolv.conf

# Add Google DNS if needed
docker-compose.yml:
  django_app:
    dns:
      - 8.8.8.8
      - 8.8.4.4
```

---

### 🔥 Cause 5: Server Location/Network Latency

**Symptom**: Timeout specifically with Liara servers

**Solution**: Increase timeout or use alternative approach

#### Option A: Increase Timeout
```python
# settings/common.py
EMAIL_TIMEOUT = int(environ.get('EMAIL_TIMEOUT', '60'))  # Increase to 60s
```

#### Option B: Use Async Email (Recommended)
Make email sending asynchronous using Celery:

```python
# accounts/tasks.py
from celery import shared_task
from accounts.utils import send_email_confirmation

@shared_task(bind=True, max_retries=3)
def send_email_confirmation_async(self, user_id):
    """Send email confirmation asynchronously"""
    try:
        from django.contrib.auth import get_user_model
        User = get_user_model()
        user = User.objects.get(id=user_id)
        return send_email_confirmation(user)
    except Exception as exc:
        # Retry after 30 seconds
        raise self.retry(exc=exc, countdown=30)
```

```python
# In RegisterSerializer.create()
# Instead of:
# send_email_confirmation(user)

# Use:
from accounts.tasks import send_email_confirmation_async
send_email_confirmation_async.delay(user.id)
```

---

## Temporary Workarounds

### Workaround 1: Use Console Backend for Testing

```python
# settings/development.py or settings/production.py
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
```

Emails will be printed to console instead of sent via SMTP.

### Workaround 2: Use File Backend

```python
# settings/development.py
EMAIL_BACKEND = 'django.core.mail.backends.filebased.EmailBackend'
EMAIL_FILE_PATH = '/tmp/app-emails'
```

Emails will be saved to files for inspection.

### Workaround 3: Use Alternative Email Service

Try a different SMTP provider as a test:

```python
# Using Gmail (for testing only)
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'your-email@gmail.com'
EMAIL_HOST_PASSWORD = 'your-app-password'  # Use App Password, not regular password
```

---

## Recommended Solution: Celery + Redis for Async Emails

### Why?
- ✅ Non-blocking registration
- ✅ Automatic retries on failure
- ✅ Better user experience
- ✅ Can handle SMTP service outages
- ✅ Scalable for high traffic

### Implementation:

#### 1. Add to docker-compose.yml:
```yaml
services:
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

  celery_worker:
    build: .
    command: celery -A core worker -l info
    volumes:
      - ./src:/app
    environment:
      - CELERY_BROKER_URL=redis://redis:6379/0
    depends_on:
      - redis
      - db
```

#### 2. Update requirements:
```txt
celery==5.3.4
redis==5.0.1
```

#### 3. Create celery app:
```python
# core/celery.py (already exists)
# Ensure it's properly configured
```

#### 4. Create async task:
```python
# accounts/tasks.py
from celery import shared_task
from django.contrib.auth import get_user_model
from accounts.utils import send_email_confirmation
import logging

logger = logging.getLogger(__name__)

@shared_task(bind=True, max_retries=5)
def send_email_confirmation_async(self, user_id):
    """Send email confirmation asynchronously with retries"""
    try:
        User = get_user_model()
        user = User.objects.get(id=user_id)
        email_sent, result = send_email_confirmation(user)
        
        if not email_sent:
            logger.warning(f"Email send failed for user {user_id}: {result}")
            # Retry after exponential backoff: 1min, 2min, 4min, 8min, 16min
            raise self.retry(exc=Exception(result), countdown=60 * (2 ** self.request.retries))
        
        return {'success': True, 'user_id': user_id}
    except User.DoesNotExist:
        logger.error(f"User {user_id} not found")
        return {'success': False, 'error': 'User not found'}
    except Exception as exc:
        logger.error(f"Email send error for user {user_id}: {exc}")
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))
```

#### 5. Update RegisterSerializer:
```python
# In create() method, replace:
# send_email_confirmation(user)

# With:
from accounts.tasks import send_email_confirmation_async
email_task = send_email_confirmation_async.delay(user.id)
email_sent = False  # Will be sent async
```

---

## Testing Email Configuration

### Test Django Email in Shell:

```bash
docker exec -it django_app python src/manage.py shell
```

```python
from django.core.mail import send_mail
from django.conf import settings

# Test email sending
result = send_mail(
    subject='Test Email',
    message='This is a test email from Pilito',
    from_email=settings.DEFAULT_FROM_EMAIL,
    recipient_list=['test@example.com'],
    fail_silently=False,
)

print(f"Email sent: {result}")
```

---

## Monitoring Email Issues

### Check Logs:
```bash
# All email-related logs
docker logs django_app 2>&1 | grep -i email

# Timeout errors specifically
docker logs django_app 2>&1 | grep -i "timeout"

# SMTP errors
docker logs django_app 2>&1 | grep -i "smtp"
```

### Set Up Alerts:
Consider setting up monitoring for email delivery rates:
- Track successful email sends
- Alert when success rate drops below threshold
- Monitor SMTP connection times

---

## Production Recommendations

1. **Use Celery** for async email sending (most important!)
2. **Set up retry logic** with exponential backoff
3. **Monitor email delivery** with logging/metrics
4. **Have a fallback** email provider
5. **Increase timeout** to 60s for production
6. **Consider SMS** as alternative for critical notifications
7. **Set up health checks** for SMTP connectivity

---

## Quick Fix Commands

```bash
# 1. Test SMTP connectivity from container
docker exec -it django_app python /app/test_smtp_connection.py

# 2. Check current email settings
docker exec -it django_app python src/manage.py shell -c "from django.conf import settings; print(f'Host: {settings.EMAIL_HOST}, Port: {settings.EMAIL_PORT}')"

# 3. Test with console backend (temporary)
docker exec -it django_app bash
export EMAIL_BACKEND='django.core.mail.backends.console.EmailBackend'
python src/manage.py shell
# Then test sending email

# 4. Restart services
docker-compose restart django_app

# 5. Check network from container
docker exec -it django_app ping smtp.c1.liara.email
docker exec -it django_app telnet smtp.c1.liara.email 587
```

---

## Need More Help?

1. Run the diagnostic script and share output
2. Check Liara email service status
3. Verify firewall/network configuration
4. Consider implementing Celery for production
5. Contact Liara support if issue persists

---

## Summary

✅ **Registration works** - Users can register even when email fails
❌ **Email delivery** - Still needs fixing (SMTP connectivity)

**Immediate action**: Run diagnostic script to identify exact issue
**Long-term solution**: Implement Celery for async email sending

