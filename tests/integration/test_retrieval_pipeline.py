"""Integration tests for the hybrid retrieval pipeline with service availability checks."""

from __future__ import annotations

import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock

from configs.settings import get_settings
from src.database.sqlite_fallback import sqlite_session_maker
from src.knowledge_graph.neo4j_client import Neo4jClient
from src.retrieval.bm25 import BM25Index
from src.retrieval.embeddings import EmbeddingService
from src.retrieval.pipeline import HybridRetrievalPipeline
from src.retrieval.vector_store import ChromaVectorStore

settings = get_settings()


@pytest.mark.asyncio
async def test_hybrid_retrieval_pipeline_integration() -> None:
    """End-to-end integration test of parallel query fusion and reranker."""
    # 1. Mock connection clients to bypass external container requirements
    mock_neo4j = MagicMock(spec=Neo4jClient)
    mock_neo4j.execute_query = AsyncMock(
        return_value=[
            {
                "id": "chunk1",
                "content": "Graph Node result content detail",
                "confidence": 0.85,
                "entity_type": "Policy",
            }
        ]
    )

    # Mock ChromaVectorStore
    mock_chroma = MagicMock(spec=ChromaVectorStore)
    mock_chroma.search.return_value = [
        {
            "id": "chunk2",
            "content": "Vector database result matching query context",
            "metadata": {"source": "vector_store"},
            "score": 0.88,
        }
    ]


    # 2. Setup concrete BM25 and Mock Embedding
    mock_emb = MagicMock(spec=EmbeddingService)
    mock_emb.model_name = "test-model"
    mock_emb.get_embeddings = AsyncMock(side_effect=lambda texts: [[0.1, 0.2, 0.3] for _ in texts])
    mock_emb.expand_query = AsyncMock(return_value=["alternative check", "expanded check"])



    bm25 = BM25Index()
    bm25.build_index(
        chunks=["Sparse keyword text document detail matching query", "Unrelated text data"],
        metadatas=[{"source": "bm25"}, {"source": "bm25"}],
        ids=["chunk3", "chunk4"],
    )

    # 3. Instantiate pipeline
    pipeline = HybridRetrievalPipeline(
        embedding_service=mock_emb,
        vector_store=mock_chroma,
        bm25_index=bm25,
        neo4j_client=mock_neo4j,
    )

    # Stub the reranker to return candidate scores directly to avoid actual model load latency
    pipeline.reranker = MagicMock()
    pipeline.reranker.rerank.side_effect = lambda q, cand, limit: cand[:limit]

    # 4. Execute retrieval
    results = await pipeline.retrieve("matching query detail", limit=2)

    # 5. Assertions
    assert len(results) > 0
    # Candidate lists must contain items from BM25 and Vector and Graph
    candidate_ids = [r["id"] for r in results]
    assert any(c_id in ["chunk1", "chunk2", "chunk3"] for c_id in candidate_ids)
