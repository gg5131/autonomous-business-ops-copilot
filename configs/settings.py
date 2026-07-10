"""Application settings — Pydantic Settings with environment-aware configuration."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class GeminiSettings(BaseSettings):
    """Gemini API configuration settings."""

    model_config = SettingsConfigDict(
        env_prefix="GEMINI_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    api_key: str = Field(default="", description="Gemini API key")
    model_planner: str = Field(default="gemini-2.5-pro", description="Model for planner agent")
    model_default: str = Field(default="gemini-2.5-flash", description="Default model for agents")
    model_draft: str = Field(default="gemini-2.5-pro", description="Model for draft agent")


class Neo4jSettings(BaseSettings):
    """Neo4j connection configuration settings."""

    model_config = SettingsConfigDict(
        env_prefix="NEO4J_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    uri: str = Field(default="bolt://localhost:7687", description="Neo4j Bolt URI")
    user: str = Field(default="neo4j", description="Neo4j username")
    password: str = Field(default="", description="Neo4j password")
    database: str = Field(default="neo4j", description="Neo4j database name")


class PostgresSettings(BaseSettings):
    """PostgreSQL connection configuration settings."""

    model_config = SettingsConfigDict(
        env_prefix="POSTGRES_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    host: str = Field(default="localhost", description="PostgreSQL host")
    port: int = Field(default=5432, description="PostgreSQL port")
    user: str = Field(default="copilot", description="PostgreSQL username")
    password: str = Field(default="", description="PostgreSQL password")
    db: str = Field(default="copilot_db", description="PostgreSQL database name")

    @property
    def async_dsn(self) -> str:
        """Async DSN for asyncpg connection."""
        return f"postgresql+asyncpg://{self.user}:{self.password}@{self.host}:{self.port}/{self.db}"

    @property
    def sync_dsn(self) -> str:
        """Sync DSN for SQLAlchemy migrations."""
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.db}"


class SQLiteSettings(BaseSettings):
    """SQLite configuration settings for local development and fallback."""

    model_config = SettingsConfigDict(
        env_prefix="SQLITE_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    db_path: str = Field(default="./data/copilot_dev.db", description="SQLite database file path")

    @property
    def async_dsn(self) -> str:
        """Async DSN for aiosqlite connection."""
        return f"sqlite+aiosqlite:///{self.db_path}"


class ChromaSettings(BaseSettings):
    """ChromaDB configuration settings."""

    model_config = SettingsConfigDict(
        env_prefix="CHROMA_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    host: str = Field(default="localhost", description="ChromaDB host")
    port: int = Field(default=8000, description="ChromaDB port")
    collection: str = Field(default="copilot_documents", description="Default collection name")


class EmbeddingSettings(BaseSettings):
    """Embedding model configuration settings."""

    model_config = SettingsConfigDict(
        env_prefix="EMBEDDING_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    model: str = Field(default="all-MiniLM-L6-v2", description="Sentence transformer model name")
    dimension: int = Field(default=384, description="Embedding vector dimension")


class APISettings(BaseSettings):
    """API server configuration settings."""

    model_config = SettingsConfigDict(
        env_prefix="API_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    host: str = Field(default="0.0.0.0", description="API bind host")
    port: int = Field(default=8000, description="API bind port")
    workers: int = Field(default=1, description="Number of Uvicorn workers")
    reload: bool = Field(default=True, description="Enable auto-reload in development")


class RateLimitSettings(BaseSettings):
    """Rate limiting configuration settings."""

    model_config = SettingsConfigDict(
        env_prefix="RATE_LIMIT_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    requests: int = Field(default=100, description="Max requests per window")
    window_seconds: int = Field(default=60, description="Rate limit window in seconds")


class SecuritySettings(BaseSettings):
    """Security configuration settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    jwt_secret_key: str = Field(default="change-me-in-production", env="JWT_SECRET_KEY")
    jwt_algorithm: str = Field(default="HS256", env="JWT_ALGORITHM")
    jwt_expiration_minutes: int = Field(default=60, env="JWT_EXPIRATION_MINUTES")
    pii_detection_enabled: bool = Field(default=True, env="PII_DETECTION_ENABLED")
    prompt_injection_defense_enabled: bool = Field(
        default=True, env="PROMPT_INJECTION_DEFENSE_ENABLED"
    )


class RetrievalSettings(BaseSettings):
    """Retrieval pipeline configuration settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    bm25_top_k: int = Field(default=25, env="BM25_TOP_K")
    vector_top_k: int = Field(default=25, env="VECTOR_TOP_K")
    graph_top_k: int = Field(default=25, env="GRAPH_TOP_K")
    reranker_top_k: int = Field(default=5, env="RERANKER_TOP_K")
    rrf_k: int = Field(default=60, env="RRF_K")


class ConfidenceSettings(BaseSettings):
    """Confidence engine configuration settings."""

    model_config = SettingsConfigDict(
        env_prefix="CONFIDENCE_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    high_threshold: int = Field(default=85, description="Score >= this is HIGH confidence")
    low_threshold: int = Field(default=60, description="Score < this is LOW confidence")


class ObservabilitySettings(BaseSettings):
    """Observability and tracing configuration settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    langfuse_public_key: str = Field(default="", env="LANGFUSE_PUBLIC_KEY")
    langfuse_secret_key: str = Field(default="", env="LANGFUSE_SECRET_KEY")
    langfuse_host: str = Field(default="https://cloud.langfuse.com", env="LANGFUSE_HOST")
    enable_tracing: bool = Field(default=True, env="ENABLE_TRACING")


class CostTrackingSettings(BaseSettings):
    """Cost tracking configuration settings for Gemini API."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    gemini_flash_input_cost_per_1k: float = Field(
        default=0.000075, env="GEMINI_FLASH_INPUT_COST_PER_1K"
    )
    gemini_flash_output_cost_per_1k: float = Field(
        default=0.0003, env="GEMINI_FLASH_OUTPUT_COST_PER_1K"
    )
    gemini_pro_input_cost_per_1k: float = Field(
        default=0.00125, env="GEMINI_PRO_INPUT_COST_PER_1K"
    )
    gemini_pro_output_cost_per_1k: float = Field(default=0.005, env="GEMINI_PRO_OUTPUT_COST_PER_1K")


class Settings(BaseSettings):
    """Root application settings class aggregating all settings groups."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Core Application Configuration
    app_name: str = Field(default="Autonomous Business Ops Copilot", env="APP_NAME")
    app_env: Literal["development", "testing", "production"] = Field(
        default="development", env="APP_ENV"
    )
    app_debug: bool = Field(default=True, env="APP_DEBUG")
    app_log_level: str = Field(default="INFO", env="APP_LOG_LEVEL")
    app_secret_key: str = Field(default="change-me-in-production", env="APP_SECRET_KEY")

    # CORS settings
    cors_origins: list[str] = Field(default=["http://localhost:8501"], env="CORS_ORIGINS")
    cors_allow_credentials: bool = Field(default=True, env="CORS_ALLOW_CREDENTIALS")

    # Aggregate Settings Objects
    gemini: GeminiSettings = Field(default_factory=GeminiSettings)
    neo4j: Neo4jSettings = Field(default_factory=Neo4jSettings)
    postgres: PostgresSettings = Field(default_factory=PostgresSettings)
    sqlite: SQLiteSettings = Field(default_factory=SQLiteSettings)
    chroma: ChromaSettings = Field(default_factory=ChromaSettings)
    embedding: EmbeddingSettings = Field(default_factory=EmbeddingSettings)
    api: APISettings = Field(default_factory=APISettings)
    rate_limit: RateLimitSettings = Field(default_factory=RateLimitSettings)
    security: SecuritySettings = Field(default_factory=SecuritySettings)
    retrieval: RetrievalSettings = Field(default_factory=RetrievalSettings)
    confidence: ConfidenceSettings = Field(default_factory=ConfidenceSettings)
    observability: ObservabilitySettings = Field(default_factory=ObservabilitySettings)
    cost_tracking: CostTrackingSettings = Field(default_factory=CostTrackingSettings)

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: str | list[str]) -> list[str]:
        """Convert a string representation of list to actual list if needed."""
        if isinstance(value, str):
            import json

            try:
                parsed = json.loads(value)
                if isinstance(parsed, list):
                    return [str(item) for item in parsed]
            except json.JSONDecodeError:
                return [x.strip() for x in value.split(",") if x.strip()]
        return value  # type: ignore

    @property
    def is_production(self) -> bool:
        """Helper checking if running in production mode."""
        return self.app_env == "production"

    @property
    def is_testing(self) -> bool:
        """Helper checking if running in testing mode."""
        return self.app_env == "testing"

    @property
    def database_dsn(self) -> str:
        """Select database DSN based on the environment."""
        if self.is_production:
            return self.postgres.async_dsn
        return self.sqlite.async_dsn

    @property
    def project_root(self) -> Path:
        """Return the absolute path of the project root."""
        return Path(__file__).resolve().parent.parent


def get_settings() -> Settings:
    """Settings factory function."""
    return Settings()
