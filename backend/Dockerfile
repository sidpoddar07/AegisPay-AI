# =============================================================================
# AegisPay-AI — Backend Dockerfile
# Python 3.11-slim: production-grade, minimal attack surface
# =============================================================================

FROM python:3.11-slim AS base

# Metadata labels
LABEL maintainer="AegisPay-AI"
LABEL description="AegisPay-AI Agent Firewall API — Zero-Trust In-Flight Payment Security Mesh"

# ── System Hardening & OS-level deps ─────────────────────────────────────────
# Install only what is strictly needed; then wipe package cache in same layer
RUN apt-get update && apt-get install -y --no-install-recommends \
        curl \
    && rm -rf /var/lib/apt/lists/*

# ── Non-root user for security ───────────────────────────────────────────────
RUN groupadd --system aegis && useradd --system --gid aegis aegis

# ── Python environment setup ─────────────────────────────────────────────────
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# ── Install Python dependencies ──────────────────────────────────────────────
# Copy requirements first for optimal layer caching (only reinstalls on changes)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ── Copy application source ───────────────────────────────────────────────────
COPY app/ ./app/

# ── Set ownership to non-root user ────────────────────────────────────────────
RUN chown -R aegis:aegis /app

USER aegis

# ── Expose port ───────────────────────────────────────────────────────────────
EXPOSE 8000

# ── Health check ──────────────────────────────────────────────────────────────
HEALTHCHECK --interval=15s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health || exit 1

# ── Launch uvicorn ────────────────────────────────────────────────────────────
# --workers 1 keeps the in-memory audit ledger & firewall singleton coherent.
# For a stateless multi-worker setup, externalise state to Redis/Postgres first.
CMD ["uvicorn", "app.main:app", \
     "--host", "0.0.0.0", \
     "--port", "8000", \
     "--workers", "1", \
     "--loop", "uvloop", \
     "--http", "httptools", \
     "--log-level", "info", \
     "--access-log"]
