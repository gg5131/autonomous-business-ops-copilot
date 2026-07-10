"""Graph Builder coordinating text parse models, extraction runs, and Neo4j database insertion."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Dict, List

from src.knowledge_graph.extractor import GraphExtractor
from src.knowledge_graph.neo4j_client import Neo4jClient
from src.observability.logging import get_logger

logger = get_logger(__name__)


class GraphBuilder:
    """Orchestrates ingestion parses, entity extraction, and Neo4j graph population."""

    def __init__(self, neo4j_client: Neo4jClient, extractor: GraphExtractor | None = None) -> None:
        self.client = neo4j_client
        self.extractor = extractor or GraphExtractor()

    async def initialize_schema(self) -> None:
        """Create indices and unique constraints on Neo4j for node matching."""
        logger.info("Initializing Neo4j schemas and constraints...")
        # Constraint to ensure name/title uniqueness within specific label scopes
        queries = [
            "CREATE CONSTRAINT unique_document_title IF NOT EXISTS FOR (d:Document) REQUIRE d.title IS UNIQUE",
            "CREATE CONSTRAINT unique_chunk_id IF NOT EXISTS FOR (c:Chunk) REQUIRE c.id IS UNIQUE",
            "CREATE CONSTRAINT unique_entity_name IF NOT EXISTS FOR (e:Entity) REQUIRE e.name IS UNIQUE",
            "CREATE CONSTRAINT unique_policy_name IF NOT EXISTS FOR (p:Policy) REQUIRE p.name IS UNIQUE",
            "CREATE CONSTRAINT unique_person_name IF NOT EXISTS FOR (pe:Person) REQUIRE pe.name IS UNIQUE",
            "CREATE CONSTRAINT unique_product_name IF NOT EXISTS FOR (pr:Product) REQUIRE pr.name IS UNIQUE",
            "CREATE CONSTRAINT unique_process_name IF NOT EXISTS FOR (pro:Process) REQUIRE pro.name IS UNIQUE",
            "CREATE INDEX entity_name_idx IF NOT EXISTS FOR (e:Entity) ON (e.name)",
        ]
        for query in queries:
            try:
                await self.client.execute_query(query)
            except Exception as e:
                logger.error("Schema constraint creation failed", error=str(e), query=query)

    async def insert_document_nodes(
        self,
        doc_id: str,
        title: str,
        metadata: Dict[str, Any],
        chunks: List[str],
        chunk_ids: List[str],
    ) -> None:
        """Inserts Document and Chunk nodes, linking them with BELONGS_TO relationships."""
        logger.info("Inserting document and chunks to Neo4j", title=title, chunk_count=len(chunks))

        # 1. Insert Document Node
        doc_cypher = (
            "MERGE (d:Document {title: $title}) "
            "SET d.id = $id, d.author = $author, d.date = $date, "
            "    d.source = $source, d.department = $department, d.language = $language "
            "RETURN d"
        )
        lineage = metadata.get("lineage") or {}
        doc_params = {
            "title": title,
            "id": doc_id,
            "author": lineage.get("author") or "system",
            "date": str(lineage.get("date") or datetime.utcnow()),
            "source": lineage.get("source") or "unknown",
            "department": lineage.get("department") or "general",
            "language": lineage.get("language") or "en",
        }
        await self.client.execute_query(doc_cypher, doc_params)

        # 2. Insert Chunk Nodes and link to Document
        chunk_cypher = (
            "MATCH (d:Document {title: $doc_title}) "
            "MERGE (c:Chunk {id: $chunk_id}) "
            "SET c.content = $content, c.index = $idx "
            "MERGE (c)-[r:BELONGS_TO]->(d) "
            "SET r.confidence = 1.0, r.extraction_source = 'ingestion', r.extraction_timestamp = $timestamp "
            "RETURN c"
        )
        timestamp = datetime.utcnow().isoformat()

        for idx, chunk in enumerate(chunks):
            chunk_params = {
                "doc_title": title,
                "chunk_id": chunk_ids[idx],
                "content": chunk,
                "idx": idx,
                "timestamp": timestamp,
            }
            await self.client.execute_query(chunk_cypher, chunk_params)

    async def insert_extracted_graph(
        self, graph_data: Dict[str, List[Dict[str, Any]]], chunk_id: str
    ) -> None:
        """Inserts entities and links them with relationships containing confidence metrics."""
        logger.info(
            "Inserting extracted graph elements",
            nodes=len(graph_data.get("nodes", [])),
            relationships=len(graph_data.get("relationships", [])),
        )

        # 1. Insert Entity/Node elements (Policy, Person, Product, Process, or general Entity)
        node_cypher_template = (
            "MERGE (n:{label} {{name: $name}}) "
            "SET n.description = $description, n.confidence = $confidence, "
            "    n.extraction_source = $source, n.extraction_timestamp = $timestamp "
            "WITH n "
            "MATCH (c:Chunk {{id: $chunk_id}}) "
            "MERGE (c)-[r:MENTIONS]->(n) "
            "SET r.confidence = $confidence, r.extraction_source = $source, r.extraction_timestamp = $timestamp "
            "RETURN n"
        )

        for node in graph_data.get("nodes", []):
            label = node["type"]  # e.g., Policy, Person, Entity...
            cypher = node_cypher_template.format(label=label)
            params = {
                "name": node["name"],
                "description": node["properties"].get("description", ""),
                "confidence": node["confidence"],
                "source": node["extraction_source"],
                "timestamp": node["extraction_timestamp"],
                "chunk_id": chunk_id,
            }
            await self.client.execute_query(cypher, params)

        # 2. Insert Relationships between nodes (MENTIONS, BELONGS_TO, RELATED_TO, REFERENCES, DERIVED_FROM, VERSION_OF)
        rel_cypher_template = (
            "MATCH (src:{source_label} {{name: $source_name}}) "
            "MATCH (dst:{target_label} {{name: $target_name}}) "
            "MERGE (src)-[r:{rel_type}]->(dst) "
            "SET r.confidence = $confidence, r.extraction_source = $source, r.extraction_timestamp = $timestamp "
            "RETURN r"
        )

        for rel in graph_data.get("relationships", []):
            cypher = rel_cypher_template.format(
                source_label=rel["source_type"],
                target_label=rel["target_type"],
                rel_type=rel["type"],
            )
            params = {
                "source_name": rel["source_node"],
                "target_name": rel["target_node"],
                "confidence": rel["confidence"],
                "source": rel["extraction_source"],
                "timestamp": rel["extraction_timestamp"],
            }
            await self.client.execute_query(cypher, params)
