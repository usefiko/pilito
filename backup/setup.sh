#!/bin/bash

###############################################################################
# Setup Script for PostgreSQL Backup System
# Run this once to set up everything automatically
###############################################################################

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}╔══════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║                                                                  ║${NC}"
echo -e "${BLUE}║        PostgreSQL Backup System - Automated Setup               ║${NC}"
echo -e "${BLUE}║                                                                  ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo -e "${RED}ERROR: .env file not found${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Found .env file${NC}"
echo ""

# Check if B2_APPLICATION_KEY is already set
if grep -q "B2_APPLICATION_KEY=" .env; then
    echo -e "${YELLOW}⚠️  B2_APPLICATION_KEY already exists in .env${NC}"
    echo -e "${YELLOW}Do you want to update it? (yes/no)${NC}"
    read -r UPDATE
    if [ "$UPDATE" != "yes" ]; then
        echo -e "${BLUE}Skipping B2_APPLICATION_KEY update${NC}"
    else
        echo -e "${YELLOW}Enter your Backblaze B2 Application Key (secret):${NC}"
        read -r B2_KEY
        # Remove old key
        sed -i.bak '/B2_APPLICATION_KEY=/d' .env
        # Add new key
        echo "B2_APPLICATION_KEY=$B2_KEY" >> .env
        echo -e "${GREEN}✅ B2_APPLICATION_KEY updated${NC}"
    fi
else
    echo -e "${YELLOW}Enter your Backblaze B2 Application Key (secret):${NC}"
    read -r B2_KEY
    echo "" >> .env
    echo "# Backblaze B2 Configuration" >> .env
    echo "B2_APPLICATION_KEY=$B2_KEY" >> .env
    echo -e "${GREEN}✅ B2_APPLICATION_KEY added to .env${NC}"
fi

echo ""

# Create backup directory
echo -e "${YELLOW}Creating backup directory...${NC}"
mkdir -p db_backups
chmod 755 db_backups
echo -e "${GREEN}✅ Created db_backups directory${NC}"
echo ""

# Make scripts executable
echo -e "${YELLOW}Making scripts executable...${NC}"
chmod +x backup/backup.sh
chmod +x backup/restore.sh
chmod +x backup/test_backup.sh
chmod +x backup/setup.sh
echo -e "${GREEN}✅ All scripts are now executable${NC}"
echo ""

# Test system
echo -e "${YELLOW}Testing backup system...${NC}"
echo ""
./backup/test_backup.sh

echo ""
echo -e "${BLUE}╔══════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║                                                                  ║${NC}"
echo -e "${BLUE}║                    Setup Complete! 🎉                            ║${NC}"
echo -e "${BLUE}║                                                                  ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${GREEN}Next steps:${NC}"
echo ""
echo -e "${YELLOW}1. Run a test backup:${NC}"
echo "   docker compose -f docker-compose.backup.yml up --abort-on-container-exit"
echo ""
echo -e "${YELLOW}2. Set up cron job for daily backups:${NC}"
echo "   crontab -e"
echo "   Add: 0 2 * * * cd $(pwd) && docker compose -f docker-compose.backup.yml up --abort-on-container-exit >> backup/backup.log 2>&1"
echo ""
echo -e "${YELLOW}3. Monitor backups:${NC}"
echo "   tail -f backup/backup.log"
echo ""
echo -e "${GREEN}Your database is now protected! 🛡️${NC}"

exit 0

