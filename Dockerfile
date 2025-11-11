# Dockerfile for Food Inspection Management System
# Supports both SQLite and PostgreSQL databases

# Use official Python runtime as base image
FROM python:3.13-slim

# Set working directory in container
WORKDIR /app

# Install system dependencies
# - postgresql-client: For PostgreSQL database tools
# - gcc: Required for compiling some Python packages
RUN apt-get update && apt-get install -y \
    postgresql-client \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=5000

# Copy requirements first (for better Docker layer caching)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p static/uploads && \
    mkdir -p templates

# Expose port (default 5000, can be overridden)
EXPOSE ${PORT}

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:${PORT}/').read()" || exit 1

# Run the application
# For development: Flask dev server
# CMD ["python", "app.py"]

# For production: Gunicorn
CMD gunicorn \
    --bind 0.0.0.0:${PORT} \
    --workers 4 \
    --timeout 120 \
    --access-logfile - \
    --error-logfile - \
    app:app
