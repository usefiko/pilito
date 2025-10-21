#!/bin/bash

# ============================================================================
# Service Health Check Script
# ============================================================================
# This script performs comprehensive health checks on all services in the
# Docker Swarm stack and reports their status.
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
HEALTH_TIMEOUT=5

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

# Health check counter
TOTAL_CHECKS=0
PASSED_CHECKS=0
FAILED_CHECKS=0

# ============================================================================
# Helper Functions
# ============================================================================

check_http_endpoint() {
    local name=$1
    local url=$2
    local expected_code=${3:-200}
    
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
    
    response=$(curl -s -o /dev/null -w "%{http_code}" --max-time "$HEALTH_TIMEOUT" "$url" 2>/dev/null || echo "000")
    
    if [ "$response" = "$expected_code" ]; then
        log_success "$name: HTTP $response"
        PASSED_CHECKS=$((PASSED_CHECKS + 1))
        return 0
    else
        log_error "$name: HTTP $response (expected $expected_code)"
        FAILED_CHECKS=$((FAILED_CHECKS + 1))
        return 1
    fi
}

check_tcp_port() {
    local name=$1
    local host=$2
    local port=$3
    
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
    
    if nc -z -w "$HEALTH_TIMEOUT" "$host" "$port" 2>/dev/null; then
        log_success "$name: Port $port is open"
        PASSED_CHECKS=$((PASSED_CHECKS + 1))
        return 0
    else
        log_error "$name: Port $port is not accessible"
        FAILED_CHECKS=$((FAILED_CHECKS + 1))
        return 1
    fi
}

check_docker_service() {
    local service=$1
    
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
    
    if docker service ls --filter "name=$service" --format "{{.Replicas}}" | grep -q "/"; then
        local replicas=$(docker service ls --filter "name=$service" --format "{{.Replicas}}")
        local current=$(echo "$replicas" | cut -d'/' -f1)
        local desired=$(echo "$replicas" | cut -d'/' -f2)
        
        if [ "$current" = "$desired" ] && [ "$current" != "0" ]; then
            log_success "Service $service: $replicas replicas"
            PASSED_CHECKS=$((PASSED_CHECKS + 1))
            return 0
        else
            log_warning "Service $service: $replicas replicas (not fully ready)"
            FAILED_CHECKS=$((FAILED_CHECKS + 1))
            return 1
        fi
    else
        log_error "Service $service: not found"
        FAILED_CHECKS=$((FAILED_CHECKS + 1))
        return 1
    fi
}

# ============================================================================
# Main Health Checks
# ============================================================================

print_header "DOCKER SWARM HEALTH CHECK REPORT"
echo "Timestamp: $(date)"
echo "Stack: $STACK_NAME"

# ============================================================================
# Check Swarm Status
# ============================================================================

print_header "1. DOCKER SWARM STATUS"

if docker info 2>/dev/null | grep -q "Swarm: active"; then
    log_success "Docker Swarm is active"
    PASSED_CHECKS=$((PASSED_CHECKS + 1))
else
    log_error "Docker Swarm is not initialized"
    FAILED_CHECKS=$((FAILED_CHECKS + 1))
    exit 1
fi
TOTAL_CHECKS=$((TOTAL_CHECKS + 1))

# ============================================================================
# Check Stack Deployment
# ============================================================================

print_header "2. STACK DEPLOYMENT STATUS"

if docker stack ls --format "{{.Name}}" | grep -q "^$STACK_NAME$"; then
    log_success "Stack '$STACK_NAME' is deployed"
    PASSED_CHECKS=$((PASSED_CHECKS + 1))
else
    log_error "Stack '$STACK_NAME' is not deployed"
    FAILED_CHECKS=$((FAILED_CHECKS + 1))
    exit 1
fi
TOTAL_CHECKS=$((TOTAL_CHECKS + 1))

# ============================================================================
# Check Service Replicas
# ============================================================================

print_header "3. SERVICE REPLICA STATUS"

check_docker_service "${STACK_NAME}_web"
check_docker_service "${STACK_NAME}_db"
check_docker_service "${STACK_NAME}_redis"
check_docker_service "${STACK_NAME}_celery_worker"
check_docker_service "${STACK_NAME}_celery_beat"
check_docker_service "${STACK_NAME}_prometheus"
check_docker_service "${STACK_NAME}_grafana"

# ============================================================================
# Check HTTP Endpoints
# ============================================================================

print_header "4. HTTP ENDPOINT HEALTH CHECKS"

log_info "Checking web application..."
check_http_endpoint "Django Health" "http://localhost:8000/health/" 200

log_info "Checking Prometheus..."
check_http_endpoint "Prometheus" "http://localhost:9090/-/healthy" 200

log_info "Checking Grafana..."
check_http_endpoint "Grafana Health" "http://localhost:3001/api/health" 200

log_info "Checking metrics endpoints..."
check_http_endpoint "Redis Exporter" "http://localhost:9121/metrics" 200
check_http_endpoint "Postgres Exporter" "http://localhost:9187/metrics" 200
check_http_endpoint "Celery Metrics" "http://localhost:9808/metrics" 200

# ============================================================================
# Check TCP Ports
# ============================================================================

print_header "5. TCP PORT ACCESSIBILITY"

log_info "Checking critical ports..."
check_tcp_port "Web Service" "localhost" 8000
check_tcp_port "Redis" "localhost" 6379
check_tcp_port "Prometheus" "localhost" 9090
check_tcp_port "Grafana" "localhost" 3001

# ============================================================================
# Check Database Connectivity
# ============================================================================

print_header "6. DATABASE CONNECTIVITY"

log_info "Testing PostgreSQL connection..."
TOTAL_CHECKS=$((TOTAL_CHECKS + 1))

# Get database credentials from .env
if [ -f .env ]; then
    source .env
    
    # Test database connection via Docker
    if docker exec $(docker ps -q -f "name=${STACK_NAME}_db" | head -n 1) pg_isready -U "$POSTGRES_USER" -d "$POSTGRES_DB" >/dev/null 2>&1; then
        log_success "PostgreSQL is accepting connections"
        PASSED_CHECKS=$((PASSED_CHECKS + 1))
    else
        log_error "PostgreSQL is not accepting connections"
        FAILED_CHECKS=$((FAILED_CHECKS + 1))
    fi
else
    log_warning "Cannot test database connection (.env not found)"
fi

# ============================================================================
# Check Redis
# ============================================================================

print_header "7. REDIS CONNECTIVITY"

log_info "Testing Redis connection..."
TOTAL_CHECKS=$((TOTAL_CHECKS + 1))

if docker exec $(docker ps -q -f "name=${STACK_NAME}_redis" | head -n 1) redis-cli ping >/dev/null 2>&1; then
    log_success "Redis is responding to PING"
    PASSED_CHECKS=$((PASSED_CHECKS + 1))
else
    log_error "Redis is not responding"
    FAILED_CHECKS=$((FAILED_CHECKS + 1))
fi

# ============================================================================
# Check for Failed Tasks
# ============================================================================

print_header "8. FAILED TASKS CHECK"

TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
FAILED_TASKS=$(docker stack ps "$STACK_NAME" --filter "desired-state=shutdown" --filter "current-state=failed" -q 2>/dev/null | wc -l | tr -d ' ')

if [ "$FAILED_TASKS" -eq 0 ]; then
    log_success "No failed tasks found"
    PASSED_CHECKS=$((PASSED_CHECKS + 1))
else
    log_warning "Found $FAILED_TASKS failed tasks"
    FAILED_CHECKS=$((FAILED_CHECKS + 1))
    
    echo ""
    log_info "Recent failed tasks:"
    docker stack ps "$STACK_NAME" \
        --filter "desired-state=shutdown" \
        --filter "current-state=failed" \
        --format "table {{.Name}}\t{{.Node}}\t{{.Error}}" \
        --no-trunc | head -n 6
fi

# ============================================================================
# Node Health
# ============================================================================

print_header "9. NODE HEALTH STATUS"

TOTAL_CHECKS=$((TOTAL_CHECKS + 1))

UNHEALTHY_NODES=$(docker node ls --filter "availability=active" --format "{{.Status}}" | grep -cv "Ready" || echo "0")

if [ "$UNHEALTHY_NODES" -eq 0 ]; then
    log_success "All nodes are healthy"
    PASSED_CHECKS=$((PASSED_CHECKS + 1))
else
    log_warning "$UNHEALTHY_NODES node(s) are not ready"
    FAILED_CHECKS=$((FAILED_CHECKS + 1))
    docker node ls
fi

# ============================================================================
# Summary Report
# ============================================================================

print_header "HEALTH CHECK SUMMARY"

echo "Total Checks:   $TOTAL_CHECKS"
echo "Passed:         $PASSED_CHECKS"
echo "Failed:         $FAILED_CHECKS"

HEALTH_PERCENTAGE=$((PASSED_CHECKS * 100 / TOTAL_CHECKS))
echo "Health Score:   $HEALTH_PERCENTAGE%"
echo ""

if [ "$FAILED_CHECKS" -eq 0 ]; then
    log_success "═══════════════════════════════════════════════════════════════"
    log_success "  ALL HEALTH CHECKS PASSED - SYSTEM IS HEALTHY"
    log_success "═══════════════════════════════════════════════════════════════"
    exit 0
elif [ "$HEALTH_PERCENTAGE" -ge 80 ]; then
    log_warning "═══════════════════════════════════════════════════════════════"
    log_warning "  SYSTEM IS MOSTLY HEALTHY ($HEALTH_PERCENTAGE%)"
    log_warning "  Some non-critical checks failed"
    log_warning "═══════════════════════════════════════════════════════════════"
    exit 0
else
    log_error "═══════════════════════════════════════════════════════════════"
    log_error "  SYSTEM HEALTH ISSUES DETECTED ($HEALTH_PERCENTAGE%)"
    log_error "  Immediate attention required"
    log_error "═══════════════════════════════════════════════════════════════"
    exit 1
fi

