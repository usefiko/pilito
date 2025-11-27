#!/bin/bash
# Server Maintenance Script
# Run this periodically to keep the server healthy

set -e

echo "🔧 Server Maintenance Script"
echo "============================"
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "⚠️  This script should be run as root for full cleanup"
    echo "Consider running: sudo $0"
fi

echo "📊 System Information:"
echo "----------------------"
uname -a
echo ""

echo "📊 Disk Usage:"
echo "--------------"
df -h
echo ""

echo "📊 Memory Usage:"
echo "----------------"
free -h
echo ""

echo "📊 Top 10 Largest Directories:"
echo "------------------------------"
du -h --max-depth=1 / 2>/dev/null | sort -rh | head -10 || true
echo ""

# Docker cleanup
echo "🐳 Docker Cleanup:"
echo "------------------"
if command -v docker &> /dev/null; then
    echo "Current Docker usage:"
    docker system df
    echo ""
    
    echo "Cleaning Docker..."
    docker container prune -f || true
    docker image prune -f || true
    docker volume prune -f || true
    docker network prune -f || true
    docker builder prune -f || true
    
    echo ""
    echo "Docker usage after cleanup:"
    docker system df
else
    echo "Docker not installed"
fi
echo ""

# System cleanup
echo "🧹 System Cleanup:"
echo "------------------"

# Clean apt cache
if command -v apt-get &> /dev/null; then
    echo "Cleaning apt cache..."
    apt-get clean || true
    apt-get autoclean || true
    apt-get autoremove -y || true
fi

# Clean old logs
echo "Cleaning old logs..."
find /var/log -type f -name "*.log.*" -delete 2>/dev/null || true
find /var/log -type f -name "*.gz" -delete 2>/dev/null || true
journalctl --vacuum-time=7d 2>/dev/null || true

# Clean temp files
echo "Cleaning temp files..."
rm -rf /tmp/* 2>/dev/null || true
rm -rf /var/tmp/* 2>/dev/null || true

# Clean old kernels (Ubuntu/Debian)
if command -v dpkg &> /dev/null; then
    echo "Removing old kernels..."
    dpkg -l | grep -E 'linux-image-[0-9]' | grep -v $(uname -r) | awk '{print $2}' | xargs -r apt-get remove -y || true
fi

echo ""
echo "✅ Maintenance complete!"
echo ""

# Final disk check
echo "📊 Final Disk Usage:"
df -h
echo ""

AVAILABLE_GB=$(df -BG / | tail -1 | awk '{print $4}' | sed 's/G//')
echo "💾 Available disk space: ${AVAILABLE_GB}GB"

if [ "$AVAILABLE_GB" -lt 15 ]; then
    echo ""
    echo "⚠️  WARNING: Only ${AVAILABLE_GB}GB available!"
    echo "Docker builds require at least 15GB free space."
    echo ""
    echo "🔍 Investigating large files..."
    echo "Top 20 largest files:"
    find / -type f -size +100M 2>/dev/null | xargs -I {} du -h {} | sort -rh | head -20 || true
fi

