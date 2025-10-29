#!/bin/bash

# Quick script to view logs of all Swarm services

STACK_NAME="pilito"

# Colors
BLUE='\033[0;34m'
NC='\033[0m'

if [ $# -eq 0 ]; then
    echo "Usage: $0 <service_name> [lines]"
    echo ""
    echo "Available services:"
    docker stack services "$STACK_NAME" --format "  - {{.Name}}" | sed "s/${STACK_NAME}_//"
    echo ""
    echo "Examples:"
    echo "  $0 web            # Show last 50 lines of web service"
    echo "  $0 web 100        # Show last 100 lines of web service"
    echo "  $0 celery_beat    # Show celery_beat logs"
    echo ""
    exit 1
fi

SERVICE="$1"
LINES="${2:-50}"

# Remove stack prefix if provided
SERVICE="${SERVICE#${STACK_NAME}_}"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}📋 Logs for ${STACK_NAME}_${SERVICE}${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Check if service exists
if ! docker service ls --format "{{.Name}}" | grep -q "^${STACK_NAME}_${SERVICE}$"; then
    echo "❌ Service '${STACK_NAME}_${SERVICE}' not found"
    echo ""
    echo "Available services:"
    docker stack services "$STACK_NAME" --format "  - {{.Name}}"
    exit 1
fi

# Show logs
docker service logs "${STACK_NAME}_${SERVICE}" --tail "$LINES" --timestamps

echo ""
echo "To follow logs in real-time, run:"
echo "  docker service logs -f ${STACK_NAME}_${SERVICE}"

