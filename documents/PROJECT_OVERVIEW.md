# 🎓 Student LMS AI - Project Overview

## 📋 Project Description

Student LMS AI is an intelligent learning management system that provides AI-powered educational assistance through a modern web interface. The system combines advanced AI capabilities with intuitive user experience to enhance learning outcomes.

## 🏗️ Project Structure

```
stident_lms_ai_backend/
├── 📁 frontend/                 # Streamlit frontend application
│   ├── 📁 components/           # Reusable UI components
│   │   ├── auth.py             # Authentication system
│   │   ├── navigation.py       # Navigation components
│   │   └── chat.py             # Chat interface
│   ├── 📁 pages/               # Page components
│   │   └── memory.py           # Memory sessions page
│   ├── 📁 utils/               # Utility functions
│   │   ├── config.py           # Configuration settings
│   │   └── api.py              # API communication
│   ├── main.py                 # Main application entry point
│   └── requirements.txt        # Python dependencies
├── 📁 scripts/                  # Launcher and utility scripts
│   ├── launch_frontend.py      # Main launcher script
│   ├── launch_frontend.bat     # Windows batch launcher
│   ├── run_frontend.py         # Frontend launcher
│   ├── run_frontend.bat        # Windows frontend launcher
│   └── run_frontend.sh         # Unix/Linux/Mac launcher
├── 📁 documents/                # Project documentation
│   ├── PROJECT_OVERVIEW.md     # This file
│   ├── FRONTEND_RESTRUCTURE.md # Frontend restructure guide
│   └── README.md               # Frontend specific README
├── 📁 app/                     # Backend FastAPI application
│   ├── 📁 api/                 # API endpoints
│   ├── 📁 agents/              # AI agent system
│   ├── 📁 config/              # Backend configuration
│   ├── 📁 core/                # Core functionality
│   ├── 📁 db/                  # Database models
│   ├── 📁 embeddings/          # AI embedding system
│   ├── 📁 memory/              # Memory management
│   ├── 📁 models/              # Data models
│   ├── 📁 prompts/             # AI prompts
│   ├── 📁 routes/              # API routes
│   ├── 📁 services/            # Business logic
│   ├── 📁 tools/               # AI tools
│   └── main.py                 # Backend entry point
├── 📁 tests/                    # Test suite
├── 📁 alembic/                  # Database migrations
├── 📁 assets/                   # Static assets
├── 📁 logs/                     # Application logs
├── 📁 migrations/               # Database migrations
├── requirements.txt             # Backend dependencies
├── pyproject.toml              # Project configuration
└── streamlit_app.py            # Legacy frontend (can be removed)
```

## 🚀 Quick Start

### **Option 1: Using Scripts (Recommended)**
```bash
# From root directory
python scripts/launch_frontend.py

# Windows users
scripts\launch_frontend.bat
```

### **Option 2: Direct Launch**
```bash
cd frontend
streamlit run main.py
```

### **Option 3: Using Frontend Scripts**
```bash
# Python launcher
python scripts/run_frontend.py

# Windows batch
scripts\run_frontend.bat

# Unix/Linux/Mac
./scripts/run_frontend.sh
```

## 🔧 Installation

1. **Install Backend Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Install Frontend Dependencies:**
   ```bash
   cd frontend
   pip install -r requirements.txt
   ```

3. **Set up Environment Variables:**
   - Create `.env` file with Azure OpenAI credentials
   - Configure database connection settings

4. **Run Backend:**
   ```bash
   uvicorn app.main:app --reload
   ```

5. **Run Frontend:**
   ```bash
   python scripts/launch_frontend.py
   ```

## 🎯 Key Features

### **🤖 AI-Powered Learning Assistant**
- Intelligent chat interface
- Context-aware responses
- Learning topic assistance
- Study tips and guidance

### **🧠 Memory Management**
- Automatic session saving
- Chat history retrieval
- Search across conversations
- Session management

### **🎨 Modern User Interface**
- Horizontal and vertical navigation
- Quick action buttons
- Responsive design
- Clean, intuitive layout

### **🔐 User Authentication**
- Secure login/signup
- Session management
- User profile management

## 🔌 API Endpoints

### **Authentication**
- `POST /auth/login` - User login
- `POST /auth/signup` - User registration
- `GET /auth/me` - Get user info

### **AI Chat**
- `POST /agent/chat` - AI chat completion

### **Memory Management**
- `GET /memory/sessions` - List sessions
- `POST /memory/sessions` - Create session
- `GET /memory/sessions/{id}/history` - Get session history
- `POST /memory/sessions/{id}/messages` - Add message
- `GET /memory/sessions/{id}/search` - Search in session

## 🛠️ Development

### **Frontend Development**
- **Location:** `frontend/` directory
- **Framework:** Streamlit
- **Structure:** Component-based architecture
- **Styling:** Custom CSS with responsive design

### **Backend Development**
- **Location:** `app/` directory
- **Framework:** FastAPI
- **Database:** SQLAlchemy with Alembic migrations
- **AI:** Azure OpenAI integration

### **Adding New Features**
1. Create new components in `frontend/components/`
2. Add new pages in `frontend/pages/`
3. Update navigation in `frontend/components/navigation.py`
4. Test thoroughly before deployment

## 📚 Documentation

- **`documents/PROJECT_OVERVIEW.md`** - This comprehensive overview
- **`documents/FRONTEND_RESTRUCTURE.md`** - Frontend restructure guide
- **`documents/README.md`** - Frontend-specific documentation
- **`frontend/README.md`** - Frontend component documentation

## 🧪 Testing

```bash
# Run all tests
python -m pytest tests/

# Run specific test file
python -m pytest tests/test_integration.py

# Run with coverage
python -m pytest --cov=app tests/
```

## 🚀 Deployment

### **Local Development**
```bash
# Backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Frontend
cd frontend
streamlit run main.py --server.port 8501
```

### **Production**
- Use production WSGI server (Gunicorn)
- Configure reverse proxy (Nginx)
- Set up SSL certificates
- Use environment variables for configuration

## 🔒 Security

- JWT token authentication
- Secure password hashing
- API rate limiting
- Input validation and sanitization
- CORS configuration

## 📊 Monitoring

- Application logging
- Error tracking
- Performance monitoring
- User analytics

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License.

## 🆘 Support

For support and questions:
- Check the documentation in `documents/`
- Review the code structure
- Check existing issues
- Create a new issue with detailed description

---

**🎉 Welcome to Student LMS AI!** This system combines the power of AI with modern web technologies to create an exceptional learning experience.
