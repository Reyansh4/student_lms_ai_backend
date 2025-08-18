# 🚀 Scripts Directory

This directory contains the essential launcher scripts for the Student LMS AI project.

## 📋 Available Scripts

### **Frontend Launcher**
#### `frontend.sh`
- **Purpose**: Launch the Streamlit frontend application
- **Usage**: `./scripts/frontend.sh` (Unix/Linux/Mac) or `bash scripts/frontend.sh`
- **Features**: 
  - Launches Streamlit application directly
  - Uses existing virtual environment
  - Cross-platform compatibility

### **API Server Launcher**
#### `api.sh`
- **Purpose**: Launch the FastAPI backend server
- **Usage**: `./scripts/api.sh` (Unix/Linux/Mac) or `bash scripts/api.sh`
- **Features**: 
  - Starts uvicorn server with hot reload
  - Uses existing virtual environment
  - Accessible at http://localhost:8000

## 🎯 Usage

### **Starting the Frontend**
```bash
# From root directory
./scripts/frontend.sh

# Or if you're on Windows (using Git Bash or WSL)
bash scripts/frontend.sh
```

### **Starting the API Server**
```bash
# From root directory
./scripts/api.sh

# Or if you're on Windows (using Git Bash or WSL)
bash scripts/api.sh
```

### **Running Both (in separate terminals)**
```bash
# Terminal 1 - Start API server
./scripts/api.sh

# Terminal 2 - Start Frontend
./scripts/frontend.sh
```

## 🔧 Script Features

### **Error Handling**
- Directory existence checks
- Dependency verification
- User-friendly error messages
- Graceful failure handling

### **Cross-Platform Support**
- Windows batch files (`.bat`)
- Unix shell scripts (`.sh`)
- Python scripts (`.py`)
- Automatic path detection

### **User Experience**
- Clear status messages
- Progress indicators
- Helpful error messages
- Easy-to-follow instructions

## 🚀 Quick Start

1. **Navigate to project root:**
   ```bash
   cd stident_lms_ai_backend
   ```

2. **Start the API server (Terminal 1):**
   ```bash
   ./scripts/api.sh
   ```

3. **Start the Frontend (Terminal 2):**
   ```bash
   ./scripts/frontend.sh
   ```

4. **Access your application:**
   - **Frontend**: http://localhost:8501
   - **API**: http://localhost:8000
   - **API Docs**: http://localhost:8000/docs

## 🔍 Troubleshooting

### **Common Issues**

1. **Script not found:**
   - Ensure you're in the correct directory
   - Check if scripts folder exists

2. **uv not found:**
   ```bash
   pip install uv
   ```

3. **Permission denied (Unix/Linux/Mac):**
   ```bash
   chmod +x scripts/*.sh
   ```

4. **Dependencies missing:**
   - Install dependencies once from root directory: `uv sync`
   - Make sure you have a valid `pyproject.toml` file

### **Getting Help**

- Check the main `README.md` file
- Review `documents/PROJECT_OVERVIEW.md`
- Ensure backend is running before frontend
- Verify environment variables are set

## 📝 Notes

- All scripts are designed to be run from their respective directories
- The main launchers automatically navigate to the correct directory
- Scripts include error checking and user feedback
- Cross-platform compatibility is maintained across all scripts

---

**🎯 Use these scripts for easy launching of the Student LMS AI frontend!**
