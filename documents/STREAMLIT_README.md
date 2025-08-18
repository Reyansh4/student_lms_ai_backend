# 🎓 Student LMS AI - Streamlit Frontend

A modern, interactive Streamlit application that provides a chatbot interface for students to interact with the Student LMS AI backend. This app allows students to login, chat with an AI assistant, create and manage activities, and access learning resources.

## ✨ Features

### 🔐 Authentication
- **User Login/Logout**: Secure authentication using JWT tokens
- **User Registration**: New user signup functionality
- **Session Management**: Persistent user sessions

### 🤖 AI Chatbot Interface
- **Intelligent Conversations**: Chat with AI assistant about learning topics
- **Context Awareness**: AI remembers conversation history and user preferences
- **Learning Support**: Get help with subjects, activities, and learning strategies

### 📚 Activity Management
- **Create Activities**: Build new learning activities with AI assistance
- **List Activities**: Browse and search through existing activities
- **Edit Activities**: Modify activity details and content
- **Start Activities**: Begin learning sessions with AI guidance
- **Delete Activities**: Remove unwanted activities

### 🎯 Smart Features
- **AI-Powered Creation**: Automatic activity generation with AI descriptions
- **Category Management**: Dynamic category and subcategory creation
- **Difficulty Levels**: Support for Beginner, Intermediate, and Advanced activities
- **Access Control**: Private and global activity sharing options

### 💬 Chat Memory
- **Conversation History**: Persistent chat memory across sessions
- **Search & Filter**: Find specific conversations and topics
- **Export Options**: Save chat history for future reference

## 🚀 Quick Start

### Prerequisites
- Python 3.8 or higher
- Student LMS AI Backend running on `http://localhost:8000`
- Database populated with sample data

### Installation

1. **Clone or download the Streamlit app files**
   ```bash
   # Make sure you have the following files:
   # - streamlit_app.py
   # - streamlit_requirements.txt
   # - STREAMLIT_README.md
   ```

2. **Install dependencies**
   ```bash
   pip install -r streamlit_requirements.txt
   ```

3. **Start the backend API** (if not already running)
   ```bash
   # In your backend directory
   uvicorn app.main:app --host 0.0.0.0 --port 8000
   ```

4. **Run the Streamlit app**
   ```bash
   streamlit run streamlit_app.py
   ```

5. **Open your browser**
   - Navigate to `http://localhost:8501`
   - The app will automatically open in your default browser

## 🔧 Configuration

### API Endpoint
The app is configured to connect to the backend at `http://localhost:8000/api/v1`. To change this:

1. Open `streamlit_app.py`
2. Modify the `API_BASE_URL` variable:
   ```python
   API_BASE_URL = "http://your-backend-url:port/api/v1"
   ```

### Demo Credentials
Use these pre-created accounts for testing:
- **Email**: `user1@example.com`
- **Password**: `password123`

## 📱 Usage Guide

### 1. Getting Started
1. **Login**: Use your credentials or create a new account
2. **Navigate**: Use the sidebar for quick access to different features
3. **Chat**: Start a conversation with the AI assistant

### 2. Chatting with AI
- **Ask Questions**: "Help me with calculus" or "Create a physics quiz"
- **Get Recommendations**: "What activities should I try?"
- **Request Help**: "I'm stuck on this math problem"

### 3. Managing Activities
- **Create**: Use the "Create Activity" button or ask AI to create one
- **Browse**: View all activities with search and filter options
- **Modify**: Edit activity details, descriptions, and settings
- **Start**: Begin learning sessions with AI guidance

### 4. Quick Actions
- **📚 List Activities**: View all available activities
- **➕ Create Activity**: Build new learning content
- **🎯 Start Activity**: Begin a learning session
- **❓ Get Help**: Access AI assistance

## 🏗️ Architecture

### Frontend (Streamlit)
- **User Interface**: Modern, responsive web interface
- **State Management**: Session state for user data and preferences
- **API Integration**: RESTful API calls to backend services
- **Real-time Updates**: Dynamic content updates and notifications

### Backend Integration
- **Authentication**: JWT token-based security
- **API Communication**: HTTP requests to backend endpoints
- **Data Management**: CRUD operations for activities and user data
- **AI Services**: Integration with chatbot and AI generation services

### Data Flow
```
User Input → Streamlit App → API Request → Backend Processing → AI Response → Frontend Display
```

## 🔒 Security Features

- **JWT Authentication**: Secure token-based authentication
- **Session Management**: Protected user sessions
- **Input Validation**: Client-side and server-side validation
- **Error Handling**: Secure error messages without data leakage

## 📊 Supported Activity Types

### Categories
- **Mathematics**: Algebra, Geometry, Calculus, Statistics
- **Science**: Physics, Chemistry, Biology, Astronomy
- **Language Arts**: Grammar, Literature, Writing, Vocabulary
- **History**: Ancient, Modern, World, American History
- **Computer Science**: Programming, Data Structures, Algorithms

### Difficulty Levels
- **Beginner**: Basic concepts and fundamentals
- **Intermediate**: Moderate complexity and depth
- **Advanced**: Complex topics and advanced applications

### Access Types
- **Private**: Personal learning activities
- **Global**: Shared with all users

## 🛠️ Troubleshooting

### Common Issues

1. **Connection Error**
   - Ensure backend is running on `http://localhost:8000`
   - Check firewall and network settings
   - Verify API endpoint configuration

2. **Authentication Failed**
   - Check user credentials
   - Ensure backend has user data
   - Verify JWT token configuration

3. **Activity Creation Failed**
   - Check required fields (name, category)
   - Verify backend permissions
   - Check API response for specific errors

4. **Chat Not Working**
   - Ensure AI services are running
   - Check backend agent configuration
   - Verify memory store setup

### Debug Mode
Enable debug logging by modifying the app:
```python
# Add to streamlit_app.py
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 🔄 API Endpoints Used

The app integrates with these backend endpoints:

- **Authentication**: `/auth/login`, `/auth/signup`, `/auth/me`
- **Activities**: `/activities/`, `/activities/create_enhanced`
- **Categories**: `/activities/categories`, `/activities/categories/{id}/subcategories`
- **AI Chat**: `/agent/chat`, `/agent/start-activity`
- **Sessions**: `/activities/{id}/sessions`

## 🚀 Deployment

### Local Development
```bash
streamlit run streamlit_app.py --server.port 8501
```

### Production Deployment
1. **Environment Variables**: Set production API endpoints
2. **HTTPS**: Enable SSL certificates
3. **Load Balancing**: Use reverse proxy (nginx)
4. **Monitoring**: Implement logging and health checks

### Docker Deployment
```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8501
CMD ["streamlit", "run", "streamlit_app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

## 🤝 Contributing

1. **Fork the repository**
2. **Create a feature branch**
3. **Make your changes**
4. **Test thoroughly**
5. **Submit a pull request**

## 📝 License

This project is part of the Student LMS AI system. Please refer to the main project license for details.

## 🆘 Support

For support and questions:
- Check the troubleshooting section
- Review backend logs and API responses
- Ensure all dependencies are properly installed
- Verify backend services are running correctly

---

**🎉 Happy Learning with AI! 🎉**
