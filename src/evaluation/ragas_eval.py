"""Ragas-like metrics evaluator checking faithfulness and relevance using sentence embeddings."""

from __future__ import annotations

import numpy as np
from typing import Any, Dict

from src.retrieval.embeddings import EmbeddingService
from src.observability.logging import get_logger

logger = get_logger(__name__)


def cosine_similarity(v1: list[float], v2: list[float]) -> float:
    """Calculates cosine similarity between two float vectors."""
    if not v1 or not v2:
        return 0.0
    arr1 = np.array(v1)
    arr2 = np.array(v2)
    n1 = np.linalg.norm(arr1)
    n2 = np.linalg.norm(arr2)
    if n1 == 0 or n2 == 0:
        return 0.0
    return float(np.dot(arr1, arr2) / (n1 * n2))


class RagasEvaluator:
    """Calculates semantic faithfulness, answer relevance, and context recalls."""

    def __init__(self, embedding_service: EmbeddingService | None = None) -> None:
        self.embeddings = embedding_service or EmbeddingService()

    async def evaluate_response(self, query: str, response: str, context: str, ground_truth: str) -> Dict[str, float]:
        """Runs evaluation over candidate responses returning semantic metrics."""
        try:
            # Generate embeddings concurrently
            q_emb = await self.embeddings.get_embedding(query)
            r_emb = await self.embeddings.get_embedding(response)
            c_emb = await self.embeddings.get_embedding(context)
            gt_emb = await self.embeddings.get_embedding(ground_truth)
            
            # Relevancy: similarity between response and query
            answer_relevancy = cosine_similarity(r_emb, q_emb)
            
            # Faithfulness: similarity between response and context
            faithfulness = cosine_similarity(r_emb, c_emb)
            
            # Recall: similarity between context and ground truth
            context_recall = cosine_similarity(c_emb, gt_emb)
            
            # Adjust ranges
            return {
                "faithfulness": max(min(faithfulness, 1.0), 0.0),
                "answer_relevancy": max(min(answer_relevancy, 1.0), 0.0),
                "context_recall": max(min(context_recall, 1.0), 0.0),
            }
        except Exception as e:
            logger.warn("Semantic evaluation failed, falling back to word overlap metrics.", error=str(e))
            # Fallback word-overlap
            q_words = set(query.lower().split())
            r_words = set(response.lower().split())
            c_words = set(context.lower().split())
            gt_words = set(ground_truth.lower().split())
            
            overlap_c = r_words.intersection(c_words)
            f_score = len(overlap_c) / max(len(r_words), 1)
            
            overlap_q = r_words.intersection(q_words)
            ar_score = len(overlap_q) / max(len(q_words), 1)
            
            overlap_gt = c_words.intersection(gt_words)
            cr_score = len(overlap_gt) / max(len(gt_words), 1)
            
            return {
                "faithfulness": min(f_score * 2.5, 1.0),
                "answer_relevancy": min(ar_score * 3.0, 1.0),
                "context_recall": min(cr_score * 2.0, 1.0),
            }
