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

# Update system packages
print_status "Updating system packages..."
sudo apt-get update && sudo apt-get upgrade -y
if [ $? -ne 0 ]; then
    print_error "Failed to update system packages"
    exit 1
fi

# Install required system dependencies
print_status "Installing system dependencies..."
sudo apt-get install -y python3.11 python3.11-venv python3.11-dev postgresql postgresql-contrib nginx supervisor
if [ $? -ne 0 ]; then
    print_error "Failed to install system dependencies"
    exit 1
fi

# Install UV
print_status "Installing UV..."
curl -sSf https://astral.sh/uv/install.sh | sh
if [ $? -ne 0 ]; then
    print_error "Failed to install UV"
    exit 1
fi

# Create application directory
print_status "Setting up application directory..."
sudo mkdir -p /opt/student-lms
sudo chown -R $USER:$USER /opt/student-lms

# Copy application files
print_status "Copying application files..."
cp -r ./* /opt/student-lms/
cd /opt/student-lms

# Create and activate virtual environment
print_status "Setting up virtual environment..."
uv venv
source .venv/bin/activate

# Install dependencies
print_status "Installing application dependencies..."
uv pip install -e ".[dev]"
if [ $? -ne 0 ]; then
    print_error "Failed to install dependencies"
    exit 1
fi

# Create systemd service file
print_status "Creating systemd service..."
sudo tee /etc/systemd/system/student-lms.service << EOL
[Unit]
Description=Student LMS AI Backend
After=network.target

[Service]
User=$USER
Group=$USER
WorkingDirectory=/opt/student-lms
Environment="PATH=/opt/student-lms/.venv/bin"
ExecStart=/opt/student-lms/.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
EOL

# Create Nginx configuration
print_status "Configuring Nginx..."
sudo tee /etc/nginx/sites-available/student-lms << EOL
server {
    listen 80;
    server_name _;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOL

# Enable Nginx site
sudo ln -sf /etc/nginx/sites-available/student-lms /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

# Start and enable services
print_status "Starting services..."
sudo systemctl daemon-reload
sudo systemctl enable student-lms
sudo systemctl start student-lms
sudo systemctl restart nginx

print_success "Deployment completed successfully!"
print_status "The application is now running at http://localhost"
print_status "Check service status with: sudo systemctl status student-lms"
print_status "View logs with: sudo journalctl -u student-lms -f" 