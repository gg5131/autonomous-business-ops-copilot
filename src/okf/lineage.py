"""Document lineage representation for OKF provenance tracking."""

from __future__ import annotations

from typing import Any, Dict


class LineageTracker:
    """Helper formatting lineage dictionaries for graph ingestion operations."""

    @staticmethod
    def extract_lineage(metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Extract lineage parameters from OKF metadata safely."""
        lineage = metadata.get("lineage", {})
        return {
            "author": lineage.get("author") or "system",
            "date": lineage.get("date") or "unknown",
            "source": lineage.get("source") or "unknown",
            "department": lineage.get("department") or "general",
            "language": lineage.get("language") or "en",
        }
