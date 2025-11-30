#!/bin/bash

###############################################################################
# Fix Conflicting Migrations - Remove Duplicate Files
# Run this on the server to fix the migration conflict
###############################################################################

set -e

echo "======================================================================"
echo "🔧 Fixing Conflicting Migrations"
echo "======================================================================"
echo ""

cd ~/pilito

# The problem: We have both 0002_user_affiliate_active.py and 0011_user_affiliate_active.py
# Solution: Remove the old 0002 file since we renamed it to 0011

echo "📋 Step 1: Checking for duplicate migration files..."

# Check if the old file exists
if [ -f "src/accounts/migrations/0002_user_affiliate_active.py" ]; then
    echo "⚠️  Found old migration file: 0002_user_affiliate_active.py"
    echo "🗑️  Removing old duplicate migration..."
    rm -f src/accounts/migrations/0002_user_affiliate_active.py
    echo "✅ Removed 0002_user_affiliate_active.py"
else
    echo "✅ No duplicate 0002 file found"
fi

# Also remove the compiled .pyc file if it exists
if [ -f "src/accounts/migrations/__pycache__/0002_user_affiliate_active.cpython-311.pyc" ]; then
    rm -f src/accounts/migrations/__pycache__/0002_user_affiliate_active.cpython-311.pyc
    echo "✅ Removed compiled .pyc file"
fi

echo ""
echo "📋 Step 2: Listing current migration files..."
ls -la src/accounts/migrations/*.py | grep -E "000[0-9]|001[0-9]" || true

echo ""
echo "======================================================================"
echo "✅ Migration conflict fixed!"
echo "======================================================================"
echo ""
echo "Now you can run migrations:"
echo "  docker compose run --rm web python manage.py migrate"
echo ""

