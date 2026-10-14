from pathlib import Path
from typing import Literal

from pydantic import model_validator

from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    DATABASE_URL: str
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    MAX_UPLOAD_SIZE_MB: int = 10

    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 150

    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_KEEP_ALIVE: str = "30m"

    # "ollama" for local development, "gemini" for the hosted demo.
    LLM_PROVIDER: Literal["ollama", "gemini"] = "ollama"
    EMBEDDING_PROVIDER: Literal["ollama", "gemini"] = "ollama"

    LLM_MODEL: str = "qwen2.5:3b"
    LLM_MAX_TOKENS: int = 120
    LLM_TIMEOUT_SECONDS: int = 300

    EMBEDDING_MODEL: str = "nomic-embed-text"
    EMBEDDING_TIMEOUT_SECONDS: int = 60

    # Previous messages included in the prompt of a conversation turn.
    CONVERSATION_HISTORY_MESSAGES: int = 6

    GEMINI_API_KEY: str | None = None
    GEMINI_LLM_MODEL: str = "gemini-3.1-flash-lite"
    GEMINI_MAX_TOKENS: int = 1024
    GEMINI_EMBEDDING_MODEL: str = "gemini-embedding-2"

    HEALTH_CHECK_TIMEOUT_SECONDS: int = 3

    # Comma-separated list of allowed frontend origins.
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:5173"

    @model_validator(mode="after")
    def _require_provider_keys(self) -> "Settings":
        if "gemini" in (self.LLM_PROVIDER, self.EMBEDDING_PROVIDER) and not (
            self.GEMINI_API_KEY
        ):
            raise ValueError("Using the gemini provider requires GEMINI_API_KEY")

        return self

    @property
    def cors_origins_list(self) -> list[str]:
        return [
            origin.strip()
            for origin in self.CORS_ORIGINS.split(",")
            if origin.strip()
        ]

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        # .env also holds variables for docker-compose (POSTGRES_*, ...).
        extra="ignore"
    )


settings = Settings()  # pyright: ignore[reportCallIssue]