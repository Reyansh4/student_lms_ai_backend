# Azure VM Deployment Guide

This guide provides step-by-step instructions for deploying the Student LMS AI Backend on Azure Virtual Machines.

## Prerequisites

1. An Azure account with an active subscription
2. Azure CLI installed on your local machine
3. SSH key pair for secure access to the VM

## Deployment Steps

### 1. Create an Azure VM

```bash
# Login to Azure
az login

# Create a resource group
az group create --name student-lms-rg --location eastus

# Create a VM (Ubuntu 22.04 LTS)
az vm create \
  --resource-group student-lms-rg \
  --name student-lms-vm \
  --image Ubuntu2204 \
  --size Standard_B2s \
  --admin-username azureuser \
  --ssh-key-value ~/.ssh/id_rsa.pub \
  --public-ip-sku Standard

# Open port 80 for HTTP traffic
az vm open-port \
  --resource-group student-lms-rg \
  --name student-lms-vm \
  --port 80
```

### 2. Configure PostgreSQL Database

1. Install PostgreSQL on the VM:
```bash
sudo apt-get update
sudo apt-get install -y postgresql postgresql-contrib
```

2. Configure PostgreSQL:
```bash
sudo -u postgres psql
CREATE DATABASE student_lms;
CREATE USER student_lms_user WITH PASSWORD 'your_secure_password';
GRANT ALL PRIVILEGES ON DATABASE student_lms TO student_lms_user;
\q
```

3. Update PostgreSQL configuration to allow remote connections:
```bash
sudo nano /etc/postgresql/14/main/postgresql.conf
# Change listen_addresses to '*'
sudo nano /etc/postgresql/14/main/pg_hba.conf
# Add: host all all 0.0.0.0/0 md5
sudo systemctl restart postgresql
```

### 3. Deploy the Application

1. Copy the application files to the VM:
```bash
# From your local machine
scp -r ./* azureuser@<VM_IP>:/tmp/student-lms/
```

2. SSH into the VM:
```bash
ssh azureuser@<VM_IP>
```

3. Make the deployment script executable and run it:
```bash
cd /tmp/student-lms
chmod +x deploy.sh
./deploy.sh
```

4. Configure environment variables:
```bash
sudo nano /opt/student-lms/.env
```

Update the following variables:
```
DATABASE_URL=postgresql://student_lms_user:your_secure_password@localhost:5432/student_lms
SECRET_KEY=your-secure-secret-key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

5. Run database migrations:
```bash
cd /opt/student-lms
source .venv/bin/activate
alembic upgrade head
```

### 4. Verify Deployment

1. Check service status:
```bash
sudo systemctl status student-lms
sudo systemctl status nginx
```

2. View application logs:
```bash
sudo journalctl -u student-lms -f
```

3. Access the application:
- Open your browser and navigate to `http://<VM_IP>`
- The API documentation will be available at `http://<VM_IP>/docs`

## Maintenance

### Updating the Application

1. Pull the latest changes:
```bash
cd /opt/student-lms
git pull
```

2. Update dependencies:
```bash
source .venv/bin/activate
uv pip install -e ".[dev]"
```

3. Run database migrations:
```bash
alembic upgrade head
```

4. Restart the service:
```bash
sudo systemctl restart student-lms
```

### Backup

1. Database backup:
```bash
sudo -u postgres pg_dump student_lms > /backup/student_lms_$(date +%Y%m%d).sql
```

2. Application backup:
```bash
sudo tar -czf /backup/student_lms_app_$(date +%Y%m%d).tar.gz /opt/student-lms
```

## Security Considerations

1. Configure SSL/TLS:
   - Install Certbot: `sudo apt-get install certbot python3-certbot-nginx`
   - Obtain SSL certificate: `sudo certbot --nginx -d your-domain.com`
   - Auto-renewal is configured by default

2. Firewall configuration:
   - Only open necessary ports (80, 443)
   - Use Azure Network Security Groups to restrict access

3. Regular updates:
   - Keep the system updated: `sudo apt-get update && sudo apt-get upgrade`
   - Monitor security advisories for dependencies

## Troubleshooting

1. Check service logs:
```bash
sudo journalctl -u student-lms -f
sudo tail -f /var/log/nginx/error.log
```

2. Common issues:
   - Database connection issues: Check PostgreSQL logs and connection string
   - Permission issues: Verify file ownership and permissions
   - Port conflicts: Check if ports 80 and 8000 are available

3. Restart services:
```bash
sudo systemctl restart student-lms
sudo systemctl restart nginx
sudo systemctl restart postgresql
``` 