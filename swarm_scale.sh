#!/bin/bash

# ============================================================================
# Docker Swarm Service Scaling Script
# ============================================================================
# This script allows you to scale services up or down in the Docker Swarm.
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
# Pre-scaling Checks
# ============================================================================

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
log_info "Current services and replicas:"
docker stack services "$STACK_NAME" --format "table {{.Name}}\t{{.Replicas}}\t{{.Image}}"

# ============================================================================
# Get Scaling Input
# ============================================================================

echo ""
if [ $# -eq 2 ]; then
    # Command line arguments provided
    SERVICE_NAME="$1"
    REPLICAS="$2"
else
    # Interactive mode
    read -p "Enter service name to scale (e.g., web, celery_worker): " SERVICE_NAME
    read -p "Enter desired number of replicas: " REPLICAS
fi

# Validate replicas is a number
if ! [[ "$REPLICAS" =~ ^[0-9]+$ ]]; then
    log_error "Replicas must be a positive number"
    exit 1
fi

# Determine full service name
if docker service ls --format "{{.Name}}" | grep -q "^${SERVICE_NAME}$"; then
    FULL_SERVICE_NAME="$SERVICE_NAME"
elif docker service ls --format "{{.Name}}" | grep -q "^${STACK_NAME}_${SERVICE_NAME}$"; then
    FULL_SERVICE_NAME="${STACK_NAME}_${SERVICE_NAME}"
else
    log_error "Service not found: $SERVICE_NAME"
    exit 1
fi

# ============================================================================
# Scale Service
# ============================================================================

log_info "Scaling $FULL_SERVICE_NAME to $REPLICAS replicas..."

docker service scale "$FULL_SERVICE_NAME=$REPLICAS"

log_success "Service scaled successfully"

# ============================================================================
# Monitor Scaling Progress
# ============================================================================

echo ""
log_info "Waiting for scaling to complete..."
sleep 3

# Show current status
echo ""
log_info "Current status:"
docker service ps "$FULL_SERVICE_NAME" --filter "desired-state=running"

echo ""
log_info "Service details:"
docker service ls --filter "name=$FULL_SERVICE_NAME"

# ============================================================================
# Recommendations
# ============================================================================

echo ""
log_info "Scaling recommendations:"
echo "  Web service (web):           3-5 replicas for high availability"
echo "  Celery workers (celery_worker): Scale based on workload (2-10)"
echo "  Database (db):               Keep at 1 (single instance)"
echo "  Redis (redis):               Keep at 1 (or use Redis Cluster)"
echo "  Celery beat (celery_beat):   Keep at 1 (scheduler)"
echo ""
log_warning "Note: Scaling stateful services (db, redis) requires special configuration"

