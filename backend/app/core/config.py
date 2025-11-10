"""Application configuration management."""

from typing import List
from pydantic import validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application
    APP_NAME: str = "SEO SaaS Tool"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "production"

    # API
    API_V1_PREFIX: str = "/api/v1"
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # Database
    DATABASE_URL: str
    DB_POOL_SIZE: int = 20
    DB_MAX_OVERFLOW: int = 10

    # Redis
    REDIS_URL: str
    REDIS_CACHE_DB: int = 1

    # Celery
    CELERY_BROKER_URL: str
    CELERY_RESULT_BACKEND: str

    # Meilisearch
    MEILISEARCH_URL: str
    MEILISEARCH_KEY: str

    # Crawler
    CRAWLER_USER_AGENT: str = "SEO-SaaS-Bot/1.0"
    CRAWLER_MAX_CONCURRENT: int = 10
    CRAWLER_DELAY: float = 1.0
    CRAWLER_RESPECT_ROBOTS: bool = True
    PLAYWRIGHT_HEADLESS: bool = True
    PLAYWRIGHT_TIMEOUT: int = 30000

    # LLM Providers
    OPENAI_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""
    HUGGINGFACE_API_KEY: str = ""

    # S3 Storage
    S3_ENDPOINT: str
    S3_ACCESS_KEY: str
    S3_SECRET_KEY: str
    S3_BUCKET: str
    S3_SECURE: bool = False

    # Monitoring
    PROMETHEUS_ENABLED: bool = True
    PROMETHEUS_PORT: int = 9090

    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000"]

    @validator("CORS_ORIGINS", pre=True)
    def parse_cors_origins(cls, v: str | List[str]) -> List[str]:
        """Parse CORS origins from string or list."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.strip("[]").split(",")]
        return v

    class Config:
        """Pydantic config."""

        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = Settings()
