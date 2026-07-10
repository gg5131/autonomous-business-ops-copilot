"""SQLite database engine and session maker fallback using aiosqlite."""

from __future__ import annotations

from pathlib import Path
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from configs.settings import get_settings
from src.observability.logging import get_logger

logger = get_logger(__name__)

settings = get_settings()

# Create SQLite parent directories if needed
sqlite_file = Path(settings.sqlite.db_path)
sqlite_file.parent.mkdir(parents=True, exist_ok=True)

from sqlalchemy import event

# Create sqlite fallback async engine
sqlite_engine = create_async_engine(
    settings.sqlite.async_dsn,
    pool_pre_ping=True,
    echo=False,
)

# Enable foreign keys for SQLite connection session
@event.listens_for(sqlite_engine.sync_engine, "connect")
def set_sqlite_pragma(dbapi_connection: any, connection_record: any) -> None:
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


# Async session maker
sqlite_session_maker = async_sessionmaker(
    bind=sqlite_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def verify_sqlite_connection() -> None:
    """Verifies SQLite connection and creates directories if needed."""
    logger.info("Verifying SQLite fallback connection...")
    async with sqlite_engine.connect() as conn:
        from sqlalchemy import text

        await conn.execute(text("SELECT 1"))
    logger.info("SQLite connection verified successfully.")


async def get_sqlite_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency for yielding SQLite session context."""
    async with sqlite_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
