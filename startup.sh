#!/bin/bash

# Create necessary directories
mkdir -p /home/site/wwwroot/logs
mkdir -p /home/site/wwwroot/data

# Ensure we're using the correct Python environment
python -m pip install --upgrade pip

# Install dependencies with memory optimization
pip install --no-cache-dir -r requirements.txt --verbose

# Set environment variables
export FLASK_APP=app.py
export FLASK_ENV=production
export PORT=8000
export PYTHONUNBUFFERED=1
export PYTHONPATH=/home/site/wwwroot

# Start the application with memory optimization
gunicorn --bind=0.0.0.0:$PORT \
         --timeout 600 \
         --workers 2 \
         --threads 4 \
         --log-level info \
         --access-logfile /home/site/wwwroot/logs/access.log \
         --error-logfile /home/site/wwwroot/logs/error.log \
         --capture-output \
         --enable-stdio-inheritance \
         --max-requests 1000 \
         --max-requests-jitter 50 \
         --worker-class=gthread \
         app:app 