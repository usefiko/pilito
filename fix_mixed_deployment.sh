#!/bin/bash

# Script to fix mixed Docker Compose and Swarm deployment
# This script will clean up Docker Compose containers and properly deploy via Swarm

set -e  # Exit on error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
STACK_NAME="pilito"
COMPOSE_FILE="docker-compose.swarm.yml"

echo "=================================================="
echo "🔧 Fixing Mixed Docker Compose and Swarm Deployment"
echo "=================================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Step 1: Check current state
print_status "Step 1: Checking current deployment state..."
echo ""

echo "📊 Current Docker Containers:"
docker ps --format "table {{.Names}}\t{{.Image}}\t{{.Status}}" || true
echo ""

echo "📊 Current Swarm Stacks:"
docker stack ls || print_warning "No Swarm stacks found"
echo ""

echo "📊 Current Swarm Services:"
docker service ls || print_warning "No Swarm services found"
echo ""

# Step 2: Stop Docker Compose containers
print_status "Step 2: Stopping Docker Compose containers..."
echo ""

if [ -f "$SCRIPT_DIR/docker-compose.yml" ]; then
    print_status "Found docker-compose.yml, stopping containers..."
    cd "$SCRIPT_DIR"
    docker-compose down 2>/dev/null || print_warning "No Docker Compose containers to stop"
    print_success "Docker Compose containers stopped"
else
    print_warning "No docker-compose.yml found, skipping..."
fi
echo ""

# Step 3: Remove existing Swarm stack
print_status "Step 3: Removing existing Swarm stack (if any)..."
echo ""

if docker stack ls | grep -q "$STACK_NAME"; then
    print_status "Found existing stack '$STACK_NAME', removing..."
    docker stack rm "$STACK_NAME"
    print_success "Stack removal initiated"
else
    print_warning "No existing stack found"
fi
echo ""

# Step 4: Wait for cleanup
print_status "Step 4: Waiting for cleanup to complete..."
echo ""

print_status "Waiting 15 seconds for containers to stop..."
sleep 15

# Check if any containers are still running
REMAINING_CONTAINERS=$(docker ps -a --filter "name=${STACK_NAME}" --format "{{.Names}}" | wc -l)
if [ "$REMAINING_CONTAINERS" -gt 0 ]; then
    print_warning "Some containers are still cleaning up, waiting another 15 seconds..."
    sleep 15
fi

print_success "Cleanup complete"
echo ""

# Step 5: Verify cleanup
print_status "Step 5: Verifying cleanup..."
echo ""

REMAINING=$(docker ps -a --format "table {{.Names}}\t{{.Image}}\t{{.Status}}")
if echo "$REMAINING" | grep -q "$STACK_NAME\|celery\|postgres\|redis\|grafana\|prometheus"; then
    print_warning "Some containers are still present:"
    echo "$REMAINING"
    echo ""
    read -p "Do you want to force remove them? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_status "Force removing remaining containers..."
        docker ps -a --filter "name=${STACK_NAME}" -q | xargs -r docker rm -f
        docker ps -a --filter "name=celery" -q | xargs -r docker rm -f
        docker ps -a --filter "name=postgres" -q | xargs -r docker rm -f
        docker ps -a --filter "name=redis" -q | xargs -r docker rm -f
        docker ps -a --filter "name=grafana" -q | xargs -r docker rm -f
        docker ps -a --filter "name=prometheus" -q | xargs -r docker rm -f
        print_success "Forced removal complete"
    fi
else
    print_success "No conflicting containers found"
fi
echo ""

# Step 6: Check Swarm status
print_status "Step 6: Checking Docker Swarm status..."
echo ""

if ! docker info | grep -q "Swarm: active"; then
    print_error "Docker Swarm is not active!"
    print_status "Initializing Docker Swarm..."
    docker swarm init || print_error "Failed to initialize Swarm"
    print_success "Docker Swarm initialized"
else
    print_success "Docker Swarm is active"
fi
echo ""

# Step 7: Build the Docker image
print_status "Step 7: Building Docker image..."
echo ""

cd "$SCRIPT_DIR"
if [ -f "Dockerfile" ]; then
    print_status "Building pilito_web:latest image..."
    docker build -t pilito_web:latest . || {
        print_error "Failed to build Docker image"
        exit 1
    }
    print_success "Docker image built successfully"
else
    print_error "Dockerfile not found!"
    exit 1
fi
echo ""

# Step 8: Deploy Swarm stack
print_status "Step 8: Deploying Swarm stack..."
echo ""

if [ ! -f "$SCRIPT_DIR/$COMPOSE_FILE" ]; then
    print_error "Compose file not found: $COMPOSE_FILE"
    exit 1
fi

cd "$SCRIPT_DIR"
print_status "Deploying stack '$STACK_NAME' from $COMPOSE_FILE..."
docker stack deploy -c "$COMPOSE_FILE" "$STACK_NAME" || {
    print_error "Failed to deploy stack"
    exit 1
}
print_success "Stack deployment initiated"
echo ""

# Step 9: Monitor deployment
print_status "Step 9: Monitoring deployment progress..."
echo ""

print_status "Waiting for services to start (30 seconds)..."
sleep 30

echo ""
echo "=================================================="
echo "📊 Current Stack Status"
echo "=================================================="
echo ""

echo "🔹 Services:"
docker stack services "$STACK_NAME"
echo ""

echo "🔹 Service Tasks:"
docker stack ps "$STACK_NAME" --no-trunc
echo ""

echo "🔹 Networks:"
docker network ls | grep pilito || true
echo ""

# Step 10: Health checks
print_status "Step 10: Checking service health..."
echo ""

# Wait a bit more for health checks to run
print_status "Waiting 30 more seconds for health checks..."
sleep 30

echo "🔹 Service Status:"
docker service ls --filter "name=${STACK_NAME}" --format "table {{.Name}}\t{{.Mode}}\t{{.Replicas}}\t{{.Image}}"
echo ""

# Check for any failed services
FAILED_SERVICES=$(docker stack ps "$STACK_NAME" --format "{{.Name}}\t{{.CurrentState}}" | grep -i "failed\|rejected" || true)
if [ -n "$FAILED_SERVICES" ]; then
    print_warning "Some services failed to start:"
    echo "$FAILED_SERVICES"
    echo ""
    print_status "Checking logs of failed services..."
    docker stack ps "$STACK_NAME" --filter "desired-state=running" --format "{{.Name}}" | while read service; do
        print_status "Logs for $service:"
        docker service logs "${STACK_NAME}_${service}" --tail 50 || true
        echo ""
    done
else
    print_success "All services are running or starting"
fi

echo ""
echo "=================================================="
echo "✅ Deployment Complete!"
echo "=================================================="
echo ""
print_success "Stack deployed successfully!"
echo ""
echo "📝 Next steps:"
echo "  1. Monitor services: docker stack ps $STACK_NAME"
echo "  2. Check logs: docker service logs ${STACK_NAME}_<service_name>"
echo "  3. Scale services: docker service scale ${STACK_NAME}_web=3"
echo "  4. View stack status: docker stack services $STACK_NAME"
echo ""
echo "🌐 Service URLs:"
echo "  - Web App: http://localhost:8000"
echo "  - Grafana: http://localhost:3001"
echo "  - Prometheus: http://localhost:9090"
echo "  - Redis: localhost:6379"
echo ""
echo "📊 Useful commands:"
echo "  - Watch status: watch -n 2 'docker stack ps $STACK_NAME'"
echo "  - Remove stack: docker stack rm $STACK_NAME"
echo "  - View logs: docker service logs -f ${STACK_NAME}_web"
echo ""

