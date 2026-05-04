#!/usr/bin/env python
# -*- coding: utf-8 -*-

from os import getenv
from pydantic_settings import BaseSettings
from typing import Optional
from functools import lru_cache
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # Application
    APP_NAME: str = "BioCloud API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False


    # Database connection settings
    DB_HOST: getenv("DB_HOST", "localhost")
    DB_PORT: getenv("DB_PORT", "5434")
    DB_NAME: getenv("DB_NAME", "competitive_intelligence")
    DB_USER: getenv("DB_USER", "postgres")
    DB_PASSWORD: getenv("DB_PASSWORD", "postgres")

    # Create database URL
    DATABASE_URL: f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"


    # JWT Settings
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # LLM Settings
    ANTHROPIC_API_KEY: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None
    DEFAULT_LLM_MODEL: str = "claude"

    # File Storage
    UPLOAD_DIR: str = "/tmp/biocloud/uploads"
    MAX_UPLOAD_SIZE: int = 100 * 1024 * 1024  # 100MB

    # CORS
    CORS_ORIGINS: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()


settings = get_settings()

