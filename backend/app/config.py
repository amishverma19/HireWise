from functools import lru_cache
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application Settings for HireWise Backend.
    Loads environment variables from .env file or system environment.
    """
    GEMINI_API_KEY: str = ""
    DATABASE_URL: str = ""
    LLM_MODEL: str = "gemini-2.0-flash"
    FALLBACK_LLM_MODELS: str = "gemini-3.8-flash,gemini-flash-latest,gemini-1.5-flash"
    EMBEDDING_MODEL: str = "gemini-embedding-001"
    JWT_SECRET: str = "hirewise-super-secret-jwt-key-2026-production"
    CORS_ORIGINS: str = "http://localhost:3000,http://127.0.0.1:3000"
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM: str = ""
    SMTP_USE_TLS: bool = True

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    @property
    def cors_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    @property
    def async_database_url(self) -> str:
        """
        Ensures the connection string uses the async psycopg dialect (postgresql+psycopg://)
        and formats parameters cleanly for asyncpg / psycopg engines.
        """
        if not self.DATABASE_URL:
            return ""
        
        url = self.DATABASE_URL.strip()
        # Normalize protocol to postgresql+psycopg://
        if url.startswith("postgres://"):
            url = "postgresql+psycopg://" + url[len("postgres://"):]
        elif url.startswith("postgresql://") and not url.startswith("postgresql+"):
            url = "postgresql+psycopg://" + url[len("postgresql://"):]
        
        # Remove unsupported query parameters for psycopg async if any
        if "channel_binding=" in url:
            parts = url.split("?")
            if len(parts) == 2:
                base, query = parts
                query_params = [p for p in query.split("&") if not p.startswith("channel_binding=")]
                url = base + ("?" + "&".join(query_params) if query_params else "")

        return url


def get_settings() -> Settings:
    return Settings()
