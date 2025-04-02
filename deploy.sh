#!/bin/bash

# Exit on error
set -e

echo "Starting deployment process..."

# Create necessary directories
echo "Creating directories..."
mkdir -p /home/site/wwwroot/logs
mkdir -p /home/site/wwwroot/data
mkdir -p /home/site/wwwroot/static

# Install Python dependencies
echo "Installing Python dependencies..."
cd /home/site/wwwroot
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
    
    # Copy built files
    echo "Copying built files..."
    cp -r build/* /home/site/wwwroot/static/
    cd ..
fi

# Set environment variables
export FLASK_APP=app.py
export FLASK_ENV=production
export PORT=8000
export PYTHONUNBUFFERED=1
export PYTHONPATH=/home/site/wwwroot:/home/site/wwwroot/src

# Start the application
echo "Starting application..."
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