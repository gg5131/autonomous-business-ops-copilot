"""Memory store segmentations into episodic, semantic, procedural, and feedback registries."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

from src.observability.logging import get_logger

logger = get_logger(__name__)


@dataclass
class MemoryRecord:
    """Represents a validated record entry within memory systems."""

    key: str
    content: Dict[str, Any]
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    tags: List[str] = field(default_factory=list)


class EpisodicMemory:
    """Stores logs of direct episodes: user queries, agent outputs, and final results."""

    def __init__(self) -> None:
        self._store: Dict[str, MemoryRecord] = {}

    def store_episode(self, ticket_id: str, plan: Dict[str, Any], results: Dict[str, Any]) -> None:
        """Saves plan and final responses generated for a ticket."""
        self._store[ticket_id] = MemoryRecord(
            key=ticket_id,
            content={"plan": plan, "results": results},
            tags=["episode", f"ticket_{ticket_id}"],
        )
        logger.info("Episodic memory recorded", ticket_id=ticket_id)

    def retrieve_episode(self, ticket_id: str) -> Optional[Dict[str, Any]]:
        """Fetch saved ticket history details."""
        rec = self._store.get(ticket_id)
        return rec.content if rec else None


class SemanticMemory:
    """Maintains domain definitions, policy abstracts, and entity mappings."""

    def __init__(self) -> None:
        self._store: Dict[str, MemoryRecord] = {}

    def store_fact(self, entity_name: str, definition: Dict[str, Any], tags: Optional[List[str]] = None) -> None:
        """Stores a resolved domain concept fact details."""
        self._store[entity_name] = MemoryRecord(
            key=entity_name,
            content=definition,
            tags=tags or ["fact"],
        )
        logger.info("Semantic fact recorded", entity=entity_name)

    def retrieve_fact(self, entity_name: str) -> Optional[Dict[str, Any]]:
        """Lookup concepts details by key."""
        rec = self._store.get(entity_name)
        return rec.content if rec else None


class ProceduralMemory:
    """Tracks generic execution strategies and operational task guides."""

    def __init__(self) -> None:
        self._store: Dict[str, MemoryRecord] = {}

    def store_procedure(self, task_type: str, steps: List[str]) -> None:
        """Registers step execution instructions."""
        self._store[task_type] = MemoryRecord(
            key=task_type,
            content={"steps": steps},
            tags=["procedure", task_type],
        )
        logger.info("Procedural flow recorded", task_type=task_type)

    def retrieve_procedure(self, task_type: str) -> Optional[List[str]]:
        """Lookup workflows instructions by key."""
        rec = self._store.get(task_type)
        return rec.content.get("steps") if rec else None


class FeedbackMemory:
    """Records human-in-the-loop audit edits, feedback notes, and corrections."""

    def __init__(self) -> None:
        self._store: List[MemoryRecord] = []

    def store_feedback(self, ticket_id: str, original: str, corrected: str, notes: str) -> None:
        """Log human corrections diffs for offline tuning or context retrieval."""
        self._store.append(
            MemoryRecord(
                key=ticket_id,
                content={"original": original, "corrected": corrected, "notes": notes},
                tags=["feedback", f"ticket_{ticket_id}"],
            )
        )
        logger.info("Human review feedback logged to memory", ticket_id=ticket_id)

    def get_ticket_feedback(self, ticket_id: str) -> List[Dict[str, Any]]:
        """Return all matching feedback updates log."""
        return [
            rec.content
            for rec in self._store
            if ticket_id in rec.tags
        ]
