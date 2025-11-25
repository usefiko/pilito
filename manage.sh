#!/bin/bash
# Django management command wrapper
# Uses docker compose exec instead of run to avoid creating temporary containers

set -e

# Check if service is running
if ! docker compose ps web | grep -q "Up"; then
    echo "⚠️  Web service is not running. Starting services..."
    docker compose up -d
    sleep 5
fi

# Run the command in the existing container
echo "🎯 Running: python manage.py $@"
docker compose exec web python manage.py "$@"

