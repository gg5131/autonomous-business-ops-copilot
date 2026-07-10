"""AgentContext container passing config context, databases, memory and logger references."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from configs.settings import get_settings
from src.tools.registry import ToolRegistry


@dataclass
class AgentContext:
    """Consolidated immutable dependencies payload injected into every agent execute call."""

    ticket: Dict[str, Any]
    execution_plan: Dict[str, Any]
    retrieved_context: List[Dict[str, Any]]
    memory_context: List[Dict[str, Any]]
    tool_registry: ToolRegistry
    trace_id: str
    logger: Any
    settings: Any = field(default_factory=get_settings)

