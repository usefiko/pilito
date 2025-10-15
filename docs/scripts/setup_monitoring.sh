#!/bin/bash
# Prometheus + Grafana Monitoring Setup Script
# This script sets up and validates the monitoring stack

set -e

echo "================================================"
echo "  Fiko Backend - Monitoring Stack Setup"
echo "================================================"
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if Docker is running
echo "🔍 Checking prerequisites..."
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}❌ Docker is not running. Please start Docker first.${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Docker is running${NC}"

# Check if docker-compose is available
if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}❌ docker-compose is not installed${NC}"
    exit 1
fi
echo -e "${GREEN}✅ docker-compose is available${NC}"

echo ""
echo "📦 Installing Python dependencies..."
if [ -f "src/requirements/base.txt" ]; then
    cd src
    pip install -q prometheus-client celery-prometheus-exporter psutil
    cd ..
    echo -e "${GREEN}✅ Dependencies installed${NC}"
else
    echo -e "${YELLOW}⚠️  requirements/base.txt not found, skipping...${NC}"
fi

echo ""
echo "🚀 Starting monitoring stack..."

# Start Prometheus
echo "  → Starting Prometheus..."
docker-compose up -d prometheus
sleep 3

# Start Grafana
echo "  → Starting Grafana..."
docker-compose up -d grafana
sleep 3

# Start exporters
echo "  → Starting Redis exporter..."
docker-compose up -d redis_exporter
sleep 2

echo "  → Starting PostgreSQL exporter..."
docker-compose up -d postgres_exporter
sleep 2

echo ""
echo "🔄 Restarting application services with monitoring..."
docker-compose up -d --build web celery_worker

echo ""
echo "⏳ Waiting for services to be ready..."
sleep 5

# Health checks
echo ""
echo "🏥 Running health checks..."

# Check Prometheus
if curl -s http://localhost:9090/-/healthy > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Prometheus is healthy${NC}"
else
    echo -e "${RED}❌ Prometheus health check failed${NC}"
fi

# Check Grafana
if curl -s http://localhost:3001/api/health > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Grafana is healthy${NC}"
else
    echo -e "${RED}❌ Grafana health check failed${NC}"
fi

# Check Django metrics endpoint
if curl -s http://localhost:8000/api/v1/metrics/health > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Django metrics endpoint is healthy${NC}"
else
    echo -e "${YELLOW}⚠️  Django metrics endpoint not responding (might need a moment)${NC}"
fi

# Check Redis exporter
if curl -s http://localhost:9121/metrics > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Redis exporter is healthy${NC}"
else
    echo -e "${RED}❌ Redis exporter health check failed${NC}"
fi

# Check PostgreSQL exporter
if curl -s http://localhost:9187/metrics > /dev/null 2>&1; then
    echo -e "${GREEN}✅ PostgreSQL exporter is healthy${NC}"
else
    echo -e "${RED}❌ PostgreSQL exporter health check failed${NC}"
fi

# Check Celery exporter
if curl -s http://localhost:9808/metrics > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Celery exporter is healthy${NC}"
else
    echo -e "${YELLOW}⚠️  Celery exporter not responding (might still be starting)${NC}"
fi

echo ""
echo "================================================"
echo "  ✨ Monitoring Stack Setup Complete!"
echo "================================================"
echo ""
echo "📊 Access your monitoring dashboards:"
echo ""
echo "  🌐 Grafana:    http://localhost:3001"
echo "     Username: admin"
echo "     Password: admin (change on first login!)"
echo ""
echo "  🔍 Prometheus: http://localhost:9090"
echo ""
echo "  📈 Metrics:    http://localhost:8000/api/v1/metrics"
echo ""
echo "================================================"
echo ""
echo "📚 Next Steps:"
echo ""
echo "  1. Open Grafana and explore the 'Fiko Backend Overview' dashboard"
echo "  2. Change the default Grafana admin password"
echo "  3. Generate some traffic to see metrics:"
echo "     $ for i in {1..20}; do curl http://localhost:8000/api/v1/usr/; sleep 1; done"
echo ""
echo "  4. Read the documentation:"
echo "     - Quick Start: MONITORING_QUICK_START.md"
echo "     - Full Guide:  PROMETHEUS_GRAFANA_SETUP.md"
echo ""
echo "================================================"
echo ""
echo "🎉 Happy Monitoring!"
echo ""

