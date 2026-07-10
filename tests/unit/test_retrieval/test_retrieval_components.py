"""Unit tests for retrieval modules — Chunker, Embeddings, BM25, Fusion, Reranker, and Metrics."""

from __future__ import annotations

import math
import tempfile
import pytest
from unittest.mock import AsyncMock, MagicMock

from src.ingestion.chunker import ChunkerService
from src.retrieval.bm25 import BM25Index
from src.retrieval.embeddings import EmbeddingService, SQLiteEmbeddingCache
from src.retrieval.fusion import ReciprocalRankFusion
from src.retrieval.metrics import RetrievalMetrics
from src.retrieval.reranker import CrossEncoderReranker


def test_chunker_recursive() -> None:
    """Validate recursive chunking character breaks."""
    chunker = ChunkerService()
    text = "Paragraph 1\n\nParagraph 2 is slightly longer. Sentence two."

    # Split with small chunk size to force chunks
    chunks = chunker.recursive_chunk(text, chunk_size=20, chunk_overlap=2)
    assert len(chunks) > 1
    assert "Paragraph 1" in chunks[0] or "Paragraph 1" in chunks[1]


def test_chunker_sliding() -> None:
    """Validate sliding window overlaps."""
    chunker = ChunkerService()
    text = "abcdefghijkl"
    chunks = chunker.sliding_window_chunk(text, window_size=5, overlap=2)
    # abcde (0-5), defgh (3-8), ghijk (6-11), jkl (9-12)
    assert len(chunks) == 4
    assert chunks[0] == "abcde"
    assert chunks[1] == "defgh"


@pytest.mark.asyncio
async def test_chunker_semantic() -> None:
    """Validate semantic chunking boundary split calls."""
    mock_emb = AsyncMock()
    # Mock batch embeddings such that sentences have low similarity and trigger split
    mock_emb.get_embeddings.return_value = [
        [1.0, 0.0],  # Sentence 1
        [0.0, 1.0],  # Sentence 2 (perpendicular, cosine similarity = 0)
    ]

    chunker = ChunkerService(embedding_service=mock_emb)

    text = "Sentence one. Sentence two."

    chunks = await chunker.semantic_chunk(text, threshold=0.5)
    assert len(chunks) == 2
    assert "Sentence one." in chunks[0]
    assert "Sentence two." in chunks[1]


def test_sqlite_embedding_cache() -> None:
    """Validate SQLite embedding cache persistence."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db_path = tmp.name

    try:
        cache = SQLiteEmbeddingCache(db_path=db_path)
        text = "test query"
        model = "test-model"
        vector = [0.1, 0.2, 0.3]

        # Get cache miss
        assert cache.get(text, model) is None

        # Set cache
        cache.set(text, model, vector)

        # Get cache hit
        cached = cache.get(text, model)
        assert cached is not None
        assert cached == vector
    finally:
        import os

        try:
            os.unlink(db_path)
        except Exception:
            pass


def test_bm25_search() -> None:
    """Validate BM25 index matching queries with a sufficiently sized corpus to ensure positive IDF."""
    index = BM25Index()
    chunks = [
        "The quick brown fox jumps",
        "Python programming language is great",
        "Database systems are complex and interesting",
        "Machine learning is fun",
        "DevOps pipeline automates builds",
    ]
    metadatas = [{"id": 0}, {"id": 1}, {"id": 2}, {"id": 3}, {"id": 4}]
    ids = ["doc0", "doc1", "doc2", "doc3", "doc4"]

    index.build_index(chunks, metadatas, ids)

    # Search word quick
    res = index.search("quick", limit=1)
    assert len(res) == 1
    assert res[0]["id"] == "doc0"
    assert "fox" in res[0]["content"]


def test_reciprocal_rank_fusion() -> None:

    """Validate RRF list merging calculations."""
    fusion = ReciprocalRankFusion(k=60)
    # RRF lists
    list1 = [{"id": "docA", "content": "A", "score": 0.9}, {"id": "docB", "content": "B", "score": 0.8}]
    list2 = [{"id": "docB", "content": "B", "score": 0.95}, {"id": "docC", "content": "C", "score": 0.7}]

    fused = fusion.fuse([list1, list2])
    assert len(fused) == 3
    # docB appears in both lists, so its rank is 2 (idx 1) in list1 and 1 (idx 0) in list2.
    # Score contribution: 1/(60+2) + 1/(60+1)
    # docA is 1 (idx 0) in list1. Score: 1/(60+1)
    # Since B has higher score contribution, B must be ranked 1st
    assert fused[0]["id"] == "docB"
    assert fused[1]["id"] == "docA"
    assert fused[2]["id"] == "docC"


def test_retrieval_metrics() -> None:
    """Validate NDCG, Precision, Recall, and MRR calculations."""
    retrieved = ["doc1", "doc2", "doc3", "doc4"]
    ground_truth = {"doc1", "doc3"}

    # Precision@2: doc1 (relevant), doc2 (not relevant) -> 0.5
    p2 = RetrievalMetrics.precision_at_k(retrieved, ground_truth, k=2)
    assert p2 == 0.5

    # Recall@2: doc1 retrieved out of 2 relevant -> 0.5
    r2 = RetrievalMetrics.recall_at_k(retrieved, ground_truth, k=2)
    assert r2 == 0.5

    # MRR: first relevant is rank 1 (idx 0) -> 1.0
    mrr = RetrievalMetrics.mean_reciprocal_rank(retrieved, ground_truth)
    assert mrr == 1.0

    # NDCG@2: relevance at 1: 1, at 2: 0. DCG@2 = 1/log2(2) + 0 = 1.0
    # IDCG@2: best is 1/log2(2) + 1/log2(3) = 1.6309 (since both elements in GT are relevant).
    ndcg2 = RetrievalMetrics.ndcg_at_k(retrieved, ground_truth, k=2)
    assert ndcg2 == pytest.approx(0.613147, rel=1e-4)

