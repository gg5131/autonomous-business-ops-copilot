"""Unified hybrid retrieval pipeline executing sparse, dense, and graph search in parallel."""

from __future__ import annotations

import asyncio
import time
from typing import Any, Dict, List, Optional

from src.knowledge_graph.neo4j_client import Neo4jClient
from src.knowledge_graph.traversal import GraphTraversal
from src.retrieval.bm25 import BM25Index
from src.retrieval.embeddings import EmbeddingService
from src.retrieval.fusion import ReciprocalRankFusion
from src.retrieval.query_engine import QueryEngineService
from src.retrieval.reranker import CrossEncoderReranker
from src.retrieval.vector_store import ChromaVectorStore
from src.observability.logging import get_logger

logger = get_logger(__name__)


class HybridRetrievalPipeline:
    """Orchestrates search intents, parallel queries, rank fusion, and cross-encoder reranking."""

    def __init__(
        self,
        embedding_service: EmbeddingService,
        vector_store: ChromaVectorStore,
        bm25_index: BM25Index,
        neo4j_client: Neo4jClient,
        query_engine: QueryEngineService | None = None,
        fusion: ReciprocalRankFusion | None = None,
        reranker: CrossEncoderReranker | None = None,
    ) -> None:
        self.embedding_service = embedding_service
        self.vector_store = vector_store
        self.bm25_index = bm25_index
        self.neo4j_client = neo4j_client
        self.traversal = GraphTraversal(neo4j_client)

        self.query_engine = query_engine or QueryEngineService()
        self.fusion = fusion or ReciprocalRankFusion()
        self.reranker = reranker or CrossEncoderReranker()

    async def _search_graph(self, query: str, min_confidence: float = 0.6, limit: int = 5) -> List[Dict[str, Any]]:
        """Traverse graph matching entities linked to chunks with confidence threshold filters."""
        # Simple keyword matching on entities in Neo4j to find linked chunks
        words = [w for w in query.split() if len(w) > 3]
        if not words:
            return []

        # Find chunks mentioning matching entities
        cypher = (
            "MATCH (e) WHERE any(w in $words WHERE toLower(e.name) CONTAINS toLower(w)) "
            "MATCH (c:Chunk)-[r:MENTIONS]->(e) "
            "WHERE r.confidence >= $min_conf "
            "RETURN c.id as id, c.content as content, r.confidence as confidence, labels(e)[0] as entity_type "
            "LIMIT $limit"
        )
        params = {"words": words, "min_conf": min_confidence, "limit": limit}

        try:
            records = await self.neo4j_client.execute_query(cypher, params)
            candidates = []
            for record in records:
                candidates.append(
                    {
                        "id": record["id"],
                        "content": record["content"],
                        "metadata": {"source": "graph_retriever", "entity_type": record["entity_type"]},
                        "score": float(record["confidence"]),
                    }
                )
            return candidates
        except Exception as e:
            logger.error("Graph database retrieval failed", error=str(e))
            return []

    async def retrieve(
        self,
        query: str,
        limit: int = 5,
        min_graph_confidence: float = 0.6,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Execute unified search pipeline sequence, logging latencies and errors."""
        start_time = time.time()
        logger.info("Starting hybrid retrieval pipeline execution", query=query)

        try:
            # 1. Intent Detection
            intent = await self.query_engine.detect_intent(query)
            logger.info("Query intent classified", intent=intent)

            # 2. Query Expansion (Multi-Query Generation)
            expanded_queries = await self.query_engine.expand_query(query)
            primary_and_expanded = [query] + expanded_queries
            logger.info("Expanded query variants generated", count=len(primary_and_expanded))

            # 3. Parallel Search Execution (BM25 + ChromaDB + Neo4j)
            bm25_tasks = []
            vector_tasks = []
            graph_tasks = []

            # Batch generate all query embeddings concurrently before search starts
            logger.info("Batch generating query embeddings...")
            query_embeddings = await self.embedding_service.get_embeddings(primary_and_expanded)

            for idx, q in enumerate(primary_and_expanded):
                # BM25 Search Task (synchronous lexical, wrapped in executor)
                bm25_tasks.append(asyncio.to_thread(self.bm25_index.search, q, limit=limit * 2))

                # ChromaDB Vector Search Task (synchronous HTTP client query, wrapped in threadpool)
                # Map pre-computed embeddings to avoid nested await calls inside search tasks
                q_emb = query_embeddings[idx]
                vector_tasks.append(
                    asyncio.to_thread(self.vector_store.search, q_emb, limit=limit * 2, filters=filters)
                )

                # Neo4j Graph Search Task (native async network operations)
                graph_tasks.append(self._search_graph(q, min_confidence=min_graph_confidence, limit=limit * 2))

            # Execute all tasks in parallel
            logger.info("Dispatching parallel queries to retrieval engines...")
            bm25_results, vector_results, graph_results = await asyncio.gather(
                asyncio.gather(*bm25_tasks),
                asyncio.gather(*vector_tasks),
                asyncio.gather(*graph_tasks),
            )


            # Flatten result lists
            flat_bm25 = [item for sublist in bm25_results for item in sublist]
            flat_vector = [item for sublist in vector_results for item in sublist]
            flat_graph = [item for sublist in graph_results for item in sublist]

            logger.info(
                "Parallel query retrieval complete",
                bm25_candidates=len(flat_bm25),
                vector_candidates=len(flat_vector),
                graph_candidates=len(flat_graph),
            )

            # 4. Reciprocal Rank Fusion (RRF)
            fused_candidates = self.fusion.fuse([flat_bm25, flat_vector, flat_graph])
            logger.info("Rank fusion complete", candidate_pool_size=len(fused_candidates))

            # Deduplicate fused candidates by id to ensure unique list before reranking
            unique_candidates: List[Dict[str, Any]] = []
            seen_ids = set()
            for cand in fused_candidates:
                if cand["id"] not in seen_ids:
                    seen_ids.add(cand["id"])
                    unique_candidates.append(cand)

            # 5. Cross-Encoder Reranking
            reranked_results = self.reranker.rerank(query, unique_candidates, limit=limit)
            logger.info("Cross-Encoder reranking complete", returned_count=len(reranked_results))

            elapsed = (time.time() - start_time) * 1000.0
            logger.info("Hybrid retrieval pipeline execution successful", latency_ms=elapsed)

            return reranked_results

        except Exception as e:
            logger.error("Hybrid retrieval pipeline execution failed", error=str(e))
            raise
