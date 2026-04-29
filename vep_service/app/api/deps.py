"""API Dependencies for VEP Service

Database session ONLY - NO authentication dependencies.
Open access service - no user validation required.
"""

from sqlalchemy.ext.asyncio import AsyncSession
from app.config.database import get_db as _get_db


async def get_db() -> AsyncSession:
    """
    Get database session dependency (NO AUTH).

    This is a standalone service - no authentication required.
    Just yields database session directly.
    """
    return _get_db()