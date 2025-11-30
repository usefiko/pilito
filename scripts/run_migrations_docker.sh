#!/bin/bash

###############################################################################
# Run Django Migrations in Docker Container
# This script runs migrations safely before deployment
###############################################################################

set -e  # Exit on error

echo "======================================================================"
echo "🔄 Django Migration Runner"
echo "======================================================================"
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Navigate to project directory
cd "$(dirname "$0")/.."
PROJECT_DIR=$(pwd)
echo "📁 Project directory: $PROJECT_DIR"
echo ""

# Step 1: Ensure database is running
echo -e "${YELLOW}🗄️ Step 1: Ensuring database is running...${NC}"
docker compose up -d db
sleep 5

# Check if database is healthy
if docker compose ps db | grep -q "Up"; then
    echo -e "${GREEN}✅ Database is running${NC}"
else
    echo -e "${RED}❌ Database failed to start${NC}"
    docker compose logs db
    exit 1
fi
echo ""

# Step 2: Build web image if needed
echo -e "${YELLOW}🔨 Step 2: Building web image (if needed)...${NC}"
if docker compose build web; then
    echo -e "${GREEN}✅ Web image built successfully${NC}"
else
    echo -e "${RED}❌ Failed to build web image${NC}"
    exit 1
fi
echo ""

# Step 3: Check for pending migrations
echo -e "${YELLOW}📋 Step 3: Checking for pending migrations...${NC}"
if docker compose run --rm web python manage.py showmigrations --plan | grep -q "\[ \]"; then
    echo -e "${YELLOW}⚠️  Pending migrations found${NC}"
    echo ""
    echo "Pending migrations:"
    docker compose run --rm web python manage.py showmigrations --plan | grep "\[ \]" | head -20
    echo ""
else
    echo -e "${GREEN}✅ No pending migrations (all up to date)${NC}"
    echo ""
    echo "======================================================================"
    echo "✅ All migrations are already applied!"
    echo "======================================================================"
    exit 0
fi

# Step 4: Run migrations
echo -e "${YELLOW}🚀 Step 4: Running migrations...${NC}"
echo ""

if docker compose run --rm web python manage.py migrate --noinput; then
    echo ""
    echo -e "${GREEN}✅ Migrations completed successfully!${NC}"
else
    echo ""
    echo -e "${RED}❌ Migration failed!${NC}"
    echo ""
    echo "Showing recent database logs:"
    docker compose logs --tail=50 db
    echo ""
    echo "Showing web container logs:"
    docker compose logs --tail=50 web
    exit 1
fi
echo ""

# Step 5: Verify migrations
echo -e "${YELLOW}🔍 Step 5: Verifying migrations...${NC}"
if docker compose run --rm web python manage.py showmigrations --plan | grep -q "\[ \]"; then
    echo -e "${RED}⚠️  Some migrations are still pending!${NC}"
    docker compose run --rm web python manage.py showmigrations --plan | grep "\[ \]"
else
    echo -e "${GREEN}✅ All migrations have been applied${NC}"
fi
echo ""

# Step 6: Run Django checks
echo -e "${YELLOW}🧪 Step 6: Running Django checks...${NC}"
if docker compose run --rm web python manage.py check; then
    echo -e "${GREEN}✅ Django checks passed${NC}"
else
    echo -e "${YELLOW}⚠️  Django checks returned warnings (may be okay)${NC}"
fi
echo ""

# Summary
echo "======================================================================"
echo "✅ Migration process complete!"
echo "======================================================================"
echo ""
echo "Next steps:"
echo "  1. Review the migration output above"
echo "  2. If everything looks good, deploy with:"
echo "     docker compose up -d"
echo ""
echo "Troubleshooting:"
echo "  - View migrations: docker compose run --rm web python manage.py showmigrations"
echo "  - Check database: docker compose logs db"
echo "  - Django shell: docker compose run --rm web python manage.py shell"
echo ""

