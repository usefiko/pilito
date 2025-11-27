# Highly optimized Dockerfile with smaller image size
# This reduces PyTorch size by using CPU-only version if GPU not needed
FROM python:3.11-slim AS base

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
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

# Create a requirements file without torch (install CPU version separately)
RUN grep -v "sentence-transformers" /tmp/requirements/base.txt > /tmp/requirements/base_no_torch.txt || \
    cp /tmp/requirements/base.txt /tmp/requirements/base_no_torch.txt

# Install Python packages WITHOUT large ML libraries first
RUN pip install --upgrade pip setuptools wheel && \
    pip install --retries 10 --timeout 300 -r /tmp/requirements/base_no_torch.txt

# Install sentence-transformers with CPU-only PyTorch (MUCH smaller)
# This reduces image size from ~7GB to ~2GB
RUN pip install --retries 10 --timeout 300 \
    torch --index-url https://download.pytorch.org/whl/cpu && \
    pip install --retries 10 --timeout 300 sentence-transformers

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
    find /app -type d -name "__pycache__" -delete && \
    # Remove unnecessary torch files to save space
    find /usr/local/lib/python3.11/site-packages/torch -name "*.a" -delete && \
    find /usr/local/lib/python3.11/site-packages/torch -name "test" -type d -exec rm -rf {} + || true

ENTRYPOINT ["/entrypoint.sh"]

