# 🚨 TROUBLESHOOTING: Backblaze B2 "Malformed Access Key Id" Error

## ❌ Error You're Seeing

```
upload failed: An error occurred (InvalidAccessKeyId) when calling the PutObject operation: Malformed Access Key Id
```

---

## 🔍 Root Cause

The **Backblaze B2 Application Key ID** in your `docker-compose.backup.yml` is **incomplete or incorrect**.

The Key ID you provided (`61242eff92a8`) is only **12 characters**, but Backblaze B2 Key IDs are typically **25 characters long**.

---

## ✅ SOLUTION (3 Options)

### **Option 1: Use the Automated Fix Script** ⚡ (RECOMMENDED)

```bash
cd /root/pilito
./backup/fix_b2_credentials.sh
```

This script will:
1. Ask you for the correct Backblaze credentials
2. Update `docker-compose.backup.yml` automatically
3. Update `.env` automatically
4. Validate the inputs

Then test again:
```bash
docker compose -f docker-compose.backup.yml up --abort-on-container-exit
```

---

### **Option 2: Manual Fix** 🔧

#### Step 1: Get Your FULL Backblaze B2 Credentials

1. **Log into Backblaze B2:**  
   https://secure.backblaze.com/user_signin.htm

2. **Navigate to "App Keys"** in the left sidebar

3. **Find your key or create a new one:**
   - Click "Add a New Application Key" if needed
   - Name: `pilito-backup`
   - Bucket: `pilito`
   - Permissions: All

4. **Copy BOTH values:**
   - **`keyID`** - ~25 characters (like `0012a3456789b0c0000000001`)
   - **`applicationKey`** - The secret key (longer string)

⚠️ **IMPORTANT:** The `applicationKey` is only shown ONCE when created. Save it!

---

#### Step 2: Update docker-compose.backup.yml

```bash
nano docker-compose.backup.yml
```

Find this section:

```yaml
environment:
  # Backblaze B2 Credentials (S3-Compatible API)
  - AWS_ACCESS_KEY_ID=61242eff92a8  # ← CHANGE THIS
  - AWS_SECRET_ACCESS_KEY=${B2_APPLICATION_KEY}
  - AWS_DEFAULT_REGION=us-west-004
  - B2_BUCKET=pilito
```

**Replace with your FULL keyID:**

```yaml
environment:
  # Backblaze B2 Credentials (S3-Compatible API)
  - AWS_ACCESS_KEY_ID=0012a3456789b0c0000000001  # ← Your FULL 25-char keyID
  - AWS_SECRET_ACCESS_KEY=${B2_APPLICATION_KEY}
  - AWS_DEFAULT_REGION=us-west-004
  - B2_BUCKET=pilito
```

Save the file (Ctrl+O, Enter, Ctrl+X)

---

#### Step 3: Update .env File

```bash
nano .env
```

Add or update this line:

```bash
B2_APPLICATION_KEY=your_full_application_key_secret_from_backblaze
```

Save the file.

---

#### Step 4: Test the Backup

```bash
docker compose -f docker-compose.backup.yml up --abort-on-container-exit
```

You should see:
```
✅ Backup uploaded successfully to Backblaze B2!
✅ Upload verified successfully on Backblaze B2.
```

---

### **Option 3: Use Environment Variables Only** 🔒 (Most Secure)

Instead of hardcoding the keyID, use environment variables for BOTH credentials.

#### Step 1: Update docker-compose.backup.yml

```bash
nano docker-compose.backup.yml
```

Change:
```yaml
environment:
  - AWS_ACCESS_KEY_ID=61242eff92a8  # ← Remove this
```

To:
```yaml
environment:
  - AWS_ACCESS_KEY_ID=${B2_KEY_ID}  # ← Use env variable
```

#### Step 2: Update .env

```bash
nano .env
```

Add BOTH credentials:
```bash
# Backblaze B2 Credentials
B2_KEY_ID=0012a3456789b0c0000000001
B2_APPLICATION_KEY=your_full_application_key_secret
```

#### Step 3: Test

```bash
docker compose -f docker-compose.backup.yml up --abort-on-container-exit
```

---

## 🔍 How to Find Your Backblaze B2 Credentials

### Visual Guide:

1. **Login to Backblaze B2:**
   ```
   https://secure.backblaze.com/user_signin.htm
   ```

2. **Click "App Keys" in the left sidebar**

3. **You'll see a table like this:**
   ```
   ┌───────────────────┬─────────────────────────┬────────────┐
   │ Key Name          │ keyID                   │ Bucket     │
   ├───────────────────┼─────────────────────────┼────────────┤
   │ Master App Key    │ 0012a3456789b0c00000001 │ All        │
   │ pilito-backup     │ 001b2c3d4e5f6789a0b0002 │ pilito     │
   └───────────────────┴─────────────────────────┴────────────┘
   ```

4. **Copy the FULL `keyID`** (25 characters)

5. **For the `applicationKey`:**
   - If you're creating a NEW key: It shows once when created
   - If using EXISTING key: You'll need to create a new one (Backblaze doesn't show old secrets)

---

## ✅ Verification Steps

After updating credentials:

### 1. Verify docker-compose.backup.yml
```bash
grep "AWS_ACCESS_KEY_ID" docker-compose.backup.yml
```

Should show:
```
- AWS_ACCESS_KEY_ID=0012a3456789b0c0000000001  # (25 characters)
```

### 2. Verify .env
```bash
grep "B2_APPLICATION_KEY" .env
```

Should show:
```
B2_APPLICATION_KEY=your_long_secret_key_here
```

### 3. Test Connection
```bash
# Install AWS CLI if not installed
apt-get update && apt-get install -y awscli

# Load environment variables
source .env

# Test connection to B2
aws --endpoint-url https://s3.us-west-004.backblazeb2.com \
    s3 ls s3://pilito/
```

If successful, you should see your bucket contents (or empty if no files yet).

---

## 🎯 Expected Output After Fix

When you run the backup again, you should see:

```
[2025-12-12 21:37:32] Uploading backup to Backblaze B2...
[2025-12-12 21:37:32]   Endpoint: https://s3.us-west-004.backblazeb2.com
[2025-12-12 21:37:32]   Bucket: s3://pilito/
[2025-12-12 21:37:32]   File: postgres_backup_2025-12-12_21-37.sql.gz
upload: ../backups/postgres_backup_2025-12-12_21-37.sql.gz to s3://pilito/postgres_backup_2025-12-12_21-37.sql.gz
[2025-12-12 21:37:35] Backup uploaded successfully to Backblaze B2!
[2025-12-12 21:37:35] Verifying upload on Backblaze B2...
[2025-12-12 21:37:36] Upload verified successfully on Backblaze B2.
[2025-12-12 21:37:36] Cleaning up local backups older than 7 days...
[2025-12-12 21:37:36] No old backups found to delete.
[2025-12-12 21:37:36] ==========================================
[2025-12-12 21:37:36] Backup Process Completed Successfully!
[2025-12-12 21:37:36] ==========================================
```

---

## 🆘 Still Having Issues?

### Check Backblaze B2 Bucket Settings

1. **Bucket must exist:** `pilito`
2. **Bucket must be in the correct region:** `us-west-004`
3. **Application Key must have permissions:** `writeFiles`, `readFiles`, `deleteFiles`

### Create a New Application Key

If you're unsure about your credentials:

1. Go to Backblaze B2 → **App Keys**
2. Click **"Add a New Application Key"**
3. Settings:
   - Name: `pilito-backup-new`
   - Allow access to: `pilito` (specific bucket)
   - Type: `Read and Write`
   - Duration: `Never expire`
4. Click **Create New Key**
5. **IMMEDIATELY SAVE** both `keyID` and `applicationKey`
6. Update your config with these NEW credentials

---

## 📞 Quick Fix Command

Run this on your server:

```bash
cd /root/pilito
./backup/fix_b2_credentials.sh
```

Follow the prompts, then test:

```bash
docker compose -f docker-compose.backup.yml up --abort-on-container-exit
```

---

**🎯 Once fixed, your backups will upload successfully to Backblaze B2!**




