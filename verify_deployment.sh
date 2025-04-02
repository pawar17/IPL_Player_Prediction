#!/bin/bash

# Enable debug mode
set -x

echo "Checking deployment structure..."

# Check main directories
echo "Checking main directories..."
ls -la /home/site/wwwroot/

# Check static folder
echo "Checking static folder..."
ls -la /home/site/wwwroot/static/

# Check if index.html exists
echo "Checking for index.html..."
if [ -f /home/site/wwwroot/static/index.html ]; then
    echo "index.html exists"
    cat /home/site/wwwroot/static/index.html | head -n 5
else
    echo "index.html not found!"
fi

# Check Python path
echo "Checking Python path..."
echo $PYTHONPATH

# Check if all required files exist
echo "Checking required files..."
required_files=(
    "app.py"
    "requirements.txt"
    "src/data_collection/data_collector.py"
    "src/data_collection/data_processor.py"
    "src/predict_player_performance.py"
    "static/index.html"
)

for file in "${required_files[@]}"; do
    if [ -f "/home/site/wwwroot/$file" ]; then
        echo "✓ $file exists"
    else
        echo "✗ $file is missing!"
    fi
done

# Check application logs
echo "Checking application logs..."
if [ -f /home/site/wwwroot/logs/error.log ]; then
    echo "Last 10 lines of error.log:"
    tail -n 10 /home/site/wwwroot/logs/error.log
fi

if [ -f /home/site/wwwroot/logs/access.log ]; then
    echo "Last 10 lines of access.log:"
    tail -n 10 /home/site/wwwroot/logs/access.log
fi

# Test the health endpoint
echo "Testing health endpoint..."
curl -v http://localhost:8000/api/health 