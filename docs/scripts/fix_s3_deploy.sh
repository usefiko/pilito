#!/bin/bash

# Fix S3 Collectstatic Error - Deployment Script
# This script updates the production server with the fixed entrypoint.sh

set -e  # Exit on any error

echo "🚀 Deploying S3 Collectstatic Fix..."
echo "=================================="

# Configuration
SSH_USER="ubuntu"
SSH_HOST="ec2-3-22-98-184.us-east-2.compute.amazonaws.com"
APP_DIR="/home/ubuntu/Fiko-Backend"

echo ""
echo "📋 Step 1: Backing up current entrypoint.sh..."
ssh ${SSH_USER}@${SSH_HOST} "cd ${APP_DIR} && cp entrypoint.sh entrypoint.sh.backup.$(date +%Y%m%d_%H%M%S)"

echo ""
echo "📤 Step 2: Uploading fixed files..."
scp entrypoint.sh ${SSH_USER}@${SSH_HOST}:${APP_DIR}/entrypoint.sh
scp src/core/settings/storage_backends.py ${SSH_USER}@${SSH_HOST}:${APP_DIR}/src/core/settings/storage_backends.py
scp src/monitoring/middleware.py ${SSH_USER}@${SSH_HOST}:${APP_DIR}/src/monitoring/middleware.py

echo ""
echo "🔧 Step 3: Rebuilding Docker containers..."
ssh ${SSH_USER}@${SSH_HOST} << 'ENDSSH'
cd /home/ubuntu/Fiko-Backend
docker-compose down
docker-compose build --no-cache web celery_worker celery_beat
docker-compose up -d
ENDSSH

echo ""
echo "⏳ Step 4: Waiting for containers to start..."
sleep 10

echo ""
echo "📊 Step 5: Checking container status..."
ssh ${SSH_USER}@${SSH_HOST} "docker ps"

echo ""
echo "📝 Step 6: Checking Django logs..."
ssh ${SSH_USER}@${SSH_HOST} "docker logs django_app --tail 30"

echo ""
echo "✅ Deployment Complete!"
echo ""
echo "Next steps:"
echo "1. Verify your app is accessible"
echo "2. Check static files are loading correctly"
echo "3. Fix the S3 bucket configuration (see fix_s3_collectstatic.md)"
echo "4. Fix the database collation warning (see fix_s3_collectstatic.md)"
echo ""

