#!/bin/bash
# Deployment script for keywords migration
# Run this on the server after pulling the latest code

set -e  # Exit on error

echo "🚀 Starting Keywords Migration Deployment..."
echo "=========================================="

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Step 1: Pull latest code (if using git)
echo -e "${YELLOW}Step 1: Pulling latest code...${NC}"
# Uncomment if you need to pull:
# git pull origin main

# Step 2: Activate virtual environment (if using)
# echo -e "${YELLOW}Step 2: Activating virtual environment...${NC}"
# source venv/bin/activate  # Adjust path as needed

# Step 3: Run migrations (if any)
echo -e "${YELLOW}Step 2: Running migrations...${NC}"
cd src
python manage.py migrate --noinput

# Step 4: Seed default keywords
echo -e "${YELLOW}Step 3: Seeding default keywords to database...${NC}"
python manage.py seed_default_keywords

# Step 5: Verify keywords
echo -e "${YELLOW}Step 4: Verifying keywords...${NC}"
python manage.py test_keywords

# Step 6: Collect static files (if needed)
echo -e "${YELLOW}Step 5: Collecting static files...${NC}"
python manage.py collectstatic --noinput

# Step 7: Restart services (adjust based on your setup)
echo -e "${YELLOW}Step 6: Restarting services...${NC}"
# For Docker:
# docker-compose restart web celery

# For systemd:
# sudo systemctl restart gunicorn
# sudo systemctl restart celery

# For supervisor:
# sudo supervisorctl restart all

echo -e "${GREEN}✅ Deployment completed successfully!${NC}"
echo ""
echo "📋 Next steps:"
echo "  1. Check logs to ensure everything is working"
echo "  2. Test a query to verify keywords are loaded from database"
echo "  3. Check admin panel to see keywords"
echo ""
echo "🔍 To verify keywords are working:"
echo "  python manage.py test_keywords"

