#!/bin/bash

# ============================================================================
# Docker Swarm Cleanup Script
# ============================================================================
# This script safely removes the stack and optionally cleans up Docker Swarm.
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
# Display Warning
# ============================================================================

log_warning "═══════════════════════════════════════════════════════"
log_warning "  DOCKER SWARM CLEANUP - DESTRUCTIVE OPERATION"
log_warning "═══════════════════════════════════════════════════════"
echo ""

# ============================================================================
# Cleanup Options
# ============================================================================

echo "Select cleanup option:"
echo "  1) Remove stack only (keep swarm and data)"
echo "  2) Remove stack and volumes (DELETES DATA)"
echo "  3) Remove stack and leave swarm"
echo "  4) Full cleanup (remove stack, volumes, and leave swarm)"
echo "  5) Cancel"
echo ""
read -p "Enter choice [1-5]: " CHOICE

case $CHOICE in
    1)
        log_info "Removing stack only..."
        REMOVE_STACK=true
        REMOVE_VOLUMES=false
        LEAVE_SWARM=false
        ;;
    2)
        log_warning "This will DELETE ALL DATA (databases, media files, etc.)"
        read -p "Are you absolutely sure? Type 'yes' to confirm: " CONFIRM
        if [ "$CONFIRM" != "yes" ]; then
            log_info "Cleanup cancelled"
            exit 0
        fi
        REMOVE_STACK=true
        REMOVE_VOLUMES=true
        LEAVE_SWARM=false
        ;;
    3)
        log_info "Removing stack and leaving swarm..."
        REMOVE_STACK=true
        REMOVE_VOLUMES=false
        LEAVE_SWARM=true
        ;;
    4)
        log_warning "This will DELETE ALL DATA and leave swarm mode"
        read -p "Are you absolutely sure? Type 'yes' to confirm: " CONFIRM
        if [ "$CONFIRM" != "yes" ]; then
            log_info "Cleanup cancelled"
            exit 0
        fi
        REMOVE_STACK=true
        REMOVE_VOLUMES=true
        LEAVE_SWARM=true
        ;;
    5)
        log_info "Cleanup cancelled"
        exit 0
        ;;
    *)
        log_error "Invalid choice"
        exit 1
        ;;
esac

# ============================================================================
# Remove Stack
# ============================================================================

if [ "$REMOVE_STACK" = true ]; then
    if docker stack ls --format "{{.Name}}" | grep -q "^$STACK_NAME$"; then
        log_info "Removing stack: $STACK_NAME"
        docker stack rm "$STACK_NAME"
        
        log_info "Waiting for stack to be fully removed..."
        while docker stack ps "$STACK_NAME" 2>/dev/null | grep -q "Running\|Pending"; do
            echo -n "."
            sleep 2
        done
        echo ""
        log_success "Stack removed successfully"
    else
        log_warning "Stack '$STACK_NAME' not found"
    fi
fi

# ============================================================================
# Remove Volumes
# ============================================================================

if [ "$REMOVE_VOLUMES" = true ]; then
    log_warning "Removing volumes..."
    
    # List of volumes to remove
    VOLUMES=(
        "${STACK_NAME}_postgres_data"
        "${STACK_NAME}_redis_data"
        "${STACK_NAME}_static_volume"
        "${STACK_NAME}_media_volume"
        "${STACK_NAME}_prometheus_data"
        "${STACK_NAME}_grafana_data"
    )
    
    for VOLUME in "${VOLUMES[@]}"; do
        if docker volume ls --format "{{.Name}}" | grep -q "^$VOLUME$"; then
            log_info "Removing volume: $VOLUME"
            docker volume rm "$VOLUME" || log_warning "Failed to remove $VOLUME"
        fi
    done
    
    log_success "Volumes cleanup complete"
fi

# ============================================================================
# Leave Swarm
# ============================================================================

if [ "$LEAVE_SWARM" = true ]; then
    if docker info 2>/dev/null | grep -q "Swarm: active"; then
        log_warning "Leaving swarm mode..."
        
        # Check if this is a manager node
        if docker node ls >/dev/null 2>&1; then
            MANAGER_COUNT=$(docker node ls --filter "role=manager" -q | wc -l | tr -d ' ')
            
            if [ "$MANAGER_COUNT" -gt 1 ]; then
                log_warning "Multiple managers detected. Demote this node first:"
                log_info "docker node demote \$(hostname)"
                read -p "Continue anyway? (yes/no): " CONFIRM
                if [ "$CONFIRM" != "yes" ]; then
                    log_info "Leaving swarm cancelled"
                    exit 0
                fi
            fi
        fi
        
        docker swarm leave --force
        log_success "Left swarm successfully"
    else
        log_warning "Not in swarm mode"
    fi
fi

# ============================================================================
# Additional Cleanup
# ============================================================================

log_info "Running additional cleanup..."

# Remove unused images
log_info "Removing unused images..."
docker image prune -f

# Remove unused networks
log_info "Removing unused networks..."
docker network prune -f

log_success "Additional cleanup complete"

# ============================================================================
# Summary
# ============================================================================

echo ""
log_success "═══════════════════════════════════════════════════════"
log_success "  CLEANUP COMPLETE"
log_success "═══════════════════════════════════════════════════════"
echo ""

if [ "$REMOVE_STACK" = true ]; then
    echo "✓ Stack removed"
fi

if [ "$REMOVE_VOLUMES" = true ]; then
    echo "✓ Volumes removed (data deleted)"
fi

if [ "$LEAVE_SWARM" = true ]; then
    echo "✓ Left swarm mode"
fi

echo ""
log_info "To redeploy:"
echo "  1. Initialize swarm: ./swarm_init.sh"
echo "  2. Deploy stack:     ./swarm_deploy.sh"

