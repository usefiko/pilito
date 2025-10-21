#!/bin/bash

# ============================================================================
# Docker Swarm Status Monitoring Script
# ============================================================================
# This script provides comprehensive status information about the Docker
# Swarm cluster and deployed services.
# ============================================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
STACK_NAME="pilito"

# Logging functions
print_header() {
    echo ""
    echo -e "${CYAN}═══════════════════════════════════════════════════════════════${NC}"
    echo -e "${CYAN}  $1${NC}"
    echo -e "${CYAN}═══════════════════════════════════════════════════════════════${NC}"
    echo ""
}

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[✓]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

log_error() {
    echo -e "${RED}[✗]${NC} $1"
}

# ============================================================================
# Check Swarm Status
# ============================================================================

print_header "DOCKER SWARM STATUS"

if docker info 2>/dev/null | grep -q "Swarm: active"; then
    log_success "Docker Swarm is ACTIVE"
else
    log_error "Docker Swarm is NOT initialized"
    exit 1
fi

# ============================================================================
# Cluster Nodes
# ============================================================================

print_header "CLUSTER NODES"
docker node ls

# Count nodes
MANAGER_COUNT=$(docker node ls --filter "role=manager" -q | wc -l | tr -d ' ')
WORKER_COUNT=$(docker node ls --filter "role=worker" -q | wc -l | tr -d ' ')
TOTAL_NODES=$(docker node ls -q | wc -l | tr -d ' ')

echo ""
log_info "Total Nodes: $TOTAL_NODES (Managers: $MANAGER_COUNT, Workers: $WORKER_COUNT)"

# ============================================================================
# Stack Status
# ============================================================================

print_header "DEPLOYED STACKS"
docker stack ls

# ============================================================================
# Services Status
# ============================================================================

if docker stack ls --format "{{.Name}}" | grep -q "^$STACK_NAME$"; then
    print_header "SERVICES STATUS - Stack: $STACK_NAME"
    docker stack services "$STACK_NAME"
    
    # ============================================================================
    # Service Health Summary
    # ============================================================================
    
    print_header "SERVICE HEALTH SUMMARY"
    
    # Get all services
    SERVICES=$(docker stack services "$STACK_NAME" --format "{{.Name}}")
    
    for SERVICE in $SERVICES; do
        REPLICAS=$(docker service ls --filter "name=$SERVICE" --format "{{.Replicas}}")
        echo -e "${BLUE}Service:${NC} $SERVICE - ${GREEN}Replicas:${NC} $REPLICAS"
    done
    
    # ============================================================================
    # Tasks Status
    # ============================================================================
    
    print_header "TASKS STATUS (Running)"
    docker stack ps "$STACK_NAME" --filter "desired-state=running" --format "table {{.Name}}\t{{.Node}}\t{{.CurrentState}}\t{{.Error}}"
    
    # Check for failed tasks
    FAILED_TASKS=$(docker stack ps "$STACK_NAME" --filter "desired-state=shutdown" --filter "current-state=failed" -q | wc -l | tr -d ' ')
    
    if [ "$FAILED_TASKS" -gt 0 ]; then
        echo ""
        log_warning "Found $FAILED_TASKS failed tasks"
        echo ""
        log_info "Failed Tasks:"
        docker stack ps "$STACK_NAME" --filter "desired-state=shutdown" --filter "current-state=failed" --format "table {{.Name}}\t{{.Node}}\t{{.CurrentState}}\t{{.Error}}" | head -n 10
    fi
    
else
    log_warning "Stack '$STACK_NAME' is not deployed"
fi

# ============================================================================
# Networks
# ============================================================================

print_header "OVERLAY NETWORKS"
docker network ls --filter "driver=overlay" --format "table {{.Name}}\t{{.Driver}}\t{{.Scope}}"

# ============================================================================
# Volumes
# ============================================================================

print_header "VOLUMES"
docker volume ls --filter "label=com.docker.stack.namespace=$STACK_NAME" --format "table {{.Name}}\t{{.Driver}}\t{{.Scope}}" 2>/dev/null || docker volume ls --format "table {{.Name}}\t{{.Driver}}\t{{.Scope}}"

# ============================================================================
# Resource Usage
# ============================================================================

print_header "RESOURCE USAGE BY NODE"

for NODE in $(docker node ls --format "{{.Hostname}}"); do
    echo ""
    echo -e "${GREEN}Node:${NC} $NODE"
    echo "-------------------"
    
    # Get node role
    ROLE=$(docker node inspect "$NODE" --format "{{.Spec.Role}}")
    STATUS=$(docker node inspect "$NODE" --format "{{.Status.State}}")
    AVAILABILITY=$(docker node inspect "$NODE" --format "{{.Spec.Availability}}")
    
    echo "Role: $ROLE | Status: $STATUS | Availability: $AVAILABILITY"
    
    # Count running tasks on this node
    TASK_COUNT=$(docker node ps "$NODE" --filter "desired-state=running" -q | wc -l | tr -d ' ')
    echo "Running Tasks: $TASK_COUNT"
done

# ============================================================================
# Health Check Endpoints
# ============================================================================

if docker stack ls --format "{{.Name}}" | grep -q "^$STACK_NAME$"; then
    print_header "HEALTH CHECK ENDPOINTS"
    
    echo "Web Application:    http://localhost:8000/health/"
    echo "Prometheus:         http://localhost:9090/-/healthy"
    echo "Grafana:            http://localhost:3001/api/health"
    echo ""
    
    log_info "Testing web health endpoint..."
    if curl -sf http://localhost:8000/health/ > /dev/null 2>&1; then
        log_success "Web service is healthy"
    else
        log_error "Web service health check failed"
    fi
fi

# ============================================================================
# Quick Stats
# ============================================================================

print_header "QUICK STATS"

if docker stack ls --format "{{.Name}}" | grep -q "^$STACK_NAME$"; then
    TOTAL_SERVICES=$(docker stack services "$STACK_NAME" -q | wc -l | tr -d ' ')
    RUNNING_TASKS=$(docker stack ps "$STACK_NAME" --filter "desired-state=running" -q | wc -l | tr -d ' ')
    
    echo "Total Services:     $TOTAL_SERVICES"
    echo "Running Tasks:      $RUNNING_TASKS"
    echo "Cluster Nodes:      $TOTAL_NODES"
    echo "Failed Tasks:       $FAILED_TASKS"
fi

# ============================================================================
# Useful Commands
# ============================================================================

print_header "USEFUL COMMANDS"

echo "View service logs:       docker service logs -f ${STACK_NAME}_web"
echo "Scale service:           ./swarm_scale.sh web 5"
echo "Update service:          ./swarm_update.sh"
echo "Rollback service:        ./swarm_rollback.sh web"
echo "Remove stack:            docker stack rm $STACK_NAME"
echo "Continuous monitoring:   watch -n 2 './swarm_status.sh'"

echo ""

