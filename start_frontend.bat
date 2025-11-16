@echo off
echo Starting React Frontend Server...
echo.
cd frontend
echo Installing dependencies if needed...
call npm install
echo.
echo Starting development server on http://localhost:3000
echo Press Ctrl+C to stop the server
echo.
call npm start
pause

