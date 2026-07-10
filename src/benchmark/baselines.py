"""Baseline pipeline simulators for benchmark comparisons."""

from __future__ import annotations

from typing import Any, Dict


class BaselinePipelines:
    """Provides methods running baseline RAG and Single LLM workflows."""

    def run_single_llm(self, query: str) -> Dict[str, Any]:
        """Runs Raw LLM call without retrieval contexts."""
        # Returns static mock latency, cost and answers
        return {
            "response": f"Raw LLM response suggestion for: {query}",
            "context": "",
            "metrics": {
                "latency_ms": 1200.0,
                "cost_usd": 0.0012,
                "tokens": 400
            }
        }

    def run_traditional_rag(self, query: str) -> Dict[str, Any]:
        """Runs Vector store retrieval + raw LLM call."""
        context = "Simulated vector retrieval context containing billing disputes rules."
        return {
            "response": f"Traditional RAG response suggestion: {context} for {query}",
            "context": context,
            "metrics": {
                "latency_ms": 2500.0,
                "cost_usd": 0.0045,
                "tokens": 1500
            }
        }
