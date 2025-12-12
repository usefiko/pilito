#!/bin/bash

###############################################################################
# Test Backup System
# 
# This script tests the backup system to ensure everything is configured correctly
###############################################################################

set -e

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Testing PostgreSQL Backup System${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Test 1: Check if .env file exists
echo -e "${YELLOW}[Test 1/7] Checking .env file...${NC}"
if [ -f .env ]; then
    echo -e "${GREEN}✅ .env file exists${NC}"
    
    # Load environment variables
    export $(cat .env | grep -v '^#' | xargs) 2>/dev/null
    
    # Check required variables
    if [ -n "$POSTGRES_USER" ] && [ -n "$POSTGRES_PASSWORD" ] && [ -n "$POSTGRES_DB" ]; then
        echo -e "${GREEN}✅ PostgreSQL credentials found${NC}"
    else
        echo -e "${RED}❌ PostgreSQL credentials missing${NC}"
        exit 1
    fi
    
    if [ -n "$B2_APPLICATION_KEY" ]; then
        echo -e "${GREEN}✅ Backblaze B2 credentials found${NC}"
    else
        echo -e "${YELLOW}⚠️  B2_APPLICATION_KEY not found in .env${NC}"
    fi
else
    echo -e "${RED}❌ .env file not found${NC}"
    exit 1
fi
echo ""

# Test 2: Check if backup script exists
echo -e "${YELLOW}[Test 2/7] Checking backup script...${NC}"
if [ -f backup/backup.sh ]; then
    echo -e "${GREEN}✅ backup.sh exists${NC}"
    if [ -x backup/backup.sh ]; then
        echo -e "${GREEN}✅ backup.sh is executable${NC}"
    else
        echo -e "${RED}❌ backup.sh is not executable${NC}"
        echo "Run: chmod +x backup/backup.sh"
        exit 1
    fi
else
    echo -e "${RED}❌ backup.sh not found${NC}"
    exit 1
fi
echo ""

# Test 3: Check if docker-compose.backup.yml exists
echo -e "${YELLOW}[Test 3/7] Checking docker-compose.backup.yml...${NC}"
if [ -f docker-compose.backup.yml ]; then
    echo -e "${GREEN}✅ docker-compose.backup.yml exists${NC}"
else
    echo -e "${RED}❌ docker-compose.backup.yml not found${NC}"
    exit 1
fi
echo ""

# Test 4: Check if PostgreSQL container is running
echo -e "${YELLOW}[Test 4/7] Checking PostgreSQL container...${NC}"
if docker ps | grep -q postgres_db; then
    echo -e "${GREEN}✅ PostgreSQL container is running${NC}"
else
    echo -e "${RED}❌ PostgreSQL container is not running${NC}"
    echo "Start it with: docker compose up -d db"
    exit 1
fi
echo ""

# Test 5: Check PostgreSQL connection
echo -e "${YELLOW}[Test 5/7] Testing PostgreSQL connection...${NC}"
if docker exec postgres_db psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "SELECT 1;" > /dev/null 2>&1; then
    echo -e "${GREEN}✅ PostgreSQL connection successful${NC}"
else
    echo -e "${RED}❌ Cannot connect to PostgreSQL${NC}"
    exit 1
fi
echo ""

# Test 6: Check AWS CLI (optional)
echo -e "${YELLOW}[Test 6/7] Checking AWS CLI...${NC}"
if command -v aws &> /dev/null; then
    echo -e "${GREEN}✅ AWS CLI is installed${NC}"
    
    # Test B2 connection
    echo -e "${YELLOW}Testing Backblaze B2 connection...${NC}"
    if aws --endpoint-url https://s3.us-west-004.backblazeb2.com s3 ls s3://pilito/ > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Backblaze B2 connection successful${NC}"
    else
        echo -e "${YELLOW}⚠️  Cannot connect to Backblaze B2${NC}"
        echo "Configure AWS CLI with: aws configure"
    fi
else
    echo -e "${YELLOW}⚠️  AWS CLI not installed (optional for local testing)${NC}"
    echo "The backup container will install it automatically"
fi
echo ""

# Test 7: Check backup directory
echo -e "${YELLOW}[Test 7/7] Checking backup directory...${NC}"
if [ -d db_backups ]; then
    echo -e "${GREEN}✅ db_backups directory exists${NC}"
    BACKUP_SIZE=$(du -sh db_backups 2>/dev/null | cut -f1)
    echo -e "${BLUE}   Current size: ${BACKUP_SIZE}${NC}"
else
    echo -e "${YELLOW}⚠️  db_backups directory doesn't exist (will be created automatically)${NC}"
    mkdir -p db_backups
    echo -e "${GREEN}✅ Created db_backups directory${NC}"
fi
echo ""

# Summary
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Test Summary${NC}"
echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}All critical tests passed!${NC}"
echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo "1. Run a test backup:"
echo "   docker compose -f docker-compose.backup.yml up --abort-on-container-exit"
echo ""
echo "2. Set up cron job for daily backups:"
echo "   crontab -e"
echo "   Add: 0 2 * * * cd $(pwd) && docker compose -f docker-compose.backup.yml up --abort-on-container-exit >> backup/backup.log 2>&1"
echo ""
echo "3. Monitor backups:"
echo "   tail -f backup/backup.log"
echo ""
echo -e "${GREEN}Your backup system is ready! 🎉${NC}"

exit 0

