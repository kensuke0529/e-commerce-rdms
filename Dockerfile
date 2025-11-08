# Use Python 3.11 slim image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency files first (for better Docker layer caching)
COPY pyproject.toml ./

# Install dependencies using pip
# Install the package in editable mode to include all dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir \
    pandas>=2.0.0 \
    psycopg2-binary>=2.9.0 \
    python-dotenv>=1.0.0 \
    jupyter>=1.0.0 \
    numpy>=1.24.0 \
    fastapi>=0.104.0 \
    uvicorn>=0.24.0 \
    pydantic>=2.0.0 \
    passlib>=1.7.4 \
    python-jose>=3.3.0 \
    bcrypt>=4.0.0 \
    PyJWT>=2.8.0 \
    openai>=1.0.0 \
    langgraph>=0.2.30 \
    langchain-core>=0.3.13 \
    langchain-community>=0.3.0 \
    langchain-openai>=0.2.0 \
    langchain-text-splitters>=0.3.0 \
    langsmith>=0.1.0 \
    chromadb>=0.4.0 \
    pypdf>=3.0.0 \
    python-multipart>=0.0.6

# Copy application code
COPY script/ ./script/
COPY sql/ ./sql/
COPY static/ ./static/
COPY documents/ ./documents/
COPY data/ ./data/

# Copy startup script
COPY start.sh /app/start.sh
RUN chmod +x /app/start.sh

# Create directories for ChromaDB and results
RUN mkdir -p /app/result/chroma_db /app/result/image

# Set Python path
ENV PYTHONPATH=/app/script:$PYTHONPATH
ENV PYTHONUNBUFFERED=1

# Default port (Render will override with $PORT)
ENV PORT=8011

# Expose port (Render uses dynamic ports)
EXPOSE 8011

# Health check (using curl which is more reliable in containers)
# Uses PORT env var for Render compatibility
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD sh -c 'curl -f http://localhost:${PORT:-8011}/health || exit 1'

# Run the application (Render-compatible: uses $PORT env var)
CMD ["/app/start.sh"]

