"""Internal Event Bus for agent and review tracking and system observability."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, List

from src.observability.logging import get_logger

logger = get_logger(__name__)


@dataclass
class SystemEvent:
    """Base class for all internal bus event payloads."""

    event_type: str
    trace_id: str
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    payload: Dict[str, Any] = field(default_factory=dict)


class EventBus:
    """Publish-subscribe event broker coordinating system-level tracing and log updates."""

    def __init__(self) -> None:
        self._listeners: Dict[str, List[Callable[[SystemEvent], Any]]] = {}

    def subscribe(self, event_type: str, callback: Callable[[SystemEvent], Any]) -> None:
        """Register a handler callback for a specific event key."""
        if event_type not in self._listeners:
            self._listeners[event_type] = []
        self._listeners[event_type].append(callback)

    def publish(self, event: SystemEvent) -> None:
        """Broadcasts event payload to all registered type listeners."""
        logger.info(
            "Event published",
            event_type=event.event_type,
            trace_id=event.trace_id,
            payload=event.payload,
        )
        listeners = self._listeners.get(event.event_type, [])
        for listener in listeners:
            try:
                listener(event)
            except Exception as e:
                logger.error(
                    "Event listener failed",
                    error=str(e),
                    event_type=event.event_type,
                    trace_id=event.trace_id,
                )


# Global event bus singleton instance
event_bus = EventBus()
