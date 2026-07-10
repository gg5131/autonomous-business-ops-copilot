"""Cross-Encoder Reranker using SentenceTransformers CrossEncoder model."""

from __future__ import annotations

from typing import Any, Dict, List

from sentence_transformers import CrossEncoder

from configs.settings import get_settings
from src.observability.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()


class CrossEncoderReranker:
    """Re-scores and re-ranks candidate text chunks using a transformer Cross-Encoder model."""

    def __init__(self, model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2") -> None:
        self.model_name = model_name
        logger.info("Initializing Cross-Encoder model", model=self.model_name)
        self._model = CrossEncoder(self.model_name)

    def rerank(self, query: str, candidates: List[Dict[str, Any]], limit: int = 5) -> List[Dict[str, Any]]:
        """Predict cross-encoder similarity scores for (query, content) pairs and sort candidates."""
        if not candidates:
            return []

        logger.info("Reranking candidates via Cross-Encoder", count=len(candidates), limit=limit)

        # Prepare sentence pairs for CrossEncoder evaluation
        pairs = [[query, item["content"]] for item in candidates]

        # Predict relevance scores (higher means more relevant)
        scores = self._model.predict(pairs)

        # Assign scores to candidates
        reranked_list = []
        for idx, item in enumerate(candidates):
            new_item = item.copy()
            new_item["score"] = float(scores[idx])
            reranked_list.append(new_item)

        # Sort descending by cross-encoder score
        reranked_list = sorted(
            reranked_list,
            key=lambda x: x["score"],
            reverse=True,
        )

        logger.info("Reranking completed successfully.")
        return reranked_list[:limit]
