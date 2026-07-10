"""Research Agent summarizing and consolidating retrieved reference contexts."""

from __future__ import annotations

from typing import Any, Dict

from src.agents.base import BaseAgent
from src.orchestrator.agent_context import AgentContext
from src.orchestrator.llm_gateway import LLMGateway


class ResearchAgent(BaseAgent):
    """Gathers and summarizes retrieved evidence chunks."""

    def __init__(self, llm_gateway: LLMGateway) -> None:
        super().__init__(llm_gateway)

    @property
    def name(self) -> str:
        return "Research"

    @property
    def system_prompt_key(self) -> str:
        return "research_system_prompt"

    def validate_input(self, context: AgentContext) -> None:
        if not context.retrieved_context:
            raise ValueError("Research Agent requires retrieved reference context to summarize.")
