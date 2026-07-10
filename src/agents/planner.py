"""Planner Agent parsing customer inputs and generating dependency DAG structures."""

from __future__ import annotations

import json
from typing import Any, Dict, List
from pydantic import BaseModel, Field

from src.agents.base import BaseAgent
from src.orchestrator.agent_context import AgentContext
from src.orchestrator.llm_gateway import LLMGateway
from src.observability.logging import get_logger

logger = get_logger(__name__)


class ExecutionPlan(BaseModel):
    """Execution plan payload specifying agent dependencies DAG."""

    active_agents: List[str] = Field(default_factory=list)
    dependencies: Dict[str, List[str]] = Field(default_factory=dict)
    confidence_threshold: float = 85.0
    human_review_requirement: bool = True
    estimated_cost: float = 0.05


class PlannerAgent(BaseAgent):
    """Planner Agent analyzing queries and outputs dynamically coordinated task dependency graphs."""

    def __init__(self, llm_gateway: LLMGateway) -> None:
        super().__init__(llm_gateway)

    @property
    def name(self) -> str:
        return "Planner"

    @property
    def system_prompt_key(self) -> str:
        return "planner_system_prompt"

    def validate_input(self, context: AgentContext) -> None:
        if not context.ticket or not context.ticket.get("content"):
            raise ValueError("Planner Agent requires a valid ticket content string.")

    def validate_output(self, context: AgentContext, response: Dict[str, Any]) -> None:
        super().validate_output(context, response)
        try:
            # Verify text parses into a valid ExecutionPlan JSON object
            data = json.loads(response["text"])
            ExecutionPlan(**data)
        except Exception as e:
            raise ValueError(f"Planner Agent response failed JSON DAG schema validation: {e}")

    async def execute_plan_generation(self, context: AgentContext) -> ExecutionPlan:
        """Call LLM and retrieve verified ExecutionPlan object."""
        result = await self.execute(context)
        data = json.loads(result["output"])
        return ExecutionPlan(**data)
