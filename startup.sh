#!/bin/bash

# Create necessary directories
mkdir -p /home/site/wwwroot/logs
mkdir -p /home/site/wwwroot/data

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export FLASK_APP=app.py
export FLASK_ENV=production
export PORT=8000

# Start the application
gunicorn --bind=0.0.0.0:$PORT --timeout 600 --workers 4 --log-level info --access-logfile /home/site/wwwroot/logs/access.log --error-logfile /home/site/wwwroot/logs/error.log app:app 