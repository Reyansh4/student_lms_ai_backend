from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
import logging
import time
from contextlib import asynccontextmanager

from app.config.settings import settings
from app.config.langfuse_config import langfuse_manager, APITracker
from app.api import auth, activities, permissions, roles, embeddings, memory
from app.core.logger import setup_logging

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    logger.info("🚀 Starting Student LMS AI Backend...")
    logger.info(f"📊 Environment: {settings.ENVIRONMENT}")
    logger.info(f"🔧 Debug mode: {settings.DEBUG}")
    logger.info(f"🌐 API prefix: {settings.API_PREFIX}")
    logger.info(f"📝 Log level: {settings.LOG_LEVEL}")
    
    # Initialize Langfuse
    if langfuse_manager.is_enabled():
        logger.info("✅ Langfuse observability enabled")
    else:
        logger.warning("⚠️ Langfuse observability disabled - check credentials")
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down Student LMS AI Backend...")

# Create FastAPI app
app = FastAPI(
    title="Student LMS AI Backend",
    description="A comprehensive Learning Management System with AI capabilities",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add trusted host middleware
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=settings.ALLOWED_HOSTS
)

# Langfuse tracing middleware
@app.middleware("http")
async def langfuse_tracing_middleware(request: Request, call_next):
    """Middleware to track all HTTP requests with Langfuse"""
    start_time = time.time()
    
    # Extract user info from request if available
    user_id = None
    if hasattr(request.state, 'user'):
        user_id = str(request.state.user.get('id', 'anonymous'))
    
    # Create API tracker
    api_tracker = APITracker(
        endpoint=str(request.url.path),
        method=request.method,
        user_id=user_id
    )
    
    # Track request
    request_data = {}
    if request.method in ["POST", "PUT", "PATCH"]:
        try:
            body = await request.body()
            if body:
                import json
                request_data = json.loads(body.decode())
        except:
            request_data = {"raw_body": str(body)}
    
    api_tracker.track_request(request_data, dict(request.headers))
    
    try:
        # Process request
        response = await call_next(request)
        
        # Track response
        response_data = {}
        if hasattr(response, 'body'):
            try:
                response_body = response.body.decode()
                response_data = {"body": response_body}
            except:
                response_data = {"raw_body": str(response.body)}
        
        api_tracker.track_response(response_data, response.status_code)
        api_tracker.finish_api_trace("success")
        
        # Add timing header
        process_time = time.time() - start_time
        response.headers["X-Process-Time"] = str(process_time)
        
        return response
        
    except Exception as e:
        # Track error
        api_tracker.finish_api_trace("error", str(e))
        logger.error(f"Request failed: {str(e)}")
        raise

# Include routers
app.include_router(auth.router, prefix=settings.API_PREFIX, tags=["Authentication"])
app.include_router(activities.router, prefix=settings.API_PREFIX, tags=["Activities"])
app.include_router(permissions.router, prefix=settings.API_PREFIX, tags=["Permissions"])
app.include_router(roles.router, prefix=settings.API_PREFIX, tags=["Roles"])
app.include_router(embeddings.router, prefix=settings.API_PREFIX, tags=["Embeddings"])
app.include_router(memory.router, prefix=settings.API_PREFIX, tags=["Memory"])

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Student LMS AI Backend",
        "version": "1.0.0",
        "status": "running",
        "langfuse_enabled": langfuse_manager.is_enabled()
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "langfuse_status": "enabled" if langfuse_manager.is_enabled() else "disabled"
    }

