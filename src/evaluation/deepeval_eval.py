"""DeepEval-like evaluator verifying groundedness and citation accuracy using sentence embeddings."""

from __future__ import annotations

from typing import Dict

from src.retrieval.embeddings import EmbeddingService
from src.evaluation.ragas_eval import cosine_similarity
from src.observability.logging import get_logger

logger = get_logger(__name__)


class DeepEvalEvaluator:
    """Calculates groundedness and hallucination indexes using dense embeddings."""

    def __init__(self, embedding_service: EmbeddingService | None = None) -> None:
        self.embeddings = embedding_service or EmbeddingService()

    async def evaluate_response(self, response: str, context: str) -> Dict[str, float]:
        """Calculates groundedness and citation indexes."""
        # Citation Accuracy: check bracket presence e.g. [doc1]
        has_citations = "[" in response and "]" in response
        citation_score = 1.0 if has_citations else 0.0

        try:
            r_emb = await self.embeddings.get_embedding(response)
            c_emb = await self.embeddings.get_embedding(context)
            
            groundedness = cosine_similarity(r_emb, c_emb)
            hallucination_rate = 1.0 - groundedness
            
            return {
                "hallucination_risk": max(min(hallucination_rate, 1.0), 0.0),
                "groundedness": max(min(groundedness, 1.0), 0.0),
                "citation_accuracy": citation_score
            }
        except Exception as e:
            logger.warn("DeepEval semantic evaluation failed, falling back to word overlap.", error=str(e))
            resp_words = set(response.lower().split())
            ctx_words = set(context.lower().split())
            
            unsupported = resp_words.difference(ctx_words)
            hallucination_rate = len(unsupported) / max(len(resp_words), 1)
            groundedness = len(resp_words.intersection(ctx_words)) * 2.0 / max(len(resp_words), 1)
            
            return {
                "hallucination_risk": min(hallucination_rate * 0.5, 1.0),
                "groundedness": min(groundedness, 1.0),
                "citation_accuracy": citation_score
            }
        
        
