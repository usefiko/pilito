# PostgreSQL Automated Backup System with Backblaze B2

## 📋 Overview

This system provides automated daily PostgreSQL backups with cloud storage on Backblaze B2.

### Features:
- ✅ Automated daily PostgreSQL dumps
- ✅ Gzip compression for reduced storage
- ✅ Automatic upload to Backblaze B2 (S3-compatible)
- ✅ Local retention policy (7 days)
- ✅ Comprehensive logging
- ✅ Production-ready error handling

---

## 📁 File Structure

```
pilito/
├── backup/
│   ├── backup.sh              # Main backup script
│   └── README.md              # This file
├── db_backups/                # Local backup storage (created automatically)
└── docker-compose.backup.yml  # Docker Compose backup service
```

---

## ⚙️ Configuration

### 1. Environment Variables

Create or update your `.env` file with the following variables:

```bash
# PostgreSQL Credentials
POSTGRES_USER=your_postgres_user
POSTGRES_PASSWORD=your_postgres_password
POSTGRES_DB=your_database_name

# Backblaze B2 Credentials
B2_APPLICATION_KEY=your_backblaze_application_key_secret
```

**Note:** The following are hardcoded in `docker-compose.backup.yml`:
- `AWS_ACCESS_KEY_ID=61242eff92a8` (Backblaze Key ID)
- `B2_BUCKET=pilito` (Bucket name)
- `AWS_DEFAULT_REGION=us-west-004`

### 2. Backblaze B2 Setup

Your Backblaze B2 credentials:
- **Application Key ID:** `61242eff92a8`
- **Bucket Name:** `pilito`
- **Region:** `us-west-004`
- **Endpoint:** `https://s3.us-west-004.backblazeb2.com`
- **Capabilities:** All permissions (writeFiles, readFiles, deleteFiles)

---

## 🚀 Usage

### Manual Backup

Run a backup manually:

```bash
cd /Users/nima/Projects/pilito
docker compose -f docker-compose.backup.yml up --abort-on-container-exit
```

### Automated Daily Backups with Cron

#### Step 1: Make the script executable
```bash
chmod +x /Users/nima/Projects/pilito/backup/backup.sh
```

#### Step 2: Edit your crontab
```bash
crontab -e
```

#### Step 3: Add the following line for daily backups at 2:00 AM
```cron
0 2 * * * cd /Users/nima/Projects/pilito && docker compose -f docker-compose.backup.yml up --abort-on-container-exit >> /Users/nima/Projects/pilito/backup/backup.log 2>&1
```

#### Cron Schedule Examples:

| Schedule | Cron Expression | Description |
|----------|----------------|-------------|
| Daily at 2:00 AM | `0 2 * * *` | Default recommendation |
| Daily at midnight | `0 0 * * *` | Run at 12:00 AM |
| Every 12 hours | `0 */12 * * *` | Run at 12:00 AM and 12:00 PM |
| Weekly (Sunday 3 AM) | `0 3 * * 0` | Once per week |
| Every 6 hours | `0 */6 * * *` | Run 4 times daily |

#### Step 4: Verify cron job
```bash
crontab -l
```

#### Step 5: Check backup logs
```bash
tail -f /Users/nima/Projects/pilito/backup/backup.log
```

---

## 📦 Backup File Naming

Backups are named with timestamps:
```
postgres_backup_YYYY-MM-DD_HH-MM.sql.gz
```

Examples:
- `postgres_backup_2025-12-13_02-00.sql.gz`
- `postgres_backup_2025-12-14_02-00.sql.gz`

---

## 🔄 Restore Instructions

### Step 1: List Available Backups on Backblaze B2

```bash
aws --endpoint-url https://s3.us-west-004.backblazeb2.com \
    s3 ls s3://pilito/ \
    --profile backblaze
```

Or configure AWS CLI with your credentials first:

```bash
aws configure set aws_access_key_id 61242eff92a8
aws configure set aws_secret_access_key YOUR_B2_APPLICATION_KEY
aws configure set region us-west-004
```

Then list backups:
```bash
aws --endpoint-url https://s3.us-west-004.backblazeb2.com s3 ls s3://pilito/
```

### Step 2: Download a Backup from Backblaze B2

```bash
# Example: Download specific backup
aws --endpoint-url https://s3.us-west-004.backblazeb2.com \
    s3 cp s3://pilito/postgres_backup_2025-12-13_02-00.sql.gz \
    ./postgres_backup_2025-12-13_02-00.sql.gz
```

### Step 3: Restore to PostgreSQL

#### Option A: Restore to Running Container

```bash
# Decompress and pipe directly to PostgreSQL
gunzip < postgres_backup_2025-12-13_02-00.sql.gz | \
docker exec -i postgres_db psql -U $POSTGRES_USER -d $POSTGRES_DB
```

#### Option B: Restore with Environment Variables

```bash
# Load environment variables from .env
source .env

# Restore
gunzip < postgres_backup_2025-12-13_02-00.sql.gz | \
docker exec -i postgres_db psql -U $POSTGRES_USER -d $POSTGRES_DB
```

#### Option C: Restore to a Fresh Database

```bash
# Drop existing database (CAREFUL!)
docker exec -i postgres_db psql -U $POSTGRES_USER -c "DROP DATABASE IF EXISTS $POSTGRES_DB;"

# Create fresh database
docker exec -i postgres_db psql -U $POSTGRES_USER -c "CREATE DATABASE $POSTGRES_DB;"

# Restore backup
gunzip < postgres_backup_2025-12-13_02-00.sql.gz | \
docker exec -i postgres_db psql -U $POSTGRES_USER -d $POSTGRES_DB
```

### Step 4: Verify Restore

```bash
# Connect to database
docker exec -it postgres_db psql -U $POSTGRES_USER -d $POSTGRES_DB

# Check tables
\dt

# Check record counts
SELECT COUNT(*) FROM your_table_name;

# Exit
\q
```

---

## 🔍 Monitoring and Logs

### View Backup Logs

```bash
# View recent backup logs
tail -f /Users/nima/Projects/pilito/backup/backup.log

# View last 100 lines
tail -n 100 /Users/nima/Projects/pilito/backup/backup.log

# Search for errors
grep ERROR /Users/nima/Projects/pilito/backup/backup.log
```

### Check Local Backups

```bash
# List local backups
ls -lh /Users/nima/Projects/pilito/db_backups/

# Check disk usage
du -sh /Users/nima/Projects/pilito/db_backups/
```

### Verify Backblaze B2 Upload

```bash
# List backups on B2
aws --endpoint-url https://s3.us-west-004.backblazeb2.com \
    s3 ls s3://pilito/ --human-readable

# Get total size of backups
aws --endpoint-url https://s3.us-west-004.backblazeb2.com \
    s3 ls s3://pilito/ --recursive --human-readable --summarize
```

---

## 🛡️ Retention Policy

### Local Backups
- **Retention:** 7 days
- **Location:** `./db_backups/`
- **Cleanup:** Automatic (runs with each backup)

### Backblaze B2 Backups
- **Retention:** Unlimited (manual deletion required)
- **Location:** `s3://pilito/`
- **Cleanup:** Manual or configure lifecycle rules in B2

#### Manual B2 Cleanup Example:

Delete backups older than 30 days:
```bash
# List old backups
aws --endpoint-url https://s3.us-west-004.backblazeb2.com \
    s3 ls s3://pilito/ | grep postgres_backup

# Delete specific backup
aws --endpoint-url https://s3.us-west-004.backblazeb2.com \
    s3 rm s3://pilito/postgres_backup_2025-11-01_02-00.sql.gz
```

---

## 🚨 Troubleshooting

### Issue: Backup fails with "connection refused"

**Solution:** Ensure PostgreSQL container is running:
```bash
docker ps | grep postgres_db
```

### Issue: Upload fails to Backblaze B2

**Solution:** Verify credentials:
```bash
# Test AWS CLI connection
aws --endpoint-url https://s3.us-west-004.backblazeb2.com \
    s3 ls s3://pilito/
```

### Issue: "Permission denied" on backup.sh

**Solution:** Make script executable:
```bash
chmod +x /Users/nima/Projects/pilito/backup/backup.sh
```

### Issue: Cron job not running

**Solution:** Check cron logs:
```bash
# macOS
tail -f /var/log/system.log | grep cron

# Linux
tail -f /var/log/syslog | grep CRON
```

### Issue: Backup file is empty

**Solution:** Check PostgreSQL credentials in `.env` file and ensure database has data:
```bash
docker exec -it postgres_db psql -U $POSTGRES_USER -d $POSTGRES_DB -c "\dt"
```

---

## 🧪 Testing the Backup System

### Test 1: Manual Backup
```bash
cd /Users/nima/Projects/pilito
docker compose -f docker-compose.backup.yml up --abort-on-container-exit
```

### Test 2: Verify Local Backup
```bash
ls -lh db_backups/
```

### Test 3: Verify B2 Upload
```bash
aws --endpoint-url https://s3.us-west-004.backblazeb2.com s3 ls s3://pilito/
```

### Test 4: Test Restore (on test database)
```bash
# Download latest backup
aws --endpoint-url https://s3.us-west-004.backblazeb2.com \
    s3 cp s3://pilito/postgres_backup_2025-12-13_02-00.sql.gz ./test_restore.sql.gz

# Restore to test database
gunzip < test_restore.sql.gz | docker exec -i postgres_db psql -U $POSTGRES_USER -d test_db
```

---

## 📊 Backup Size Estimates

Typical PostgreSQL database sizes (compressed):

| Database Size | Compressed Backup | Compression Ratio |
|--------------|-------------------|-------------------|
| 100 MB | ~10-20 MB | ~90% |
| 1 GB | ~100-200 MB | ~90% |
| 10 GB | ~1-2 GB | ~90% |
| 100 GB | ~10-20 GB | ~90% |

---

## 💰 Backblaze B2 Costs

**Current Pricing (as of 2025):**
- Storage: $0.005/GB per month ($5/TB)
- Download: $0.01/GB
- Free: 10 GB storage, 1 GB daily download

**Example:** 10 GB of backups per month:
- Storage cost: 10 GB × $0.005 = **$0.05/month**
- Very cost-effective! 💰

---

## 🔐 Security Best Practices

1. **Never commit credentials to Git:**
   - Keep `.env` in `.gitignore`
   - Use environment variables for secrets

2. **Restrict B2 Key Permissions:**
   - Create application keys with minimum required permissions
   - Use separate keys for backup and restore

3. **Encrypt sensitive backups:**
   - Consider encrypting backups before upload for additional security
   - Use `gpg` for encryption:
     ```bash
     gpg -c backup.sql.gz
     ```

4. **Regular restore testing:**
   - Test restore process monthly
   - Verify data integrity

---

## 📞 Support

For issues or questions:
1. Check the troubleshooting section above
2. Review backup logs: `/Users/nima/Projects/pilito/backup/backup.log`
3. Verify environment variables in `.env`
4. Test AWS CLI connection to Backblaze B2

---

## 📝 Changelog

### Version 1.0 (2025-12-13)
- Initial backup system
- Daily automated backups
- Backblaze B2 integration
- 7-day local retention
- Comprehensive logging

---

**✨ Your database is now protected with automated backups! ✨**

