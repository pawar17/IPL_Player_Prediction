import subprocess
import sys
import time
import webbrowser
from pathlib import Path

def run_backend():
    """Run the Flask backend"""
    print("Starting Flask backend...")
    subprocess.Popen([sys.executable, 'app.py'])

def run_frontend():
    """Run the React frontend"""
    print("Starting React frontend...")
    frontend_dir = Path('frontend')
    # Use shell=True on Windows to find npm in PATH
    subprocess.Popen(['npm', 'start'], cwd=frontend_dir, shell=True)

def main():
    # Create necessary directories
    Path('data').mkdir(exist_ok=True)
    
    # Start the backend
    run_backend()
    
    # Wait for backend to start
    time.sleep(2)
    
    # Start the frontend
    run_frontend()
    
    # Wait for frontend to start
    time.sleep(5)
    
    # Open the application in the browser
    webbrowser.open('http://localhost:3000')
    
    print("\nApplication is running!")
    print("Frontend: http://localhost:3000")
    print("Backend API: http://localhost:5000")
    print("\nPress Ctrl+C to stop the application...")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping application...")
        sys.exit(0)

if __name__ == '__main__':
    main() 