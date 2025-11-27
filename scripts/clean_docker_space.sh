#!/bin/bash
# Docker Space Cleanup Script
# This script aggressively cleans Docker to free up disk space

set -e

echo "🗑️  Docker Space Cleanup Script"
echo "================================"
echo ""

# Show current disk usage
echo "📊 Current disk usage:"
df -h /
echo ""

# Show Docker disk usage
echo "📊 Docker disk usage:"
docker system df
echo ""

# Function to confirm action
confirm() {
    read -p "$1 (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        return 1
    fi
    return 0
}

# Stop all running containers
if confirm "Stop all running containers?"; then
    echo "🛑 Stopping all containers..."
    docker stop $(docker ps -aq) 2>/dev/null || echo "No containers to stop"
fi

# Remove stopped containers
if confirm "Remove all stopped containers?"; then
    echo "🗑️  Removing stopped containers..."
    docker container prune -f
fi

# Remove dangling images
if confirm "Remove dangling images?"; then
    echo "🗑️  Removing dangling images..."
    docker image prune -f
fi

# Remove all unused images
if confirm "Remove ALL unused images (keeps only running containers)?"; then
    echo "🗑️  Removing unused images..."
    docker image prune -a -f
fi

# Remove unused volumes
if confirm "Remove unused volumes? (⚠️  This will delete database data if not in use!)"; then
    echo "🗑️  Removing unused volumes..."
    docker volume prune -f
fi

# Remove unused networks
if confirm "Remove unused networks?"; then
    echo "🗑️  Removing unused networks..."
    docker network prune -f
fi

# Remove build cache
if confirm "Remove build cache?"; then
    echo "🗑️  Removing build cache..."
    docker builder prune -a -f
fi

# Clean containerd snapshots
if command -v ctr &> /dev/null; then
    if confirm "Clean containerd snapshots?"; then
        echo "🗑️  Cleaning containerd snapshots..."
        ctr -n moby content ls -q | xargs -r ctr -n moby content rm || true
    fi
fi

# System prune (everything at once)
if confirm "Run full system prune? (⚠️  Removes everything not in use!)"; then
    echo "🗑️  Running system prune..."
    docker system prune -a -f --volumes
fi

echo ""
echo "✅ Cleanup complete!"
echo ""

# Show disk usage after cleanup
echo "📊 Disk usage after cleanup:"
df -h /
echo ""

echo "📊 Docker disk usage after cleanup:"
docker system df
echo ""

AVAILABLE_GB=$(df -BG / | tail -1 | awk '{print $4}' | sed 's/G//')
echo "💾 Available disk space: ${AVAILABLE_GB}GB"

if [ "$AVAILABLE_GB" -lt 15 ]; then
    echo ""
    echo "⚠️  WARNING: Still only ${AVAILABLE_GB}GB available!"
    echo "Consider:"
    echo "  1. Deleting old log files: find /var/log -type f -name '*.log' -delete"
    echo "  2. Cleaning apt cache: apt-get clean && apt-get autoclean"
    echo "  3. Removing old kernels: apt-get autoremove"
    echo "  4. Checking large files: du -h / | sort -rh | head -20"
    echo "  5. Increasing server disk size"
else
    echo "✅ Sufficient disk space available for Docker builds!"
fi

