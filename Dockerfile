FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    ffmpeg \
    libmagic1 \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy lightweight requirements first for better caching
COPY requirements-backend-light.txt .

# Install Python dependencies
RUN pip install --default-timeout=100 --no-cache-dir -r requirements-backend-light.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p /app/data /app/scraped_content /app/facebook_posts /app/faiss_local

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Expose ports
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Default command
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]