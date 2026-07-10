"""Reciprocal Rank Fusion (RRF) implementation merging rank lists."""

from __future__ import annotations

from typing import Any, Dict, List

from configs.settings import get_settings
from src.observability.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()


class ReciprocalRankFusion:
    """Combines multiple ranked retrieval result lists into a single consolidated ranking."""

    def __init__(self, k: int | None = None) -> None:
        self.k = k or settings.retrieval.rrf_k

    def fuse(self, rank_lists: List[List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
        """Applies RRF formula to rank candidate items across multiple sparse and dense lists."""
        logger.info("Executing Reciprocal Rank Fusion", list_count=len(rank_lists))

        if not rank_lists:
            return []

        rrf_scores: Dict[str, float] = {}
        # Keep track of the original item object mapping by id
        item_map: Dict[str, Dict[str, Any]] = {}

        for rank_list in rank_lists:
            for rank, item in enumerate(rank_list):
                item_id = item["id"]
                item_map[item_id] = item

                # Calculate RRF score contribution: 1 / (k + rank) (where rank is 1-indexed)
                rank_1_indexed = rank + 1
                score_contribution = 1.0 / (self.k + rank_1_indexed)

                rrf_scores[item_id] = rrf_scores.get(item_id, 0.0) + score_contribution

        # Sort item ids based on the calculated RRF score descending
        sorted_ids = sorted(
            rrf_scores.keys(),
            key=lambda i_id: rrf_scores[i_id],
            reverse=True,
        )

        fused_results: List[Dict[str, Any]] = []
        for item_id in sorted_ids:
            item = item_map[item_id].copy()
            # Set computed RRF score on the document dictionary
            item["score"] = rrf_scores[item_id]
            fused_results.append(item)

        logger.info("RRF completed", fused_count=len(fused_results))
        return fused_results
