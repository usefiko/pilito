#!/bin/bash

# Fix PostgreSQL Collation Version Mismatch
# Run this on your EC2 instance to fix the collation warning

set -e

echo "🔧 Fixing PostgreSQL Collation Version Mismatch..."
echo "================================================="

# Configuration
SSH_USER="ubuntu"
SSH_HOST="ec2-3-22-98-184.us-east-2.compute.amazonaws.com"

echo ""
echo "Connecting to production server..."

ssh ${SSH_USER}@${SSH_HOST} << 'ENDSSH'

echo ""
echo "📊 Current collation version status:"
docker exec -it postgres_db psql -U postgres -d FikoDB -c "SELECT datname, datcollate, datctype, datcollversion FROM pg_database WHERE datname = 'FikoDB';"

echo ""
echo "🔧 Refreshing collation version..."
docker exec -it postgres_db psql -U postgres -d FikoDB -c "ALTER DATABASE \"FikoDB\" REFRESH COLLATION VERSION;"

echo ""
echo "✅ Collation version updated!"
echo ""
echo "📊 New collation version status:"
docker exec -it postgres_db psql -U postgres -d FikoDB -c "SELECT datname, datcollate, datctype, datcollversion FROM pg_database WHERE datname = 'FikoDB';"

echo ""
echo "🔄 Restarting Django container to clear the warning..."
docker restart django_app

echo ""
echo "⏳ Waiting for Django to restart..."
sleep 5

echo ""
echo "📝 Checking logs (warning should be gone)..."
docker logs django_app --tail 20

ENDSSH

echo ""
echo "✅ Database collation fix complete!"

