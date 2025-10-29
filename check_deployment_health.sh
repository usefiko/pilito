#!/bin/bash

# Quick health check script to detect mixed deployment issues

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_header() {
    echo ""
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

clear

echo ""
echo "╔════════════════════════════════════════╗"
echo "║   🏥 Pilito Deployment Health Check   ║"
echo "╔════════════════════════════════════════╗"
echo ""

ISSUES_FOUND=0

# Check 1: Docker Compose containers
print_header "1. Checking Docker Compose Containers"

COMPOSE_CONTAINERS=$(docker ps --format "{{.Names}}" | grep -E "^(django_app|postgres_db|redis_cache|celery_worker|celery_beat|celery_ai|grafana|prometheus)$" | wc -l)

if [ "$COMPOSE_CONTAINERS" -gt 0 ]; then
    print_error "Found $COMPOSE_CONTAINERS Docker Compose containers running"
    docker ps --format "table {{.Names}}\t{{.Image}}\t{{.Status}}" | grep -E "^(django_app|postgres_db|redis_cache|celery_worker|celery_beat|celery_ai|grafana|prometheus)"
    ISSUES_FOUND=$((ISSUES_FOUND + 1))
else
    print_success "No Docker Compose containers found"
fi

# Check 2: Docker Swarm services
print_header "2. Checking Docker Swarm Services"

if docker info 2>/dev/null | grep -q "Swarm: active"; then
    print_success "Docker Swarm is active"
    
    SWARM_SERVICES=$(docker service ls 2>/dev/null | tail -n +2 | wc -l)
    if [ "$SWARM_SERVICES" -gt 0 ]; then
        print_success "Found $SWARM_SERVICES Swarm services"
        docker service ls --format "table {{.Name}}\t{{.Mode}}\t{{.Replicas}}"
    else
        print_warning "No Swarm services found"
    fi
else
    print_warning "Docker Swarm is not active"
fi

# Check 3: Mixed deployment detection
print_header "3. Mixed Deployment Detection"

if [ "$COMPOSE_CONTAINERS" -gt 0 ] && [ "$SWARM_SERVICES" -gt 0 ]; then
    print_error "MIXED DEPLOYMENT DETECTED!"
    echo ""
    echo "You have both Docker Compose containers AND Swarm services running."
    echo "This causes network isolation and services cannot communicate."
    echo ""
    echo "👉 Run this to fix: ./fix_mixed_deployment.sh"
    ISSUES_FOUND=$((ISSUES_FOUND + 1))
else
    print_success "No mixed deployment detected"
fi

# Check 4: Network configuration
print_header "4. Checking Networks"

PILITO_NETWORKS=$(docker network ls | grep pilito | wc -l)
if [ "$PILITO_NETWORKS" -gt 0 ]; then
    print_success "Found $PILITO_NETWORKS pilito network(s)"
    docker network ls | grep pilito
else
    print_warning "No pilito networks found"
fi

# Check 5: Failed containers/services
print_header "5. Checking for Failed Services"

# Check Docker Compose
FAILED_COMPOSE=$(docker ps -a --filter "status=exited" --filter "status=dead" --format "{{.Names}}" | grep -E "(django|postgres|redis|celery|grafana|prometheus)" | wc -l)
if [ "$FAILED_COMPOSE" -gt 0 ]; then
    print_warning "Found $FAILED_COMPOSE failed Compose container(s)"
    docker ps -a --filter "status=exited" --filter "status=dead" --format "table {{.Names}}\t{{.Status}}" | grep -E "(django|postgres|redis|celery|grafana|prometheus)"
    ISSUES_FOUND=$((ISSUES_FOUND + 1))
fi

# Check Swarm services
if [ "$SWARM_SERVICES" -gt 0 ]; then
    FAILED_SWARM=$(docker stack ps pilito 2>/dev/null | grep -i "failed\|rejected" | wc -l)
    if [ "$FAILED_SWARM" -gt 0 ]; then
        print_warning "Found $FAILED_SWARM failed Swarm task(s)"
        docker stack ps pilito --no-trunc | grep -i "failed\|rejected"
        ISSUES_FOUND=$((ISSUES_FOUND + 1))
    else
        print_success "No failed Swarm tasks"
    fi
fi

# Check 6: Port conflicts
print_header "6. Checking for Port Conflicts"

PORTS_TO_CHECK="8000 6379 5432 9090 3001"
PORT_CONFLICTS=0

for PORT in $PORTS_TO_CHECK; do
    LISTENERS=$(docker ps --format "{{.Names}}\t{{.Ports}}" | grep ":$PORT->" | wc -l)
    if [ "$LISTENERS" -gt 1 ]; then
        print_warning "Port $PORT has multiple listeners"
        docker ps --format "{{.Names}}\t{{.Ports}}" | grep ":$PORT->"
        PORT_CONFLICTS=$((PORT_CONFLICTS + 1))
    fi
done

if [ "$PORT_CONFLICTS" -eq 0 ]; then
    print_success "No port conflicts detected"
else
    ISSUES_FOUND=$((ISSUES_FOUND + 1))
fi

# Check 7: Health checks
print_header "7. Checking Container Health"

UNHEALTHY=$(docker ps --filter "health=unhealthy" --format "{{.Names}}" | wc -l)
if [ "$UNHEALTHY" -gt 0 ]; then
    print_warning "Found $UNHEALTHY unhealthy container(s)"
    docker ps --filter "health=unhealthy" --format "table {{.Names}}\t{{.Status}}\t{{.Image}}"
    ISSUES_FOUND=$((ISSUES_FOUND + 1))
else
    HEALTHY=$(docker ps --filter "health=healthy" --format "{{.Names}}" | wc -l)
    STARTING=$(docker ps --filter "health=starting" --format "{{.Names}}" | wc -l)
    
    if [ "$HEALTHY" -gt 0 ]; then
        print_success "$HEALTHY healthy container(s)"
    fi
    if [ "$STARTING" -gt 0 ]; then
        print_info "$STARTING container(s) starting up..."
    fi
fi

# Summary
print_header "📊 Health Check Summary"

echo ""
if [ "$ISSUES_FOUND" -eq 0 ]; then
    print_success "All checks passed! Your deployment looks healthy."
    echo ""
    echo "Current deployment type:"
    if [ "$COMPOSE_CONTAINERS" -gt 0 ]; then
        echo "  📦 Docker Compose ($COMPOSE_CONTAINERS containers)"
    elif [ "$SWARM_SERVICES" -gt 0 ]; then
        echo "  🐝 Docker Swarm ($SWARM_SERVICES services)"
    else
        echo "  ❓ No deployment detected"
    fi
else
    print_error "Found $ISSUES_FOUND issue(s) that need attention!"
    echo ""
    echo "🔧 Recommended actions:"
    echo ""
    
    if [ "$COMPOSE_CONTAINERS" -gt 0 ] && [ "$SWARM_SERVICES" -gt 0 ]; then
        echo "  1. Fix mixed deployment:"
        echo "     ./fix_mixed_deployment.sh"
        echo ""
    fi
    
    if [ "$FAILED_COMPOSE" -gt 0 ] || [ "$FAILED_SWARM" -gt 0 ]; then
        echo "  2. Check logs of failed services:"
        echo "     ./quick_swarm_logs.sh <service_name>"
        echo "     or"
        echo "     docker logs <container_name>"
        echo ""
    fi
    
    if [ "$PORT_CONFLICTS" -gt 0 ]; then
        echo "  3. Resolve port conflicts by stopping extra services"
        echo ""
    fi
    
    echo "  4. Monitor deployment status:"
    echo "     ./monitor_swarm.sh"
    echo ""
fi

# Show helpful commands
print_header "📝 Useful Commands"
echo ""
echo "  Monitoring:"
echo "    ./monitor_swarm.sh          # Monitor Swarm stack"
echo "    ./check_deployment_health.sh # Run this check again"
echo ""
echo "  Logs:"
echo "    ./quick_swarm_logs.sh web   # View service logs"
echo "    docker logs <container>     # View Compose logs"
echo ""
echo "  Management:"
echo "    ./fix_mixed_deployment.sh   # Fix mixed deployment"
echo "    docker stack ps pilito      # Check Swarm tasks"
echo "    docker-compose ps           # Check Compose status"
echo ""

exit $ISSUES_FOUND

