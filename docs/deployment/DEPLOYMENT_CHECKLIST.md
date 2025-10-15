# 🚀 Subscription Fix - Deployment Checklist

## Pre-Deployment

- [ ] Review all code changes in:
  - `src/billing/models.py` - Added `deactivate_subscription()` method
  - `src/billing/signals.py` - Removed aggressive token check
  - `src/billing/services.py` - Removed immediate deactivation on token depletion
  - `src/billing/views.py` - Updated to use new deactivation method
  - `src/billing/management/commands/check_subscription_status.py` - New command

- [ ] Run tests locally:
  ```bash
  python test_subscription_fix.py
  ```

- [ ] Check for linting errors:
  ```bash
  cd src
  python -m flake8 billing/
  ```

## Deployment Steps

### 1. Backup Database (Critical!)
```bash
# Backup subscription data
python src/manage.py dumpdata billing.Subscription > backup_subscriptions_$(date +%Y%m%d).json
python src/manage.py dumpdata message.Conversation > backup_conversations_$(date +%Y%m%d).json
```

- [ ] Database backup completed
- [ ] Backup files verified and saved securely

### 2. Deploy Code
```bash
git add .
git commit -m "Fix: Prevent unexpected subscription deactivations

- Remove aggressive pre_save signal that deactivated on every save
- Separate status check from enforcement for controlled deactivation
- Add explicit deactivate_subscription() method with logging
- Create management command for periodic subscription checks
- Prevent token depletion from triggering immediate deactivation

Resolves issue where subscriptions ended suddenly and chats
converted to manual support mode without warning."

git push origin main
```

- [ ] Code pushed to repository
- [ ] Production server pulled latest changes

### 3. Restart Services
```bash
# Restart Django
sudo systemctl restart gunicorn
# Or if using Docker
docker-compose restart web

# Restart Celery (if applicable)
sudo systemctl restart celery
```

- [ ] Django service restarted
- [ ] Celery service restarted (if applicable)
- [ ] No errors in logs after restart

### 4. Verify Deployment
```bash
# Check Django logs
tail -f /path/to/logs/django.log

# Test the new management command
python src/manage.py check_subscription_status --dry-run
```

- [ ] Logs show no errors
- [ ] Management command runs successfully
- [ ] Dry-run shows expected output

## Post-Deployment

### 5. Monitor for 24-48 Hours
```bash
# Watch for subscription-related logs
tail -f src/logs/django.log | grep -i subscription

# Check for any deactivation warnings
grep "Deactivating subscription" src/logs/django.log
```

- [ ] Monitor logs for 24 hours
- [ ] No unexpected deactivations reported
- [ ] No user complaints about service interruption

### 6. Set Up Periodic Checks (Optional but Recommended)
```bash
# Add to crontab
crontab -e

# Add this line (adjust path as needed):
0 2 * * * cd /path/to/Fiko-Backend && source venv/bin/activate && python src/manage.py check_subscription_status >> /path/to/logs/subscription_checks.log 2>&1
```

- [ ] Cron job added
- [ ] First automatic run verified
- [ ] Log rotation configured

### 7. Review Existing Subscriptions (Optional)
```python
# Check if any subscriptions were mistakenly deactivated before the fix
from django.contrib.auth import get_user_model
from billing.models import Subscription
from django.utils import timezone

User = get_user_model()

# Find inactive subscriptions that still have tokens and valid end_date
potentially_mistaken = Subscription.objects.filter(
    is_active=False,
    tokens_remaining__gt=0
).exclude(end_date__lt=timezone.now())

print(f"Found {potentially_mistaken.count()} potentially mistaken deactivations")
for sub in potentially_mistaken:
    print(f"User: {sub.user.username}, Tokens: {sub.tokens_remaining}, End: {sub.end_date}")
```

- [ ] Checked for mistakenly deactivated subscriptions
- [ ] Reviewed and reactivated if necessary
- [ ] Users notified if reactivated

## Rollback Plan (If Needed)

If issues arise after deployment:

### Quick Rollback
```bash
# 1. Revert code changes
git revert HEAD
git push origin main

# 2. Pull on production
git pull origin main

# 3. Restart services
sudo systemctl restart gunicorn
sudo systemctl restart celery

# 4. Restore database if needed
python src/manage.py loaddata backup_subscriptions_YYYYMMDD.json
python src/manage.py loaddata backup_conversations_YYYYMMDD.json
```

### If Rollback Fails
- [ ] Contact senior developer
- [ ] Review logs: `/path/to/logs/django.log`
- [ ] Check database integrity
- [ ] Restore from full database backup

## Testing in Production

### Manual Test Cases

1. **Test token consumption doesn't deactivate**:
   - Create test user with subscription
   - Consume some tokens
   - Verify subscription stays active

2. **Test management command**:
   ```bash
   python src/manage.py check_subscription_status --dry-run
   ```

3. **Test explicit deactivation**:
   - Use Django admin or shell
   - Call `subscription.deactivate_subscription('test')`
   - Verify proper logging

## Success Criteria

- [ ] No unexpected subscription deactivations for 48 hours
- [ ] Token consumption works normally
- [ ] Management command runs without errors
- [ ] Logs show proper deactivation reasons when needed
- [ ] No user complaints about sudden service loss
- [ ] All tests pass

## Communication

### Internal Team
- [ ] Notify team about deployment
- [ ] Share documentation links
- [ ] Brief on new management command usage

### Users (If Applicable)
- [ ] Prepare announcement about improved stability
- [ ] Create support article about subscription management
- [ ] Monitor support tickets for related issues

## Documentation Updates

- [ ] Update internal wiki/docs with new subscription management process
- [ ] Document new management command in admin guide
- [ ] Add troubleshooting guide for subscription issues

## Final Sign-Off

- [ ] Deployment completed successfully
- [ ] All checklist items completed
- [ ] No critical issues identified
- [ ] Team notified of successful deployment

**Deployment Date**: _______________  
**Deployed By**: _______________  
**Verified By**: _______________  

---

## Quick Reference Commands

```bash
# Check subscription status (safe, no changes)
python src/manage.py check_subscription_status --dry-run

# Check with low token warnings
python src/manage.py check_subscription_status --dry-run --warn-threshold 200

# Deactivate expired subscriptions only
python src/manage.py check_subscription_status

# Deactivate zero-token subscriptions (careful!)
python src/manage.py check_subscription_status --deactivate-zero-tokens

# Monitor logs
tail -f src/logs/django.log | grep -i subscription

# Run tests
python test_subscription_fix.py
```

## Support Contacts

- **Technical Issues**: [Your team contact]
- **Database Issues**: [DBA contact]
- **Emergency**: [On-call contact]

---

**Remember**: This fix prevents aggressive auto-deactivation. Subscriptions will now only deactivate when explicitly requested or when checked via the management command.

