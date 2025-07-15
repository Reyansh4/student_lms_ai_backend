from fastapi import APIRouter
from app.routes import auth, roles, activities, permissions, documents

api_router = APIRouter()

# Include all routers
api_router.include_router(auth.router)
api_router.include_router(roles.router, prefix="/roles", tags=["roles"])
api_router.include_router(permissions.router, prefix="/permissions", tags=["permissions"])
api_router.include_router(activities.router, prefix="/activities", tags=["activities"])
