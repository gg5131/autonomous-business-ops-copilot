"""BM25 Lexical Keyword search index using rank_bm25."""

from __future__ import annotations

import re
from typing import Any, Dict, List

from rank_bm25 import BM25Okapi

from src.observability.logging import get_logger

logger = get_logger(__name__)


class BM25Index:
    """Manages keyword-based BM25 indexing and querying of text chunks."""

    def __init__(self) -> None:
        self._index: BM25Okapi | None = None
        self._chunks: List[str] = []
        self._metadatas: List[Dict[str, Any]] = []
        self._ids: List[str] = []

    def _tokenize(self, text: str) -> List[str]:
        """Simple tokenizer splitting on non-alphanumeric characters, lowercasing."""
        if not text:
            return []
        return [w.lower() for w in re.findall(r"\b\w+\b", text)]

    def build_index(
        self,
        chunks: List[str],
        metadatas: List[Dict[str, Any]],
        ids: List[str],
    ) -> None:
        """Constructs Okapi BM25 search index over the list of text segments."""
        if not chunks:
            logger.warn("Attempted to build BM25 index with empty chunks.")
            return

        logger.info("Building BM25 index", chunk_count=len(chunks))
        self._chunks = chunks
        self._metadatas = metadatas
        self._ids = ids

        tokenized_corpus = [self._tokenize(chunk) for chunk in chunks]
        self._index = BM25Okapi(tokenized_corpus)
        logger.info("BM25 index built successfully.")

    def search(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Compute BM25 scores and return top candidate segments for the query."""
        if not self._index or not self._chunks:
            logger.warn("BM25 search requested but index is not built.")
            return []

        logger.info("Executing BM25 lexical query", query=query, limit=limit)
        tokenized_query = self._tokenize(query)
        scores = self._index.get_scores(tokenized_query)

        # Pair scores with indexes and sort descending
        ranked_indices = sorted(
            range(len(scores)),
            key=lambda i: float(scores[i]),
            reverse=True,
        )[:limit]

        results: List[Dict[str, Any]] = []
        for idx in ranked_indices:
            score = float(scores[idx])
            # Only include documents with non-zero similarity matching query tokens
            if score > 0.0:
                results.append(
                    {
                        "id": self._ids[idx],
                        "content": self._chunks[idx],
                        "metadata": self._metadatas[idx],
                        "score": score,
                    }
                )

        logger.info("BM25 search completed", matches_found=len(results))
        return results
