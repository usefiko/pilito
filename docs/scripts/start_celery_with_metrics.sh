#!/bin/bash
# Start Celery worker with Prometheus metrics exporter

set -e

echo "Starting Celery Prometheus Exporter in background..."
cd /app
python -m celery_prometheus_exporter --broker=$REDIS_URL --addr=0.0.0.0:9808 &
EXPORTER_PID=$!

echo "Starting Celery Worker..."
celery -A core worker --loglevel=info --concurrency=2 -Q celery,workflow_tasks,ai_tasks,instagram_tokens &
WORKER_PID=$!

# Function to handle shutdown
shutdown() {
    echo "Shutting down..."
    kill $EXPORTER_PID 2>/dev/null || true
    kill $WORKER_PID 2>/dev/null || true
    wait
    exit 0
}

# Trap signals
trap shutdown SIGTERM SIGINT

# Wait for either process to exit
wait -n

# If we get here, one process exited, so shut down both
shutdown

