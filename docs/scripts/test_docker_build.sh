#!/bin/bash

# Test script to verify Docker build works locally
# This helps debug deployment issues before pushing to production

echo "🐳 Testing Docker build locally..."

# Clean up any existing containers
echo "🧹 Cleaning up existing containers..."
docker-compose down || true
docker system prune -f || true

# Build the containers
echo "🔨 Building containers..."
export DOCKER_BUILDKIT=1
export COMPOSE_DOCKER_CLI_BUILD=1

if docker-compose build --pull; then
    echo "✅ Docker build successful!"
    
    # Test that Django can be imported
    echo "🔍 Testing Django import..."
    if docker-compose run --rm web python -c "import django; print(f'Django {django.get_version()} imported successfully')"; then
        echo "✅ Django import test successful!"
    else
        echo "❌ Django import test failed!"
        exit 1
    fi
    
    # Test that all required packages are available
    echo "🔍 Testing required packages..."
    if docker-compose run --rm web python -c "
import django
import rest_framework
import channels
import celery
import daphne
print('All required packages imported successfully')
"; then
        echo "✅ All packages test successful!"
    else
        echo "❌ Package import test failed!"
        exit 1
    fi
    
    echo "🎉 All tests passed! Docker build is ready for deployment."
    
else
    echo "❌ Docker build failed!"
    exit 1
fi
