"""Neo4j Client — Async connection manager and query execution."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from neo4j import AsyncGraphDatabase
from tenacity import retry, stop_after_attempt, wait_exponential

from configs.settings import get_settings
from src.observability.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()


class Neo4jClient:
    """Manages connection lifecycles and async Cypher query runs in Neo4j."""

    def __init__(self) -> None:
        self.uri = settings.neo4j.uri
        self.user = settings.neo4j.user
        self.password = settings.neo4j.password
        self.database = settings.neo4j.database
        logger.info("Initializing Neo4j Async Driver", uri=self.uri)
        self._driver = AsyncGraphDatabase.driver(
            self.uri,
            auth=(self.user, self.password),
        )

    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True,
    )
    async def verify_connectivity(self) -> None:
        """Ping database connection to ensure Neo4j connectivity at startup."""
        logger.info("Verifying Neo4j connection...")
        async with self._driver.session(database=self.database) as session:
            await session.run("RETURN 1")
        logger.info("Neo4j connectivity verified successfully.")

    async def close(self) -> None:
        """Close driver connections pool."""
        logger.info("Closing Neo4j Driver pool.")
        await self._driver.close()

    async def execute_query(
        self, cypher: str, parameters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Run Cypher read/write queries and yield parsed dictionaries."""
        logger.debug("Executing Cypher query", cypher=cypher)
        async with self._driver.session(database=self.database) as session:
            try:
                result = await session.run(cypher, parameters)
                records = await result.data()
                return records
            except Exception as e:
                logger.error("Cypher query execution failed", error=str(e), query=cypher)
                raise
