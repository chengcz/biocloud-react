"""API dependencies for dependency injection"""

from typing import AsyncGenerator, Optional
from fastapi import Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.database import get_db as get_db_session
from app.core.security import get_current_user, get_current_active_user, CheckPermission
from app.models import UserModel


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Get database session"""
    async for session in get_db_session():
        yield session


def get_pagination_params(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Page size")
) -> dict:
    """Get pagination parameters"""
    return {"page": page, "page_size": page_size}


class PaginationParams:
    """Pagination parameters class"""

    def __init__(
        self,
        page: int = Query(1, ge=1, description="Page number"),
        page_size: int = Query(20, ge=1, le=100, description="Page size")
    ):
        self.page = page
        self.page_size = page_size
        self.offset = (page - 1) * page_size
        self.limit = page_size


# Re-export security dependencies
__all__ = [
    "get_db",
    "get_pagination_params",
    "PaginationParams",
    "get_current_user",
    "get_current_active_user",
    "CheckPermission",
]