################################################################################
# Dockerfile – Production image for the FastAPI application
#
# Multi-stage build:
#   Stage 1 (builder): install dependencies in a venv
#   Stage 2 (runtime): copy only the venv and source, run as non-root
################################################################################

# ── Stage 1: Builder ──────────────────────────────────────────────────────────
FROM python:3.12-slim AS builder

WORKDIR /build

# Install build deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libpq-dev \
  && rm -rf /var/lib/apt/lists/*

# Create virtual environment and install dependencies
COPY requirements.txt .
RUN python -m venv /opt/venv \
  && /opt/venv/bin/pip install --upgrade pip \
  && /opt/venv/bin/pip install --no-cache-dir -r requirements.txt

# ── Stage 2: Runtime ──────────────────────────────────────────────────────────
FROM python:3.12-slim AS runtime

WORKDIR /app

# Non-root user for security
RUN groupadd -r appgroup && useradd -r -g appgroup appuser

# Copy venv from builder
COPY --from=builder /opt/venv /opt/venv

# Copy application source
COPY --chown=appuser:appgroup . .

# Add venv to PATH
ENV PATH="/opt/venv/bin:$PATH"
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

USER appuser

EXPOSE 8000

# Production: use Gunicorn with Uvicorn workers
CMD ["gunicorn", "app.main:app", \
     "--worker-class", "uvicorn.workers.UvicornWorker", \
     "--workers", "4", \
     "--bind", "0.0.0.0:8000", \
     "--access-logfile", "-", \
     "--error-logfile", "-", \
     "--timeout", "60"]
