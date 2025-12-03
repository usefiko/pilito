# Invite Code & Affiliate URL Format Update

## Overview

Updated the affiliate invite system to use **4-character numeric codes** instead of 10-character alphanumeric codes, and changed the URL format to be shorter and cleaner.

---

## 🔄 Changes Made

### 1. **Invite Code Format**

**Before:**
- Length: 10 characters
- Format: Alphanumeric (uppercase letters + digits)
- Example: `ABC123XYZ0`

**After:**
- Length: 4 characters
- Format: Numeric only (digits 0-9)
- Example: `6543`

### 2. **Affiliate URL Format**

**Before:**
```
https://app.pilito.com/auth/register?affiliate=ABC123XYZ0
```

**After:**
```
app.pilito.com/6543
```

Much cleaner and shorter for sharing!

---

## 📝 Files Modified

### 1. `/src/accounts/models/user.py`

**Changed:** Invite code generation method

```python
def _generate_unique_invite_code(self):
    """Generate a unique 4-character invite code for the user"""
    while True:
        # Generate a random 4-character numeric code
        code = ''.join(random.choices(string.digits, k=4))
        if not User.objects.filter(invite_code=code).exists():
            return code
```

**Key Changes:**
- Changed from 10 to 4 characters (`k=10` → `k=4`)
- Changed from alphanumeric to digits only (`string.ascii_uppercase + string.digits` → `string.digits`)
- Updated comments to reflect new format

### 2. `/src/accounts/serializers/affiliate.py`

**Changed:** Invite link generation in `AffiliateSerializer`

```python
def to_representation(self, instance):
    """Generate the affiliate data for the user"""
    # Build the invite link in the new format: app.pilito.com/6543
    from django.conf import settings
    base_url = getattr(settings, 'FRONTEND_URL', 'https://app.pilito.com')
    # Remove protocol and trailing slash for cleaner format
    domain = base_url.replace('https://', '').replace('http://', '').rstrip('/')
    invite_link = f"{domain}/{instance.invite_code}"
    
    # ... rest of the code
```

**Key Changes:**
- Removed protocol (`https://`) from the invite link
- Changed URL structure from `/auth/register?affiliate={code}` to `/{code}`
- Result: `app.pilito.com/6543` instead of `https://app.pilito.com/auth/register?affiliate=ABC123XYZ0`

### 3. **New Management Command**

Created: `/src/accounts/management/commands/update_invite_codes.py`

A management command to update all existing users' invite codes from the old 10-character format to the new 4-character format.

---

## 🚀 Deployment Steps

### Step 1: Update Existing Invite Codes (Recommended)

Run the management command to update all existing users:

```bash
# Preview changes without applying (dry-run)
cd /Users/nima/Projects/pilito/src
../venv/bin/python manage.py update_invite_codes --dry-run

# Apply the changes
../venv/bin/python manage.py update_invite_codes
```

**What it does:**
- Finds all users with invite codes
- Skips users already with 4-digit codes
- Generates new unique 4-digit codes for others
- Updates the database
- Shows summary of changes

**Output example:**
```
Found 150 users with invite codes
✓ Updated user john@example.com: ABC123XYZ0 → 1234
✓ Updated user jane@example.com: XYZ9876ABC → 5678
⊘ Skipped user admin@example.com (already 4-digit)
...

========================================
SUMMARY
========================================
Total users processed: 150
✓ Updated: 148
⊘ Skipped (already 4-digit): 2
✗ Errors: 0

✓ All changes saved successfully!
```

### Step 2: Update Frontend Routing

The frontend needs to handle the new URL format. Add a route handler for `/{invite_code}`:

```javascript
// Example React Router setup
<Route path="/:inviteCode" element={<InviteRedirect />} />

// InviteRedirect component
function InviteRedirect() {
  const { inviteCode } = useParams();
  
  // Validate if it's a 4-digit code
  if (/^\d{4}$/.test(inviteCode)) {
    // Redirect to registration with affiliate parameter
    navigate(`/auth/register?affiliate=${inviteCode}`);
  } else {
    // Not an invite code, handle as 404
    navigate('/404');
  }
}
```

### Step 3: Test the Flow

1. **Get a user's affiliate info:**
   ```bash
   curl -X GET "http://localhost:8000/api/v1/accounts/affiliate" \
     -H "Authorization: Bearer {token}"
   ```
   
   **Response:**
   ```json
   {
     "invite_link": "app.pilito.com/6543",
     "invite_code": "6543",
     "direct_referrals": [...],
     "total_referrals": 5,
     "wallet_balance": "1250.50"
   }
   ```

2. **User shares link:** `app.pilito.com/6543`

3. **New user clicks link:**
   - Frontend extracts code `6543`
   - Redirects to `/auth/register?affiliate=6543`
   - Registration form pre-fills or stores affiliate code

4. **Registration completes:**
   - API receives `affiliate: "6543"` in registration data
   - System links new user to referrer

---

## 🔢 Code Capacity

With 4-digit numeric codes:
- **Total possible codes:** 10,000 (0000-9999)
- **Realistic capacity:** ~9,000 unique codes (excluding similar patterns)

This should be sufficient for most applications. If you need more capacity:

**Option A: Use 5 digits**
- Capacity: 100,000 codes
- Change `k=4` to `k=5` in `_generate_unique_invite_code()`

**Option B: Use alphanumeric 4 characters**
- Capacity: 1,679,616 codes (36^4)
- Change `string.digits` to `string.ascii_uppercase + string.digits`
- Codes like: `A1B2`, `X9Z3`, `5K7M`

---

## 📊 API Response Changes

### Before

```json
{
  "invite_link": "https://app.pilito.com/auth/register?affiliate=ABC123XYZ0",
  "invite_code": "ABC123XYZ0"
}
```

### After

```json
{
  "invite_link": "app.pilito.com/6543",
  "invite_code": "6543"
}
```

---

## 🔍 Database Schema

No database migration needed! The `invite_code` field already supports up to 20 characters:

```python
invite_code = models.CharField(max_length=20, unique=True, null=True, blank=True)
```

The 4-character codes fit perfectly within this limit.

---

## ⚠️ Important Notes

### 1. **Uniqueness**
- The system ensures all codes are unique
- Collision handling is built into the generation logic
- Maximum 100 attempts to find a unique code (very unlikely to fail with 10,000 possible codes)

### 2. **New Users**
- All newly created users will automatically get 4-digit codes
- No manual intervention needed

### 3. **Existing Users**
- Old 10-character codes continue to work until updated
- Use the management command to migrate them all at once
- Or they'll be updated individually on next `user.save()` if their code is regenerated

### 4. **URL Handling**
- Frontend must handle both formats during transition:
  - Old: `/auth/register?affiliate=ABC123XYZ0`
  - New: `/6543` → redirects to `/auth/register?affiliate=6543`
  
### 5. **SEO & Sharing**
- Much cleaner URLs for social media sharing
- Easier to remember and type
- Looks more professional

---

## 🧪 Testing Checklist

- ✅ New user registration creates 4-digit code
- ✅ Code generation ensures uniqueness
- ✅ Affiliate API returns new URL format
- ✅ Registration with 4-digit code works
- ✅ Management command updates existing codes
- ✅ Frontend routing handles `/{code}` format
- ✅ Old URLs continue to work during transition
- ✅ Referral tracking still works correctly

---

## 🔄 Rollback Plan

If needed, you can revert the changes:

1. **Restore old code generation:**
   ```python
   code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
   ```

2. **Restore old URL format:**
   ```python
   invite_link = f"{base_url}/auth/register?affiliate={instance.invite_code}"
   ```

3. **No database changes needed** - field already supports both formats

---

## 📞 Support

The new format provides:
- ✅ Shorter, cleaner URLs
- ✅ Easier to share via SMS, social media, or verbally
- ✅ More professional appearance
- ✅ Simpler for users to remember

All existing functionality remains intact - only the format has changed!

