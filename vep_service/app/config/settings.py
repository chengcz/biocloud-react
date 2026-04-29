"""VEP Service Settings

Service-specific configuration for standalone VEP annotation service.
NO authentication settings - this service is open access.
"""

from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """VEP Service settings loaded from environment variables"""

    # Service Info
    SERVICE_NAME: str = "VEP Annotation Service"
    SERVICE_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8001

    # Database (no auth required)
    DATABASE_URL: str = "postgresql+asyncpg://vep_user:vep_password@localhost:5432/vep_cache"

    # VEP Configuration
    VEP_DATA_DIR: str = "/data/vep_data"
    SPECIES_CONFIG_PATH: str = "config/species.yaml"
    VEP_TIMEOUT: int = 300  # 5 minutes
    MAX_VCF_SIZE: int = 50 * 1024 * 1024  # 50MB
    VEP_CACHE_RESULTS: bool = True

    # File Storage
    UPLOAD_DIR: str = "/tmp/vep_service/uploads"
    MAX_UPLOAD_SIZE: int = 100 * 1024 * 1024  # 100MB

    # CORS
    CORS_ORIGINS: list[str] = ["*"]  # Open access

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()


settings = get_settings()