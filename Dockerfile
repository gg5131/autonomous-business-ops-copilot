# ============================================================
# Autonomous Business Operations Copilot — Dockerfile
# Multi-stage build for production deployment
# ============================================================

# --- Stage 1: Builder ---
FROM python:3.11-slim AS builder

WORKDIR /app

# Install system dependencies for building packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    tesseract-ocr \
    libtesseract-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency specifications
COPY pyproject.toml ./

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir ".[frontend]"

# --- Stage 2: Runtime ---
FROM python:3.11-slim AS runtime

WORKDIR /app

# Install runtime system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    tesseract-ocr \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application source
COPY src/ ./src/
COPY configs/ ./configs/
COPY knowledge/ ./knowledge/
COPY frontend/ ./frontend/
COPY scripts/ ./scripts/

# Create non-root user for security
RUN groupadd --gid 1000 copilot && \
    useradd --uid 1000 --gid copilot --shell /bin/bash --create-home copilot && \
    chown -R copilot:copilot /app

USER copilot

# Create data directories
RUN mkdir -p /app/data /app/logs /app/data/faiss_indices

# Expose API and Streamlit ports
EXPOSE 8000 8501

# Health check
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health || exit 1

# Default command: run the FastAPI server
CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
