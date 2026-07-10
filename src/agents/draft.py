"""Draft Agent formulating professional customer responses."""

from __future__ import annotations

from typing import Any, Dict

from src.agents.base import BaseAgent
from src.orchestrator.agent_context import AgentContext
from src.orchestrator.llm_gateway import LLMGateway


class DraftAgent(BaseAgent):
    """Combines category triage and research highlights to compile response drafts."""

    def __init__(self, llm_gateway: LLMGateway) -> None:
        super().__init__(llm_gateway)

    @property
    def name(self) -> str:
        return "Draft"

    @property
    def system_prompt_key(self) -> str:
        return "draft_system_prompt"

    def build_context(self, context: AgentContext) -> str:
        """Inject previous agent outputs (Triage, Research, Policy) into the draft generator context."""
        base_ctx = super().build_context(context)
        
        # Merge other active agent outputs if present in context
        lines = [base_ctx, "## Inputs from Preceding Agents"]
        for key, val in context.ticket.items():
            if key == "agent_results":
                for agent_name, out in val.items():
                    lines.append(f"### {agent_name} Output:\n{out}")
                    
        return "\n".join(lines).strip()
