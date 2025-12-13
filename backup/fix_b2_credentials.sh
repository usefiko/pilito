#!/bin/bash

###############################################################################
# Fix Backblaze B2 Credentials
# 
# This script helps you configure the correct Backblaze B2 credentials
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
echo -e "${BLUE}║     Fix Backblaze B2 Credentials Configuration                  ║${NC}"
echo -e "${BLUE}║                                                                  ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════════════════╝${NC}"
echo ""

echo -e "${YELLOW}You need TWO credentials from Backblaze B2:${NC}"
echo ""
echo -e "${GREEN}1. keyID${NC} (25 characters, like: 0012a3456789b0c0000000001)"
echo -e "${GREEN}2. applicationKey${NC} (the secret key, longer string)"
echo ""
echo -e "${YELLOW}To find these:${NC}"
echo "  1. Log into Backblaze B2: https://secure.backblaze.com/user_signin.htm"
echo "  2. Go to 'App Keys' in the sidebar"
echo "  3. Find your 'Master Application Key' or create a new one"
echo ""

# Get keyID
echo -e "${YELLOW}Enter your Backblaze B2 keyID (25 characters):${NC}"
read -r B2_KEY_ID

# Validate keyID length
if [ ${#B2_KEY_ID} -lt 20 ]; then
    echo -e "${RED}ERROR: keyID seems too short (should be ~25 characters)${NC}"
    echo -e "${YELLOW}Please make sure you copied the FULL keyID from Backblaze${NC}"
    exit 1
fi

echo -e "${GREEN}✅ keyID: $B2_KEY_ID${NC}"
echo ""

# Get applicationKey
echo -e "${YELLOW}Enter your Backblaze B2 applicationKey (secret):${NC}"
read -r B2_APP_KEY

# Validate applicationKey length
if [ ${#B2_APP_KEY} -lt 20 ]; then
    echo -e "${RED}ERROR: applicationKey seems too short${NC}"
    echo -e "${YELLOW}Please make sure you copied the FULL applicationKey from Backblaze${NC}"
    exit 1
fi

echo -e "${GREEN}✅ applicationKey: ${B2_APP_KEY:0:10}...${B2_APP_KEY: -4} (hidden)${NC}"
echo ""

# Update docker-compose.backup.yml
echo -e "${YELLOW}Updating docker-compose.backup.yml...${NC}"

if [ ! -f docker-compose.backup.yml ]; then
    echo -e "${RED}ERROR: docker-compose.backup.yml not found${NC}"
    exit 1
fi

# Backup original file
cp docker-compose.backup.yml docker-compose.backup.yml.bak
echo -e "${GREEN}✅ Backed up original to docker-compose.backup.yml.bak${NC}"

# Update the keyID in docker-compose.backup.yml
sed -i "s/- AWS_ACCESS_KEY_ID=.*/- AWS_ACCESS_KEY_ID=$B2_KEY_ID/" docker-compose.backup.yml
echo -e "${GREEN}✅ Updated AWS_ACCESS_KEY_ID in docker-compose.backup.yml${NC}"

# Update .env file
echo -e "${YELLOW}Updating .env file...${NC}"

if [ ! -f .env ]; then
    echo -e "${RED}ERROR: .env file not found${NC}"
    exit 1
fi

# Check if B2_APPLICATION_KEY exists
if grep -q "B2_APPLICATION_KEY=" .env; then
    # Update existing
    sed -i.bak "s/B2_APPLICATION_KEY=.*/B2_APPLICATION_KEY=$B2_APP_KEY/" .env
    echo -e "${GREEN}✅ Updated B2_APPLICATION_KEY in .env${NC}"
else
    # Add new
    echo "" >> .env
    echo "# Backblaze B2 Configuration" >> .env
    echo "B2_APPLICATION_KEY=$B2_APP_KEY" >> .env
    echo -e "${GREEN}✅ Added B2_APPLICATION_KEY to .env${NC}"
fi

echo ""
echo -e "${BLUE}╔══════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║                                                                  ║${NC}"
echo -e "${BLUE}║                    ✅ Configuration Updated!                      ║${NC}"
echo -e "${BLUE}║                                                                  ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════════════════╝${NC}"
echo ""

echo -e "${GREEN}Updated files:${NC}"
echo "  ✅ docker-compose.backup.yml (keyID updated)"
echo "  ✅ .env (applicationKey updated)"
echo ""

echo -e "${YELLOW}Now test the backup again:${NC}"
echo "  docker compose -f docker-compose.backup.yml up --abort-on-container-exit"
echo ""

exit 0





