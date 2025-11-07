# Email Image Caching Fix Guide

## Problem
You replaced `logo.png` with a new image (same filename), but emails still show the old logo.

## Why This Happens

### Multiple Cache Layers:
1. **Gmail's Cache** (24-48 hours) - The main culprit
2. **Django's Static Files** - Not yet collected
3. **Browser Cache** - Your browser cached the old image
4. **Email Client Cache** - Some email clients cache images

---

## ✅ Solution: Cache-Busting with Version Parameters

I've updated your email templates to use **cache-busting** by adding `?v=2` to all image URLs:

**Before:**
```html
<img src="https://api.pilito.com/static/email_assets/logo.png" />
```

**After:**
```html
<img src="https://api.pilito.com/static/email_assets/logo.png?v=2" />
```

This forces Gmail and browsers to fetch the new image instead of using the cached version.

---

## 🚀 Steps to Apply the Fix

### Step 1: Run the Update Script

```bash
cd /Users/nima/Projects/pilito
./update_static_files.sh
```

This script will:
- Remove old collected static files
- Run `collectstatic` to collect the new logo
- Restart your Django application
- Verify the new image is accessible

### Step 2: Test with a New Email

**Important:** You must send a **NEW** email to test:

```bash
# Send a test email
cd src
python manage.py send_test_emails --email your@email.com --type reset
```

Or trigger a real password reset/confirmation email from your app.

### Step 3: Verify

- ✅ Check the **NEWLY sent** email (not old emails)
- ✅ Look for `?v=2` in the image URL when you inspect it
- ✅ The logo should be updated

---

## 📋 Files Updated

### Email Templates (Cache-Busting Added):
1. ✅ `src/templates/emails/password_reset.html`
   - Logo: `logo.png?v=2`
   - Background: `bg.jpg?v=2`
   - Social icons: `facebook.png?v=2`, `instagram.png?v=2`, `telegram.png?v=2`

2. ✅ `src/templates/emails/email_confirmation.html`
   - Logo: `logo.png?v=2`
   - Background: `bg.jpg?v=2`
   - Social icons: `facebook.png?v=2`, `instagram.png?v=2`, `telegram.png?v=2`

### Scripts Created:
- ✅ `update_static_files.sh` - Automated update script

---

## ⚠️ Important Notes

### Old Emails Will Not Update
- **Old emails** that were already sent **will still show the old logo**
- This is because Gmail cached the image when the email was first sent
- There's **no way** to update images in already-sent emails

### New Emails Will Show New Logo
- **NEW emails** sent after this fix will show the **new logo**
- Gmail will fetch the new image because of the `?v=2` parameter

### Gmail Cache Duration
- Gmail caches images for **24-48 hours**
- Even without cache-busting, the old cache would expire eventually
- Cache-busting makes it immediate for new emails

---

## 🔧 Manual Steps (if script fails)

If the automated script doesn't work, run these manually:

### For Docker Compose:

```bash
# Remove old static files
docker-compose exec web rm -rf /app/staticfiles/email_assets/

# Collect new static files
docker-compose exec web python manage.py collectstatic --noinput

# Restart Django
docker-compose restart web

# Test the URL
curl -I https://api.pilito.com/static/email_assets/logo.png?v=2
```

### For Docker Swarm:

```bash
# Update the service (this collects static and restarts)
docker service update --force pilito_web

# Wait for it to restart
sleep 10

# Test the URL
curl -I https://api.pilito.com/static/email_assets/logo.png?v=2
```

### For Local Development:

```bash
cd src

# Remove old static files
rm -rf staticfiles/email_assets/

# Collect new static files
python manage.py collectstatic --noinput

# Restart Django dev server
# (Just stop and start it again)
```

---

## 🧪 Testing

### Test with Command:
```bash
cd src
python manage.py send_test_emails --email your@email.com --type reset
```

### Test Manually:
1. Go to your app's password reset page
2. Enter an email address
3. Check the email
4. Inspect the logo image URL - should see `?v=2`

### Verify URL Directly:
```bash
# Should return HTTP 200
curl -I https://api.pilito.com/static/email_assets/logo.png?v=2
```

---

## 🔄 Future Logo Updates

When you need to change the logo again:

### Method 1: Increment Version (Recommended)

1. Replace `logo.png` with your new image
2. Edit both email templates:
   - Change `logo.png?v=2` to `logo.png?v=3`
3. Run the update script:
   ```bash
   ./update_static_files.sh
   ```

### Method 2: Use Different Filename

1. Save new logo as `logo-v2.png` or `logo-new.png`
2. Edit templates to use the new filename
3. Run the update script

---

## 🐛 Troubleshooting

### "I still see the old logo in new emails"

1. **Check the email was sent AFTER the fix:**
   - Look at the email timestamp
   - Make sure it's after you ran the update script

2. **Check the image URL in the email:**
   - Right-click on the logo → Inspect
   - Look for `?v=2` in the URL
   - If it's not there, templates weren't updated

3. **Check Django collected the new file:**
   ```bash
   ls -la src/staticfiles/email_assets/logo.png
   ```

4. **Clear browser cache:**
   - Press Ctrl+Shift+Delete (or Cmd+Shift+Delete)
   - Clear images and cache
   - Reload the email

5. **Test in different email client:**
   - Forward the email to a different address
   - Check in a different email client
   - Try incognito/private mode

### "URL returns 404"

1. **Verify file exists:**
   ```bash
   ls -la src/static/email_assets/logo.png
   ls -la src/staticfiles/email_assets/logo.png
   ```

2. **Run collectstatic again:**
   ```bash
   docker-compose exec web python manage.py collectstatic --noinput
   ```

3. **Check Django is serving static files:**
   ```bash
   # In src/core/urls.py, make sure this line exists:
   urlpatterns += static(STATIC_URL, document_root=STATIC_ROOT)
   ```

### "Images work but social icons are still old"

- Social icons are also cache-busted with `?v=2`
- Follow the same steps as the logo
- If you didn't change them, they'll show the same image (which is correct)

---

## 📊 Summary

**What was done:**
- ✅ Added `?v=2` to all images in email templates
- ✅ Created automated update script
- ✅ Updated 2 email template files

**What you need to do:**
1. Run `./update_static_files.sh`
2. Send a **NEW** test email
3. Verify the logo is updated in the **NEW** email

**Remember:**
- Old emails = Old logo (can't be changed)
- New emails = New logo (with `?v=2`)
- This is normal Gmail behavior

---

## 🎯 Next Time You Update Images

1. Replace the image file in `src/static/email_assets/`
2. Edit templates to increment version: `?v=2` → `?v=3`
3. Run `./update_static_files.sh`
4. Send new emails

---

**Last Updated:** November 7, 2025

**Related Files:**
- `src/templates/emails/password_reset.html`
- `src/templates/emails/email_confirmation.html`
- `update_static_files.sh`

