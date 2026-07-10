"""Confidence Engine calculating groundedness, citation coverage, and compliance risk scores."""

from __future__ import annotations

import re
from typing import Any, Dict, List


class ConfidenceEngine:
    """Computes aggregate confidence scores (0-100) using weighted validation signals."""

    @staticmethod
    def calculate_groundedness(draft: str, sources: List[Dict[str, Any]]) -> float:
        """Estimate groundedness based on draft terms matching source chunks."""
        if not draft or not sources:
            return 0.0
        # Simple token similarity checks
        draft_words = set(re.findall(r"\w+", draft.lower()))
        source_text = " ".join([s.get("content", "") for s in sources]).lower()
        source_words = set(re.findall(r"\w+", source_text))

        if not draft_words:
            return 0.0
        overlap = draft_words.intersection(source_words)
        return float(len(overlap) / len(draft_words))

    @staticmethod
    def calculate_citation_coverage(draft: str) -> float:
        """Calculates percentage of assertions backed by source brackets, e.g. [doc0]."""
        if not draft:
            return 0.0
        sentences = re.split(r"(?<=[.!?])\s+", draft.strip())
        if not sentences:
            return 0.0

        cited_sentences = 0
        for sent in sentences:
            if re.search(r"\[(doc|chunk|source)_\w+\]|\[\d+\]", sent):
                cited_sentences += 1

        return float(cited_sentences / len(sentences))

    def compute_score(
        self,
        draft: str,
        sources: List[Dict[str, Any]],
        fact_checker_output: Dict[str, Any],
        compliance_passed: bool = True,
    ) -> Dict[str, float]:
        """Aggregate signals into a weighted score."""
        groundedness = self.calculate_groundedness(draft, sources)
        citation_cov = self.calculate_citation_coverage(draft)

        # Parse hallucination risk from fact checker
        hallucination_risk = float(fact_checker_output.get("hallucination_risk", 0.0))
        compliance = 1.0 if compliance_passed else 0.0
        validation_pass = 1.0 - hallucination_risk

        # Weighted calculation:
        # 30% groundedness + 25% citation_coverage + 20% (1-hallucination) + 15% compliance + 10% validation
        raw_score = (
            0.30 * groundedness +
            0.25 * citation_cov +
            0.20 * (1.0 - hallucination_risk) +
            0.15 * compliance +
            0.10 * validation_pass
        )

        overall_score = float(min(1.0, max(0.0, raw_score)) * 100.0)

        return {
            "groundedness": float(groundedness * 100.0),
            "citation_coverage": float(citation_cov * 100.0),
            "hallucination_risk": float(hallucination_risk * 100.0),
            "overall_confidence": overall_score,
        }
