#!/bin/bash
# Emergency Server Cleanup and Deployment Fix
# Run this on your production server to fix the disk space issue

set -e

SERVER_IP="46.249.98.162"
SERVER_USER="root"

echo "🚨 Emergency Deployment Fix for Pilito Production Server"
echo "=========================================================="
echo ""
echo "This script will:"
echo "  1. Clean up Docker resources on the server"
echo "  2. Free up disk space"
echo "  3. Redeploy with optimized Docker images"
echo ""
read -p "Continue? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    exit 1
fi

echo ""
echo "📡 Connecting to server: $SERVER_IP"
echo "====================================="
echo ""

# SSH into server and run cleanup
ssh -o StrictHostKeyChecking=no ${SERVER_USER}@${SERVER_IP} << 'ENDSSH'
set -e

echo "🔍 Checking current disk usage..."
df -h
echo ""

echo "📊 Docker disk usage before cleanup:"
docker system df || true
echo ""

echo "🗑️  Starting aggressive cleanup..."
echo "===================================="

# Stop all containers to release locks
echo "1️⃣  Stopping all containers..."
docker stop $(docker ps -aq) 2>/dev/null || echo "No containers to stop"

# Remove all stopped containers
echo "2️⃣  Removing stopped containers..."
docker container prune -f

# Remove ALL unused images (not just dangling)
echo "3️⃣  Removing unused images..."
docker image prune -a -f

# Remove unused volumes (careful with this!)
echo "4️⃣  Removing unused volumes..."
docker volume ls -qf dangling=true | xargs -r docker volume rm || true

# Remove unused networks
echo "5️⃣  Removing unused networks..."
docker network prune -f

# Remove build cache
echo "6️⃣  Removing build cache..."
docker builder prune -a -f

# Clean containerd snapshots
echo "7️⃣  Cleaning containerd snapshots..."
if command -v ctr &> /dev/null; then
    # Remove failed snapshots
    ctr -n moby snapshot ls | grep -v "NAME" | awk '{print $1}' | xargs -r ctr -n moby snapshot rm || true
    # Clean content store
    ctr -n moby content ls -q | xargs -r ctr -n moby content rm || true
fi

# System cleanup
echo "8️⃣  System cleanup..."
apt-get clean || true
apt-get autoclean || true
rm -rf /var/log/*.log.* || true
rm -rf /tmp/* || true
journalctl --vacuum-time=3d || true

echo ""
echo "✅ Cleanup complete!"
echo ""

echo "📊 Disk usage after cleanup:"
df -h
echo ""

echo "📊 Docker disk usage after cleanup:"
docker system df || true
echo ""

# Check available space
AVAILABLE_GB=$(df -BG / | tail -1 | awk '{print $4}' | sed 's/G//')
echo "💾 Available disk space: ${AVAILABLE_GB}GB"
echo ""

if [ "$AVAILABLE_GB" -lt 15 ]; then
    echo "⚠️  WARNING: Only ${AVAILABLE_GB}GB available!"
    echo "Need at least 15GB for Docker build with PyTorch."
    echo ""
    echo "🔍 Top 20 largest files on system:"
    find /var /root /opt -type f -size +100M 2>/dev/null | xargs -I {} du -h {} | sort -rh | head -20 || true
    echo ""
    echo "Consider:"
    echo "  1. Deleting old Docker images manually"
    echo "  2. Checking /var/lib/docker size: du -sh /var/lib/docker/*"
    echo "  3. Increasing disk size"
    exit 1
fi

echo "✅ Sufficient space available! Proceeding with deployment..."

ENDSSH

echo ""
echo "✅ Server cleanup completed successfully!"
echo ""
echo "Now you can deploy with: git push origin main"
echo ""
echo "Or manually on the server:"
echo "  ssh ${SERVER_USER}@${SERVER_IP}"
echo "  cd ~/pilito"
echo "  docker-compose up -d --build"
echo ""

