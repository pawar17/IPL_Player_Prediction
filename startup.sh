#!/bin/bash

# Create necessary directories
mkdir -p /home/site/wwwroot/logs
mkdir -p /home/site/wwwroot/data

# Ensure we're using the correct Python environment
python -m pip install --upgrade pip

# Install dependencies with verbose output
pip install -r requirements.txt --verbose

# Set environment variables
export FLASK_APP=app.py
export FLASK_ENV=production
export PORT=8000

# Start the application with proper logging
gunicorn --bind=0.0.0.0:$PORT \
         --timeout 600 \
         --workers 4 \
         --log-level info \
         --access-logfile /home/site/wwwroot/logs/access.log \
         --error-logfile /home/site/wwwroot/logs/error.log \
         --capture-output \
         --enable-stdio-inheritance \
         app:app 