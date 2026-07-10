"""Tool registry managing permissions, retry boundaries, and run configuration metadata."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

from tenacity import retry, stop_after_attempt, wait_exponential

from src.observability.logging import get_logger

logger = get_logger(__name__)


@dataclass
class Tool:
    """Represents a validated tool execution binding."""

    name: str
    description: str
    func: Callable[..., Any]
    permissions: List[str] = field(default_factory=lambda: ["user"])
    timeout: float = 10.0
    retries: int = 2
    metadata: Dict[str, Any] = field(default_factory=dict)


class ToolRegistry:
    """Discovers and registers callable tools, validating execution privileges."""

    def __init__(self) -> None:
        self._tools: Dict[str, Tool] = {}

    def register(
        self,
        name: str,
        description: str,
        permissions: Optional[List[str]] = None,
        timeout: float = 10.0,
        retries: int = 2,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        """Decorator binding a function to the central registry."""
        perms = permissions or ["user"]
        meta = metadata or {}

        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            tool = Tool(
                name=name,
                description=description,
                func=func,
                permissions=perms,
                timeout=timeout,
                retries=retries,
                metadata=meta,
            )
            self._tools[name] = tool
            logger.info("Tool registered successfully", name=name, permissions=perms)
            return func

        return decorator

    def get_tool(self, name: str) -> Tool:
        """Fetch tool details by name."""
        if name not in self._tools:
            raise KeyError(f"Tool '{name}' is not registered.")
        return self._tools[name]

    async def execute(self, name: str, user_role: str, *args: Any, **kwargs: Any) -> Any:
        """Runs registered tool, verifying permissions and managing retries/timeouts."""
        tool = self.get_tool(name)

        # 1. Verify role permissions
        if user_role not in tool.permissions and "*" not in tool.permissions:
            raise PermissionError(
                f"Role '{user_role}' has insufficient privileges to run tool '{name}'."
            )

        # 2. Build resilience wrapper
        @retry(
            stop=stop_after_attempt(tool.retries + 1),
            wait=wait_exponential(multiplier=1, min=1, max=5),
            reraise=True,
        )
        async def _run_with_retry() -> Any:
            if asyncio.iscoroutinefunction(tool.func):
                return await asyncio.wait_for(tool.func(*args, **kwargs), timeout=tool.timeout)
            else:
                # Run synchronous tool in executor to prevent thread blocks
                return await asyncio.wait_for(
                    asyncio.to_thread(tool.func, *args, **kwargs),
                    timeout=tool.timeout,
                )

        logger.info("Executing tool", name=name, role=user_role)
        return await _run_with_retry()


# Central registry instance
registry = ToolRegistry()
