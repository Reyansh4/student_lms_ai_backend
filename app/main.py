from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.logger import get_logger
from app.routes import api_router
from app.db.base import Base
from app.db.session import engine

# Initialize logger
logger = get_logger(__name__)

# Create all tables
try:
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created successfully")
except Exception as e:
    logger.error(f"Error creating database tables: {str(e)}")
    raise

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_PREFIX}/openapi.json"
)

logger.info("Initializing FastAPI application")

# Set up CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
logger.info("CORS middleware configured")

# Include routers
app.include_router(api_router, prefix=settings.API_PREFIX)
logger.info("API routers included")

@app.get("/")
def root():
    """
    Root endpoint returning API information.
    """
    logger.info("Root endpoint accessed")
    return {
        "message": "Welcome to the Learning Management System API",
        "version": settings.VERSION,
        "docs_url": "/docs",
        "redoc_url": "/redoc"
    }

@app.on_event("startup")
async def startup_event():
    """
    Startup event handler.
    """
    logger.info("Application startup")

@app.on_event("shutdown")
async def shutdown_event():
    """
    Shutdown event handler.
    """
    logger.info("Application shutdown")

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting Uvicorn server")
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level=settings.LOG_LEVEL.lower()
    ) 