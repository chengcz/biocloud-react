"""API v1 routes"""

from fastapi import APIRouter

from .auth import router as auth_router
from .users import router as user_router, dept_router, role_router

api_router = APIRouter()

# Include all routers
api_router.include_router(auth_router)
api_router.include_router(user_router)
api_router.include_router(dept_router)
api_router.include_router(role_router)