#!/bin/bash

###############################################################################
# PostgreSQL Backup Script with Backblaze B2 Upload
# 
# This script:
# - Creates a PostgreSQL dump
# - Compresses it with gzip
# - Uploads to Backblaze B2 using S3-compatible API
# - Cleans up old local backups (older than 7 days)
###############################################################################

set -e  # Exit on error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR:${NC} $1"
}

warning() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING:${NC} $1"
}

###############################################################################
# Validate Required Environment Variables
###############################################################################
log "Starting PostgreSQL backup process..."

if [ -z "$POSTGRES_USER" ] || [ -z "$POSTGRES_PASSWORD" ] || [ -z "$POSTGRES_DB" ]; then
    error "PostgreSQL credentials are missing. Please set POSTGRES_USER, POSTGRES_PASSWORD, and POSTGRES_DB."
    exit 1
fi

if [ -z "$AWS_ACCESS_KEY_ID" ] || [ -z "$AWS_SECRET_ACCESS_KEY" ]; then
    error "Backblaze B2 credentials are missing. Please set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY."
    exit 1
fi

if [ -z "$B2_BUCKET" ]; then
    error "B2_BUCKET is not set. Please specify the Backblaze bucket name."
    exit 1
fi

if [ -z "$AWS_DEFAULT_REGION" ]; then
    AWS_DEFAULT_REGION="us-west-004"
    warning "AWS_DEFAULT_REGION not set, using default: $AWS_DEFAULT_REGION"
fi

log "Environment variables validated successfully."

###############################################################################
# Configuration
###############################################################################
BACKUP_DIR="/backups"
TIMESTAMP=$(date +'%Y-%m-%d_%H-%M')
BACKUP_FILE="postgres_backup_${TIMESTAMP}.sql.gz"
BACKUP_PATH="${BACKUP_DIR}/${BACKUP_FILE}"
B2_ENDPOINT="https://s3.${AWS_DEFAULT_REGION}.backblazeb2.com"
RETENTION_DAYS=7

# PostgreSQL connection details
PGHOST=${PGHOST:-db}
PGPORT=${PGPORT:-5432}

log "Configuration:"
log "  - Backup Directory: $BACKUP_DIR"
log "  - Backup File: $BACKUP_FILE"
log "  - B2 Bucket: $B2_BUCKET"
log "  - B2 Endpoint: $B2_ENDPOINT"
log "  - Retention Period: $RETENTION_DAYS days"
log "  - PostgreSQL Host: $PGHOST"
log "  - PostgreSQL Database: $POSTGRES_DB"

###############################################################################
# Create Backup Directory
###############################################################################
if [ ! -d "$BACKUP_DIR" ]; then
    log "Creating backup directory: $BACKUP_DIR"
    mkdir -p "$BACKUP_DIR"
fi

###############################################################################
# Perform PostgreSQL Backup
###############################################################################
log "Starting PostgreSQL dump..."

export PGPASSWORD="$POSTGRES_PASSWORD"

if pg_dump -h "$PGHOST" -p "$PGPORT" -U "$POSTGRES_USER" -d "$POSTGRES_DB" | gzip > "$BACKUP_PATH"; then
    log "PostgreSQL dump completed successfully."
    
    # Get file size
    BACKUP_SIZE=$(du -h "$BACKUP_PATH" | cut -f1)
    log "Backup file size: $BACKUP_SIZE"
else
    error "PostgreSQL dump failed!"
    exit 1
fi

unset PGPASSWORD

###############################################################################
# Verify Backup File
###############################################################################
if [ ! -f "$BACKUP_PATH" ]; then
    error "Backup file not found: $BACKUP_PATH"
    exit 1
fi

if [ ! -s "$BACKUP_PATH" ]; then
    error "Backup file is empty: $BACKUP_PATH"
    exit 1
fi

log "Backup file verified successfully."

###############################################################################
# Upload to Backblaze B2
###############################################################################
log "Uploading backup to Backblaze B2..."
log "  Endpoint: $B2_ENDPOINT"
log "  Bucket: s3://$B2_BUCKET/"
log "  File: $BACKUP_FILE"

if aws --endpoint-url "$B2_ENDPOINT" s3 cp "$BACKUP_PATH" "s3://${B2_BUCKET}/${BACKUP_FILE}" --no-progress; then
    log "Backup uploaded successfully to Backblaze B2!"
else
    error "Failed to upload backup to Backblaze B2!"
    exit 1
fi

###############################################################################
# Verify Upload
###############################################################################
log "Verifying upload on Backblaze B2..."

if aws --endpoint-url "$B2_ENDPOINT" s3 ls "s3://${B2_BUCKET}/${BACKUP_FILE}" > /dev/null 2>&1; then
    log "Upload verified successfully on Backblaze B2."
else
    warning "Could not verify upload on Backblaze B2. File might still be uploading."
fi

###############################################################################
# Clean Up Old Local Backups
###############################################################################
log "Cleaning up local backups older than $RETENTION_DAYS days..."

DELETED_COUNT=0
if [ -d "$BACKUP_DIR" ]; then
    while IFS= read -r -d '' old_backup; do
        log "Deleting old backup: $(basename "$old_backup")"
        rm -f "$old_backup"
        ((DELETED_COUNT++))
    done < <(find "$BACKUP_DIR" -name "postgres_backup_*.sql.gz" -type f -mtime +$RETENTION_DAYS -print0)
    
    if [ $DELETED_COUNT -eq 0 ]; then
        log "No old backups found to delete."
    else
        log "Deleted $DELETED_COUNT old backup(s)."
    fi
else
    warning "Backup directory does not exist: $BACKUP_DIR"
fi

###############################################################################
# Summary
###############################################################################
log "=========================================="
log "Backup Process Completed Successfully!"
log "=========================================="
log "Backup Details:"
log "  - Local File: $BACKUP_PATH"
log "  - Remote Location: s3://${B2_BUCKET}/${BACKUP_FILE}"
log "  - File Size: $BACKUP_SIZE"
log "  - Timestamp: $TIMESTAMP"
log "=========================================="

exit 0

