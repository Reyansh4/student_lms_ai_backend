from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes import api_router
from core.config import settings
from routes import auth, roles, activities
import uvicorn
from sqlalchemy import create_engine
from db.base import Base
from db.session import engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Create all tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Student LMS",
    version="1.0.0",
    openapi_url=f"{settings.API_PREFIX}/openapi.json"
)

# Set up CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(api_router, prefix=settings.API_PREFIX)
app.include_router(auth.router)
app.include_router(roles.router)
app.include_router(activities.router)

@app.get("/")
def root():
    return {
        "message": "Welcome to the Learning Management System API",
        "docs_url": "/docs",
        "redoc_url": "/redoc"
    }

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True) 