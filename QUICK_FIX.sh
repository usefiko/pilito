#!/bin/bash
# QUICK FIX: Run this script to fix the disk space issue immediately

echo "🚨 EMERGENCY FIX FOR DISK SPACE ISSUE"
echo "====================================="
echo ""

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

SERVER_IP="46.249.98.162"
SERVER_USER="root"
SERVER="${SERVER_USER}@${SERVER_IP}"

echo -e "${YELLOW}Step 1: Cleaning up server disk space...${NC}"
echo ""

# Run cleanup on server
ssh -o StrictHostKeyChecking=no ${SERVER} bash << 'ENDSSH'
set -e

echo "🔍 Current disk usage:"
df -h /
echo ""

echo "🛑 Stopping all Docker containers..."
docker stop $(docker ps -aq) 2>/dev/null || echo "No containers running"

echo "🗑️  Removing stopped containers..."
docker container prune -f

echo "🗑️  Removing unused images..."
docker image prune -a -f

echo "🗑️  Removing unused volumes..."
docker volume prune -f

echo "🗑️  Removing build cache..."
docker builder prune -a -f

echo "🗑️  Cleaning containerd snapshots..."
if command -v ctr &> /dev/null; then
    ctr -n moby snapshot ls | grep -v "NAME" | awk '{print $1}' | xargs -r ctr -n moby snapshot rm 2>/dev/null || true
fi

echo ""
echo "✅ Cleanup complete!"
echo ""
echo "📊 Disk usage after cleanup:"
df -h /
echo ""

AVAILABLE_GB=$(df -BG / | tail -1 | awk '{print $4}' | sed 's/G//')
echo "💾 Available space: ${AVAILABLE_GB}GB"

if [ "$AVAILABLE_GB" -lt 15 ]; then
    echo ""
    echo "⚠️  WARNING: Only ${AVAILABLE_GB}GB available"
    echo "Deployment may still fail. Consider:"
    echo "  1. Manually removing large files"
    echo "  2. Increasing server disk size"
    echo "  3. Using the optimized Dockerfile (recommended)"
    exit 1
else
    echo "✅ Sufficient space available!"
fi

ENDSSH

if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN}✅ Server cleanup successful!${NC}"
    echo ""
    echo -e "${YELLOW}Step 2: Now deploy with the optimized Dockerfile${NC}"
    echo ""
    echo "The Dockerfile has been updated to use CPU-only PyTorch (70% smaller)."
    echo ""
    echo "Run these commands to deploy:"
    echo ""
    echo "  git add Dockerfile"
    echo "  git commit -m 'Use optimized CPU-only PyTorch Dockerfile'"
    echo "  git push origin main"
    echo ""
else
    echo ""
    echo -e "${RED}❌ Cleanup failed or insufficient space${NC}"
    echo ""
    echo "Manual intervention required:"
    echo "  ssh ${SERVER}"
    echo "  df -h"
    echo "  docker system df"
    echo "  # Manually remove large files if needed"
fi

