# 🚀 Quick Setup Guide - PostgreSQL Backup System

## ⚡ Quick Start (5 minutes)

### Step 1: Prepare Your Environment Variables

Add the Backblaze Application Key to your existing `.env` file:

```bash
# Add this line to your .env file
B2_APPLICATION_KEY=your_actual_backblaze_application_key_secret
```

**Note:** Replace `your_actual_backblaze_application_key_secret` with your real Backblaze Application Key.

Your existing `.env` should already have:
- `POSTGRES_USER`
- `POSTGRES_PASSWORD`
- `POSTGRES_DB`

---

### Step 2: Create Backup Directory

The backup script will create this automatically, but you can do it manually:

```bash
mkdir -p /Users/nima/Projects/pilito/db_backups
```

---

### Step 3: Test Manual Backup

Run your first backup:

```bash
cd /Users/nima/Projects/pilito
docker compose -f docker-compose.backup.yml up --abort-on-container-exit
```

You should see:
- ✅ AWS CLI installation
- ✅ PostgreSQL dump creation
- ✅ Gzip compression
- ✅ Upload to Backblaze B2
- ✅ Verification

---

### Step 4: Set Up Automated Daily Backups

#### Open crontab:
```bash
crontab -e
```

#### Add this line (runs daily at 2:00 AM):
```cron
0 2 * * * cd /Users/nima/Projects/pilito && docker compose -f docker-compose.backup.yml up --abort-on-container-exit >> /Users/nima/Projects/pilito/backup/backup.log 2>&1
```

#### Save and verify:
```bash
crontab -l
```

---

### Step 5: Verify Everything Works

#### Check local backups:
```bash
ls -lh /Users/nima/Projects/pilito/db_backups/
```

#### Check Backblaze B2:
```bash
# Configure AWS CLI once
aws configure set aws_access_key_id 61242eff92a8
aws configure set aws_secret_access_key YOUR_B2_APPLICATION_KEY
aws configure set region us-west-004

# List backups on B2
aws --endpoint-url https://s3.us-west-004.backblazeb2.com s3 ls s3://pilito/
```

---

## 🎯 What You Get

✅ **Automated Daily Backups** at 2:00 AM  
✅ **Cloud Storage** on Backblaze B2  
✅ **Local Copies** for 7 days  
✅ **Compressed Backups** (90% size reduction)  
✅ **Detailed Logs** for monitoring  
✅ **Production-Ready** error handling  

---

## 📋 Quick Commands Cheat Sheet

```bash
# Manual backup
cd /Users/nima/Projects/pilito && docker compose -f docker-compose.backup.yml up --abort-on-container-exit

# View logs
tail -f /Users/nima/Projects/pilito/backup/backup.log

# List local backups
ls -lh /Users/nima/Projects/pilito/db_backups/

# List B2 backups
aws --endpoint-url https://s3.us-west-004.backblazeb2.com s3 ls s3://pilito/

# Download backup from B2
aws --endpoint-url https://s3.us-west-004.backblazeb2.com s3 cp s3://pilito/FILENAME ./FILENAME

# Restore backup
gunzip < FILENAME | docker exec -i postgres_db psql -U $POSTGRES_USER -d $POSTGRES_DB

# Check cron jobs
crontab -l

# Test database connection
docker exec -it postgres_db psql -U $POSTGRES_USER -d $POSTGRES_DB
```

---

## 🔧 Troubleshooting

### Backup fails?
1. Check if PostgreSQL is running: `docker ps | grep postgres`
2. Verify credentials in `.env` file
3. Check logs: `tail -f backup/backup.log`

### Upload fails?
1. Verify B2 credentials: `aws --endpoint-url https://s3.us-west-004.backblazeb2.com s3 ls s3://pilito/`
2. Check internet connection
3. Verify B2 Application Key has write permissions

### Cron not running?
1. Check cron syntax: `crontab -l`
2. Ensure full paths are used
3. Check system logs: `tail -f /var/log/system.log | grep cron`

---

## 📚 Full Documentation

See [backup/README.md](./README.md) for complete documentation including:
- Detailed restore instructions
- Advanced configuration
- Security best practices
- Cost estimates
- Complete troubleshooting guide

---

**🎉 You're all set! Your database is now protected with automated backups.**

