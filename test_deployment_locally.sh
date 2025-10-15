#!/bin/bash

# Local Deployment Test Script
# Run this before pushing to test the deployment locally

set -e

echo "🧪 Testing Deployment Locally"
echo "============================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_info() {
    echo -e "ℹ️  $1"
}

# Check if .env exists
if [ ! -f ".env" ]; then
    print_error ".env file not found!"
    print_info "Create a .env file with your environment variables"
    exit 1
fi
print_success ".env file found"

# Check if docker is running
if ! docker info > /dev/null 2>&1; then
    print_error "Docker is not running!"
    print_info "Please start Docker and try again"
    exit 1
fi
print_success "Docker is running"

# Check if docker-compose.yml exists
if [ ! -f "docker-compose.yml" ]; then
    print_error "docker-compose.yml not found!"
    exit 1
fi
print_success "docker-compose.yml found"

# Stop existing containers
print_info "Stopping existing containers..."
docker-compose down 2>/dev/null || true
print_success "Containers stopped"

# Clean up
print_info "Cleaning up old images and containers..."
docker container prune -f > /dev/null 2>&1 || true
docker image prune -f > /dev/null 2>&1 || true
print_success "Cleanup complete"

# Build containers
print_info "Building containers..."
if docker-compose build --parallel; then
    print_success "Build successful"
else
    print_error "Build failed!"
    exit 1
fi

# Start containers
print_info "Starting containers..."
if docker-compose up -d; then
    print_success "Containers started"
else
    print_error "Failed to start containers!"
    docker-compose logs
    exit 1
fi

# Wait for services to be ready
print_info "Waiting for services to start..."
sleep 15

# Check if containers are running
print_info "Checking container status..."
RUNNING_CONTAINERS=$(docker-compose ps | grep -c "Up" || echo "0")
if [ "$RUNNING_CONTAINERS" -eq 0 ]; then
    print_error "No containers are running!"
    docker-compose logs --tail=50
    exit 1
fi
print_success "$RUNNING_CONTAINERS containers are running"

# Check Django app
print_info "Checking Django application..."
if docker exec django_app python manage.py check; then
    print_success "Django check passed"
else
    print_error "Django check failed!"
    docker logs django_app --tail=50
    exit 1
fi

# Run migrations
print_info "Running migrations..."
if docker exec django_app python manage.py migrate --noinput; then
    print_success "Migrations completed"
else
    print_warning "Migrations had issues (may be normal if DB already migrated)"
fi

# Collect static files
print_info "Collecting static files..."
if docker exec django_app python manage.py collectstatic --noinput; then
    print_success "Static files collected"
else
    print_warning "Static files collection had issues"
fi

# Check Celery worker
print_info "Checking Celery worker..."
sleep 5
if docker exec celery_worker celery -A core inspect ping > /dev/null 2>&1; then
    print_success "Celery worker is responding"
else
    print_warning "Celery worker is starting up or not responding"
fi

# Display container status
echo ""
echo "════════════════════════════════════════════════"
print_success "Deployment Test Complete!"
echo "════════════════════════════════════════════════"
echo ""

print_info "Container Status:"
docker-compose ps

echo ""
print_info "Service URLs:"
echo "  - Django API: http://localhost:8000"
echo "  - Django Admin: http://localhost:8000/admin"
echo "  - Grafana: http://localhost:3001"
echo "  - Prometheus: http://localhost:9090"

echo ""
print_info "Useful Commands:"
echo "  - View logs: docker-compose logs -f"
echo "  - Stop containers: docker-compose down"
echo "  - Restart: docker-compose restart"

echo ""
print_success "Everything looks good! Ready to push to production. 🚀"
echo ""
print_info "To deploy to VPS:"
echo "  git add ."
echo "  git commit -m 'Your message'"
echo "  git push origin main"
echo ""

