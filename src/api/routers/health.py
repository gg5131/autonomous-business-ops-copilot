"""Health check router verifying database and external dependency availability."""

from __future__ import annotations

import httpx
from fastapi import APIRouter, Depends, status
from neo4j import GraphDatabase
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from configs.settings import get_settings
from src.api.dependencies import get_db
from src.api.schemas.common import APIResponse
from src.observability.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/health", tags=["system"])
settings = get_settings()


async def check_database(db: AsyncSession) -> bool:
    """Execute simple ping query to check database responsiveness."""
    try:
        await db.execute(text("SELECT 1"))
        return True
    except Exception as e:
        logger.error("Health Check: Database connection failed", error=str(e))
        return False


def check_neo4j() -> bool:
    """Validate connection to Neo4j database endpoint."""
    try:
        # Use Driver connection check
        with GraphDatabase.driver(
            settings.neo4j.uri,
            auth=(settings.neo4j.user, settings.neo4j.password),
            connection_timeout=2.0,
        ) as driver:
            driver.verify_connectivity()
        return True
    except Exception as e:
        logger.error("Health Check: Neo4j connection failed", error=str(e))
        return False


async def check_chroma() -> bool:
    """Validate connectivity to ChromaDB REST endpoint."""
    url = f"http://{settings.chroma.host}:{settings.chroma.port}/api/v1/heartbeat"
    try:
        async with httpx.AsyncClient(timeout=2.0) as client:
            response = await client.get(url)
            return response.status_code == 200
    except Exception as e:
        logger.error("Health Check: ChromaDB heartbeat failed", error=str(e))
        return False


@router.get("", response_model=APIResponse[dict])
async def get_health_status(db: AsyncSession = Depends(get_db)) -> dict:
    """Returns dynamic status metrics for external database dependencies."""
    db_ok = await check_database(db)
    neo4j_ok = check_neo4j()
    chroma_ok = await check_chroma()

    all_healthy = db_ok and neo4j_ok and chroma_ok
    status_msg = "healthy" if all_healthy else "degraded"

    # Set status header code implicitly if degraded is desired,
    # but here we return a standard APIResponse container.
    return {
        "success": all_healthy,
        "data": {
            "status": status_msg,
            "dependencies": {
                "relational_db": "up" if db_ok else "down",
                "neo4j_graph": "up" if neo4j_ok else "down",
                "chromadb_vector": "up" if chroma_ok else "down",
            },
        },
    }
