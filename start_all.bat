@echo off
echo ========================================
echo IPL Player Prediction - Starting Servers
echo ========================================
echo.

echo [1/3] Checking Python dependencies...
python -c "import flask" 2>nul
if errorlevel 1 (
    echo ERROR: Flask not found. Installing dependencies...
    pip install -r requirements.txt
)

echo.
echo [2/3] Starting Flask Backend on port 5000...
start "Flask Backend" cmd /k "python app.py"

echo Waiting for backend to start...
timeout /t 3 /nobreak >nul

echo.
echo [3/3] Starting React Frontend on port 3000...
cd frontend
start "React Frontend" cmd /k "npm start"
cd ..

echo.
echo ========================================
echo Servers are starting!
echo ========================================
echo.
echo Backend API: http://localhost:5000
echo Frontend UI: http://localhost:3000
echo.
echo Both servers are running in separate windows.
echo Close those windows to stop the servers.
echo.
pause

