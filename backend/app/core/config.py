"""Application Configuration Module."""
import os
from pydantic_settings import BaseSettings
from pydantic import ConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "EXAMFLOW Backend"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Database
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", 
        "postgresql+asyncpg://postgres:postgres@localhost:5432/examflow"
    )
    # Sync database URL for Alembic migrations
    SYNC_DATABASE_URL: str = os.getenv(
        "SYNC_DATABASE_URL",
        "postgresql://postgres:postgres@localhost:5432/examflow"
    )
    
    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "examflow-super-secret-key-change-in-production-2024")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 1 day
    
    # Environment
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    CORS_ORIGINS: list[str] = ["*"]
    
    model_config = ConfigDict(case_sensitive=True, env_file=".env", extra="ignore")


settings = Settings()
