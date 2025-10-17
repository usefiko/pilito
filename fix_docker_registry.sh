#!/bin/bash

# 🔧 Fix Docker Registry Access for Iranian VPS
# 
# Usage:
#   chmod +x fix_docker_registry.sh
#   sudo ./fix_docker_registry.sh
#
# This script sets Iranian Docker registry mirrors to bypass DockerHub restrictions.
# ⚠️  Only run this on Iranian VPS servers. Running on foreign servers may slow down pulls.

set -e

echo "🔧 Configuring Docker Registry Mirror for Iranian VPS..."

# Create daemon.json if it doesn't exist
DAEMON_FILE="/etc/docker/daemon.json"

# Backup existing config if it exists
if [ -f "$DAEMON_FILE" ]; then
    echo "📦 Backing up existing Docker daemon.json..."
    sudo cp "$DAEMON_FILE" "$DAEMON_FILE.backup.$(date +%Y%m%d_%H%M%S)"
fi

# Create new daemon.json with Iranian registry mirrors and international fallback
echo "📝 Creating Docker daemon.json with registry mirrors..."
sudo tee "$DAEMON_FILE" > /dev/null <<EOF
{
  "registry-mirrors": [
    "https://docker.iranrepo.ir",
    "https://registry.docker.ir",
    "https://dockerhub.ir",
    "https://mirror.gcr.io"
  ],
  "insecure-registries": [],
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  }
}
EOF

echo "✅ Docker daemon.json created successfully"

# Test if mirrors are accessible (simple healthcheck)
echo "🔍 Testing mirror accessibility..."
MIRROR_OK=false

for mirror in "https://docker.iranrepo.ir" "https://registry.docker.ir" "https://dockerhub.ir"; do
    if curl -s --max-time 5 "$mirror" > /dev/null 2>&1; then
        echo "✅ Mirror accessible: $mirror"
        MIRROR_OK=true
        break
    else
        echo "⚠️  Mirror not responding: $mirror"
    fi
done

if [ "$MIRROR_OK" = false ]; then
    echo "⚠️  Warning: No Iranian mirrors responding. Will fallback to international mirror."
fi

# Restart Docker service
echo "🔄 Restarting Docker service..."
sudo systemctl daemon-reload
sudo systemctl restart docker

# Wait for Docker to restart
echo "⏳ Waiting for Docker to restart..."
sleep 5

# Verify Docker is running
if sudo systemctl is-active --quiet docker; then
    echo "✅ Docker is running successfully"
else
    echo "❌ Docker failed to start. Check logs with: sudo journalctl -xeu docker"
    exit 1
fi

# Test registry access with a small image
echo "🧪 Testing registry access..."
if sudo docker pull hello-world:latest > /dev/null 2>&1; then
    echo "✅ Registry access is working!"
    sudo docker rmi hello-world:latest > /dev/null 2>&1 || true
else
    echo "⚠️  Warning: Could not pull test image. This might be temporary."
    echo "💡 Try running: docker pull hello-world:latest manually"
fi

# Show Docker info
echo ""
echo "📊 Docker configuration:"
sudo docker info | grep -A 5 "Registry Mirrors" || echo "Registry mirrors configured"

echo ""
echo "✅ Docker registry mirror configuration completed!"
echo "💡 You can now run your deployment again"
echo ""
echo "📝 Note: If mirrors are down, Docker will automatically fallback to direct connection"
