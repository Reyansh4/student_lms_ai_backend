# 🎓 Student LMS AI

An intelligent learning management system powered by AI, built with FastAPI backend and Streamlit frontend.

## 🚀 Quick Start

### **Start API Server (Terminal 1)**
```bash
./scripts/api.sh
```

### **Start Frontend (Terminal 2)**
```bash
./scripts/frontend.sh
```

### **Direct Launch (Alternative)**
```bash
cd frontend
uv run streamlit run main.py
```

## 📁 Project Structure

- **`frontend/`** - Streamlit frontend application
- **`scripts/`** - Launcher and utility scripts
- **`documents/`** - Project documentation
- **`app/`** - FastAPI backend application

## 📚 Documentation

- **`documents/PROJECT_OVERVIEW.md`** - Comprehensive project guide
- **`documents/FRONTEND_RESTRUCTURE.md`** - Frontend restructure details
- **`frontend/README.md`** - Frontend-specific documentation

## 🔧 Installation

1. **Install uv (if not already installed):**
   ```bash
   pip install uv
   ```

2. **Set up environment variables** (see `.env.example`)

3. **Install dependencies once:**
   ```bash
   # From root directory - installs all dependencies
   uv sync
   ```

4. **Run the application:**
   ```bash
   # Terminal 1 - API Server
   ./scripts/api.sh
   
   # Terminal 2 - Frontend
   ./scripts/frontend.sh
   ```

## 🎯 Features

- 🤖 AI-powered learning assistant
- 🧠 Intelligent memory management
- 🎨 Modern, responsive UI
- 🔐 Secure user authentication
- 📱 Horizontal and vertical navigation
- 📝 **Unified logging system** - All logs in single `app.log` file

## 📝 Logging & Debugging

The application uses a **unified logging system** where both frontend and backend write to the same `logs/app.log` file. This makes debugging much easier:

### **Log File Location**
```
logs/app.log
```

### **What Gets Logged**
- **Frontend**: User actions, API calls, navigation, authentication
- **Backend**: API requests, database operations, system events
- **Format**: `timestamp - logger_name - level - message`

### **Viewing Logs**
```bash
# View real-time logs
tail -f logs/app.log

# View last 50 lines
tail -n 50 logs/app.log

# Search for specific logs
grep "frontend" logs/app.log
grep "app." logs/app.log
```

### **Test Logging System**
```bash
python test_logging.py
```

## 📖 More Information

For detailed documentation, see the `documents/` folder.

---

**Built with ❤️ using FastAPI + Streamlit + Azure OpenAI**
