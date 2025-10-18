# Optimized multi-stage Dockerfile with better caching
FROM python:3.12-slim as base

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# ─────────────────────────────────────────
# Stage 1: System dependencies (cached unless Dockerfile changes)
# ─────────────────────────────────────────
FROM base as system-deps

RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    netcat-openbsd \
    --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

# ─────────────────────────────────────────
# Stage 2: Python dependencies (cached unless requirements change)
# ─────────────────────────────────────────
FROM system-deps as python-deps

# Copy only requirements first (for better layer caching)
COPY src/requirements/*.txt /tmp/requirements/

# Install Python packages (this layer will be cached)
RUN pip install --upgrade pip && \
    pip install -r /tmp/requirements/base.txt

# ─────────────────────────────────────────
# Stage 3: Final application (only rebuilds when code changes)
# ─────────────────────────────────────────
FROM python-deps as final

# Now copy application code (this layer changes frequently)
COPY ./src /app
COPY entrypoint.sh /entrypoint.sh

# Setup and cleanup
RUN chmod +x /entrypoint.sh && \
    find /app -type f -name "*.pyc" -delete && \
    find /app -type d -name "__pycache__" -delete

ENTRYPOINT ["/entrypoint.sh"]