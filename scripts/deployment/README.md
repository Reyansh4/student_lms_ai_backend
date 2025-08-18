# 🚀 Deployment Scripts

This directory contains scripts for deploying and managing the Student LMS AI application.

## 📋 Available Scripts

### **Initialization**
- **`init.sh`** - Initialize the application environment
- **`deploy.sh`** - Deploy the application to production

## 🚀 Usage

### **Initialization (Unix/Linux/Mac)**
```bash
cd scripts/deployment
chmod +x init.sh
./init.sh
```

### **Deployment (Unix/Linux/Mac)**
```bash
cd scripts/deployment
chmod +x deploy.sh
./deploy.sh
```

### **Windows Users**
For Windows users, you can run these scripts using:
- Git Bash
- WSL (Windows Subsystem for Linux)
- PowerShell with appropriate modifications

## 🔧 What These Scripts Do

### **`init.sh`**
- Sets up environment variables
- Installs dependencies
- Configures database
- Sets up logging
- Initializes application

### **`deploy.sh`**
- Builds the application
- Runs tests
- Deploys to production server
- Sets up monitoring
- Configures SSL certificates

## ⚠️ Important Notes

- **Review scripts** before running in production
- **Test in staging** environment first
- **Backup data** before deployment
- **Check permissions** and access rights
- **Verify environment** variables are set

## 🔧 Prerequisites

- Server access and permissions
- Database credentials configured
- Environment variables set
- Required software installed (Docker, Python, etc.)

## 🛠️ Customization

These scripts can be customized for your specific:
- Server environment
- Database configuration
- Deployment requirements
- Monitoring setup

---

**🚀 Use these scripts for application deployment and management!**
