"""Main FastAPI application definition and startup lifespan checks."""

from __future__ import annotations

import os
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncGenerator

import uvicorn
from fastapi import FastAPI

from configs.settings import get_settings
from src.api.exceptions import ConfigurationError, register_exception_handlers
from src.api.middleware.cors import setup_cors
from src.api.middleware.rate_limit import RateLimiter
from src.api.middleware.trace import TracingMiddleware
from src.api.routers import analytics, health, knowledge, review, tickets
from src.database.postgres import verify_postgres_connection
from src.database.sqlite_fallback import verify_sqlite_connection
from src.api.routers.health import check_chroma, check_neo4j
from src.observability.logging import get_logger, setup_logging

# Setup structlog framework before initializing FastAPI
setup_logging()
logger = get_logger(__name__)

settings = get_settings()


async def run_startup_validations() -> None:
    """Verifies that configs, databases, vector stores, and directories are available."""
    logger.info("Initializing startup validations...")

    # 1. Directory Checks
    project_root = settings.project_root
    required_dirs = [
        project_root / "logs",
        project_root / "data",
        project_root / "data" / "faiss_indices",
    ]
    for directory in required_dirs:
        try:
            directory.mkdir(parents=True, exist_ok=True)
            logger.info("Directory validated", path=str(directory))
        except Exception as e:
            raise ConfigurationError(
                f"Failed to create/validate required directory: {directory}",
                details={"error": str(e)},
            )

    # 2. Config & Env Verification
    # Check Gemini API Key
    if not settings.gemini.api_key:
        logger.warn("GEMINI_API_KEY environment variable is not configured. LLM calls will fail.")

    # 3. Database Connectivity Validation
    try:
        if settings.is_production:
            await verify_postgres_connection()
        else:
            await verify_sqlite_connection()
    except Exception as e:
        raise ConfigurationError("Database connection validation failed.", details={"error": str(e)})

    # 4. Neo4j Availability Check
    logger.info("Verifying Neo4j graph database connectivity...")
    if not check_neo4j():
        raise ConfigurationError("Neo4j database is unreachable. Check network or credentials.")
    logger.info("Neo4j connection verified successfully.")

    # 5. ChromaDB Availability Check
    logger.info("Verifying ChromaDB vector store connectivity...")
    chroma_ok = await check_chroma()
    if not chroma_ok:
        raise ConfigurationError("ChromaDB vector store is unreachable. Check configuration.")
    logger.info("ChromaDB connection verified successfully.")

    logger.info("Startup validations completed successfully.")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Lifespan event context manager, validating services on startup."""
    try:
        await run_startup_validations()
    except ConfigurationError as ce:
        logger.critical("Startup validation failed! Aborting service start.", error=ce.message, details=ce.details)
        # Abort startup by raising exception
        raise ce
    except Exception as e:
        logger.critical("Unexpected startup check failure! Aborting service start.", error=str(e))
        raise ConfigurationError("Unexpected startup check failure", details={"error": str(e)}) from e

    yield

    logger.info("Application shutting down...")


# Create FastAPI App Factory
def create_app() -> FastAPI:
    """FastAPI application factory configuring exception handlers, middlewares, and routers."""
    app = FastAPI(
        title=settings.app_name,
        debug=settings.app_debug,
        lifespan=lifespan,
    )

    # 1. Register middleware stack (order of execution: Tracing -> RateLimiter -> CORS)
    app.add_middleware(TracingMiddleware)
    app.add_middleware(RateLimiter)
    setup_cors(app)

    # 2. Register exception handlers
    register_exception_handlers(app)

    # 3. Register routers
    app.include_router(health.router, prefix="/api/v1")
    app.include_router(tickets.router, prefix="/api/v1")
    app.include_router(review.router, prefix="/api/v1")
    app.include_router(analytics.router, prefix="/api/v1")
    app.include_router(knowledge.router, prefix="/api/v1")

    return app


app = create_app()


def run() -> None:
    """Programmatic entry point to run Uvicorn server."""
    uvicorn.run(
        "src.api.main:app",
        host=settings.api.host,
        port=settings.api.port,
        reload=settings.api.reload,
        workers=settings.api.workers,
    )


if __name__ == "__main__":
    run()
