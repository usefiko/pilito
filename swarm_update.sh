#!/bin/bash

# ============================================================================
# Docker Swarm Service Update Script
# ============================================================================
# This script updates services in the Docker Swarm stack with zero downtime.
# ============================================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
STACK_NAME="pilito"
COMPOSE_FILE="docker-compose.swarm.yml"

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
# Pre-update Checks
# ============================================================================

log_info "Running pre-update checks..."

# Check if Swarm is active
if ! docker info 2>/dev/null | grep -q "Swarm: active"; then
    log_error "Docker Swarm is not initialized."
    exit 1
fi

# Check if stack exists
if ! docker stack ls --format "{{.Name}}" | grep -q "^$STACK_NAME$"; then
    log_error "Stack '$STACK_NAME' is not deployed. Run ./swarm_deploy.sh first."
    exit 1
fi

log_success "Pre-update checks passed"

# ============================================================================
# Service Selection
# ============================================================================

echo ""
log_info "Available services:"
docker stack services "$STACK_NAME" --format "table {{.Name}}\t{{.Replicas}}\t{{.Image}}"

echo ""
read -p "Enter service name to update (or 'all' to update all): " SERVICE_NAME

# ============================================================================
# Build Updated Images
# ============================================================================

log_info "Building latest Docker images..."
docker-compose -f "$COMPOSE_FILE" build
log_success "Images built successfully"

# ============================================================================
# Update Service(s)
# ============================================================================

if [ "$SERVICE_NAME" = "all" ]; then
    log_info "Updating entire stack..."
    
    docker stack deploy \
        --compose-file "$COMPOSE_FILE" \
        --with-registry-auth \
        "$STACK_NAME"
    
    log_success "Stack update initiated"
else
    # Validate service name
    if ! docker service ls --format "{{.Name}}" | grep -q "^${STACK_NAME}_${SERVICE_NAME}$" && \
       ! docker service ls --format "{{.Name}}" | grep -q "^${SERVICE_NAME}$"; then
        log_error "Service not found: $SERVICE_NAME"
        exit 1
    fi
    
    # Determine full service name
    if docker service ls --format "{{.Name}}" | grep -q "^${SERVICE_NAME}$"; then
        FULL_SERVICE_NAME="$SERVICE_NAME"
    else
        FULL_SERVICE_NAME="${STACK_NAME}_${SERVICE_NAME}"
    fi
    
    log_info "Updating service: $FULL_SERVICE_NAME"
    
    # Force update with new image
    docker service update \
        --force \
        --update-parallelism 1 \
        --update-delay 10s \
        "$FULL_SERVICE_NAME"
    
    log_success "Service update initiated"
fi

# ============================================================================
# Monitor Update Progress
# ============================================================================

echo ""
log_info "Monitoring update progress..."
echo "Press Ctrl+C to stop monitoring (update will continue in background)"
echo ""

if [ "$SERVICE_NAME" = "all" ]; then
    # Monitor all services
    while true; do
        clear
        echo "Update Progress - $(date)"
        echo "================================"
        docker stack services "$STACK_NAME"
        sleep 2
    done
else
    # Monitor specific service
    while true; do
        clear
        echo "Update Progress - $(date)"
        echo "================================"
        docker service ps "$FULL_SERVICE_NAME" --no-trunc | head -n 20
        echo ""
        echo "Service Status:"
        docker service ls --filter "name=$FULL_SERVICE_NAME"
        sleep 2
    done
fi

