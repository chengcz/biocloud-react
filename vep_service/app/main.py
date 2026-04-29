"""VEP Annotation Service - Standalone FastAPI Application

NO authentication middleware - open access service.
Runs on port 8001 separately from main backend.
"""

import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config.settings import settings
from app.config.database import init_db
from app.api.vep import router as vep_router

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan - startup and shutdown events"""
    # Startup
    logger.info(f"Starting {settings.SERVICE_NAME} v{settings.SERVICE_VERSION}")

    # Create upload directory
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

    # Initialize database tables
    await init_db()
    logger.info("Database tables initialized")

    yield

    # Shutdown
    logger.info("Shutting down VEP service")


def create_app() -> FastAPI:
    """Create FastAPI application (NO auth middleware)"""
    app = FastAPI(
        title=settings.SERVICE_NAME,
        version=settings.SERVICE_VERSION,
        description="VEP annotation service - open access, no authentication required",
        lifespan=lifespan,
    )

    # CORS - open access
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include VEP router
    app.include_router(vep_router)

    # Health check endpoint (no auth)
    @app.get("/health")
    async def health_check():
        """Health check endpoint (NO AUTH)"""
        return {
            "service": settings.SERVICE_NAME,
            "version": settings.SERVICE_VERSION,
            "status": "healthy",
        }

    # Root endpoint
    @app.get("/")
    async def root():
        """Root endpoint (NO AUTH)"""
        return {
            "service": settings.SERVICE_NAME,
            "version": settings.SERVICE_VERSION,
            "docs": "/docs",
            "health": "/health",
        }

    return app


# Create application instance
app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
    )