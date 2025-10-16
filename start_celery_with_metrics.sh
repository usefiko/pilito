#!/bin/bash

# Start Celery worker with Prometheus metrics
echo "Starting Celery worker with metrics exporter..."

# Start celery-exporter in the background for Prometheus metrics
celery-exporter --broker-url=${REDIS_URL:-redis://redis:6379} --port=9808 &

# Wait a moment for exporter to start
sleep 2

# Start Celery worker with autoscaling
exec celery -A core worker \
    --loglevel=info \
    --max-tasks-per-child=1000 \
    --time-limit=300 \
    --soft-time-limit=240

