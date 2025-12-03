# Quick SMTP Fix - Apply One of These Solutions

## Your Setup
- Docker containers running in default bridge network
- SMTP server: `smtp.c1.liara.email:587`
- Timeout: 30 seconds

## Issue
Docker container cannot reach external SMTP server (connection times out)

---

## 🚀 SOLUTION 1: Use Async Email with Celery (RECOMMENDED)

You already have Celery running! Let's use it for email sending.

### Step 1: Create Email Task

Create file: `src/accounts/tasks.py`

```python
from celery import shared_task
from django.contrib.auth import get_user_model
from accounts.utils import send_email_confirmation
import logging

logger = logging.getLogger(__name__)

@shared_task(bind=True, max_retries=5, default_retry_delay=60)
def send_email_confirmation_async(self, user_id):
    """
    Send email confirmation asynchronously with retries
    Retries: 5 times with 60 second delay between attempts
    """
    try:
        User = get_user_model()
        user = User.objects.get(id=user_id)
        
        logger.info(f"Attempting to send email confirmation to user {user_id} ({user.email})")
        email_sent, result = send_email_confirmation(user)
        
        if not email_sent:
            logger.warning(f"Email send failed for user {user_id}: {result}")
            # Retry with exponential backoff
            raise self.retry(
                exc=Exception(result), 
                countdown=60 * (2 ** self.request.retries)
            )
        
        logger.info(f"✅ Email successfully sent to user {user_id}")
        return {'success': True, 'user_id': user_id, 'email': user.email}
        
    except User.DoesNotExist:
        logger.error(f"❌ User {user_id} not found")
        return {'success': False, 'error': 'User not found'}
        
    except Exception as exc:
        logger.error(f"❌ Email send error for user {user_id}: {exc}")
        if self.request.retries < self.max_retries:
            # Retry with exponential backoff: 60s, 120s, 240s, 480s, 960s
            raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))
        else:
            logger.error(f"❌ Max retries reached for user {user_id}. Email sending failed permanently.")
            return {'success': False, 'error': str(exc), 'max_retries_reached': True}
```

### Step 2: Update RegisterSerializer

In `src/accounts/serializers/register.py`, update the email sending part:

```python
# Around line 53-64, replace the email sending code with:

# Send email confirmation asynchronously via Celery
email_sent = False
email_error = None
try:
    from accounts.tasks import send_email_confirmation_async
    # Queue the email to be sent asynchronously
    task = send_email_confirmation_async.apply_async(args=[user.id], countdown=2)
    email_sent = True  # Queued successfully
    print(f"✅ Email confirmation queued for async sending (task: {task.id})")
except Exception as e:
    email_error = str(e)
    print(f"❌ Failed to queue email: {str(e)}")
```

### Step 3: Restart Services

```bash
docker-compose restart web celery_worker
```

### Why This Works:
- ✅ Celery worker has more time (no 30s timeout during registration)
- ✅ Automatic retries (up to 5 times)
- ✅ Exponential backoff (waits longer between retries)
- ✅ Registration completes immediately
- ✅ User doesn't wait for email

---

## 🔧 SOLUTION 2: Fix Docker Network (If Firewall Issue)

### Option A: Add DNS Servers to docker-compose.yml

```yaml
services:
  web:
    # ... existing config ...
    dns:
      - 8.8.8.8      # Google DNS
      - 8.8.4.4      # Google DNS backup
      - 1.1.1.1      # Cloudflare DNS
```

### Option B: Test with Host Network (Debugging Only)

```yaml
services:
  web:
    # ... existing config ...
    network_mode: "host"  # Use host network (removes isolation)
```

**⚠️ Warning**: Host network removes container isolation. Use only for testing!

### Option C: Increase Timeout

```yaml
services:
  web:
    environment:
      # ... existing vars ...
      - EMAIL_TIMEOUT=120  # Increase from 30 to 120 seconds
```

---

## 🧪 SOLUTION 3: Use Alternative Email Provider (Testing)

### Try Gmail (for testing only):

```yaml
services:
  web:
    environment:
      - EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
      - EMAIL_HOST=smtp.gmail.com
      - EMAIL_PORT=587
      - EMAIL_USE_TLS=True
      - EMAIL_HOST_USER=your-email@gmail.com
      - EMAIL_HOST_PASSWORD=your-gmail-app-password
      - EMAIL_TIMEOUT=30
```

**Note**: Use Gmail App Password, not regular password. Create one at: https://myaccount.google.com/apppasswords

---

## 🎯 RECOMMENDED: Solution 1 (Celery)

This is the best approach because:
1. ✅ Works regardless of network issues
2. ✅ Automatic retries
3. ✅ Fast registration (no waiting)
4. ✅ Production-ready
5. ✅ You already have Celery running!

---

## Quick Test After Applying Solution 1

```bash
# 1. Check if Celery worker is running
docker logs celery_worker --tail 50

# 2. Test registration
curl -X POST http://localhost:8000/api/v1/usr/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@example.com",
    "password": "SecurePass123!"
  }'

# 3. Check Celery logs for email task
docker logs celery_worker --tail 50 | grep "send_email_confirmation_async"

# 4. Monitor email sending
docker logs celery_worker -f
```

---

## What You Should See After Fix

```
✅ Registration successful (immediate)
✅ Email task queued to Celery
✅ Celery worker picks up task
✅ Email sent (or retried if fails)
```

---

Would you like me to implement Solution 1 (Celery async emails) for you? It's the cleanest and most production-ready approach.

