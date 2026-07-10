"""Graph Traversal strategies using Neo4j clients with relationship confidence filtering."""

from __future__ import annotations

from typing import Any, Dict, List

from src.knowledge_graph.neo4j_client import Neo4jClient
from src.observability.logging import get_logger

logger = get_logger(__name__)


class GraphTraversal:
    """Provides methods to navigate Neo4j graph nodes and query relationships with confidence filtering."""

    def __init__(self, client: Neo4jClient) -> None:
        self.client = client

    async def get_neighbors(self, entity_name: str, min_confidence: float = 0.0) -> List[Dict[str, Any]]:
        """Retrieve all nodes connected to target entity with confidence exceeding threshold."""
        logger.info("Traversing neighbors", entity=entity_name, min_confidence=min_confidence)

        # Enforce Neo4j relationships confidence filters in Cypher query
        cypher = (
            "MATCH (n {name: $name})-[r]-(m) "
            "WHERE r.confidence >= $min_conf "
            "RETURN m.name as name, labels(m)[0] as label, type(r) as relationship, r.confidence as confidence"
        )
        params = {"name": entity_name, "min_conf": min_confidence}

        try:
            records = await self.client.execute_query(cypher, params)
            return records
        except Exception as e:
            logger.error("Failed to traverse neighbors", error=str(e), entity=entity_name)
            return []

    async def get_document_lineage(self, doc_title: str) -> List[Dict[str, Any]]:
        """Retrieve lineage trace nodes for a given document."""
        cypher = (
            "MATCH (d:Document {title: $title}) "
            "RETURN d.title as title, d.author as author, d.date as date, d.source as source, d.department as department"
        )
        params = {"title": doc_title}
        try:
            return await self.client.execute_query(cypher, params)
        except Exception as e:
            logger.error("Failed to retrieve document lineage", error=str(e), title=doc_title)
            return []
