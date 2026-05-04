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
    DB_HOST: str = getenv("DB_HOST", "localhost")
    DB_PORT: str = getenv("DB_PORT", "5434")
    DB_NAME: str = getenv("DB_NAME", "pg-biocloud")
    DB_USER: str = getenv("DB_USER", "postgres")
    DB_PASSWORD: str = getenv("DB_PASSWORD", "postgres")

    # Create database URL (computed from DB settings)
    @property
    def DATABASE_URL(self) -> str:
        """Compute database URL from connection settings (async driver)"""
        return f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"


    # JWT Settings
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # LLM Settings
    ANTHROPIC_API_KEY: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None
    DEFAULT_LLM_MODEL: str = "claude"

    # LLM Model Mappings (provider -> litellm model name)
    LLM_MODEL_CLAUDE: str = "anthropic/claude-sonnet-4-20250514"
    LLM_MODEL_CLAUDE_FAST: str = "anthropic/claude-3-5-haiku-20241022"

    LLM_MODEL_OPENAI: str = "openai/gpt-4o"
    LLM_MODEL_OPENAI_FAST: str = "openai/gpt-4o-mini"

    LLM_MODEL_LOCAL: str = "ollama/llama3"

    # Conversation defaults
    CONVERSATION_DEFAULT_MODEL: str = "claude"

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

