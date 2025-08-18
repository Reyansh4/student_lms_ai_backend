@echo off
echo 🚀 Starting Student LMS AI Frontend...
echo 📱 The application will open in your default browser
echo 🔗 URL: http://localhost:8501
echo 📝 Logs will be written to: logs/app.log
echo ⏹️  Press Ctrl+C to stop the application
echo ----------------------------------------

REM Check if frontend directory exists
if not exist "frontend" (
    echo ❌ Error: frontend directory not found.
    pause
    exit /b 1
)

REM Start the frontend from root directory with proper Python path
echo 🚀 Launching frontend...
set PYTHONPATH=%PYTHONPATH%;%CD%
streamlit run frontend/main.py

pause
