#!/bin/bash

# ============================================================================
# Docker Swarm Stack Deployment Script
# ============================================================================
# This script deploys the Pilito application stack to Docker Swarm with
# proper health checks and high availability configurations.
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
# Pre-deployment Checks
# ============================================================================

log_info "Running pre-deployment checks..."

# Check if Swarm is active
if ! docker info 2>/dev/null | grep -q "Swarm: active"; then
    log_error "Docker Swarm is not initialized. Run ./swarm_init.sh first."
    exit 1
fi

# Check if compose file exists
if [ ! -f "$COMPOSE_FILE" ]; then
    log_error "Compose file '$COMPOSE_FILE' not found."
    exit 1
fi

# Check if .env file exists
if [ ! -f .env ]; then
    log_error ".env file not found. Please create it from .env.example"
    exit 1
fi

log_success "Pre-deployment checks passed"

# ============================================================================
# Build Updated Images
# ============================================================================

log_info "Building latest Docker images..."
docker-compose -f "$COMPOSE_FILE" build
log_success "Images built successfully"

# ============================================================================
# Deploy Stack
# ============================================================================

log_info "Deploying stack '$STACK_NAME'..."

# Deploy the stack
docker stack deploy \
    --compose-file "$COMPOSE_FILE" \
    --with-registry-auth \
    "$STACK_NAME"

log_success "Stack deployed successfully"

# ============================================================================
# Wait for Services to Start
# ============================================================================

log_info "Waiting for services to start..."
sleep 5

# ============================================================================
# Display Stack Status
# ============================================================================

echo ""
log_info "Stack Services Status:"
docker stack services "$STACK_NAME"

echo ""
log_info "Service Tasks Status:"
docker stack ps "$STACK_NAME" --no-trunc

# ============================================================================
# Health Check Status
# ============================================================================

log_info "Checking service health..."
sleep 10

echo ""
log_info "Service Replicas Status:"
docker service ls --filter "label=com.docker.stack.namespace=$STACK_NAME"

# ============================================================================
# Monitoring Commands
# ============================================================================

echo ""
log_success "Deployment complete!"
echo ""
log_info "Useful commands:"
echo "  View services:           docker stack services $STACK_NAME"
echo "  View service logs:       docker service logs -f ${STACK_NAME}_web"
echo "  View service tasks:      docker stack ps $STACK_NAME"
echo "  Scale a service:         docker service scale ${STACK_NAME}_web=5"
echo "  Update service:          docker service update ${STACK_NAME}_web"
echo "  Remove stack:            docker stack rm $STACK_NAME"
echo ""
log_info "Access points:"
echo "  Django API:              http://localhost:8000"
echo "  Prometheus:              http://localhost:9090"
echo "  Grafana:                 http://localhost:3001"
echo "  Health Check:            http://localhost:8000/health/"
echo ""
log_info "Monitor deployment progress:"
echo "  watch -n 1 'docker stack ps $STACK_NAME'"

