"""Base agent class defining standardized lifecycles and circuit breaker decorators."""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional
import asyncio

from src.orchestrator.agent_context import AgentContext
from src.orchestrator.event_bus import SystemEvent, event_bus
from src.orchestrator.llm_gateway import LLMGateway
from src.observability.logging import get_logger

logger = get_logger(__name__)


class CircuitBreakerError(Exception):
    """Raised when a node circuit is open and failing fast."""
    pass


class CircuitBreaker:
    """Manages agent state stability to prevent cascading failures."""

    def __init__(self, failure_threshold: int = 3, recovery_timeout: float = 30.0) -> None:
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
        self.failure_count = 0
        self.last_state_change = time.time()

    def record_success(self) -> None:
        """Resets failure counts on successful run executions."""
        self.failure_count = 0
        self.state = "CLOSED"

    def record_failure(self) -> None:
        """Accumulates fail metrics, tripping circuit if limit is exceeded."""
        self.failure_count += 1
        if self.failure_count >= self.failure_threshold:
            self.state = "OPEN"
            self.last_state_change = time.time()
            logger.warn("Circuit breaker TRIPPED to OPEN state", failure_count=self.failure_count)

    def allow_execution(self) -> bool:
        """Returns True if execution can proceed; handles HALF_OPEN transitions."""
        if self.state == "CLOSED":
            return True
        if self.state == "OPEN":
            # If cooling threshold expired, transition to HALF_OPEN
            if time.time() - self.last_state_change > self.recovery_timeout:
                self.state = "HALF_OPEN"
                logger.info("Circuit breaker entered HALF_OPEN cooling test state.")
                return True
            return False
        return True


class BaseAgent(ABC):
    """Abstract base agent providing standard lifecycle hooks and resiliency wrappers."""

    def __init__(
        self,
        llm_gateway: LLMGateway,
        failure_threshold: int = 3,
        recovery_timeout: float = 30.0,
    ) -> None:
        self.llm_gateway = llm_gateway
        self.circuit_breaker = CircuitBreaker(failure_threshold, recovery_timeout)

    @property
    @abstractmethod
    def name(self) -> str:
        """Return unique agent identification label."""
        pass

    @property
    @abstractmethod
    def system_prompt_key(self) -> str:
        """Return the yaml configuration prompt key to fetch from registry."""
        pass

    def validate_input(self, context: AgentContext) -> None:
        """Lifecycle Hook 1: Override to inspect incoming context inputs before executions."""
        pass

    def build_context(self, context: AgentContext) -> str:
        """Lifecycle Hook 2: Compile search and customer variables into context format."""
        from src.orchestrator.context_builder import ContextBuilder
        builder = ContextBuilder()
        return builder.build_context(context.retrieved_context, context.memory_context)

    def validate_output(self, context: AgentContext, response: Dict[str, Any]) -> None:
        """Lifecycle Hook 4: Assert outputs are non-empty and schema-correct."""
        if not response or not response.get("text"):
            raise ValueError(f"Agent '{self.name}' produced an empty text response.")

    async def execute(self, context: AgentContext) -> Dict[str, Any]:
        """Standardized template lifecycle executing validations, gateways, and bus events."""
        start_time = time.time()
        trace_id = context.trace_id

        # Publish Agent Started event
        event_bus.publish(
            SystemEvent(
                event_type="AgentStarted",
                trace_id=trace_id,
                payload={"agent_name": self.name},
            )
        )

        # Step 1: Circuit breaker check
        if not self.circuit_breaker.allow_execution():
            logger.error("Circuit breaker is OPEN. Failing fast.", agent=self.name)
            event_bus.publish(
                SystemEvent(
                    event_type="AgentFailed",
                    trace_id=trace_id,
                    payload={"agent_name": self.name, "error": "CircuitBreakerOpen"},
                )
            )
            raise CircuitBreakerError(f"Circuit breaker for agent '{self.name}' is OPEN.")

        try:
            # Step 2: Validate inputs
            self.validate_input(context)

            # Step 3: Build formatted system context
            formatted_ctx = self.build_context(context)

            # Step 4: Call LLM Gateway (wrapped in dynamic timeout)
            # Retrieve prompt templates
            from src.orchestrator.prompts import PromptRegistry
            registry = PromptRegistry()
            system_inst = registry.get_prompt(self.system_prompt_key)

            # Execution logic combining system instructions
            response = await self.llm_gateway.generate_response(
                prompt=formatted_ctx,
                system_instruction=system_inst,
            )

            # Step 5: Validate outputs
            self.validate_output(context, response)

            # Record success in circuit breaker
            self.circuit_breaker.record_success()

            duration_ms = (time.time() - start_time) * 1000.0

            # Step 6: Log metrics & publish complete event
            event_bus.publish(
                SystemEvent(
                    event_type="AgentCompleted",
                    trace_id=trace_id,
                    payload={
                        "agent_name": self.name,
                        "duration_ms": duration_ms,
                        "prompt_tokens": response["prompt_tokens"],
                        "completion_tokens": response["completion_tokens"],
                        "cost_usd": response["cost_usd"],
                    },
                )
            )

            # Step 7: Return formatted state updates
            return {
                "agent_name": self.name,
                "output": response["text"],
                "tokens": response["total_tokens"],
                "cost": response["cost_usd"],
                "latency_ms": duration_ms,
            }

        except Exception as e:
            self.circuit_breaker.record_failure()
            logger.error("Agent execution failed", agent=self.name, error=str(e))
            event_bus.publish(
                SystemEvent(
                    event_type="AgentFailed",
                    trace_id=trace_id,
                    payload={"agent_name": self.name, "error": str(e)},
                )
            )
            raise
