#!/bin/bash

# Pilito VPS Setup Script
# This script sets up your VPS server for automated deployment
# Run this script on your VPS server

set -e

echo "🚀 Pilito VPS Setup Script"
echo "=========================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_info() {
    echo -e "ℹ️  $1"
}

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    print_error "Please run as root (use sudo)"
    exit 1
fi

print_info "Starting VPS setup..."
echo ""

# Update system
print_info "Updating system packages..."
apt-get update -qq
apt-get upgrade -y -qq
print_success "System updated"

# Install Docker
if ! command -v docker &> /dev/null; then
    print_info "Installing Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    rm get-docker.sh
    print_success "Docker installed"
else
    print_success "Docker already installed"
fi

# Install Docker Compose
if ! command -v docker-compose &> /dev/null; then
    print_info "Installing Docker Compose..."
    apt-get install -y docker-compose
    print_success "Docker Compose installed"
else
    print_success "Docker Compose already installed"
fi

# Enable Docker service
systemctl enable docker
systemctl start docker
print_success "Docker service enabled"

# Install other useful tools
print_info "Installing additional tools..."
apt-get install -y git curl wget nano htop rsync
print_success "Additional tools installed"

# Create project directory
PROJECT_DIR="/root/pilito"
if [ ! -d "$PROJECT_DIR" ]; then
    mkdir -p "$PROJECT_DIR"
    print_success "Project directory created: $PROJECT_DIR"
else
    print_success "Project directory exists: $PROJECT_DIR"
fi

# Create .env file if it doesn't exist
ENV_FILE="$PROJECT_DIR/.env"
if [ ! -f "$ENV_FILE" ]; then
    print_info "Creating .env template..."
    cat > "$ENV_FILE" << 'ENVEOF'
# Django Settings
DEBUG=False
SECRET_KEY=change-this-to-a-secure-random-key
ALLOWED_HOSTS=185.164.72.165

# Database Configuration
POSTGRES_DB=pilito_db
POSTGRES_USER=pilito_user
POSTGRES_PASSWORD=change-this-password

# Redis
REDIS_URL=redis://redis:6379

# RapidAPI
RAPIDAPI_KEY=your-rapidapi-key-here

# Email Configuration (optional)
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend

# Add your other environment variables here
ENVEOF
    print_success ".env template created"
    print_warning "Please edit $ENV_FILE and update the values!"
else
    print_success ".env file already exists"
fi

# Set up firewall
print_info "Configuring firewall..."
if command -v ufw &> /dev/null; then
    ufw --force reset
    ufw default deny incoming
    ufw default allow outgoing
    ufw allow 22/tcp comment 'SSH'
    ufw allow 80/tcp comment 'HTTP'
    ufw allow 443/tcp comment 'HTTPS'
    ufw allow 8000/tcp comment 'Django'
    ufw allow 3001/tcp comment 'Grafana'
    ufw allow 9090/tcp comment 'Prometheus'
    echo "y" | ufw enable
    print_success "Firewall configured"
else
    print_warning "UFW not available, skipping firewall setup"
fi

# Set up automated cleanup cron job
print_info "Setting up automated cleanup..."
cat > /etc/cron.d/pilito-cleanup << 'CRONEOF'
# Pilito Backend Automated Cleanup
SHELL=/bin/bash
PATH=/usr/local/sbin:/usr/local/bin:/sbin:/bin:/usr/sbin:/usr/bin

# Run full cleanup every Sunday at 2 AM
0 2 * * 0 root docker system prune -af --volumes >/tmp/weekly-cleanup.log 2>&1

# Clean Docker logs every day at 3 AM
0 3 * * * root find /var/lib/docker/containers/ -name "*-json.log" -exec truncate -s 10M {} \; 2>/dev/null || true

# Clean system logs daily at 4 AM
0 4 * * * root journalctl --vacuum-time=7d >/dev/null 2>&1
CRONEOF

chmod 644 /etc/cron.d/pilito-cleanup
systemctl reload cron || service cron reload
print_success "Automated cleanup configured"

# Create a manual cleanup script
print_info "Creating manual cleanup script..."
cat > "$PROJECT_DIR/cleanup.sh" << 'CLEANUPEOF'
#!/bin/bash
echo "🧹 Running manual cleanup..."
docker system prune -af --volumes
journalctl --vacuum-time=3d
apt-get autoremove -y
apt-get autoclean
echo "✅ Cleanup completed!"
df -h
CLEANUPEOF

chmod +x "$PROJECT_DIR/cleanup.sh"
print_success "Manual cleanup script created at $PROJECT_DIR/cleanup.sh"

# Display system information
echo ""
echo "════════════════════════════════════════════════"
echo "🎉 VPS Setup Complete!"
echo "════════════════════════════════════════════════"
echo ""
print_info "System Information:"
echo "  - Docker version: $(docker --version)"
echo "  - Docker Compose version: $(docker-compose --version)"
echo "  - Project directory: $PROJECT_DIR"
echo "  - Available disk space:"
df -h / | tail -1
echo ""

print_warning "Next Steps:"
echo ""
echo "1. Edit the .env file with your configuration:"
echo "   nano $ENV_FILE"
echo ""
echo "2. Set up SSH key authentication (recommended):"
echo "   - On your local machine, run:"
echo "     ssh-keygen -t ed25519 -C 'github-actions-deploy' -f ~/.ssh/pilito_deploy"
echo "     ssh-copy-id -i ~/.ssh/pilito_deploy.pub root@185.164.72.165"
echo ""
echo "3. Add the private key to GitHub Secrets:"
echo "   - Go to: Repository Settings → Secrets → New secret"
echo "   - Name: VPS_SSH_PRIVATE_KEY"
echo "   - Value: Content of ~/.ssh/pilito_deploy"
echo ""
echo "4. Add other GitHub Secrets:"
echo "   - VPS_HOST: 185.164.72.165"
echo "   - VPS_USER: root"
echo ""
echo "5. Push to main branch to trigger deployment!"
echo ""
print_success "Ready for CI/CD deployment! 🚀"
echo ""

