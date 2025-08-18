#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to print status messages
print_status() {
    echo -e "${BLUE}==>${NC} $1"
}

# Function to print success messages
print_success() {
    echo -e "${GREEN}==>${NC} $1"
}

# Function to print error messages
print_error() {
    echo -e "${RED}==>${NC} $1"
}

# Check if Python 3.11+ is installed
if ! command -v python3 &> /dev/null; then
    print_error "Python 3 is not installed. Please install Python 3.11 or higher."
    exit 1
fi

# Check Python version
PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
if (( $(echo "$PYTHON_VERSION < 3.11" | bc -l) )); then
    print_error "Python 3.11 or higher is required. Current version: $PYTHON_VERSION"
    exit 1
fi

# Check if UV is installed
if ! command -v uv &> /dev/null; then
    print_status "UV not found. Installing UV..."
    curl -sSf https://astral.sh/uv/install.sh | sh
    if [ $? -ne 0 ]; then
        print_error "Failed to install UV"
        exit 1
    fi
    print_success "UV installed successfully"
fi

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    print_status "Creating virtual environment..."
    uv venv
    if [ $? -ne 0 ]; then
        print_error "Failed to create virtual environment"
        exit 1
    fi
    print_success "Virtual environment created successfully"
fi

# Activate virtual environment
print_status "Activating virtual environment..."
source .venv/bin/activate
if [ $? -ne 0 ]; then
    print_error "Failed to activate virtual environment"
    exit 1
fi

# Install dependencies
print_status "Installing dependencies..."
uv pip install -e ".[dev]"
if [ $? -ne 0 ]; then
    print_error "Failed to install dependencies"
    exit 1
fi
print_success "Dependencies installed successfully"

# Check if .env file exists
if [ ! -f ".env" ]; then
    print_status "Creating .env file..."
    cat > .env << EOL
DATABASE_URL=postgresql://user:password@localhost:5432/dbname
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
EOL
    print_success ".env file created. Please update the values in .env file with your actual configuration."
fi

# Run database migrations
print_status "Running database migrations..."
alembic upgrade head
if [ $? -ne 0 ]; then
    print_error "Failed to run database migrations"
    exit 1
fi
print_success "Database migrations completed successfully"

# Start the application
print_status "Starting the application..."
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000