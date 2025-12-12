#!/bin/bash

###############################################################################
# PostgreSQL Restore Script from Backblaze B2
# 
# This script helps you restore a PostgreSQL backup from Backblaze B2
###############################################################################

set -e

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
B2_ENDPOINT="https://s3.us-west-004.backblazeb2.com"
B2_BUCKET="pilito"
DOWNLOAD_DIR="./restore_temp"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}PostgreSQL Restore from Backblaze B2${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Check if AWS CLI is installed
if ! command -v aws &> /dev/null; then
    echo -e "${RED}ERROR: AWS CLI is not installed.${NC}"
    echo "Install it with: brew install awscli"
    exit 1
fi

# Load environment variables
if [ -f .env ]; then
    echo -e "${GREEN}Loading environment variables...${NC}"
    export $(cat .env | grep -v '^#' | xargs)
else
    echo -e "${RED}ERROR: .env file not found${NC}"
    exit 1
fi

# Validate credentials
if [ -z "$POSTGRES_USER" ] || [ -z "$POSTGRES_PASSWORD" ] || [ -z "$POSTGRES_DB" ]; then
    echo -e "${RED}ERROR: PostgreSQL credentials missing in .env${NC}"
    exit 1
fi

# List available backups
echo -e "${YELLOW}Fetching available backups from Backblaze B2...${NC}"
echo ""

aws --endpoint-url "$B2_ENDPOINT" s3 ls "s3://${B2_BUCKET}/" | grep postgres_backup

echo ""
echo -e "${YELLOW}Enter the backup filename to restore:${NC}"
read -r BACKUP_FILE

if [ -z "$BACKUP_FILE" ]; then
    echo -e "${RED}ERROR: No filename provided${NC}"
    exit 1
fi

# Create download directory
mkdir -p "$DOWNLOAD_DIR"

# Download backup
echo ""
echo -e "${GREEN}Downloading backup: ${BACKUP_FILE}${NC}"
aws --endpoint-url "$B2_ENDPOINT" s3 cp "s3://${B2_BUCKET}/${BACKUP_FILE}" "${DOWNLOAD_DIR}/${BACKUP_FILE}"

# Verify download
if [ ! -f "${DOWNLOAD_DIR}/${BACKUP_FILE}" ]; then
    echo -e "${RED}ERROR: Download failed${NC}"
    exit 1
fi

echo -e "${GREEN}Download completed successfully${NC}"

# Ask for confirmation
echo ""
echo -e "${RED}⚠️  WARNING: This will restore the database: ${POSTGRES_DB}${NC}"
echo -e "${RED}⚠️  All current data will be replaced!${NC}"
echo ""
echo -e "${YELLOW}Do you want to continue? (yes/no)${NC}"
read -r CONFIRM

if [ "$CONFIRM" != "yes" ]; then
    echo -e "${YELLOW}Restore cancelled${NC}"
    rm -rf "$DOWNLOAD_DIR"
    exit 0
fi

# Check if PostgreSQL container is running
if ! docker ps | grep -q postgres_db; then
    echo -e "${RED}ERROR: PostgreSQL container (postgres_db) is not running${NC}"
    exit 1
fi

# Restore database
echo ""
echo -e "${GREEN}Restoring database...${NC}"

export PGPASSWORD="$POSTGRES_PASSWORD"

if gunzip < "${DOWNLOAD_DIR}/${BACKUP_FILE}" | docker exec -i postgres_db psql -U "$POSTGRES_USER" -d "$POSTGRES_DB"; then
    echo ""
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}✅ Database restored successfully!${NC}"
    echo -e "${GREEN}========================================${NC}"
else
    echo -e "${RED}ERROR: Restore failed${NC}"
    exit 1
fi

# Cleanup
echo ""
echo -e "${YELLOW}Cleaning up temporary files...${NC}"
rm -rf "$DOWNLOAD_DIR"
echo -e "${GREEN}Cleanup completed${NC}"

echo ""
echo -e "${BLUE}Restore Details:${NC}"
echo -e "  Backup File: ${BACKUP_FILE}"
echo -e "  Database: ${POSTGRES_DB}"
echo -e "  User: ${POSTGRES_USER}"

exit 0

