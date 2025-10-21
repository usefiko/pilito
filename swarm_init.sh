#!/bin/bash

# ============================================================================
# Docker Swarm Initialization Script
# ============================================================================
# This script initializes Docker Swarm and prepares the environment for
# high-availability deployment of the Pilito application.
# ============================================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# ============================================================================
# Pre-flight Checks
# ============================================================================

log_info "Starting Docker Swarm initialization..."

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    log_error "Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if docker-compose is installed
if ! command -v docker-compose &> /dev/null; then
    log_warning "docker-compose is not installed. Some features may not work."
fi

# Check if .env file exists
if [ ! -f .env ]; then
    log_error ".env file not found. Please create it from .env.example"
    exit 1
fi

log_success "Pre-flight checks passed"

# ============================================================================
# Docker Swarm Initialization
# ============================================================================

# Check if Swarm is already initialized
if docker info 2>/dev/null | grep -q "Swarm: active"; then
    log_warning "Docker Swarm is already initialized"
    
    # Display current swarm info
    log_info "Current Swarm Status:"
    docker node ls
    
    read -p "Do you want to continue with the existing swarm? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_info "Exiting..."
        exit 0
    fi
else
    log_info "Initializing Docker Swarm..."
    
    # Get the advertise address (default to first non-loopback IP)
    ADVERTISE_ADDR=$(ip route get 8.8.8.8 | awk -F"src " 'NR==1{split($2,a," ");print a[1]}' 2>/dev/null)
    
    if [ -z "$ADVERTISE_ADDR" ]; then
        log_warning "Could not automatically detect IP address"
        read -p "Enter the advertise address for this manager node: " ADVERTISE_ADDR
    else
        log_info "Detected IP address: $ADVERTISE_ADDR"
        read -p "Use this IP address? (y/n) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            read -p "Enter the advertise address for this manager node: " ADVERTISE_ADDR
        fi
    fi
    
    # Initialize swarm
    docker swarm init --advertise-addr "$ADVERTISE_ADDR"
    log_success "Docker Swarm initialized successfully"
fi

# ============================================================================
# Node Labeling
# ============================================================================

log_info "Labeling current node as manager..."
MANAGER_NODE=$(docker node ls --format "{{.Hostname}}" --filter "role=manager" | head -n 1)
docker node update --label-add node.role=manager "$MANAGER_NODE"
log_success "Node labeled successfully"

# ============================================================================
# Network Creation
# ============================================================================

log_info "Creating overlay network for services..."

# Check if network already exists
if docker network ls --format "{{.Name}}" | grep -q "^pilito_network$"; then
    log_warning "Network 'pilito_network' already exists"
else
    docker network create \
        --driver overlay \
        --attachable \
        --subnet 10.0.10.0/24 \
        pilito_network
    log_success "Overlay network created successfully"
fi

# ============================================================================
# Build Docker Images
# ============================================================================

log_info "Building Docker images..."
docker-compose -f docker-compose.swarm.yml build
log_success "Docker images built successfully"

# ============================================================================
# Display Join Commands
# ============================================================================

log_info "To add worker nodes to this swarm, run the following command on each worker node:"
echo ""
docker swarm join-token worker
echo ""

log_info "To add manager nodes to this swarm, run the following command on each manager node:"
echo ""
docker swarm join-token manager
echo ""

# ============================================================================
# Final Instructions
# ============================================================================

log_success "Docker Swarm initialization complete!"
echo ""
log_info "Next steps:"
echo "  1. Add worker nodes (optional) using the join command above"
echo "  2. Deploy the stack: ./swarm_deploy.sh"
echo "  3. Monitor services: docker service ls"
echo "  4. View logs: docker service logs <service_name>"
echo ""
log_info "To save join tokens for later:"
echo "  Worker token: docker swarm join-token worker -q > worker_token.txt"
echo "  Manager token: docker swarm join-token manager -q > manager_token.txt"

