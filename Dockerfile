# Optimized multi-stage Dockerfile with better caching
FROM python:3.11-slim AS base

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# ─────────────────────────────────────────
# Stage 1: System dependencies (cached unless Dockerfile changes)
# ─────────────────────────────────────────
FROM base AS system-deps

RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    postgresql-client \
    netcat-openbsd \
    --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

# ─────────────────────────────────────────
# Stage 2: Python dependencies (cached unless requirements change)
# ─────────────────────────────────────────
FROM system-deps AS python-deps

# Copy only requirements first (for better layer caching)
COPY src/requirements/*.txt /tmp/requirements/

# Install Python packages (this layer will be cached)
# Use increased retries and timeout for large packages like torch
RUN pip install --upgrade pip setuptools wheel && \
    pip install --retries 10 --timeout 300 --resume-retries 10 -r /tmp/requirements/base.txt

# ─────────────────────────────────────────
# Stage 3: Final application (only rebuilds when code changes)
# ─────────────────────────────────────────
FROM python-deps AS final

# Now copy application code (this layer changes frequently)
COPY ./src /app
COPY ./entrypoint.sh /entrypoint.sh

# Setup and cleanup
RUN chmod +x /entrypoint.sh && \
    find /app -type f -name "*.pyc" -delete && \
    find /app -type d -name "__pycache__" -delete

ENTRYPOINT ["/entrypoint.sh"]