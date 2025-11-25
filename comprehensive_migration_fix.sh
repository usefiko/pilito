#!/bin/bash
# Comprehensive script to fix the Django migration issue on production server
# This handles the case where containers are crashing due to migration errors

set -e

SERVER="root@185.164.72.165"
PASSWORD="9188945776poST?"

echo "🔧 Comprehensive fix for migration 0013 on production server..."

# Check if sshpass is installed
if ! command -v sshpass &> /dev/null; then
    echo "❌ sshpass is not installed. Installing..."
    if [[ "$OSTYPE" == "darwin"* ]]; then
        brew install hudochenkov/sshpass/sshpass
    else
        echo "Please install sshpass manually"
        exit 1
    fi
fi

# SSH commands to run on server
sshpass -p "$PASSWORD" ssh -o StrictHostKeyChecking=no "$SERVER" << 'ENDSSH'
set -e

cd /root/pilito

echo "🛑 Step 1: Stopping all containers..."
docker-compose down

echo ""
echo "📊 Step 2: Connecting directly to database to fix migration..."

# Start only the database
docker-compose up -d db

echo "⏳ Waiting for database to be ready..."
sleep 10

# Get database credentials from docker-compose or .env
DB_CONTAINER="postgres_db"

echo ""
echo "🔍 Step 3: Checking if columns exist in database..."

# Check and mark migration as fake in the database directly
docker exec $DB_CONTAINER psql -U postgres -d pilito_db << 'EOSQL'
-- Check if columns exist
SELECT 
    CASE 
        WHEN EXISTS (
            SELECT 1 FROM information_schema.columns 
            WHERE table_name='accounts_user' AND column_name='email_confirmed'
        ) THEN 'email_confirmed EXISTS ✅'
        ELSE 'email_confirmed MISSING ❌'
    END as email_confirmed_status,
    CASE 
        WHEN EXISTS (
            SELECT 1 FROM information_schema.columns 
            WHERE table_name='accounts_user' AND column_name='invite_code'
        ) THEN 'invite_code EXISTS ✅'
        ELSE 'invite_code MISSING ❌'
    END as invite_code_status,
    CASE 
        WHEN EXISTS (
            SELECT 1 FROM information_schema.columns 
            WHERE table_name='accounts_user' AND column_name='wallet_balance'
        ) THEN 'wallet_balance EXISTS ✅'
        ELSE 'wallet_balance MISSING ❌'
    END as wallet_balance_status,
    CASE 
        WHEN EXISTS (
            SELECT 1 FROM information_schema.columns 
            WHERE table_name='accounts_user' AND column_name='referred_by_id'
        ) THEN 'referred_by_id EXISTS ✅'
        ELSE 'referred_by_id MISSING ❌'
    END as referred_by_status;

-- Check if migration 0013 is already applied
SELECT app, name, applied FROM django_migrations 
WHERE app='accounts' AND name='0013_user_email_confirmed_user_invite_code_and_more';

-- If columns exist but migration is not marked as applied, mark it as fake
INSERT INTO django_migrations (app, name, applied)
SELECT 'accounts', '0013_user_email_confirmed_user_invite_code_and_more', NOW()
WHERE NOT EXISTS (
    SELECT 1 FROM django_migrations 
    WHERE app='accounts' AND name='0013_user_email_confirmed_user_invite_code_and_more'
)
AND EXISTS (
    SELECT 1 FROM information_schema.columns 
    WHERE table_name='accounts_user' AND column_name='email_confirmed'
);

-- Confirm the migration is now marked as applied
SELECT 
    CASE 
        WHEN EXISTS (
            SELECT 1 FROM django_migrations 
            WHERE app='accounts' AND name='0013_user_email_confirmed_user_invite_code_and_more'
        ) THEN '✅ Migration 0013 is marked as applied'
        ELSE '❌ Migration 0013 is NOT marked as applied'
    END as migration_status;
EOSQL

echo ""
echo "✅ Step 4: Database fix completed!"

echo ""
echo "🚀 Step 5: Starting all containers..."
docker-compose up -d

echo ""
echo "⏳ Waiting for containers to start..."
sleep 20

echo ""
echo "🔍 Step 6: Checking Django app health..."
if docker ps | grep -q django_app; then
    echo "✅ Django app container is running"
    
    echo ""
    echo "📊 Step 7: Verifying migrations..."
    docker exec django_app python manage.py showmigrations accounts || echo "⚠️  Migration check failed"
    
    echo ""
    echo "🔍 Step 8: Running Django check..."
    docker exec django_app python manage.py check || echo "⚠️  Django check failed"
    
    echo ""
    echo "📋 Container logs (last 30 lines):"
    docker logs django_app --tail 30
else
    echo "❌ Django app container is not running"
    echo ""
    echo "📋 Checking logs..."
    docker logs django_app --tail 50 || echo "Container not found"
fi

echo ""
echo "📊 Final container status:"
docker-compose ps

echo ""
echo "✅ Fix process completed!"
ENDSSH

echo ""
echo "🎉 Server fix process completed!"

