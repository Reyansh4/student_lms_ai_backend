#!/bin/bash

echo "🚀 Starting Student LMS AI Backend API..."
echo "🔗 API will be available at: http://localhost:8000"
echo "📚 API docs at: http://localhost:8000/docs"
echo "📝 Logs will be written to: logs/app.log"
echo "⏹️  Press Ctrl+C to stop the server"
echo "----------------------------------------"

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "❌ Error: uv is not installed."
    echo "Please install uv first: pip install uv"
    exit 1
fi

# Check if pyproject.toml exists
if [ ! -f "pyproject.toml" ]; then
    echo "❌ Error: pyproject.toml not found."
    echo "Please run this script from the project root directory."
    exit 1
fi

# Start the API server
echo "🚀 Starting API server..."
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
