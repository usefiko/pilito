#!/bin/bash

# Quick monitoring script for Swarm deployment

STACK_NAME="pilito"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_header() {
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}"
}

clear

print_header "📊 Pilito Swarm Stack Status"
echo ""

# Check if stack exists
if ! docker stack ls | grep -q "$STACK_NAME"; then
    echo -e "${RED}❌ Stack '$STACK_NAME' is not deployed${NC}"
    echo ""
    echo "To deploy, run:"
    echo "  ./fix_mixed_deployment.sh"
    exit 1
fi

# Services overview
print_header "🔹 Services"
docker stack services "$STACK_NAME" --format "table {{.Name}}\t{{.Mode}}\t{{.Replicas}}\t{{.Image}}" 2>/dev/null || echo "No services found"
echo ""

# Task status
print_header "🔹 Tasks Status"
docker stack ps "$STACK_NAME" --format "table {{.Name}}\t{{.CurrentState}}\t{{.Error}}" --no-trunc 2>/dev/null || echo "No tasks found"
echo ""

# Check for failures
FAILED=$(docker stack ps "$STACK_NAME" --filter "desired-state=running" --format "{{.Name}}\t{{.CurrentState}}" | grep -i "failed\|rejected" | wc -l)
if [ "$FAILED" -gt 0 ]; then
    echo -e "${RED}⚠️  $FAILED tasks have failed${NC}"
    echo ""
    print_header "❌ Failed Tasks"
    docker stack ps "$STACK_NAME" --filter "desired-state=running" --format "table {{.Name}}\t{{.CurrentState}}\t{{.Error}}" | grep -i "failed\|rejected"
    echo ""
else
    echo -e "${GREEN}✅ All tasks are healthy${NC}"
    echo ""
fi

# Network info
print_header "🌐 Networks"
docker network ls | grep pilito || echo "No pilito networks found"
echo ""

# Quick stats
print_header "📈 Quick Stats"
TOTAL_SERVICES=$(docker stack services "$STACK_NAME" 2>/dev/null | tail -n +2 | wc -l)
TOTAL_TASKS=$(docker stack ps "$STACK_NAME" --filter "desired-state=running" 2>/dev/null | tail -n +2 | wc -l)
RUNNING_TASKS=$(docker stack ps "$STACK_NAME" --filter "desired-state=running" --format "{{.CurrentState}}" 2>/dev/null | grep -i "running" | wc -l)

echo -e "Total Services: ${BLUE}$TOTAL_SERVICES${NC}"
echo -e "Total Tasks: ${BLUE}$TOTAL_TASKS${NC}"
echo -e "Running Tasks: ${GREEN}$RUNNING_TASKS${NC}"
echo ""

# Service URLs
print_header "🌐 Service URLs"
echo "  - Web App: http://localhost:8000"
echo "  - Grafana: http://localhost:3001 (admin/admin)"
echo "  - Prometheus: http://localhost:9090"
echo "  - Redis: localhost:6379"
echo ""

# Useful commands
print_header "📝 Useful Commands"
echo "  - Watch live: watch -n 2 'docker stack ps $STACK_NAME'"
echo "  - View logs: docker service logs -f ${STACK_NAME}_<service>"
echo "  - Scale web: docker service scale ${STACK_NAME}_web=3"
echo "  - Remove stack: docker stack rm $STACK_NAME"
echo "  - Re-run this: ./monitor_swarm.sh"
echo ""

# Auto-refresh option
echo -e "${YELLOW}Press Ctrl+C to exit${NC}"
echo ""
read -t 5 -p "Auto-refresh in 5 seconds... (press Enter to refresh now): " || true
exec "$0"

