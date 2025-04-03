FROM python:3.9-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PORT=8000 \
    FLASK_APP=app.py \
    FLASK_ENV=production \
    PYTHONPATH=/app:/app/src

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    nodejs \
    npm \
    && rm -rf /var/lib/apt/lists/*

# Create necessary directories with correct permissions
RUN mkdir -p /app/logs /app/static /app/data && \
    chmod 777 /app/logs /app/static /app/data

# Copy requirements first to leverage Docker cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Build frontend if it exists
RUN if [ -d "frontend" ]; then \
    cd frontend && \
    npm install --legacy-peer-deps && \
    npm run build && \
    cp -r build/* ../static/ && \
    cd ..; \
    fi

# Create a non-root user
RUN useradd -m appuser && \
    chown -R appuser:appuser /app
USER appuser

# Command to run the application
CMD ["gunicorn", "--bind", "0.0.0.0:8000", \
     "--timeout", "600", \
     "--workers", "2", \
     "--threads", "4", \
     "--log-level", "info", \
     "--access-logfile", "/app/logs/access.log", \
     "--error-logfile", "/app/logs/error.log", \
     "--capture-output", \
     "--enable-stdio-inheritance", \
     "--max-requests", "1000", \
     "--max-requests-jitter", "50", \
     "--worker-class=gthread", \
     "app:app"] 