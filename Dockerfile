FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY . .

# Copy and make start script executable
COPY start.sh .
RUN chmod +x start.sh

# Create directories
RUN mkdir -p uploads outputs

# Set environment for production
ENV ENVIRONMENT=production
ENV PYTHONPATH=/app

# Health check (simpler)
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:${PORT:-8000}/health || exit 1

# Use start script
CMD ["./start.sh"]