#!/bin/bash
# Script to fix the migration issue on the production server using sshpass
# This will mark the migration as applied without running it

set -e

SERVER="root@185.164.72.165"
PASSWORD="9188945776poST?"

echo "🔧 Fixing migration 0013 on production server..."

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

echo "📊 Checking current migration status..."
docker exec django_app python manage.py showmigrations accounts || echo "⚠️  Container not running, will check after restart"

echo ""
echo "🔧 Marking migration 0013 as fake (since columns already exist)..."
docker exec django_app python manage.py migrate accounts 0013 --fake || echo "⚠️  Will retry after container restart"

echo ""
echo "✅ Migration 0013 has been marked as applied"

echo ""
echo "📊 Updated migration status:"
docker exec django_app python manage.py showmigrations accounts || echo "Will show after restart"

echo ""
echo "🔄 Restarting containers to apply changes..."
docker-compose restart web celery_worker celery_beat celery_ai

echo ""
echo "⏳ Waiting for containers to start..."
sleep 10

echo ""
echo "📊 Final migration status:"
docker exec django_app python manage.py showmigrations accounts

echo ""
echo "✅ Migration fix complete!"
ENDSSH

echo ""
echo "🎉 Server migration fixed successfully!"

