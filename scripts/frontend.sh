#!/bin/bash

echo "🚀 Starting Student LMS AI Frontend..."
echo "📱 The application will open in your default browser"
echo "🔗 URL: http://localhost:8501"
echo "📝 Logs will be written to: logs/app.log"
echo "⏹️  Press Ctrl+C to stop the application"
echo "----------------------------------------"

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "❌ Error: uv is not installed."
    echo "Please install uv first: pip install uv"
    exit 1
fi

# Check if frontend directory exists
if [ ! -d "frontend" ]; then
    echo "❌ Error: frontend directory not found."
    exit 1
fi

# Start the frontend from root directory with proper Python path
echo "🚀 Launching frontend..."
export PYTHONPATH="${PWD}"
python -m streamlit run frontend/main.py
