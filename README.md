# Student LMS AI Backend

A modern, FastAPI-based Learning Management System backend with AI capabilities, designed to provide a robust and scalable platform for educational institutions.

## 🚀 Features

- FastAPI-based RESTful API
- PostgreSQL database with SQLAlchemy ORM
- JWT-based authentication and authorization
- AI-powered learning features
- Comprehensive API documentation (Swagger/OpenAPI)
- Modern Python 3.11+ codebase
- Type hints and validation with Pydantic
- Database migrations with Alembic
- Comprehensive test suite

## 📋 Prerequisites

- Python 3.11 or higher
- PostgreSQL database
- Virtual environment (recommended)

## 🛠️ Installation

1. Clone the repository:
```bash
git clone git@github.com:Reyansh4/stident_lms_ai_backend.git
cd student_lms_ai_backend
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
# On Windows
.\venv\Scripts\activate
# On Unix or MacOS
source venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
Create a `.env` file in the root directory with the following variables:
```env
DATABASE_URL=postgresql://user:password@localhost:5432/dbname
SECRET_KEY=your-secret-key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

5. Run database migrations:
```bash
alembic upgrade head
```

## 🏃‍♂️ Running the Application

Start the development server:
```bash
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`
API documentation will be available at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## 🧪 Testing

Run the test suite:
```bash
pytest
```

For coverage report:
```bash
pytest --cov=app
```

## �� Project Structure
