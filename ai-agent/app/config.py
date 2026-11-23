
"""Configuration management for EXAMFLOW AI.
Handles Secret Manager integration, Llama endpoints, and environment variables.
"""

import os
import secrets
from typing import Optional
from pydantic import BaseModel, Field


class Settings(BaseModel):
    # App & Environment
    PROJECT_NAME: str = "EXAMFLOW AI"
    PROJECT_ID: str = "AI-056"
    PROBLEM_STATEMENT: str = "PS-072 – Online Exam Proctoring Result Engine"

    ENVIRONMENT: str = Field(
        default_factory=lambda: os.getenv("ENVIRONMENT", "development")
    )
    DEBUG: bool = Field(
        default_factory=lambda: os.getenv("DEBUG", "false").lower() == "true"
    )
    HOST: str = Field(default_factory=lambda: os.getenv("HOST", "0.0.0.0"))
    PORT: int = Field(default_factory=lambda: int(os.getenv("PORT", "8080")))

    # Google Cloud
    GCP_PROJECT: Optional[str] = Field(
        default_factory=lambda: os.getenv("GOOGLE_CLOUD_PROJECT")
    )
    GCS_BUCKET_NAME: Optional[str] = Field(
        default_factory=lambda: os.getenv("GCS_BUCKET_NAME")
    )

    # Llama API
    LLAMA_API_BASE_URL: str = Field(
        default_factory=lambda: os.getenv(
            "LLAMA_API_BASE_URL",
            "https://api.groq.com/openai/v1"
        )
    )
    LLAMA_API_KEY: str = Field(
        default_factory=lambda: os.getenv("LLAMA_API_KEY", "")
    )
    LLAMA_MODEL_ID: str = Field(
        default_factory=lambda: os.getenv(
            "LLAMA_MODEL_ID",
            "llama-3.3-70b-versatile"
        )
    )
    LLAMA_TIMEOUT_SECONDS: float = Field(
        default_factory=lambda: float(os.getenv("LLAMA_TIMEOUT_SECONDS", "30.0"))
    )
    LLAMA_MAX_RETRIES: int = Field(
        default_factory=lambda: int(os.getenv("LLAMA_MAX_RETRIES", "3"))
    )
    LLAMA_MAX_TOKENS: int = Field(
        default_factory=lambda: int(os.getenv("LLAMA_MAX_TOKENS", "4096"))
    )
    LLAMA_CONTEXT_WINDOW: int = Field(
        default_factory=lambda: int(os.getenv("LLAMA_CONTEXT_WINDOW", "8192"))
    )

    # PDF & Document Processing
    UPLOAD_DIR: str = Field(
        default_factory=lambda: os.getenv(
            "UPLOAD_DIR",
            os.path.join(
                os.path.dirname(os.path.dirname(__file__)),
                "uploads"
            )
        )
    )
    MAX_FILE_SIZE_MB: int = Field(
        default_factory=lambda: int(os.getenv("MAX_FILE_SIZE_MB", "25"))
    )
    CHUNK_SIZE: int = Field(
        default_factory=lambda: int(os.getenv("CHUNK_SIZE", "600"))
    )
    CHUNK_OVERLAP: int = Field(
        default_factory=lambda: int(os.getenv("CHUNK_OVERLAP", "100"))
    )

    # Security
    SECRET_KEY: str = Field(
        default_factory=lambda: os.getenv("SECRET_KEY", "")
    )
    ACTION_CONFIRMATION_TIMEOUT_MINUTES: int = 15

    def get_secret(self, secret_id: str, default: str = "") -> str:
        """Fetch a secret from Google Secret Manager, then environment."""
        if self.GCP_PROJECT:
            try:
                from google.cloud import secretmanager

                client = secretmanager.SecretManagerServiceClient()
                name = (
                    f"projects/{self.GCP_PROJECT}/secrets/"
                    f"{secret_id}/versions/latest"
                )
                response = client.access_secret_version(
                    request={"name": name}
                )
                value = response.payload.data.decode("UTF-8").strip()
                if value:
                    return value
            except Exception:
                # Do not expose secret-manager details in application responses.
                # Production validation below will reject a missing secret.
                pass

        return os.getenv(secret_id, default)

    def initialize_secrets(self):
        """Load secrets and validate the security configuration."""

        if not self.LLAMA_API_KEY:
            self.LLAMA_API_KEY = self.get_secret("LLAMA_API_KEY", "")

        if not self.SECRET_KEY:
            self.SECRET_KEY = self.get_secret("SECRET_KEY", "")

        environment = self.ENVIRONMENT.strip().lower()

        if environment in {"production", "prod"}:
            if not self.SECRET_KEY or len(self.SECRET_KEY) < 32:
                raise RuntimeError(
                    "Production requires SECRET_KEY with at least "
                    "32 characters. Configure it using Google Secret "
                    "Manager or the SECRET_KEY environment variable."
                )
        elif not self.SECRET_KEY:
            # Ephemeral development-only key.
            # Approval tokens will not survive an application restart.
            self.SECRET_KEY = secrets.token_urlsafe(48)


settings = Settings()
settings.initialize_secrets()
