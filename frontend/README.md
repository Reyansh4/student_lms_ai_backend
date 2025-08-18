# 🎓 Student LMS AI Frontend

This is the frontend application for the Student LMS AI system, built with Streamlit.

## 🏗️ Project Structure

```
frontend/
├── components/          # Reusable UI components
│   ├── auth.py         # Authentication components
│   ├── navigation.py   # Navigation components
│   └── chat.py         # Chat interface components
├── pages/              # Page components
│   └── memory.py       # Memory sessions page
├── utils/              # Utility functions
│   ├── config.py       # Configuration settings
│   └── api.py          # API request functions
├── main.py             # Main application entry point
├── requirements.txt    # Python dependencies
└── README.md          # This file
```

## 🚀 Features

- **Vertical Sidebar**: Navigation with New Chat, Chat & Conversations, and Memory Sessions
- **Horizontal Top Bar**: Quick action buttons for common tasks
- **Chat Interface**: AI-powered learning assistant chat
- **Memory Management**: Automatic session saving and retrieval
- **Responsive Design**: Modern, clean UI with proper styling

## 🎯 Navigation Structure

### Vertical Sidebar
- **New Chat**: Start fresh conversations
- **Chat & Conversations**: Manage current chat sessions
- **Memory Sessions**: Access saved chat history
- **System Info**: API status and connection info

### Horizontal Top Bar
- **Get Help**: Quick access to help topics
- **Learning Topics**: Explore available subjects
- **Study Tips**: Get study advice
- **Search**: Search for learning resources

## 🛠️ Installation

1. **Navigate to frontend directory:**
   ```bash
   cd frontend
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application:**
   ```bash
   streamlit run main.py
   ```

## 🔧 Configuration

The application configuration is in `utils/config.py`:
- API base URL
- Streamlit page settings
- CSS styling

## 📱 Usage

1. **Login/Signup**: Use the authentication system to access the app
2. **Start Chatting**: Begin conversations with the AI learning assistant
3. **Quick Actions**: Use the horizontal bar for common tasks
4. **Memory Access**: View and load previous chat sessions
5. **Navigation**: Use the vertical sidebar for app navigation

## 🔌 API Integration

The frontend communicates with the backend through:
- `/auth/*` - Authentication endpoints
- `/agent/chat` - AI chat functionality
- `/memory/*` - Memory management endpoints

## 🎨 Styling

Custom CSS is applied for:
- Chat message styling
- Navigation bars
- Button designs
- Responsive layout

## 🚀 Alternative Launch Methods

### **From Root Directory (Recommended)**
```bash
# Python launcher
python scripts/launch_frontend.py

# Windows batch file
scripts\launch_frontend.bat
```

### **From Scripts Directory**
```bash
# Python launcher
python scripts/run_frontend.py

# Windows batch file
scripts\run_frontend.bat

# Unix/Linux/Mac shell script
./scripts/run_frontend.sh
```

## 🔍 Troubleshooting

### **Common Issues**

1. **Dependencies missing:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Backend not running:**
   - Ensure backend is running on port 8000
   - Check API_BASE_URL in `utils/config.py`

3. **Import errors:**
   - Ensure you're running from the frontend directory
   - Check that all `__init__.py` files exist

### **Getting Help**

- Check the main project README
- Review `documents/PROJECT_OVERVIEW.md`
- Ensure backend is running before frontend
- Verify environment variables are set

## 📚 More Documentation

For comprehensive project information, see:
- **`documents/PROJECT_OVERVIEW.md`** - Complete project guide
- **`documents/FRONTEND_RESTRUCTURE.md`** - Frontend restructure details

---

**🎯 This frontend provides an intuitive interface for the Student LMS AI system!**
