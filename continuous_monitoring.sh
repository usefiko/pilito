#!/bin/bash

# ============================================================================
# Continuous Monitoring Script for Docker Swarm
# ============================================================================
# This script provides real-time monitoring of the Docker Swarm cluster
# and automatically runs health checks at specified intervals.
# ============================================================================

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
STACK_NAME="pilito"
REFRESH_INTERVAL=5  # seconds
HEALTH_CHECK_INTERVAL=60  # seconds

# Counter for health checks
HEALTH_CHECK_COUNTER=0

# Logging functions
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
# Display Header
# ============================================================================

display_header() {
    clear
    echo -e "${CYAN}═══════════════════════════════════════════════════════════════${NC}"
    echo -e "${CYAN}  DOCKER SWARM CONTINUOUS MONITORING - Stack: $STACK_NAME${NC}"
    echo -e "${CYAN}  $(date)${NC}"
    echo -e "${CYAN}═══════════════════════════════════════════════════════════════${NC}"
    echo ""
}

# ============================================================================
# Display Services Status
# ============================================================================

display_services() {
    echo -e "${BLUE}Services Status:${NC}"
    echo "-------------------------------------------------------------------"
    docker stack services "$STACK_NAME" --format "table {{.Name}}\t{{.Replicas}}\t{{.Image}}" 2>/dev/null || echo "Stack not deployed"
    echo ""
}

# ============================================================================
# Display Recent Tasks
# ============================================================================

display_tasks() {
    echo -e "${BLUE}Recent Tasks (Running):${NC}"
    echo "-------------------------------------------------------------------"
    docker stack ps "$STACK_NAME" \
        --filter "desired-state=running" \
        --format "table {{.Name}}\t{{.Node}}\t{{.CurrentState}}" \
        --no-trunc 2>/dev/null | head -n 11 || echo "No tasks found"
    echo ""
}

# ============================================================================
# Display Failed Tasks
# ============================================================================

display_failed_tasks() {
    local FAILED_COUNT=$(docker stack ps "$STACK_NAME" \
        --filter "desired-state=shutdown" \
        --filter "current-state=failed" \
        -q 2>/dev/null | wc -l | tr -d ' ')
    
    if [ "$FAILED_COUNT" -gt 0 ]; then
        echo -e "${RED}Failed Tasks ($FAILED_COUNT):${NC}"
        echo "-------------------------------------------------------------------"
        docker stack ps "$STACK_NAME" \
            --filter "desired-state=shutdown" \
            --filter "current-state=failed" \
            --format "table {{.Name}}\t{{.Error}}" \
            --no-trunc 2>/dev/null | head -n 6
        echo ""
    fi
}

# ============================================================================
# Display Resource Usage
# ============================================================================

display_resources() {
    echo -e "${BLUE}Node Status:${NC}"
    echo "-------------------------------------------------------------------"
    docker node ls 2>/dev/null || echo "Unable to fetch nodes"
    echo ""
}

# ============================================================================
# Display Quick Stats
# ============================================================================

display_stats() {
    local TOTAL_SERVICES=$(docker stack services "$STACK_NAME" -q 2>/dev/null | wc -l | tr -d ' ')
    local RUNNING_TASKS=$(docker stack ps "$STACK_NAME" --filter "desired-state=running" -q 2>/dev/null | wc -l | tr -d ' ')
    local FAILED_TASKS=$(docker stack ps "$STACK_NAME" --filter "desired-state=shutdown" --filter "current-state=failed" -q 2>/dev/null | wc -l | tr -d ' ')
    
    echo -e "${BLUE}Quick Statistics:${NC}"
    echo "-------------------------------------------------------------------"
    echo "Total Services:    $TOTAL_SERVICES"
    echo "Running Tasks:     $RUNNING_TASKS"
    echo "Failed Tasks:      $FAILED_TASKS"
    echo ""
}

# ============================================================================
# Display Health Status
# ============================================================================

display_health() {
    echo -e "${BLUE}Health Checks:${NC}"
    echo "-------------------------------------------------------------------"
    
    # Check web endpoint
    if curl -sf http://localhost:8000/health/ >/dev/null 2>&1; then
        echo -e "${GREEN}✓${NC} Web Service:    Healthy"
    else
        echo -e "${RED}✗${NC} Web Service:    Unhealthy"
    fi
    
    # Check Prometheus
    if curl -sf http://localhost:9090/-/healthy >/dev/null 2>&1; then
        echo -e "${GREEN}✓${NC} Prometheus:     Healthy"
    else
        echo -e "${RED}✗${NC} Prometheus:     Unhealthy"
    fi
    
    # Check Grafana
    if curl -sf http://localhost:3001/api/health >/dev/null 2>&1; then
        echo -e "${GREEN}✓${NC} Grafana:        Healthy"
    else
        echo -e "${RED}✗${NC} Grafana:        Unhealthy"
    fi
    
    echo ""
}

# ============================================================================
# Display Controls
# ============================================================================

display_controls() {
    echo -e "${CYAN}Controls:${NC}"
    echo "  Press Ctrl+C to exit"
    echo "  Refresh interval: ${REFRESH_INTERVAL}s"
    echo "  Next full health check in: $((HEALTH_CHECK_INTERVAL - (HEALTH_CHECK_COUNTER * REFRESH_INTERVAL)))s"
}

# ============================================================================
# Run Full Health Check
# ============================================================================

run_health_check() {
    echo ""
    log_info "Running comprehensive health check..."
    
    if [ -x "./health_check_services.sh" ]; then
        ./health_check_services.sh
        echo ""
        read -p "Press Enter to continue monitoring..." -t 10 || true
    else
        log_warning "Health check script not found or not executable"
    fi
}

# ============================================================================
# Main Monitoring Loop
# ============================================================================

# Check if in swarm mode
if ! docker info 2>/dev/null | grep -q "Swarm: active"; then
    log_error "Docker Swarm is not initialized"
    exit 1
fi

# Check if stack exists
if ! docker stack ls --format "{{.Name}}" | grep -q "^$STACK_NAME$"; then
    log_error "Stack '$STACK_NAME' is not deployed"
    exit 1
fi

log_info "Starting continuous monitoring..."
sleep 2

# Main loop
while true; do
    display_header
    display_services
    display_tasks
    display_failed_tasks
    display_resources
    display_stats
    display_health
    display_controls
    
    # Increment counter
    HEALTH_CHECK_COUNTER=$((HEALTH_CHECK_COUNTER + 1))
    
    # Run full health check at intervals
    if [ $((HEALTH_CHECK_COUNTER * REFRESH_INTERVAL)) -ge "$HEALTH_CHECK_INTERVAL" ]; then
        run_health_check
        HEALTH_CHECK_COUNTER=0
    fi
    
    # Wait before next refresh
    sleep "$REFRESH_INTERVAL"
done

