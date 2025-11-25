#!/bin/bash
# Script to fix the migration issue on the production server
# This will mark the migration as applied without running it

set -e

echo "🔧 Fixing migration 0013 on production server..."

# SSH into the server and run the commands
ssh root@185.164.72.165 << 'ENDSSH'
    cd /root/pilito
    
    echo "📊 Checking current migration status..."
    docker exec django_app python manage.py showmigrations accounts
    
    echo ""
    echo "🔧 Marking migration 0013 as fake (since columns already exist)..."
    docker exec django_app python manage.py migrate accounts 0013 --fake
    
    echo ""
    echo "✅ Migration 0013 has been marked as applied"
    
    echo ""
    echo "📊 Updated migration status:"
    docker exec django_app python manage.py showmigrations accounts
    
    echo ""
    echo "✅ Migration fix complete!"
ENDSSH

echo ""
echo "🎉 Server migration fixed successfully!"

