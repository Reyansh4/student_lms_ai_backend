from fastapi import APIRouter
from routes import auth, roles, activities

api_router = APIRouter()

api_router.include_router(auth.router)
api_router.include_router(roles.router)
api_router.include_router(activities.router)
