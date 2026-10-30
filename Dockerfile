# ==============================================================================
# FastAPI Backend Dockerfile — NovaStore AI Customer Support System
# ==============================================================================
FROM python:3.11-slim

# Prevent Python from writing .pyc files and buffer stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    ENVIRONMENT=production \
    PORT=8001

WORKDIR /app

# Install system dependencies (build-essential needed for some C extensions if wheel unavailable)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies first for caching layer
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source code
COPY app/ ./app/
COPY data/ ./data/
COPY database/ ./database/
COPY scripts/ ./scripts/
COPY .env.example .

# Pre-build FAISS vector index during build stage so vector store is ready at startup
RUN python scripts/ingest_documents.py

# Expose default backend port
EXPOSE 8001

# Liveness probe using curl
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:${PORT:-8001}/health/live || exit 1

# Start FastAPI application bound to 0.0.0.0 and dynamic cloud PORT
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8001}"]
