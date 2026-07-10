"""Retrieval metrics calculation — Precision@K, Recall@K, MRR, NDCG, and latency."""

from __future__ import annotations

import math
from typing import Any, List, Set


class RetrievalMetrics:
    """Calculates search accuracy and ranking performance metrics."""

    @staticmethod
    def precision_at_k(retrieved_ids: List[Any], ground_truth_ids: Set[Any], k: int) -> float:
        """Calculate Precision@K: fraction of retrieved documents in top K that are relevant."""
        if not retrieved_ids or not ground_truth_ids or k <= 0:
            return 0.0

        top_k = retrieved_ids[:k]
        relevant_retrieved = sum(1 for item in top_k if item in ground_truth_ids)
        return float(relevant_retrieved / k)

    @staticmethod
    def recall_at_k(retrieved_ids: List[Any], ground_truth_ids: Set[Any], k: int) -> float:
        """Calculate Recall@K: fraction of relevant documents in ground truth retrieved in top K."""
        if not retrieved_ids or not ground_truth_ids or k <= 0:
            return 0.0

        top_k = retrieved_ids[:k]
        relevant_retrieved = sum(1 for item in top_k if item in ground_truth_ids)
        return float(relevant_retrieved / len(ground_truth_ids))

    @staticmethod
    def mean_reciprocal_rank(retrieved_ids: List[Any], ground_truth_ids: Set[Any]) -> float:
        """Calculate Reciprocal Rank (RR): reciprocal of the rank of the first relevant document."""
        if not retrieved_ids or not ground_truth_ids:
            return 0.0

        for rank, item in enumerate(retrieved_ids):
            if item in ground_truth_ids:
                return float(1.0 / (rank + 1))
        return 0.0

    @staticmethod
    def ndcg_at_k(retrieved_ids: List[Any], ground_truth_ids: Set[Any], k: int) -> float:
        """Calculate NDCG@K (Normalized Discounted Cumulative Gain) using binary relevance."""
        if not retrieved_ids or not ground_truth_ids or k <= 0:
            return 0.0

        top_k = retrieved_ids[:k]

        # Calculate Discounted Cumulative Gain (DCG)
        dcg = 0.0
        for rank, item in enumerate(top_k):
            if item in ground_truth_ids:
                # DCG logic: 1 / log2(rank + 2) since rank is 0-indexed
                dcg += 1.0 / math.log2(rank + 2)

        # Calculate Ideal Discounted Cumulative Gain (IDCG)
        idcg = 0.0
        ideal_limit = min(len(ground_truth_ids), k)
        for rank in range(ideal_limit):
            idcg += 1.0 / math.log2(rank + 2)

        if idcg == 0.0:
            return 0.0

        return float(dcg / idcg)
