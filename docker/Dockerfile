# Use Python 3.11 slim image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    graphviz \
    libgraphviz-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip
RUN pip install --no-cache-dir --upgrade pip

# Copy dependency files
COPY pyproject.toml ./

# Install dependencies from pyproject.toml
# pip can read pyproject.toml directly in newer versions
RUN pip install --no-cache-dir \
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
    pygraphviz>=1.11 \
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
COPY static/ ./static/
COPY sql/ ./sql/
COPY data/ ./data/
COPY documents/ ./documents/

# Create necessary directories
RUN mkdir -p result/chroma_db

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Expose port
EXPOSE 8011

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8011/health')" || exit 1

# Run the application
CMD ["python", "-m", "uvicorn", "script.api:app", "--host", "0.0.0.0", "--port", "8011"]

