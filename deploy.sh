#!/bin/bash

# Exit on error
set -e

echo "Starting deployment process..."

# Set environment variables
export FLASK_APP=app.py
export FLASK_ENV=production
export PORT=8000
export PYTHONUNBUFFERED=1
export PYTHONPATH=/home/site/wwwroot:/home/site/wwwroot/src

# Create temp directory for logs
mkdir -p /tmp/app_logs
export LOG_DIR=/tmp/app_logs

# Install Python dependencies
echo "Installing Python dependencies..."
python -m pip install --upgrade pip
pip install --no-cache-dir -r requirements.txt

# Verify critical packages
echo "Verifying critical packages..."
python -c "import flask; import flask_cors; import gunicorn"

# Build React app if frontend directory exists
if [ -d "frontend" ]; then
    echo "Building React app..."
    cd frontend
    npm install --legacy-peer-deps
    npm run build
    
    # Copy built files to static directory
    echo "Copying built files..."
    mkdir -p ../static
    cp -r build/* ../static/
    cd ..
fi

# Start the application with Gunicorn
echo "Starting application..."
gunicorn --bind=0.0.0.0:$PORT \
         --timeout 600 \
         --workers 2 \
         --threads 4 \
         --log-level info \
         --access-logfile /tmp/app_logs/access.log \
         --error-logfile /tmp/app_logs/error.log \
         --capture-output \
         --enable-stdio-inheritance \
         --max-requests 1000 \
         --max-requests-jitter 50 \
         --worker-class=gthread \
         app:app 