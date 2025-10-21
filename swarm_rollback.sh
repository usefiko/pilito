#!/bin/bash

# ============================================================================
# Docker Swarm Service Rollback Script
# ============================================================================
# This script rolls back a service to its previous version in case of
# deployment issues or failures.
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
# Pre-rollback Checks
# ============================================================================

log_warning "ROLLBACK OPERATION - This will revert services to their previous state"

# Check if Swarm is active
if ! docker info 2>/dev/null | grep -q "Swarm: active"; then
    log_error "Docker Swarm is not initialized."
    exit 1
fi

# Check if stack exists
if ! docker stack ls --format "{{.Name}}" | grep -q "^$STACK_NAME$"; then
    log_error "Stack '$STACK_NAME' is not deployed."
    exit 1
fi

# ============================================================================
# Display Current Services
# ============================================================================

echo ""
log_info "Current services:"
docker stack services "$STACK_NAME" --format "table {{.Name}}\t{{.Replicas}}\t{{.Image}}"

# ============================================================================
# Service Selection
# ============================================================================

echo ""
if [ $# -eq 1 ]; then
    SERVICE_NAME="$1"
else
    read -p "Enter service name to rollback (or 'all' for all services): " SERVICE_NAME
fi

# Confirmation
echo ""
log_warning "You are about to rollback: $SERVICE_NAME"
read -p "Are you sure? (yes/no): " CONFIRM

if [ "$CONFIRM" != "yes" ]; then
    log_info "Rollback cancelled"
    exit 0
fi

# ============================================================================
# Perform Rollback
# ============================================================================

if [ "$SERVICE_NAME" = "all" ]; then
    log_info "Rolling back all services..."
    
    # Get all services in the stack
    SERVICES=$(docker stack services "$STACK_NAME" --format "{{.Name}}")
    
    for SERVICE in $SERVICES; do
        log_info "Rolling back: $SERVICE"
        docker service rollback "$SERVICE" || log_warning "Failed to rollback $SERVICE"
    done
    
    log_success "All services rollback initiated"
else
    # Determine full service name
    if docker service ls --format "{{.Name}}" | grep -q "^${SERVICE_NAME}$"; then
        FULL_SERVICE_NAME="$SERVICE_NAME"
    elif docker service ls --format "{{.Name}}" | grep -q "^${STACK_NAME}_${SERVICE_NAME}$"; then
        FULL_SERVICE_NAME="${STACK_NAME}_${SERVICE_NAME}"
    else
        log_error "Service not found: $SERVICE_NAME"
        exit 1
    fi
    
    log_info "Rolling back: $FULL_SERVICE_NAME"
    docker service rollback "$FULL_SERVICE_NAME"
    log_success "Service rollback initiated"
fi

# ============================================================================
# Monitor Rollback Progress
# ============================================================================

echo ""
log_info "Monitoring rollback progress..."
echo "Press Ctrl+C to stop monitoring (rollback will continue in background)"
echo ""
sleep 3

if [ "$SERVICE_NAME" = "all" ]; then
    # Monitor all services
    for i in {1..10}; do
        clear
        echo "Rollback Progress - Iteration $i/10"
        echo "===================================="
        docker stack services "$STACK_NAME"
        sleep 3
    done
else
    # Monitor specific service
    for i in {1..10}; do
        clear
        echo "Rollback Progress - Iteration $i/10"
        echo "===================================="
        docker service ps "$FULL_SERVICE_NAME" --no-trunc | head -n 15
        echo ""
        docker service ls --filter "name=$FULL_SERVICE_NAME"
        sleep 3
    done
fi

echo ""
log_success "Rollback monitoring complete"
log_info "Check service status: docker service ps <service-name>"

