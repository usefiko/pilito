#!/bin/bash

# DNS Fix Deployment Script
# Adds Google DNS to Docker containers to fix SMTP and OAuth timeouts

set -e  # Exit on error

echo "==========================================="
echo "🚀 Deploying DNS Fix for Network Issues"
echo "==========================================="
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if docker-compose is available
if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}❌ docker-compose not found${NC}"
    exit 1
fi

echo -e "${YELLOW}📋 What this fix does:${NC}"
echo "  • Adds Google DNS (8.8.8.8, 8.8.4.4, 1.1.1.1) to containers"
echo "  • Fixes SMTP timeout to smtp.c1.liara.email"
echo "  • Fixes Google OAuth certificate fetching"
echo "  • Applies to: web, celery_worker, celery_ai"
echo ""

# Backup current docker-compose.yml
echo -e "${YELLOW}📦 Creating backup...${NC}"
cp docker-compose.yml docker-compose.yml.backup.$(date +%Y%m%d_%H%M%S)
echo -e "${GREEN}✓ Backup created${NC}"
echo ""

# Show what changed
echo -e "${YELLOW}📝 Changes made to docker-compose.yml:${NC}"
echo "  web service:"
echo "    + dns:"
echo "      + - 8.8.8.8"
echo "      + - 8.8.4.4"
echo "      + - 1.1.1.1"
echo ""
echo "  celery_worker service:"
echo "    + dns:"
echo "      + - 8.8.8.8"
echo "      + - 8.8.4.4"
echo "      + - 1.1.1.1"
echo ""
echo "  celery_ai service:"
echo "    + dns:"
echo "      + - 8.8.8.8"
echo "      + - 8.8.4.4"
echo "      + - 1.1.1.1"
echo ""

# Ask for confirmation
read -p "🤔 Deploy these changes? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${RED}❌ Deployment cancelled${NC}"
    exit 1
fi

echo ""
echo -e "${YELLOW}🔄 Restarting services...${NC}"
echo "This will:"
echo "  1. Stop current containers"
echo "  2. Recreate with new DNS settings"
echo "  3. Start all services"
echo ""

# Restart services with new configuration
docker-compose down
echo -e "${GREEN}✓ Services stopped${NC}"

docker-compose up -d
echo -e "${GREEN}✓ Services started with new DNS configuration${NC}"
echo ""

# Wait for services to be ready
echo -e "${YELLOW}⏳ Waiting for services to be ready...${NC}"
sleep 5

# Check service status
echo ""
echo -e "${YELLOW}📊 Service Status:${NC}"
docker-compose ps

echo ""
echo -e "${YELLOW}🧪 Testing DNS Resolution...${NC}"

# Test DNS from web container
echo "Testing from django_app container..."
if docker exec django_app nslookup smtp.c1.liara.email > /dev/null 2>&1; then
    echo -e "${GREEN}✓ DNS resolution working${NC}"
else
    echo -e "${RED}✗ DNS resolution failed${NC}"
fi

# Test SMTP connectivity
echo "Testing SMTP connectivity..."
if timeout 5 docker exec django_app nc -zv smtp.c1.liara.email 587 2>&1 | grep -q succeeded; then
    echo -e "${GREEN}✓ SMTP connection successful${NC}"
else
    echo -e "${YELLOW}⚠ SMTP connection test inconclusive (nc may not be installed)${NC}"
fi

# Test Google API connectivity
echo "Testing Google API connectivity..."
if docker exec django_app curl -s --max-time 5 https://www.googleapis.com > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Google API reachable${NC}"
else
    echo -e "${YELLOW}⚠ Google API connection test inconclusive${NC}"
fi

echo ""
echo "==========================================="
echo -e "${GREEN}✅ Deployment Complete!${NC}"
echo "==========================================="
echo ""
echo "📝 Next steps:"
echo "  1. Test registration: Should send email without timeout"
echo "  2. Test Google OAuth: Should work without certificate errors"
echo "  3. Monitor logs: docker logs django_app -f"
echo ""
echo "📊 Monitor email sending:"
echo "  docker logs django_app -f | grep -i email"
echo ""
echo "📊 Monitor Celery worker:"
echo "  docker logs celery_worker -f | grep -i email"
echo ""
echo "🔙 To rollback (if needed):"
echo "  docker-compose down"
echo "  cp docker-compose.yml.backup.[timestamp] docker-compose.yml"
echo "  docker-compose up -d"
echo ""

