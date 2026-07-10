"""PostgreSQL database engine and session maker setup using SQLAlchemy asyncpg."""

from __future__ import annotations

from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from tenacity import retry, stop_after_attempt, wait_exponential

from configs.settings import get_settings
from src.observability.logging import get_logger

logger = get_logger(__name__)

settings = get_settings()

# Create async engine with robust connection pooling settings
postgres_engine = create_async_engine(
    settings.postgres.async_dsn,
    pool_size=20,
    max_overflow=10,
    pool_recycle=1800,
    pool_pre_ping=True,
    echo=False,
)

# Async session maker
postgres_session_maker = async_sessionmaker(
    bind=postgres_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


@retry(
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    reraise=True,
)
async def verify_postgres_connection() -> None:
    """Verifies connection to Postgres DB at startup, retrying on failure."""
    logger.info("Verifying PostgreSQL connection...")
    async with postgres_engine.connect() as conn:
        from sqlalchemy import text

        await conn.execute(text("SELECT 1"))
    logger.info("PostgreSQL connection verified successfully.")


async def get_postgres_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency for yielding database session context."""
    async with postgres_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
