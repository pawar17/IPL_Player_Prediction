import os
import subprocess
import sys
from pathlib import Path

def main():
    """
    Run the IPL Player Prediction Streamlit frontend
    """
    print("Starting IPL Player Prediction System Frontend...")
    
    # Get the project root directory
    project_root = Path(__file__).parent
    frontend_dir = project_root / "frontend"
    
    # Check if frontend directory exists
    if not frontend_dir.exists():
        print(f"Error: Frontend directory not found at {frontend_dir}")
        return
    
    # Check if app.py exists
    app_path = frontend_dir / "app.py"
    if not app_path.exists():
        print(f"Error: Frontend app not found at {app_path}")
        return
    
    # Run the Streamlit app
    try:
        print("Launching Streamlit frontend...")
        os.chdir(frontend_dir)
        subprocess.run([sys.executable, "-m", "streamlit", "run", "app.py"])
    except Exception as e:
        print(f"Error running Streamlit app: {str(e)}")
        print("\nPlease make sure Streamlit is installed by running:")
        print("pip install streamlit")

if __name__ == "__main__":
    main()
