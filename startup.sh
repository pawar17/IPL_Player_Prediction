#!/bin/bash

# Enable debug mode
set -x

# Create necessary directories
echo "Creating directories..."
mkdir -p /home/site/wwwroot/logs
mkdir -p /home/site/wwwroot/data
mkdir -p /home/site/wwwroot/static

# Ensure we're using the correct Python environment
echo "Upgrading pip..."
python -m pip install --upgrade pip

# Install dependencies with memory optimization
echo "Installing dependencies..."
pip install --no-cache-dir -r requirements.txt --verbose

# Build React app if frontend directory exists
if [ -d "frontend" ]; then
    echo "Building React app..."
    cd frontend
    
    # Install npm dependencies
    echo "Installing npm dependencies..."
    npm install --legacy-peer-deps
    
    # Set production environment variables
    echo "Setting production environment variables..."
    export NODE_ENV=production
    export PUBLIC_URL=/
    
    # Build the app
    echo "Building React app..."
    npm run build
    
    # Verify build output
    echo "Verifying build output..."
    if [ ! -d "build" ]; then
        echo "Build failed - build directory not found"
        exit 1
    fi
    
    # Copy built files to static directory
    echo "Copying built files to static directory..."
    rm -rf /home/site/wwwroot/static/*
    cp -r build/* /home/site/wwwroot/static/
    
    # Verify static files
    echo "Verifying static files..."
    ls -la /home/site/wwwroot/static/
    
    cd ..
fi

# Set environment variables
echo "Setting environment variables..."
export FLASK_APP=app.py
export FLASK_ENV=production
export PORT=8000
export PYTHONUNBUFFERED=1
export PYTHONPATH=/home/site/wwwroot:/home/site/wwwroot/src

# Print environment information
echo "Environment information:"
echo "Python version: $(python --version)"
echo "Pip version: $(pip --version)"
echo "Working directory: $(pwd)"
echo "Directory contents: $(ls -la)"
echo "Python path: $PYTHONPATH"
echo "Static folder contents: $(ls -la /home/site/wwwroot/static/)"

# Run deployment verification
echo "Running deployment verification..."
bash verify_deployment.sh

# Start the application with memory optimization
echo "Starting application..."
cd /home/site/wwwroot
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