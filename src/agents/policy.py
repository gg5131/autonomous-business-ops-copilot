"""Policy Agent checking extracted ticket requirements against company policy rules."""

from __future__ import annotations

from typing import Any, Dict

from src.agents.base import BaseAgent
from src.orchestrator.agent_context import AgentContext
from src.orchestrator.llm_gateway import LLMGateway


class PolicyAgent(BaseAgent):
    """Identifies and highlights business rules and policy constraints."""

    def __init__(self, llm_gateway: LLMGateway) -> None:
        super().__init__(llm_gateway)

    @property
    def name(self) -> str:
        return "Policy"

    @property
    def system_prompt_key(self) -> str:
        return "policy_system_prompt"

    def validate_input(self, context: AgentContext) -> None:
        if not context.retrieved_context:
            raise ValueError("Policy Agent requires company policy reference documents in retrieved context.")
