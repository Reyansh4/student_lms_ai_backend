from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.logger import get_logger
from app.routes import api_router
from app.db.base import Base
from app.db.session import engine
# Import agent router
from app.agent.routers import router as agent_router
from app.api.memory import router as memory_router
# from app.tools.swagger_loader import clear_openapi_spec_cache, get_openapi_spec
# from app.tools.swagger_connectors import register_swagger_tools

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

# Include agent router
app.include_router(agent_router, prefix=f"{settings.API_PREFIX}/agent", tags=["agent"])
logger.info("Agent router included")

app.include_router(memory_router, prefix=f"{settings.API_PREFIX}/memory", tags=["memory"])
logger.info("Memory router included")

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

